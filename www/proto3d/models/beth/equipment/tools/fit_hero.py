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
FRONT=np.sign(((BH['eye_L']+BH['eye_R'])/2-BH['head'])[1]) or -1.0
neckz=BH['neck'][2]; beltz=BH['spine'][2]
def ero(m,k=1): return ~dil(~m,k)
def close(m,k): return ero(dil(m,k),k)
def region(slot,side=None):
    m=np.zeros(len(sidx),bool); X='_'+(side or '')
    if slot=='chest':
        m=np.isin(cbn,['spine','spine2','chest','upperChest'])&(spos[:,2]<neckz-0.005)&(spos[:,2]>beltz+0.02)
        sx=abs(BH['upperArm_L'][0])-0.035; m&=abs(spos[:,0])<sx; m&=capew<0.15
    elif slot=='shoulder':
        ua='upperArm'+X; sgn=np.sign(BH[ua][0])
        m=(np.isin(cbn,[ua,'shoulder'+X])&(tpar(spos,ua)<0.78))
        m|=np.isin(cbn,['upperChest','chest'])&(spos[:,0]*sgn>abs(BH[ua][0])-0.05)&(spos[:,2]>BH[ua][2]-0.09)
    elif slot=='glove':      # gauntlet + vambrace + couter (overlaps the rerebrace -> no elbow gap)
        m=(cbn=='foreArm'+X)|((cbn=='upperArm'+X)&(tpar(spos,'upperArm'+X)>0.66))
        m|=np.array([n.endswith(X) and (n.startswith(('hand','fingers','index','middle','ring','pinky','thumb'))) for n in cbn])
    elif slot=='leg':        # cuisse + poleyn (overlaps the greave -> no knee gap)
        m=(cbn=='thigh'+X)|((cbn=='shin'+X)&(tpar(spos,'shin'+X)<0.24))
    elif slot=='boot':
        m=((cbn=='shin'+X)&(tpar(spos,'shin'+X)>=0.12))|np.isin(cbn,['foot'+X,'toe'+X])
    elif slot=='belt':       # belt + faulds: covers the groin so the tabard no longer shows there
        m=(np.isin(cbn,['hips','spine','spine2'])|np.char.startswith(cbn.astype(str),'coat')|np.char.startswith(cbn.astype(str),'thigh'))&(spos[:,2]<beltz+0.035)&(spos[:,2]>beltz-0.17)
        m&=~(np.char.startswith(cbn.astype(str),'thigh')&(spos[:,2]<beltz-0.12))
        m|=(np.isin(cbn,['hips'])|np.char.startswith(cbn.astype(str),'coat'))&(abs(spos[:,0])<0.09)&(spos[:,2]<=beltz-0.17)&(spos[:,2]>beltz-0.26)   # front tasset over the groin (tabard)
    elif slot=='helm':
        hb=BH['head']; m=(spos[:,2]>BH['neck'][2]+0.025)&(np.hypot(spos[:,0]-hb[0],spos[:,1]-hb[1])<0.19)   # everything above the neck: face+beard+hair (beard is upperChest-weighted on Darius)
    elif slot=='cloak':
        m=np.char.startswith(cbn.astype(str),'cape')|(capew>=0.15)
    R=np.zeros(S,bool); R[tuple(sidx[m].T)]=True; return R
BONESET={'chest':['spine','spine2','chest','upperChest','hips'],'belt':['hips','spine','spine2','thigh_L','thigh_R'],'helm':['head','neck'],'cloak':[b for b in BH if b.startswith('cape')]+['upperChest','chest'],
 'shoulder':lambda X:['upperArm'+X,'shoulder'+X,'upperChest','chest'],'glove':lambda X:['upperArm'+X,'foreArm'+X,'hand'+X]+[f+n+X for f in ('index','middle','ring','pinky','thumb') for n in '123']+['fingers'+X],
 'leg':lambda X:['thigh'+X,'shin'+X,'hips'],'boot':lambda X:['shin'+X,'foot'+X,'toe'+X]}
