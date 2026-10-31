import bpy,sys,math,json
import numpy as np
from mathutils import Matrix,Vector,Quaternion
a=sys.argv[sys.argv.index('--')+1:]; blend,out,name=a[0],a[1],a[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30; bpy.context.scene.render.fps_base=1  # load at 30 fps (24 fps load sped clips up)
bpy.ops.import_scene.gltf(filepath=blend)
sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
T=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
old=set(bpy.data.objects); olda=set(bpy.data.actions)
import re
src_acts={}
for lib,p in (('U1','/workspace/mocap/ual1.glb'),('U2','/workspace/mocap/ual2/Universal Animation Library 2[Standard]/Unreal-Godot/UAL2_Standard.glb')):
    o0=set(bpy.data.objects); a0=set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=p)
    Sx=[o for o in set(bpy.data.objects)-o0 if o.type=='ARMATURE'][0]
    for o in set(bpy.data.objects)-o0:
        if o.type!='ARMATURE': bpy.data.objects.remove(o)
    for x in set(bpy.data.actions)-a0: src_acts[lib+':'+re.sub(r'_Armature(\.\d+)?$','',x.name)]=x
    if lib=='U1': S=Sx
    else: S2=Sx
bpy.data.objects.remove(S2)
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
    if t in (HIPS,) or s in ('Head',): C[t]=Matrix.Identity(3)
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
HANDS=[k for k in M if M[k] in ('hand_l','hand_r')]
ARM_MAX=[None]; TWIST_MAX=[None]; PLANT=[False]; LASTPR={}; SIDE_ABD=[{}]; PR_RATE=float(os.environ.get('PR_RATE','30'))
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
            if n in UPARMS and (CUR_ABD[0] or SIDE_ABD[0]):
                sgn=-1 if pos.x>0 else 1
                ab=CUR_ABD[0]+SIDE_ABD[0].get('L' if 'Left' in n or n.endswith('_L') else 'R',0)
                hy=D[HIPS]@Vector((0,1,0))
                base=Matrix.Translation(pos)@Matrix.Rotation(math.radians(sgn*ab),4,hy)@Matrix.Translation(-pos)@base
        if n in D and n in UPARMS and ARM_MAX[0] is not None:
            hr=D[HIPS]; lat=(hr@Vector((1,0,0))).normalized()
            sh=base.translation; hp=W[HIPS].translation; sgn=1 if (sh-hp).dot(lat)>0 else -1; latv=lat*sgn
            ch=[c for c in TB[n].children if c.name in M][0]
            d=(base.to_3x3()@(wrest(T,n).to_3x3().inverted()@(wrest(T,ch.name).translation-Rb.translation))).normalized()
            ox=d.dot(latv); pr=d-latv*ox; rest_=pr.length
            ang=math.degrees(math.atan2(ox,max(rest_,1e-6)))
            lim=ARM_MAX[0][0 if sgn>0 and n.endswith(('LeftArm','_l')) or (sgn>0 and 'Left' in n) else 1] if isinstance(ARM_MAX[0],(list,tuple)) else ARM_MAX[0]
            prd=pr.normalized() if rest_>1e-5 else (LASTPR.get(n) or Vector((0,0,-1)))
            if LASTPR.get(n) is not None:
                # rate-limit how fast the clamp's swing plane turns about the lateral axis (no single-frame flips)
                lp=(LASTPR[n]-latv*LASTPR[n].dot(latv)).normalized()
                th=math.atan2(lp.cross(prd).dot(latv),lp.dot(prd)); mx=math.radians(PR_RATE)
                if abs(th)>mx: prd=(Matrix.Rotation(math.copysign(mx,th),3,latv)@lp).normalized()
            LASTPR[n]=prd.copy()
            al=math.radians(min(ang,lim))
            if True:
                tgt=(prd*math.cos(al)+latv*math.sin(al)).normalized()
                q=d.rotation_difference(tgt).to_matrix()
                base=Matrix.Translation(sh)@(q@base.to_3x3()).to_4x4()
        if n in D and n in HANDS and TWIST_MAX[0] is not None and b.parent:
            Rf=W[b.parent.name].to_3x3(); rel0=(wrest(T,b.parent.name).to_3x3().inverted()@Rb.to_3x3())
            q=(rel0.inverted()@Rf.inverted()@base.to_3x3()).to_quaternion()
            tw=2*math.atan2(q.y,q.w); tw=(tw+math.pi)%(2*math.pi)-math.pi
            lim=math.radians(TWIST_MAX[0])
            if abs(tw)>lim:
                corr=Quaternion((0,1,0),-(tw-math.copysign(lim,tw)))
                newrel=(q@corr).to_matrix()
                base=Matrix.Translation(base.translation)@(Rf@rel0@newrel).to_4x4()
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
    d=target-Hh; L=min(d.length,l1+l2-1e-4); L=max(L,abs(l1-l2)+1e-4); dn=d.normalized()
    pole=(K-Hh)-dn*((K-Hh).dot(dn));
    if pole.length<1e-6: pole=Vector((0,-1,0))
    pole.normalize()
    ca=(l1*l1+L*L-l2*l2)/(2*l1*L); ang=math.acos(max(-1,min(1,ca)))
    Kn=Hh+(dn*math.cos(ang)+pole*math.sin(ang))*l1
    An=Hh+dn*L
    footrot=W[ft].to_3x3() if not PLANT[0] else wrest(T,ft).to_3x3()
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
    if PLANT[0]:
        for c in TB[ft].children_recursive:
            W[c.name]=W[c.parent.name]@wrest(T,c.parent.name).inverted()@wrest(T,c.name)
