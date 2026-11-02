# Equipment v2 (fitted): per-hero armour conformed to the hero's own body mesh.
# usage: blender -b -P fit_hero.py -- <hero> <family> <outdir>
# Reads Lucian's rig glb (read-only), writes Beth's own fitted skinned pieces + per-slot body masks.
import bpy,sys,os,json,math,numpy as np
sys.path.insert(0,'/workspace/godot-art/loot3_tools')
import bl, armor3d as A, gmodels as G
from vox import V
from edata import RARITIES
from mathutils.kdtree import KDTree
args=sys.argv[sys.argv.index('--')+1:]; HERO,FAM,OUT=args[0],args[1],args[2]; os.makedirs(OUT,exist_ok=True); ROBED=FAM in ('cloth','mystic')
SRC=args[3] if len(args)>3 else f'/workspace/vmain/voxel/{HERO}_voxel.glb'   # v3: Darius uses Lucky's weaponless rig (af4e553, read-only copy)
ONLY=args[4].split(',') if len(args)>4 else None
RES=0.01
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
body=max([o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm],key=lambda o:len(o.data.vertices))
arm.data.pose_position='REST'; bpy.context.view_layer.update()
for o in list(bpy.data.objects):
    if o not in (arm,body): bpy.data.objects.remove(o)
me=body.data; mw=np.array(body.matrix_world)
co=np.array([v.co for v in me.vertices]); co=co@mw[:3,:3].T+mw[:3,3]
gn=[g.name for g in body.vertex_groups]
VW=[]; dom=np.zeros(len(co),int)
for i,v in enumerate(me.vertices):
    w=sorted(((g.weight,gn[g.group]) for g in v.groups if g.weight>0.001),reverse=True); VW.append(w); dom[i]=gn.index(w[0][1]) if w else -1
domname=np.array([gn[d] if d>=0 else '' for d in dom])
BH={b.name:np.array(arm.matrix_world@b.head_local) for b in arm.data.bones}; BT={b.name:np.array(arm.matrix_world@b.tail_local) for b in arm.data.bones}
# ---------- voxelise body (rest pose) ----------
me.calc_loop_triangles(); T=np.array([t.vertices for t in me.loop_triangles]); P=co[T]
lo=co.min(0)-0.08; hi=co.max(0)+np.array([0.08,0.08,0.35]); S=np.ceil((hi-lo)/RES).astype(int)+1
surf=np.zeros(S,bool)
L=np.max(np.linalg.norm(P[:,[1,2,0]]-P,axis=2),1); N=np.clip(np.ceil(L/(RES*0.5)).astype(int),1,40)
for n in np.unique(N):
    tri=P[N==n]; ab=[(a/n,b/n) for a in range(n+1) for b in range(n+1-a)]
    for a,b in ab:
        q=tri[:,0]*(1-a-b)+tri[:,1]*a+tri[:,2]*b; ij=np.floor((q-lo)/RES).astype(int); surf[ij[:,0],ij[:,1],ij[:,2]]=True
def dil(m,k=1):
    for _ in range(k):
        o=m.copy(); o[1:]|=m[:-1]; o[:-1]|=m[1:]; o[:,1:]|=m[:,:-1]; o[:,:-1]|=m[:,1:]; o[:,:,1:]|=m[:,:,:-1]; o[:,:,:-1]|=m[:,:,1:]; m=o
    return m
out=np.zeros(S,bool); out[0]=out[-1]=True; out[:,0]=out[:,-1]=True; out[:,:,0]=out[:,:,-1]=True; out&=~surf
while True:
    n2=dil(out)&~surf
    if n2.sum()==out.sum(): break
    out=n2
solid=~out; skin=solid&dil(out)          # body cells touching air
sidx=np.argwhere(skin); spos=lo+(sidx+0.5)*RES
kd=KDTree(len(co))
for i,p in enumerate(co): kd.insert(p,i)
kd.balance()
NV=[kd.find(p)[1] for p in spos]; cb=np.array([dom[i] for i in NV]); cbn=np.array([gn[d] if d>=0 else '' for d in cb])
capew=np.array([sum(w for w,b in VW[i] if b.startswith('cape')) for i in NV])   # v3: cape cloth that is weighted mostly to upperChest at the top
def tpar(pos,b):   # 0..1 along bone
    h,t=BH[b],BT[b]; d=t-h; return ((pos-h)@d)/(d@d)
_fv=co[np.isin(domname,['foot_L','toe_L','foot_R','toe_R'])]
FRONT=float(np.sign(_fv[:,1].mean()-(BH['foot_L'][1]+BH['foot_R'][1])/2)) if len(_fv) else -1.0   # toes stick out in front of the ankles (works on every rig)
neckz=BH['neck'][2]; beltz=BH['spine'][2]
def ero(m,k=1): return ~dil(~m,k)
def close(m,k): return ero(dil(m,k),k)
def _fax(X):
    f_=BH['foot'+X]; d_=np.array([0,FRONT*0.14,-0.03]); u_=np.clip(((spos-f_)@d_)/(d_@d_),-0.1,1); return np.linalg.norm(spos-f_-u_[:,None]*d_,axis=1)
def region(slot,side=None):
    m=np.zeros(len(sidx),bool); X='_'+(side or '')
    if slot=='chest':
        m=(np.isin(cbn,['spine','spine2','chest','upperChest','hips'])|np.char.startswith(cbn.astype(str),'coat'))&(spos[:,2]<neckz-0.005)&(spos[:,2]>beltz-0.03)   # v11: overlaps the belt (no tunic bleed between them)
        sx=max(abs(BH['upperArm_L'][0])-0.035,0.15); m&=abs(spos[:,0])<sx; m&=(capew<0.15)|(((spos[:,1]-BH['spine'][1])*FRONT)>0)|np.char.startswith(cbn.astype(str),'coat')   # v11: front cells always (Wren's coat-weighted tunic)
    elif slot=='shoulder':
        ua='upperArm'+X; sgn=np.sign(BH[ua][0])
        m=(np.isin(cbn,[ua,'shoulder'+X])&(tpar(spos,ua)<(0.35 if ROBED else 0.78)))
        if ROBED: m&=spos[:,2]>BH[ua][2]-0.01   # v15 slim: mantle rides on top of the shoulder only and drapes from there
        m|=np.isin(cbn,['upperChest','chest'])&(spos[:,0]*sgn>abs(BH[ua][0])-0.05)&(spos[:,2]>BH[ua][2]-0.09)
        m&=spos[:,2]<BH[ua][2]+9   # v10: no cap (1-vox pauldrons hug the shoulder; a cap exposed raw body voxels)
    elif slot=='glove':      # gauntlet + vambrace + couter (overlaps the rerebrace -> no elbow gap)
        m=((cbn=='foreArm'+X)&(tpar(spos,'foreArm'+X)>(0.55 if BH['hand'+X][2]>BH['upperArm'+X][2]-0.15 else 0.05))) if ROBED else ((cbn=='foreArm'+X)|((cbn=='upperArm'+X)&(tpar(spos,'upperArm'+X)>0.66)))   # robed: gauntlet + cuff only, the sleeve stays
        m|=np.array([n.endswith(X) and (n.startswith(('hand','fingers','index','middle','ring','pinky','thumb'))) for n in cbn])
    elif slot=='leg':        # cuisse + poleyn (overlaps the greave -> no knee gap)
        m=(cbn=='thigh'+X)|((cbn=='shin'+X)&(tpar(spos,'shin'+X)<0.62))
        m|=np.char.startswith(cbn.astype(str),'coat')&(spos[:,0]*np.sign(BH['thigh'+X][0])>0)&(spos[:,2]<beltz-0.12)   # v16: coat-weighted shin cells (Rook) get a greave too
    elif slot=='boot':
        m=((cbn=='shin'+X)&(tpar(spos,'shin'+X)>=0.12))|(np.isin(cbn,['foot'+X,'toe'+X])&((_fax(X)<0.065) if HERO=='rook' else True))   # v29: no claw hem bits   # v19: boot follows the foot, not the coat hem
    elif slot=='belt' and ROBED:   # robed: a sash/girdle band only, the robe skirt stays
        m=np.isin(cbn,['hips','spine','spine2'])&(abs(spos[:,2]-beltz)<0.03)
        kz=BH['foot_L'][2]+0.04; m|=(spos[:,2]<beltz)&(spos[:,2]>kz)&(abs(spos[:,0])<0.40)&~np.array([n.startswith(('hand','fing','index','middle','ring','pinky','thumb','foreArm','upperArm')) for n in cbn])   # v15: tabard panel hides the patterned skirt
    elif slot=='belt':       # belt + faulds: covers the groin so the tabard no longer shows there
        m=(np.isin(cbn,['hips','spine','spine2'])|np.char.startswith(cbn.astype(str),'coat')|np.char.startswith(cbn.astype(str),'thigh'))&(spos[:,2]<beltz+0.035)&(spos[:,2]>beltz-0.17)
        m&=~(np.char.startswith(cbn.astype(str),'thigh')&(spos[:,2]<beltz-0.12))
        m|=(np.isin(cbn,['hips'])|np.char.startswith(cbn.astype(str),'coat'))&(abs(spos[:,0])<0.09)&(spos[:,2]<=beltz-0.17)&(spos[:,2]>beltz-0.26)   # front tasset over the groin (tabard)
    elif slot=='helm':
        hb=BH['head'] if 'jaw' in BH else np.r_[np.median(spos[cbn=='head'][:,:2],0),BH['head'][2]]   # v7: Rook/Talia head bones sit 15-19 cm behind the modelled head -> centre on the head's own cells
        if 'jaw' in BH: m=(spos[:,2]>BH['neck'][2]+0.025)&(np.hypot(spos[:,0]-hb[0],spos[:,1]-hb[1])<0.19)
        else: m=(spos[:,2]>BH['neck'][2]-0.01)&(np.hypot(spos[:,0]-hb[0],spos[:,1]-hb[1])<0.23)&~np.char.startswith(cbn.astype(str),'cape')   # v6: rigs without jaw bones carry the face lower/forward   # everything above the neck: face+beard+hair (beard is upperChest-weighted on Darius)
    elif slot=='cloak':
        m=(np.char.startswith(cbn.astype(str),'cape')|(capew>=0.15))&(((spos[:,1]-BH['spine'][1])*FRONT)<0.01)   # back half only (robe skirts on some rigs ride cape bones)
        ctop=spos[m,2].max() if m.any() else neckz; back=((spos[:,1]-BH['spine'][1])*FRONT)<-0.02
        sx=abs(BH['upperArm_L'][0])+0.06
        m|=back&(spos[:,2]>ctop-0.10)&(spos[:,2]<neckz+0.03)&(abs(spos[:,0])<sx)&~np.isin(cbn,['head','jaw'])   # v4: mantle up to the shoulders + collar behind the neck
    R=np.zeros(S,bool); R[tuple(sidx[m].T)]=True; return R
