# ground-snap the fall: from frame F0 on, move hips so the lowest non-cape vertex sits on the floor (both directions), smoothed
import bpy,sys,os
import numpy as np
a=sys.argv[sys.argv.index('--')+1:]; blend,an,out=a[0],a[1],a[2]; F0=int(os.environ.get('F0','20')); RAMP=6
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
gn={g.index:g.name for g in ob.vertex_groups}
BODY=np.ones(len(ob.data.vertices),bool) if os.environ.get('ALLV') else np.array([not (v.groups and gn[max(v.groups,key=lambda q:q.weight).group].startswith('cape')) for v in ob.data.vertices])
H=[b.name for b in arm.pose.bones if b.name.lower().endswith('hips')][0]
def minz():
    e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m=e.to_mesh(); n=len(m.vertices)
    c=np.empty(n*3); m.vertices.foreach_get('co',c); W=np.array(ob.matrix_world); z=(c.reshape(-1,3)@W[:3,:3].T+W[:3,3])[:,2]; e.to_mesh_clear(); return z[BODY[:n]].min()
arm.animation_data.action=None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update(); G=minz()+0.006; OFF=float(os.environ.get('OFF','0')); F1=int(os.environ.get('F1','9999'))
A=bpy.data.actions[an]; arm.animation_data.action=A; f1=int(A.frame_range[1])
for it in range(3):
    dz=np.zeros(f1+1)
    for f in range(F0-RAMP,f1+1): sc.frame_set(f); dz[f]=minz()-G-(OFF*min(1,max(0,(f-F1)/6)))
    w=np.clip((np.arange(f1+1)-(F0-RAMP))/RAMP,0,1); d=dz*w
    d=np.convolve(np.pad(d,2,mode='edge'),np.ones(5)/5,'valid') if it==0 else d
    print('DZ',it,round(float(np.abs(dz[F0:]).max()),3),flush=True)
    if np.abs(dz[F0:]).max()<0.004: break
    pb=arm.pose.bones[H]
    for f in range(F0-RAMP,f1+1):
        if abs(d[f])<1e-4: continue
        sc.frame_set(f); M=arm.matrix_world@pb.matrix; M.translation.z-=d[f]
        pb.matrix=arm.matrix_world.inverted()@M; bpy.context.view_layer.update(); pb.keyframe_insert('location',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=out)
