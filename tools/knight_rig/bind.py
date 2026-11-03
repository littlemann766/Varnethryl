import bpy,sys,os,json,math,numpy as np
from mathutils import Vector
G=sys.argv[-1]; OUT=f'/tmp/kr/{G}'
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/stage1.blend')
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; me=fig.data
P=np.array([v.co[:] for v in me.vertices]); pid=np.zeros(len(P),np.int32); me.attributes['part'].data.foreach_get('value',pid)
BH={b.name:np.array(b.head_local) for b in ARM.data.bones}
up_=np.unique(pid); idx={p:np.where(pid==p)[0] for p in up_}
cen={p:P[idx[p]].mean(0) for p in up_}; spy=BH['spine'][1]
# ---------- secondary chains ----------
bpy.context.view_layer.objects.active=ARM
for x in bpy.data.objects: x.select_set(False)
ARM.select_set(True); bpy.ops.object.mode_set(mode='EDIT'); eb=ARM.data.edit_bones
def add(name,parent,head,length=0.05):
    b=eb.new(name); b.head=Vector(head); b.tail=Vector(head)+Vector((0,length,0)); b.roll=0; b.parent=eb[parent]; return b
CH={}   # chain name -> list of (bone, joint) + end
def chain(nm,parent,pts):
    bones=[]
    for i in range(len(pts)-1):
        add(f'{nm}_{i+1:02d}',parent if i==0 else f'{nm}_{i:02d}',pts[i]); bones.append(f'{nm}_{i+1:02d}')
    CH[nm]=(bones,np.array(pts))
cls={}
uc='upperChest'
for p in up_:
    c=cen[p]
    if c[1]-spy>0.10 and c[2]>BH['upperArm_L'][2]-0.12: cls[p]='wing_L' if c[0]>0 else 'wing_R'
for X,sg in (('_L',1),('_R',-1)):
    ws=[p for p in up_ if cls.get(p)=='wing'+X]
    if not ws: continue
    Q=np.vstack([P[idx[p]] for p in ws]); root=BH[uc]+np.array([sg*0.07,0.10,0.02])
    dd=np.linalg.norm(Q-root,axis=1); tip=Q[dd>=np.percentile(dd,97)].mean(0)
    # curved chain through the wing's mass: 4 segments, joints at quantiles of distance from root
    js=[root]
    for qq in (0.30,0.55,0.78):
        r=np.percentile(dd,qq*100); ring=Q[np.abs(dd-r)<0.03]; js.append(ring.mean(0) if len(ring) else root+(tip-root)*qq)
    js.append(tip); chain('wing'+X,uc,js)
for p in up_:
    if p in cls: continue
    c=cen[p]
    if abs(c[0])<0.10 and c[1]-spy<-0.06 and 0.35<c[2]<BH['hips'][2]+0.02: cls[p]='tabard_F'
    elif abs(c[0])<0.24 and c[1]-spy>0.07 and 0.30<c[2]<BH['chest'][2]: cls[p]='tabard_B'
for nm,sgn in (('tabard_F',-1),('tabard_B',1)):
    ps=[p for p in up_ if cls.get(p)==nm]
    if not ps: continue
    Q=np.vstack([P[idx[p]] for p in ps]); top=min(Q[:,2].max(),BH['hips'][2]+0.05); bot=Q[:,2].min()
    yy=np.median(Q[:,1]); js=[np.array([0,yy,top-(top-bot)*t]) for t in (0,0.33,0.66,1.0)]
    chain(nm,'hips',js)
bpy.ops.object.mode_set(mode='OBJECT')
BH={b.name:np.array(b.head_local) for b in ARM.data.bones}
# ---------- core segments ----------
sp2='spine2'
SEG=[('hips',BH['hips']-np.array([0,0,0.10]),BH['spine2']),('spine2',BH['spine2'],BH['chest']),('chest',BH['chest'],BH[uc]),(uc,BH[uc],BH['neck']),('neck',BH['neck'],BH['head']),('head',BH['head'],BH['head']+np.array([0,0,0.28]))]
fingers=['index','middle','ring','pinky','thumb']
for X,sg in (('_L',1),('_R',-1)):
    SEG+=[('shoulder'+X,BH['shoulder'+X],BH['upperArm'+X]),('upperArm'+X,BH['upperArm'+X],BH['foreArm'+X]),('foreArm'+X,BH['foreArm'+X],BH['hand'+X]),
          ('hand'+X,BH['hand'+X],BH['fingers'+X]),('thigh'+X,BH['thigh'+X],BH['shin'+X]),('shin'+X,BH['shin'+X],BH['foot'+X]),
          ('foot'+X,BH['foot'+X],BH['toe'+X]),('toe'+X,BH['toe'+X],BH['toe'+X]+np.array([0,-0.08,-0.02]))]
    for f in fingers:
        for k in (1,2,3):
            a=BH[f'{f}{k}{X}']; b=BH[f'{f}{k+1}{X}'] if k<3 else a+(a-BH[f'{f}{k-1}{X}'])
            SEG.append((f'{f}{k}{X}',a,b))
