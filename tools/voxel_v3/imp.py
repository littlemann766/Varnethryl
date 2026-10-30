import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
bpy.ops.import_scene.gltf(filepath=a[0])
for x in bpy.data.actions: x.name=x.name[:x.name.rindex('_',0,x.name.rindex('_'))] if x.name.count('_')>=2 and x.name.endswith('_Rig') else x.name
print('ACTS',[x.name for x in bpy.data.actions])
bpy.ops.wm.save_as_mainfile(filepath=a[1])
