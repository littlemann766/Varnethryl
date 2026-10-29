# Titan v2: heavy UAL walk retarget + ground-contact slams.
# blender -b -P tw2.py -- <src glb|blend> <out prefix> [steps: walk,slams]
import bpy,sys,os,math,json,re
import numpy as np
from mathutils import Matrix,Vector,Quaternion
a=sys.argv[sys.argv.index('--')+1:]; src,out=a[0],a[1]; steps=a[2].split(',') if len(a)>2 else ['walk','slams']
if src.endswith('.blend'): bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=30; bpy.context.scene.render.fps_base=1
    bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
T=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
for act in bpy.data.actions: act.name=act.name.split('_'+T.name)[0]; act.use_fake_user=True
body=max([o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==T],key=lambda o:len(o.data.vertices))
TB=T.data.bones; Tinv=T.matrix_world.inverted()
M2G=114.0/21.14; GOAL=-0.01/M2G   # target lowest point: 1 cm (game) into the ground
order=[]
def _w(b): order.append(b.name); [_w(c) for c in b.children]
[_w(b) for b in TB if not b.parent]
def wrest(arm,n): return arm.matrix_world@arm.data.bones[n].matrix_local
REST={n:wrest(T,n) for n in order}; RESTI={n:REST[n].inverted() for n in order}
# ---------- regions + LBS ----------
GN={g.index:g.name for g in body.vertex_groups}
def reg(n):
    if n[-2:] not in('_L','_R'): return None
    s=n[-1]; b=n[:-2].rstrip('0123456789')
    if b in('hand','fingers','thumb','index','middle','ring','pinky'): return 'fist_'+s
    if b=='foreArm': return 'forearm_'+s
    if b in('foot','toe','shin'): return 'foot_'+s
    return None
Mw=body.matrix_world; RV={}
for v in body.data.vertices:
    if not v.groups: continue
    r=reg(GN[max(v.groups,key=lambda g:g.weight).group])
    if r: RV.setdefault(r,[]).append(v)
LB={}
for r,vs in RV.items():
    if r.startswith('foot'):  # only the sole matters: lowest 30% of the region at rest
        zs=sorted((Mw@v.co).z for v in vs); cut=zs[int(len(zs)*0.3)]; vs=[v for v in vs if (Mw@v.co).z<=cut]
    P=np.array([list(Mw@v.co)+[1.0] for v in vs]); bl={}
    for i,v in enumerate(vs):
        tot=sum(g.weight for g in v.groups if GN[g.group] in TB) or 1
        for g in v.groups:
            n=GN[g.group]
            if n in TB and g.weight>0: bl.setdefault(n,np.zeros(len(vs)))[i]+=g.weight/tot
    LB[r]=(P,bl)
for s_ in 'LR':
    if 'fist_'+s_ in LB and 'forearm_'+s_ in LB:
        P1,b1=LB['fist_'+s_]; P2,b2=LB['forearm_'+s_]; bl={}
        for n_ in set(b1)|set(b2): bl[n_]=np.concatenate([b1.get(n_,np.zeros(len(P1))),b2.get(n_,np.zeros(len(P2)))])
        LB['arm_'+s_]=(np.vstack([P1,P2]),bl)
def RG(e): return e if e.startswith('foot') else 'arm_'+e[-1]
def rmin(W,r):
    P,bl=LB[r]; acc=np.zeros((len(P),3))
    for n,w in bl.items():
        M=np.array(W[n]@RESTI[n]); acc+=w[:,None]*(P@M.T)[:,:3]
    return float(acc[:,2].min())

from mathutils.bvhtree import BVHTree
_V=body.data.vertices; NV=len(_V)
_P=np.array([list(Mw@v.co)+[1.0] for v in _V])
_WB={}
for v in _V:
    tot=sum(g.weight for g in v.groups if GN[g.group] in TB) or 1
    for g in v.groups:
        n_=GN[g.group]
        if n_ in TB and g.weight>0: _WB.setdefault(n_,{})[v.index]=g.weight/tot
