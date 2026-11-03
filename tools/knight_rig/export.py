import bpy,sys,json
G=sys.argv[-1]; OUT=f'/tmp/kr/{G}'
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/stage3.blend')
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; ARM.data.pose_position='REST'
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
ARM.animation_data_clear()
for c in [c for pb in ARM.pose.bones for c in pb.constraints]: pass
for n in list(fig.data.attributes):
    if n.name in ('part','blended'): pass
for i in fig.data.images if hasattr(fig.data,'images') else []: pass
for im in bpy.data.images:
    if im.size[0]>1024: im.scale(1024,1024)
mat=[m for m in fig.data.materials if m.name!='gambeson'][0]; nt=mat.node_tree
img=bpy.data.images.load('/tmp/kr/base.jpg'); img.scale(1024,1024)
bs=[n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'][0]
tex=[n for n in nt.nodes if n.type=='TEX_IMAGE' and any(l.to_socket.name=='Base Color' for l in n.outputs['Color'].links)]
if tex: tex[0].image=img
else:
    t=nt.nodes.new('ShaderNodeTexImage'); t.image=img; nt.links.new(t.outputs['Color'],bs.inputs['Base Color'])
bs.inputs['Metallic'].default_value=0.65; bs.inputs['Roughness'].default_value=0.38
for n in list(nt.nodes):
    if n.type=='TEX_IMAGE' and not any(l.to_socket.name=='Base Color' for l in n.outputs['Color'].links): nt.nodes.remove(n)
def export(o,path):
    for x in bpy.data.objects: x.select_set(False)
    o.select_set(True); ARM.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path,use_selection=True,export_animations=False,export_skins=True,export_image_format='JPEG',export_image_quality=88,export_attributes=False)
nh=sum(len(p.vertices)-2 for p in fig.data.polygons); export(fig,f'{OUT}/knight_{G}.glb')
lo=fig.copy(); lo.data=fig.data.copy(); bpy.context.collection.objects.link(lo)
for x in bpy.data.objects: x.select_set(False)
bpy.context.view_layer.objects.active=lo; lo.select_set(True)
d=lo.modifiers.new('d','DECIMATE'); d.ratio=0.45; bpy.ops.object.modifier_move_to_index(modifier='d',index=0); bpy.ops.object.modifier_apply(modifier='d')
# keep lod1 rigid: snap every vertex to its strongest bone
cloth=set(v for p in lo.data.polygons if lo.data.materials[p.material_index].name=='gambeson' for v in p.vertices)
for v in lo.data.vertices:
    if len(v.groups)>1 and v.index not in cloth:
        g=max(v.groups,key=lambda g:g.weight).group
        for gg in list(v.groups):
            if gg.group!=g: lo.vertex_groups[gg.group].remove([v.index])
        lo.vertex_groups[g].add([v.index],1.0,'REPLACE')
nl=sum(len(p.vertices)-2 for p in lo.data.polygons); export(lo,f'{OUT}/knight_{G}_lod1.glb')
nu=sum(1 for p in fig.data.polygons if fig.data.materials[p.material_index].name=='gambeson')
json.dump({'under_faces_high':nu,'high_tris':nh,'lod1_tris':nl,'ratio':round(nl/nh,3),'bones':len(ARM.data.bones)},open(f'{OUT}/knight_{G}_tris.json','w'))
print('EXPORT',G,nh,nl,len(ARM.data.bones))
