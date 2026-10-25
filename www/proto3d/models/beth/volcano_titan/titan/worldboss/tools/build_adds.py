# Ash Fiend (2.4 m melee add, A-pose, rig-ready single mesh) and Ember Wisp (1.3 m floating fire spirit).
# Game convention: +Z forward in glTF/Godot (Titan toes point +Z) => Blender -Y forward.
# Vertex colour: R = ember-crack mask, G = ash/char variation, B = heat (0..1). Use shaders/wb_add_lava.gdshader.
import bpy, bmesh, math, random, os
from mathutils import Vector, noise
OUT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
def reset(): bpy.ops.wm.read_factory_settings(use_empty=True)
def mb_elem(mb,co,r,kind='BALL',size=None,rot=None,stiff=2.0):
    e=mb.elements.new(); e.type=kind; e.co=co; e.radius=r; e.stiffness=stiff
    if size: e.size_x,e.size_y,e.size_z=size
    if rot: e.rotation=rot
    return e
def capsule_chain(mb,pts,rads):
    for (a,ra),(b,rb) in zip(zip(pts,rads),zip(pts[1:],rads[1:])):
        a=Vector(a); b=Vector(b); n=max(2,int((b-a).length/0.06))
        for i in range(n+1): mb_elem(mb,a.lerp(b,i/n),ra+(rb-ra)*i/n)
def to_mesh(obj,voxel):
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    bpy.ops.object.convert(target='MESH'); m=bpy.context.object
    mod=m.modifiers.new('r','REMESH'); mod.mode='VOXEL'; mod.voxel_size=voxel; bpy.ops.object.modifier_apply(modifier='r')
    return m
def cells(p,pts):
    d=sorted((p-q).length for q in pts[:]); return d[1]-d[0]
def sculpt_and_paint(m,disp,crack_w,seed,crack_bias):
    rnd=random.Random(seed); bm=bmesh.new(); bm.from_mesh(m.data); bm.normal_update()
    lo=Vector(m.bound_box[0]); hi=Vector(m.bound_box[6])
    pts=[Vector((rnd.uniform(lo.x,hi.x),rnd.uniform(lo.y,hi.y),rnd.uniform(lo.z,hi.z))) for _ in range(int(420*(hi-lo).length))]
    col=bm.loops.layers.color.new('Col'); vals={}
    from mathutils.kdtree import KDTree
    kd=KDTree(len(pts)); [kd.insert(p,i) for i,p in enumerate(pts)]; kd.balance()
    for v in bm.verts:
        p=v.co.copy(); n=v.normal.copy()
        rock=noise.fractal(p*6.0,0.6,2.0,4)*0.6+noise.noise(p*22.0)*0.25
        nn=kd.find_n(p,2); f=nn[1][2]-nn[0][2]
        crack=max(0.0,1.0-f/crack_w)*(0.6+0.4*noise.noise(p*9))*crack_bias(p)
        # plates bulge, cracks sink
        v.co=p+n*(disp*(0.5+0.5*rock) - disp*1.6*crack)
        vals[v.index]=(min(1,crack*1.4), 0.5+0.5*noise.noise(p*4.0), max(0.0,min(1,0.3+0.7*crack_bias(p))))
    for f in bm.faces:
        for l in f.loops: c=vals[l.vert.index]; l[col]=(c[0],c[1],c[2],1)
    bm.to_mesh(m.data); bm.free()
def material(m,name,emis_col):
    mat=bpy.data.materials.new(name); mat.use_nodes=True; nt=mat.node_tree; b=nt.nodes['Principled BSDF']
    vc=nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name='Col'
    sep=nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(vc.outputs['Color'],sep.inputs[0])
    mix=nt.nodes.new('ShaderNodeMix'); mix.data_type='RGBA'; nt.links.new(sep.outputs[0],mix.inputs[0])
    mix.inputs[6].default_value=(0.06,0.05,0.045,1); mix.inputs[7].default_value=(*emis_col,1)
    nt.links.new(mix.outputs[2],b.inputs['Base Color']); b.inputs['Roughness'].default_value=0.92
    m.data.materials.clear(); m.data.materials.append(mat)