def segd(Q,a,b):
    d=b-a; t=np.clip(((Q-a)@d)/max(d@d,1e-9),0,1); return np.linalg.norm(Q-a-t[:,None]*d,axis=1),t
D=np.array([segd(P,a,b)[0] for _,a,b in SEG]); near=D.argmin(0); segn=np.array([s[0] for s in SEG])
# ---------- per-part classification ----------
PARENT={b.name:(b.parent.name if b.parent else None) for b in ARM.data.bones}
def limb(b):
    for k in ('upperArm','foreArm','thigh','shin','hand','foot'):
        if b.startswith(k): return k
    return 'torso'
W={}   # vertex -> {bone:w}
report={'rigid':0,'blended':0,'chain_rigid':0,'chain_blended':0,'split':0}; kind={}; VL=np.array(['']*len(P),dtype=object)
TW={'upperArm':'upperArm_twist','foreArm':'foreArm_twist','thigh':'thigh_twist','shin':'shin_twist'}
def blend_chain(ids,bones,J):
    Q=P[ids]; best=None
    dists=[]; ts=[]
    for i in range(len(bones)): d_,t_=segd(Q,J[i],J[i+1]); dists.append(d_); ts.append(t_)
    dists=np.array(dists); k=dists.argmin(0)
    for n,vi in enumerate(ids):
        i=k[n]; t=ts[i][n]; w={bones[i]:1.0}
        if t<0.5 and i>0: a=0.5+t; w={bones[i]:a,bones[i-1]:1-a}            # v2: full-length linear blend (cloth bends, no shear band)
        elif t>=0.5 and i<len(bones)-1: a=1.5-t; w={bones[i]:a,bones[i+1]:1-a}
        W[vi]=w
for p in up_:
    ids=idx[p]; c=cls.get(p)
    if c and c in CH:
        bones,J=CH[c]; d_=[segd(cen[p][None],J[i],J[i+1])[0][0] for i in range(len(bones))]
        spanned=np.ptp(P[ids]@((J[-1]-J[0])/np.linalg.norm(J[-1]-J[0])))
        seglen=np.linalg.norm(J[1]-J[0])
        if spanned>=0.6*seglen:   # v3: wings AND tabards   # wing membrane: split per chain segment, each slice rigid
            dd=np.array([segd(P[ids],J[i],J[i+1])[0] for i in range(len(bones))]); VL[ids]=np.array(bones)[dd.argmin(0)]
            report['split']+=1; kind[p]='split'; continue
        if spanned<0.6*seglen:   # feather / small flap: rigid to its segment
            b=bones[int(np.argmin(d_))]
            for vi in ids: W[vi]={b:1.0}
            report['chain_rigid']+=1; kind[p]='rigid'
        else: blend_chain(ids,bones,J); report['chain_blended']+=1; kind[p]='blend'
        continue
    ns=segn[near[ids]]; u,cn=np.unique(ns,return_counts=True); maj=u[cn.argmax()]; share=cn.max()/len(ids)
    limbs=set(limb(x) for x,cc in zip(u,cn) if cc>=0.15*len(ids))
    big=len(ids)>150
    soft=big and len(limbs)>1 and share<0.80   # spans a limb joint with real mass on both sides -> connective (mail/leather/cloth)
    if not soft:
        for vi in ids: W[vi]={maj:1.0}
        report['rigid']+=1; kind[p]='rigid'
    else:
        VL[ids]=ns; report['split']+=1; kind[p]='split'   # spans a joint: cut along the joint, every slice rigid
