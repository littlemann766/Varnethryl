import bpy, sys, math, json, os
from mathutils import Vector, Quaternion, Matrix
argv=sys.argv[sys.argv.index('--')+1:]
src, out = argv[0], argv[1]
FPS=30
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
scn=bpy.context.scene; scn.render.fps=FPS
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
B=arm.data.bones
def has(n): return n in B
# --- frames
up=Vector((0,0,1))
f = Vector((0,-1,0))
if has('foot_L') and has('toe_L'):
    d=B['toe_L'].head_local-B['foot_L'].head_local; f=Vector((0,-1,0)) if d.y<0 else Vector((0,1,0))
sideL = 1.0 if B['upperArm_L'].head_local.x>0 else -1.0
lft = Vector((sideL,0,0))
hipsH=B['hips'].head_local.copy()
legLen = (B['thigh_L'].length+B['shin_L'].length) if has('thigh_L') else 0.5
H = max(b.head_local.z for b in B)  # approx height
def V(F,U,S,s):  # body-local vector; s=+1 left, -1 right
    return (f*F + up*U + lft*(S*s)).normalized()
def rot(axis,deg): return Quaternion(axis.normalized(), math.radians(deg))
CORE=set()
for s in 'LR':
    CORE|={f'upperArm_{s}',f'foreArm_{s}',f'thigh_{s}',f'shin_{s}',f'foot_{s}'}
SPINE=[n for n in ['spine','spine2','chest','upperChest'] if has(n)]
HEADC=[n for n in ['neck','head'] if has(n)]
_hw={'spine':.3,'spine2':.35,'chest':.35}
_t=sum(v for k,v in _hw.items() if k in B)
HW={k:v/_t for k,v in _hw.items() if k in B}
SEC_PFX=('hair','cape','coat','tail','finHip','fluke')
def depth(n):
    d=0;b=B[n]
    while b.parent and b.parent.name.startswith(SEC_PFX): d+=1;b=b.parent
    return d
def chainlen(n):
    b=B[n]
    while b.parent and b.parent.name.startswith(SEC_PFX): b=b.parent
    def dd(x): return 1+max([dd(c) for c in x.children if c.name.startswith(SEC_PFX)] or [0])
    return dd(b)
S2=lambda t,n=1,ph=0: math.sin(2*math.pi*(n*t+ph))
C2=lambda t,n=1,ph=0: math.cos(2*math.pi*(n*t+ph))
# ---- clip definitions: return dict of params at phase t
def P_hover(t):
    return dict(pitch=8+2*S2(t), roll=1.5*S2(t,1,.25), yaw=0, bob=0.022*H*S2(t),
      arch=2+2*S2(t,1,.1), headUp=0.5,
      th={1:V(0.28+0.06*S2(t),-1,0.12,1),-1:V(0.10-0.06*S2(t),-1,0.12,-1)},
      sh={1:V(-0.45-0.08*S2(t,1,.15),-1,0.06,1),-1:V(-0.30+0.08*S2(t,1,.15),-1,0.06,-1)},
      ft={s:V(0.85,-0.5,0.03,s) for s in(1,-1)},
      ua={s:V(0.08+0.06*S2(t,1,.1),-1,0.36+0.05*S2(t,1,.1),s) for s in(1,-1)},
      fa={s:V(0.32+0.08*S2(t,1,.2),-1,0.28,s) for s in(1,-1)},
      wind=-up*0.15, bias=3, flut=4)
def forwardish(t,pitch,ua,fa,legS,flut,bias,kb):
    return dict(pitch=pitch+2*S2(t), roll=2*S2(t,1,.25), yaw=0, bob=0.012*H*S2(t),
      arch=-6+1.5*S2(t,1,.1), headUp=0.38,
      th={s:V(-0.12+0.07*S2(t,1,.5*(s<0)),-1,legS,s) for s in(1,-1)},
      sh={s:V(-0.12-kb+0.08*S2(t,1,.5*(s<0)+.12),-1,legS*0.6,s) for s in(1,-1)},
      ft={s:V(0.75,-0.65,0.0,s) for s in(1,-1)},
      ua={s:V(ua[0],-1,ua[1],s) for s in(1,-1)},
      fa={s:V(fa[0],-1,fa[1],s) for s in(1,-1)},
      wind=None, bias=bias, flut=flut)
