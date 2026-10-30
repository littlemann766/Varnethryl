# rebuild voxel mesh: one closed-where-needed cube per cell; cull shared face ONLY if neighbor cube is bound to the same bone.
# K>1 re-grids for LODs. Removes isolated single cells. Optional cape inflate.
import bpy,sys,math,json,os,bmesh
from collections import defaultdict,Counter
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; blend,K,out=a[0],float(a[1]),a[2]
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
me=ob.data; S=0.018; G=K*S; INF=float(os.environ.get('INFLATE','1.0'))
info={'src_tris':sum(len(p.vertices)-2 for p in me.polygons)}
gn={g.index:g.name for g in ob.vertex_groups}
uvl=me.uv_layers.active.data
vg=[(max(v.groups,key=lambda g:g.weight).group if v.groups else -1) for v in me.vertices]
R=lambda x,sz:round(x/(sz*0.2))
cells=defaultdict(lambda:{'w':Counter(),'uv':Counter(),'s':0.0,'c':None})
VC=[v.co.copy() for v in me.vertices]
def geo(p):
    if len(p.vertices)==3:
        a,b,c=[VC[i] for i in p.vertices]; e=max([(a,b),(b,c),(c,a)],key=lambda t:(t[0]-t[1]).length)
        return (e[0]+e[1])/2,(e[0]-e[1]).length/math.sqrt(2)
    return p.center,math.sqrt(p.area)
for p in me.polygons:
    pc,sz=geo(p)
    if K==1:
        c=pc-p.normal*(sz/2); k=(R(c.x,sz),R(c.y,sz),R(c.z,sz),round(sz,6))
    else:
        c=pc-p.normal*(sz/2); k=tuple(int(math.floor(x/G)) for x in c)+(0,)
    d=cells[k]; d['s']=sz if K==1 else G
    if d['c'] is None: d['c']=c.copy() if K==1 else Vector([(k[i]+0.5)*G for i in range(3)])
    for v in p.vertices: d['w'][vg[v]]+=p.area
    uv=sum((uvl[l].uv for l in p.loop_indices),start=uvl[p.loop_indices[0]].uv*0)/len(p.loop_indices)
    d['uv'][(round(uv.x,4),round(uv.y,4))]+=p.area
def nb(k,n):
    d=cells[k]
    if K==1:
        c=d['c']+Vector(n)*d['s']; sz=d['s']; return (R(c.x,sz),R(c.y,sz),R(c.z,sz),k[3])
    return (k[0]+n[0],k[1]+n[1],k[2]+n[2],0)
bone={k:d['w'].most_common(1)[0][0] for k,d in cells.items()}
N6=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
iso=[k for k in list(cells) if not any(nb(k,n) in cells for n in N6)]
for k in iso: del cells[k]; del bone[k]
info['removed_isolated']=len(iso)
bm=bmesh.new(); uvb=bm.loops.layers.uv.new('UVMap'); dl=bm.verts.layers.deform.verify()
D=[((1,0,0),[(1,0,0),(1,1,0),(1,1,1),(1,0,1)]),((-1,0,0),[(0,0,0),(0,0,1),(0,1,1),(0,1,0)]),
   ((0,1,0),[(0,1,0),(0,1,1),(1,1,1),(1,1,0)]),((0,-1,0),[(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),
   ((0,0,1),[(0,0,1),(1,0,1),(1,1,1),(0,1,1)]),((0,0,-1),[(0,0,0),(0,1,0),(1,1,0),(1,0,0)])]
sealed=0
for k,d in cells.items():
    g=bone[k]; uv=d['uv'].most_common(1)[0][0]
    cape=g>=0 and gn[g].startswith('cape'); f=INF if cape else 1.0
    for nrm,cs in D:
        nk=nb(k,nrm)
        if nk in bone:
            if bone[nk]==g and not cape: continue
            if bone[nk]==g and cape: continue
            if cape and os.environ.get('CAPE_NOSEAL_BODY') and not gn.get(bone[nk],'').startswith('cape'): continue
            sealed+=1
        vs=[]
        for c in cs:
            q=[d['c'][i]+(c[i]-0.5)*f*d['s'] for i in range(3)]
            v=bm.verts.new(q)
            if g>=0: v[dl][g]=1.0
            vs.append(v)
        fc=bm.faces.new(vs)
        for l in fc.loops: l[uvb].uv=uv
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5) if False else None
nm=bpy.data.meshes.new(me.name+'_sealed'); bm.to_mesh(nm); bm.free()
nm.materials.append(ob.active_material)
names=[gn[i] for i in range(len(gn))]
ob.data=nm
for x in names: ob.vertex_groups.new(name=x)
mat=ob.active_material
if mat: mat.blend_method='OPAQUE'; mat.use_backface_culling=True
info.update(cells=len(cells),sealed_faces=sealed,tris=sum(len(p.vertices)-2 for p in nm.polygons))
print('SEAL',json.dumps(info))
arm.animation_data.action=bpy.data.actions['idle']
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
json.dump(info,open(out+'.lod.json','w'))