_WBI={n_:(np.array(list(d.keys())),np.array(list(d.values()))) for n_,d in _WB.items()}
def _dom(v): return GN[max(v.groups,key=lambda g:g.weight).group] if v.groups else ''
_LEGV=set(); _ARMV={'L':[],'R':[]}
for v in _V:
    n_=_dom(v)
    if n_.startswith(('thigh_','shin_','foot_')): _LEGV.add(v.index)
    elif n_[-2:] in ('_L','_R') and n_.split('_')[0].rstrip('0123456789') in ('upperArm','foreArm','hand','fingers','thumb','index','middle','ring','pinky'): _ARMV[n_[-1]].append(v.index)
_LP=[list(p.vertices) for p in body.data.polygons if all(i in _LEGV for i in p.vertices)]
_DIR=Vector((0.0123,0.0071,0.99991)).normalized(); _H=21.14
def lbs_all(W):
    acc=np.zeros((NV,3))
    for n_,(ix,w) in _WBI.items():
        M=np.array(W[n_]@RESTI[n_]); acc[ix]+=w[:,None]*(_P[ix]@M.T)[:,:3]
    return acc
def n_inside(W):
    co=lbs_all(W); cv=[Vector(c) for c in co]
    bvh=BVHTree.FromPolygons(cv,_LP,all_triangles=False); c=0
    for s_ in 'LR':
        for i in _ARMV[s_][::3]:
            r=bvh.find_nearest(cv[i],_H*0.2)
            if r[0] is None or (cv[i]-r[0]).length>0.06*_H: continue
            hits=0;o=cv[i].copy()
            for _ in range(20):
                h=bvh.ray_cast(o,_DIR)
                if h[0] is None: break
                hits+=1;o=h[0]+_DIR*1e-5*_H
            if hits%2==1: c+=1
    return c
# ---------- pose helpers ----------
def getW():
    return {n:T.matrix_world@T.pose.bones[n].matrix for n in order}
def subtree(n): return [c.name for c in TB[n].children_recursive]
def xform_sub(W,n,M):
    for c in [n]+subtree(n): W[c]=M@W[c]
def two_bone(W,a_,b_,c_,target,keep_rot=None,pole_hint=None):
    A=W[a_].translation; B=W[b_].translation; C=W[c_].translation
    rotC=(keep_rot if keep_rot is not None else W[c_].to_3x3()).copy()
    l1=(B-A).length; l2=(C-B).length
    d=target-A; L=min(d.length,l1+l2-1e-4); L=max(L,abs(l1-l2)+1e-4); dn=d.normalized()
    pole=(B-A)-dn*((B-A).dot(dn))
    if pole_hint is not None and (pole.length<0.05*l1 or os.environ.get('POLE','1')=='1'):
        ph=pole_hint-dn*pole_hint.dot(dn)
        if ph.length>1e-4: pole=ph
    if pole.length<1e-6: pole=Vector((0,-1,0))
    pole.normalize()
    ang=math.acos(max(-1,min(1,(l1*l1+L*L-l2*l2)/(2*l1*L))))
    Bn=A+(dn*math.cos(ang)+pole*math.sin(ang))*l1; Cn=A+dn*L
    r1=(B-A).normalized().rotation_difference((Bn-A).normalized()).to_matrix()
    xform_sub(W,a_,Matrix.Translation(A)@r1.to_4x4()@Matrix.Translation(-A))
    B2=W[b_].translation; C2=W[c_].translation
    r2=(C2-B2).normalized().rotation_difference((Cn-B2).normalized()).to_matrix()
    xform_sub(W,b_,Matrix.Translation(B2)@r2.to_4x4()@Matrix.Translation(-B2))
    p=W[c_].translation.copy(); cur=W[c_].to_3x3()
    xform_sub(W,c_,Matrix.Translation(p)@(rotC@cur.inverted()).to_4x4()@Matrix.Translation(-p))
    return (target-A).length<=l1+l2
def apply(W,f):
    for n in order:
        b=TB[n]; pb=T.pose.bones[n]; Ma=Tinv@W[n]
        if b.parent: pb.matrix_basis=(b.parent.matrix_local.inverted()@b.matrix_local).inverted()@(Tinv@W[b.parent.name]).inverted()@Ma
        else: pb.matrix_basis=b.matrix_local.inverted()@Ma
        pb.rotation_mode='QUATERNION'
        pb.keyframe_insert('rotation_quaternion',frame=f); pb.keyframe_insert('location',frame=f)
        if f==0 or True: pb.scale=(1,1,1); pb.keyframe_insert('scale',frame=f)
