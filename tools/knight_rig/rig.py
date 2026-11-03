# Knight rig: split -> fit Darius-named skeleton (+clavicles, twist bones, wing/tabard/cape/tasset chains) -> per-part rigid binding
import bpy,sys,os,json,math,numpy as np
from mathutils import Vector,Matrix
G=sys.argv[-1]; OUT=f'/tmp/kr/{G}'; os.makedirs(OUT,exist_ok=True)
d=np.load('/tmp/kr/parts.npz'); INV=d['inv']; CEN=d['cen']
bpy.ops.wm.read_factory_settings(use_empty=True)
# --- template skeleton (Darius) + its animations
bpy.ops.import_scene.gltf(filepath='/workspace/godot-voxel/voxel/darius_voxel_noweapon.glb')
ARM=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; ARM.name='knight_rig'; ARM.data.name='knight_rig'
for o in list(bpy.data.objects):
    if o is not ARM: bpy.data.objects.remove(o)
ARM.data.pose_position='REST'
if G=='female':   # Talia's clips for the female validation
    keep=set(bpy.data.actions.keys())
    bpy.ops.import_scene.gltf(filepath='/workspace/godot-voxel/voxel/talia_voxel.glb')
    for o in list(bpy.data.objects):
        if o is not ARM: bpy.data.objects.remove(o)
    for a in list(bpy.data.actions):
        if a.name in keep: bpy.data.actions.remove(a)
for a in bpy.data.actions: a.use_fake_user=True
BH0={b.name:np.array(b.head_local) for b in ARM.data.bones}
# --- figure
bpy.ops.import_scene.gltf(filepath='/workspace/uploads/ref_armor.glb')
fig=[o for o in bpy.data.objects if o.type=='MESH'][0]
for x in bpy.data.objects: x.select_set(False)
fig.select_set(True); bpy.context.view_layer.objects.active=fig; bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
me=fig.data; co=np.array([v.co[:] for v in me.vertices])
male_part=CEN[:,0]<5.0      # v2 split: by part centroid (male wing tips reach x=4; female hands start at x=6)
keepv=male_part[INV] if G=='male' else ~male_part[INV]
import bmesh
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not keepv[v.index]],context='VERTS'); bm.to_mesh(me); bm.free()
partid=INV[keepv]; co=co[keepv]
pa=me.attributes.new('part','INT','POINT'); pa.data.foreach_set('value',partid.astype(np.int32))
S=0.01913850652133653   # same unit scale for both figures (modelled side by side at one scale)
cx=(co[:,0].min()+co[:,0].max())/2 if G=='male' else None
# centre on the torso (wings are symmetric, torso band median is robust)
H=co[:,2].max(); tb=(co[:,2]>0.55*H)&(co[:,2]<0.70*H)
cxx=np.median(co[tb,0]); cyy=np.median(co[tb,1])
P=(co-np.array([cxx,cyy,0]))*S+np.array([0,BH0['spine'][1],0])
for i,v in enumerate(me.vertices): v.co=Vector(P[i])
me.update(); fig.name=f'knight_{G}'
Hm=P[:,2].max(); print('FIG',G,'verts',len(P),'tris',sum(len(p.vertices)-2 for p in me.polygons),'height',round(Hm,3))
# --- fit skeleton
B=dict(BH0); sz=Hm/1.854   # template is the male knight at Darius scale
def wid(Q,z0,z1): m=(Q[:,2]>z0)&(Q[:,2]<z1); return np.percentile(np.abs(Q[m,0]),85)
sx=1.0
if G=='female':
    sx=wid(P,0.50*Hm,0.62*Hm)/0.205   # hip/waist width vs male template
for n in B: B[n]=np.array([B[n][0]*sx,B[n][1],B[n][2]*sz]) if not n.startswith(('upperArm','foreArm','hand','fingers','index','middle','ring','pinky','thumb')) else B[n]*np.array([1,1,sz])
# measured arm centreline: outer cluster per height slice (the arm hangs clear of the torso), line fit
def arm_line(sg):
    pts=[]
    for z in np.arange(0.82*sz,1.24*sz,0.03):
        m=(np.abs(P[:,2]-z)<0.012)&(P[:,0]*sg>0.05); q=P[m]
        if len(q)<20: continue
        xs=np.sort(q[:,0]*sg); gaps=np.where(np.diff(xs)>0.02)[0]
        if not len(gaps): continue
        lo=xs[gaps[-1]+1]; arm=q[q[:,0]*sg>=lo]
        if len(arm)>15 and np.ptp(arm[:,0])<0.16: pts.append([arm[:,0].mean(),arm[:,1].mean(),z])
    pts=np.array(pts); A=np.c_[pts[:,2],np.ones(len(pts))]
    kx=np.linalg.lstsq(A,pts[:,0],rcond=None)[0]; ky=np.linalg.lstsq(A,pts[:,1],rcond=None)[0]
    return lambda z:np.array([kx[0]*z+kx[1],ky[0]*z+ky[1],z]),len(pts)
