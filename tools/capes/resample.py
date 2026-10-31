# Re-key every clip at 30 fps (one key per frame), keeping clip length in seconds. usage: blender -b -P resample.py -- in.glb out.glb
import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.context.scene.render.fps_base=1
bpy.ops.import_scene.gltf(filepath=a[0])
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_yup=True,export_skins=True,export_apply=False)