def new_action(name):
    old=bpy.data.actions.get(name)
    if old: old.name=name+'__old'
    act=bpy.data.actions.new(name); act.use_fake_user=True; T.animation_data_create(); T.animation_data.action=act
    return act,old
LEGS={'L':('thigh_L','shin_L','foot_L'),'R':('thigh_R','shin_R','foot_R')}
ARMS={'L':('upperArm_L','foreArm_L','hand_L'),'R':('upperArm_R','foreArm_R','hand_R')}
report={}
def sstep(x): x=max(0,min(1,x)); return x*x*(3-2*x)
# =============== WALK ===============
if 'walk' in steps:
    SLOW=float(os.environ.get('SLOW','0.444')); STRIDE=float(os.environ.get('STRIDE','1.2')); DIP=float(os.environ.get('DIP','2.2'))
    SWAY=float(os.environ.get('SWAY','2.0')); LEAN=float(os.environ.get('LEAN','6')); CROUCH=float(os.environ.get('CROUCH','0.025')); ABD=float(os.environ.get('ABD','10'))
    old=set(bpy.data.objects); olda=set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath='/workspace/mocap/ual1.glb')
    S=[o for o in set(bpy.data.objects)-old if o.type=='ARMATURE'][0]
    for o in set(bpy.data.objects)-old:
        if o.type!='ARMATURE': bpy.data.objects.remove(o)
    src_acts={re.sub(r'_Armature(\.\d+)?$','',x.name):x for x in set(bpy.data.actions)-olda}
    M={'hips':'pelvis','spine':'spine_01','spine2':'spine_02','chest':'spine_03','neck':'neck_01','head':'Head'}
    for s,t in (('L','l'),('R','r')):
        M.update({'shoulder_'+s:'clavicle_'+t,'upperArm_'+s:'upperarm_'+t,'foreArm_'+s:'lowerarm_'+t,'hand_'+s:'hand_'+t,
                  'thigh_'+s:'thigh_'+t,'shin_'+s:'calf_'+t,'foot_'+s:'foot_'+t,'toe_'+s:'ball_'+t})
    M={k:v for k,v in M.items() if k in TB}
    def child_dir(arm,n,ch):
        h=wrest(arm,n).translation
        for c in ch:
            if c in arm.data.bones: return ((arm.matrix_world@arm.data.bones[c].head_local)-h).normalized()
        return (wrest(arm,n).to_3x3()@Vector((0,1,0))).normalized()
    def mchild_t(n):
        for c in TB[n].children_recursive:
            if c.name in M and c.parent and (c.parent.name==n or c.parent.name not in M): return [c.name]
        return []
    C={}
    for t,s in M.items():
        ct=mchild_t(t)
        if ct: cs=[M[ct[0]]]
        else:
            cs={'hand_l':['middle_01_l'],'hand_r':['middle_01_r'],'ball_l':['ball_leaf_l'],'ball_r':['ball_leaf_r']}.get(s,[])
            ct=['fingers_'+t[-1]] if t.startswith('hand') else []
        C[t]=child_dir(T,t,ct).rotation_difference(child_dir(S,s,cs)).to_matrix()
        if t=='hips' or s=='Head': C[t]=Matrix.Identity(3)
    k_h=REST['hips'].translation.z/wrest(S,'pelvis').translation.z
    def src_pose():
        D={t:(S.matrix_world@S.pose.bones[s].matrix).to_3x3()@wrest(S,s).to_3x3().inverted() for t,s in M.items()}
        pp=(S.matrix_world@S.pose.bones['pelvis'].matrix).translation-wrest(S,'pelvis').translation
        return D,pp
    def amp(Dp,Dc,k):
        q=(Dp.inverted()@Dc).to_quaternion(); ax,an=q.to_axis_angle()
        return Dp@Quaternion(ax,an*k).to_matrix()
    def build(D,pp):
        W={}
        for n in order:
            b=TB[n]; Rb=REST[n]
            base=W[b.parent.name]@RESTI[b.parent.name]@Rb if b.parent else Rb.copy()
            if n in D:
                pos=base.translation if n!='hips' else Rb.translation+pp*k_h
                base=Matrix.Translation(pos)@(D[n]@C[n]@Rb.to_3x3()).to_4x4()
                if n.startswith('upperArm') and ABD:
                    sg=-1 if pos.x>0 else 1
                    base=Matrix.Translation(pos)@Matrix.Rotation(math.radians(sg*ABD),4,'Y')@Matrix.Translation(-pos)@base
            W[n]=base
        return W
    act=src_acts['Walk_Loop']; S.animation_data.action=act; f0,f1=[int(round(x)) for x in act.frame_range]; n_src=f1-f0
    N=int(round(n_src/SLOW)); raw=[]
    for i in range(N+1):
        fs=f0+i*n_src/N; sc.frame_set(int(math.floor(fs)),subframe=fs-math.floor(fs)); raw.append(src_pose())
    pz=np.array([p.z for _,p in raw]); px=np.array([p.x for _,p in raw]); mz,mx=pz[:N].mean(),px[:N].mean()
    frames=[]
    for (D,pp),zz,xx in zip(raw,pz,px):
        pp=pp.copy(); pp.z=mz+(zz-mz)*DIP-CROUCH; pp.x=mx+(xx-mx)*SWAY
        lean=Matrix.Rotation(math.radians(LEAN),3,'X')
        for s in 'LR':
            D['thigh_'+s]=amp(D['hips'],D['thigh_'+s],STRIDE)
        for k in ('spine',):
            D[k]=lean@D[k]
        for k in ('spine2','chest','neck','head','shoulder_L','shoulder_R','upperArm_L','upperArm_R','foreArm_L','foreArm_R','hand_L','hand_R'):
            if k in D: D[k]=lean@D[k]
        D['neck']=Matrix.Rotation(math.radians(-LEAN*0.8),3,'X')@D['neck']; D['head']=Matrix.Rotation(math.radians(-LEAN*0.8),3,'X')@D['head']
        frames.append((D,pp))
    Ws=[build(D,pp) for D,pp in frames]; n=N
    H=21.14
    ank={s:np.array([list(W[LEGS[s][2]].translation) for W in Ws]) for s in LEGS}
    ADD=np.array([((zz-mz)*(DIP-1)-CROUCH)*k_h for zz in pz])
    ank={s:ank[s]-np.outer(ADD,[0,0,1]) for s in LEGS}
    ball={s:np.array([list(W['toe_'+s].translation) for W in Ws])-np.outer(ADD,[0,0,1]) for s in LEGS}
    cont={s:ball[s][:,2]<ball[s][:,2].min()+0.015*H for s in LEGS}
    vs=[(ball[s][(i+1)%n,1]-ball[s][i,1])*30 for s in LEGS for i in range(n) if cont[s][i] and cont[s][(i+1)%n]]
    v=float(np.median(vs))
    targets={}
    for s in LEGS:
        A=ank[s]; Bl=ball[s]; c=cont[s]; segs=[]
        for i in range(n):
            if c[i] and not c[(i-1)%n]:
                j=i
                while c[(j+1)%n] and j-i<n: j+=1
                if j-i>=4: segs.append((i,j))
        tg=[None]*(n+1); wv=[0.0]*(n+1)
        for i in range(n+1):
            best=None
            for (s0,s1) in segs:
                for off in (-n,0,n):
                    a0,a1=s0+off,s1+off
                    if a0-9<=i<=a1+12:
                        w=1.0 if a0<=i<=a1 else (1-(a0-i)/10 if i<a0 else 1-(i-a1)/13)
                        if best is None or w>best[0]: best=(w,a0,a1)
            if not best or best[0]<=0: continue
            w,a0,a1=best
            x=Bl[[k%n for k in range(a0,a1+1)],0].mean(); by=Bl[a0%n,1]+v*(i-a0)/30.0
            zs=Bl[[k%n for k in range(a0,a1+1)],2]; zmin=float(zs.min()); bz=float(Bl[i%n,2])
            rp=1-sstep(min(i-a0,a1-i)/6.0) if a0<=i<=a1 else 1.0
            bz=min(bz,zmin+(bz-zmin)*rp)
            at=Vector((x,by,bz))+Vector(A[i%n]-Bl[i%n])
            tg[i]=(Vector(A[i%n])+Vector((0,0,ADD[i]))).lerp(at,sstep(w)); wv[i]=sstep(w)
        targets[s]=(tg,segs,wv)
    # pass 1 IK, then sole grounding per side, pass 2
    def solve(off):
        out=[]
        for i,W0 in enumerate(Ws):
            W={k:m.copy() for k,m in W0.items()}
            for s in LEGS:
                t=targets[s][0][i]
                if t is None: t=W[LEGS[s][2]].translation.copy()
                ww=targets[s][2][i]
                if not two_bone(W,*LEGS[s],t+Vector((0,0,off[s]*ww))): UNR[0]+=1
                m=rmin(W,'foot_'+s)
                if m<GOAL-1e-4: two_bone(W,*LEGS[s],W[LEGS[s][2]].translation+Vector((0,0,GOAL-m)))
            out.append(W)
        return out
    off={'L':0.0,'R':0.0}; UNR=[0]
    for it in range(3):
        Wk=solve(off)
        for s in LEGS:
            st=[i for i in range(n) if cont[s][i]]
            m=min(rmin(Wk[i],'foot_'+s) for i in st); off[s]+=GOAL-m
    UNR[0]=0; Wk=solve(off)
    actT,oldw=new_action('wb_walk')
    root_m=[]
    for i,W in enumerate(Wk):
        sh=Matrix.Translation((0,-v*i/30.0,0))
        W={k:sh@m for k,m in W.items()}
        apply(W,i)
    # foot slide + heights
    slide={}; sole={}
    for s in LEGS:
        sp=[]; hs=[]
        for i in range(n):
            if cont[s][i] and cont[s][(i+1)%n]:
                p0=Wk[i]['toe_'+s].translation+Vector((0,-v*i/30,0)); p1=Wk[i+1]['toe_'+s].translation+Vector((0,-v*(i+1)/30,0))
                sp.append((p1-p0).xy.length*M2G); hs.append(rmin(Wk[i],'foot_'+s)*M2G)
        slide[s]=round(max(sp),4); sole[s]=[round(min(hs),3),round(max(hs),3)]
    steps_t={s:[round(a0/30,3) for a0,_ in targets[s][1]] for s in LEGS}
    report['wb_walk']={'source':'Quaternius UAL1 Walk_Loop (CC0)','playback':round(n_src/N,3),'frames':N,'cycle_s':round(N/30,3),
        'root_speed_units':round(abs(v),4),'root_speed_mps_114m':round(abs(v)*M2G,3),'stride_m':round(abs(v)*N/30/2*M2G,2),
        'max_slide_per_frame_m':slide,'stance_sole_height_m':sole,'footsteps':steps_t,'unreachable_leg_frames':UNR[0],'off':off,
        'params':dict(SLOW=SLOW,STRIDE=STRIDE,DIP=DIP,SWAY=SWAY,LEAN=LEAN,CROUCH=CROUCH,ABD=ABD)}
    print('WALK',report['wb_walk'],flush=True)
    if oldw: bpy.data.actions.remove(oldw)
    bpy.data.objects.remove(S)
    for x in list(bpy.data.actions):
        if x in src_acts.values(): bpy.data.actions.remove(x)
