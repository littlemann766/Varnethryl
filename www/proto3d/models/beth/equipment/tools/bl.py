import bpy, math, numpy as np, sys
sys.path.insert(0,'/workspace/godot-art/loot3_tools')
from vox import faces
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
MATS={}
def mat(glow):
    if glow in MATS: return MATS[glow]
    m=bpy.data.materials.new("vox_glow" if glow else "vox"); m.use_nodes=True; nt=m.node_tree; b=nt.nodes["Principled BSDF"]
    ca=nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name="Col"; nt.links.new(ca.outputs[0],b.inputs["Base Color"])
    b.inputs["Roughness"].default_value=0.75
    if glow: nt.links.new(ca.outputs[0],b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value=1.2
    MATS[glow]=m; return m
def mesh(v,name,vs,center=True,origin=None):
    q=faces(v); verts=[];fs=[];cols=[];mi=[]
    sh=np.array(v.g.shape); off=-(sh*vs)/2.0; off[2]=0
    if origin is not None: off=np.array(origin)
    for (p,d,ci) in q:
        p=np.array(p,float); ax=[i for i in range(3) if d[i]!=0][0]; s=d[ax]
        o=[i for i in range(3) if i!=ax]; base=p.copy(); base[ax]+=1 if s>0 else 0
        cs=[]
        for a,b in [(0,0),(1,0),(1,1),(0,1)]:
            c=base.copy(); c[o[0]]+=a; c[o[1]]+=b; cs.append(c)
        if (s>0)!=(ax==1): cs=cs[::-1]
        i0=len(verts); verts+= [tuple(c*vs+off) for c in cs]; fs.append((i0,i0+1,i0+2,i0+3))
        rgb,glow=v.pal[ci]; shade=[0.82,0.82,0.9,0.9,1.0,0.7][[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)].index(tuple(d))]
        cols.append(tuple(min(1,(c*(1 if glow else shade))**2.2) for c in rgb)+(1,)); mi.append(1 if glow else 0)
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],fs); me.update()
    ca=me.color_attributes.new("Col",'FLOAT_COLOR','CORNER')
    for f,c in zip(me.polygons,cols):
        for li in f.loop_indices: ca.data[li].color=c
    me.materials.append(mat(0)); me.materials.append(mat(1))
    for f,m in zip(me.polygons,mi): f.material_index=m
    ob=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=vs*0.01); bpy.ops.object.mode_set(mode='OBJECT')
    return ob, len(fs)*2
def export(path,objs,anim=False):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path,use_selection=True,export_format='GLB',export_animations=anim,export_apply=False)
def rig_scene(res=256, ortho=0.5, el=28, yaw=32, target=(0,0,0.2)):
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=48; sc.cycles.device='CPU'
    sc.render.resolution_x=sc.render.resolution_y=res; sc.render.film_transparent=True
    sc.view_settings.view_transform='Standard'
    w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[1].default_value=0.9
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.75,0.72,0.68,1)
    cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=ortho; cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
    r=3; e=math.radians(90-el); y=math.radians(yaw)
    cam.location=(target[0]+r*math.sin(e)*math.sin(y), target[1]-r*math.sin(e)*math.cos(y), target[2]+r*math.cos(e))
    cam.rotation_euler=(e,0,y)
    ld=bpy.data.lights.new("s",'SUN'); ld.energy=3.2; ld.angle=0.2; l=bpy.data.objects.new("s",ld); l.rotation_euler=(math.radians(40),math.radians(15),math.radians(-35)); sc.collection.objects.link(l)
    return cam
SRGB=True   # Equipment v1 polish 4: COLOR_0 holds sRGB values; Godot material uses vertex_color_is_srgb=true (correct in Mobile/Forward+ AND Compatibility)
def mesh_g(v,name,vs,origin):
    """greedy-meshed variant of mesh() (same colours/shading/materials)"""
    import greedy
    q=greedy.quads(v.g); verts=[];fs=[];cols=[];mi=[]; off=np.array(origin)
    SH={(1,0,0):0.82,(-1,0,0):0.82,(0,1,0):0.9,(0,-1,0):0.9,(0,0,1):1.0,(0,0,-1):0.7}
    for cs,d,ci in q:
        ax=[i for i in range(3) if d[i]!=0][0]; s=d[ax]
        cs=[np.array(c,float) for c in cs]
        # orient CCW seen from outside
        n=np.cross(cs[1]-cs[0],cs[2]-cs[0])
        if np.dot(n,np.array(d))<0: cs=cs[::-1]
        i0=len(verts); verts+=[tuple(c*vs+off) for c in cs]; fs.append((i0,i0+1,i0+2,i0+3))
        rgb,glow=v.pal[ci]; sh=SH[tuple(d)]
        cols.append(tuple(min(1,(c*(1 if glow else sh))**(1.0 if SRGB else 2.2)) for c in rgb)+(1,)); mi.append(1 if glow else 0)
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],fs); me.update()
    ca=me.color_attributes.new("Col",'FLOAT_COLOR','CORNER')
    for f,c in zip(me.polygons,cols):
        for li in f.loop_indices: ca.data[li].color=c
    me.materials.append(mat(0)); me.materials.append(mat(1))
    for f,m in zip(me.polygons,mi): f.material_index=m
    ob=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(ob)
    return ob,len(fs)*2
