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
# ---------- v3 deform helper bones (identity rest like the core rig) ----------
for X in ('_L','_R'):
    add('pauldron'+X,'shoulder'+X,BH['upperArm'+X]+np.array([0,0,0.02]))
    add('elbow'+X,'upperArm'+X,BH['foreArm'+X])
    add('knee'+X,'thigh'+X,BH['shin'+X])
    add('tasset'+X,'hips',BH['thigh'+X]+np.array([0,0,0.03]))
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
# ---- v3: NO cutting. joint-spanning (connective) parts get a short smooth weight band across each label boundary
from mathutils import kdtree
lab=VL.astype(str); band_v=np.zeros(len(P),bool)
nbl=[[] for _ in range(len(P))]
for e in me.edges:
    a,b=e.vertices; nbl[a].append(b); nbl[b].append(a)
for p in up_:
    if kind.get(p)!='split': continue
    ids=idx[p]; c=cls.get(p,'')
    L_=lab[ids].copy(); u_,cn_=np.unique(L_,return_counts=True); mj=u_[cn_.argmax()]
    adj=lambda a,b:PARENT.get(a)==b or PARENT.get(b)==a or a==b
    # labels not adjacent (in the hierarchy) to the part's majority bone are mislabels (e.g. gauntlet touching thigh): fold into majority
    for l in u_:
        if not adj(l,mj) and not any(adj(l,m2) and adj(m2,mj) and (L_==m2).sum()>0.2*len(ids) for m2 in u_): L_[L_==l]=mj
    lab[ids]=L_
    BAND=0.08 if c.startswith('tabard') else (0.05 if c.startswith('wing') else (0.12 if any(x.startswith('shoulder') for x in np.unique(L_)) else 0.10))
    for l in np.unique(L_):
        own=ids[L_==l]; oth=ids[L_!=l]
        if len(oth)==0: continue
        kd=kdtree.KDTree(len(oth))
        for i,vi in enumerate(oth): kd.insert(P[vi],i)
        kd.balance()
        for vi in own:
            co,j,d=kd.find(P[vi]); x=np.clip(d/BAND,0,1); s=x*x*(3-2*x)   # smoothstep falloff
            wc=0.5*(1-s)
            if os.environ.get('NOBAND') or wc<1e-3 or not adj(l,lab[oth[j]]): W[vi]={l:1.0}
            else: W[vi]={l:1-wc,lab[oth[j]]:wc}; band_v[vi]=True
blend_v=band_v.copy()
print('BAND verts',int(band_v.sum()))
# forearm: blended verts near the wrist share with the twist bone (anti candy-wrapper)
for vi in np.where(blend_v)[0]:
    w=W[vi]
    for X in ('_L','_R'):
        if 'foreArm'+X in w:
            _,t=segd(P[vi][None],BH['foreArm'+X],BH['hand'+X]); t=t[0]
            if t>0.5: f=(t-0.5)*2*0.6; x=w.pop('foreArm'+X); w['foreArm'+X]=x*(1-f); w['foreArm_twist'+X]=x*f
for vi in range(len(P)):
    if vi not in W: W[vi]={'hips':1.0}
# ---------- v3 rigid-part re-homing: stray fragments, pauldrons, couters, poleyns, tassets ----------
kdA=kdtree.KDTree(len(P))
for i,p_ in enumerate(P): kdA.insert(p_,i)
kdA.balance()
vbone=np.array([max(W[i],key=W[i].get) for i in range(len(P))],dtype=object)
psize={p:len(idx[p]) for p in up_}
RH={'fragment':0,'pauldron':0,'elbow':0,'knee':0,'tasset':0}
def rehome(p,b):
    if os.environ.get('NOHELP') and b.startswith(('pauldron','elbow','knee','tasset')): return
    for vi in idx[p]: W[vi]={b:1.0}
    vbone[idx[p]]=b
