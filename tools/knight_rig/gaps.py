# stage2 -> stage3: stray-fragment fix, lame rim overlap, blended cloth underlayer at every joint
import bpy,sys,json,math,numpy as np,bmesh
from mathutils import Vector,kdtree
G=sys.argv[-1]; OUT=f'/tmp/kr/{G}'
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/stage2.blend')
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; me=fig.data
BH={b.name:np.array(b.head_local) for b in ARM.data.bones}
gn=[g.name for g in fig.vertex_groups]
N=len(me.vertices); P=np.array([v.co[:] for v in me.vertices])
pid=np.zeros(N,np.int32); me.attributes['part'].data.foreach_get('value',pid)
bone=np.array([gn[max(v.groups,key=lambda g:g.weight).group] if len(v.groups) else 'hips' for v in me.vertices],dtype=object)
# connected islands after the bind-time cuts (each island = one rigid piece)
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
isl=-np.ones(N,int); k=0
for v in bm.verts:
    if isl[v.index]>=0: continue
    st=[v]; isl[v.index]=k
    while st:
        x=st.pop()
        for e in x.link_edges:
            o=e.other_vert(x)
            if isl[o.index]<0: isl[o.index]=k; st.append(o)
    k+=1
bm.free()
I={i:np.where(isl==i)[0] for i in range(k)}
ischain=lambda b:b.startswith(('wing','tabard'))
REP={'islands':k}
# ---- 1. stray fragments: small pieces adopt the bone of the big plates they touch
kd=kdtree.KDTree(N)
for i,p in enumerate(P): kd.insert(p,i)
kd.balance()
size={i:len(v) for i,v in I.items()}; moved=[]
for i,ids in I.items():
    if size[i]>=120: continue
    b0=bone[ids[0]]
    if ischain(b0) or any(s in b0 for s in ('index','middle','ring','pinky','thumb')): continue
    votes={}
    for vi in ids[::max(1,len(ids)//12)]:
        for co,j,d in kd.find_range(P[vi],0.025):
            if isl[j]==i or size[isl[j]]<300: continue
            votes[bone[j]]=votes.get(bone[j],0)+1
    if not votes: continue
    bb=max(votes,key=votes.get)
    armb=lambda b:b.startswith(('upperArm','shoulder'))
    okm=armb(b0) or (armb(bb) and b0 in ('chest','upperChest','spine2','neck'))
    if bb!=b0 and okm and votes[bb]>=0.6*sum(votes.values()):
        L_=[int(x) for x in ids]
        for g in fig.vertex_groups: g.remove(L_)
        fig.vertex_groups[bb].add(L_,1.0,'REPLACE')
        bone[ids]=bb; moved.append((int(i),b0,bb,int(size[i])))
# 1b. tassets / skirt plates that hang over a thigh follow that thigh (they were on hips/tabard and floated when the leg swung)
tas=[]
for i,ids in I.items():
    b0=bone[ids[0]]
    if b0 not in ('hips','spine2'): continue
    c=P[ids].mean(0)
    for X,sg in (('_L',1),('_R',-1)):
        if c[2]<BH['thigh'+X][2]+0.02 and sg*c[0]>=0.075:
            L_=[int(x) for x in ids]
            for g in fig.vertex_groups: g.remove(L_)
            fig.vertex_groups['thigh'+X].add(L_,1.0,'REPLACE'); bone[ids]='thigh'+X; tas.append((int(i),b0,'thigh'+X,int(size[i])))
REP['tassets_to_thigh']=len(tas); print('TASSETS',len(tas),tas[:10])
REP['fragments_rebound']=len(moved); REP['fragments_sample']=moved[:25]
print('MOVED',len(moved),moved[:20])
# ---- 2. lame rim overlap: grow each core plate ~5 mm about its own centroid (rigid scale, rest only)
grown=0
for i,ids in I.items():
    b=bone[ids[0]]
    if ischain(b) or size[i]<30 or any(s in b for s in ('index','middle','ring','pinky','thumb')): continue
    Q=P[ids]; c=Q.mean(0); ext=np.ptp(Q,0).max()
    s=min(1.04,1+0.010/max(ext,1e-3)); P[ids]=c+(Q-c)*s; grown+=1
for v,p in zip(me.vertices,P): v.co=p
REP['plates_grown']=grown
# ---- 3. underlayer tubes
plate=np.array([not ischain(b) for b in bone])
def L(a,b,t): return BH[a]+(BH[b]-BH[a])*t
up=np.array([0,0,1.0])
J={}
J['neck']=[(BH['neck']-np.array([0,0,0.05]),{'upperChest':1}),(BH['neck'],{'upperChest':.5,'neck':.5}),(L('neck','head',.6),{'neck':1}),(BH['head']+np.array([0,0,0.03]),{'head':1})]
J['waist']=[(BH['spine2']-np.array([0,0,0.07]),{'hips':1}),(BH['spine2'],{'hips':.5,'spine2':.5}),(BH['chest'],{'spine2':.5,'chest':.5}),(BH['chest']+np.array([0,0,0.06]),{'chest':1})]
for X in ('_L','_R'):
    J['shoulder'+X]=[(L('shoulder'+X,'upperArm'+X,.45),{'shoulder'+X:1}),(BH['upperArm'+X],{'shoulder'+X:.5,'upperArm'+X:.5}),(L('upperArm'+X,'foreArm'+X,.28),{'upperArm'+X:1})]
    J['elbow'+X]=[(L('upperArm'+X,'foreArm'+X,.70),{'upperArm'+X:1}),(BH['foreArm'+X],{'upperArm'+X:.5,'foreArm'+X:.5}),(L('foreArm'+X,'hand'+X,.28),{'foreArm'+X:1})]
    J['wrist'+X]=[(L('foreArm'+X,'hand'+X,.55),{'foreArm'+X:.6,'foreArm_twist'+X:.4}),(BH['hand'+X],{'foreArm_twist'+X:.5,'hand'+X:.5}),(L('hand'+X,'fingers'+X,.45),{'hand'+X:1})]
    J['hip'+X]=[(BH['thigh'+X]+np.array([0,0,0.07]),{'hips':1}),(BH['thigh'+X],{'hips':.5,'thigh'+X:.5}),(L('thigh'+X,'shin'+X,.28),{'thigh'+X:1})]
    J['knee'+X]=[(L('thigh'+X,'shin'+X,.70),{'thigh'+X:1}),(BH['shin'+X],{'thigh'+X:.5,'shin'+X:.5}),(L('shin'+X,'foot'+X,.25),{'shin'+X:1})]
    J['ankle'+X]=[(L('shin'+X,'foot'+X,.80),{'shin'+X:1}),(BH['foot'+X],{'shin'+X:.5,'foot'+X:.5}),(L('foot'+X,'toe'+X,.35),{'foot'+X:1})]
NS=20; PV=P[plate]
newv=[];neww=[];newf=[]; fit={}; ctr=[]
for nm,st in J.items():
    pts=np.array([s[0] for s in st]); seg=np.linalg.norm(np.diff(pts,axis=0),axis=1); cum=np.r_[0,np.cumsum(seg)]
    nr=max(6,int(cum[-1]/0.02)+1); tt=np.linspace(0,cum[-1],nr)
    rmax=0.32 if nm in ('waist','neck') else 0.17
    base=len(newv); radii=[]
    for r,s in enumerate(tt):
        j=min(np.searchsorted(cum,s,side='right')-1,len(pts)-2); f=(s-cum[j])/max(seg[j],1e-9)
        c=pts[j]+(pts[j+1]-pts[j])*f; t=(pts[j+1]-pts[j])/max(seg[j],1e-9)
        w={}
        for b,x in st[j][1].items(): w[b]=w.get(b,0)+x*(1-f)
        for b,x in st[j+1][1].items(): w[b]=w.get(b,0)+x*f
        ref=up if abs(t@up)<0.9 else np.array([0,-1.0,0]); u=np.cross(t,ref); u/=np.linalg.norm(u); v_=np.cross(t,u)
        d=PV-c; ax=d@t; m=np.abs(ax)<0.03; dr=d[m]-ax[m][:,None]*t; rr=np.linalg.norm(dr,axis=1); m2=(rr<rmax)&(rr>0.012); dr=dr[m2]; rr=rr[m2]
        ang=np.arctan2(dr@v_,dr@u); R=np.zeros(NS)
        for q in range(NS):
            a=-math.pi+2*math.pi*q/NS; da=np.abs((ang-a+math.pi)%(2*math.pi)-math.pi); sel=da<2.2*math.pi/NS
            R[q]=np.percentile(rr[sel],12)*0.90 if sel.sum()>=4 else np.nan
        if np.all(np.isnan(R)): R[:]=0.03
        R=np.where(np.isnan(R),np.nanmedian(R),R); R=np.maximum(R,0.018)
        R=(np.roll(R,1)+2*R+np.roll(R,-1))/4; radii.append(R)
        for q in range(NS):
            a=-math.pi+2*math.pi*q/NS; newv.append(c+R[q]*(math.cos(a)*u+math.sin(a)*v_)); neww.append(w); ctr.append(c)
    radii=np.array(radii); sm=radii.copy()
    for r in range(1,nr-1): sm[r]=(radii[r-1]+2*radii[r]+radii[r+1])/4
    for r in range(nr):
        for q in range(NS):
            vi=base+r*NS+q; c0=newv[vi]; # rescale toward ring centre to smoothed radius
    for r in range(nr-1):
        for q in range(NS):
            a=base+r*NS+q; b=base+r*NS+(q+1)%NS; newf.append((a,b,b+NS,a+NS))
    fit[nm]={'rings':int(nr),'r_mean_cm':round(float(radii.mean())*100,2)}
# hide in rest: shrink any underlayer vertex that a view ray can see past the plates
from mathutils.bvhtree import BVHTree
me.calc_loop_triangles(); PTRI=[t.vertices[:] for t in me.loop_triangles]
tree=BVHTree.FromPolygons([tuple(x) for x in P],PTRI)
NV=np.array(newv); C=np.array(ctr)
DIRS=[]
for el in (0,20,40):
    for az in range(0,360,30): DIRS.append(np.array([math.cos(math.radians(el))*math.cos(math.radians(az)),math.cos(math.radians(el))*math.sin(math.radians(az)),math.sin(math.radians(el))]))
DIRS=np.array(DIRS)
def exposed(NV):
    ex=np.zeros(len(NV),bool)
    for i,v in enumerate(NV):
        n=v-C[i]; n/=max(np.linalg.norm(n),1e-9)
        for d in DIRS[DIRS@n>0.25]:
            if tree.ray_cast(Vector(v+d*0.001),Vector(d),3.0)[0] is None: ex[i]=True; break
    return ex
hist=[]
for it in range(7):
    ex=exposed(NV); hist.append(int(ex.sum()))
    if not ex.any(): break
    # spread shrink to ring neighbours for smoothness
    r=np.linalg.norm(NV-C,axis=1); f=np.where(ex,0.82,1.0); r2=np.maximum(r*f,0.010); NV=C+(NV-C)*(r2/np.maximum(r,1e-9))[:,None]
ex=exposed(NV); hist.append(int(ex.sum()))
r=np.linalg.norm(NV-C,axis=1); NV[ex]=C[ex]+(NV[ex]-C[ex])*(0.004/np.maximum(r[ex],1e-9))[:,None]   # still-visible verts collapse onto the axis
REP['under_collapsed']=int(ex.sum()); COLL=ex.copy(); ex=exposed(NV); hist.append(int(ex.sum())); newv=list(NV)
REP['under_exposed_rest_iter']=hist; REP['under_exposed_rest_final']=int(ex.sum()); REP['under_verts_total']=len(NV)
print('EXPOSED',hist,len(NV))
nmv=[];[nmv.extend([k]*(v['rings']*NS)) for k,v in fit.items()]
import collections;print(collections.Counter(np.array(nmv)[ex]),collections.Counter(nmv))
REP['underlayer']=fit
um=bpy.data.meshes.new('under'); um.from_pydata([tuple(x) for x in newv],[],newf); um.update()
uo=bpy.data.objects.new('under',um); bpy.context.collection.objects.link(uo)
for b in ARM.data.bones: uo.vertex_groups.new(name=b.name)
for i,w in enumerate(neww):
    s=sum(w.values())
    for b,x in w.items():
        if x>1e-3: uo.vertex_groups[b].add([i],x/s,'ADD')
mat=bpy.data.materials.new('gambeson'); mat.use_nodes=True; bs=mat.node_tree.nodes['Principled BSDF']
bs.inputs['Base Color'].default_value=(0.035,0.03,0.027,1); bs.inputs['Roughness'].default_value=0.85; bs.inputs['Metallic'].default_value=0.1
mat.use_backface_culling=False; um.materials.append(mat)
for p in um.polygons: p.use_smooth=True
# make sure underlayer has the uv / attributes of the figure so join is clean
um.uv_layers.new(name=me.uv_layers[0].name)
ab=me.attributes['blended']
# join
for x in bpy.data.objects: x.select_set(False)
uo.select_set(True); fig.select_set(True); bpy.context.view_layer.objects.active=fig
nf_before=len(me.polygons); nv_before=len(me.vertices)
if len(me.materials)<2: me.materials.append(mat)
bpy.ops.object.join(); me=fig.data
mi=np.zeros(len(me.polygons),int); me.polygons.foreach_get('material_index',mi)
bl=np.zeros(len(me.vertices),np.int32); bl[nv_before:]=1
bl[nv_before:][COLL]=2
me.attributes['blended'].data.foreach_set('value',bl)
pa=np.zeros(len(me.vertices),np.int32); me.attributes['part'].data.foreach_get('value',pa); pa[nv_before:]=-1; me.attributes['part'].data.foreach_set('value',pa)
REP.update(under_verts=len(me.vertices)-nv_before,under_faces=len(me.polygons)-nf_before,mat_idx=sorted(set(mi.tolist())))
print('REP',json.dumps(REP)[:1500]); json.dump(REP,open(OUT+'/gaps_report.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/stage3.blend')