P_forward=lambda t: forwardish(t,64,(-0.22,0.24),(-0.06,0.18),0.07,7,14,0.18)
P_fast=lambda t: forwardish(t,78,(-0.14,0.13),(-0.03,0.09),0.03,9,18,0.08)
def P_ascend(t):
    return dict(pitch=14+2*S2(t), roll=1.5*S2(t,1,.25), yaw=0, bob=0.02*H*S2(t),
      arch=-4, headUp=0.5,
      th={s:V(-0.08+0.06*S2(t,1,.5*(s<0)),-1,0.08,s) for s in(1,-1)},
      sh={s:V(-0.28+0.08*S2(t,1,.5*(s<0)+.12),-1,0.05,s) for s in(1,-1)},
      ft={s:V(0.8,-0.6,0,s) for s in(1,-1)},
      ua={s:V(-0.22-0.06*S2(t),-1,0.26,s) for s in(1,-1)},
      fa={s:V(-0.05-0.06*S2(t,1,.1),-1,0.2,s) for s in(1,-1)},
      wind=-up, bias=10, flut=6)
def P_descend(t):
    return dict(pitch=-8+2*S2(t), roll=1.5*S2(t,1,.25), yaw=0, bob=0.015*H*S2(t),
      arch=3, headUp=0,
      th={1:V(0.45,-1,0.14,1),-1:V(0.30,-1,0.14,-1)},
      sh={1:V(-0.15,-1,0.06,1),-1:V(-0.30,-1,0.06,-1)},
      ft={s:V(0.95,-0.3,0.03,s) for s in(1,-1)},
      ua={s:V(0.15,-1+0.08*S2(t,1,.05),0.75,s) for s in(1,-1)},
      fa={s:V(0.4,-1+0.1*S2(t,1,.15),0.5,s) for s in(1,-1)},
      wind=up, bias=10, flut=6)
def bank(sgn):
    def P(t):
        p=P_forward(t); p['roll']=sgn*34+2*S2(t,1,.25); p['yaw']=sgn*8
        inn=sgn  # inner side (left for L bank)
        p['ua'][inn]=V(-0.15,-1,0.45,inn); p['fa'][inn]=V(0.05,-1,0.38,inn)
        p['ua'][-inn]=V(-0.25,-1,0.16,-inn)
        p['th'][inn]=V(0.02,-1,0.12,inn); p['sh'][inn]=V(-0.40,-1,0.05,inn)
        return p
    return P
CLIPS=[('fly_hover',2.0,P_hover),('fly_forward',1.6,P_forward),('fly_fast',1.0,P_fast),
       ('fly_ascend',1.6,P_ascend),('fly_descend',1.6,P_descend),('fly_bank_L',1.6,bank(1)),('fly_bank_R',1.6,bank(-1))]
# roll sign: bank_L must lower the left side
def bodyQ(p):
    qp=rot(f.cross(up)*-1, 0)  # placeholder
    # pitch: rotate up toward front -> axis a=u x f
    qpitch=rot(up.cross(f), p['pitch'])
    fw=qpitch@f
    qr=rot(fw, p['roll']); 
    if (qr@ (qpitch@lft)).z > (qpitch@lft).z and p['roll']>0: qr=rot(fw,-p['roll'])
    if (qr@ (qpitch@lft)).z < (qpitch@lft).z and p['roll']<0: qr=rot(fw,-p['roll'])
    qy=rot(up, p['yaw']*sideL*(1 if f.y<0 else -1))
    return qy@qr@qpitch