for p in up_:
    c=cen[p]
    if kind.get(p)=='rigid' and str(cls.get(p,'')).startswith('tabard') and c[2]<BH['hips'][2]:
        for X,sg in (('_L',1),('_R',-1)):
            if sg*c[0]>=0.09: rehome(p,'tasset'+X); RH['tasset']+=1
        continue
    if kind.get(p)!='rigid' or cls.get(p): continue
    ids=idx[p]; b0=vbone[ids[0]]; c=cen[p]
    if any(f in b0 for f in ('index','middle','ring','pinky','thumb')): continue
    for X,sg in (('_L',1),('_R',-1)):
        if psize[p]<120 and b0 in ('upperArm'+X,'shoulder'+X):
            votes={}
            for vi in ids[::max(1,len(ids)//12)]:
                for co,j,d in kdA.find_range(P[vi],0.025):
                    if pid[j]==p or psize.get(pid[j],0)<300: continue
                    votes[vbone[j]]=votes.get(vbone[j],0)+1
            if votes:
                bb=max(votes,key=votes.get)
                if bb in ('chest','upperChest','spine2','neck') and votes[bb]>=0.6*sum(votes.values()): rehome(p,bb); RH['fragment']+=1; break
        if b0 in ('upperArm'+X,'shoulder'+X) and c[2]>BH['upperArm'+X][2]-0.05 and sg*c[0]>sg*BH['upperArm'+X][0]-0.06: rehome(p,'pauldron'+X); RH['pauldron']+=1; break
        if b0 in ('upperArm'+X,'foreArm'+X) and np.linalg.norm(c-BH['foreArm'+X])<0.05: rehome(p,'elbow'+X); RH['elbow']+=1; break
        if b0 in ('thigh'+X,'shin'+X) and np.linalg.norm(c-BH['shin'+X])<0.06 and c[1]<BH['shin'+X][1]: rehome(p,'knee'+X); RH['knee']+=1; break
        if b0=='hips' and c[2]<BH['thigh'+X][2]+0.03 and sg*c[0]>=0.07: rehome(p,'tasset'+X); RH['tasset']+=1; break
print('REHOME',RH)
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
# ---------- v3 helper drivers (baked into the exported animations) ----------
pb=ARM.pose.bones
def cr(bn,src,inf,axes=(1,1,1)):
    c=pb[bn].constraints.new('COPY_ROTATION'); c.target=ARM; c.subtarget=src; c.target_space='LOCAL'; c.owner_space='LOCAL'; c.mix_mode='ADD'; c.influence=inf
    c.use_x,c.use_y,c.use_z=[bool(a) for a in axes]
for X in ('_L','_R'):
    cr('pauldron'+X,'upperArm'+X,0.45); cr('elbow'+X,'foreArm'+X,0.5); cr('knee'+X,'shin'+X,0.5); cr('tasset'+X,'thigh'+X,0.85)
for t in ('tabard_F_01','tabard_B_01'):
    if t in pb and not os.environ.get('NOTAB'): cr(t,'thigh_L',0.35,(1,0,0)); cr(t,'thigh_R',0.35,(1,0,0))
for t in ('tabard_F_02','tabard_B_02'):
    if t in pb and not os.environ.get('NOTAB'): cr(t,'thigh_L',0.15,(1,0,0)); cr(t,'thigh_R',0.15,(1,0,0))
report['rehome']=RH; report['band_verts']=int(band_v.sum())
exec(open('/tmp/kr/retarget_fix.py').read().replace('for b in CH_: CORR[b]','for b in (CH_ if not os.environ.get("NORT") else []): CORR[b]').replace("for b in ('hand'+X,'foot'+X): CORR[b]","for b in (('hand'+X,'foot'+X) if not os.environ.get('NORT') else ()): CORR[b]"))
print('REPORT3',json.dumps(report))
json.dump(report,open(OUT+'/bind3_report.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/stage3.blend')
