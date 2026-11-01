# Shield upright + face forward: the shield voxels are bound to LeftHandThumb3. Per frame, rotate that bone about its head (the grip) so the
# shield's face normal (PCA min axis, sign away from body) points along the hips' forward and its long axis (PCA max) is vertical.
# usage: blender -b -P shieldfix.py -- in.glb out.glb '<clip regex>' [STRENGTH=1]
import sys,bpy,numpy as np,math,re,json
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
res={}
for act in sorted(bpy.data.actions,key=lambda x:x.name):
    cl=act.name.split('_'+arm.name)[0]
    if not re.search(a[2],cl): continue
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); pb=arm.pose.bones[SB]; pb.rotation_mode='QUATERNION'; b=[];af=[]
    for fr in range(f0,f1+1):
        sc.frame_set(fr); n,L=axes(); f=fwd(); b.append((round(math.degrees(math.acos(np.clip(np.dot(n,f),-1,1))),1),round(math.degrees(math.acos(np.clip(L[2],-1,1))),1)))
        u=np.array([0,0,1.0]); fx=f; ux=u-np.dot(u,fx)*fx; ux/=np.linalg.norm(ux)
        Lx=L-np.dot(L,n)*n; Lx/=np.linalg.norm(Lx)
        C=np.stack([n,Lx,np.cross(n,Lx)],1); T=np.stack([fx,ux,np.cross(fx,ux)],1); R=Matrix((T@C.T).tolist())
        q=R.to_quaternion(); q=Matrix.Identity(3).to_quaternion().slerp(q,K)
        pw=mw@pb.head; Rw=Matrix.Translation(pw)@q.to_matrix().to_4x4()@Matrix.Translation(-pw)
        pb.matrix=mw.inverted()@Rw@mw@pb.matrix; pb.keyframe_insert('rotation_quaternion',frame=fr); bpy.context.view_layer.update()
        n2,L2=axes(); af.append((math.degrees(math.acos(np.clip(np.dot(n2,fwd()),-1,1))),math.degrees(math.acos(np.clip(L2[2],-1,1)))))
    A=np.array(af); res[cl]={'before_normal_fwd_med':float(np.median([x[0] for x in b])),'before_long_vert_med':float(np.median([x[1] for x in b])),'before_long_vert_max':float(max(x[1] for x in b)),'after_normal_fwd_max':round(float(A[:,0].max()),1),'after_long_vert_max':round(float(A[:,1].max()),1)}
    print('SF',cl,res[cl],flush=True)
json.dump(res,open(a[1].replace('.glb','.shieldfix.json'),'w'),indent=1)
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
