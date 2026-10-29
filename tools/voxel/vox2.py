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
if fly!='none': bpy.ops.import_scene.gltf(filepath=fly)
print('FLYACTS',[x.name for x in set(bpy.data.actions)-ba])
for o in set(bpy.data.objects)-before: bpy.data.objects.remove(o)
for act in bpy.data.actions:
    act.use_fake_user=True; act.name=act.name.split('_'+arm.name)[0]

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
HEADB=set(b for b in bones if b in('head','jaw','eye_L','eye_R') or b.startswith('hair'))
SH=float(a[5]) if len(a)>5 else S
def domb(vi):
    w=vw[vi]; return max(w,key=w.get) if w else 'hips'
def voxelize(S,keep,vlist):
    mn=Vector([min(verts[i][k] for i in vlist) for k in range(3)])-Vector((S,S,S))*2
    mx=Vector([max(verts[i][k] for i in vlist) for k in range(3)])+Vector((S,S,S))*2
    N=[int(math.ceil((mx[i]-mn[i])/S))+1 for i in range(3)]
    o0=mn; out={}; R=S*0.62
    for i in range(N[0]):
      for j in range(N[1]):
        for k in range(N[2]):
          c=o0+Vector((i*S,j*S,k*S))
          loc,nrm,fi,d=bvh.find_nearest(c,R)
          if loc is None: continue
          t=tris[fi]; b=bary(loc,verts[t[0]],verts[t[1]],verts[t[2]])
          uv=tuv[fi][0]*b[0]+tuv[fi][1]*b[1]+tuv[fi][2]*b[2]
          x=int((uv.x%1)*W)%W; y=int((uv.y%1)*H)%H
          if S<0.012:
            col=px[y,x,:3].copy()
            ax_=max(range(3),key=lambda q:abs(nrm[q])); sg=1 if nrm[ax_]>0 else -1
            org=c.copy(); org[ax_]+=sg*0.5; dv=Vector((0,0,0)); dv[ax_]=-sg
            hit=bvh.ray_cast(org,dv)
            if hit[0] is not None and (hit[0]-c).length<S*1.2:
              t2=tris[hit[2]]; b2=bary(hit[0],verts[t2[0]],verts[t2[1]],verts[t2[2]])
              u2=tuv[hit[2]][0]*b2[0]+tuv[hit[2]][1]*b2[1]+tuv[hit[2]][2]*b2[2]
              col=px[int((u2.y%1)*H)%H,int((u2.x%1)*W)%W,:3].copy()
          elif S<0.02: col=px[y,x,:3].copy()
          else: col=px[max(0,y-1):y+2,max(0,x-1):x+2,:3].reshape(-1,3).mean(0)
          acc={}
          for wv,vi in zip(b,t):
            for g,w in vw[vi].items(): acc[g]=acc.get(g,0)+w*wv
          bone=max(acc,key=acc.get) if acc else 'hips'
          if not keep(bone,c): continue
          out[(i,j,k)]=[col,bone,c]
    return out,o0
HB='head' if 'head' in arm.data.bones else 'mixamorig:Head'; NB='neck' if 'neck' in arm.data.bones else 'mixamorig:Neck'
hh=arm.matrix_world@arm.data.bones[HB].head_local
nh=arm.matrix_world@arm.data.bones[NB].head_local
HZ=min(hh.z-0.06,nh.z+0.03)
def inhead(c): return c.z>=HZ and ((c.x-hh.x)**2+(c.y-hh.y)**2)**0.5<0.24
vox,o0=voxelize(S,lambda b,c: not inhead(c),range(len(verts)))
hv=[i for i in range(len(verts)) if inhead(verts[i])]
headvox,ho0=voxelize(SH,lambda b,c: inhead(c),hv) if hv else ({},None)
print('raw voxels',len(vox))
if 'mixamorig:Hips' in arm.data.bones:
    from mathutils.geometry import intersect_point_line
    limb=[b.name for b in arm.data.bones if any(t in b.name for t in ('Shoulder','Arm','UpLeg','Leg')) and 'Hand' not in b.name]
    def seg(n):
        b=arm.data.bones[n]; return arm.matrix_world@b.head_local, arm.matrix_world@b.tail_local
    torso=[(n,seg(n)) for n in ('mixamorig:Hips','mixamorig:Spine','mixamorig:Spine1','mixamorig:Spine2')]
    moved=0
    for VX in (vox,):
        for v in VX.values():
            if v[1] in limb:
                A_,B_=seg(v[1]); q,t=intersect_point_line(v[2],A_,B_); t=min(1,max(0,t)); d=(v[2]-A_.lerp(B_,t)).length
                if d>(0.10 if 'Leg' in v[1] else 0.085):
                    v[1]=min(torso,key=lambda x:abs(x[1][0].z-v[2].z))[0]; moved+=1
    print('cloth reassigned',moved)
