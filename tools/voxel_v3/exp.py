import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere') or (o.type=='MESH' and o.parent!=arm): bpy.data.objects.remove(o)
arm.animation_data.action=bpy.data.actions['idle']
bpy.ops.wm.save_as_mainfile(filepath=a[1]+'.blend')
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
