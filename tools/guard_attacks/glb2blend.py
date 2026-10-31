import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=a[0])
for x in bpy.data.actions:
    if x.name.endswith('_Armature'): x.name=x.name[:-9]
bpy.ops.wm.save_as_mainfile(filepath=a[1])
