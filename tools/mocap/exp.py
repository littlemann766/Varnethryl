import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
for o in bpy.data.objects:
    if o.type=='ARMATURE':
        for pb in o.pose.bones: pb.custom_shape=None
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
