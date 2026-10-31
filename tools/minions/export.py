import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]; blend,keep,out=a[0],a[1],a[2]
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name!=keep: bpy.data.objects.remove(o)
    elif o.type not in ('MESH','ARMATURE'): bpy.data.objects.remove(o)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
arm.animation_data.action=bpy.data.actions['idle']; sc.frame_set(0)
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_vertex_color='ACTIVE',export_def_bones=True,export_optimize_animation_size=False)
print('EXPORTED',out)