def apply(W,f):
    for n in order:
        b=TB[n]; pb=T.pose.bones[n]; Ma=Tinv@W[n]
        if b.parent:
            Rp=b.parent.matrix_local; Pp=Tinv@W[b.parent.name]
            pb.matrix_basis=(Rp.inverted()@b.matrix_local).inverted()@Pp.inverted()@Ma
        else: pb.matrix_basis=b.matrix_local.inverted()@Ma
        pb.rotation_mode='QUATERNION'
        pb.keyframe_insert('rotation_quaternion',frame=f); pb.keyframe_insert('location',frame=f)

CLIPS=json.load(open(os.environ['CLIPS']))
def sample(segs):
    frames=[]
    for seg in segs:
        sname,a0,a1=seg[:3]; spd=seg[3] if len(seg)>3 else 1.0
        act=src_acts[sname]; S.animation_data.action=act; f0,f1=[int(round(x)) for x in act.frame_range]
        a0=f0 if a0 is None else a0; a1=f1 if a1 is None else a1
        fr=[]; t=float(a0)
        while t<=a1+1e-6:
            fi=int(math.floor(t)); sc.frame_set(fi,subframe=t-fi); fr.append(src_pose()); t+=spd
        if frames:  # seam blend 4 frames
            D0,p0=frames[-1]; 
            for k in range(min(4,len(fr))):
                t=(k+1)/5.0; D1,p1=fr[k]
                fr[k]=({b:D0[b].to_quaternion().slerp(D1[b].to_quaternion(),t).to_matrix() for b in D1},p0.lerp(p1,t))
            fr=fr[1:]
        frames+=fr
    return frames
