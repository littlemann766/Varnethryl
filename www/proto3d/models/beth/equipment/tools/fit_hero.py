# Equipment v2 (fitted): per-hero armour conformed to the hero's own body mesh.
# usage: blender -b -P fit_hero.py -- <hero> <family> <outdir>
# Reads Lucian's rig glb (read-only), writes Beth's own fitted skinned pieces + per-slot body masks.
import bpy,sys,os,json,math,numpy as np
sys.path.insert(0,'/workspace/godot-art/loot3_tools')
import bl, armor3d as A, gmodels as G
from vox import V
from edata import RARITIES
from mathutils.kdtree import KDTree
args=sys.argv[sys.argv.index('--')+1:]; HERO,FAM,OUT=args[0],args[1],args[2]; os.makedirs(OUT,exist_ok=True)
RES=0.01
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f'/workspace/vmain/voxel/{HERO}_voxel.glb')
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
cb=np.array([dom[kd.find(p)[1]] for p in spos]); cbn=np.array([gn[d] if d>=0 else '' for d in cb])
def tpar(pos,b):   # 0..1 along bone
    h,t=BH[b],BT[b]; d=t-h; return ((pos-h)@d)/(d@d)
FRONT=np.sign(((BH['eye_L']+BH['eye_R'])/2-BH['head'])[1]) or -1.0
neckz=BH['neck'][2]; beltz=BH['spine'][2]
def region(slot,side=None):
    m=np.zeros(len(sidx),bool)
    if slot=='chest':
        m=np.isin(cbn,['spine','spine2','chest','upperChest'])&(spos[:,2]<neckz-0.005)&(spos[:,2]>beltz+0.035)
        sx=abs(BH['upperArm_L'][0])-0.035; m&=abs(spos[:,0])<sx
    elif slot=='shoulder':
        X='_'+side; ua='upperArm'+X; sgn=np.sign(BH[ua][0])
        m=(np.isin(cbn,[ua,'shoulder'+X])&(tpar(spos,ua)<0.62))
        m|=np.isin(cbn,['upperChest','chest'])&(spos[:,0]*sgn>abs(BH[ua][0])-0.05)&(spos[:,2]>BH[ua][2]-0.09)
    elif slot=='glove':
        X='_'+side; m=(cbn=='foreArm'+X)&(tpar(spos,'foreArm'+X)>0.08)
        m|=np.array([n.endswith(X) and (n.startswith(('hand','fingers','index','middle','ring','pinky','thumb'))) for n in cbn])
    elif slot=='leg':
        X='_'+side; m=(cbn=='thigh'+X)|((cbn=='shin'+X)&(tpar(spos,'shin'+X)<0.12))
    elif slot=='boot':
        X='_'+side; m=((cbn=='shin'+X)&(tpar(spos,'shin'+X)>=0.12))|np.isin(cbn,['foot'+X,'toe'+X])
    elif slot=='belt':
        m=np.isin(cbn,['hips','spine','spine2'])&(abs(spos[:,2]-beltz)<0.035)
    R=np.zeros(S,bool); R[tuple(sidx[m].T)]=True; return R
BONESET={'chest':['spine','spine2','chest','upperChest','hips'],'belt':['hips','spine','spine2'],
 'shoulder':lambda X:['upperArm'+X,'shoulder'+X,'upperChest','chest'],'glove':lambda X:['foreArm'+X,'hand'+X]+[f+n+X for f in ('index','middle','ring','pinky','thumb') for n in '123']+['fingers'+X],
 'leg':lambda X:['thigh'+X,'shin'+X,'hips'],'boot':lambda X:['shin'+X,'foot'+X,'toe'+X]}
