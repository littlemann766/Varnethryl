# rebuild the boss's original PBR material (glTF importer layout): base*0.8, ORM (G=rough,B=metal), normal map, specular 0.8
def setup_mat(me,tag='hi'):
    m=[x for x in me.materials][0]; nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); bs=nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0],out.inputs[0])
    def tex(p,non_color):
        t=nt.nodes.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(p,check_existing=True)
        if non_color: t.image.colorspace_settings.name='Non-Color'
        return t
    tb=tex('/tmp/kr/t_base.jpg',False); mul=nt.nodes.new('ShaderNodeMix'); mul.data_type='RGBA'; mul.blend_type='MULTIPLY'; mul.inputs[0].default_value=1.0
    mul.inputs[7].default_value=(0.8,0.8,0.8,1); nt.links.new(tb.outputs['Color'],mul.inputs[6]); nt.links.new(mul.outputs[2],bs.inputs['Base Color'])
    tr=tex('/tmp/kr/t_rm.jpg',True); sp=nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tr.outputs['Color'],sp.inputs[0])
    nt.links.new(sp.outputs[1],bs.inputs['Roughness']); nt.links.new(sp.outputs[2],bs.inputs['Metallic'])
    tn=tex('/tmp/kr/t_nrm.jpg',True); nm=nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'],nm.inputs['Color']); nt.links.new(nm.outputs[0],bs.inputs['Normal'])
    bs.inputs['Specular Tint'].default_value=(0.8,0.8,0.8,1)
    return m
