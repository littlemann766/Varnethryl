# per-frame hand (wrist) re-aim so the hand + mace/shield clear the legs; only frames that clip get a rotation, which is dilated (+-R) and gaussian-smoothed so no snaps; key timing untouched.
# usage: blender -b -P handclear2.py -- in.glb out.glb '<clip regex>'
import sys,bpy,json,numpy as np,math,re,os
sys.path.insert(0,'/workspace/varn-core/tools/capes'); from lib import *
from mathutils import Matrix
a=sys.argv[sys.argv.index('--')+1:]; src,OUT,ONLY=a[0],a[1],a[2]
me,arm=load(src); sc=bpy.context.scene; sc.render.fps=30
co,dom=vinfo(me); Cl=np.array([cls(d) for d in dom]); W=np.c_[co,np.ones(len(co))]; S=0.018
def K(P):
    k=np.floor(P/S).astype(np.int64); return (k[:,0]+4096)*67108864+(k[:,1]+4096)*8192+(k[:,2]+4096)
names=sorted(set(dom))
def desc(bn): s={bn}; [s.add(c.name) for c in arm.data.bones[bn].children_recursive]; return s
HB={'L':'mixamorig:LeftHand','R':'mixamorig:RightHand'}; UA={'L':'mixamorig:LeftArm','R':'mixamorig:RightArm'}
hmask={s:np.isin(dom,list(desc(n))) for s,n in HB.items()}; amask={s:np.isin(dom,list(desc(n))) for s,n in UA.items()}
def pose():
    P=np.zeros_like(co)
    for nm in names:
        if nm not in arm.pose.bones: continue
        Mx=np.array(arm.matrix_world@arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted()@arm.matrix_world.inverted()); i=dom==nm; P[i]=(Mx@W[i].T).T[:,:3]
    return P
def rot(axis,ang):
    c,s=math.cos(ang),math.sin(ang); x,y,z=axis; C=1-c
    return np.array([[c+x*x*C,x*y*C-z*s,x*z*C+y*s],[y*x*C+z*s,c+y*y*C,y*z*C-x*s],[z*x*C-y*s,z*y*C+x*s,c+z*z*C]])
