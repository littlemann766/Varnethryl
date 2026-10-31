import bpy,sys,math,json
import numpy as np
from mathutils import Matrix,Vector,Quaternion
a=sys.argv[sys.argv.index('--')+1:]; blend,out,name=a[0],a[1],a[2]
bpy.ops.wm.open_mainfile(filepath=blend)
sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
T=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
old=set(bpy.data.objects); olda=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath='/workspace/mocap/ual1.glb')
S=[o for o in set(bpy.data.objects)-old if o.type=='ARMATURE'][0]
for o in set(bpy.data.objects)-old:
    if o.type!='ARMATURE': bpy.data.objects.remove(o)
import re
src_acts={re.sub(r'_Armature(\.\d+)?$','',x.name):x for x in set(bpy.data.actions)-olda}
ual1names=set(src_acts)
old2=set(bpy.data.objects); olda2=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath='/workspace/mocap/ual2/Universal Animation Library 2[Standard]/Unreal-Godot/UAL2_Standard.glb')
for o in set(bpy.data.objects)-old2: bpy.data.objects.remove(o)
for x in set(bpy.data.actions)-olda2:
    k=re.sub(r'_Armature(\.\d+)?$','',x.name)
    if k not in src_acts: src_acts[k]=x
sc.render.fps=30; sc.render.fps_base=1
TB=T.data.bones
def side(m,L,R): return {k.replace('_L',L).replace('_R',R) if False else k:v for k,v in m.items()}
if 'mixamorig:Hips' in TB:
    P='mixamorig:'; M={P+'Hips':'pelvis',P+'Spine':'spine_01',P+'Spine1':'spine_02',P+'Spine2':'spine_03',P+'Neck':'neck_01',P+'Head':'Head'}
    for s,t in (('Left','l'),('Right','r')):
        M.update({P+s+'Shoulder':'clavicle_'+t,P+s+'Arm':'upperarm_'+t,P+s+'ForeArm':'lowerarm_'+t,P+s+'Hand':'hand_'+t,
                  P+s+'UpLeg':'thigh_'+t,P+s+'Leg':'calf_'+t,P+s+'Foot':'foot_'+t,P+s+'ToeBase':'ball_'+t})
    LEG={'L':(P+'LeftUpLeg',P+'LeftLeg',P+'LeftFoot'),'R':(P+'RightUpLeg',P+'RightLeg',P+'RightFoot')}; HIPS=P+'Hips'
else:
    M={'hips':'pelvis','spine':'spine_01','neck':'neck_01','head':'Head'}
    if 'spine2' in TB: M.update({'spine2':'spine_02','chest':'spine_03'})
    else: M.update({'chest':'spine_03'})
    for s,t in (('L','l'),('R','r')):
        M.update({'shoulder_'+s:'clavicle_'+t,'upperArm_'+s:'upperarm_'+t,'foreArm_'+s:'lowerarm_'+t,'hand_'+s:'hand_'+t,
                  'thigh_'+s:'thigh_'+t,'shin_'+s:'calf_'+t,'foot_'+s:'foot_'+t,'toe_'+s:'ball_'+t})
    LEG={'L':('thigh_L','shin_L','foot_L'),'R':('thigh_R','shin_R','foot_R')}; HIPS='hips'
M={k:v for k,v in M.items() if k in TB}
inv={v:k for k,v in M.items()}
SB=S.data.bones
def wrest(arm,n): return arm.matrix_world@arm.data.bones[n].matrix_local
def child_dir(arm,n,mapping_children):
    b=arm.data.bones[n]; h=wrest(arm,n).translation
    for c in mapping_children:
        if c in arm.data.bones: return ((arm.matrix_world@arm.data.bones[c].head_local)-h).normalized()
    return (wrest(arm,n).to_3x3()@Vector((0,1,0))).normalized()