# ---- cut split parts along label boundaries (bmesh edge split), then each vertex is rigid to its face label
import bmesh
FL=[]
for f in me.polygons:
    vs=list(f.vertices); lab=VL[vs]
    if lab[0]=='' : FL.append('')
    else: u,c=np.unique(lab.astype(str),return_counts=True); FL.append(u[c.argmax()])
bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table()
cut=[e for e in bm.edges if len(e.link_faces)==2 and FL[e.link_faces[0].index]!='' and FL[e.link_faces[0].index]!=FL[e.link_faces[1].index]]
fl_layer=bm.faces.layers.int.new('fl'); names=sorted(set(x for x in FL if x)); nid={n:i+1 for i,n in enumerate(names)}
for f in bm.faces: f[fl_layer]=nid.get(FL[f.index],0)
oldidx=bm.verts.layers.int.new('oldv')
for v in bm.verts: v[oldidx]=v.index
bmesh.ops.split_edges(bm,edges=cut)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
newW={}; 
for v in bm.verts:
    labs=set(f[fl_layer] for f in v.link_faces)
    o=v[oldidx]
    if 0 in labs or not labs: newW[v.index]=W.get(o)
    else: newW[v.index]={names[min(labs)-1]:1.0}
NB=len(bm.verts); bm.to_mesh(me); bm.free(); me.update()
W={k:v for k,v in newW.items() if v is not None}
P=np.array([v.co[:] for v in me.vertices]); pid=np.zeros(len(P),np.int32); me.attributes['part'].data.foreach_get('value',pid)
print('CUT edges',len(cut),'verts now',len(P))
# Laplacian smoothing of blended parts
blend_v=np.zeros(len(P),bool)
for p in up_:
    if kind[p]=='blend': blend_v[pid==p]=True
nb=[[] for _ in range(len(P))]
for e in me.edges:
    a,b=e.vertices
    if blend_v[a]: nb[a].append(b)
    if blend_v[b]: nb[b].append(a)
for it in range(6):
    NW={}
    for vi in np.where(blend_v)[0]:
        acc=dict(W[vi]); n=1.0
        for j in nb[vi]:
            for k,x in W[j].items(): acc[k]=acc.get(k,0)+x
            n+=1
        tot=sum(acc.values()); top=sorted(acc.items(),key=lambda kv:-kv[1])[:4]; s_=sum(x for _,x in top)
        NW[vi]={k:x/s_ for k,x in top if x/s_>0.01}
    W.update(NW)
# forearm: blended verts near the wrist share with the twist bone (anti candy-wrapper)
for vi in np.where(blend_v)[0]:
    w=W[vi]
    for X in ('_L','_R'):
        if 'foreArm'+X in w:
            _,t=segd(P[vi][None],BH['foreArm'+X],BH['hand'+X]); t=t[0]
            if t>0.5: f=(t-0.5)*2*0.6; x=w.pop('foreArm'+X); w['foreArm'+X]=x*(1-f); w['foreArm_twist'+X]=x*f
for vi in range(len(P)):
    if vi not in W: W[vi]={'hips':1.0}
# ---------- write groups ----------
fig.vertex_groups.clear()
for b in ARM.data.bones: fig.vertex_groups.new(name=b.name)
for vi,w in W.items():
    for b,x in w.items(): fig.vertex_groups[b].add([int(vi)],float(x),'REPLACE')
ka=me.attributes.new('blended','INT','POINT'); ka.data.foreach_set('value',blend_v.astype(np.int32))
fig.parent=ARM; md=fig.modifiers.new('arm','ARMATURE'); md.object=ARM
# twist constraint for validation (Godot: CopyTransformModifier3D or bake)
pb=ARM.pose.bones
for X in ('_L','_R'):
    c=pb['foreArm_twist'+X].constraints.new('COPY_ROTATION'); c.target=ARM; c.subtarget='hand'+X; c.target_space='LOCAL'; c.owner_space='LOCAL'; c.mix_mode='ADD'; c.influence=0.5
cnts={k:sum(1 for p in up_ if cls.get(p,'').startswith(k)) for k in ('wing','tabard_F','tabard_B')}
report.update(parts=len(up_),chains={k:v[0] for k,v in CH.items()},chain_parts=cnts,bones=len(ARM.data.bones))
print('REPORT',json.dumps(report))
json.dump(report,open(OUT+'/bind_report.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/stage2.blend')
