# after landing: shrink cape bone patches (uniform scale about bone head) only as much as needed so no cube goes under the floor or into body/leg cells
import bpy,sys,os,re
import numpy as np
from mathutils import Matrix
a=sys.argv[sys.argv.index('--')+1:]; blend,an,out=a[0],a[1],a[2]; DF=int(os.environ.get('DF','22'))
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
me=ob.data; n=len(me.vertices); S=0.018
co=np.empty(n*3); me.vertices.foreach_get('co',co); co=np.c_[co.reshape(-1,3),np.ones(n)]
W=(np.array(ob.matrix_world)@co.T).T
gi=np.array([max(v.groups,key=lambda g:g.weight).group if v.groups else -1 for v in me.vertices])
gname={g.index:g.name for g in ob.vertex_groups}
def cls(nm):
    l=nm.lower().replace('mixamorig:','')
    if l.startswith('cape'): return 'cape'
    if any(t in l for t in ('upperarm','forearm','leftarm','rightarm','hand','fingers','index','middle','ring','pinky','thumb','weapon')): return 'arm'
    if any(t in l for t in ('thigh','shin','foot','toe','upleg','leftleg','rightleg')): return 'leg'
    if l.startswith(('hair','coat','hood','tail')): return 'other'
    return 'body'
C=np.array([cls(gname.get(g,'')) for g in gi])
groups=[(g,nm) for g,nm in gname.items() if nm in arm.pose.bones]
mw=np.array(arm.matrix_world); mwi=np.linalg.inv(mw)
def pose_pts(idx_names):
    P=np.zeros((n,3))
    for g,nm in idx_names:
        M=mw@np.array(arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted())@mwi
        idx=gi==g; P[idx]=(M@W[idx].T).T[:,:3]
    return P
pat=re.compile(r'capeV_c(\d+)_r(\d+)')
cb=sorted([(int(m.group(2)),int(m.group(1)),nm) for nm in arm.pose.bones.keys() for m in [pat.fullmatch(nm)] if m])
gidx={nm:g for g,nm in gname.items()}
arm.animation_data.action=None
for pb in arm.pose.bones: pb.matrix_basis=Matrix()
bpy.context.view_layer.update()
P=pose_pts(groups); T=np.floor(P/S).astype(int)
occ=set(map(tuple,T[(C=='body')|(C=='leg')]))
base_in={nm:set(np.where([tuple(t) in occ for t in T[gi==gidx[nm]]])[0]) for _,_,nm in cb if nm in gidx}
A=bpy.data.actions[an]; arm.animation_data.action=A; f0,f1=[int(round(x)) for x in A.frame_range]
GZ=-0.004; stats=[]
for f in range(max(f0,DF),f1+1):
    sc.frame_set(f)
    for _,_,nm in cb: arm.pose.bones[nm].scale=(1,1,1)
    bpy.context.view_layer.update()
    P=pose_pts(groups); T=np.floor(P/S).astype(int)
    occ=set(map(tuple,T[(C=='body')|(C=='leg')]))
    Ms={nm:arm.pose.bones[nm].matrix.copy() for _,_,nm in cb}
    sc_={}
    for _,_,nm in cb:
        if nm not in gidx: sc_[nm]=1.0; continue
        idx=np.where(gi==gidx[nm])[0]
        if len(idx)==0: sc_[nm]=1.0; continue
        h=np.array(arm.matrix_world@arm.pose.bones[nm].head)
        V=P[idx]
        def cost(s):
            Q=h+(V-h)*s
            fl=max(0.0,GZ-Q[:,2].min())
            t=np.floor(Q/S).astype(int); bi=base_in.get(nm,())
            bad=sum(1 for k,x in enumerate(map(tuple,t)) if x in occ and k not in bi)
            return (round(fl,2), bad, -s)
        cands=[1.0,0.85,0.7,0.55,0.4,0.3,0.2,0.12,0.06]
        sc_[nm]=min(cands,key=cost)
    for _,_,nm in cb:
        pb=arm.pose.bones[nm]; s=sc_[nm]
        pb.matrix=Ms[nm]@Matrix.Diagonal((s,s,s,1)); bpy.context.view_layer.update()
        pb.keyframe_insert('location',frame=f); pb.keyframe_insert('rotation_quaternion',frame=f); pb.keyframe_insert('scale',frame=f)
    stats.append(min(sc_.values()))
# key scale=1 on frame DF-1 so earlier frames unaffected
sc.frame_set(DF-1)
for _,_,nm in cb:
    pb=arm.pose.bones[nm]; pb.scale=(1,1,1); pb.keyframe_insert('scale',frame=DF-1)
print('DROPFIX min scale per frame',[round(x,2) for x in stats])
bpy.ops.wm.save_as_mainfile(filepath=out)