# mapped-child for each mapped target bone: the first mapped descendant (direct child preferably)
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
        ct={'hand':['fingers_L' if t.endswith('L') else 'fingers_R']}.get('hand' if 'hand' in t.lower() else '',[])
        if 'mixamorig' in t and 'Hand' in t: ct=[t+'Middle1']
    dt=child_dir(T,t,ct); ds=child_dir(S,s,cs)
    C[t]=dt.rotation_difference(ds).to_matrix()
    if t in (HIPS,) or s in ('Head','neck_01'): C[t]=Matrix.Identity(3)
order=[]
def walk(b):
    order.append(b.name); [walk(c) for c in b.children]
[walk(b) for b in TB if not b.parent]
Tinv=T.matrix_world.inverted()
k_h=(wrest(T,HIPS).translation.z)/(wrest(S,'pelvis').translation.z)
H=max((T.matrix_world@b.head_local).z for b in TB)
def src_pose():
    out={}
    for t,s in M.items():
        Wp=S.matrix_world@S.pose.bones[s].matrix; Wr=wrest(S,s)
        out[t]=(Wp.to_3x3()@Wr.to_3x3().inverted())
    pp=(S.matrix_world@S.pose.bones['pelvis'].matrix).translation-wrest(S,'pelvis').translation
    return out,pp
import os
CAPE_K=float(os.environ.get('CAPE_K','0')); CAPE_MODE=os.environ.get('CAPE_MODE','rigid'); ABD=float(os.environ.get('ABD','0'))
UPARMS=[k for k in M if M[k] in ('upperarm_l','upperarm_r')]
HOLD=[x for x in os.environ.get('HOLD','').split(',') if x]
ABD_IDLE=float(os.environ.get('ABD_IDLE',ABD)); CUR_ABD=[ABD]
def build(D,pp,ik=None):
    W={}
    for n in order:
        b=TB[n]; Rb=wrest(T,n)
        if b.parent:
            base=W[b.parent.name]@wrest(T,b.parent.name).inverted()@Rb
        else: base=Rb.copy()
        if n in D:
            pos=base.translation if n!=HIPS else Rb.translation+pp*k_h
            R3=D[n]@C[n]@C[n].inverted()@Rb.to_3x3() if False else D[n]@Rb.to_3x3()
            # direction-corrected: rotate rest by C first so dirs match source rest, then apply source delta
            R3=D[n]@C[n]@Rb.to_3x3()
            if n in HOLD and b.parent:
                pr=W[b.parent.name].to_3x3()@wrest(T,b.parent.name).to_3x3().inverted()
                if os.environ.get('HOLD_MODE')=='world': pr=D[HIPS]
                R3=pr@Rb.to_3x3()
            base=Matrix.Translation(pos)@R3.to_4x4()
            if n in UPARMS and CUR_ABD[0]:
                sgn=-1 if pos.x>0 else 1
                base=Matrix.Translation(pos)@Matrix.Rotation(math.radians(sgn*CUR_ABD[0]),4,'Y')@Matrix.Translation(-pos)@base
        if n.startswith('cape') and b.parent and b.parent.name.startswith('cape'):
            h=base.translation; cur=(base.to_3x3()@Vector((0,1,0))).normalized()
            restd=(Rb.to_3x3()@Vector((0,1,0))).normalized()
            want=(Vector((0,0.45,-1)).normalized()*0.5+restd*0.5).normalized() if CAPE_MODE=='hang' else restd
            if cur.dot(want)<0.999:
                q=cur.rotation_difference(cur.lerp(want,CAPE_K).normalized()).to_matrix()
                base=Matrix.Translation(h)@(q@base.to_3x3()).to_4x4()
        W[n]=base
    return W