def export(m,name,lod_ratio):
    ca=m.data.color_attributes
    for a in [a.name for a in ca if a.name!='Col']: ca.remove(ca[a])
    ca.active_color=ca['Col']; ca.render_color_index=ca.active_color_index
    for a in [a.name for a in m.data.uv_layers]: m.data.uv_layers.remove(m.data.uv_layers[a])
    bpy.ops.object.select_all(action='DESELECT'); m.select_set(True); bpy.context.view_layer.objects.active=m
    bpy.ops.object.shade_smooth()
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/{name}.glb',export_format='GLB',export_yup=True,use_selection=True,export_vertex_color='ACTIVE' if bpy.app.version>=(4,2,0) else None) if False else bpy.ops.export_scene.gltf(filepath=f'{OUT}/{name}.glb',export_format='GLB',export_yup=True,use_selection=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
    print(name,len(m.data.polygons))
    d=m.modifiers.new('d','DECIMATE'); d.ratio=lod_ratio; bpy.ops.object.modifier_apply(modifier='d')
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/{name}_lod1.glb',export_format='GLB',export_yup=True,use_selection=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
    print(name+'_lod1',len(m.data.polygons))
def fiend():
    reset(); mbd=bpy.data.metaballs.new('f'); mbd.resolution=0.03; mbd.threshold=0.6
    o=bpy.data.objects.new('wb_ash_fiend',mbd); bpy.context.scene.collection.objects.link(o)
    F=-1 # forward = -Y in Blender
    # torso: hunched, broad chest, narrow waist
    capsule_chain(mbd,[(0,0,1.0),(0,0.02*F,1.25),(0,0.08*F,1.55),(0,0.14*F,1.78)],[0.22,0.24,0.32,0.30])
    for s in (-1,1):
        mb_elem(mbd,(s*0.24,0.10*F,1.62),0.24)            # pecs/lats
        mb_elem(mbd,(s*0.34,0.0,1.78),0.2)                 # traps/shoulder
    # head: low-slung, heavy brow, jaw
    capsule_chain(mbd,[(0,0.16*F,1.82),(0,0.28*F,1.98)],[0.12,0.1])
    mb_elem(mbd,(0,0.34*F,2.02),0.17); mb_elem(mbd,(0,0.44*F,1.95),0.11); mb_elem(mbd,(0,0.40*F,2.08),0.12)
    for s in (-1,1):
        mb_elem(mbd,(s*0.09,0.48*F,2.07),0.06)             # brow ridge
        # horns sweeping back
        capsule_chain(mbd,[(s*0.12,0.34*F,2.15),(s*0.22,0.26*F,2.32),(s*0.28,0.08*F,2.42),(s*0.27,-0.08*F,2.38)],[0.07,0.055,0.035,0.015])
        # A-pose arms ~40 deg down, long, gorilla-ish
        sh=Vector((s*0.46,0.04*F,1.80)); el=Vector((s*0.80,0.06*F,1.42)); wr=Vector((s*1.05,0.12*F,1.06))
        capsule_chain(mbd,[sh,(sh+el)/2,el],[0.17,0.15,0.12]); capsule_chain(mbd,[el,(el+wr)/2,wr],[0.12,0.13,0.09])
        mb_elem(mbd,sh+Vector((0,0,0.06)),0.2)
        hand=wr+Vector((s*0.08,0.02*F,-0.08)); mb_elem(mbd,hand,0.1)
        for k in range(4):   # splayed fingers -> claws
            a=(k-1.5)*0.35; base=hand+Vector((s*0.05,F*0.06*math.sin(a),-0.05)); tip=base+Vector((s*0.08,F*0.12*math.sin(a)+F*0.02,-0.2))
            capsule_chain(mbd,[base,tip],[0.04,0.012])
        # legs: digitigrade-ish, wide stance
        hp=Vector((s*0.18,0,0.98)); kn=Vector((s*0.26,0.12*F,0.55)); an=Vector((s*0.30,-0.06*F,0.16))
        capsule_chain(mbd,[hp,(hp+kn)/2,kn],[0.17,0.17,0.12]); capsule_chain(mbd,[kn,(kn+an)/2,an],[0.12,0.1,0.08])
        for k in range(3):
            a=(k-1)*0.4; capsule_chain(mbd,[an+Vector((0,0,-0.08)),an+Vector((s*0.1*math.sin(a),0.26*F,-0.13))],[0.07,0.03])
    # back spikes / ash shards along spine
    for k in range(6):
        b=Vector((0,0.06+0.03*k,1.15+k*0.13)); capsule_chain(mbd,[b,b+Vector((0,0.14+0.02*k,0.1))],[0.06,0.01])
    m=to_mesh(o,0.012)
    chest_hot=lambda p: 0.85+0.7*max(0.0,1.0-((p-Vector((0,-0.2,1.55))).length/0.6))
    sculpt_and_paint(m,0.022,0.03,7,chest_hot)
    material(m,'ash_fiend',(1.0,0.45,0.08)); m.name='wb_ash_fiend'
    export(m,'wb_ash_fiend',0.08)