THK={'chest':2,'shoulder':3,'glove':2,'leg':2,'boot':2,'belt':2}
PIECES=[('chest',None),('belt',None)]+[(s,x) for s in ('shoulder','glove','leg','boot') for x in ('L','R')]
def build_grid(slot,side,r,R):
    i=RARITIES.index(r); p=A.pal(FAM,r); t=THK[slot]+(1 if slot=='shoulder' and i>=3 else 0)
    layers=[R]; acc=R.copy()
    for k in range(t):
        nx=dil(acc)&out&~acc; layers.append(nx); acc|=nx
    shell=acc&out; outer=layers[-1]
    Rin=R&~dil(skin&~R,2); core=dil(Rin,t+1)&shell; trim=shell&~core
    g=np.zeros(S,np.int16); v=V(1); v.g=g
    metal=v.c(p['metal']); dark=v.c(tuple(c*0.62 for c in p['metal'])); tr=v.c(p['trim'] if i>=2 else p['edge'])
    g[shell]=metal
    X_,Y_,Z_=np.indices(S)
    rows=None
    if slot in('chest','leg','shoulder','glove','boot'):
        per={'chest':18,'leg':16,'shoulder':7,'glove':14,'boot':15}[slot]; rows=(Z_%per==0)
        if slot=='shoulder':
            ridge=dil(outer&rows)&out&~shell&dil(shell)
            if i>=1: g[ridge]=dark; shell|=ridge
        if i>=1: g[outer&rows]=dark
        if i>=1:
            riv=outer&(np.roll(rows,1,2))&((X_+Y_)%7==0); g[riv]=v.c(p['edge'])
    if slot=='chest' and i>=2:
        cx=int(round((0-lo[0])/RES)); keel=outer&(abs(X_-cx)<=1)&(np.sign(Y_-np.median(np.argwhere(R)[:,1]))==FRONT)
        k2=dil(keel)&out&~shell&dil(shell); g[k2]=tr; shell|=k2
    if slot=='shoulder':
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
    g[trim&shell]=tr
    # crop
    idx=np.argwhere(g>0); a=idx.min(0)-1; b=idx.max(0)+2
    vv=V(1); vv.pal=v.pal; vv.g=g[a[0]:b[0],a[1]:b[1],a[2]:b[2]].copy()
    if i>=4: A.filigree(vv,p)
    G.wear(vv,p,seed=hash((slot,side))%97)
    if i==5: A.molten(vv,p,seed=11)
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
stats={}; masks={}
for slot,side in PIECES:
    name=slot+('_'+side if side else ''); R=region(slot,side)
    bones=BONESET[slot](('_'+side)) if callable(BONESET[slot]) else BONESET[slot]; kdw=weight_kd(bones)
    M=dil(R,1)&skin; mi=np.argwhere(M); masks[name]={"cells":(np.ravel_multi_index(mi.T,S)).tolist()}
    for r in RARITIES:
        v,org=build_grid(slot,side,r,R); vv=v.down()
        for lod,(gg,s) in enumerate(((v,RES),(vv,RES*2))):
            bl.MATS.clear(); nm=f"{HERO}_{FAM}_{r}_{name}"+("_lod1" if lod else "")
            ob,tr=bl.mesh_g(gg,nm,s,origin=tuple(org)); ob,tr=bl.smooth_plate(ob,gg,s,tuple(org))
            skin_obj(ob,kdw)
            bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); arm.select_set(True)
            bpy.ops.export_scene.gltf(filepath=f"{OUT}/{nm}.glb",use_selection=True,export_format='GLB',export_animations=False,export_skins=True,export_apply=False)
            stats[nm]=tr; bpy.data.objects.remove(ob)
        print('DONE',name,r,stats[f"{HERO}_{FAM}_{r}_{name}"],flush=True)
json.dump({"hero":HERO,"res":RES,"origin_blender":lo.tolist(),"dims":S.tolist(),
 "coords":"cell=floor((blender-origin)/res), blender=(godot.x,-godot.z,godot.y), rest pose",
 "rule":"hide a body triangle when all 3 of its rest-pose vertices fall in an equipped slot's cells","slots":masks},open(f"{OUT}/{HERO}_body_mask.json","w"))
json.dump(stats,open(f"{OUT}/{HERO}_{FAM}_tris.json","w"),indent=1)
