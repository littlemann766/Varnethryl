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
lo=co.min(0)-0.08; hi=co.max(0)+0.08; S=np.ceil((hi-lo)/RES).astype(int)+1
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
def region(slot,side=None):
    m=np.zeros(len(sidx),bool); X='_'+(side or '')
    if slot=='chest':
        m=(np.isin(cbn,['spine','spine2','chest','upperChest','hips'])|np.char.startswith(cbn.astype(str),'coat'))&(spos[:,2]<neckz-0.005)&(spos[:,2]>beltz-0.03)   # v11: overlaps the belt (no tunic bleed between them)
        sx=max(abs(BH['upperArm_L'][0])-0.035,0.15); m&=abs(spos[:,0])<sx; m&=(capew<0.15)|(((spos[:,1]-BH['spine'][1])*FRONT)>0)   # v11: front cells always (Wren's coat-weighted tunic)
    elif slot=='shoulder':
        ua='upperArm'+X; sgn=np.sign(BH[ua][0])
        m=(np.isin(cbn,[ua,'shoulder'+X])&(tpar(spos,ua)<(0.35 if ROBED else 0.78)))
        m|=np.isin(cbn,['upperChest','chest'])&(spos[:,0]*sgn>abs(BH[ua][0])-0.05)&(spos[:,2]>BH[ua][2]-0.09)
        m&=spos[:,2]<BH[ua][2]+9   # v10: no cap (1-vox pauldrons hug the shoulder; a cap exposed raw body voxels)
    elif slot=='glove':      # gauntlet + vambrace + couter (overlaps the rerebrace -> no elbow gap)
        m=((cbn=='foreArm'+X)&(tpar(spos,'foreArm'+X)>0.55)) if ROBED else ((cbn=='foreArm'+X)|((cbn=='upperArm'+X)&(tpar(spos,'upperArm'+X)>0.66)))   # robed: gauntlet + cuff only, the sleeve stays
        m|=np.array([n.endswith(X) and (n.startswith(('hand','fingers','index','middle','ring','pinky','thumb'))) for n in cbn])
    elif slot=='leg':        # cuisse + poleyn (overlaps the greave -> no knee gap)
        m=(cbn=='thigh'+X)|((cbn=='shin'+X)&(tpar(spos,'shin'+X)<0.24))
    elif slot=='boot':
        m=((cbn=='shin'+X)&(tpar(spos,'shin'+X)>=0.12))|np.isin(cbn,['foot'+X,'toe'+X])
    elif slot=='belt' and ROBED:   # robed: a sash/girdle band only, the robe skirt stays
        m=np.isin(cbn,['hips','spine','spine2'])&(abs(spos[:,2]-beltz)<0.03)
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
if ROBED: PIECES=[p for p in PIECES if p[0] not in ('chest','leg')]; THK.update(helm=2,shoulder=1,belt=1,glove=1,cloak=3)   # robed casters stay robed: no breastplate/cuisses over the robe
def build_grid(slot,side,r,R):
    i=RARITIES.index(r); p=A.pal(FAM,r); t=THK[slot]+(1 if slot=='shoulder' and i>=3 else 0)
    if ROBED and slot!='helm':
        nb=np.zeros(S,np.int8)
        for ax in range(3):
            for d in (1,-1): nb+=np.roll(R,d,ax)
        R=R&(nb>=3)   # v6: drop 1-voxel spurs -> no blobby edges on robed sets
    layers=[R]; acc=R.copy()
    for k in range(t):
        nx=dil(acc)&out&~acc; layers.append(nx); acc|=nx
    shell=acc&out
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
        zbot={'great':zb-1,'basc':zb+0.30*Hh,'cowl':zb-2}[STY]
        def prof(T):   # radius scale per height + backward lean of the crown (bascinet point)
            U=(Z_-zs)/(Hd+T); Lw=np.clip((zs-Z_)/max(zs-zb,1),0,1.5)
            if STY=='basc': f=np.where(U>0,np.clip(1-U,0,1)**0.62*(1-0.25*U*U),1-0.10*Lw); lean=np.clip(U,0,1)*0.45*bb
            elif STY=='cowl': f=np.where(U>0,np.sqrt(np.clip(1-U**2.2,0,1)),1+0.35*Lw**1.5); lean=np.clip(U,0,1)*0.35*bb
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
        R=R|(inside&skin)
        hg_=np.isin(cbn,['head','neck','jaw','eye_L','eye_R','chest','upperChest','spine2'])|np.char.startswith(cbn.astype(str),'hair')
        hg_&=spos[:,2]>BH['neck'][2]-0.02; HGM=np.zeros(S,bool); HGM[tuple(sidx[hg_].T)]=True   # v11: hide gear riding above the neck (Rook's beige back gear)
        HGM=dil(HGM,1)&solid&~((ell(t+9)>1)&(Z_<zbot-8)&False)
        masks[name]={'cells':np.ravel_multi_index(np.argwhere((HGM|(ell(t+9)<=1)&(Z_>=zbot-(3 if ROBED else 8))|inside|dil(R,3))&solid).T,S).tolist()}   # hide every body cell inside the helm envelope   # v7: hide every body cell inside the helm envelope (faces under helm/hood)
    if slot=='cloak': shell=close((layers[-1]|layers[-2]),1)&out   # cloak floats just outside the plate; close() fills pin-holes (Darius back speck)
    if slot not in ('cloak','helm') and not ROBED: shell=close(shell,1)&out&dil(R,t)   # v10: fill pin-holes only within the armour's own thickness of the body (no bridging bulk)             # v3: fill the body's voxel lumps -> smooth plate surface, real thickness kept
    outer=shell&dil(out&~shell)
    Rin=R&~dil(skin&~R,2); core=dil(Rin,t+1)&shell; trim=shell&~core
    if slot=='helm': trim=np.zeros(S,bool)
    if ROBED and slot not in ('helm','cloak'): zz_=np.argwhere(shell)[:,2]; trim=shell&(np.indices(S)[2]<=zz_.min()+1)   # v9: robed: gold only on the hem, no edge blotches
    g=np.zeros(S,np.int16); v=V(1); v.g=g; KEEP=np.zeros(S,bool); AV=HG['av'] if slot=='helm' and 'av' in HG else np.zeros(S,bool)
    base=p['leather'] if FAM=='leather' else A.PAL[r].get('cloth',p['metal']) if ROBED else p['metal']   # robed: rarity cloth colour, not the white robe
    metal=v.c(base); dark=v.c(tuple(c*0.62 for c in base)); tr=v.c(p['trim'] if i>=2 else p['edge'])
    g[shell]=metal
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
            if STY=='great' and i>=1:   # breaths: rows of black holes on the right cheek of the face plate
                br=outer&front&(Z_<ze-3)&(Z_>HZ[0]+3)&((X_-cx)*1>=3)&((X_-cx)<=H_['ax']*0.65)&((Z_%3)==0)&((X_%2)==0); g[br]=blk
            rim=outer&(Z_<=HZ[0]+1)&~(H_.get('av',np.zeros(S,bool))); rr=dil(rim)&ext&~shell&(Z_<=HZ[0]+1); g[rr]=tr if i>=2 else dark; shell|=rr
            g[rr&((X_+Y_)%4==0)]=edge   # rivets on the rim
            g[band&((X_+Y_)%5==0)]=edge
        top=int(np.argwhere(shell)[:,2].max())
        if i>=2 and STY!='cowl':   # comb crest front-to-back along the crown centre (taller on higher tiers)
            ch=2+(i-2)
            cr=(abs(X_-cx)<=0)&(Z_>top-6)&(Z_<=top+ch)&ext&dil(shell&(Z_>=top-6),ch+1)&(fy>-0.9*H_['bb'])&(fy<0.8*H_['bf'])
            g[cr]=tr; shell|=cr
        if i>=3 and STY!='cowl':   # horns sweep out and up from the temples
            hc=v.c((0.88,0.84,0.74) if i<5 else (0.10,0.08,0.08)); zh=int(H_['zs']+0.35*(H_['zt']-H_['zs'])); ys=int(round(H_['cy']-FRONT*0.1*H_['bb']))
            xs=np.where(shell[:,ys,zh])[0]; x0=xs.max() if len(xs) else cx+10
            for k in range(16):
                x=x0-1+int(k*0.8); z=zh+int(k**1.45/3.0); r=max(0.6,2.6-k*0.13)
                for dx in range(-3,4):
                    for dy in range(-3,4):
                        for dz in range(-3,4):
                            if dx*dx+dy*dy+dz*dz<=r*r:
                                for xx in (x+dx,int(round(2*cx-(x+dx)))):
                                    q=(xx,ys+dy,z+dz)
                                    if all(0<=q[j]<S[j] for j in range(3)) and not shell[q]: g[q]=hc if k<13 else tr; shell[q]=True
    rows=None
    if slot in('chest','leg','shoulder','glove','boot'):
        if slot in('leg','glove'):   # leather straps on the back
            st=outer&((Y_-np.median(np.argwhere(R)[:,1]))*FRONT<0)&((Z_%11)<=1); g[st]=v.c((0.24,0.15,0.09)); g[st&((X_%4)==0)&((Z_%11)==0)]=v.c(p['edge'])
        per={'chest':18,'leg':16,'shoulder':7,'glove':14,'boot':15}[slot]; rows=(Z_%per==0)
        if slot=='shoulder':
            ridge=dil(outer&rows)&out&~shell&dil(shell)
            if i>=1 and not ROBED: g[ridge]=dark; shell|=ridge
        if i>=1: g[outer&rows]=dark
        if i>=1:
            riv=outer&(np.roll(rows,1,2))&((X_+Y_)%7==0); g[riv]=v.c(p['edge'])
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
        lp={'chest':6,'leg':5,'shoulder':4,'glove':5,'boot':5,'belt':4}.get(slot)
        if lp and FAM in ('plate','scale','leather') or slot in ('shoulder','boot'):
            zc=np.argwhere(shell)[:,2]; zmid=np.percentile(zc,55)
            band=outer&((Z_%lp)==0)&((Z_<zmid) if slot=='chest' else True)
            st=dil(band)&out&~shell&(np.roll(band,1,2)|band|np.roll(band,-1,2)); g[st]=dark; shell|=st   # lame lip (each plate overlaps the next)
            rv=st&((X_+Y_)%6==0); g[rv]=edge
            rv2=dil(rv)&out&~shell&((X_+Y_)%6==0); g[rv2]=edge; shell|=rv2   # domed rivet heads
        if slot in ('glove','leg') and FAM!='leather':   # couter / poleyn: round cop over the joint
            jb=('foreArm_' if slot=='glove' else 'shin_')+side; jp=(BH[jb]-lo)/RES
            d2=(X_-jp[0])**2+(Y_-jp[1])**2+(Z_-jp[2])**2; facing=((Y_-jp[1])*FRONT>0) if slot=='leg' else ((Y_-jp[1])*FRONT<0)
            cop=dil(outer&(d2<=5.5**2)&facing,1)&out&~shell&(d2<=6.5**2); g[cop]=metal if i<2 else tr; shell|=cop
            cop2=dil(cop)&out&~shell&(d2<=3.0**2)&facing; g[cop2]=metal; shell|=cop2
        if slot in ('chest','leg','glove','boot'):   # raised leather buckle straps
            zz=np.argwhere(R)[:,2]; zm=int(np.median(zz)); sd=((Y_-np.median(np.argwhere(R)[:,1]))*FRONT<0) if slot!='chest' else (abs(X_-int(round((0-lo[0])/RES)))>int(0.11/RES))
            stp=dil(outer&sd&(abs(Z_-zm)<=1))&out&~shell&(abs(Z_-zm)<=1); g[stp]=leather; shell|=stp; g[stp&((X_+Y_)%9==0)]=edge
    g[trim&shell]=tr
    if slot not in ('helm','cloak'):   # v11: rolled rim on every piece edge -> visible plate thickness, reads as a worn piece not painted skin
        ed=shell&dil(skin&~dil(R,1),2)&dil(out&~shell); rl=dil(ed)&out&~shell&dil(skin&~dil(R,1),3)
        g[rl]=tr if i>=2 else v.c(p['edge']) if not ROBED else dark; shell|=rl
    # crop
    idx=np.argwhere(g>0); a=idx.min(0)-1; b=idx.max(0)+2
    vv=V(1); vv.pal=v.pal; vv.g=g[a[0]:b[0],a[1]:b[1],a[2]:b[2]].copy()
    if i>=4 and not ROBED and slot=='helm': A.filigree(vv,p)   # v11: gold rims carry legendary on body pieces (no speckle noise)   # v9: no gold blotches on robed mantles (trim hem only)
    if FAM in ('chain','scale','leather') and slot not in ('cloak',): A.skin(vv,FAM,p,i)   # family surface (rings / scales / stitched leather)
    G.wear(vv,p,seed=hash((slot,side))%97)
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
    lo_=hi.copy(); lo_.data=hi.data.copy(); bpy.context.scene.collection.objects.link(lo_)
    t1=len(lo_.data.polygons)*2 if any(len(p.vertices)==4 for p in lo_.data.polygons) else len(lo_.data.polygons)
    bpy.ops.object.select_all(action='DESELECT'); lo_.select_set(True); bpy.context.view_layer.objects.active=lo_
    while sum(len(p.vertices)-2 for p in lo_.data.polygons)<target*1.05:   # v7: thin pieces: subdivide so the budget floor (>=3.5k) is met
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
        if slot!='helm': drop_islands(hi,0.06 if ROBED else 0.03)
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
mp=f"{OUT}/{HERO}_body_mask.json"
if ONLY and os.path.exists(mp): old=json.load(open(mp))["slots"]; old.update(masks); masks=old
json.dump({"hero":HERO,"res":RES,"origin_blender":lo.tolist(),"dims":S.tolist(),
 "coords":"cell=floor((blender-origin)/res), blender=(godot.x,-godot.z,godot.y), rest pose",
 "rule":"hide a body triangle when all 3 of its rest-pose vertices fall in an equipped slot's cells","slots":masks},open(f"{OUT}/{HERO}_body_mask.json","w"))
tp=f"{OUT}/{HERO}_{FAM}_tris.json"
if ONLY and os.path.exists(tp): o=json.load(open(tp)); o.update(stats); stats=o
json.dump(stats,open(tp,"w"),indent=1)
