# v3 contact optimisation: re-home each rigid part to the bone that keeps it in contact with its rest-pose neighbours across the animations
import bpy,sys,json,numpy as np
from mathutils import kdtree
G=sys.argv[-1]; OUT=f'/tmp/kr/{G}'
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/stage3.blend')
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; me=fig.data; ARM.data.pose_position='POSE'; sc=bpy.context.scene
gn=[g.name for g in fig.vertex_groups]; NB=len(gn); N=len(me.vertices)
P=np.array([v.co[:] for v in me.vertices]); pid=np.zeros(N,np.int32); me.attributes['part'].data.foreach_get('value',pid)
Wm=np.zeros((N,NB),np.float32)
for v in me.vertices:
    for g in v.groups: Wm[v.index,g.group]=g.weight
Wm/=np.maximum(Wm.sum(1,keepdims=True),1e-9)
dom=Wm.argmax(1); rigid=Wm.max(1)>=0.999
bi={n:i for i,n in enumerate(gn)}
# sample poses (animations only) -> skinning matrices (constraints evaluated)
for pb in ARM.pose.bones: pb.rotation_mode='QUATERNION'
ARM.animation_data_create()
acts=[a for a in bpy.data.actions if any(k in a.name for k in ('idle','walk','run','attack','hit','death','skill'))]
Ms=[]
for a in acts:
    ARM.animation_data.action=a
    f0,f1=a.frame_range
    for f in np.linspace(f0,f1,6):
        sc.frame_set(int(round(f))); bpy.context.view_layer.update()
        M=np.zeros((NB,4,4))
        for n,i in bi.items():
            pb=ARM.pose.bones[n]; M[i]=np.array(pb.matrix@pb.bone.matrix_local.inverted())
        Ms.append(M)
Ms=np.array(Ms); K=len(Ms); print('poses',K)
Ph=np.c_[P,np.ones(N)]
def posed(ids):   # (K,len,3) via LBS
    w=Wm[ids]; nz=np.unique(np.nonzero(w)[1]); out=np.zeros((K,len(ids),3))
    for b in nz: out+=w[:,b][None,:,None]*np.einsum('kij,nj->kni',Ms[:,b,:3,:],Ph[ids])
    return out
kd=kdtree.KDTree(N)
for i,p in enumerate(P): kd.insert(p,i)
kd.balance()
parts=np.unique(pid); idx={p:np.where(pid==p)[0] for p in parts}
chain=lambda n:n.startswith(('wing','tabard'))
fing=lambda n:any(f in n for f in ('index','middle','ring','pinky','thumb'))
PAR={b.name:(b.parent.name if b.parent else None) for b in ARM.data.bones}
def anc(n):
    out=[n]
    while PAR.get(out[-1]): out.append(PAR[out[-1]])
    return out
def hd(a,b):
    A=anc(a); B=anc(b)
    for i,x in enumerate(A):
        if x in B: return i+B.index(x)
    return 99
changed=[]; rng=np.random.default_rng(0)
for rnd in range(2):
    nch=0
    for p in parts:
        ids=idx[p]
        if not rigid[ids].all() or len(np.unique(dom[ids]))>1 or len(ids)>2500: continue
        b0=gn[dom[ids[0]]]
        if b0.startswith('wing') or fing(b0): continue
        smp=ids if len(ids)<=60 else rng.choice(ids,60,replace=False)
        C=[]
        for vi in smp:
            for co,j,d in kd.find_range(P[vi],0.012):
                if pid[j]!=p: C.append((vi,j,d)); 
        if len(C)<3: continue
        C=np.array(C); a_=C[:,0].astype(int); b_=C[:,1].astype(int); d0=C[:,2]
        Xj=posed(b_)                     # neighbours as currently skinned
        cand=set([dom[ids[0]]])|set(dom[b_][rigid[b_]].tolist())
        cand={c for c in cand if not gn[c].startswith('wing') and (not fing(gn[c]) or fing(b0)) and hd(gn[c],b0)<=2}
        best=None
        for c in cand:
            Xi=np.einsum('kij,nj->kni',Ms[:,c,:3,:],Ph[a_])
            cost=np.abs(np.linalg.norm(Xi-Xj,axis=2)-d0[None]).mean()
            if best is None or cost<best[1]: best=(c,cost)
            if c==dom[ids[0]]: cur=cost
        if best[0]!=dom[ids[0]] and best[1]<0.7*cur and cur>0.004:
            Wm[ids]=0; Wm[ids,best[0]]=1; dom[ids]=best[0]; nch+=1
            changed.append((int(p),b0,gn[best[0]],int(len(ids)),round(cur*1000,1),round(best[1]*1000,1)))
    print('round',rnd,'changed',nch)
import collections
print('MOVES',collections.Counter((a,b) for _,a,b,*_ in changed).most_common(25))
for p,b0,b1,*_ in changed:
    L=[int(x) for x in idx[p]]
    for g in fig.vertex_groups: g.remove(L)
    fig.vertex_groups[b1].add(L,1.0,'REPLACE')
r=json.load(open(OUT+'/bind3_report.json')); r['contact_rehomed']=len(changed); r['contact_moves']=changed[:200]; json.dump(r,open(OUT+'/bind3_report.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/stage3.blend')
