import bpy,sys,json,numpy as np
G=sys.argv[-1]; OUT=f'/tmp/kr/{G}'
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/stage3.blend')
exec(open('/tmp/kr/mat.py').read())
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; ARM.data.pose_position='POSE'
setup_mat(fig.data)
for x in [o for o in bpy.data.objects if o not in (ARM,fig)]: bpy.data.objects.remove(x)
for pb in ARM.pose.bones: pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0); pb.scale=(1,1,1)
acts=[a for a in bpy.data.actions]
ARM.animation_data_create()
# bake every clip with the helper/tabard/twist constraints evaluated (visual keying) so Godot gets plain bone tracks
baked=[]
for a in acts:
    ARM.animation_data.action=a
    try: ARM.animation_data.action_slot=a.slots[0]
    except Exception: pass
    f0,f1=[int(round(x)) for x in a.frame_range]
    for o in bpy.data.objects: o.select_set(False)
    ARM.select_set(True); bpy.context.view_layer.objects.active=ARM
    bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.nla.bake(frame_start=f0,frame_end=f1,only_selected=False,visual_keying=True,clear_constraints=False,use_current_action=False,bake_types={'POSE'})
    bpy.ops.object.mode_set(mode='OBJECT')
    nb=ARM.animation_data.action; nb.name=a.name.split('.')[0]+'_baked'; nb.use_fake_user=True; baked.append(nb)
for a in acts: bpy.data.actions.remove(a)
for pb in ARM.pose.bones:
    for c in list(pb.constraints): pb.constraints.remove(c)
for tr in list(ARM.animation_data.nla_tracks): ARM.animation_data.nla_tracks.remove(tr)
for b in baked: b.name=b.name.replace('_baked','')
for b in baked:   # push to NLA so the exporter writes every clip
    tr=ARM.animation_data.nla_tracks.new(); tr.name=b.name; st=tr.strips.new(b.name,int(b.frame_range[0]),b); tr.mute=True
ARM.animation_data.action=None
for pb in ARM.pose.bones: pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0); pb.scale=(1,1,1)
def export(o,path,anim=True):
    for x in bpy.data.objects: x.select_set(False)
    o.select_set(True); ARM.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path,use_selection=True,export_animations=anim,export_animation_mode='NLA_TRACKS',export_skins=True,export_image_format='JPEG',export_image_quality=92,export_attributes=False,export_force_sampling=True,export_frame_step=1)
ARM.data.pose_position='REST'
tri=lambda o:sum(len(p.vertices)-2 for p in o.data.polygons)
nh=tri(fig); export(fig,f'{OUT}/knight_{G}.glb')
lo=fig.copy(); lo.data=fig.data.copy(); bpy.context.collection.objects.link(lo)
for x in bpy.data.objects: x.select_set(False)
bpy.context.view_layer.objects.active=lo; lo.select_set(True)
d=lo.modifiers.new('d','DECIMATE'); d.ratio=0.45; bpy.ops.object.modifier_move_to_index(modifier='d',index=0); bpy.ops.object.modifier_apply(modifier='d')
# lod1: plate verts (dominant weight >0.9) snapped to one bone; seam-band verts keep their blend
sn=0
for v in lo.data.vertices:
    if len(v.groups)>1:
        g=max(v.groups,key=lambda g:g.weight)
        if g.weight>0.9:
            gi=g.group
            for gg in list(v.groups):
                if gg.group!=gi: lo.vertex_groups[gg.group].remove([v.index])
            lo.vertex_groups[gi].add([v.index],1.0,'REPLACE'); sn+=1
for x in bpy.data.objects: x.select_set(False)
fig.select_set(False); bpy.context.collection.objects.unlink(fig)
nl=tri(lo); export(lo,f'{OUT}/knight_{G}_lod1.glb')
json.dump({'high_tris':nh,'lod1_tris':nl,'ratio':round(nl/nh,3),'bones':len(ARM.data.bones),'clips':[b.name for b in baked],'textures':'2048 JPEG base/ORM/normal'},open(f'{OUT}/knight_{G}_tris.json','w'))
print('EXPORT',G,nh,nl,len(baked))
