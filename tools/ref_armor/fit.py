import bpy,sys,os,json,numpy as np
from mathutils import Vector
G=sys.argv[-1]   # male|female
RIG={'male':'/workspace/godot-voxel/voxel/darius_voxel_noweapon.glb','female':'/workspace/godot-voxel/voxel/talia_voxel.glb'}[G]
OUT=f'/tmp/ref/out_{G}'; os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=RIG)
ARM=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; ARM.data.pose_position='REST'
body=max([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices))
for o in list(bpy.data.objects):
    if o not in (ARM,body): bpy.data.objects.remove(o)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
ARM.animation_data_clear(); bpy.context.view_layer.update()
BH={b.name:np.array(ARM.matrix_world@b.head_local) for b in ARM.data.bones}
bco=np.array([(body.matrix_world@v.co)[:] for v in body.data.vertices])
bpy.ops.import_scene.gltf(filepath=f'/workspace/uploads/ref_{G}.glb')
ref=[o for o in bpy.data.objects if o.type=='MESH' and o!=body][0]
for x in bpy.data.objects: x.select_set(False)
ref.select_set(True); bpy.context.view_layer.objects.active=ref; bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
rco=np.array([v.co[:] for v in ref.data.vertices])
# scale: shoulder-height match is more robust than total height (horns/hair)
H_r=rco[:,2].max(); H_b=bco[:,2].max()
s=(BH['head'][2]+0.20)/H_r if True else H_b/H_r
cx=(rco[:,0].min()+rco[:,0].max())/2
# depth centre: torso band
tb=(rco[:,2]>0.55*H_r)&(rco[:,2]<0.70*H_r)&(np.abs(rco[:,0]-cx)<0.12*H_r); cyr=np.median(rco[tb,1])
bb=(bco[:,2]>BH.get('spine2',BH['spine'])[2])&(bco[:,2]<BH['chest'][2]+0.1)&(np.abs(bco[:,0])<0.15); cyb=np.median(bco[bb,1])
new=(rco-np.array([cx,cyr,0]))*s+np.array([0,cyb,0])
# hand check
def hands(P,zlo,zhi):
    m=(P[:,2]>zlo)&(P[:,2]<zhi); q=P[m]; return q[q[:,0].argmax()], q[q[:,0].argmin()]
print('SCALE',s,'ref hand L',hands(new,0.75,1.0)[0].round(3),'rig hand',BH['hand_'+'L'].round(3),'rig upperArm',BH['upperArm_L'].round(3))
for i,v in enumerate(ref.data.vertices): v.co=Vector(new[i])
ref.data.update()
json.dump({'scale':s,'cx':cx,'cyr':float(cyr),'cyb':float(cyb)},open(OUT+'/xform.json','w'))
bpy.ops.wm.save_as_mainfile(filepath=f'/tmp/ref/{G}_aligned.blend')
# ---------- v2: bone-segment assignment + arm retarget (robust to the puffy voxel bodies) ----------
P=new.copy(); H=P[:,2].max()
def seg_d(p,a,b):
    d=b-a; t=np.clip(((p-a)@d)/(d@d),0,1); return np.linalg.norm(p-a-t[:,None]*d,axis=1),t
J=lambda n:BH[n] if n in BH else None
sp2='spine2' if 'spine2' in BH else 'spine'; uc='upperChest' if 'upperChest' in BH else 'chest'
REF={}
for X in ('_L','_R'):
    sg=1 if X=='_L' else -1; sh=BH['upperArm'+X]
    band=(P[:,2]>BH['hand'+X][2]-0.25)&(P[:,2]<BH['hand'+X][2]+0.25)&(P[:,0]*sg>0)
    q=P[band]; hr=q[np.argmax(q[:,0]*sg)]; hr=np.array([hr[0]-sg*0.03,BH['hand'+X][1]+(hr[1]-BH['hand'+X][1])*0.0+ (np.median(q[np.abs(q[:,0]-hr[0])<0.06][:,1])-BH['hand'+X][1]),hr[2]+0.03])
    Lu=np.linalg.norm(BH['foreArm'+X]-sh); Lf=np.linalg.norm(BH['hand'+X]-BH['foreArm'+X]); d=(hr-sh)/np.linalg.norm(hr-sh)
    REF['elbow'+X]=sh+d*np.linalg.norm(hr-sh)*Lu/(Lu+Lf); REF['hand'+X]=hr
    print('ARM',X,'ref hand',hr.round(3),'rig hand',BH['hand'+X].round(3))