BONESET={'chest':['spine','spine2','chest','upperChest','hips'],'belt':['hips','spine','spine2','thigh_L','thigh_R'],'helm':['head','neck'],'cloak':[b for b in BH if b.startswith('cape')]+['upperChest','chest'],
 'shoulder':lambda X:['upperArm'+X,'shoulder'+X,'upperChest','chest'],'glove':lambda X:['upperArm'+X,'foreArm'+X,'hand'+X]+[f+n+X for f in ('index','middle','ring','pinky','thumb') for n in '123']+['fingers'+X],
 'leg':lambda X:['thigh'+X,'shin'+X,'hips'],'boot':lambda X:['shin'+X,'foot'+X,'toe'+X]}
THK={'chest':2,'shoulder':2,'glove':2,'leg':2,'boot':2,'belt':2,'helm':3,'cloak':4}
TRI={'chest':7000,'helm':7990,'shoulder':5020,'belt':4520,'glove':3540,'leg':4530,'boot':4030,'cloak':4030}
TEX={'chest':512,'helm':512,'cloak':512}
PIECES=[('helm',None),('cloak',None),('chest',None),('belt',None)]+[(s,x) for s in ('shoulder','glove','leg','boot') for x in ('L','R')]
if ROBED: PIECES=[p for p in PIECES if p[0] not in ('chest','leg')]; THK.update(helm=2,shoulder=1,belt=1,glove=1,cloak=1)   # robed casters stay robed: no breastplate/cuisses over the robe

# ---------- v13: reshape -> armour follows a CLEANED silhouette (per-slice ellipse / per-bone tube fits), body hidden under it ----------
OUTG=None
BNG=None
def _bng():
    global BNG
    if BNG is None:
        BNG=np.full(S,'',dtype=object); BNG[tuple(sidx.T)]=cbn
    return BNG
