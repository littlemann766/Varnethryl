# copy all actions from LOD0 final blend onto a LOD glb's rig, export
import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]; lodglb,src,out=a
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
bpy.ops.import_scene.gltf(filepath=lodglb)
for x in list(bpy.data.actions): bpy.data.actions.remove(x)
with bpy.data.libraries.load(src) as (fr,to): to.actions=list(fr.actions)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
miss=set()
for act in bpy.data.actions:
    act.use_fake_user=True
    for fc in list(act.fcurves):
        if fc.data_path.startswith('pose.bones["'):
            b=fc.data_path.split('"')[1]
            if b not in arm.pose.bones: miss.add(b); act.fcurves.remove(fc)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
if arm.animation_data is None: arm.animation_data_create()
arm.animation_data.action=bpy.data.actions.get('idle') or bpy.data.actions[0]
print('LODCOPY',len(bpy.data.actions),'missing bones',sorted(miss))
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