SEGS=[('hips',BH['hips']+np.array([0,0,-0.12]),BH[sp2]),(sp2,BH[sp2],BH['chest']),('chest',BH['chest'],BH[uc]),(uc,BH[uc],BH['neck']),('head',BH['neck'],BH['head']+np.array([0,0,0.25]))]
for X in ('_L','_R'):
    SEGS+=[('upperArm'+X,BH['upperArm'+X],REF['elbow'+X]),('foreArm'+X,REF['elbow'+X],REF['hand'+X]),('hand'+X,REF['hand'+X],REF['hand'+X]+(REF['hand'+X]-REF['elbow'+X])*0.35),
           ('thigh'+X,BH['thigh'+X],BH['shin'+X]),('shin'+X,BH['shin'+X],BH['foot'+X]),('foot'+X,BH['foot'+X],BH['foot'+X]+np.array([0,-0.15,-0.08]))]
SEGS=[sg for sg in SEGS if np.linalg.norm(sg[2]-sg[1])>1e-4]
D=[];T=[]
for nm,a_,b_ in SEGS: d_,t_=seg_d(P,a_,b_); D.append(d_); T.append(t_)
D=np.array(D); T=np.array(T)
# torso-ish bias: favour torso for wide skirt/wings, favour limbs only when clearly closer
for i,(nm,_,_) in enumerate(SEGS):
    if nm.startswith(('thigh','shin')): D[i]*=1.0
si=D.argmin(0); segn=np.array([SEGS[i][0] for i in si])
neckz=BH['neck'][2]; hm=(P[:,2]>neckz+0.01)&(np.abs(P[:,0])<0.17)&(np.abs(P[:,1]-BH['head'][1])<0.2)
segn[hm]='head'
# retarget arms: piecewise rotation from ref arm segments to rig arm segments
from mathutils import Matrix
def rot_between(u,v):
    u=u/np.linalg.norm(u); v=v/np.linalg.norm(v); c=np.cross(u,v); s_=np.linalg.norm(c); k=u@v
    if s_<1e-8: return np.eye(3)
    K=np.array([[0,-c[2],c[1]],[c[2],0,-c[0]],[-c[1],c[0],0]])/s_; a=np.arctan2(s_,k); return np.eye(3)+np.sin(a)*K+(1-np.cos(a))*K@K
for X in ('_L','_R'):
    R1=rot_between(REF['elbow'+X]-BH['upperArm'+X],BH['foreArm'+X]-BH['upperArm'+X])
    m=segn=='upperArm'+X; P[m]=(P[m]-BH['upperArm'+X])@R1.T+BH['upperArm'+X]
    e_new=(REF['elbow'+X]-BH['upperArm'+X])@R1.T+BH['upperArm'+X]
    sc=np.linalg.norm(BH['hand'+X]-BH['foreArm'+X])/np.linalg.norm(REF['hand'+X]-REF['elbow'+X])
    R2=rot_between(REF['hand'+X]-REF['elbow'+X],BH['hand'+X]-BH['foreArm'+X])
    for nm in ('foreArm'+X,'hand'+X):
        m=segn==nm; P[m]=((P[m]-REF['elbow'+X])@R2.T)*1.0+BH['foreArm'+X]
for i,v in enumerate(ref.data.vertices): v.co=Vector(P[i])
ref.data.update()
# weights: segment bone with joint blending to parent/child
PAR={'hips':None,sp2:'hips','chest':sp2,uc:'chest','head':'neck'}
for X in ('_L','_R'): PAR.update({'upperArm'+X:'shoulder'+X if 'shoulder'+X in BH else uc,'foreArm'+X:'upperArm'+X,'hand'+X:'foreArm'+X,'thigh'+X:'hips','shin'+X:'thigh'+X,'foot'+X:'shin'+X})
for nm in set(list(PAR.values())+list(PAR.keys())):
    if nm and nm not in ref.vertex_groups: ref.vertex_groups.new(name=nm)
for i in range(len(P)):
    k=si[i]; nm=segn[i]; t=T[k,i] if SEGS[k][0]==nm else 0.5; par=PAR.get(nm)
    if nm=='head': ref.vertex_groups['head'].add([i],1.0,'REPLACE'); continue
    if par and t<0.2: a_=0.5+2.5*t; ref.vertex_groups[nm].add([i],a_,'REPLACE'); ref.vertex_groups[par].add([i],1-a_,'REPLACE')
    else: ref.vertex_groups[nm].add([i],1.0,'REPLACE')
gn=[g.name for g in ref.vertex_groups]
def slot_of(b):
    if b in ('head','neck'): return 'helm'
    for X in ('_L','_R'):
        if b.endswith(X):
            if b.startswith(('upperArm','shoulder')): return 'shoulder'+X
            if b.startswith(('foreArm','hand')): return 'glove'+X
            if b.startswith('thigh'): return 'leg'+X
            if b.startswith(('shin','foot')): return 'boot'+X
    return 'chest'
