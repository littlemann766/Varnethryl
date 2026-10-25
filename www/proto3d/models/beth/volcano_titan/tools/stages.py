import json
exec(open('/tmp/volc/build.py').read().split("info={}")[0])
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point
ARR=33.2
rg_=np.random.default_rng(77); seeds=rg_.uniform(-36,36,(900,2))   # same seeds as the painted crust in t_albedo
vor=Voronoi(np.vstack([seeds,[[0,500],[0,-500],[500,0],[-500,0]]]))
disc=Point(0,0).buffer(ARR,resolution=32)
cells=[]
for si in range(len(seeds)):
    reg=vor.regions[vor.point_region[si]]
    if -1 in reg or not reg: continue
    pg=Polygon(vor.vertices[reg]).intersection(disc)
    if pg.is_empty or pg.area<0.3 or pg.geom_type!='Polygon': continue
    cells.append((si,pg))
print('cells',len(cells))
cen=np.array([[p.centroid.x,p.centroid.y] for _,p in cells])
# stage 2: ~25% sunk (clustered, never the spawn plate or bridge landing)
spawn=np.array([0,4.0]); land=P[-1,:2]
noise=nd.gaussian_filter(np.random.default_rng(123).random((N,N)).astype(np.float32),10); nz_=lambda x,y: noise[int((y+R)/D),int((x+R)/D)]
sc2=np.array([nz_(x,y) for x,y in cen])
safe=(np.hypot(*(cen-spawn).T)<5)|(np.hypot(*(cen-land*ARR/np.linalg.norm(land)).T)<5)
th2=np.quantile(sc2[~safe],0.75); sunk2=(sc2>=th2)&~safe
# stage 3: 6 islands + loose stepping stones
isl=np.array([[0,4],[-17,14],[16,15],[-18,-13],[15,-16],[0,-25]],float)
lr=land*ARR/np.linalg.norm(land)*0.93
keep3=np.zeros(len(cells),bool)
for c in isl: keep3|=np.hypot(*(cen-c).T)<6.5
keep3|=np.hypot(*(cen-lr).T)<3.5
# loose links: every other cell along lines island0->others and landing->nearest
def link(a,b):
    global keep3
    for t in np.linspace(0,1,12)[1:-1:2]:
        q=a+(b-a)*t; k=np.argmin(np.hypot(*(cen-q).T)); keep3[k]=True
for c in isl[1:]: link(isl[0],c)
link(lr,isl[np.argmin(np.hypot(*(isl-lr).T))])
STG={1:dict(gap=0.12,keep=np.ones(len(cells),bool),tilt=0.0),2:dict(gap=0.38,keep=~sunk2,tilt=0.05),3:dict(gap=0.55,keep=keep3,tilt=0.09)}
def plate(pg,gap,lvl,seed,tilt):
    ip=pg.buffer(-gap/2,join_style=2)
    if ip.is_empty or ip.geom_type!='Polygon': return None
    if lvl==2: ip=ip.simplify(0.6) 
    ring=np.array(ip.exterior.coords)[:-1]
    if len(ring)<3: return None
    r2=np.random.default_rng(seed); c=ring.mean(0); n=len(ring)
    tx,ty=r2.normal(0,tilt,2)
    top=lambda p,k: FLOOR+0.05+(p[0]-c[0])*tx+(p[1]-c[1])*ty+k*r2.uniform(-0.06,0.06)
    V=[];F=[]
    if lvl==0:
        rings=[ring, c+(ring-c)*0.93, c+(ring-c)*0.55]  # bevel ring, mid ring
        V.append([c[0],c[1],top(c,1)+0.04])
        for ri,rg in enumerate(rings[::-1]):
            for p in rg: V.append([p[0],p[1],top(p,1)-(0.10 if ri==2 else 0)])
        # fan centre->mid
        for k in range(n): F.append([0,1+k,1+(k+1)%n])
        for a in range(2):
            o1=1+a*n;o2=1+(a+1)*n
            for k in range(n): F+= [[o1+k,o2+k,o2+(k+1)%n],[o1+k,o2+(k+1)%n,o1+(k+1)%n]]
        edge0=1+2*n
    else:
        V.append([c[0],c[1],top(c,0)])
        for p in ring: V.append([p[0],p[1],top(p,0)])
        for k in range(n): F.append([0,1+k,1+(k+1)%n])
        edge0=1
    if lvl==2:
        V=np.array(V);F=np.array(F);T=V[F];nn=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);fl=nn[:,2]<0;F[fl]=F[fl][:,::-1];return V,F
    b0=len(V)
    for p in ring: V.append([p[0],p[1],FLOOR-1.7])
    for k in range(n):
        a=edge0+k;bq=edge0+(k+1)%n; F+=[[a,b0+k,b0+(k+1)%n],[a,b0+(k+1)%n,bq]]
    V=np.array(V);F=np.array(F)
    # orient top faces up
    T=V[F]; nn=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0])
    out=np.einsum('ij,ij->i',nn[:,:2],(T.mean(1)[:,:2]-c))
    flip=np.where(np.abs(nn[:,2])>1e-6,nn[:,2]<0,out<0); F[flip]=F[flip][:,::-1]
    return V,F