def leg_ik(W,side_,target):
    th,sh,ft=LEG[side_]
    Hh=W[th].translation; K=W[sh].translation; A=W[ft].translation
    l1=(K-Hh).length; l2=(A-K).length
    d=target-Hh; L=min(d.length,(l1+l2)*SOFT); L=max(L,abs(l1-l2)+1e-4); dn=d.normalized()
    pole=(K-Hh)-dn*((K-Hh).dot(dn));
    if pole.length<1e-6: pole=Vector((0,-1,0))
    pole.normalize()
    ca=(l1*l1+L*L-l2*l2)/(2*l1*L); ang=math.acos(max(-1,min(1,ca)))
    Kn=Hh+(dn*math.cos(ang)+pole*math.sin(ang))*l1
    An=Hh+dn*L
    footrot=W[ft].to_3x3()
    r1=(K-Hh).normalized().rotation_difference((Kn-Hh).normalized()).to_matrix()
    newth=Matrix.Translation(Hh)@(r1@W[th].to_3x3()).to_4x4()
    r2=(A-K).normalized().rotation_difference((An-Kn).normalized()).to_matrix()
    newsh=Matrix.Translation(Kn)@(r2@W[sh].to_3x3()).to_4x4()
    # recompute subtree: shift children rigidly
    delta_th=newth@W[th].inverted()
    for c in [x.name for x in TB[th].children_recursive]: W[c]=delta_th@W[c]
    W[th]=newth
    delta_sh=newsh@W[sh].inverted()
    for c in [x.name for x in TB[sh].children_recursive]: W[c]=delta_sh@W[c]
    W[sh]=newsh
    # keep foot world orientation from mocap
    fpos=W[ft].translation.copy(); dF=(Matrix.Translation(fpos)@footrot.to_4x4())@W[ft].inverted()
    for c in [x.name for x in TB[ft].children_recursive]: W[c]=dF@W[c]
    W[ft]=Matrix.Translation(fpos)@footrot.to_4x4()
def apply(W,f):
    for n in order:
        b=TB[n]; pb=T.pose.bones[n]; Ma=Tinv@W[n]
        if b.parent:
            Rp=b.parent.matrix_local; Pp=Tinv@W[b.parent.name]
            pb.matrix_basis=(Rp.inverted()@b.matrix_local).inverted()@Pp.inverted()@Ma
        else: pb.matrix_basis=b.matrix_local.inverted()@Ma
        pb.rotation_mode='QUATERNION'
        pb.keyframe_insert('rotation_quaternion',frame=f); pb.keyframe_insert('location',frame=f)