order=[b for b in B]  # bones are parent-first in Blender
REST={b.name:b.matrix_local.copy() for b in B}
CH={'upperArm':'foreArm','foreArm':'hand','thigh':'shin','shin':'foot','foot':'toe','neck':'head'}
def restvec(b):
    n=b.name; base=n[:-2] if n[-2:] in('_L','_R') else n; suf=n[len(base):]
    c=CH.get(base)
    if c and has(c+suf):
        v=B[c+suf].head_local-b.head_local
        if v.length>1e-4: return v.normalized()
    for ch in b.children:
        v=ch.head_local-b.head_local
        if v.length>1e-3: return v.normalized()
    if base=='head': return up.copy()
    if base=='foot': return (f*0.9-up*0.3).normalized()
    if b.parent:
        v=b.head_local-b.parent.head_local
        if v.length>1e-3: return v.normalized()
    return (b.tail_local-b.head_local).normalized()
RV={b.name:restvec(b) for b in B}
import os
DBG=os.environ.get('DBG','')
WAVE={'fly_hover':(8,1,0.12),'fly_forward':(12,2,0.2),'fly_fast':(15,3,0.3),'fly_ascend':(10,2,0.18),'fly_descend':(10,2,0.18),'fly_bank_L':(12,2,0.2),'fly_bank_R':(12,2,0.2)}
CUR_CLIP=''
PUSH=0.0
def solve(p,t):
    if 'nosec' in DBG: p['bias']=0; p['flut']=0
    _k=float(os.environ.get('SECK','1')); p['bias']*=_k; p['flut']*=_k
    if 'nohead' in DBG: p['headUp']=0
    if 'noarm' in DBG: p['ua']={s:V(0.05,-1,0.25,s) for s in(1,-1)}; p['fa']={s:V(0.15,-1,0.2,s) for s in(1,-1)}
    if 'nofoot' in DBG: p['ft']=None
    if 'noarch' in DBG: p['arch']=0
    Q=bodyQ(p); P={}
    for b in order:
        n=b.name
        if b.parent is None: P[n]=REST[n].copy(); continue
        pn=b.parent.name
        I=P[pn]@REST[pn].inverted()@REST[n]
        h=I.translation.copy()
        def about(q,M=None):
            M=I if M is None else M; hh=M.translation.copy()
            return Matrix.Translation(hh)@q.to_matrix().to_4x4()@Matrix.Translation(-hh)@M
        def aim(target):
            cur=((I@REST[n].inverted()).to_3x3()@RV[n]).normalized()
            return about(cur.rotation_difference(target))
        if n=='hips':
            M=Matrix.Translation(hipsH)@Q.to_matrix().to_4x4()@Matrix.Translation(-hipsH)@I
            M=Matrix.Translation(up*p['bob'])@M; P[n]=M; continue
        side=1 if n.endswith('_L') else -1
        base=n[:-2] if n[-2:] in('_L','_R') else n
        if n in SPINE or n in HEADC:
            ext=-p['headUp']*max(p['pitch'],0)
            ang=p['arch']/len(SPINE) if n in SPINE else 0
            ang+=ext*HW.get(n,0)
            P[n]=about(rot(Q@up.cross(f), ang)); continue
        if base=='shoulder' and has('upperArm'+n[-2:]):
            ua=Q@p['ua'][side]; cur=((I@REST[n].inverted()).to_3x3()@RV[n]).normalized()
            q=cur.rotation_difference(ua); P[n]=about(Quaternion(q.axis,q.angle*0.18)); continue
        if n in CORE:
            key={'upperArm':'ua','foreArm':'fa','thigh':'th','shin':'sh','foot':'ft'}[base]
            if p[key] is None: P[n]=I; continue
            QQ=Q
            if key in('ua','fa'):
                tot=sum(HW.get(k,0) for k in HW if k not in('neck','head'))
                QQ=rot(Q@up.cross(f), -p['headUp']*max(p['pitch'],0)*tot + p['arch'])@Q
            P[n]=aim(QQ@p[key][side]); continue
        if n.startswith(('cape','coat')):
            d=depth(n); tip=not any(c.name.startswith(('cape','coat')) for c in b.children)
            if n.startswith('cape'):
                rb=B[n]
                while rb.parent.name.startswith('cape'): rb=rb.parent
                rp=rb.parent.name
                Rc=(P[rp]@REST[rp].inverted()).to_quaternion()   # chest/upper-back frame in flight
                drape=(Rc@RV[n]).normalized()                     # where this segment lies at rest, carried by the back
                straight=(Q@(-up + f*(float(os.environ.get('CO','-0.2')) if p['pitch']>30 else -0.18))).normalized()
                wgt=min(1.0, float(depth(n)))                        # root keeps its rest attachment, blends to straight by segment 3
                tgt=drape.slerp(straight,wgt) if hasattr(drape,'slerp') else (drape*(1-wgt)+straight*wgt).normalized()
            else:
                th='thigh'+n[-2:] if n[-2:] in('_L','_R') else None
                if th and th in P:
                    tv=((P[th]@REST[th].inverted()).to_3x3()@RV[th]).normalized()
                    sd=Q@lft*(1 if n.endswith('_L') else -1)*sideL
                    tgt=(tv+sd*0.12+(Q@-f)*0.12).normalized()
                else: tgt=Q@(-up)
            if n.startswith('cape'):
                pt=p['pitch']; W=WAVE.get(CUR_CLIP,(10,2,0.2))
                Lc=chainlen(n); dd=depth(n); u_=(dd+1)/Lc
                ang=W[0]*u_**1.5*0.5*(1+S2(t,W[1],-W[2]*dd))   # travelling wave root->tip, away from body only
                fl=rot(Rc@up.cross(f), ang)
            else: fl=Quaternion()
            cur=((I@REST[n].inverted()).to_3x3()@RV[n]).normalized()
            if n.startswith('cape') and PUSH: fl=rot(Rc@up.cross(f), PUSH)@fl
            q=cur.rotation_difference(fl@tgt)
            cl_=chainlen(n)
            if cl_<=2: q=Quaternion()
            P[n]=about(q); continue
        if n.startswith(SEC_PFX):
            d=depth(n); cur=((I@REST[n].inverted()).to_3x3()@RV[n]).normalized()
            wind = p['wind'] if p['wind'] is not None else -f
            wind=wind.normalized(); ax=cur.cross(wind)
            q=Quaternion()
            k=(0.45 if n.startswith('hair') else 1.0)*min(1.0,chainlen(n)/4.0)
            if ax.length>1e-4: q=rot(ax, k*p['bias']*min(1,ax.length*1.5)/(1+0.3*d))
            fl=rot(Q@lft, k*p['flut']*S2(t,2 if p['flut']>6 else 1,-0.11*(d+1)))
            P[n]=about(fl@q); continue
        P[n]=I
    return P