vslot=np.array([slot_of(n) for n in segn]); print('SEGN',dict(zip(*np.unique(segn,return_counts=True))),'VSLOT',dict(zip(*np.unique(vslot,return_counts=True))),len(P),len(ref.data.polygons))
fslot=[]
for p in ref.data.polygons:
    ss=vslot[list(p.vertices)]; u,c=np.unique(ss,return_counts=True); fslot.append(u[c.argmax()])
fslot=np.array(fslot)
import bmesh
bm=bmesh.new(); bm.from_mesh(ref.data); bm.faces.ensure_lookup_table()
seen=np.zeros(len(bm.faces),bool)
for f0 in bm.faces:
    if seen[f0.index]: continue
    stack=[f0]; comp=[]; seen[f0.index]=True
    while stack:
        f=stack.pop(); comp.append(f.index)
        for e in f.edges:
            for g2 in e.link_faces:
                if not seen[g2.index]: seen[g2.index]=True; stack.append(g2)
    if len(comp)<1500:
        u,c=np.unique(fslot[comp],return_counts=True); fslot[comp]=u[c.argmax()]
bm.free()
TRI={}; SLOTS=['helm','chest','shoulder_L','shoulder_R','glove_L','glove_R','leg_L','leg_R','boot_L','boot_R']
TARGET={'helm':7600,'chest':7900}
# shrink texture for mobile: base colour 1024, drop rm/normal maps
mat=ref.data.materials[0]; nt=mat.node_tree; bsdf=[n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'][0]
for n in list(nt.nodes):
    if n.type=='TEX_IMAGE' and n.image:
        if 'basecolor' in n.image.name.lower() or any(l.to_socket.name=='Base Color' for l in n.outputs['Color'].links):
            n.image.scale(1024,1024)
        else: nt.nodes.remove(n)
for l in list(nt.links):
    if l.to_node.type=='NORMAL_MAP': nt.links.remove(l)
bsdf.inputs['Metallic'].default_value=0.65; bsdf.inputs['Roughness'].default_value=0.38
mat.name=f'ref_{G}_armor'
for sl in SLOTS:
    for x in bpy.data.objects: x.select_set(False)
    ob=ref.copy(); ob.data=ref.data.copy(); bpy.context.collection.objects.link(ob); ob.name=sl
    bm=bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if fslot[f.index]!=sl],context='FACES'); bm.to_mesh(ob.data); bm.free()
    n0=len(ob.data.polygons)
    if n0==0: print('EMPTY',sl); continue
    tgt=TARGET.get(sl,6500)
    bpy.context.view_layer.objects.active=ob; ob.select_set(True)
    if n0>tgt:
        d=ob.modifiers.new('d','DECIMATE'); d.ratio=tgt/n0; bpy.ops.object.modifier_apply(modifier='d')
    elif n0<3600:
        d=ob.modifiers.new('s','SUBSURF'); d.levels=1; d.subdivision_type='SIMPLE'; bpy.ops.object.modifier_apply(modifier='s')
        n1=len(ob.data.polygons)*2
        if n1>tgt: d=ob.modifiers.new('d','DECIMATE'); d.ratio=tgt/n1; bpy.ops.object.modifier_apply(modifier='d')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
    ob.parent=ARM; md=ob.modifiers.new('arm','ARMATURE'); md.object=ARM
    def export(o,path):
        for x in bpy.data.objects: x.select_set(False)
        o.select_set(True); ARM.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path,use_selection=True,export_animations=False,export_skins=True,export_apply=False,export_image_format='JPEG',export_image_quality=88)
    nh=len(ob.data.polygons); export(ob,f'{OUT}/ref_{G}_{sl}.glb')
    lo=ob.copy(); lo.data=ob.data.copy(); bpy.context.collection.objects.link(lo)
    for x in bpy.data.objects: x.select_set(False)
    bpy.context.view_layer.objects.active=lo; lo.select_set(True)
    d=lo.modifiers.new('d','DECIMATE'); d.ratio=0.45; bpy.ops.object.modifier_move_to_index(modifier='d',index=0); bpy.ops.object.modifier_apply(modifier='d')
    nl=len(lo.data.polygons); export(lo,f'{OUT}/ref_{G}_{sl}_lod1.glb')
    TRI[sl]={'src':n0,'high':nh,'lod1':nl,'ratio':round(nl/nh,3)}; print('PIECE',sl,n0,nh,nl)
    bpy.data.objects.remove(lo); bpy.data.objects.remove(ob)
json.dump(TRI,open(f'{OUT}/ref_{G}_tris.json','w'),indent=1)
