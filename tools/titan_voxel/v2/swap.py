import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]; src,actsrc,out=a
if src.endswith('.blend'): bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.ops.import_scene.gltf(filepath=src)
bpy.context.scene.render.fps=30
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
for x in list(bpy.data.actions): bpy.data.actions.remove(x)
with bpy.data.libraries.load(actsrc) as (f,t): t.actions=list(f.actions)
for x in bpy.data.actions: x.use_fake_user=True
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; arm.animation_data_create(); arm.animation_data.action=bpy.data.actions['wb_idle']
print('ACTS',len(bpy.data.actions))
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
