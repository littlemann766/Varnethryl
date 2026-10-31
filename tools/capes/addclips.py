# Copy missing clips from a donor glb (same rig, e.g. LOD0) into a target (e.g. LOD1). usage: blender -b -P addclips.py -- target.glb donor.glb out.glb
import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=a[0]); keep=set(bpy.data.objects); arm=[o for o in keep if o.type=='ARMATURE'][0]; have={x.name.replace('_'+arm.name,'') for x in bpy.data.actions}
pre=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=a[1]); darm=[o for o in bpy.data.objects if o not in keep and o.type=='ARMATURE'][0]; dn=darm.name
for o in [o for o in bpy.data.objects if o not in keep]: bpy.data.objects.remove(o)
added=[]
for ac in list(bpy.data.actions):
    if ac in pre: continue
    cl=ac.name.replace('_'+dn,'')
    if cl in have: bpy.data.actions.remove(ac); continue
    ac.name=cl+'_'+arm.name; ac.use_fake_user=True
    tr=arm.animation_data_create().nla_tracks.new(); tr.name=cl; tr.strips.new(cl,int(ac.frame_range[0]),ac)
    added.append(cl)
print('ADDED',added)
bpy.ops.export_scene.gltf(filepath=a[2],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