info={}
for tname,cfg in CLIPS.items():
    CUR_ABD[0]=ABD
    LASTPR.clear(); SIDE_ABD[0]=cfg.get('side_abd',{}); ARM_MAX[0]=cfg.get('arm_max',30.0); TWIST_MAX[0]=cfg.get('twist_max',45.0); PLANT[0]=cfg.get('plant',True)
    frames=sample(cfg['segs']); n=len(frames)
    if cfg.get('left_arm_from'):
        # keep the shield arm in the guard pose, carried by the chest (one-handed weapon + shield)
        gsrc,gf=cfg['left_arm_from']; S.animation_data.action=src_acts[gsrc]; sc.frame_set(gf); Dg,_=src_pose()
        LA=[k for k in M if M[k] in ('clavicle_l','upperarm_l','lowerarm_l','hand_l')]; CH=inv['spine_03']
        w=cfg.get('left_arm_weight',1.0)
        for D,pp in frames:
            for k in LA:
                tgt=D[CH]@Dg[CH].inverted()@Dg[k]
                D[k]=D[k].to_quaternion().slerp(tgt.to_quaternion(),w).to_matrix()
    for it in range(3):
        for bn in frames[0][0]:
            q=[fr[0][bn].to_quaternion() for fr in frames]
            st=[math.degrees(q[i].rotation_difference(q[i+1]).angle) for i in range(len(q)-1)]; st=[x if x<=180 else 360-x for x in st]
            for i in range(1,len(st)-1):
                if st[i]>25 and st[i]>2.5*max(st[i-1],st[i+1] if i+1<len(st) else 0,1):
                    # spread the jump over neighbouring frames
                    k0=max(0,i-2); k1=min(len(q)-1,i+3)
                    for k in range(k0+1,k1):
                        t=(k-k0)/(k1-k0); frames[k][0][bn]=q[k0].slerp(q[k1],t).to_matrix()
                    q=[fr[0][bn].to_quaternion() for fr in frames]
                    st=[math.degrees(q[j].rotation_difference(q[j+1]).angle) for j in range(len(q)-1)]; st=[x if x<=180 else 360-x for x in st]
    hold=cfg.get('pad',0)
    frames+= [frames[-1]]*hold
    # optional blend tail back to frame0 (loops)
    if cfg.get('loop'):
        D0,p0=frames[0]; Dl,pl=frames[-1]; L=min(6,n//3)
        for k in range(L):
            t=(k+1)/(L+1); i=len(frames)-L+k; Di,pi=frames[i]
            frames[i]=({b:Di[b].to_quaternion().slerp(D0[b].to_quaternion(),t).to_matrix() for b in Di},pi.lerp(p0,t))
    n=len(frames)
    DAMP=cfg.get('damp',1.0)
    frames=[(D,pp*DAMP) for D,pp in frames]
    MAXDROP=cfg.get('max_drop',0.07)
    for D,pp in frames:
        if pp.z*k_h<-MAXDROP: pp.z=-MAXDROP/k_h
    Ws=[build(D,pp) for D,pp in frames]
    ank={s_:np.array([list(W[LEG[s_][2]].translation) for W in Ws]) for s_ in LEG}
    TOE={s_:[b for b in TB[LEG[s_][2]].children if b.name in M][0].name for s_ in LEG}
    ball={s_:np.array([list(W[TOE[s_]].translation) for W in Ws]) for s_ in LEG}
    rest_ank={s_:wrest(T,LEG[s_][2]).translation.z for s_ in LEG}
    targets={}; contact={}
    for s_ in LEG:
        A=ank[s_]; Bl=ball[s_]
        low=np.minimum(A[:,2]-rest_ank[s_],Bl[:,2]-wrest(T,TOE[s_]).translation.z)
        sp=np.r_[0,np.linalg.norm(np.diff(Bl[:,:2],axis=0),axis=1)*30]
        c=(low<0.03*H)&(sp<0.35)
        # close tiny gaps / drop tiny islands
        c=c.copy()
        for i in range(1,n-1):
            if not c[i] and c[i-1] and c[i+1]: c[i]=True
        contact[s_]=c
        segs=[]; i=0
        while i<n:
            if c[i]:
                j=i
                while j+1<n and c[j+1]: j+=1
                segs.append((i,j)); i=j+1
            else: i+=1
        tg=[None]*n
        lock=np.array(A)
        for (s0,s1) in segs:
            m=A[s0:s1+1].mean(0)
            for k in range(s0,s1+1): lock[k]=[m[0],m[1],rest_ank[s_]]
        # swing frames: blend between previous and next lock positions, keep source lift
        for k in range(n):
            if c[k]: tg[k]=Vector(lock[k]); continue
            prv=[s for s in segs if s[1]<k]; nxt=[s for s in segs if s[0]>k]
            lift=max(0.0,A[k,2]-A[:,2].min())
            if prv and nxt:
                a_=prv[-1][1]; b_=nxt[0][0]; t=(k-a_)/(b_-a_); t=t*t*(3-2*t)
                p=Vector(lock[a_]).lerp(Vector(lock[b_]),t)
            elif prv: p=Vector(lock[prv[-1][1]])
            elif nxt: p=Vector(lock[nxt[0][0]])
            else: p=Vector(A[k])
            p.z=rest_ank[s_]+lift; tg[k]=p
        if DAMP<1:
            base=wrest(T,LEG[s_][2]).translation
            tg=[base+(p-base)*DAMP if p is not None else None for p in tg]
            for p in tg: p.z=rest_ank[s_] if cfg.get('plant',True) else max(p.z,rest_ank[s_])
        targets[s_]=tg
    actT=bpy.data.actions.get(tname)
    if actT: bpy.data.actions.remove(actT)
    actT=bpy.data.actions.new(tname); actT.use_fake_user=True
    T.animation_data_create(); T.animation_data.action=actT
    for i,W in enumerate(Ws):
        for s_ in LEG: leg_ik(W,s_,targets[s_][i])
        apply(W,i)
    info[tname]={'source':' + '.join('Quaternius '+g[0].replace('U1:','UAL1 ').replace('U2:','UAL2 ')+('' if g[1] is None else f' [{g[1]}-{g[2]}]')+('' if len(g)<4 or g[3]==1 else f' x{g[3]}') for g in cfg['segs']),'frames':n,'fps':30,'loop':bool(cfg.get('loop')),'lower_body_damp':DAMP,'max_hip_drop_m':MAXDROP,'side_abd_deg':SIDE_ABD[0],'arm_out_max_deg':ARM_MAX[0],'wrist_twist_max_deg':TWIST_MAX[0],'feet_planted_flat':PLANT[0],
                  'contact_frames':{s_:int(contact[s_].sum()) for s_ in LEG}}
    print('CLIP',tname,n)
T.animation_data.action=bpy.data.actions['idle'] if 'idle' in bpy.data.actions else None
bpy.data.objects.remove(S)
for x in list(bpy.data.actions):
    if x in src_acts.values(): bpy.data.actions.remove(x)
info['_params']={'CAPE_K':CAPE_K,'CAPE_MODE':CAPE_MODE,'ABD':ABD,'ABD_IDLE':ABD_IDLE,'HOLD':HOLD,'HOLD_MODE':os.environ.get('HOLD_MODE','parent')}
json.dump(info,open(out+'.clips.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
for pb in T.pose.bones: pb.custom_shape=None
bpy.ops.export_scene.gltf(filepath=out+'.glb',export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
