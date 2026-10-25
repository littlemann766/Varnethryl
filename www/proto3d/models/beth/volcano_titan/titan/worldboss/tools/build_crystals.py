# Builds weak-point magma-crystal clusters (intact + broken, high + lod1). Unit = 1 m, +Y = out of the body, origin = socket on skin.
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix
OUT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name, col, emis, strength):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*col,1); b.inputs['Roughness'].default_value=0.35 if 'crystal' in name else 0.95
    b.inputs['Emission Color'].default_value=(*emis,1); b.inputs['Emission Strength'].default_value=strength
    return m
def shard(bm, base, axis, length, radius, sides, tipfrac, rnd, broken=False):
    axis=axis.normalized(); up=Vector((0,0,1))
    rot=up.rotation_difference(axis).to_matrix()
    rings=[]
    spin=rnd.random()*6.28
    hs=[0, length*0.15, length*(1-tipfrac)] if sides>5 else [0, length*(1-tipfrac)]
    for k,h in enumerate(hs):
        r=radius*(1.0+0.08*k if k<2 else 1.0)
        ring=[]
        for i in range(sides):
            a=spin+i*6.2831/sides; jr=r*(0.85+0.3*rnd.random())
            ring.append(bm.verts.new(base+rot@Vector((math.cos(a)*jr, math.sin(a)*jr, h))))
        rings.append(ring)
    for a,b in zip(rings,rings[1:]):
        for i in range(sides):
            bm.faces.new((a[i],a[(i+1)%sides],b[(i+1)%sides],b[i]))
    top=rings[-1]
    if broken:
        # snapped: jagged flat-ish break, cap with fan around offset centre
        c=bm.verts.new(base+rot@Vector((radius*0.2,0,length*(1-tipfrac)+radius*0.25*rnd.random())))
        for v in top: v.co+= rot@Vector((0,0,(rnd.random()-0.5)*radius*0.9))
    else:
        c=bm.verts.new(base+rot@Vector(((rnd.random()-0.5)*radius*0.3,(rnd.random()-0.5)*radius*0.3,length)))
    for i in range(sides): bm.faces.new((top[i],top[(i+1)%sides],c))
    bm.faces.new(list(reversed(rings[0])))
def rock_base(bm, radius, rnd, segs):
    # lumpy lava-rock socket dome, sits slightly below origin so it sinks into skin
    r=bmesh.ops.create_icosphere(bm, subdivisions=segs, radius=1.0)
    for v in r['verts']:
        p=v.co
        n=1+0.18*math.sin(p.x*7.1+rnd.random())*math.sin(p.y*5.3)+0.1*rnd.random()
        v.co=Vector((p.x*radius*n, p.y*radius*n, p.z*radius*0.38*n-radius*0.12))
    return r['verts']
def build(name, size, nshards, broken, lod):
    clear(); rnd=random.Random(hash(name.replace('_broken','').replace('_lod1',''))%9999)
    me=bpy.data.meshes.new(name); obj=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(obj)
    bmr=bmesh.new(); rock_base(bmr, size*0.75, random.Random(7), 1 if lod else 3); 
    bmc=bmesh.new()
    sides=5 if lod else 7
    n=nshards if not lod else max(3,nshards//2)
    for i in range(n):
        if i==0: ang,tilt,L=0,0,1.0
        else:
            ang=rnd.random()*6.28; tilt=0.25+0.55*rnd.random(); L=0.45+0.45*rnd.random()
        ax=Vector((math.sin(tilt)*math.cos(ang), math.sin(tilt)*math.sin(ang), math.cos(tilt)))
        off=Vector((math.cos(ang),math.sin(ang),0))*size*0.35*(0 if i==0 else (0.3+0.7*rnd.random()))
        length=size*1.6*L; rad=size*(0.22 if i==0 else 0.09+0.08*rnd.random())
        br = broken and (i==0 or rnd.random()<0.75)
        if br: length*=0.25+0.25*rnd.random()
        if lod and i>=n: break
        shard(bmc, off+Vector((0,0,-size*0.1)), ax, length, rad, sides, 0.0 if br else 0.32, rnd, br)
    # z-up blender -> glTF y-up handled by exporter
    for b,m_ in ((bmr,'rock'),(bmc,'crystal')):
        pass
    bmc.to_mesh(me); me2=bpy.data.meshes.new(name+'_rock'); bmr.to_mesh(me2)
    o2=bpy.data.objects.new(name+'_rock',me2); bpy.context.scene.collection.objects.link(o2)
    me.materials.append(mat('wb_crystal' if not broken else 'wb_crystal_dead',(0.9,0.25,0.04) if not broken else (0.08,0.05,0.04),(1.0,0.35,0.05),3.0 if not broken else 0.15))
    me2.materials.append(mat('wb_rock',(0.05,0.04,0.035),(0,0,0),0))
    for o in (obj,o2):
        o.data.polygons.foreach_set('use_smooth',[False]*len(o.data.polygons))
    bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active=obj; bpy.ops.object.join()
    obj.name=name
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,name+'.glb'), export_format='GLB', use_selection=False, export_yup=True, export_apply=True)
    print(name, len(obj.data.polygons))
for kind,size,n in (('forearm',0.55,9),('knee',0.75,11),('core',1.1,15)):
    for broken in (False,True):
        for lod in (False,True):
            build('wb_crystal_%s%s%s'%(kind,'_broken' if broken else '','_lod1' if lod else ''),size,n,broken,lod)
