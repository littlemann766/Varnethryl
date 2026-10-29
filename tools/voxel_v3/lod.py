import bpy,sys,math,json,os,bmesh
import numpy as np
from collections import defaultdict,Counter
a=sys.argv[sys.argv.index('--')+1:]; blend,K,out=a[0],float(a[1]),a[2]
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
for pb in arm.pose.bones: pb.custom_shape=None
me=ob.data; S=0.018; info={'lod0_tris':sum(len(p.vertices)-2 for p in me.polygons)}
if K>1:
    G=K*S; gn={g.index:g.name for g in ob.vertex_groups}
    uvl=me.uv_layers.active.data
    cells=defaultdict(lambda:{'w':Counter(),'uv':Counter(),'a':0})
    vg=[ (max(v.groups,key=lambda g:g.weight).group if v.groups else -1) for v in me.vertices]
    for p in me.polygons:
        s=math.sqrt(p.area); c=p.center-p.normal*(s/2)
        k=tuple(int(math.floor(x/G)) for x in c)
        d=cells[k]; d['a']+=p.area
        for v in p.vertices: d['w'][vg[v]]+=p.area
        uv=sum((uvl[l].uv for l in p.loop_indices),start=uvl[p.loop_indices[0]].uv*0)/len(p.loop_indices)
        d['uv'][(round(uv.x,4),round(uv.y,4))]+=p.area
    keys=set(cells)
    bm=bmesh.new(); uvb=bm.loops.layers.uv.new('UVMap'); dl=bm.verts.layers.deform.verify()
    D=[((1,0,0),[(1,0,0),(1,1,0),(1,1,1),(1,0,1)]),((-1,0,0),[(0,0,0),(0,0,1),(0,1,1),(0,1,0)]),
       ((0,1,0),[(0,1,0),(0,1,1),(1,1,1),(1,1,0)]),((0,-1,0),[(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),
       ((0,0,1),[(0,0,1),(1,0,1),(1,1,1),(0,1,1)]),((0,0,-1),[(0,0,0),(0,1,0),(1,1,0),(1,0,0)])]
    for k,d in cells.items():
        g=d['w'].most_common(1)[0][0]; uv=d['uv'].most_common(1)[0][0]
        for n,cs in D:
            if (k[0]+n[0],k[1]+n[1],k[2]+n[2]) in keys: continue
            vs=[]
            for c in cs:
                v=bm.verts.new(((k[0]+c[0])*G,(k[1]+c[1])*G,(k[2]+c[2])*G))
                if g>=0: v[dl][g]=1.0
                vs.append(v)
            f=bm.faces.new(vs)
            for l in f.loops: l[uvb].uv=uv
    nm=bpy.data.meshes.new(me.name+f'_lod{K:g}'); bm.to_mesh(nm); bm.free()
    nm.materials.append(ob.active_material)
    me.clear_geometry() if False else None
    names=[gn[i] for i in range(len(gn))]
    ob.data=nm
    for x in names: ob.vertex_groups.new(name=x)
    for mod in ob.modifiers:
        if mod.type!='ARMATURE': mod.show_viewport=True
    # remove doubles to share verts within same-group cubes
    bpy.context.view_layer.objects.active=ob; ob.select_set(True)
    pass
    info['cells']=len(cells)
info['tris']=sum(len(p.vertices)-2 for p in ob.data.polygons); info['ratio']=round(info['tris']/info['lod0_tris'],3)
print('LOD',json.dumps(info))
arm.animation_data.action=bpy.data.actions['idle']
if os.environ.get('SAVEBLEND'): bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
json.dump(info,open(out+'.lod.json','w'))
