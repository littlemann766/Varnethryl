import bpy,numpy as np,sys
src,out,strength=sys.argv[-3],sys.argv[-2],float(sys.argv[-1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt=m.node_tree; b=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if b is None or not b.inputs['Base Color'].links: continue
    img=b.inputs['Base Color'].links[0].from_node.image
    W,H=img.size; px=np.array(img.pixels[:],np.float32).reshape(H,W,4)[...,:3]
    r,g,bb=px[...,0],px[...,1],px[...,2]
    mask=np.clip((r-np.maximum(g,bb)*1.05-0.12)*4,0,1)*np.clip((r-0.35)*3,0,1)   # orange/red lava cracks + eyes
    em=np.zeros((H,W,4),np.float32); em[...,0]=mask; em[...,1]=mask*0.42; em[...,2]=mask*0.08; em[...,3]=1
    ei=bpy.data.images.new('titan_emissive',W,H); ei.pixels=em.ravel(); ei.file_format='PNG'
    t=nt.nodes.new('ShaderNodeTexImage'); t.image=ei; ei.pack()
    nt.links.new(t.outputs[0],b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value=strength
    print('mask cover',float((mask>0.3).mean()))
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_image_format='AUTO',export_animations=True,export_skins=True)