act_names=[]
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
arm.animation_data_create()
for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
for o in bpy.data.objects:
    if o.animation_data: o.animation_data_clear() if o!=arm else None
for b in arm.pose.bones: b.rotation_mode='QUATERNION'
if True:  # cape weight cleanup: cape-dominant verts follow only cape chain + upper back
    KEEP=('cape','chest','upperChest','shoulder')
    for o in bpy.data.objects:
        if o.type!='MESH' or not o.vertex_groups: continue
        GN={g.index:g.name for g in o.vertex_groups}
        if not any(n.startswith('cape2') for n in GN.values()): continue
        for v in o.data.vertices:
            if not v.groups: continue
            dg_=max(v.groups,key=lambda g:g.weight)
            if not GN[dg_.group].startswith('cape'): continue
            for g in v.groups:
                if not GN[g.group].startswith(KEEP): g.weight=0.0
            tot=sum(g.weight for g in v.groups)
            if tot>0:
                for g in v.groups: g.weight/=tot
if os.environ.get('REWEIGHT') or True:
    pass
if os.environ.get('REWEIGHT'):
    CL=('cape','coat'); LIMB=('upperArm','foreArm','hand','thigh','shin','foot','toe','fingers','index','middle','ring','pinky','thumb')
    nfix=0
    for o in bpy.data.objects:
        if o.type!='MESH' or not o.vertex_groups: continue
        GN={g.index:g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            cw=sum(g.weight for g in v.groups if GN[g.group].startswith(CL)); lw=sum(g.weight for g in v.groups if GN[g.group].startswith(LIMB))
            if cw>0 and lw>0:
                drop=CL if lw>=cw else LIMB; nfix+=1
                for g in v.groups:
                    if GN[g.group].startswith(drop): g.weight=0.0
                tot=sum(g.weight for g in v.groups)
                if tot>0:
                    for g in v.groups: g.weight/=tot
    print('REWEIGHT verts',nfix)
for o in bpy.data.objects:
    if o.type!='MESH' or not o.vertex_groups: continue
    for v in o.data.vertices:
        gs=sorted(v.groups,key=lambda g:-g.weight)
        for g in gs[4:]: g.weight=0.0
        tot=sum(g.weight for g in gs[:4])
        if tot>0:
            for g in gs[:4]: g.weight/=tot
import numpy as np
from mathutils.bvhtree import BVHTree
exec(open('/workspace/hero-motion/fly/inside_lib.py').read())
CHN=0
if os.environ.get('CHAINW'):   # cape verts that lie above their dominant cape bone's head belong to the segment above: move that weight to the parent cape bone
    for o in bpy.data.objects:
        if o.type!='MESH' or not o.vertex_groups: continue
        GN={g.index:g.name for g in o.vertex_groups}; IX={v:k for k,v in GN.items()}
        for v in o.data.vertices:
            if not v.groups: continue
            dg_=max(v.groups,key=lambda g:g.weight); bn=GN[dg_.group]
            if not bn.startswith('cape') or bn not in B or B[bn].parent is None or not B[bn].parent.name.startswith('cape'): continue
            pb_=B[bn].parent; h=B[bn].head_local; ph=pb_.head_local; ax=(h-ph); L_=ax.length; ax=ax/L_
            sabove=(h-v.co).dot(ax)   # >0: vertex sits on the parent side of this head
            if sabove<=0: continue
            fr_=min(1.0,2*sabove/L_); mv=dg_.weight*fr_
            dg_.weight-=mv
            gi=IX.get(pb_.name)
            if gi is None: continue
            hit=[g for g in v.groups if g.group==gi]
            if hit: hit[0].weight+=mv
            else: o.vertex_groups[pb_.name].add([v.index],mv,'ADD')
            CHN+=1
print('CHAINW',CHN)
SEAMN=0
if os.environ.get('SEAM'):   # cape seam verts (cape-chain weight < 0.5) ride with the upper back they are sewn to
    for o in bpy.data.objects:
        if o.type!='MESH' or not o.vertex_groups: continue
        GN={g.index:g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            cw=sum(g.weight for g in v.groups if GN[g.group].startswith('cape'))
            if 0<cw<0.5 and any(GN[g.group] in ('chest','upperChest') for g in v.groups):
                for g in v.groups:
                    if GN[g.group].startswith('cape'): g.weight=0.0
                tot=sum(g.weight for g in v.groups)
                for g in v.groups: g.weight/=tot
                SEAMN+=1
print('SEAM',SEAMN)
RESTFIX=0
MG=float(os.environ.get('MARGIN','0.004'))
RFM=float(os.environ.get('RFM','0.004'))
for o in bpy.data.objects:   # rest-geometry fix: cape verts sunk in / touching the body at bind are lifted 6 mm off it
    if o.type!='MESH' or not o.vertex_groups: continue
    GN={g.index:g.name for g in o.vertex_groups}
    dom=[GN[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in o.data.vertices]
    body=[d.startswith(('hips','spine','chest','upperChest','thigh','shin','foot','toe')) for d in dom]
    polys=[list(p.vertices) for p in o.data.polygons if all(body[i] for i in p.vertices)]
    if not polys: continue
    co=[v.co.copy() for v in o.data.vertices]; bvh=BVHTree.FromPolygons(co,polys)
    for i,d in enumerate(dom):
        if d.startswith('cape') and is_bad(bvh,co[i],RFM):
            loc,nor,fi,dist=bvh.find_nearest(co[i]); o.data.vertices[i].co=loc+nor*(RFM+0.002); RESTFIX+=1
print('RESTFIX',RESTFIX)
BODY=[o for o in bpy.data.objects if o.type=='MESH' and o.vertex_groups]
def masks(o):
    GN={g.index:g.name for g in o.vertex_groups}
    dom=[GN[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in o.data.vertices]
    cape=np.array([d.startswith('cape') for d in dom])
    body=np.array([d.startswith(('hips','spine','chest','upperChest','thigh','shin','foot','toe')) for d in dom])
    return cape,body
MASK={o.name:masks(o) for o in BODY}
GLUED=0
GR=float(os.environ.get('GLUEROOT','0'))
if os.environ.get('GLUE') or GR>0 or os.environ.get('GLUEUC'):   # cape verts hugging the torso follow the skin they lie on (blend 3-6 cm), keep MASK = original cape set
    for o in BODY:
        GN={g.index:g.name for g in o.vertex_groups}; cape,body=MASK[o.name]
        polys=[list(p.vertices) for p in o.data.polygons if all(body[i] for i in p.vertices)]
        if not polys or not cape.any(): continue
        co=[v.co.copy() for v in o.data.vertices]; bvh=BVHTree.FromPolygons(co,polys)
        for i in np.where(cape)[0]:
            loc,nor,fi,d=bvh.find_nearest(co[i])
            if loc is None or d>0.06: continue
            w=min(1.0,max(0.0,(0.06-d)/0.03))
            if os.environ.get('GLUEUC'):
                GNb={g.index:g.name for g in o.vertex_groups}
                fb=max(o.data.vertices[polys[fi][0]].groups,key=lambda g:g.weight)
                if GNb[fb.group] not in ('upperChest','chest') or d>0.04: continue
                w=0.7*(0.04-d)/0.04
            elif GR>0:
                rh=arm.data.bones['cape'].head_local; r_=(co[i]-rh).length
                if r_>GR: continue
                w*=min(1.0,(GR-r_)/(GR*0.5))
            j=min(polys[fi],key=lambda k:(co[k]-co[i]).length)
            cw={GN[g.group]:g.weight*(1-w) for g in o.data.vertices[i].groups}
            for g in o.data.vertices[j].groups: cw[GN[g.group]]=cw.get(GN[g.group],0)+g.weight*w
            top=sorted(cw.items(),key=lambda x:-x[1])[:4]; tot=sum(x[1] for x in top)
            for g in list(o.data.vertices[i].groups): o.vertex_groups[GN[g.group]].remove([int(i)])
            for nm,wt in top: o.vertex_groups[nm].add([int(i)],wt/tot,'REPLACE')
            GLUED+=1
print('GLUED',GLUED)
HASCAPE=any(m[0].any() for m in MASK.values()) and any(n.startswith('cape') and chainlen(n)>2 for n in B.keys())
def inside_count():
    dg=bpy.context.evaluated_depsgraph_get(); allco=[];allbody=[];allcape=[];polys=[];off=0
    for o in BODY:
        e=o.evaluated_get(dg); m=e.to_mesh(); co=[o.matrix_world@v.co for v in m.vertices]
        cape,body=MASK[o.name]
        for p in m.polygons:
            if all(body[i] for i in p.vertices): polys.append([i+off for i in p.vertices])
        allco+=co; allcape+=[i+off for i in np.where(cape)[0]]; off+=len(co); e.to_mesh_clear()
    if not polys or not allcape: return 0
    bvh=BVHTree.FromPolygons(allco,polys); c=0
    for i in allcape:
        p=allco[i]
        if is_bad(bvh,p,MG): c+=1
    return c
def apply_pose(P,fr=None):
    for b in B:
        n=b.name
        if b.parent is None: continue
        pn=b.parent.name
        L=(REST[pn].inverted()@REST[n]).inverted()@P[pn].inverted()@P[n]
        pb=arm.pose.bones[n]; loc,q,_=L.decompose(); pb.rotation_quaternion=q
        if n=='hips': pb.location=loc
        if fr is not None:
            pb.keyframe_insert('rotation_quaternion',frame=fr)
            if n=='hips': pb.keyframe_insert('location',frame=fr)
REPORT={}
for name,dur,fn in CLIPS:
    CUR_CLIP=name
    act=bpy.data.actions.new(name); arm.animation_data.action=None
    N=int(round(dur*FPS)); pushes=[0.0]*N; before=[0]*N
    if os.environ.get('FIXPUSH'): HASCAPE_=False; sm=[float(os.environ['FIXPUSH'])]*N
    elif HASCAPE:
        for fr in range(N):
            t=fr/N; pv=0.0
            while True:
                PUSH=pv; P=solve(fn(t),t); apply_pose(P); bpy.context.view_layer.update()
                c=inside_count()
                if fr==0 or pv==0.0: before[fr]=c if pv==0.0 else before[fr]
                if c==0 or pv>=35: break
                pv+=2.5
            pushes[fr]=pv
        def envelope(req):
            m=[max(req[(fr+k)%N] for k in range(-6,7)) for fr in range(N)]
            for _ in range(3): m=[(m[(fr-1)%N]+2*m[fr]+m[(fr+1)%N])/4 for fr in range(N)]
            return m
        req=[p+(2.0 if p>0 else 0.0) for p in pushes]
        for it in range(5):
            sm=envelope(req); changed=False
            for fr in range(N):
                t=fr/N; PUSH=sm[fr]; P=solve(fn(t),t); apply_pose(P); bpy.context.view_layer.update()
                if inside_count()==0: continue
                for dv in (2.5,5,7.5,10,15,20,25):
                    if sm[fr]+dv>50: break
                    PUSH=sm[fr]+dv; P=solve(fn(t),t); apply_pose(P); bpy.context.view_layer.update()
                    if inside_count()==0: req[fr]=PUSH+1.0; changed=True; break
            if not changed: break
        sm=envelope(req)
    elif not os.environ.get('FIXPUSH'): sm=[0.0]*N
    arm.animation_data.action=act
    after=[]
    for fr in range(N+1):
        t=(fr%N)/N; PUSH=sm[fr%N]; P=solve(fn(t),t); apply_pose(P,fr)
    arm.animation_data.action=None
    if HASCAPE:
        for fr in range(N):
            t=fr/N; PUSH=sm[fr]; P=solve(fn(t),t); apply_pose(P); bpy.context.view_layer.update(); after.append(inside_count())
    REPORT[name]=dict(before=max(before) if HASCAPE else None,after=max(after) if after else None,push_max=round(max(sm),1))
    arm.animation_data.action=act
    act.use_fake_user=True
    tr=arm.animation_data.nla_tracks.new(); tr.name=name; tr.strips.new(name,0,act); tr.mute=True
arm.animation_data.action=None
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_animations=True,
    export_animation_mode='NLA_TRACKS', export_force_sampling=True, export_frame_step=1, export_yup=True)
print('PEN',json.dumps(REPORT)); json.dump(REPORT,open(out+'.pen.json','w'))
print('OK',out)
