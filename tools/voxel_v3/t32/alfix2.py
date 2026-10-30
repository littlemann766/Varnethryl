# arm-in-leg vertex solver v2. Per clip/frame/side, cheapest combo of shoulder abduction (outward, limited in walk/run so total abd <= ABDLIM),
# shoulder flex and elbow flex (forearm forward) that leaves 0 arm verts in leg cells (S grid, dominant weight, RAW). MAXA=0 => measure only.
import bpy,sys,json,math,os
import numpy as np
from mathutils import Matrix,Vector
sys.path.insert(0,'/workspace/t32/tools'); from lib import write_rot,basis_from
a=sys.argv[sys.argv.index('--')+1:]; src,out=a[0],a[1]
S=float(os.environ.get('S','0.018')); DIL=int(os.environ.get('DIL','0')); MAXA=float(os.environ.get('MAXA','40')); ABDLIM=float(os.environ.get('ABDLIM','30'))
bpy.ops.wm.open_mainfile(filepath=src); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
me=ob.data; n=len(me.vertices); co=np.empty(n*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
Mo=np.array(arm.matrix_world.inverted()@ob.matrix_world); co=(Mo@np.c_[co,np.ones(n)].T).T
gi=np.array([v.groups[0].group if v.groups else -1 for v in me.vertices]); gname={g.index:g.name for g in ob.vertex_groups}
def cls(nm):
    l=nm.lower().replace('mixamorig:','')
    if l.startswith('cape'): return 'cape'
    if any(t in l for t in ('upperarm','forearm','leftarm','rightarm','hand','fingers','index','middle','ring','pinky','thumb','weapon')): return 'arm'
    if any(t in l for t in ('thigh','shin','foot','toe','upleg','leftleg','rightleg')): return 'leg'
    return 'body'
GN=np.array([gname.get(g,'') for g in gi]); C=np.array([cls(x) for x in GN])
def side_of(nm):
    l=nm.lower()
    if l.endswith('_l') or 'left' in l: return 'L'
    if l.endswith('_r') or 'right' in l: return 'R'
    return ''
SD=np.array([side_of(x) for x in GN])
def bn(kind,s):
    LR='Left' if s=='L' else 'Right'
    for c in {'ua':('upperArm_'+s,'mixamorig:%sArm'%LR),'fa':('foreArm_'+s,'mixamorig:%sForeArm'%LR)}[kind]:
        if c in arm.pose.bones: return c
groups=[g for g in gname if gname[g] in arm.pose.bones]; idxs={g:np.where(gi==g)[0] for g in groups}
def skin():
    P=np.zeros((n,3))
    for g in groups:
        nm=gname[g]; M=np.array(arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted()); P[idxs[g]]=(M@co[idxs[g]].T).T[:,:3]
    return P
K=np.array([1,1<<21,1<<42],dtype=np.int64)
def keys(X): return (np.floor(X/S).astype(np.int64)+(1<<20))@K
OFF=np.array([(i,j,k) for i in range(-DIL,DIL+1) for j in range(-DIL,DIL+1) for k in range(-DIL,DIL+1)])
def legkeys(X):
    c=np.floor(X/S).astype(np.int64); return np.unique(np.concatenate([((c+o)+(1<<20))@K for o in OFF]))
def rot(axis,deg): return np.array(Matrix.Rotation(math.radians(deg),3,axis))
CAND=sorted([(ab,sf,ef) for ab in np.arange(0,61,3) for sf in (0,10,-10,20,-20) for ef in (0,15,30,45)],key=lambda c:c[0]+1.5*abs(c[1])+c[2])
LOOP=('walk','run','idle','fly','swim','jump_loop'); rep={}
sides=[s for s in 'LR' if bn('ua',s) and bn('fa',s)]
UAM={s:np.where((C=='arm')&(SD==s)&(GN==bn('ua',s)))[0] for s in sides}
FAM={s:np.where((C=='arm')&(SD==s)&(GN!=bn('ua',s)))[0] for s in sides}
def transform(s,X_u,X_f,sh,el,ab,sf,ef,absign,efsign):
    Rs=rot('X',sf)@rot('Y',absign*ab)
    U=(X_u-sh)@Rs.T+sh; el2=(el-sh)@Rs.T+sh; F=(X_f-sh)@Rs.T+sh
    if ef: Re=rot('X',efsign*ef); F=(F-el2)@Re.T+el2
    return U,F,Rs,el2
for act in bpy.data.actions:
    arm.animation_data.action=act; f0,f1=[int(round(x)) for x in act.frame_range]; N=f1-f0+1
    loc=act.name.startswith(('walk','run'))
    corr={s:np.zeros((N,3)) for s in sides}; sgn={s:[1,1] for s in sides}; before={s:0 for s in sides}; after={s:0 for s in sides}; unres={s:0 for s in sides}
    for i in range(N):
        sc.frame_set(f0+i); P=skin(); LK=legkeys(P[C=='leg'])
        for s in sides:
            X_u=P[UAM[s]]; X_f=P[FAM[s]]
            h0=int(np.isin(keys(X_u),LK).sum()+np.isin(keys(X_f),LK).sum()); before[s]=max(before[s],h0)
            if h0==0 or MAXA<=0: continue
            ub=arm.pose.bones[bn('ua',s)]; fb=arm.pose.bones[bn('fa',s)]
            sh=np.array(ub.head); el=np.array(fb.head); u=el-sh
            abd=math.degrees(math.atan2(abs(u[0]),max(-u[2],1e-4))) if -u[2]>0 else 90
            amax=min(MAXA,max(0,ABDLIM-abd)) if loc else MAXA
            # signs: abduction outward (|x| grows), elbow flex forward (-Y)
            hand=X_f.mean(0)
            absign=1 if abs(((hand-sh)@rot('Y',5).T+sh)[0])>abs(hand[0]) else -1
            efsign=1 if (((hand-el)@rot('X',10).T+el)[1])<hand[1] else -1
            best=None
            for ab,sf,ef in CAND:
                if ab>amax: continue
                if loc and sf: continue
                U,F,_,_=transform(s,X_u,X_f,sh,el,ab,sf,ef,absign,efsign)
                h=int(np.isin(keys(U),LK).sum()+np.isin(keys(F),LK).sum())
                if best is None or h<best[0]: best=(h,ab,sf,ef)
                if h==0: break
            corr[s][i]=[absign*best[1],best[2],efsign*best[3]]
            if best[0]: unres[s]+=1
    cyc=act.name.startswith(LOOP)
    for s in sides:
        c=corr[s]
        if not np.abs(c).any(): continue
        w=np.exp(-np.arange(-3,4)**2/2.0); w/=w.sum(); J=lambda j:(j%N if cyc else min(max(j,0),N-1))
        for k in range(3):
            x=c[:,k].copy(); mx=np.array([x[[J(j) for j in range(i-2,i+3)]][np.argmax(np.abs(x[[J(j) for j in range(i-2,i+3)]]))] for i in range(N)])
            y=np.array([sum(ww*mx[J(i+d)] for d,ww in zip(range(-3,4),w)) for i in range(N)])
            c[:,k]=np.where(np.abs(y)<np.abs(x),x,y)
        un=bn('ua',s); fn=bn('fa',s); ub=arm.pose.bones[un]; fb=arm.pose.bones[fn]; qu=[];qf=[]
        for i in range(N):
            sc.frame_set(f0+i); Mu=ub.matrix.copy(); Mf=fb.matrix.copy(); Pm=ub.parent.matrix.copy() if ub.parent else Matrix()
            shv=Mu.translation.copy(); Rs=Matrix.Rotation(math.radians(c[i,1]),4,'X')@Matrix.Rotation(math.radians(c[i,0]),4,'Y')
            A=Matrix.Translation(shv)@Rs@Matrix.Translation(-shv); Mu2=A@Mu; Mf2=A@Mf; e2=Mf2.translation.copy()
            Mf3=Matrix.Translation(e2)@Matrix.Rotation(math.radians(c[i,2]),4,'X')@Matrix.Translation(-e2)@Mf2
            qu.append(basis_from(arm,un,Mu2,Pm)); qf.append(basis_from(arm,fn,Mf3,Mu2))
        write_rot(act,arm,un,f0,qu); write_rot(act,arm,fn,f0,qf)
    if MAXA>0:
        for i in range(N):
            sc.frame_set(f0+i); P=skin(); LK0=np.unique(keys(P[C=='leg']))
            for s in sides:
                am=np.concatenate([UAM[s],FAM[s]]); after[s]=max(after[s],int(np.isin(keys(P[am]),LK0).sum()))
    else: after=before
    rep[act.name]={'before_raw_max':sum(before.values()),'after_raw_max':sum(after.values()),'unresolved_frames':sum(unres.values()),
      'abd_deg_max':{s:round(float(np.abs(corr[s][:,0]).max()),1) for s in sides},'shoulder_flex_max':{s:round(float(np.abs(corr[s][:,1]).max()),1) for s in sides},'elbow_flex_max':{s:round(float(np.abs(corr[s][:,2]).max()),1) for s in sides}}
    print('ALFIX',act.name,rep[act.name],flush=True)
json.dump(rep,open(out+'.alfix.json','w'),indent=1)
if MAXA>0: bpy.ops.wm.save_as_mainfile(filepath=out)