def export(path):
    bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',export_image_format='JPEG',export_jpeg_quality=88,export_apply=True,export_yup=True,export_vertex_color='ACTIVE')
G=lambda p:[round(float(p[0]),2),round(float(p[2]),2),round(float(-p[1]),2)]
report={}
for st,cfg in STG.items():
    report[st]={}
    for lvl,tag,tex,ctex in [(0,'',4096,'h'),(1,'_lod1',2048,'m'),(2,'_lod2',1024,'l')]:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mt=mat_terrain(tex); mc=mat_cliff(ctex)
        VV=[];FF=[];UU=[];MM=[];off=0
        for i,(si,pg) in enumerate(cells):
            if not cfg['keep'][i]: continue
            r_=plate(pg,cfg['gap'],lvl,si,cfg['tilt'])
            if r_ is None: continue
            v,f=r_; T=v[f]; nn=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); side=np.abs(nn[:,2])/np.linalg.norm(nn,axis=1)<0.5
            ub,_=boxuv(v,f,3.0); up=planar(v)[f.ravel()]
            UU.append(np.where(np.repeat(side,3)[:,None],ub,up)); MM.append(side.astype(int))
            VV.append(v);FF.append(f+off);off+=len(v)
        V=np.concatenate(VV);F=np.concatenate(FF)
        o=mkmesh2(f'arena_stage{st}{tag}',V,F,np.concatenate(UU),np.concatenate(MM))
        ca=o.data.color_attributes.new('Col','BYTE_COLOR','CORNER'); ca.data.foreach_set('color',np.ones(F.size*4,np.float32))
        o.data.materials.append(mt); o.data.materials.append(mc)
        export(f'{OUT}/volcano_arena_stage{st}{tag}.glb'); report[st][tag or 'high']=len(F)
    # collision (lod1 geometry, merged)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    VV=[];FF=[];off=0
    for i,(si,pg) in enumerate(cells):
        if not cfg['keep'][i]: continue
        r_=plate(pg,cfg['gap'],1,si,cfg['tilt'])
        if r_ is None: continue
        v,f=r_; VV.append(v);FF.append(f+off);off+=len(v)
    V=np.concatenate(VV);F=np.concatenate(FF); mkmesh(f'arena_stage{st}-colonly',V,F,planar(V)); export(f'{OUT}/volcano_arena_stage{st}_col.glb')
    # hazard: arena disc minus kept plates (lava), flat mesh at lava level + polygon list
    from shapely.ops import unary_union
    kept=unary_union([pg.buffer(-cfg['gap']/2,join_style=2) for i,(si,pg) in enumerate(cells) if cfg['keep'][i]])
    hz=disc.difference(kept.buffer(0.0))
    polys=[g for g in (hz.geoms if hasattr(hz,'geoms') else [hz]) if g.area>0.5]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import shapely
    VV=[];FF=[];off=0
    for g_ in polys:
        for tri in shapely.delaunay_triangles(g_).geoms:
            if not tri.representative_point().within(g_.buffer(1e-6)): continue
            c=np.array(tri.exterior.coords)[:3]; VV.append(np.c_[c,np.full(3,FLOOR-0.95)]); FF.append(np.array([[off,off+1,off+2]])); off+=3
    V=np.concatenate(VV);F=np.concatenate(FF); mkmesh(f'arena_stage{st}_lava_hazard',V,F,planar(V)); export(f'{OUT}/volcano_arena_stage{st}_hazard.glb')
    big_hz=sorted(polys,key=lambda g:-g.area)
    report[st].update(plates=int(cfg['keep'].sum()),hazard_area_m2=round(hz.area,1),plate_area_m2=round(kept.area,1),
        hazard_polys=[[G((x,y,FLOOR-0.95)) for x,y in list(g.simplify(0.3).exterior.coords)] for g in big_hz if g.area>2.0])
json.dump(report,open('/tmp/volc/stages_info.json','w'))
print({k:{kk:v for kk,v in r.items() if kk!='hazard_polys'} for k,r in report.items()})