J={}
for X,sg in (('_L',1),('_R',-1)):
    f,n=arm_line(sg); zs=B['upperArm'+X][2]-0.04*sz; sh=f(zs); sh[0]=sg*max(abs(sh[0])-0.02,abs(B['upperArm'+X][0])); sh[1]=B['upperArm'+X][1]
    lowz=np.percentile(P[(P[:,0]*sg>abs(sh[0])+0.03)&(P[:,2]>0.35*Hm)&(P[:,2]<0.6*Hm)][:,2],3)
    wrist=f(lowz+0.10*sz)
    Lu=np.linalg.norm(BH0['foreArm'+X]-BH0['upperArm'+X]); Lf=np.linalg.norm(BH0['hand'+X]-BH0['foreArm'+X])
    e=sh+(wrist-sh)*Lu/(Lu+Lf); e[1]+=0.02
    B['upperArm'+X]=sh; B['shoulder'+X]=np.array([sg*abs(sh[0])*0.5,sh[1],sh[2]])
    dh=wrist-BH0['hand'+X]
    for nm in list(B):
        if nm.endswith(X) and nm.startswith(('hand','fingers','index','middle','ring','pinky','thumb')): B[nm]=BH0[nm]+dh
    B['foreArm'+X]=e
    J[X]=(sh,e,wrist)
    print('ARM',X,'slices',n,'shoulder',sh.round(3),'elbow',e.round(3),'wrist',wrist.round(3))
M_=[(np.abs(J['_L'][i])+np.abs(J['_R'][i]))/2 for i in range(3)]; M_[0][0]=min(M_[0][0],0.25)
for X,sg in (('_L',1),('_R',-1)):
    sh,e,wrist=[np.array([sg*m[0],m[1]*np.sign(J[X][i][1]) if False else J[X][i][1]*0+ (J['_L'][i][1]+J['_R'][i][1])/2,m[2]]) for i,m in enumerate(M_)]
    B['upperArm'+X]=sh; B['shoulder'+X]=np.array([sg*abs(sh[0])*0.5,sh[1],sh[2]]); B['foreArm'+X]=e
    dh=wrist-BH0['hand'+X]
    for nm in list(B):
        if nm.endswith(X) and nm.startswith(('hand','fingers','index','middle','ring','pinky','thumb')): B[nm]=BH0[nm]+dh
    print('SYM',X,sh.round(3),e.round(3),wrist.round(3))
bpy.context.view_layer.objects.active=ARM
for x in bpy.data.objects: x.select_set(False)
ARM.select_set(True); bpy.ops.object.mode_set(mode='EDIT'); eb=ARM.data.edit_bones
for b in list(eb):
    if b.name.startswith(('cape','coat','hair','eye','jaw')): eb.remove(b)
for b in eb:
    if b.name in B:
        L=b.length; b.head=Vector(B[b.name]); b.tail=b.head+Vector((0,max(L,0.02),0)); b.roll=0
def add(name,parent,head,length=0.05,deform=True):
    b=eb.new(name); b.head=Vector(head); b.tail=Vector(head)+Vector((0,length,0)); b.roll=0; b.parent=eb[parent]; b.use_deform=deform; return b
# twist bones (mid-limb)
for X in ('_L','_R'):
    add('upperArm_twist'+X,'upperArm'+X,(B['upperArm'+X]+B['foreArm'+X])/2)
    add('foreArm_twist'+X,'foreArm'+X,B['foreArm'+X]*0.35+B['hand'+X]*0.65)
    add('thigh_twist'+X,'thigh'+X,(B['thigh'+X]+B['shin'+X])/2)
    add('shin_twist'+X,'shin'+X,(B['shin'+X]+B['foot'+X])/2)
bpy.ops.object.mode_set(mode='OBJECT')
BH={b.name:np.array(b.head_local) for b in ARM.data.bones}
json.dump({k:v.tolist() for k,v in BH.items()},open(OUT+'/bones_core.json','w'))
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/stage1.blend')