def srgb_fix_imported(objs):
    """for Blender renders of sRGB-COLOR_0 glbs: insert a 2.2 gamma between the colour attribute and the BSDF"""
    for o in objs:
        for sl in getattr(o,'material_slots',[]):
            m=sl.material
            if not m or not m.use_nodes or m.get('srgbfix'): continue
            nt=m.node_tree
            for l in list(nt.links):
                if l.from_node.bl_idname in('ShaderNodeVertexColor','ShaderNodeAttribute') and l.to_socket.name in('Base Color','Emission Color'):
                    g=nt.nodes.new('ShaderNodeGamma'); g.inputs[1].default_value=2.2
                    fs,ts=l.from_socket,l.to_socket; nt.links.remove(l); nt.links.new(fs,g.inputs[0]); nt.links.new(g.outputs[0],ts)
            m['srgbfix']=1
FLAT_FACES=False   # crisp per-face colour on the smoothed surface (Godot interpolates per-vertex colour into mush)
def smooth_plate(ob,v,vs,origin,tri_mult=99,rem=1.0,iters=2,fac=0.5):
    """polish: kill the voxel stair-steps on plate. remesh -> smooth -> decimate, then re-colour every face straight from the voxel grid
    (sample just inside the surface along -normal) so trim lines and rivets stay crisp. glow voxels keep material 1."""
    t0=sum(len(p.vertices)-2 for p in ob.data.polygons)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    m=ob.modifiers.new("r",'REMESH'); m.mode='VOXEL'; m.voxel_size=vs*rem; m.adaptivity=0; bpy.ops.object.modifier_apply(modifier="r")
    m=ob.modifiers.new("s",'SMOOTH'); m.factor=fac; m.iterations=iters; bpy.ops.object.modifier_apply(modifier="s")
    t1=sum(len(p.vertices)-2 for p in ob.data.polygons)
    if t1>t0*tri_mult:
        m=ob.modifiers.new("d",'DECIMATE'); m.ratio=t0*tri_mult/t1; bpy.ops.object.modifier_apply(modifier="d")
    me=ob.data; g=v.g; off=np.array(origin); S=np.array(g.shape); me.update()
    for a in list(me.color_attributes): me.color_attributes.remove(a)
    ca=me.color_attributes.new("Col",'FLOAT_COLOR','CORNER')
    if len(me.materials)<2: me.materials.clear(); me.materials.append(mat(0)); me.materials.append(mat(1))
    from mathutils.kdtree import KDTree
    pad=np.pad(g>0,1); core=pad[1:-1,1:-1,1:-1]&pad[2:,1:-1,1:-1]&pad[:-2,1:-1,1:-1]&pad[1:-1,2:,1:-1]&pad[1:-1,:-2,1:-1]&pad[1:-1,1:-1,2:]&pad[1:-1,1:-1,:-2]
    surf=np.argwhere((g>0)&~core); kd=KDTree(len(surf))
    for i,q in enumerate(surf): kd.insert(tuple((q+0.5)*vs+off),i)
    kd.balance()
    vc=[]
    for vt in me.vertices:
        ci=0; co=np.array(vt.co); n=np.array(vt.normal)
        for d in (0.5,0.1,0.9):
            q=np.floor((co-n*vs*d-off)/vs).astype(int)
            if (q>=0).all() and (q<S).all() and g[tuple(q)]>0: ci=g[tuple(q)]; break
        if not ci: ci=g[tuple(surf[kd.find(vt.co)[1]])]
        vc.append(ci)
    for p in me.polygons:
        cs=[vc[me.loops[li].vertex_index] for li in p.loop_indices]; glow=any(v.pal[c][1] for c in cs)
        fc=max(set(cs),key=cs.count) if FLAT_FACES else None
        for li in p.loop_indices:
            rgb,gl=v.pal[fc or vc[me.loops[li].vertex_index]]; ca.data[li].color=tuple(min(1,x)**(1.0 if SRGB else 2.2) for x in rgb)+(1,)
        p.material_index=1 if glow and all(v.pal[c][1] for c in cs) else 0; p.use_smooth=True
    return ob,sum(len(p.vertices)-2 for p in me.polygons)