CLIPS=json.loads(os.environ['CLIPS']); SOFT=float(os.environ.get('SOFT','0.985')); WARP=float(os.environ.get('WARP','30'))
info={}
for tname,sname,moving in CLIPS:
    sname_=sname
    CUR_ABD[0]=ABD_IDLE if tname=='idle' else ABD
    frames=[]; tmap=[]
    for pi_,part in enumerate(sname.split('+')):
        act=src_acts[part]; S.animation_data.action=act; f0,f1=[int(round(x)) for x in act.frame_range]
        SBN=list(M.values()); ts=[]
        prevq=None
        for f in range(f0,f1+1):
            sc.frame_set(f); q={b:S.pose.bones[b].matrix_basis.to_quaternion() for b in SBN}
            if prevq is not None:
                st=max(min(math.degrees(prevq[b].rotation_difference(q[b]).angle),360-math.degrees(prevq[b].rotation_difference(q[b]).angle)) for b in SBN)
                k=1 if moving else max(1,math.ceil(st/WARP))
                ts+= [f-1+j/k for j in range(1,k+1)]
            else: ts.append(float(f))
            prevq=q
        if pi_>0: ts=ts[1:]
        for t in ts:
            fi=int(math.floor(t)); sc.frame_set(fi,subframe=t-fi); D,pp=src_pose(); frames.append((D,pp)); tmap.append((part,round(t-f0,3)))
    n=len(frames)-1
    Ws=[build(D,pp) for D,pp in frames]
    ank={s_:np.array([list(W[LEG[s_][2]].translation) for W in Ws]) for s_ in LEG}
    gz={s_:ank[s_][:,2].min() for s_ in LEG}
    TOE={s_:[b for b in TB[LEG[s_][2]].children if b.name in M][0].name if [b for b in TB[LEG[s_][2]].children if b.name in M] else LEG[s_][2] for s_ in LEG}
    ball={s_:np.array([list(W[TOE[s_]].translation) for W in Ws]) for s_ in LEG}
    rest_ank={s_:wrest(T,LEG[s_][2]).translation.z for s_ in LEG}
    v=0.0; targets={}
    if moving:
        cont={s_:ball[s_][:,2]<ball[s_][:,2].min()+0.015*H for s_ in LEG}
        vs=[(ball[s_][(i+1)%n,1]-ball[s_][i,1])*30 for s_ in LEG for i in range(n) if cont[s_][i] and cont[s_][(i+1)%n]]
        v=float(np.median(vs))
        for s_ in LEG:
            A=ank[s_]; Bl=ball[s_]; c=cont[s_]
            segs=[]
            for i in range(n):
                if c[i] and not c[(i-1)%n]:
                    j=i
                    while c[(j+1)%n] and j-i<n: j+=1
                    segs.append((i,j))
            tg=[None]*(n+1)
            for i in range(n+1):
                best=None
                for (s0,s1) in segs:
                    for off in (-n,0,n):
                        a0,a1=s0+off,s1+off
                        if a0-4<=i<=a1+5:
                            w=1.0 if a0<=i<=a1 else (1-(a0-i)/5 if i<a0 else 1-(i-a1)/6)
                            if best is None or w>best[0]: best=(w,a0,a1,off)
                if not best or best[0]<=0: continue
                w,a0,a1,off=best
                x=Bl[[k%n for k in range(a0,a1+1)],0].mean()
                by=Bl[a0%n,1]+v*(i-a0)/30.0
                bt=Vector((x,by,Bl[i%n,2]))
                at=bt+Vector(A[i%n]-Bl[i%n])
                src=Vector(A[i%n])
                tg[i]=src.lerp(at,max(0,min(1,w)))
            targets[s_]=tg
    else:
        for s_ in LEG:
            A=ank[s_]; m=A[:n].mean(0); span=np.ptp(A[:,:2],axis=0).max()
            if tname.startswith('death') or span>0.10*H:
                targets[s_]=[None]*(n+1); continue
            targets[s_]=[Vector((m[0],m[1],rest_ank[s_]+max(0,A[i%n,2]-A[:,2].min()))) for i in range(n+1)]
    actT=bpy.data.actions.get(tname)
    if actT: bpy.data.actions.remove(actT)
    actT=bpy.data.actions.new(tname); actT.use_fake_user=True
    T.animation_data_create(); T.animation_data.action=actT
    slide=[]
    for i,W in enumerate(Ws):
        for s_ in LEG:
            t=targets[s_][i]
            if t is None: continue
            # soft blend at stance edges
            leg_ik(W,s_,t)
        apply(W,i)
    # loop: last frame == first
    info[tname]={'timewarp':tmap,'source':'Quaternius '+('UAL1 ' if sname in ual1names else 'UAL2 ')+sname,'frames':n,'speed_mps':abs(v),'cycle_s':n/30}
    print('CLIP',tname,n,'speed',round(abs(v),3))
T.animation_data.action=bpy.data.actions['idle']
bpy.data.objects.remove(S)
for x in list(bpy.data.actions):
    if x.name not in [c[0] for c in CLIPS]: bpy.data.actions.remove(x)
for x in list(bpy.data.actions):
    if x in src_acts.values(): bpy.data.actions.remove(x)
info['_params']={'CAPE_K':CAPE_K,'CAPE_MODE':CAPE_MODE,'ABD':ABD,'ABD_IDLE':ABD_IDLE,'HOLD':HOLD,'HOLD_MODE':os.environ.get('HOLD_MODE','parent')}
json.dump(info,open(out+'.speeds.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
