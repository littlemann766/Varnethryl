# arm-in-leg vertex solver: per clip/frame/side, smallest outward shoulder rotation (about the body forward axis, then also forward flex) that leaves 0 arm verts in leg cells (18 mm grid, dominant weight, as check1, RAW - no rest subtraction)
import bpy,sys,json,math,os
import numpy as np
from mathutils import Matrix,Vector
sys.path.insert(0,'/workspace/t32/tools'); from lib import write_rot,basis_from
a=sys.argv[sys.argv.index('--')+1:]; src,out=a[0],a[1]
S=float(os.environ.get('S','0.018')); DIL=int(os.environ.get('DIL','0')); MAXA=float(os.environ.get('MAXA','40'))
bpy.ops.wm.open_mainfile(filepath=src); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
me=ob.data; n=len(me.vertices); co=np.empty(n*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
Mo=np.array(arm.matrix_world.inverted()@ob.matrix_world); co=(Mo@np.c_[co,np.ones(n)].T).T  # armature space homog
gi=np.array([v.groups[0].group if v.groups else -1 for v in me.vertices]); gname={g.index:g.name for g in ob.vertex_groups}
def cls(nm):
    l=nm.lower().replace('mixamorig:','')
    if l.startswith('cape'): return 'cape'
    if any(t in l for t in ('upperarm','forearm','leftarm','rightarm','hand','fingers','index','middle','ring','pinky','thumb','weapon')): return 'arm'
    if any(t in l for t in ('thigh','shin','foot','toe','upleg','leftleg','rightleg')): return 'leg'
    return 'body'
C=np.array([cls(gname.get(g,'')) for g in gi])
def side_of(nm):
    l=nm.lower()
    if l.endswith('_l') or 'left' in l: return 'L'
    if l.endswith('_r') or 'right' in l: return 'R'
    return None
SD=np.array([side_of(gname.get(g,'')) or '' for g in gi])
def ua_name(s):
    for c in (('upperArm_'+s),('mixamorig:%sArm'%('Left' if s=='L' else 'Right'))):
        if c in arm.pose.bones: return c
def fa_name(s):
    for c in (('foreArm_'+s),('mixamorig:%sForeArm'%('Left' if s=='L' else 'Right'))):
        if c in arm.pose.bones: return c
groups=[g for g in gname if gname[g] in arm.pose.bones]
idxs={g:np.where(gi==g)[0] for g in groups}
def skin():
    P=np.zeros((n,3))
    for g in groups:
        nm=gname[g]; M=np.array(arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted())
        P[idxs[g]]=(M@co[idxs[g]].T).T[:,:3]
    return P
K=np.array([1,1<<21,1<<42],dtype=np.int64)
def keys(X): return (np.floor(X/S).astype(np.int64)+(1<<20))@K
OFF=np.array([(i,j,k) for i in range(-DIL,DIL+1) for j in range(-DIL,DIL+1) for k in range(-DIL,DIL+1)])
def legkeys(X):
    c=np.floor(X/S).astype(np.int64)
    return np.unique(np.concatenate([((c+o)+(1<<20))@K for o in OFF]))
LOOP=('walk','run','idle','fly','swim','jump_loop')
rep={}
for act in bpy.data.actions:
    arm.animation_data.action=act; f0,f1=[int(round(x)) for x in act.frame_range]; N=f1-f0+1
    sides=[s for s in 'LR' if ua_name(s)]
    corr={s:np.zeros((N,2)) for s in sides}; before={s:0 for s in sides}; after={s:0 for s in sides}
    cache=[]
    for i in range(N):
        sc.frame_set(f0+i); P=skin(); LK=legkeys(P[C=='leg'])
        for s in sides:
            am=np.where((C=='arm')&(SD==s))[0]
            if not len(am): continue
            X=P[am]; h0=int(np.isin(keys(X),LK).sum()); before[s]=max(before[s],h0)
            if h0==0: continue
            ub=arm.pose.bones[ua_name(s)]; sh=np.array(ub.head)
            out_sign=1 if s=='L' else -1   # +x is character left for Beth rig (checked below per frame)
            hand=X.mean(0); 
            best=None
            for fl in (0,10,20,30):           # forward flex (about lateral axis) after abduction
                for ab in np.arange(0,MAXA+0.1,2.0):
                    for sg in (1,-1):
                        Ra=Matrix.Rotation(math.radians(sg*ab),3,'Y'); Rf=Matrix.Rotation(math.radians(-fl),3,'X')
                        R=np.array(Rf@Ra); Y=(X-sh)@R.T+sh
                        if ab>0 and abs(Y.mean(0)[0])<abs(hand[0]): continue  # must move outward
                        if fl>0 and Y.mean(0)[1]>hand[1]: Rf=Matrix.Rotation(math.radians(fl),3,'X'); R=np.array(Rf@Ra); Y=(X-sh)@R.T+sh
                        h=int(np.isin(keys(Y),LK).sum())
                        if best is None or h<best[0] or (h==best[0] and ab+fl<best[1]): best=(h,ab+fl,sg*ab,(fl if Y.mean(0)[1]<=hand[1] else -fl) if fl else 0)
                        if h==0: break
                    if best and best[0]==0: break
                if best and best[0]==0: break
            corr[s][i]=[best[2],best[3]]
    # smooth: max-hold +-2 frames then gaussian
    cyc=act.name.startswith(LOOP)
    for s in sides:
        c=corr[s]
        if not np.abs(c).any(): continue
        for k in range(2):
            x=c[:,k]; mx=np.array([x[[j%N if cyc else min(max(j,0),N-1) for j in range(i-2,i+3)]][np.argmax(np.abs(x[[j%N if cyc else min(max(j,0),N-1) for j in range(i-2,i+3)]]))] for i in range(N)])
            w=np.exp(-np.arange(-3,4)**2/2.0); w/=w.sum()
            c[:,k]=np.array([sum(ww*mx[(i+d)%N if cyc else min(max(i+d,0),N-1)] for d,ww in zip(range(-3,4),w)) for i in range(N)])
            # keep at least the needed value where needed
            c[:,k]=np.where(np.abs(c[:,k])<np.abs(x),x,c[:,k])
        un=ua_name(s); ub=arm.pose.bones[un]; qs=[]
        for i in range(N):
            sc.frame_set(f0+i); Mu=ub.matrix.copy(); Pm=ub.parent.matrix.copy() if ub.parent else Matrix()
            shv=Mu.translation.copy(); R=Matrix.Rotation(math.radians(c[i,1]),4,'X')@Matrix.Rotation(math.radians(c[i,0]),4,'Y')
            Mn=Matrix.Translation(shv)@R@Matrix.Translation(-shv)@Mu
            qs.append(basis_from(arm,un,Mn,Pm))
        write_rot(act,arm,un,f0,qs)
    # re-measure
    for i in range(N):
        sc.frame_set(f0+i); P=skin(); LK0=np.unique(keys(P[C=='leg']))
        for s in sides:
            am=np.where((C=='arm')&(SD==s))[0]
            if len(am): after[s]=max(after[s],int(np.isin(keys(P[am]),LK0).sum()))
    rep[act.name]={'before_raw_max':sum(before.values()),'after_raw_max':sum(after.values()),'abd_deg_max':{s:round(float(np.abs(corr[s][:,0]).max()),1) for s in sides},'flex_deg_max':{s:round(float(np.abs(corr[s][:,1]).max()),1) for s in sides}}
    print('ALFIX',act.name,rep[act.name],flush=True)
json.dump(rep,open(out+'.alfix.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out)