def lin2s(c): return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.clip(c,0,1),1/2.4)-0.055)
# image.pixels of 8-bit textures are already sRGB-encoded; no conversion
center=sum((v[2] for v in vox.values()),Vector())/len(vox)
zmin=min(v[2].z for v in vox.values())
import random; random.seed(7)
def key(p): return tuple(int(round((p[i]-o0[i])/S)) for i in range(3))
def put(p,col,bone):
    k=key(p); vox[k]=[np.array(col,dtype=float),bone,o0+Vector(k)*S]
def bpos(n,t=0.0):
    b=arm.data.bones[n]; return arm.matrix_world@(b.head_local.lerp(b.tail_local,t))
HAIR=np.array([0.36,0.22,0.12]); SKIN=np.array([0.88,0.66,0.50]); YEL=np.array([0.98,0.82,0.12]); BRN=np.array([0.40,0.24,0.10])
if hero=='owner':
    # onesie recolor + stripes
    for (i,j,k),v in vox.items():
        c,bone,p=v; h,l,s_=colorsys.rgb_to_hls(*np.clip(c,0,1))
        if 0.09<h<0.2 and s_>0.35 and l>0.3 and (p.z-zmin)>0.10:
            v[0]=YEL.copy(); rel=p.z-zmin; band=(rel%0.20)<0.045
            if band and 0.35<rel<1.55 and (p.y>center.y-0.02 or bone.startswith(('upperArm','foreArm','thigh','shin'))): v[0]=BRN.copy()
    # big hairy hobbit-feet slippers
    feet=[k for k,v in vox.items() if v[1].startswith(('foot','toe')) or (v[2].z-zmin)<0.10]
    fb={k:vox[k][1] for k in feet}
    for (i,j,k) in feet:
        for dx in range(-2,3):
            for dy in range(-3,3):
                for dz in range(0,3):
                    nk=(i+dx,j+dy,k+dz)
                    if nk not in vox and (o0.z+nk[2]*S-zmin)<0.16: vox[nk]=[SKIN.copy(),fb[(i,j,k)],o0+Vector(nk)*S]; fb[nk]=fb[(i,j,k)]
    for side in (-1,1):
        ks=[k for k in fb if (vox[k][2].x-center.x)*side>0]
        if not ks: continue
        ymin=min(k[1] for k in ks); kmin=min(k[2] for k in ks)
        for k in ks:
            v=vox[k]; top=(k[0],k[1],k[2]+1) not in vox
            if k[2]==kmin: v[0]=np.array([0.30,0.20,0.12])
            elif k[1]<=ymin+2 and k[2]<=kmin+2: v[0]=SKIN*(0.8 if k[0]%3==0 else 1.0)  # toes
            elif top: v[0]=HAIR*(0.8+0.4*random.random()) if random.random()<0.85 else SKIN
            else: v[0]=HAIR*(0.8+0.4*random.random()) if random.random()<0.45 else SKIN
    # Pikachu hood hanging down the back, with ears
    nk_=bpos('neck'); hc=nk_+Vector((0,0.13,-0.02)); hb='hood' if 'hood' in bones else 'chest'
    rx,ry,rz=0.15,0.08,0.15
    n=int(0.4/S)
    for a_ in range(-n,n+1):
        for b_ in range(-n,n+1):
            for c_ in range(-n,n+1):
                p=hc+Vector((a_,b_,c_))*S; d=((p.x-hc.x)/rx)**2+((p.y-hc.y)/ry)**2+((p.z-hc.z)/rz)**2
                if 0.70<d<=1.0 and p.y>hc.y-0.03: put(p,YEL*(0.92 if d<0.8 else 1.0),hb)
    for sx in (-1,1):
        st=hc+Vector((sx*0.07,0.04,rz*0.75)); dr=Vector((sx*0.22,0.30,0.93)).normalized()
        steps=int(0.20/S)
        for t in range(steps):
            w=max(1,int((0.05*(1-t/steps*0.7))/S))
            for q in range(-w,w+1):
                for r in range(0,2):
                    p=st+dr*(t*S)+Vector((1,0,0))*(q*S*0.8)+Vector((0,1,0))*(r*S)
                    put(p,(0.08,0.06,0.05) if t>steps*0.65 else YEL,hb)