def wisp():
    reset(); mbd=bpy.data.metaballs.new('w'); mbd.resolution=0.02; mbd.threshold=0.6
    o=bpy.data.objects.new('wb_ember_wisp',mbd); bpy.context.scene.collection.objects.link(o)
    F=-1; rnd=random.Random(5)
    mb_elem(mbd,(0,0,0),0.34)
    # flame tongues spiralling up, leaning back (trail behind = +Y in blender = -Z game)
    for k in range(11):
        a=k*2.39; r=0.16+0.06*(k%3); L=0.55+0.35*rnd.random(); pts=[]; rad=[]
        for t in range(8):
            u=t/7; pts.append((math.cos(a+u*1.6)*r*(1+0.6*u),math.sin(a+u*1.6)*r*(1+0.6*u)-F*0.18*u*u,0.12+u*L)); rad.append(0.13*(1-u)+0.015)
        capsule_chain(mbd,pts,rad)
    for k in range(5):  # side flares (arms)
        s_=1 if k%2 else -1; capsule_chain(mbd,[(s_*0.25,0,0.0),(s_*0.5,-F*0.05,0.2+0.08*k),(s_*0.6,-F*0.12,0.42+0.06*k)],[0.1,0.06,0.015])
    # ember trail streaming behind/below
    for k in range(14):
        t=k/13; ox=0.08*math.sin(t*9); capsule_chain(mbd,[(ox,-F*(0.2+t*0.9),-0.15-t*0.45),(ox,-F*(0.24+t*0.9),-0.17-t*0.45)],[0.13*(1-t)+0.015,0.12*(1-t)+0.012])
    m=to_mesh(o,0.012)
    bm=bmesh.new(); bm.from_mesh(m.data); col=bm.loops.layers.color.new('Col')
    for f in bm.faces:
        for l in f.loops:
            p=l.vert.co; r=p.length; heat=max(0,1-r/0.55)
            l[col]=(1.0, 0.5+0.5*noise.noise(p*6), heat, 1)
    # face: two eye sockets on +Z(game) side
    bm.to_mesh(m.data); bm.free()
    # orbiting obsidian shards (separate parts of same mesh)
    for k in range(7):
        a=k*6.283/7; bpy.ops.mesh.primitive_cone_add(vertices=5,radius1=0.06,depth=0.22,location=(math.cos(a)*0.62,math.sin(a)*0.62,0.05+0.12*math.sin(a*2)),rotation=(rnd.random(),rnd.random(),a))
        s=bpy.context.object; bm=bmesh.new(); bm.from_mesh(s.data); c=bm.loops.layers.color.new('Col')
        for f in bm.faces:
            for l in f.loops: l[c]=(0.0,0.2,0.0,1)
        bm.to_mesh(s.data); bm.free()
        s.select_set(True); m.select_set(True); bpy.context.view_layer.objects.active=m; bpy.ops.object.join()
    for s in (-1,1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=0.05,location=(s*0.11,F*0.33,0.1)); e=bpy.context.object; e.scale=(1.3,0.5,0.6)
        bm=bmesh.new(); bm.from_mesh(e.data); c=bm.loops.layers.color.new('Col')
        for f in bm.faces:
            for l in f.loops: l[c]=(1,1,1,1)
        bm.to_mesh(e.data); bm.free(); bpy.ops.object.transform_apply(scale=True)
        e.select_set(True); m.select_set(True); bpy.context.view_layer.objects.active=m; bpy.ops.object.join()
    material(m,'ember_wisp',(1.0,0.6,0.15)); m.name='wb_ember_wisp'
    export(m,'wb_ember_wisp',0.15)
fiend(); wisp()