def _smooth(a,w):
    if len(a)<3: return a
    k=np.ones(w)/w; pad=np.pad(a,(w//2,w//2),mode='edge'); return np.convolve(pad,k,mode='valid')[:len(a)]
def fit_torso(R,t,pc):
    X_,Y_,Z_=np.indices(S); q=np.argwhere(R); cx=(0-lo[0])/RES; cy=np.median(q[:,1])
    z0,z1=q[:,2].min(),q[:,2].max(); n=z1-z0+1; xr=np.zeros(n); yf=np.zeros(n); yb=np.zeros(n)
    for k in range(n):
        w=q[abs(q[:,2]-(z0+k))<=2]
        if len(w)<8: continue
        dy=(w[:,1]-cy)*FRONT; xr[k]=np.percentile(abs(w[:,0]-cx),pc)
        yf[k]=np.percentile(dy[dy>0],pc) if (dy>0).sum()>3 else 0; yb[k]=np.percentile(-dy[dy<0],pc) if (dy<0).sum()>3 else 0
    for a_ in (xr,yf,yb):
        nz=np.where(a_>0)[0]
        if len(nz): a_[:]=np.interp(np.arange(n),nz,a_[nz])
        a_[:]=np.maximum(_smooth(a_,9),2)
    if not BELTMODE[0]:   # v28: breastplate rolls in to a gorget at the top (no open-bucket rim)
        k0=int(n*0.80); nr=0.085/RES
        for k in range(k0,n): w_=((k-k0)/max(n-1-k0,1))**1.3; xr[k]=xr[k]*(1-w_)+nr*1.15*w_; yf[k]=yf[k]*(1-w_)+nr*w_; yb[k]=yb[k]*(1-w_)+nr*w_
    if HERO=='rook' and not BELTMODE[0]: xr[:]=np.minimum(xr,0.175/RES); yf[:]=np.minimum(yf,0.13/RES); yb[:]=np.minimum(yb,0.13/RES)   # v29: fitted scale cuirass, no barrel
    if HERO=='rook' and not BELTMODE[0]:
        for k in range(int(n*0.35)): w_=1-k/max(int(n*0.35),1); xr[k]*=1-0.14*w_; yf[k]*=1-0.08*w_; yb[k]*=1-0.08*w_   # v30: waist taper
    if BELTMODE[0]:   # belt/faulds hug the hips: cap the width so coats don't turn it into a lampshade
        cap_=np.percentile(xr,40); xr[:]=np.minimum(xr,cap_*(0.94 if HERO=='rook' else 1.08)); yf[:]=np.minimum(yf,np.percentile(yf,40)*(0.97 if HERO=='rook' else 1.1)); yb[:]=np.minimum(yb,np.percentile(yb,40)*(0.97 if HERO=='rook' else 1.1))
    Zc=np.clip(Z_-z0,0,n-1); dy=(Y_-cy)*FRONT; RX=xr[Zc]; RY=np.where(dy>0,yf[Zc],yb[Zc]); zr=(Z_>=z0)&(Z_<=z1)
    E=lambda T: ((X_-cx)/(RX+T))**2+(dy/(RY+T))**2
    zm=z0+0.55*n if not BELTMODE[0] else z1+1; lam=6; fr=((z1-Z_)%lam)/lam; st=np.where(Z_<zm,fr*((0.7 if HERO in ('orin','finn','elira','wren') else 1.2) if BELTMODE[0] else (0.9 if HERO in ('orin','finn','elira','wren') else 1.8)),0)   # v14: faulds/plackart lames flare at their lower edge
    E2=lambda T: ((X_-cx)/(RX+T+st))**2+(dy/(RY+T+st))**2
    e=E2(0); inside=(e<=1)&zr; shell=(E2(t)<=1)&(e>1)&zr; env=(E(t+(14 if BELTMODE[0] else 10))<=1)&zr
    LAMEM[0]=shell&(Z_<zm)&(fr>0.8); JOINTM[0]=np.zeros(S,bool)
    return shell,inside,env
def fit_limb(R,t,bones,pc,cap=False):
    BN=_bng(); DR=dil(R,15); a=np.maximum(np.argwhere(DR).min(0),0); b=np.minimum(np.argwhere(DR).max(0)+1,S)
    sl=tuple(slice(a[j],b[j]) for j in range(3)); I=np.indices(tuple(b-a)).reshape(3,-1).T+a; P=lo+(I+0.5)*RES
    inside=np.zeros(S,bool); shell=np.zeros(S,bool); env=np.zeros(S,bool); Rb=R&(BN!=''); LAMEM[0]=np.zeros(S,bool); JOINTM[0]=np.zeros(S,bool)
    for bn in bones:
        if bn not in BH: continue
        qb=np.argwhere(Rb&(BN==bn))
        if bn in SYN: qb=np.vstack([qb,SYN[bn]])
        if len(qb)<30: continue
        CH={'thigh':'shin','shin':'foot','upperArm':'foreArm','foreArm':'hand'}; base_,sd_=bn.split('_')[0],bn[len(bn.split('_')[0]):]
        h=BH[bn]
        if base_ in CH and CH[base_]+sd_ in BH: tl=BH[CH[base_]+sd_]
        elif base_=='hand': tl=h+(h-BH['foreArm'+sd_])*0.45
        elif base_ in ('foot','toe'): tl=h+np.array([0,FRONT*0.14,-0.03])
        else: tl=BT[bn]
        d=tl-h; L2=d@d; Lm=np.sqrt(L2)   # v13: axis = joint to child joint (glTF bone tails are arbitrary)
        Q=lo+(qb+0.5)*RES; u=((Q-h)@d)/L2; rq=np.linalg.norm(Q-h-u[:,None]*d,axis=1)
        ok_=(u>-0.25)&(u<1.25)&(rq<0.16); u,rq=u[ok_],rq[ok_]
        if len(u)<30: continue
        u0,u1=np.percentile(u,1),np.percentile(u,99); nb=max(int((u1-u0)*Lm/0.015),1); rf=np.zeros(nb)
        bi=np.clip(((u-u0)/(u1-u0+1e-9)*nb).astype(int),0,nb-1)
        for k in range(nb):
            if (bi==k).sum()>4: rf[k]=np.percentile(rq[bi==k],pc)
        nz=np.where(rf>0)[0]
        if not len(nz): continue
        rf=np.interp(np.arange(nb),nz,rf[nz]); rf=np.minimum(_smooth(rf,3),0.095)   # v29: Rook arm widening undone   # v27: Rook's thick sleeves -> wider rerebrace/pauldron closes the chest-arm gap
        uP=((P-h)@d)/L2; rP=np.linalg.norm(P-h-uP[:,None]*d,axis=1)
        rr=np.interp(np.clip((uP-u0)/(u1-u0+1e-9)*nb-0.5,0,nb-1),np.arange(nb),rf); inr=(uP>=u0)&(uP<=u1)
        lam,amp=LAMEP[0]; fr_=((uP-u0)*Lm%lam)/lam; off=fr_*amp
        T=t*RES; ins=inr&(rP<=rr+off); sh=inr&(rP>rr+off)&(rP<=rr+off+T); lm_=sh&(fr_>0.78)
        jd=abs((uP-u0)*Lm) if bn.startswith(('foreArm','shin')) else np.full(len(uP),9.0); jm_=sh&(jd<0.03)
        for M_,v_ in ((LAMEM[0],lm_),(JOINTM[0],jm_)):
            tmp=np.zeros(tuple(b-a),bool).reshape(-1); tmp[:]=v_; M_[sl]|=tmp.reshape(tuple(b-a))
        ins=ins; en=inr&(rP<=rr+(0.13 if bn.startswith(('thigh','shin')) else 0.06))   # legs: hide skirts/fur flaps too
        if cap:   # pauldron dome over the joint
            c0=h+u0*d; dc=np.linalg.norm(P-c0,axis=1); bc=uP<u0; r0=rf[0]
            ins|=bc&(dc<=r0); sh|=bc&(dc>r0)&(dc<=r0+T); en|=bc&(dc<=r0+0.06)
        for M_,v_ in ((inside,ins),(shell,sh),(env,en)):
            tmp=np.zeros(tuple(b-a),bool).reshape(-1); tmp[:]=v_; M_[sl]|=tmp.reshape(tuple(b-a))
    shell&=~inside
    return shell,inside,env
SYN={}; LAMEM=[None]; JOINTM=[None]; LAMEP=[(0.05,0.012)]; BELTMODE=[False]
FITSET={'chest','belt','shoulder','glove','leg'}   # boots keep the hugging shell (foot axis unreliable)
def _fit(slot): return slot in FITSET and not (ROBED and slot in ('glove','shoulder','belt'))
def fit_piece(slot,side,R,t):
    X='_'+(side or '')
    if slot in ('chest','belt'): return fit_torso(R,t,(82 if HERO=='rook' and slot=='chest' else 84) if not ROBED else 70)   # v22: Rook's coat bulges at the chest sides -> envelope it
    if slot=='shoulder': return fit_limb(R,t,['upperArm'+X],40 if ROBED else (50 if HERO in ('orin','finn','elira','wren') else 60),cap=not ROBED)   # robed: slim mantle, no dome
    if slot=='glove': return fit_limb(R,t,['upperArm'+X,'foreArm'+X,'hand'+X],50 if HERO in ('orin','finn','elira','wren') else 60)
    if slot=='leg': return fit_limb(R,t,['thigh'+X,'shin'+X],47 if HERO in ('orin','finn','elira','wren') else 55)
    if slot=='boot': return fit_limb(R,t,['shin'+X,'foot'+X,'toe'+X],65)
def build_grid(slot,side,r,R):
    out=OUTG if OUTG is not None else globals()['out']
    i=RARITIES.index(r); p=A.pal(FAM,r); t=THK[slot]+(1 if slot=='shoulder' and i>=3 else 0)
    if ROBED and slot!='helm':
        nb=np.zeros(S,np.int8)
        for ax in range(3):
            for d in (1,-1): nb+=np.roll(R,d,ax)
        R=R&(nb>=3)   # v6: drop 1-voxel spurs -> no blobby edges on robed sets
    if slot=='boot' and not ROBED:
        h_=BH['shin_'+side]; f_=BH['foot_'+side]; I_=np.indices(S).reshape(3,-1).T; Pw=lo+(I_+0.5)*RES; d_=f_-h_; uu=((Pw-h_)@d_)/(d_@d_)
        rr_=np.linalg.norm(Pw-h_-uu[:,None]*d_,axis=1); cyl=((uu>0.2)&(uu<1.05)&(rr_<0.065)).reshape(S)
        fq=sidx[cbn=='foot_'+side]
        if len(fq): fc=lo+(np.median(fq,0)+0.5)*RES; d2=fc-f_; u2=((Pw-f_)@d2)/max(d2@d2,1e-6); r2=np.linalg.norm(Pw-f_-u2[:,None]*d2,axis=1); cyl|=((u2>-0.2)&(u2<1.0)&(r2<0.075)).reshape(S)   # ankle bridge to the foot (Rook's feet sit forward)
        R=R|cyl; print("BOOTCYL",side,int(cyl.sum()),flush=True)
        out=out|(solid&~dil(R,1))   # v17: coat wraps the shins (Rook) -> no air next to them; let the greave grow through the hidden coat
    CAPE=None
    if slot=='leg' and not ROBED:   # v19: thigh core (coat-wrapped thighs give the cuisse no cells near the hip)
        h_=BH['thigh_'+side]; d_=BH['shin_'+side]-h_; I_=np.indices(S).reshape(3,-1).T; Pw=lo+(I_+0.5)*RES; uu=((Pw-h_)@d_)/(d_@d_)
        cyl=((uu>-0.05)&(uu<0.9)&(np.linalg.norm(Pw-h_-uu[:,None]*d_,axis=1)<0.075)).reshape(S); SYN['thigh_'+side]=np.argwhere(cyl)
    if ROBED and slot=='shoulder':   # v17 pelerine: a thin conical cape sheet hanging from the neck over the shoulder (not a shell around the arm)
        X_,Y_,Z_=np.indices(S); vz=lambda z:(z-lo[2])/RES; sg=np.sign(BH['upperArm_'+side][0]); cx=(0-lo[0])/RES
        tc=np.isin(cbn,['chest','upperChest','spine2']); cy=np.median(sidx[tc][:,1]) if tc.any() else np.median(sidx[:,1])
        zt=vz(BH['neck'][2]+0.04); zs=vz(BH['upperArm_'+side][2]-0.01); zb=zs-0.24/RES
        sel=tc&(abs(spos[:,2]-BH['upperArm_'+side][2])<0.05); dyv=(sidx[sel][:,1]-cy)*FRONT if sel.any() else np.array([4.,-4.])
        rxs=abs(BH['upperArm_'+side][0])/RES+(0.11 if HERO=='talia' else 0.08)/RES; ryf=np.percentile(dyv[dyv>0],95)+0.04/RES if (dyv>0).any() else 6; ryb=min(np.percentile(-dyv[dyv<0],95)+0.04/RES,0.17/RES) if (dyv<0).any() else 6; ryf=min(ryf,0.15/RES)
        u=np.clip((zt-Z_)/max(zt-zb,1),0,1)**0.55*1.12; r0=0.085/RES   # v30: one continuous curved drape (no box corner) # r0=0.085/RES   # v17: steep shoulder slope, then hangs nearly straight down; r0=0.075/RES
        rx=r0+(rxs-r0)*u; dy=(Y_-cy)*FRONT; ry=r0+(np.where(dy>0,ryf,ryb)-r0)*u
        ee=np.sqrt(((X_-cx)/rx)**2+(dy/ry)**2); band=(Z_<=zt)&(Z_>=zb+4*np.clip((Y_-cy)*FRONT/max(ryf,1),0,1))&((X_-cx)*sg>=0)   # v30: hem curves up at the front
        CAPE=band&(ee>=1)&(ee<=1+1.6/np.minimum(rx,ry)); INS=(band&(ee<1))|((Z_<=zt+10)&(Z_>=zb-3)&((X_-cx)*sg>=0)&(ee<1.9))   # v19: also hide specks just outside the sheet
        Zd=Z_; ang_=np.arctan2(dy,(X_-cx)*sg); CAPE&=~((Zd<=zb+3)&((np.floor(ang_*9)%2)==0))   # dagged hem (teeth around the rim)
        txh=abs(BH['upperArm_'+side][0])-0.02
        xw_=lo[0]+(X_+0.5)*RES; zw_=lo[2]+(Z_+0.5)*RES
        DRP=solid&(abs(xw_)>txh-0.12)&(xw_*sg>0)&(zw_>BH['foot_'+side][2]+0.05)&(zw_<BH['upperArm_'+side][2]-0.04)&~np.isin(_bng(),(['hand_'+side] if BH['hand_'+side][2]>BH['upperArm_'+side][2]-0.15 else ['foreArm_'+side,'hand_'+side]))   # sleeve drapes (T-pose arms: forearm drapes too) hanging below the T-pose arms
        print('CAPE',side,int(CAPE.sum()),int(INS.sum()),int(DRP.sum()),round(zt,1),round(zs,1),round(rxs,1),round(ryf,1),round(ryb,1),flush=True)
        hd=np.linalg.norm(spos-BH['hand_'+side],axis=1); fa=np.isin(cbn,['hand_'+side])&((hd>0.085)|(spos[:,2]<BH['hand_'+side][2]-0.05))   # v22: loose bits skinned to the hand far from it (Talia elbow/hip specks)
        fl_=(spos[:,0]*sg>0.06)&(abs(spos[:,0])<abs(BH['upperArm_'+side][0])+0.14)&(spos[:,2]>BH['upperArm_'+side][2]-0.04)&(spos[:,2]<BH['neck'][2]+0.12)&~np.isin(cbn,['head','neck','jaw'])&~np.array([n.startswith(('hand','fore')) for n in cbn])   # v25: collar/pauldron flares poking above the cape (Rowan red bits)
        fa=fa|fl_
        ad=BH['hand_'+side]-BH['upperArm_'+side]
        if abs(ad[2])/np.linalg.norm(ad)<0.6:   # v26: near-horizontal arms (Talia): sleeve tips hanging below the forearm line
            a0=BH['foreArm_'+side]; dd=BH['hand_'+side]-a0; uq=((spos-a0)@dd)/(dd@dd); zl=a0[2]+np.clip(uq,0,1)*dd[2]
            fa=fa|(np.isin(cbn,['foreArm_'+side,'upperArm_'+side])&(spos[:,2]<zl-0.02)&(uq>-0.6))
        FAR=np.zeros(S,bool); FAR[tuple(sidx[fa].T)]=True
        masks[name]={'cells':np.ravel_multi_index(np.argwhere((INS|dil(CAPE,1)|DRP|dil(FAR,1))&solid).T,S).tolist()}
    if ROBED and slot=='belt':   # v29: full slim robe (bodice + gently flared draped skirt) replaces the bulbous body robe
        X_,Y_,Z_=np.indices(S); vz=lambda z:(z-lo[2])/RES; cx=(0-lo[0])/RES
        tb=np.isin(cbn,['spine','spine2','chest','upperChest','hips']); cy=np.median(sidx[tb][:,1])
        zt=vz(BH['neck'][2]-0.01); zw=vz(beltz); zf=vz(BH['foot_L'][2]+0.02); za=vz(BH['upperArm_L'][2])
        def wr(z):   # half widths (vox) at height z
            if z>=za: k=np.clip((z-za)/max(zt-za,1),0,1); return (0.15-0.07*k)/RES,(0.115-0.04*k)/RES
            if z>=zw: k=(za-z)/max(za-zw,1); return (0.15-0.02*k)/RES,(0.115-0.01*k)/RES
            k=(zw-z)/max(zw-zf,1); return (0.13+0.08*k**1.2)/RES,(0.105+0.05*k**1.2)/RES
        tz=np.arange(S[2]); RXz=np.array([wr(z)[0] for z in tz]); RYz=np.array([wr(z)[1] for z in tz])
        dy=(Y_-cy)*FRONT; ang_=np.arctan2(dy,X_-cx); kz=np.clip((zw-Z_)/max(zw-zf,1),0,1)
        fold=1+0.07*kz*np.sin(ang_*10+kz*2.5); dy=dy+kz**2*(0.035/RES)   # v30: sway - folds twist and the hem trails back   # drape folds deepen toward the hem
        ee=np.sqrt(((X_-cx)/(RXz[Z_]*fold))**2+(dy/(RYz[Z_]*fold))**2); band=(Z_<=zt)&(Z_>=zf)
        CAPE=band&(ee>=1)&(ee<=1+1.7/np.minimum(RXz[Z_],RYz[Z_]));
        keep=np.isin(_bng(),['head','neck','jaw','eye_L','eye_R']+[b+s_ for b in ('upperArm','foreArm','hand','fingers','thumb1','thumb2','thumb3','index1','index2','index3','middle1','middle2','middle3','ring1','ring2','ring3','pinky1','pinky2','pinky3') for s_ in ('_L','_R')])
        xw_=lo[0]+(X_+0.5)*RES
        HID=solid&(Z_>=zf-1)&(Z_<=zt)&((~keep)|(ee<1.15))&(abs(xw_)<0.55)
        def _sd(P,a_,b_): d_=BH[b_]-BH[a_]; u_=np.clip(((P-BH[a_])@d_)/(d_@d_),0,1); return np.linalg.norm(P-BH[a_]-u_[:,None]*d_,axis=1)
        sl_=np.zeros(len(spos),bool)
        for s_ in ('_L','_R'):   # v30: sleeve/robe chunks hanging off the arm below the shoulder
            dd_=np.minimum(_sd(spos,'upperArm'+s_,'foreArm'+s_),_sd(spos,'foreArm'+s_,'hand'+s_)); sl_|=(dd_>0.075)&(spos[:,2]<BH['upperArm'+s_][2]-0.03)&~np.isin(cbn,['head','neck','jaw'])
        SLV=np.zeros(S,bool); SLV[tuple(sidx[sl_].T)]=True; HID|=SLV
        masks[name]={'cells':np.ravel_multi_index(np.argwhere(HID|(dil(CAPE,1)&solid)).T,S).tolist()}
        print('ROBE',int(CAPE.sum()),int(HID.sum()),flush=True)
    layers=[R]; acc=R.copy()
    for k in range(t):
        nx=dil(acc)&out&~acc; layers.append(nx); acc|=nx
    shell=acc&out
    if CAPE is not None: shell=CAPE.copy(); R=CAPE&False|R
    if (slot=='boot' and HERO=='rook'):   # v20: smooth the boot (close pin-holes/lumps), drop loose voxels behind the heel
        shell=close(shell,2)&out; op=dil(ero(shell,1),1)&shell; shell=op if op.sum()>0.6*shell.sum() else shell   # opening drops 1-voxel strays
        HEM=np.zeros(S,bool); sgf=np.sign(BH['foot_'+side][0]); hq=(np.isin(cbn,['foot_'+side,'toe_'+side])&(spos[:,2]<BH['foot_'+side][2]+0.18))|((spos[:,2]<BH['shin_'+side][2]-0.02)&(spos[:,0]*sgf>-0.01)&~np.isin(cbn,['hand_L','hand_R','foreArm_L','foreArm_R']));   # v30: whole coat hem + claw bits below the knee on this side HEM[tuple(sidx[hq].T)]=True   # v21: coat hem on the ground skinned to the foot
        masks[name]={'cells':np.ravel_multi_index(np.argwhere((dil(R,3)|dil(HEM,3))&solid).T,S).tolist()}
    if _fit(slot):   # v13 reshape (robed cuffs/mantles keep the draped shell)
        if slot=='chest':   # v20: hide the coat under the arms at the chest sides (Rook)
            xw_=lo[0]+(np.indices(S)[0]+0.5)*RES; zw_=lo[2]+(np.indices(S)[2]+0.5)*RES; ax_=abs(BH['upperArm_L'][0])
            CSIDE=solid&(abs(xw_)<ax_+0.06)&(zw_>beltz-0.02)&(zw_<BH['upperArm_L'][2]-0.03)&~(np.isin(_bng(),['upperArm_L','upperArm_R','foreArm_L','foreArm_R','hand_L','hand_R'])&~((abs(xw_)<ax_+(0.07 if HERO=='rook' else 0.02))&(zw_<BH['upperArm_L'][2]-(0.02 if HERO=='rook' else 0.08))&np.isin(_bng(),['upperArm_L','upperArm_R']+(['foreArm_L','foreArm_R'] if HERO=='rook' else []))))   # v21: under-arm sleeve hang hidden (arm is armoured)
            CSIDE|=solid&np.isin(_bng(),['shoulder_L','shoulder_R'])&(abs(xw_)<ax_+0.02)&(zw_<BH['upperArm_L'][2]-0.05)&(zw_>beltz-0.02)
        LAMEP[0]=({'shoulder':(0.032,0.011),'glove':(0.045,0.005),'leg':(0.05,0.005)} if HERO in ('orin','finn','elira','wren') else {'shoulder':(0.032,0.022),'glove':(0.045,0.010),'leg':(0.05,0.011)}).get(slot,(0.05,0.012)); BELTMODE[0]=(slot=='belt')
        shell,fin,fenv=fit_piece(slot,side,R,t); layers=[R,shell]; acc=shell|fin; print('FIT',slot,side,int(R.sum()),int(shell.sum()),int(fin.sum()),flush=True)
        if slot=='leg':   # v13: hide skirts/coats hanging around the legs on this side (Rook/Wren/Finn broad silhouettes) down to mid-shin
            Xg,Yg,Zg=np.indices(S); xw=lo[0]+(Xg+0.5)*RES; zw=lo[2]+(Zg+0.5)*RES; sg=np.sign(BH['thigh'+'_'+side][0])
            zlo=BH['foot_'+side][2]+0.02; zhi=beltz+0.02
            fenv=fenv|((zw>zlo)&(zw<zhi)&(abs(xw)<0.75)&(xw*sg>-0.01))
        if slot in ('glove','shoulder'): fenv=fenv|dil(R,3)
        if slot=='glove':   # v17: coat sleeve cuffs hanging off the elbow/forearm (Rook)
            I_=np.indices(S).reshape(3,-1).T; Pw=lo+(I_+0.5)*RES; cm=np.zeros(len(Pw),bool)
            for a_,b_ in (('upperArm_'+side,'foreArm_'+side),('foreArm_'+side,'hand_'+side)):
                if a_ in BH and b_ in BH:
                    h_=BH[a_]; d_=BH[b_]-h_; uu=((Pw-h_)@d_)/(d_@d_); cm|=(uu>0.3)&(uu<1.1)&(np.linalg.norm(Pw-h_-uu[:,None]*d_,axis=1)<0.16)
            fenv=fenv|(cm.reshape(S)&~np.isin(_bng(),['chest','upperChest','spine','spine2','hips','head','neck']))   # v15: stray coat bits near the hands
        if slot=='chest': fenv=fenv|CSIDE; shell=shell|(dil(CSIDE&~fin,1)&~fin&dil(shell|fin,3)&(solid|out))|((CSIDE&~fin) if HERO=='rook' else False)   # v25: Rook: solid inner liner on the arm side   # v22: armour closes over the under-arm gap (no body/inner wall visible)
        masks[name]={'cells':np.ravel_multi_index(np.argwhere((fenv|fin|dil(R,1))&solid).T,S).tolist()}
        out=~fin
    if slot=='helm':   # v8: skull-fitted helm (egg/dome profile, not a cylinder): great helm (plate/leather), bascinet+aventail (chain/scale), cowl (robed)
        X_,Y_,Z_=np.indices(S); qa=np.argwhere(R)
        sk_=np.zeros(S,bool); sel=np.isin(cbn,['head','jaw','eye_L','eye_R']); sk_[tuple(sidx[sel].T)]=True; q=np.argwhere(sk_&R)
        if len(q)<200: q=qa
        cx_=(0-lo[0])/RES; cy_=np.median(q[:,1]); zb=qa[:,2].min(); zt=np.percentile(q[:,2],99.5); Hh=zt-zb
        fy=(q[:,1]-cy_)*FRONT; up=q[:,2]>zb+0.35*Hh; PC=97
        if np.percentile(abs(q[up,0]-cx_),97)*RES>0.12: PC=84   # v9: very wide heads (Rook) -> snug fit, overflow hidden by the mask
        ax=np.percentile(abs(q[up,0]-cx_),PC)+1.0; bf=np.percentile(fy[up&(fy>0)],PC)+1.0; bb=np.percentile(-fy[up&(fy<0)],PC)+1.0
        STY='cowl' if ROBED else ('basc' if FAM in ('chain','scale') else 'great')
        zs=zb+0.52*Hh; Hd=zt-zs+1.5
        zbot={'great':zb-1,'basc':zb-1,'cowl':zb-2}[STY]   # v12: bascinet closes to the chin with a snout visor
        def prof(T):   # radius scale per height + backward lean of the crown (bascinet point)
            U=(Z_-zs)/(Hd+T); Lw=np.clip((zs-Z_)/max(zs-zb,1),0,1.5)
            if STY=='basc': f=np.where(U>0,np.clip(1-U,0,1)**0.62*(1-0.25*U*U),1-0.10*Lw); lean=np.clip(U,0,1)*0.45*bb
            elif STY=='cowl': f=np.where(U>0,np.sqrt(np.clip(1-U**2.2,0,1)),1+0.12*Lw**1.5); lean=np.clip(U,0,1)*0.35*bb
            else: f=np.where(U>0,np.sqrt(np.clip(1-U**2.4,0,1)),1-0.08*Lw); lean=np.clip(U,0,1)*0.10*bb
            return f,lean
        def ell(T):
            f,lean=prof(T); dy=(Y_-cy_)*FRONT+lean; ry=np.where(dy>0,bf,bb)+T
            return ((X_-cx_)/np.maximum((ax+T)*f,0.3))**2+(dy/np.maximum(ry*f,0.3))**2
        e=ell(0); eo=ell(t)
        inside=(e<=1)&(Z_>=zbot); wall=(eo<=1)&(e>1)&(Z_>=zbot)
        shell=wall.copy(); HZ=(int(zbot),int(zt)); HG=dict(cx=cx_,cy=cy_,zs=zs,zb=zb,zt=zt,ax=ax,bf=bf,bb=bb,STY=STY,e=e,eo=eo)
        if STY=='basc':   # mail aventail: curtain from the helm rim to the shoulders, flaring out
            zr=int(zbot); za=int(round((BH['neck'][2]-0.05-lo[2])/RES)); fl=np.clip((zr-Z_)/max(zr-za,1),0,1)
            dy=(Y_-cy_)*FRONT; ry=np.where(dy>0,bf,bb)
            ea=((X_-cx_)/(ax+1+3*fl))**2+(dy/(ry+1+3*fl))**2; eai=((X_-cx_)/(ax-1+3*fl))**2+(dy/(ry-1+3*fl))**2
            av=(ea<=1)&(eai>1)&(Z_<zr)&(Z_>=za)&out; shell|=av; HG['av']=av; inside|=(eai<=1)&(Z_<zr)&(Z_>=za)
        if STY=='great':   # v12 gorget: two thin lames from the helm rim down to the collar
            zr=int(zbot); za=int(round((BH['neck'][2]-0.04-lo[2])/RES)); dy=(Y_-cy_)*FRONT; ry=np.where(dy>0,bf,bb)
            go=(((X_-cx_)/(ax+t+1))**2+(dy/(ry+t+1))**2<=1)&(((X_-cx_)/(ax+1))**2+(dy/(ry+1))**2>1)&(Z_<zr)&(Z_>=za)
            shell|=go; HG['go']=go
        R=R|(inside&skin)
        hg_=np.isin(cbn,['head','neck','jaw','eye_L','eye_R','chest','upperChest','spine2'])|np.char.startswith(cbn.astype(str),'hair')
        hg_&=spos[:,2]>BH['neck'][2]-0.02; HGM=np.zeros(S,bool); HGM[tuple(sidx[hg_].T)]=True   # v11: hide gear riding above the neck (Rook's beige back gear)
        HGM=dil(HGM,1)&solid&~((ell(t+9)>1)&(Z_<zbot-8)&False)
        masks[name]={'cells':np.ravel_multi_index(np.argwhere((HGM|(ell(t+9)<=1)&(Z_>=zbot-(3 if ROBED else 8))|inside|dil(R,3))&solid).T,S).tolist()}   # hide every body cell inside the helm envelope   # v7: hide every body cell inside the helm envelope (faces under helm/hood)
    if slot=='cloak': shell=close((layers[-1]|layers[-2]),1)&out   # cloak floats just outside the plate; close() fills pin-holes (Darius back speck)
    if slot not in ('cloak','helm') and not _fit(slot) and not ROBED: shell=close(shell,1)&out&dil(R,t)   # v10: fill pin-holes only within the armour's own thickness of the body (no bridging bulk)             # v3: fill the body's voxel lumps -> smooth plate surface, real thickness kept
    outer=shell&dil(out&~shell)
    Rin=R&~dil(skin&~R,2); core=dil(Rin,t+1)&shell; trim=shell&~core
    if (slot=='boot' and HERO=='rook'): zq_=np.argwhere(shell)[:,2]; trim=shell&(np.indices(S)[2]>=zq_.max()-1)   # v20: clean rim band only at the boot top
    if _fit(slot): zq=np.argwhere(shell)[:,2]; trim=shell&((np.indices(S)[2]<=zq.min()+1)|(np.indices(S)[2]>=zq.max()-1))   # v13: rolled edge = top/bottom band of the fitted piece
    if slot=='helm': trim=np.zeros(S,bool)
    if ROBED and slot not in ('helm','cloak'): zz_=np.argwhere(shell)[:,2]; trim=shell&(np.indices(S)[2]<=zz_.min()+(1 if slot=='belt' else 0))
    FOLD=ROBED and slot in ('belt','shoulder')   # v16 vertical drape folds   # v9: robed: gold only on the hem, no edge blotches
    if ROBED and slot=='shoulder' and CAPE is None:   # v14 draped mantle: dagged (scalloped) lower edge
        Xd,Yd,Zd=np.indices(S); zq=np.argwhere(shell)[:,2]; zb_=zq.min()
        zq=np.argwhere(shell)[:,2]; zb_=zq.min()
        shell&=~((Zd<=zb_+3)&(((Xd//3)+(Yd//3))%2==0))
    g=np.zeros(S,np.int16); v=V(1); v.g=g; KEEP=np.zeros(S,bool); AV=HG['av'] if slot=='helm' and 'av' in HG else np.zeros(S,bool)
    base=p['leather'] if FAM=='leather' else A.PAL[r].get('cloth',p['metal']) if ROBED else p['metal']   # robed: rarity cloth colour, not the white robe
    metal=v.c(base); dark=v.c(tuple(c*0.62 for c in base)); tr=v.c(p['trim'] if i>=2 else p['edge'])
    g[shell]=metal
    if FOLD and not (slot=='belt' and CAPE is not None): g[shell&((X_f:=np.indices(S)[0])%4==0)]=dark
    if ROBED and slot=='belt' and CAPE is not None:
        Zs=np.indices(S)[2]; zwv=int(round((beltz-lo[2])/RES))
        Xs=np.indices(S)[0]; g[shell&(Zs<zwv)&((Xs%5)==0)]=dark   # fold shadows on the skirt
        sash=v.c(tuple(c*0.45 for c in base)); g[shell&(abs(Zs-zwv)<=2)]=sash
        if i>=2: g[shell&(abs(Zs-zwv)==3)]=tr   # gold sash edge only
    if _fit(slot):   # v14: lame lips dark + rivets, mail at elbows/knees, chest emblem (named-piece look)
        X1,Y1,Z1=np.indices(S); lm=LAMEM[0]&shell; g[lm]=dark; g[lm&((X1+Y1)%8==0)&((Z1%3)==0)]=v.c(p['edge'] if i<4 else p['trim'])
        jm=JOINTM[0]&shell&~lm; g[jm]=v.c(tuple(min(1,c*1.3) for c in base)); g[jm&(((X1+Y1+Z1)%2)==0)]=v.c(tuple(c*0.5 for c in base))
        if slot=='chest':
            cxx=int(round((0-lo[0])/RES)); fz=np.argwhere(shell)[:,2]; ez=int(fz.min()+0.72*(fz.max()-fz.min()))
            fr_=shell&((Y1-np.median(np.argwhere(shell)[:,1]))*FRONT>0)
            em=fr_&((X1-cxx)**2+(Z1-ez)**2<=3.2**2); emo=dil(em)&~shell&~fin&((X1-cxx)**2+(Z1-ez)**2<=3.2**2)&dil(fr_,1)
            g[em]=tr if i>=1 else v.c(p['edge']); g[emo]=tr if i>=1 else v.c(p['edge']); shell|=emo   # raised boss/emblem
            g[emo&((X1-cxx)**2+(Z1-ez)**2<=1.2**2)]=v.c((0.9,0.25,0.05) if i==5 else (0.55,0.08,0.08)) if i>=3 else metal   # jewel
    X_,Y_,Z_=np.indices(S)
    if slot=='cloak':
        cl=A.PAL[r].get('cloth',(0.30,0.06,0.06)); g[shell]=v.c(cl); g[shell&(Z_%5==0)]=v.c(tuple(c*0.8 for c in cl))
        zb=np.argwhere(shell)[:,2].min()
        if i>=2: g[shell&(Z_<=zb+1)]=tr   # v4: gold hem only (no trim blobs inside the cloak)
        idx=np.argwhere(g>0); a=idx.min(0)-1; b=idx.max(0)+2
        vv=V(1); vv.pal=v.pal; vv.g=g[a[0]:b[0],a[1]:b[1],a[2]:b[2]].copy(); return vv,lo+a*RES
    if slot=='helm':   # v8 features: recessed eye slits, face plate keel + breaths, brow band, riveted rim, comb crest, horns
        H_=HG; cx=int(round(H_['cx'])); STY=H_['STY']; blk=v.c((0.03,0.03,0.03)); edge=v.c(p['edge'])
        ext=H_['eo']>1; outer=shell&dil(ext&~shell); fy=(Y_-H_['cy'])*FRONT; front=fy>0.45*H_['bf']
        if STY=='basc': g[H_['av']]=v.c(tuple(c*0.85 for c in base))
        ze=int(round((np.mean([BH['eye_L'][2],BH['eye_R'][2]])-lo[2])/RES)) if 'eye_L' in BH else int(round(H_['zb']+0.56*(H_['zt']-H_['zb'])))
        if STY=='cowl':   # open hood: face opening + black shadow, pointed back, mantle collar
            zo=(HZ[0]+2+ze+6)/2; fo=shell&front&((((X_-cx)/(H_['ax']*0.62))**2+((Z_-zo)/((ze+6-HZ[0]-2)/2))**2)<=1); shell&=~fo; g[fo]=0   # oval face opening
            sh_=dil(fo,3)&(H_['e']<=1)&(fy>0.2*H_['bf'])&(Z_<=ze+6); g[sh_]=v.c((0.02,0.02,0.025)); shell|=sh_
            g[shell&dil(fo,2)&~sh_&~dil(ext,1)]=v.c((0.02,0.02,0.025)); KEEP|=sh_|(shell&dil(fo,2)&~dil(ext,1)); lip=dil(fo,1)&shell&~sh_&dil(ext,1); g[lip]=tr if i>=2 else dark   # inner wall around the opening in shadow, lip only on the outer edge
            tip=(fy<-0.6*H_['bb'])&(abs(X_-cx)<=1)&(Z_>=H_['zt']-3)&(Z_<=H_['zt']+2)&dil(shell,2)&ext; g[tip]=metal; shell|=tip
        else:
            sw=H_['ax']*(0.78 if STY=='great' else 0.70)
            slit=shell&front&(abs(Z_-ze)<=1)&(abs(X_-cx)>=2)&(abs(X_-cx)<=sw)
            g[slit]=blk; KEEP|=slit; so=slit&outer; shell&=~so; g[so]=0   # recessed: outer layer cut, black liner behind
            band=outer&(abs(Z_-(ze+3))<=1); bump=dil(band)&ext&~shell&(abs(Z_-(ze+3))<=1); g[bump]=tr if i>=2 else metal; shell|=bump   # raised brow band
            g[dil(slit,1)&outer&(Z_<ze-1)&(Z_>=ze-2)]=edge   # bright lower lip
            kl=outer&front&(abs(X_-cx)<=1)&(Z_<ze-1); kb=dil(kl)&ext&~shell&(abs(X_-cx)<=0)&(Z_<ze-1)&(Z_>=HZ[0]); g[kb]=tr if i>=2 else metal; shell|=kb   # face keel
            if STY=='basc':   # v12 pig-faced snout: visor pushed forward below the slit, tapering to a point
                for k_ in range(1,4):
                    sn=dil(outer&front&(Z_<ze-1)&(Z_>HZ[0]+2)&(abs(X_-cx)<=H_['ax']*(0.55-0.12*k_)),1)&ext&~shell&(Z_<ze-1)&(Z_>HZ[0]+2)&(abs(X_-cx)<=H_['ax']*(0.55-0.12*k_)); g[sn]=metal; shell|=sn; ext=ext&~sn; outer=shell&dil(ext&~shell)
                g[outer&front&(Z_<ze-2)&((Z_%2)==0)&((X_%2)==0)&(abs(X_-cx)>=2)&(abs(X_-cx)<=H_['ax']*0.4)]=blk
            if STY=='great' and i>=1:   # breaths: rows of black holes on the right cheek of the face plate
                br=outer&front&(Z_<ze-3)&(Z_>HZ[0]+3)&((X_-cx)*1>=3)&((X_-cx)<=H_['ax']*0.65)&((Z_%3)==0)&((X_%2)==0); g[br]=blk
            rim=outer&(Z_<=HZ[0]+1)&~(H_.get('av',np.zeros(S,bool))); rr=dil(rim)&ext&~shell&(Z_<=HZ[0]+1); g[rr]=tr if i>=2 else dark; shell|=rr
            g[rr&((X_+Y_)%4==0)]=edge   # rivets on the rim
            g[band&((X_+Y_)%5==0)]=edge
        top=int(np.argwhere(shell)[:,2].max())
        HSTY={'darius':('comb','up'),'orin':('plume','wing'),'rook':('none','ram'),'finn':('spike','none'),'elira':('comb','wing'),'wren':('crown','none'),'rowan':('tip',None),'talia':('diadem',None)}.get(HERO,('comb','up'))   # v15: unique silhouette per hero
        def stamp(x,y,z,r,col):
            R_=int(np.ceil(r))
            for dx in range(-R_,R_+1):
                for dy in range(-R_,R_+1):
                    for dz in range(-R_,R_+1):
                        if dx*dx+dy*dy+dz*dz<=r*r:
                            for xx in ((x+dx,int(round(2*cx-(x+dx)))) if x!=cx else (x+dx,)):
                                q=(xx,int(y+dy),int(z+dz))
                                if all(0<=q[j]<S[j] for j in range(3)) and not shell[q]: g[q]=col; shell[q]=True
        cr_,hn_=HSTY; hc=v.c((0.88,0.84,0.74) if i<5 else (0.10,0.08,0.08)); cy=int(round(H_['cy']))
        if STY!='cowl' and i>=2:
            if cr_ in ('comb','plume'):
                ch=2+(i-2)+(4 if cr_=='plume' else 0)
                cr=(abs(X_-cx)<=(1 if cr_=='plume' else 0))&(Z_>top-6)&(Z_<=top+ch)&ext&dil(shell&(Z_>=top-6),ch+1)&(fy>-(1.4 if cr_=='plume' else 0.9)*H_['bb'])&(fy<0.8*H_['bf'])
                g[cr]=tr if cr_=='comb' else v.c(A.PAL[r].get('cloth',(0.55,0.08,0.08))); shell|=cr
                if cr_=='plume':   # plume falls down the back
                    for k in range(10): stamp(cx,cy-FRONT*(H_['bb']+k*0.6),top+ch-k*1.2,1.6,v.c(A.PAL[r].get('cloth',(0.55,0.08,0.08))))
            elif cr_=='spike':
                ap=np.argwhere(shell&(Z_==top)).mean(0).astype(int)
                L_=20+2*i
                for k in range(L_): stamp(int(ap[0]),int(ap[1]),top-2+k,2.4-1.0*k/L_,metal if k<L_*0.6 else tr)   # thick tapered shaft
                stamp(int(ap[0]),int(ap[1]),top,3.4,tr); stamp(int(ap[0]),int(ap[1]),top+L_,3.0,tr)   # collar + gold ball finial
                stamp(int(ap[0]),int(ap[1]),top+int(L_*0.55),2.6,v.c((0.55,0.08,0.08)) if i<5 else v.c((0.9,0.3,0.05)))   # jewel knop
            elif cr_=='crown':   # circlet of spikes around the crown
                zc=top-4; pts=np.argwhere(outer[:,:,zc]) if 0<=zc<S[2] else np.zeros((0,2),int)
                if len(pts):
                    ang=np.arctan2(pts[:,1]-cy,pts[:,0]-cx)
                    for a_ in np.linspace(-np.pi,np.pi,9)[:-1]:
                        q=pts[np.argmin(abs(np.angle(np.exp(1j*(ang-a_)))))]
                        for k in range(3+i): stamp(int(q[0]),q[1],zc+k,max(0.5,1.5-k*0.15),tr)
        if STY!='cowl' and i>=(2 if hn_=='wing' else 3) and hn_!='none':
            zh=int(H_['zs']+0.35*(H_['zt']-H_['zs'])); ys=int(round(H_['cy']-FRONT*0.1*H_['bb']))
            xs=np.where(shell[:,ys,zh])[0]; x0=xs.max() if len(xs) else cx+10
            for k in range(16):
                if hn_=='up': stamp(x0-1+int(k*0.8),ys,zh+int(k**1.45/3.0),max(0.6,2.6-k*0.13),hc if k<13 else tr)
                elif hn_=='ram':   # curls back and down beside the cheek
                    a_=k*0.45; stamp(x0+1+int(k*0.6),ys-FRONT*7*(1-np.cos(a_)),zh+3+7*np.sin(a_)-k*0.2,max(1.0,3.4-k*0.14),hc if k<14 else tr)
                elif hn_=='wing':   # swept-back fin
                    if k<15:
                        for zz in range(0,max(1,15-k)): stamp(x0+int(k*0.75),ys-FRONT*int(k*0.8),zh-2+zz+int(k*0.6),0.9,tr if zz>=9-k or i>=4 and zz%3==0 else metal)
        if STY=='cowl' and i>=2:
            if cr_=='tip':   # tall pointed hood tip falling back
                for k in range(6+i): stamp(cx,cy-FRONT*(0.6*H_['bb']+k*0.7),H_['zt']+2-k*0.3+min(k,4)*0.8,max(0.8,2.2-k*0.12),metal)
            else:   # diadem across the brow with a jewel
                db=outer&front&(abs(Z_-(ze+7))<=0)&(abs(X_-cx)<=H_['ax']*0.8); g[db]=tr; KEEP&=~db
                stamp(cx,int(round(H_['cy']+FRONT*H_['bf']))+FRONT,ze+7,1.4,v.c((0.9,0.25,0.05) if i==5 else (0.15,0.35,0.85)))
    rows=None
    if slot in('chest','leg','shoulder','glove','boot'):
        if slot in('leg','glove'):   # leather straps on the back
            st=outer&((Y_-np.median(np.argwhere(R)[:,1]))*FRONT<0)&((Z_%11)<=1); g[st]=v.c((0.24,0.15,0.09)); g[st&((X_%4)==0)&((Z_%11)==0)]=v.c(p['edge'])
        per={'chest':18,'leg':16,'shoulder':7,'glove':14,'boot':15}[slot]; rows=(Z_%per==0)
        if slot=='shoulder':
            ridge=dil(outer&rows)&out&~shell&dil(shell)
            pass   # v12: no raised ridges (grooves only)
        if i>=1: g[outer&rows]=dark
    if slot=='chest' and i>=2:
        cx=int(round((0-lo[0])/RES)); keel=outer&(abs(X_-cx)<=1)&(np.sign(Y_-np.median(np.argwhere(R)[:,1]))==FRONT)
        k2=dil(keel)&out&~shell&dil(shell); g[k2]=tr; shell|=k2
    if slot=='shoulder' and not ROBED:   # v7: robed mantles stay flat (no flare/spikes)
        top=np.argwhere(shell)[:,2].max()
        if i>=3:
            fl=dil(outer&(Z_>=top-2))&out&~shell; g[fl]=tr; shell|=fl
        if i==5:   # masterwork spikes
            cand=np.argwhere(outer&(Z_>=top-1)); rng=np.random.default_rng(7)
            for q in cand[rng.choice(len(cand),min(3,len(cand)),replace=False)]:
                for k in range(1,8):
                    for dx in range(-max(0,2-k//3),max(0,2-k//3)+1):
                        x,y,z=q[0]+dx,q[1],q[2]+k
                        if z<S[2] and out[x,y,z]: g[x,y,z]=v.c((0.10,0.08,0.08)) if k<6 else tr; shell[x,y,z]=True
    if slot!='helm' and not ROBED:   # v8: real layering -> overlapping lames, raised rivets, couters/poleyns, raised straps
        ext=~shell; outer=shell&dil(out&~shell); leather=v.c((0.24,0.15,0.09)); edge=v.c(p['edge'])
        lp={'chest':8,'leg':7,'shoulder':5,'glove':7,'boot':6,'belt':5}.get(slot)
        if (lp and FAM in ('plate','scale','leather') or slot in ('shoulder','boot')) and not _fit(slot):
            zc=np.argwhere(shell)[:,2]; zmid=np.percentile(zc,55)
            band=outer&((Z_%lp)==0)&((Z_<zmid) if slot=='chest' else True)
            st=dil(band)&out&~shell&(np.roll(band,1,2)|band|np.roll(band,-1,2)); g[st]=dark; shell|=st   # lame lip (each plate overlaps the next)
            rv=st&((X_+Y_)%9==0); g[rv]=edge
            rv2=dil(rv)&out&~shell&((X_+Y_)%9==0); g[rv2]=edge; shell|=rv2   # domed rivet heads
        if slot in ('glove','leg') and FAM!='leather':   # couter / poleyn: round cop over the joint
            jb=('foreArm_' if slot=='glove' else 'shin_')+side; jp=(BH[jb]-lo)/RES
            d2=(X_-jp[0])**2+(Y_-jp[1])**2+(Z_-jp[2])**2; facing=((Y_-jp[1])*FRONT>0) if slot=='leg' else ((Y_-jp[1])*FRONT<0)
            cop=dil(outer&(d2<=5.5**2)&facing,1)&out&~shell&(d2<=6.5**2); g[cop]=metal if i<2 else tr; shell|=cop
            cop2=dil(cop)&out&~shell&(d2<=3.0**2)&facing; g[cop2]=metal; shell|=cop2
            if FAM=='plate':   # v12: mail showing at the joint around the cop (layered kit)
                mz=outer&(d2>6.5**2)&(d2<=9.5**2)&~cop; g[mz]=v.c(tuple(min(1,c*1.25) for c in base)); g[mz&(((X_+Y_+Z_)%2)==0)]=v.c(tuple(c*0.55 for c in base))
        if slot in ('chest','leg','glove','boot'):   # raised leather buckle straps
            zz=np.argwhere(R)[:,2]; zm=int(np.median(zz)); sd=((Y_-np.median(np.argwhere(R)[:,1]))*FRONT<0) if slot!='chest' else (abs(X_-int(round((0-lo[0])/RES)))>int(0.11/RES))
            stp=dil(outer&sd&(abs(Z_-zm)<=1))&out&~shell&(abs(Z_-zm)<=1); g[stp]=leather; shell|=stp; g[stp&((X_+Y_)%9==0)]=edge
    g[trim&shell]=tr
    if HERO in ('orin','finn','elira','wren') and _fit(slot):   # v30: bevelled plate edges - raised rolled rim + light chamfer above each lame lip
        Zb=np.indices(S)[2]; bev=dil(trim&shell)&out&~shell&dil(shell)&(np.roll(trim,1,2)|trim|np.roll(trim,-1,2)); g[bev]=tr if i>=2 else v.c(p['edge']); shell|=bev
        lm2=LAMEM[0]&shell; hl=shell&np.roll(lm2,1,2)&~lm2&~trim; g[hl]=v.c(tuple(min(1,c*1.45) for c in base))
    if slot not in ('helm','cloak') and not _fit(slot) and not (slot=='boot' and HERO=='rook') and CAPE is None:   # v11: rolled rim on every piece edge -> visible plate thickness, reads as a worn piece not painted skin
        ed=shell&dil(skin&~dil(R,1),2)&dil(out&~shell); rl=dil(ed)&out&~shell&dil(skin&~dil(R,1),3)
        g[rl]=tr if i>=2 else v.c(p['edge']) if not ROBED else dark; shell|=rl
    # crop
    idx=np.argwhere(g>0); a=idx.min(0)-1; b=idx.max(0)+2
    vv=V(1); vv.pal=v.pal; vv.g=g[a[0]:b[0],a[1]:b[1],a[2]:b[2]].copy()
    if i>=4 and not ROBED and slot=='helm': A.filigree(vv,p)   # v11: gold rims carry legendary on body pieces (no speckle noise)   # v9: no gold blotches on robed mantles (trim hem only)
    if FAM=='scale' and slot not in ('cloak','helm'):   # v28: overlapping scale rows (brick-offset dark scale edges), no speckle
        Xc,Yc,Zc=np.indices(vv.g.shape); mm=(vv.g==vv.c(base)); rw=(Zc//3)%2
        vv.g[mm&((Zc%3)==0)]=vv.c(tuple(c*0.62 for c in base)); vv.g[mm&((Zc%3)!=0)&(((Xc+Yc+rw*2)%4)==0)]=vv.c(tuple(c*0.80 for c in base))
    elif FAM=='chain' and _fit(slot):   # v15: calm mail - horizontal ring rows instead of a 1-voxel checker
        Zc=np.indices(vv.g.shape)[2]; mm=(vv.g==vv.c(base)); vv.g[mm&((Zc%3)==0)]=vv.c(tuple(c*0.72 for c in base))
    elif FAM in ('chain','scale','leather') and slot not in ('cloak',): A.skin(vv,FAM,p,i)   # family surface (rings / scales / stitched leather)
    if i<=1 or slot=='helm': G.wear(vv,p,seed=hash((slot,side))%97)   # v12: clean metal on rare+ body pieces (speckle read as voxel bulk)
    if i==5: A.molten(vv,p,seed=11)
    av_=AV[a[0]:b[0],a[1]:b[1],a[2]:b[2]]&(vv.g>0)
    if av_.any():   # v9: real riveted-ring mail on the aventail (light rings, dark gaps, row shading)
        Xa,Ya,Za=np.indices(vv.g.shape); mb=tuple(min(1,c*1.35) for c in base); md=tuple(c*0.45 for c in base)
        vv.g[av_]=vv.c(mb); vv.g[av_&(((Xa+Ya+Za+(Za//1))%2)==0)]=vv.c(tuple(c*1.0 for c in base)); vv.g[av_&((Za%3)==0)&(((Xa+Ya)%2)==0)]=vv.c(md)
        if i>=4: vv.g[av_&(Za==Za[av_].min())]=vv.c(p['trim'])
        if i==5: vv.g[av_&((Xa*7+Za*3)%17==0)]=vv.c((0.9,0.35,0.05))
    kk=KEEP[a[0]:b[0],a[1]:b[1],a[2]:b[2]]&(vv.g>0); vv.g[kk]=vv.c((0.02,0.02,0.025))   # hood shadow stays black after filigree/wear/molten
    if i==0:
        m=np.isin(vv.g,[vv.c(p['edge'])]); rng=np.random.default_rng(3); q=np.argwhere(m); q=q[rng.random(len(q))<0.08]; vv.g[tuple(q.T)]=0
    return vv,lo+a*RES
# ---------- skin weights from the hero body (restricted to the slot's bones) ----------
def weight_kd(bones):
    sel=np.where(np.isin(domname,bones))[0]; k=KDTree(len(sel))
    for j,i in enumerate(sel): k.insert(co[i],int(i))
    k.balance(); return k
def skin_obj(ob,kdw):
    vg={}
    for v in ob.data.vertices:
        hits=kdw.find_n(ob.matrix_world@v.co,6); acc={}
        for (pp,i,d) in hits:
            w=1.0/(d+0.004)
            for ww,bn in VW[i][:4]: acc[bn]=acc.get(bn,0)+ww*w
        top=sorted(acc.items(),key=lambda x:-x[1])[:4]; s=sum(x[1] for x in top)
        for bn,ww in top:
            if bn not in vg: vg[bn]=ob.vertex_groups.new(name=bn)
            vg[bn].add([v.index],ww/s,'REPLACE')
    ob.parent=arm; m=ob.modifiers.new('Armature','ARMATURE'); m.object=arm
def drop_islands(ob,frac=0.02):
    """remove tiny disconnected bits (e.g. cells next to a baked prop in the hand)"""
    import bmesh
    bm=bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); seen=set(); comps=[]
    for v0 in bm.verts:
        if v0.index in seen: continue
        st=[v0]; c=[]; seen.add(v0.index)
        while st:
            v=st.pop(); c.append(v)
            for e in v.link_edges:
                o=e.other_vert(v)
                if o.index not in seen: seen.add(o.index); st.append(o)
        comps.append(c)
    n=len(bm.verts); kill=[v for c in comps if len(c)<frac*n for v in c]
    if kill: bmesh.ops.delete(bm,geom=kill,context='VERTS')
    bm.to_mesh(ob.data); bm.free(); return len(kill)
def bake_low(hi,name,target,texres):
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=1; sc.cycles.device='CPU'
    for m in hi.data.materials:
        nt=m.node_tree; nt.nodes.clear(); a=nt.nodes.new('ShaderNodeVertexColor'); a.layer_name='Col'; e=nt.nodes.new('ShaderNodeEmission'); o=nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(a.outputs[0],e.inputs[0]); nt.links.new(e.outputs[0],o.inputs[0])
    print('HI',name,len(hi.data.polygons),flush=True)
    lo_=hi.copy(); lo_.data=hi.data.copy(); bpy.context.scene.collection.objects.link(lo_)
    t1=len(lo_.data.polygons)*2 if any(len(p.vertices)==4 for p in lo_.data.polygons) else len(lo_.data.polygons)
    bpy.ops.object.select_all(action='DESELECT'); lo_.select_set(True); bpy.context.view_layer.objects.active=lo_
    for _k in range(6):
        if not len(lo_.data.polygons) or sum(len(p.vertices)-2 for p in lo_.data.polygons)>=target*1.05: break   # v7: thin pieces: subdivide so the budget floor (>=3.5k) is met
        s_=lo_.modifiers.new('s','SUBSURF'); s_.subdivision_type='SIMPLE'; s_.levels=1; bpy.ops.object.modifier_apply(modifier='s')
    m=lo_.modifiers.new('d','DECIMATE'); m.ratio=min(1,target/max(1,sum(len(p.vertices)-2 for p in lo_.data.polygons))); bpy.ops.object.modifier_apply(modifier='d')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=0.004); bpy.ops.object.mode_set(mode='OBJECT')
    for a_ in list(lo_.data.color_attributes): lo_.data.color_attributes.remove(a_)
    img=bpy.data.images.new(name+'_alb',texres,texres); img.colorspace_settings.name='Non-Color'   # bake raw sRGB numbers -> png = sRGB albedo
    mat=bpy.data.materials.new(name+'_mat'); mat.use_nodes=True; nt=mat.node_tree; bsdf=nt.nodes['Principled BSDF']; tx=nt.nodes.new('ShaderNodeTexImage'); tx.image=img
    nt.links.new(tx.outputs[0],bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value=0.62; bsdf.inputs['Metallic'].default_value=0.0; nt.nodes.active=tx
    lo_.data.materials.clear(); lo_.data.materials.append(mat)
    for p in lo_.data.polygons: p.use_smooth=True
    bpy.ops.object.select_all(action='DESELECT'); hi.select_set(True); lo_.select_set(True); bpy.context.view_layer.objects.active=lo_
    bk=sc.render.bake; bk.use_selected_to_active=True; bk.cage_extrusion=RES*1.5; bk.max_ray_distance=RES*4; bk.margin=4
    bpy.ops.object.bake(type='EMIT')
    img.filepath_raw=f"/tmp/l3w/tex_{name}.png"; img.file_format='PNG'; img.save(); img.colorspace_settings.name='sRGB'; img.pack()
    return lo_
stats={}; masks={}
for slot,side in PIECES:
    name=slot+('_'+side if side else '')
    if ONLY and name not in ONLY: continue
    R=region(slot,side)
    bones=BONESET[slot](('_'+side)) if callable(BONESET[slot]) else BONESET[slot]; kdw=weight_kd(bones)
    M=(dil(R,3)&solid) if slot=='helm' else (dil(R,1)&skin)
    if slot=='belt' and not ROBED:   # also hide the tabard strip that hangs between the thighs under the front tasset
        tb=(abs(spos[:,0])<0.075)&(spos[:,2]>beltz-0.34)&(spos[:,2]<beltz-0.05)
        T_=np.zeros(S,bool); T_[tuple(sidx[tb].T)]=True; M|=dil(T_,2)&solid
    if slot=='leg' and not ROBED:   # v7: skirt/tabard flaps the rig weights to thigh/shin swing loose in attack1 (floating bits) -> hide them under the cuisses
        X=side; bb=np.isin(cbn,['thigh'+'_'+X,'shin'+'_'+X])
        def _sd(P,b_):
            h_,t_=BH[b_],BT[b_]; d_=t_-h_; u_=np.clip(((P-h_)@d_)/(d_@d_),0,1); return np.linalg.norm(P-(h_+u_[:,None]*d_),axis=1)
        dd=np.minimum(_sd(spos,'thigh_'+X),_sd(spos,'shin_'+X)); fl=bb&(dd>0.115)&(spos[:,2]<beltz-0.05)
        T_=np.zeros(S,bool); T_[tuple(sidx[fl].T)]=True; M|=dil(T_,1)&solid; print('FLAP',name,int(fl.sum()))
    mi=np.argwhere(M); masks[name]={"cells":(np.ravel_multi_index(mi.T,S)).tolist()}
    for r in RARITIES:
        v,org=build_grid(slot,side,r,R); nm=f"{HERO}_{FAM}_{r}_{name}"
        bl.MATS.clear(); hi,_=bl.mesh_g(v,nm+"_hi",RES,origin=tuple(org)); hi,_=bl.smooth_plate(hi,v,RES,tuple(org),iters=5,fac=0.6)
        if slot!='helm': drop_islands(hi,(0.005 if slot=='shoulder' else 0.06) if ROBED else 0.03)
        low=bake_low(hi,nm,TRI[slot],TEX.get(slot,256)); bpy.data.objects.remove(hi)
        l1=low.copy(); l1.data=low.data.copy(); bpy.context.scene.collection.objects.link(l1)
        bpy.ops.object.select_all(action='DESELECT'); l1.select_set(True); bpy.context.view_layer.objects.active=l1
        m=l1.modifiers.new('d','DECIMATE'); m.ratio=0.45; bpy.ops.object.modifier_apply(modifier='d')
        for lod,ob in enumerate((low,l1)):
            ob.name=nm+("_lod1" if lod else ""); skin_obj(ob,kdw)
            bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); arm.select_set(True)
            bpy.ops.export_scene.gltf(filepath=f"{OUT}/{ob.name}.glb",use_selection=True,export_format='GLB',export_animations=False,export_skins=True,export_apply=False,export_image_format='AUTO')
            ob.data.calc_loop_triangles(); stats[ob.name]=len(ob.data.loop_triangles)
        for ob in (low,l1): bpy.data.objects.remove(ob)
        print('DONE',name,r,stats[nm],stats[nm+'_lod1'],flush=True)
if HERO=='rook':   # v24: Rook's coat leaves 1-cell slivers at every mask edge -> grow each non-helm slot mask by 1 cell (body only)
    for k_ in list(masks):
        if k_=='helm': continue
        m_=np.zeros(S,bool); m_.flat[np.array(masks[k_]['cells'],dtype=np.int64)]=True; masks[k_]={'cells':np.ravel_multi_index(np.argwhere(dil(m_,1)&solid).T,S).tolist()}
mp=f"{OUT}/{HERO}_body_mask.json"
if ONLY and os.path.exists(mp): old=json.load(open(mp))["slots"]; old.update(masks); masks=old
json.dump({"hero":HERO,"res":RES,"origin_blender":lo.tolist(),"dims":S.tolist(),
 "coords":"cell=floor((blender-origin)/res), blender=(godot.x,-godot.z,godot.y), rest pose",
 "rule":"hide a body triangle when all 3 of its rest-pose vertices fall in an equipped slot's cells","slots":masks},open(f"{OUT}/{HERO}_body_mask.json","w"))
tp=f"{OUT}/{HERO}_{FAM}_tris.json"
if ONLY and os.path.exists(tp): o=json.load(open(tp)); o.update(stats); stats=o
json.dump(stats,open(tp,"w"),indent=1)
