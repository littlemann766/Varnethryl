import bpy,sys,json,os
import numpy as np
a=sys.argv[sys.argv.index('--')+1:]; blend,acts,out=a
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
H='mixamorig:Hips' if 'mixamorig:Hips' in arm.data.bones else 'hips'
def minz():
    dg=bpy.context.evaluated_depsgraph_get(); e=ob.evaluated_get(dg); m=e.to_mesh()
    n=len(m.vertices); c=np.empty(n*3); m.vertices.foreach_get('co',c); c=c.reshape(-1,3)
    W=np.array(ob.matrix_world); z=(c@W[:3,:3].T+W[:3,3])[:,2]; e.to_mesh_clear(); return z.min()
arm.animation_data.action=None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update(); r=minz()-0.012
for an in acts.split(','):
    act=bpy.data.actions[an]; arm.animation_data.action=act; f1=int(act.frame_range[1])
    for it in range(3):
        dz=[]
        for f in range(0,f1+1): sc.frame_set(f); dz.append(max(0,r-minz()))
        print('DZ',an,it,round(max(dz),3))
        if max(dz)<0.002: break
        pb=arm.pose.bones[H]
        for f in range(0,f1+1):
            if dz[f]<=0: continue
            sc.frame_set(f); Mw=arm.matrix_world@pb.matrix; Mw.translation.z+=dz[f]+0.001
            pb.matrix=arm.matrix_world.inverted()@Mw; bpy.context.view_layer.update()
            pb.keyframe_insert('location',frame=f); pb.keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=out)
