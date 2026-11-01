# Shield upright + face forward: the shield voxels are bound to LeftHandThumb3. Per frame, rotate that bone about its head (the grip) so the
# shield's face normal (PCA min axis, sign away from body) points along the hips' forward and its long axis (PCA max) is vertical.
# usage: blender -b -P shieldfix.py -- in.glb out.glb '<clip regex>' [STRENGTH=1]
import sys,os,bpy,numpy as np,math,re,json
sys.path.insert(0,'/workspace/varn-core/tools/capes'); from lib import *
from mathutils import Matrix,Vector
a=sys.argv[sys.argv.index('--')+1:]; K=float(a[3]) if len(a)>3 else 1.0
me,arm=load(a[0]); sc=bpy.context.scene; sc.render.fps=30; co,dom=vinfo(me); SB='mixamorig:LeftHandThumb3'
m=dom==SB; W=np.c_[co[m],np.ones(m.sum())]; mw=arm.matrix_world
lt=mw@arm.data.bones['mixamorig:LeftToeBase'].head_local; lf=mw@arm.data.bones['mixamorig:LeftFoot'].head_local
rt=mw@arm.data.bones['mixamorig:RightToeBase'].head_local; rf=mw@arm.data.bones['mixamorig:RightFoot'].head_local
FWD0=(lt-lf)+(rt-rf); FWD0.z=0; FWD0.normalize()
def fwd():
    hb=arm.pose.bones['mixamorig:Hips']; R=(mw@hb.matrix).to_3x3()@(mw@arm.data.bones['mixamorig:Hips'].matrix_local).to_3x3().inverted()
    f=np.array(R@FWD0); f[2]=0; return f/np.linalg.norm(f)
# shield frame from the rest pose (face normal = PCA min axis pointing away from the body at rest, long = PCA max, up), carried by the bone transform
P0=co[m]; c0=P0.mean(0); _,_,V0=np.linalg.svd(P0-c0,full_matrices=False); N0,L0=V0[2],V0[0]
if np.dot(c0-np.array(mw@arm.data.bones['mixamorig:Spine1'].head_local),N0)<0: N0=-N0
if L0[2]<0: L0=-L0
def axes():
    M=np.array(mw@arm.pose.bones[SB].matrix@arm.data.bones[SB].matrix_local.inverted())[:3,:3]
    n=M@N0; L=M@L0; return n/np.linalg.norm(n),L/np.linalg.norm(L)
S=0.018
def KK(P):
    k=np.floor(P/S).astype(np.int64); return (k[:,0]+4096)*67108864+(k[:,1]+4096)*8192+(k[:,2]+4096)
Cl=np.array([cls(d) for d in dom]); Wall=np.c_[co,np.ones(len(co))]; names=sorted(set(dom)); legsel=Cl=='leg'
def legkeys():
    out=[]
    for nm in set(dom[legsel]):
        Mx=np.array(mw@arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted()); i=dom==nm; out.append((Mx@Wall[i].T).T[:,:3])
    return np.unique(KK(np.concatenate(out)))
def axrot(ax,ang):
    ax=np.asarray(ax)/np.linalg.norm(ax); c,s_=math.cos(ang),math.sin(ang); x,y,z=ax; C=1-c
    return np.array([[c+x*x*C,x*y*C-z*s_,x*z*C+y*s_],[y*x*C+z*s_,c+y*y*C,y*z*C-x*s_],[z*x*C-y*s_,z*y*C+x*s_,c+z*z*C]])
def Rtarget(n,L,f,yaw,side,roll=0.0):
    u=np.array([0,0,1.0]); c,sn=math.cos(yaw),math.sin(yaw); lat=np.cross(u,f)*side
    fx=c*f+sn*lat; fx/=np.linalg.norm(fx)
    Lx=L-np.dot(L,n)*n; Lx/=np.linalg.norm(Lx)
    C=np.stack([n,Lx,np.cross(n,Lx)],1); T=np.stack([fx,u,np.cross(fx,u)],1); R=T@C.T
    if roll:
        # tilt the shield's bottom edge outward (away from the legs) about the face normal
        R1=axrot(fx,roll); R2=axrot(fx,-roll); ul=np.cross(fx,u)
        R=(R1 if np.dot(R1@(-u),lat)>0 else R2)@R
    return R
