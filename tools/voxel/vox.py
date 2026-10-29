import bpy,sys,math,json,colorsys
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]
hero,src,fly,out,S=a[0],a[1],a[2],a[3],float(a[4])
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
bpy.ops.import_scene.gltf(filepath=src)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
body=bpy.data.objects['Body']
for act in bpy.data.actions: act.use_fake_user=True
# fly actions
before=set(bpy.data.objects); ba=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=fly)
print('FLYACTS',[x.name for x in set(bpy.data.actions)-ba])
for o in set(bpy.data.objects)-before: bpy.data.objects.remove(o)
for act in bpy.data.actions:
    act.use_fake_user=True; act.name=act.name.split('_Darius_Rig')[0]

arm.animation_data.action=None
arm.data.pose_position='REST'; bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
ev=body.evaluated_get(dg); me=ev.to_mesh()
mw=body.matrix_world
verts=[mw@v.co for v in me.vertices]
me.calc_loop_triangles()
tris=[tuple(t.vertices) for t in me.loop_triangles]
uvl=me.uv_layers.active.data
tuv=[[uvl[l].uv.copy() for l in t.loops] for t in me.loop_triangles]
bvh=BVHTree.FromPolygons(verts,tris)
# texture
mat=body.data.materials[0]
img=max([n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image],key=lambda i:i.size[0]*i.size[1])
for n in []:
    if n.type=='BSDF_PRINCIPLED':
        l=n.inputs['Base Color'].links
        if l:
            nd=l[0].from_node
            while nd.type!='TEX_IMAGE' and nd.inputs and nd.inputs[0].links: nd=nd.inputs[0].links[0].from_node
            img=nd.image
W,H=img.size; px=np.array(img.pixels[:],dtype=np.float32).reshape(H,W,4)
# weights
vgn={g.index:g.name for g in body.vertex_groups}
bones=set(b.name for b in arm.data.bones if b.use_deform)
vw=[{vgn[g.group]:g.weight for g in v.groups if vgn.get(g.group) in bones} for v in body.data.vertices]
def bary(p,A,B,C):
    v0,v1,v2=B-A,C-A,p-A
    d00,d01,d11,d20,d21=v0.dot(v0),v0.dot(v1),v1.dot(v1),v2.dot(v0),v2.dot(v1)
    den=d00*d11-d01*d01 or 1e-12
    v=(d11*d20-d01*d21)/den; w=(d00*d21-d01*d20)/den
    return max(0,1-v-w),max(0,v),max(0,w)
mn=Vector([min(v[i] for v in verts) for i in range(3)]); mx=Vector([max(v[i] for v in verts) for i in range(3)])
N=[int(math.ceil((mx[i]-mn[i])/S))+2 for i in range(3)]
o0=mn-Vector((S,S,S))*0.5
vox={}
R=S*0.62
for i in range(N[0]):
  for j in range(N[1]):
    for k in range(N[2]):
      c=o0+Vector((i*S,j*S,k*S))
      loc,nrm,fi,d=bvh.find_nearest(c,R)
      if loc is None: continue
      t=tris[fi]; b=bary(loc,verts[t[0]],verts[t[1]],verts[t[2]])
      uv=tuv[fi][0]*b[0]+tuv[fi][1]*b[1]+tuv[fi][2]*b[2]
      x=int((uv.x%1)*W)%W; y=int((uv.y%1)*H)%H
      col=px[max(0,y-1):y+2,max(0,x-1):x+2,:3].reshape(-1,3).mean(0)
      acc={}
      for wv,vi in zip(b,t):
        for g,w in vw[vi].items(): acc[g]=acc.get(g,0)+w*wv
      bone=max(acc,key=acc.get) if acc else 'hips'
      vox[(i,j,k)]=[col,bone,c]
print('raw voxels',len(vox))
def lin2s(c): return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.clip(c,0,1),1/2.4)-0.055)
for v in vox.values(): v[0]=lin2s(v[0])
center=sum((v[2] for v in vox.values()),Vector())/len(vox)
zmin=min(v[2].z for v in vox.values())
# ---- hero tweaks
import random; random.seed(7)
if hero=='owner':
    for (i,j,k),v in vox.items():
        c,bone,p=v
        h,s_,l=colorsys.rgb_to_hls(*c)
        yellow= 0.09<h<0.2 and s_>0.35 and l>0.35
        if bone.startswith(('foot','toe')) or (p.z-zmin)<0.09:
            # hobbit feet slippers: skin with hairy brown top
            top=(i,j,k+1) not in vox
            v[0]=np.array([0.36,0.22,0.12]) if (top and random.random()<0.5) else np.array([0.86,0.64,0.48])
            if not top and random.random()<0.06: v[0]=np.array([0.42,0.26,0.13])
        elif yellow:
            v[0]=np.array([0.98,0.82,0.12])
            rel=(p.z-zmin)
            band=(rel%0.20)<S*1.05
            if band and p.y>center.y-0.02 and 0.35<rel<1.55: v[0]=np.array([0.40,0.24,0.10])
            elif band and bone.startswith(('upperArm','foreArm','thigh','shin')): v[0]=np.array([0.40,0.24,0.10])
