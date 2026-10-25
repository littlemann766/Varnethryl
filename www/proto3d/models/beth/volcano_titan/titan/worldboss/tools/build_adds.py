# Ash Fiend (melee add, ~2.4 m, unrigged static sculpt for Lucian to rig) and Ember Wisp (ranged, floating, ~1.3 m). +Z forward, origin at feet / wisp centre.
import bpy, bmesh, math, random, os
from mathutils import Vector
OUT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
def mat(name,col,emis,s,rough=0.9):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*col,1); b.inputs['Roughness'].default_value=rough
    b.inputs['Emission Color'].default_value=(*emis,1); b.inputs['Emission Strength'].default_value=s; return m
def blob(name,loc,scale,m,sub=2,noise=0.15,seed=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,location=loc); o=bpy.context.object; o.name=name; o.scale=scale
    r=random.Random(seed)
    for v in o.data.vertices: v.co*=1+noise*(r.random()-0.5)
    o.data.materials.append(m); return o
def limb(a,b,r,m,sub,seed):
    a=Vector(a); b=Vector(b); n=4
    return [blob('seg',a.lerp(b,i/(n-1)),(r*(1-0.15*i/n),)*3,m,sub,0.25,seed+i) for i in range(n)]
def finish(name,lod):
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join(); o=bpy.context.object; o.name=name
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.ops.object.shade_flat()
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,name+('_lod1' if lod else '')+'.glb'),export_format='GLB',export_yup=True)
    print(name,lod,len(o.data.polygons))
def fiend(lod):
    bpy.ops.wm.read_factory_settings(use_empty=True); sub=1 if lod else 3
    ash=mat('fiend_ash',(0.09,0.08,0.075),(0,0,0),0); emb=mat('fiend_ember',(0.9,0.3,0.05),(1,0.38,0.06),6,0.4)
    blob('torso',(0,0.1,1.45),(0.55,0.45,0.6),ash,sub,0.25,1); blob('pelvis',(0,0,0.95),(0.42,0.32,0.3),ash,sub,0.25,2)
    blob('head',(0,0.38,1.95),(0.26,0.3,0.24),ash,sub,0.3,3); blob('core',(0,0.38,1.5),(0.16,0.1,0.18),emb,sub,0.2,4)
    for s in (-1,1):
        blob('eye',(s*0.1,0.62,1.98),(0.05,0.03,0.04),emb,1,0,5)
        blob('horn',(s*0.2,0.25,2.18),(0.06,0.06,0.2),ash,sub,0.2,6).rotation_euler=(0.5,s*0.4,0)
        limb((s*0.62,0.15,1.75),(s*0.85,0.45,0.75),0.17,ash,sub,10+s)            # long arm
        for f in range(3): blob('claw',(s*(0.8+0.07*f),0.65,0.55),(0.04,0.04,0.16),emb if f==1 else ash,1,0.1,20+f).rotation_euler=(0.6,0,0)
        limb((s*0.25,0,0.85),(s*0.32,0.1,0.12),0.16,ash,sub,30+s)              # legs
        blob('foot',(s*0.33,0.2,0.07),(0.14,0.25,0.08),ash,sub,0.2,40)
        for k in range(3): blob('vent',(s*0.3,0.35-k*0.1,1.3+k*0.18),(0.07,0.06,0.03),emb,1,0.2,50+k)
    for k in range(5): blob('spike',(0,-0.3-0.02*k,1.25+k*0.18),(0.07,0.12,0.07),ash,sub,0.2,60+k)
    finish('wb_ash_fiend',lod)
def wisp(lod):
    bpy.ops.wm.read_factory_settings(use_empty=True); sub=1 if lod else 3
    core=mat('wisp_core',(1,0.75,0.3),(1,0.6,0.15),10,0.3); flame=mat('wisp_flame',(0.95,0.3,0.05),(1,0.3,0.04),5,0.5); rock=mat('wisp_rock',(0.08,0.07,0.06),(0,0,0),0)
    blob('core',(0,0,0),(0.28,)*3,core,sub,0.05,1)
    for k in range(6 if lod else 10):
        a=k*2.39; h=0.15+k*0.07; blob('tongue',(math.cos(a)*0.15,math.sin(a)*0.15,h),(0.18-k*0.012,0.18-k*0.012,0.3),flame,sub-1 if sub>1 else 1,0.35,k)
    for k in range(5 if lod else 8):
        a=k*6.283/(5 if lod else 8); blob('shard',(math.cos(a)*0.62,math.sin(a)*0.62,-0.1+0.15*math.sin(a*3)),(0.09,0.09,0.16),rock,1,0.4,20+k)
    blob('tail',(0,0,-0.45),(0.12,0.12,0.3),flame,1,0.3,40)
    finish('wb_ember_wisp',lod)
for l in (False,True): fiend(l); wisp(l)
