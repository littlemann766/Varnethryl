# Keep mesh/skin/rig of target, replace ALL its clips with donor's (same bone names). usage: blender -b -P swapclips.py -- target.glb donor.glb out.glb
import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=a[0]); keep=set(bpy.data.objects); arm=[o for o in keep if o.type=='ARMATURE'][0]
for ac in list(bpy.data.actions): bpy.data.actions.remove(ac)
if arm.animation_data: arm.animation_data_clear()
bpy.ops.import_scene.gltf(filepath=a[1]); darm=[o for o in bpy.data.objects if o not in keep and o.type=='ARMATURE'][0]; dn=darm.name
miss=[b.name for b in darm.data.bones if b.name not in arm.data.bones]
for o in [o for o in bpy.data.objects if o not in keep]: bpy.data.objects.remove(o)
ad=arm.animation_data_create(); n=[]
for ac in list(bpy.data.actions):
    cl=ac.name.replace('_'+dn,''); ac.name=cl+'_'+arm.name; ac.use_fake_user=True
    tr=ad.nla_tracks.new(); tr.name=cl; tr.strips.new(cl,int(ac.frame_range[0]),ac); n.append(cl)
print('SWAP',len(n),'missing_bones',miss)
bpy.ops.export_scene.gltf(filepath=a[2],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