if hero=='darius':
    hb_=arm.data.bones['hand_R']; M=arm.matrix_world@hb_.matrix_local
    hp=M@Vector((0,hb_.length*0.9,0))
    SWD=Vector(json.loads(a[6])) if len(a)>6 else Vector((0,0,-1))
    ax=(M.to_3x3()@SWD).normalized()
    ax2=(M.to_3x3()@Vector((1,0,0))).normalized()
    print('sword',hp,ax)
    L_=int(0.75/S)
    for t in range(-int(0.12/S),L_):
        p=hp+ax*(t*S*0.95)
        if t<0:
            put(p,(0.25,0.2,0.15),'hand_R')
            if t==-int(0.12/S): put(p,(0.8,0.3,0.9),'hand_R')
        elif t<=1:
            for q in range(-int(0.09/S),int(0.09/S)+1): put(p+ax2*q*S,(0.85,0.65,0.2),'hand_R')
        else:
            for q in (0,1): put(p+ax2*q*S,(0.80,0.82,0.88) if q==0 else (0.62,0.64,0.7),'hand_R')
    # tabard cross
    def ispur(c):
        h,l,s_=colorsys.rgb_to_hls(*np.clip(c,0,1)); return 0.7<h<0.92 and s_>0.18
    front=lambda k:(k[0],k[1]-1,k[2]) not in vox
    pur=[(k,v) for k,v in vox.items() if not v[1].startswith(('cape','hand','fore','upperArm')) and ispur(v[0]) and front(k)]
    xs=sorted(v[2].x for _,v in pur); cx=xs[len(xs)//2]
    zs=sorted(v[2].z for _,v in pur if abs(v[2].x-cx)<0.04); z0,z1=zs[int(len(zs)*0.05)],zs[int(len(zs)*0.95)]
    zc=z0+(z1-z0)*0.72; GOLD=np.array([0.95,0.75,0.22]); PUR=np.array([0.32,0.12,0.42])
    for k,v in vox.items():
        if v[1].startswith(('cape','hand','fore','upperArm')) or not front(k) or v[2].y>center.y: continue
        p=v[2]; dx=abs(p.x-cx)
        if z0<=p.z<=z1 and dx<0.13:
            vert=dx<=0.022 and z0+0.04<=p.z<=z1-0.03
            hor=abs(p.z-zc)<=0.022 and dx<=0.10
            if vert or hor: v[0]=GOLD.copy()
            elif ispur(v[0]) or dx<0.08: v[0]=PUR.copy()
    print('cross',cx,z0,z1,zc)
for v in vox.values():
    h,l,s_=colorsys.rgb_to_hls(*np.clip(v[0],0,1)); v[0]=np.array(colorsys.hls_to_rgb(h,l,min(1,s_*1.25)))
hls_=[colorsys.rgb_to_hls(*np.clip(v[0],0,1)) for v in headvox.values()]
med=sorted(x[1] for x in hls_)[len(hls_)//2] if hls_ else 0.5
for v in headvox.values():
    h,l,s_=colorsys.rgb_to_hls(*np.clip(v[0],0,1))
    if l<0.35 or l<med-0.12: l*=0.5
    v[0]=np.array(colorsys.hls_to_rgb(h,l,min(1,s_*1.3)))
print('voxels',len(vox),'head',len(headvox),'HZ',HZ,'hh',hh,'nh',nh,'img',img.name,img.size[:])
SETS=[(vox,S)]+([(headvox,SH)] if headvox else [])
keys=[]; idx={}
for VX,_ in SETS:
  for v in VX.values():
    q=tuple(int(round(x*31)) for x in np.clip(v[0],0,1))
    if q not in idx: idx[q]=len(keys); keys.append(q)
    v.append(idx[q])
A=max(4,1<<int(math.ceil(math.log2(math.sqrt(len(keys))))))
apx=np.ones((A,A,4),dtype=np.float32)
for n,q in enumerate(keys):
    apx[n//A,n%A,:3]=[x/31 for x in q]
im=bpy.data.images.new(hero+'_vox_pal',A,A); im.pixels[:]=apx.ravel(); im.pack()
F=[((-1,0,0),[(0,0,0),(0,0,1),(0,1,1),(0,1,0)]),((1,0,0),[(1,0,0),(1,1,0),(1,1,1),(1,0,1)]),
   ((0,-1,0),[(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),((0,1,0),[(0,1,0),(0,1,1),(1,1,1),(1,1,0)]),
   ((0,0,-1),[(0,0,0),(0,1,0),(1,1,0),(1,0,0)]),((0,0,1),[(0,0,1),(1,0,1),(1,1,1),(0,1,1)])]
V=[];P=[];UV=[];VB=[]
for VX,SS in SETS:
  for (i,j,k),v in VX.items():
    col,bone,c,pi=v
    u=((pi%A)+0.5)/A; w=((pi//A)+0.5)/A
    base=c-Vector((SS,SS,SS))*0.5
    for d,cs in F:
        nb=VX.get((i+d[0],j+d[1],k+d[2]))
        if nb and nb[1]==bone: continue
        n0=len(V)
        for cc in cs: V.append(base+Vector(cc)*SS)
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
for pb in arm.pose.bones: pb.custom_shape=None
for o_ in list(bpy.data.objects):
    if o_.name.startswith('Icosphere'): bpy.data.objects.remove(o_)
arm.data.pose_position='POSE'
stats=dict(hero=hero,cube=S,head_cube=SH,voxels=len(vox)+len(headvox),quads=len(P),tris=len(P)*2,verts=len(V),palette=len(keys),
  actions=sorted(a.name for a in bpy.data.actions))
print('STATS',json.dumps(stats))
json.dump(stats,open(out+'.stats.json','w'))
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
bpy.ops.export_scene.gltf(filepath=out+'.glb',export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