# =============== SLAMS ===============
SLAMS={ # clip: (impact frame guess, effectors)
 'wb_stomp':(72,['foot_R']),
 'wb_swat_knee':(72,['foot_R']),
 'wb_ritual_fissure_release':(27,['fist_L','fist_R']),
 'wb_ritual_lavawave_release':(39,['fist_L','fist_R']),
 'wb_swat_forearm_L':(48,['forearm_L']),
 'wb_swat_forearm_R':(48,['forearm_R']),
}
BAX=[Vector((1,0,0))]
ONLY=[x for x in os.environ.get('ONLY','').split(',') if x]
if 'slams' in steps:
  for clip,(fc,effs) in SLAMS.items():
    if ONLY and clip not in ONLY: continue
    act0=bpy.data.actions[clip]; T.animation_data_create(); T.animation_data.action=act0
    f0,f1=[int(round(x)) for x in act0.frame_range]; NF=f1-f0+1
    W0=[]
    for f in range(f0,f1+1): sc.frame_set(f); W0.append(getW())
    PRE=int(os.environ.get('PRE','8')); HOLD=3; REC=int(os.environ.get('REC','24')); ANT=int(os.environ.get('ANT','26'))
    fc=max(fc,PRE+6); ANT=min(ANT,fc-PRE)
    def wts(f):
        k=f-fc
        wc=((k+PRE)/PRE)**2 if -PRE<=k<0 else (1.0 if 0<=k<=HOLD else (1-sstep((k-HOLD)/REC) if HOLD<k<=HOLD+REC else 0.0))
        wd=((k+PRE+2)/(PRE+2))**2 if -(PRE+2)<=k<0 else (1.0 if 0<=k<=HOLD+1 else (1-sstep((k-HOLD-1)/(REC+6)) if HOLD+1<k<=HOLD+1+REC+6 else 0.0))
        wa=math.sin(math.pi*(k+PRE+ANT)/ANT)**2 if -(PRE+ANT)<=k<-PRE else 0.0
        return wc,wd,wa
    def body_adj(W,th,d,lean_back,feet,eff_leg=None,eff_tgt=None):
        W={k:m.copy() for k,m in W.items()}
        hp=W['hips'].translation.copy()
        xform_sub(W,'hips',Matrix.Translation((0,0,-d)))
        hp2=W['hips'].translation.copy()
        R=Matrix.Rotation(math.radians(th-lean_back),4,BAX[0])
        xform_sub(W,'spine',Matrix.Translation(hp2)@R@Matrix.Translation(-hp2))
        for s in 'LR':
            t=eff_tgt if s==eff_leg else feet[s]
            two_bone(W,*LEGS[s],t,keep_rot=None)
        return W
    def plan():
        fW=W0[fc-f0]; feet={s:fW[LEGS[s][2]].translation.copy() for s in 'LR'}
        kind=effs[0].split('_')[0]
        # contact targets (joint end-effector positions) at impact
        tg={}
        for e in effs:
            s=e[-1]
            if kind=='foot':
                ft=fW[LEGS[s][2]].translation.copy(); tg[e]=ft
            else:
                hb=ARMS[s][2]; hpos=fW[hb].translation.copy()
                sg=1 if s=='L' else -1
                sh=fW[ARMS[s][0]].translation; hip=fW['hips'].translation
                v=Vector((hpos.x-hip.x,hpos.y-hip.y,0))
                if kind=='fist' and len(effs)>1: v=Vector((sg*float(os.environ.get('FX','4.6')),-float(os.environ.get('FY','8.5')),0))
                elif v.length<1e-3: v=Vector((sg*3,-5,0))
                if v.y>-1.5 and kind=='fist' and 'back' not in clip: v.y=-4.0
                L=v.length; v=v.normalized()*min(max(L,5.0),9.5) if len(effs)==1 else v
                if kind=='forearm': v.x=sg*max(abs(v.x),float(os.environ.get('AX','7.0'))); v.y=min(v.y,-float(os.environ.get('AY','6.0')))
                tg[e]=Vector((hip.x+v.x,hip.y+v.y,0.0))
                if os.environ.get('STRAIGHT','1')=='1':
                    Lr=(REST[ARMS[s][1]].translation-REST[ARMS[s][0]].translation).length+(REST[ARMS[s][2]].translation-REST[ARMS[s][1]].translation).length
                    zf=sh.z-1.3; K=float(os.environ.get('SK','0.93'))*Lr
                    hd=math.sqrt(max(K*K-zf*zf,1.0))
                    dv=Vector((sg*float(os.environ.get('SX'+s,os.environ.get('SXO','0.45' if kind=='fist' else '1.2'))),-1,0)).normalized()
                    tg[e]=Vector((sh.x,sh.y,0))+dv*hd
        feetA={s:W0[0][LEGS[s][2]].translation.copy() for s in 'LR'}
        def solve_at(W,wc,wd,wa,th,d,ztg,rot0):
            lb=10.0*wa if kind!='foot' else 0.0
            legeff=effs[0][-1] if kind=='foot' else None
            eff_t=None
            if legeff:
                cur=W[LEGS[legeff][2]].translation.copy()
                lift=Vector((0,0,2.2*wa))
                eff_t=(cur+lift).lerp(tg[effs[0]]+Vector((0,0,ztg[effs[0]])),wc)
            Wn=body_adj(W,th*wd,d*wd,lb,{s:W[LEGS[s][2]].translation.copy() for s in 'LR'},legeff,eff_t)
            ok=True
            if kind!='foot':
                for e in effs:
                    s=e[-1]; ch=ARMS[s]; cur=Wn[ch[2]].translation.copy()
                    t=(cur+Vector((0,0,3.0*wa))).lerp(tg[e]+Vector((0,0,ztg[e])),wc)
                    ok&=two_bone(Wn,*ch,t,keep_rot=rot0[s] if wc>0 else None,pole_hint=Vector((1 if s=='L' else -1,float(os.environ.get('PY','0.2')),float(os.environ.get('PZ','0.5')))))
            return Wn,ok
        rot0={}
        for s_ in 'LR':
            r=fW[ARMS[s_][2]].to_3x3(); ydir=(r@Vector((0,1,0))).normalized()
            rot0[s_]=ydir.rotation_difference(Vector((0,-0.35,-1)).normalized()).to_matrix()@r if kind=='fist' else r
        # z offset of effector joint so the region's lowest point hits GOAL
        ztg={e:(fW[ARMS[e[-1]][2]].translation.z-rmin(fW,RG(e)) if kind!='foot' else fW[LEGS[e[-1]][2]].translation.z-rmin(fW,RG(e))) for e in effs}
        best=None
        if kind!='foot':
            hip=fW['hips'].translation; dv=sum((tg[e]-hip for e in effs),Vector()); dv.z=0
            BAX[0]=Vector((0,0,1)).cross(dv.normalized()) if dv.length>1e-3 else Vector((1,0,0))
        else: BAX[0]=Vector((1,0,0))
        for outer in range(4):
            best=None
            FB=[None]
            if kind=='foot': best=(0.0,1.2)
            else:
                for d in np.arange(float(os.environ.get('D0','0.6')),5.01,0.2):
                    for th in range(int(os.environ.get('TH0','0')),82,2):
                        Wn,ok=solve_at(fW,1,1,0,th,d,ztg,rot0)
                        exc=max((tg[e]+Vector((0,0,ztg[e]))-Wn[ARMS[e[-1]][0]].translation).length/((REST[ARMS[e[-1]][1]].translation-REST[ARMS[e[-1]][0]].translation).length+(REST[ARMS[e[-1]][2]].translation-REST[ARMS[e[-1]][1]].translation).length) for e in effs)
                        if FB[0] is None or exc<FB[0][0]: FB[0]=(exc,th,d)
                        reach=all((tg[e]+Vector((0,0,ztg[e]))-Wn[ARMS[e[-1]][0]].translation).length<=0.96*((REST[ARMS[e[-1]][1]].translation-REST[ARMS[e[-1]][0]].translation).length+(REST[ARMS[e[-1]][2]].translation-REST[ARMS[e[-1]][1]].translation).length) for e in effs)
                        if reach:
                            c=th/50+d/float(os.environ.get('DW','3'))
                            if best is None or c<best[0]: best=(c,th,d)
                            break
                print('REACH',clip,best,FB[0],{e:tuple(round(x,2) for x in tg[e]) for e in effs},ztg,flush=True)
                best=(best[1],best[2]) if best else (FB[0][1],FB[0][2])
            th,d=best
            for it in range(6):
                Wn,ok=solve_at(fW,1,1,0,th,d,ztg,rot0)
                err={e:rmin(Wn,RG(e))-GOAL for e in effs}
                if max(abs(x) for x in err.values())<0.0008: break
                for e in effs: ztg[e]-=err[e]
            if max(abs(x) for x in err.values())<0.0008: break
        return solve_at,th,d,ztg,rot0,kind,tg
    kind0=effs[0].split('_')[0]
    CANDS=[{}] if kind0=='foot' else [dict(SXO=a_,SK=k_,D0=d_,DW='0.5') for d_ in ('0','-0.6') for k_ in ('0.98','1.0','1.03','1.06') for a_ in (('0.7','0.9','1.2','1.6') if kind0=='fist' else ('1.2','2.0','3.0','4.5'))]
    if clip=='wb_ritual_fissure_release': CANDS=[dict(STRAIGHT='1',SXO='0.7',SXR='2.2',SK='1.0',D0='0',DW='0.5')]+[dict(STRAIGHT='1',SXO=l_,SXR=r_,SK=k_,D0='0',DW='0.5') for k_ in ('1.0','0.97') for r_ in ('2.2','3.0','4.5','7') for l_ in ('0.7','2.2')]+[dict(STRAIGHT='0',FX=x_,FY=y_,D0='0',DW='0.5') for x_ in ('6','7') for y_ in ('6','8','10')]
    elif kind0=='fist': CANDS=[dict(STRAIGHT='0',FX='4.6',FY='8.5',D0='0.6',DW='3'),dict(STRAIGHT='0',FX='6',FY='9',D0='0.6',DW='3')]+[dict(c_,STRAIGHT='1') for c_ in CANDS]
    elif kind0=='forearm': CANDS=[dict(STRAIGHT='0',AX=ax,AY=ay,D0=d_,DW='0.5') for d_ in ('0','-1') for ax in ('9','11','13') for ay in ('1','3','5','0','-1.5')]
    chosen=None; BEST=[None]
    for cd in CANDS:
        for k_,v_ in cd.items(): os.environ[k_]=v_
        solve_at,th,d,ztg,rot0,kind,tg=plan()
        if kind=='foot': chosen=cd; break
        bad=0
        for f in (range(fc,fc+HOLD+1) if os.environ.get('HOLDONLY') else range(fc-PRE,fc+HOLD+REC+2,2)):
            if f>f1: continue
            wc,wd,wa=wts(f); Wb=W0[fc-f0] if fc<=f<=fc+HOLD else W0[f-f0]
            Wt,_=solve_at(Wb,wc,wd,wa,th,d,ztg,rot0); bad+=n_inside(Wt)
        print('CAND',clip,cd,'inside',bad,'th',th,'d',round(d,2),flush=True)
        if BEST[0] is None or bad<BEST[0][0]: BEST[0]=(bad,cd)
        if bad==0: chosen=cd; break
    if chosen is None:
        print('NOCAND',clip,BEST[0],flush=True)
        for k_,v_ in BEST[0][1].items(): os.environ[k_]=v_
        solve_at,th,d,ztg,rot0,kind,tg=plan()
    report.setdefault('_cands',{})[clip]={'chosen':chosen if chosen is not None else BEST[0][1],'inside_samples':0 if chosen is not None else BEST[0][0]}
    actN,old=new_action(clip)
    hs={e:[] for e in effs}
    for f in range(f0,f1+1):
        wc,wd,wa=wts(f)
        W=W0[fc-f0] if fc<=f<=fc+HOLD else W0[f-f0]
        if wc>0 or wd>0 or wa>0: W,_=solve_at(W,wc,wd,wa,th,d,ztg,rot0)
        apply(W,f)
        for e in effs: hs[e].append(round(rmin(W,RG(e))*M2G,3))
    # keep fcurve extras (e.g. custom props) not needed; copy markers
    if old: bpy.data.actions.remove(old)
    imp=[f for f in range(fc,fc+HOLD+1)]
    report[clip]={'impact_frame':fc,'impact_s':round(fc/30,3),'hold_frames':imp,'effectors':effs,'spine_bend_deg':th,'body_drop_m':round(d*M2G,2),
                  'contact_min_height_m':{e:[hs[e][f-f0] for f in imp] for e in effs},'frames':NF}
    print('SLAM',clip,report[clip],flush=True)
json.dump(report,open(out+'.report.json','w'),indent=1)
T.animation_data.action=bpy.data.actions.get('wb_idle')
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
bpy.ops.export_scene.gltf(filepath=out+'.glb',export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
print('DONE')