# darius sword
if hero=='darius':
    hb=arm.data.bones['hand_R']; M=arm.matrix_world@hb.matrix_local
    hp=M@Vector((0,hb.length*0.9,0))
    ax=(M.to_3x3()@Vector((0,0,-1))*0.8+Vector((0,-1,0))*0.6).normalized()
    print('sword',hp,ax)
    ax2=(M.to_3x3()@Vector((1,0,0))).normalized()
    def put(p,col,bone='hand_R'):
        key=tuple(int(round((p[i]-o0[i])/S)) for i in range(3)); vox[key]=[np.array(col),bone,o0+Vector(key)*S]
    for t in range(-3,16):
        p=hp+ax*(t*S*0.95)
        if t<0: put(p,(0.25,0.2,0.15))
        elif t==0:
            for q in (-2,-1,0,1,2): put(p+ax2*q*S,(0.85,0.65,0.2))
        else: put(p,(0.78,0.8,0.85)); 
        if t==-3: put(p,(0.8,0.3,0.9))
print('voxels',len(vox))
if hero=='darius':
    pur=[(k,v) for k,v in vox.items() if not v[1].startswith('cape') and (lambda h,l,s_: (0.7<h<0.9) and s_>0.2)(*colorsys.rgb_to_hls(*v[0])) and (k[0],k[1]-1,k[2]) not in vox]
    if pur:
        xs=sorted(k[0] for k,_ in pur); cx=xs[len(xs)//2]; zs=[k[2] for k,_ in pur if abs(k[0]-cx)<=1]; z0,z1=min(zs),max(zs)
        zc=z1-(z1-z0)//3
        for k,v in pur:
            if k[0]==cx and z0+2<=k[2]<=z1-2: v[0]=np.array([0.9,0.7,0.2])
        for k,v in vox.items():
            if k[2]==zc and abs(k[0]-cx)<=2 and (k[0],k[1]-1,k[2]) not in vox and not v[1].startswith(('cape','hand','fore')): v[0]=np.array([0.9,0.7,0.2])

        print('cross',cx,z0,z1)
for v in vox.values():
    h,l,s_=colorsys.rgb_to_hls(*np.clip(v[0],0,1)); v[0]=np.array(colorsys.hls_to_rgb(h,l,min(1,s_*1.3)))
# ---- palette atlas
keys=[]; idx={}
for v in vox.values():
    q=tuple(int(round(x*31)) for x in np.clip(v[0],0,1))
    if q not in idx: idx[q]=len(keys); keys.append(q)
    v.append(idx[q])
A=max(4,1<<int(math.ceil(math.log2(math.sqrt(len(keys))))))
apx=np.ones((A,A,4),dtype=np.float32)
for n,q in enumerate(keys):
    apx[n//A,n%A,:3]=[x/31 for x in q]
im=bpy.data.images.new(hero+'_vox_pal',A,A); im.pixels[:]=apx.ravel(); im.pack()
# ---- build mesh
F=[((-1,0,0),[(0,0,0),(0,0,1),(0,1,1),(0,1,0)]),((1,0,0),[(1,0,0),(1,1,0),(1,1,1),(1,0,1)]),
   ((0,-1,0),[(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),((0,1,0),[(0,1,0),(0,1,1),(1,1,1),(1,1,0)]),
   ((0,0,-1),[(0,0,0),(0,1,0),(1,1,0),(1,0,0)]),((0,0,1),[(0,0,1),(1,0,1),(1,1,1),(0,1,1)])]
V=[];P=[];UV=[];VB=[]
for (i,j,k),v in vox.items():
    col,bone,c,pi=v
    u=((pi%A)+0.5)/A; w=((pi//A)+0.5)/A
    base=c-Vector((S,S,S))*0.5
    for d,cs in F:
        nb=vox.get((i+d[0],j+d[1],k+d[2]))
        if nb and nb[1]==bone: continue
        n0=len(V)
        for cc in cs: V.append(base+Vector(cc)*S)
        P.append((n0,n0+1,n0+2,n0+3)); UV+= [(u,w)]*4; VB+=[bone]*4
mesh=bpy.data.meshes.new(hero+'_voxel'); mesh.from_pydata([tuple(x) for x in V],[],P)
ul=mesh.uv_layers.new(name='UVMap')
for l in mesh.loops: ul.data[l.index].uv=UV[l.vertex_index]
m2=bpy.data.materials.new(hero+'_voxel'); m2.use_nodes=True
nt=m2.node_tree; bs=nt.nodes['Principled BSDF']; tx=nt.nodes.new('ShaderNodeTexImage'); tx.image=im; tx.interpolation='Closest'
nt.links.new(tx.outputs[0],bs.inputs['Base Color']); bs.inputs['Roughness'].default_value=0.9; bs.inputs['Metallic'].default_value=0
mesh.materials.append(m2)
for p in mesh.polygons: p.use_smooth=False
ob=bpy.data.objects.new(hero+'_voxel',mesh); sc.collection.objects.link(ob)
ob.parent=arm; ob.matrix_parent_inverse=arm.matrix_world.inverted()
groups={}
for vi,b in enumerate(VB):
    if b not in groups: groups[b]=ob.vertex_groups.new(name=b)
    groups[b].add([vi],1.0,'REPLACE')
md=ob.modifiers.new('Armature','ARMATURE'); md.object=arm
bpy.data.objects.remove(body)
arm.data.pose_position='POSE'
stats=dict(hero=hero,cube=S,voxels=len(vox),quads=len(P),tris=len(P)*2,verts=len(V),palette=len(keys),
  actions=sorted(a.name for a in bpy.data.actions))
print('STATS',json.dumps(stats))
json.dump(stats,open(out+'.stats.json','w'))
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
bpy.ops.export_scene.gltf(filepath=out+'.glb',export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