THK={'chest':2,'shoulder':3,'glove':2,'leg':2,'boot':3,'belt':2,'helm':3,'cloak':4}
TRI={'chest':7000,'helm':8000,'shoulder':5000,'belt':4500,'glove':3500,'leg':4500,'boot':4000,'cloak':4000}
TEX={'chest':512,'helm':512,'cloak':512}
PIECES=[('helm',None),('cloak',None),('chest',None),('belt',None)]+[(s,x) for s in ('shoulder','glove','leg','boot') for x in ('L','R')]
def build_grid(slot,side,r,R):
    i=RARITIES.index(r); p=A.pal(FAM,r); t=THK[slot]+(1 if slot=='shoulder' and i>=3 else 0)
    layers=[R]; acc=R.copy()
    for k in range(t):
        nx=dil(acc)&out&~acc; layers.append(nx); acc|=nx
    shell=acc&out
    if slot=='helm':   # great helm: per-height ellipse fitted to this hero's head (+1 cm air), 3-voxel wall, flat-ish crown
        X_,Y_,Z_=np.indices(S); q=np.argwhere(R); cx_=np.median(q[:,0]); cy_=np.median(q[:,1]); z0,z1=q[:,2].min(),q[:,2].max()
        rx=np.zeros(S[2]); ry=np.zeros(S[2])
        for z in range(z0,z1+1):
            w=q[abs(q[:,2]-z)<=3]
            if len(w): rx[z]=np.percentile(abs(w[:,0]-cx_),97)+0.5; ry[z]=np.percentile(abs(w[:,1]-cy_),97)+0.5
        for z in range(z0,z1+1): rx[z]=max(rx[max(z0,z-6):z+7].max(),1); ry[z]=max(ry[max(z0,z-6):z+7].max(),1)
        RX=rx[np.clip(Z_,z0,z1)]; RY=ry[np.clip(Z_,z0,z1)]; e=((X_-cx_)/RX)**2+((Y_-cy_)/RY)**2
        eo=((X_-cx_)/(RX+t))**2+((Y_-cy_)/(RY+t))**2
        wall=(eo<=1)&(e>1)&(Z_>=z0)&(Z_<=z1); cap=(eo<=1)&(Z_>z1)&(Z_<=z1+t)
        shell=(wall|cap)&out; inside=(e<=1)&(Z_>=z0)&(Z_<=z1)
        R=R|(inside&skin); HZ=(z0,z1)
    if slot=='cloak': shell=(layers[-1]|layers[-2])&out   # cloak floats just outside the 2-3 cm back/shoulder plate
    if slot!='cloak': shell=close(shell,1)&out             # v3: fill the body's voxel lumps -> smooth plate surface, real thickness kept
    outer=shell&dil(out&~shell)
    Rin=R&~dil(skin&~R,2); core=dil(Rin,t+1)&shell; trim=shell&~core
    if slot=='helm': Zh=np.indices(S)[2]; trim=shell&((Zh<=HZ[0]+1)|((Zh>=HZ[1])&(Zh<=HZ[1]+1)&~(np.indices(S)[2]>HZ[1]+t)))
    g=np.zeros(S,np.int16); v=V(1); v.g=g
    metal=v.c(p['metal']); dark=v.c(tuple(c*0.62 for c in p['metal'])); tr=v.c(p['trim'] if i>=2 else p['edge'])
    g[shell]=metal
    X_,Y_,Z_=np.indices(S)
    if slot=='cloak':
        cl=p.get('cloth',(0.30,0.06,0.06)); g[shell]=v.c(cl); g[shell&(Z_%5==0)]=v.c(tuple(c*0.8 for c in cl))
        if i>=2: g[trim&shell]=tr
        idx=np.argwhere(g>0); a=idx.min(0)-1; b=idx.max(0)+2
        vv=V(1); vv.pal=v.pal; vv.g=g[a[0]:b[0],a[1]:b[1],a[2]:b[2]].copy(); return vv,lo+a*RES
    if slot=='helm':
        hz=int(HZ[0]+0.60*(HZ[1]-HZ[0])); cx=int(round((0-lo[0])/RES)); idx=np.argwhere(shell)
        yc=np.median(idx[:,1]); yd=idx[:,1].ptp()/2; front=((Y_-yc)*FRONT>yd*0.35)
        blk=v.c((0.03,0.03,0.03))
        slit=shell&front&(Z_>=hz-2)&(Z_<=hz+1)&(abs(X_-cx)>=2)&(abs(X_-cx)<=11)
        g[slit]=blk; so=slit&dil(out&~shell); g[so]=0; shell&=~so; g[dil(slit)&shell&~outer&front]=blk   # recessed black eye slits
        rim=dil(slit,1)&outer&~slit&~dil(slit&False,0)
        if i>=1: g[rim&((Z_>hz+1)|(Z_<hz-2))]=v.c(p['edge'] if i<4 else p['trim'])   # bright lip above/below the slit so it reads on dark steel
        Xi,Yi,Zi=X_,Y_,Z_; lin=dil(slit,2)&~shell&~dil(out&~dil(shell,1),0)&(((Yi-yc)*FRONT)<((idx[:,1]-yc)*FRONT).max()-2); lin&=~slit; g[lin&out]=blk; shell|=lin&out   # dark liner behind the slit
        if i>=1:   # visor plate: raised front below the slit, breaths on rare+
            vis=dil(outer&front&(Z_<hz-1)&(Z_>hz-12))&out&~shell&~dil(slit,1); g[vis]=metal; shell|=vis
            if i>=2: g[vis&((X_+Z_)%3==0)&(Z_<hz-4)&(abs(X_-cx)>2)]=blk
        if i>=2: g[outer&front&(abs(X_-cx)<=1)&(Z_<hz-1)]=tr; g[outer&(abs(Z_-(hz+2))<=0)]=tr  # cross + brow band
        top=idx[:,2].max()
        if i>=4:   # crest
            cr=(abs(X_-cx)<=1)&(Z_>top)&(Z_<=top+4)&dil(shell&(Z_>=top-1),4)&out; g[cr]=tr; shell|=cr
        if i>=3:   # horns
            hc=v.c((0.88,0.84,0.74) if i<5 else (0.10,0.08,0.08)); ys=int(yc)
            xs=np.where(shell[:,ys,top-6])[0]; x0=xs.max() if len(xs) else cx+10; ccx=(xs.max()+xs.min())/2 if len(xs) else cx
            for k in range(16):
                x=x0+int(k*0.7); z=top-6+int(k**1.4/3.2); r=max(0.6,2.6-k*0.13)
                for dx in range(-3,4):
                    for dy in range(-3,4):
                        for dz in range(-3,4):
                            if dx*dx+dy*dy+dz*dz<=r*r:
                                for xx in (x+dx,int(round(2*ccx-(x+dx)))):   # mirrored pair
                                    q=(xx,ys+dy,z+dz)
                                    if all(0<=q[j]<S[j] for j in range(3)) and not shell[q]: g[q]=hc if k<13 else tr; shell[q]=True
    rows=None
    if slot in('chest','leg','shoulder','glove','boot'):
        if slot in('leg','glove'):   # leather straps on the back
            st=outer&((Y_-np.median(np.argwhere(R)[:,1]))*FRONT<0)&((Z_%11)<=1); g[st]=v.c((0.24,0.15,0.09)); g[st&((X_%4)==0)&((Z_%11)==0)]=v.c(p['edge'])
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
    if slot=='shoulder' and True:
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
def bake_low(hi,name,target,texres):
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=1; sc.cycles.device='CPU'
    for m in hi.data.materials:
        nt=m.node_tree; nt.nodes.clear(); a=nt.nodes.new('ShaderNodeVertexColor'); a.layer_name='Col'; e=nt.nodes.new('ShaderNodeEmission'); o=nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(a.outputs[0],e.inputs[0]); nt.links.new(e.outputs[0],o.inputs[0])
    lo_=hi.copy(); lo_.data=hi.data.copy(); bpy.context.scene.collection.objects.link(lo_)
    t1=len(lo_.data.polygons)*2 if any(len(p.vertices)==4 for p in lo_.data.polygons) else len(lo_.data.polygons)
    bpy.ops.object.select_all(action='DESELECT'); lo_.select_set(True); bpy.context.view_layer.objects.active=lo_
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
    if slot=='belt':   # also hide the tabard strip that hangs between the thighs under the front tasset
        tb=(abs(spos[:,0])<0.075)&(spos[:,2]>beltz-0.34)&(spos[:,2]<beltz-0.05)
        T_=np.zeros(S,bool); T_[tuple(sidx[tb].T)]=True; M|=dil(T_,2)&solid
    mi=np.argwhere(M); masks[name]={"cells":(np.ravel_multi_index(mi.T,S)).tolist()}
    for r in RARITIES:
        v,org=build_grid(slot,side,r,R); nm=f"{HERO}_{FAM}_{r}_{name}"
        bl.MATS.clear(); hi,_=bl.mesh_g(v,nm+"_hi",RES,origin=tuple(org)); hi,_=bl.smooth_plate(hi,v,RES,tuple(org),iters=5,fac=0.6)
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
