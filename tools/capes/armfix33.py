import sys,bpy,json,numpy as np,math
sys.path.insert(0,'/tmp/af33'); from lib import *
from mathutils import Matrix,Quaternion,Vector
a=sys.argv[sys.argv.index('--')+1:]; src,OUT=a[0],a[1]; CAP=float(a[2]) if len(a)>2 else 40
me,arm=load(src); sc=bpy.context.scene; sc.render.fps=30
co,dom=vinfo(me); Cl=np.array([cls(d) for d in dom]); W=np.c_[co,np.ones(len(co))]; S=0.018
def K(P):
    k=np.floor(P/S).astype(np.int64); return (k[:,0]+4096)*67108864+(k[:,1]+4096)*8192+(k[:,2]+4096)
def side(n):
    l=n.lower(); return 'L' if (l.endswith(('_l','.l','left')) or 'left' in l) else ('R' if (l.endswith(('_r','.r')) or 'right' in l) else None)
ua={}
for b in arm.data.bones:
    l=b.name.lower()
    if cls(b.name)=='arm' and ('upperarm' in l or l.endswith('leftarm') or l.endswith('rightarm')) and side(b.name): ua[side(b.name)]=b.name
def desc(bn):
    s={bn}; [s.add(c.name) for c in arm.data.bones[bn].children_recursive]; return s
amask={s:np.isin(dom,list(desc(n))) for s,n in ua.items()}
names=sorted(set(dom))
def pose():
    P=np.zeros_like(co)
    for nm in names:
        if nm not in arm.pose.bones: continue
        Mx=np.array(arm.matrix_world@arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted()@arm.matrix_world.inverted()); i=dom==nm; P[i]=(Mx@W[i].T).T[:,:3]
    return P
hips=[b.name for b in arm.data.bones if b.parent is None][0]
def rot(axis,ang):
    c,s=math.cos(ang),math.sin(ang); x,y,z=axis; C=1-c
    return np.array([[c+x*x*C,x*y*C-z*s,x*z*C+y*s],[y*x*C+z*s,c+y*y*C,y*z*C-x*s],[z*x*C-y*s,z*y*C+x*s,c+z*z*C]])
def frame_info():
    P=pose(); legs=np.unique(K(P[Cl=='leg'])); mw=np.array(arm.matrix_world)
    piv={s:(mw@np.r_[np.array(arm.pose.bones[n].head),1])[:3] for s,n in ua.items()}
    hp=(mw@np.r_[np.array(arm.pose.bones[hips].head),1])[:3]
    # forward axis in world = character facing; use armature -Y? use world Y (glTF imported Z-up, char faces -Y)
    return P,legs,piv,hp
def hits(P,legs,s,ang,piv,hp):
    Q=P[amask[s]]
    if ang:
        out=np.sign(piv[s][0]-hp[0]) or (1 if s=='L' else -1)
        R=rot((0,1,0),-out*ang)  # rotate about Y so arm swings outward in +out x
        Q=(Q-piv[s])@R.T+piv[s]
    return int(np.isin(K(Q),legs).sum())
def chk(act):
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); m=0
    for fr in range(f0,f1+1,2):
        sc.frame_set(fr); P,legs,piv,hp=frame_info(); m=max(m,sum(hits(P,legs,s,0,piv,hp) for s in ua))
    return m
arm.animation_data_create(); res={}
steps0=[math.radians(x) for x in range(0,int(CAP)+1,3)]; steps1=[math.radians(x) for x in range(0,61,3)]
for act in sorted(bpy.data.actions,key=lambda x:x.name):
    cl=act.name.split('_'+arm.name)[0]
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); before=0
    angs={s:[] for s in ua}
    for fr in range(f0,f1+1):
        sc.frame_set(fr); P,legs,piv,hp=frame_info()
        for s in ua:
            h0=hits(P,legs,s,0,piv,hp); before=max(before,h0); best=(h0,0)
            if h0>0:
                for t in (steps1 if 'fly' in cl else steps0)[1:]:
                    h=hits(P,legs,s,t,piv,hp)
                    if h<best[0]: best=(h,t)
                    if h==0: break
            angs[s].append(best[1])
    if max(max(v) for v in angs.values())==0: res[cl]={'before':before,'after':before,'maxdeg':0}; continue
    # smooth: running max over +-3 frames then gaussian
    for s in ua:
        A=np.array(angs[s]); n=len(A); B=np.array([A[max(0,i-3):i+4].max() for i in range(n)])
        g=np.exp(-0.5*(np.arange(-4,5)/2.0)**2); g/=g.sum(); Bp=np.pad(B,4,mode='edge'); C=np.convolve(Bp,g,'valid')
        angs[s]=np.maximum(C,A)
    # bake: world rotation about shoulder pivot, per frame
    for fr in range(f0,f1+1):
        sc.frame_set(fr); mw=arm.matrix_world; hp=mw@arm.pose.bones[hips].head
        for s,n in ua.items():
            t=float(angs[s][fr-f0])
            if t<=0: continue
            pb=arm.pose.bones[n]; pw=mw@pb.head; out=1 if pw.x>=hp.x else -1
            Rw=Matrix.Translation(pw)@Matrix.Rotation(-out*t,4,'Y')@Matrix.Translation(-pw)
            pb.matrix=mw.inverted()@Rw@mw@pb.matrix
            pb.rotation_mode='QUATERNION'; pb.keyframe_insert('rotation_quaternion',frame=fr)
            bpy.context.view_layer.update()
    after=chk(act); res[cl]={'before':before,'after':after,'maxdeg':round(math.degrees(max(max(v) for v in angs.values())),1)}
    print('CLIP',cl,res[cl],flush=True)
json.dump(res,open(OUT.replace('.glb','.armfix.json'),'w'),indent=1)
print('SUMMARY',json.dumps(res))
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