CANDS=sorted([(y,r) for y in range(0,91,10) for r in (0,10,20,30)],key=lambda t:t[0]+1.5*t[1])
res={}
for act in sorted(bpy.data.actions,key=lambda x:x.name):
    cl=act.name.split('_'+arm.name)[0]
    if not re.search(a[2],cl): continue
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); pb=arm.pose.bones[SB]; pb.rotation_mode='QUATERNION'
    fr_data=[]; b=[]
    for fr in range(f0,f1+1):
        sc.frame_set(fr); n,L=axes(); f=fwd(); b.append((math.degrees(math.acos(np.clip(np.dot(n,f),-1,1))),math.degrees(math.acos(np.clip(L[2],-1,1)))))
        Mb=np.array(mw@pb.matrix@arm.data.bones[SB].matrix_local.inverted()); P=(Mb@W.T).T[:,:3]; pw=np.array(mw@pb.head)
        side=1 if np.dot(np.cross([0,0,1.0],f),P.mean(0)-np.array(mw@arm.pose.bones['mixamorig:Spine1'].head))>0 else -1
        legs=legkeys(); best=None
        for y,r in CANDS:
            R=Rtarget(n,L,f,math.radians(y),side,math.radians(r)); h=int(np.isin(KK((P-pw)@R.T+pw),legs).sum())
            if best is None or h<best[2]: best=(math.radians(y),math.radians(r),h)
            if h==0: break
        fr_data.append([n,L,f,side,best[0],pb.matrix.copy(),best[1]])
    g=np.exp(-0.5*(np.arange(-4,5)/2.0)**2); g/=g.sum()
    def sm(Y):
        D2=Y.copy(); Rd=int(os.environ.get('SDIL','5')); loop=cl in ('run','walk','idle','guard_stance','combat_idle'); n_=len(Y)
        for t in range(n_): D2[t]=max(Y[(t+d)%n_] if loop else Y[min(max(t+d,0),n_-1)] for d in range(-Rd,Rd+1))
        return np.convolve(np.pad(D2,4,mode='wrap' if cl in ('run','walk','idle','guard_stance','combat_idle') else 'edge'),g,'valid')
    Ys=sm(np.array([d[4] for d in fr_data])); Rs=sm(np.array([d[6] for d in fr_data]))
    af=[]
    for k,fr in enumerate(range(f0,f1+1)):
        n,L,f,side,_,M0,_r=fr_data[k]; sc.frame_set(fr); pb.matrix=M0; bpy.context.view_layer.update()
        R=Matrix(Rtarget(n,L,f,Ys[k],side,Rs[k]).tolist()); q=Matrix.Identity(3).to_quaternion().slerp(R.to_quaternion(),K)
        pw=mw@pb.head; pb.matrix=mw.inverted()@Matrix.Translation(pw)@q.to_matrix().to_4x4()@Matrix.Translation(-pw)@mw@pb.matrix
        pb.keyframe_insert('rotation_quaternion',frame=fr); bpy.context.view_layer.update()
    # exact pass: frames still touching the legs take the best candidate directly (no smoothing)
    ex=[]
    for fr in range(f0,f1+1):
        sc.frame_set(fr); Mb=np.array(mw@pb.matrix@arm.data.bones[SB].matrix_local.inverted()); P=(Mb@W.T).T[:,:3]; legs=legkeys()
        if os.environ.get('EXACT')!='1' or int(np.isin(KK(P),legs).sum())==0: continue
        n,L=axes(); f=fwd(); pw=np.array(mw@pb.head)
        side=1 if np.dot(np.cross([0,0,1.0],f),P.mean(0)-np.array(mw@arm.pose.bones['mixamorig:Spine1'].head))>0 else -1
        # undo nothing: search candidates relative to the original target frame
        best=None
        for y,r in CANDS:
            R=Rtarget(n,L,f,math.radians(y),side,math.radians(r)); h=int(np.isin(KK((P-pw)@R.T+pw),legs).sum())
            if best is None or h<best[0]: best=(h,R,y,r)
            if h==0: break
        R=Matrix(best[1].tolist()); pwv=mw@pb.head
        pb.matrix=mw.inverted()@Matrix.Translation(pwv)@R.to_4x4()@Matrix.Translation(-pwv)@mw@pb.matrix; pb.keyframe_insert('rotation_quaternion',frame=fr); bpy.context.view_layer.update(); ex.append([fr,best[2],best[3],best[0]])
    if ex: print('SFX',cl,ex,flush=True)
    for fr in range(f0,f1+1):
        sc.frame_set(fr); n2,L2=axes(); af.append((math.degrees(math.acos(np.clip(np.dot(n2,fwd()),-1,1))),math.degrees(math.acos(np.clip(L2[2],-1,1)))))
    A=np.array(af); B_=np.array(b)
    res[cl]={'before_face_fwd_med':round(float(np.median(B_[:,0])),1),'before_long_vert_med':round(float(np.median(B_[:,1])),1),'before_long_vert_max':round(float(B_[:,1].max()),1),
             'after_face_fwd_med':round(float(np.median(A[:,0])),1),'after_face_fwd_max':round(float(A[:,0].max()),1),'after_long_vert_max':round(float(A[:,1].max()),1),'yaw_out_max':round(math.degrees(Ys.max()),1),'roll_out_max':round(math.degrees(Rs.max()),1)}
    print('SF',cl,res[cl],flush=True)
json.dump(res,open(a[1].replace('.glb','.shieldfix.json'),'w'),indent=1)
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
