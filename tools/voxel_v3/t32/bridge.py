# replace keys a..b of bones in a clip by slerp between keys a-1 and b+1 (removes a short kick + snap)
import bpy,sys,json,os
from mathutils import Quaternion
x=sys.argv[sys.argv.index('--')+1:]; src,out,clip,bones,a,b=x[0],x[1],x[2],x[3].split(','),int(x[4]),int(x[5])
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
bpy.ops.import_scene.gltf(filepath=src)
for ac in bpy.data.actions: ac.name=ac.name[:ac.name.rindex('_',0,ac.name.rindex('_'))] if ac.name.count('_')>=2 and ac.name.endswith('_Rig') else (ac.name[:-9] if ac.name.endswith('_Armature') else ac.name)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; act=bpy.data.actions[clip]
for bn in bones:
    fcs=[act.fcurves.find('pose.bones["%s"].rotation_quaternion'%bn,index=k) for k in range(4)]
    q0=Quaternion([f.keyframe_points[a-1].co[1] for f in fcs]); q1=Quaternion([f.keyframe_points[b+1].co[1] for f in fcs])
    if q0.dot(q1)<0: q1.negate()
    for t in range(a,b+1):
        q=q0.slerp(q1,(t-a+1)/(b-a+2))
        for k,f in enumerate(fcs):
            p=f.keyframe_points[t]; p.co[1]=q[k]; p.handle_left[1]=q[k]; p.handle_right[1]=q[k]
    for f in fcs: f.update()
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
for ac in bpy.data.actions: ac.use_fake_user=True
arm.animation_data.action=bpy.data.actions['idle']
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
print('BRIDGED',clip,bones,a,b)