G=sorted([(x,y,z) for x in range(-60,61,15) for y in range(-90,91,10) for z in range(-45,46,15)],key=lambda t:abs(t[0])+abs(t[1])+abs(t[2]))
D=math.radians; res={}; R=int(os.environ.get('DIL','3'))
for act in sorted(bpy.data.actions,key=lambda x:x.name):
    cl=act.name.split('_'+arm.name)[0]
    if not re.search(ONLY,cl): continue
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); b00=None
    for it in range(int(os.environ.get('ITERS','3'))):
      prm={s:[] for s in HB}; before=0
      for fr in range(f0,f1+1):
          sc.frame_set(fr); P=pose(); legs=np.unique(K(P[Cl=='leg']))
          for s in HB:
              idx=np.where(amask[s])[0]; Q=P[idx]; hm=hmask[s][idx]
              h0=int(np.isin(K(Q),legs).sum()); before=max(before,h0); best=(h0,0,0,0)
              if h0>0:
                  wp=np.array(arm.matrix_world@arm.pose.bones[HB[s]].head)
                  pv=np.array(prm[s][-1]) if prm[s] else np.zeros(3); bc=1e18
                  for x,y,z in G:
                      Q2=Q.copy(); Q2[hm]=(Q[hm]-wp)@(rot((0,0,1),D(z))@rot((0,1,0),D(y))@rot((1,0,0),D(x))).T+wp
                      h=int(np.isin(K(Q2),legs).sum()); c=h*1000+np.abs(np.array([x,y,z])-pv).sum()+0.3*(abs(x)+abs(y)+abs(z))
                      if c<bc: bc=c; best=(h,x,y,z)
              prm[s].append(best[1:])
              if h0>0 and os.environ.get('DBG'): print('HCD',cl,it,fr,s,h0,best,flush=True)
      g=np.exp(-0.5*(np.arange(-4,5)/2.0)**2); g/=g.sum(); n=0
      for s in HB:
          A=np.array(prm[s],float); B=A.copy()
          for t in range(len(A)):
              for i in range(3): w=A[max(0,t-R):t+R+1,i]; B[t,i]=w[np.argmax(np.abs(w))]
          prm[s]=np.stack([np.convolve(np.pad(B[:,i],4,mode='edge'),g,'valid') for i in range(3)],1)
      for fr in range(f0,f1+1):
          sc.frame_set(fr); mw=arm.matrix_world
          for s,bn in HB.items():
              x,y,z=prm[s][fr-f0]
              if abs(x)+abs(y)+abs(z)<1e-3: continue
              pb=arm.pose.bones[bn]; pw=mw@pb.head
              Rw=Matrix.Translation(pw)@Matrix.Rotation(D(z),4,'Z')@Matrix.Rotation(D(y),4,'Y')@Matrix.Rotation(D(x),4,'X')@Matrix.Translation(-pw)
              pb.matrix=mw.inverted()@Rw@mw@pb.matrix; pb.rotation_mode='QUATERNION'; pb.keyframe_insert('rotation_quaternion',frame=fr); bpy.context.view_layer.update()
      after=0
      for fr in range(f0,f1+1):
          sc.frame_set(fr); P=pose(); legs=np.unique(K(P[Cl=='leg']))
          after=max(after,max(int(np.isin(K(P[amask[s]]),legs).sum()) for s in HB))
      if b00 is None: b00=before
      if after==0: break
    # final exact pass: frames still clipping get the smallest fine-grid wrist turn (<=30 deg, no smoothing, so no snap > 35)
    GF=sorted([(x,y,z) for x in range(-30,31,5) for y in range(-30,31,5) for z in range(-30,31,10)],key=lambda t:abs(t[0])+abs(t[1])+abs(t[2]))
    for fr in range(f0,f1+1):
        sc.frame_set(fr); P=pose(); legs=np.unique(K(P[Cl=='leg']))
        for s,bn in HB.items():
            idx=np.where(amask[s])[0]; Q=P[idx]; hm=hmask[s][idx]; h0=int(np.isin(K(Q),legs).sum())
            if h0==0: continue
            wp=np.array(arm.matrix_world@arm.pose.bones[bn].head); best=(h0,0,0,0)
            for x,y,z in GF:
                Q2=Q.copy(); Q2[hm]=(Q[hm]-wp)@(rot((0,0,1),D(z))@rot((0,1,0),D(y))@rot((1,0,0),D(x))).T+wp
                h=int(np.isin(K(Q2),legs).sum())
                if h<best[0]: best=(h,x,y,z)
                if h==0: break
            _,x,y,z=best
            if (x,y,z)==(0,0,0): continue
            mw=arm.matrix_world; pb=arm.pose.bones[bn]; pw=mw@pb.head
            pb.matrix=mw.inverted()@Matrix.Translation(pw)@Matrix.Rotation(D(z),4,'Z')@Matrix.Rotation(D(y),4,'Y')@Matrix.Rotation(D(x),4,'X')@Matrix.Translation(-pw)@mw@pb.matrix
            pb.rotation_mode='QUATERNION'; pb.keyframe_insert('rotation_quaternion',frame=fr); bpy.context.view_layer.update(); P=pose()
    after=0
    for fr in range(f0,f1+1):
        sc.frame_set(fr); P=pose(); legs=np.unique(K(P[Cl=='leg']))
        after=max(after,max(int(np.isin(K(P[amask[s]]),legs).sum()) for s in HB))
    res[cl]={'before':b00,'after':after,'iters':it+1}; print('HC2',cl,res[cl],flush=True)
json.dump(res,open(OUT.replace('.glb','.handclear2.json'),'w'),indent=1)
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
