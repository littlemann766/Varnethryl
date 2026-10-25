import bpy,bmesh,numpy as np,json,math,sys,os
from scipy import ndimage as nd
from scipy.spatial import cKDTree
OUT='/workspace/godot-art/volcano'; os.makedirs(OUT,exist_ok=True)
d=np.load('design.npz',allow_pickle=True); H=d['H']; R=148.0; N=H.shape[0]; D=2*R/(N-1)
P=d['P']; FW=d['FW']; moat=d['moat']
def hs(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float);sh=x.shape
    return nd.map_coordinates(H,[np.atleast_1d((y+R)/D),np.atleast_1d((x+R)/D)],order=1,mode="nearest").reshape(sh)
rng=np.random.default_rng(42)
kdp=cKDTree(P[:,:2])
def slope_at(x,y,e=1.0): return np.degrees(np.arctan(np.hypot(hs(x+e,y)-hs(x-e,y),hs(x,y+e)-hs(x,y-e))/(2*e)))
# ---- placements (shared by all LODs)
cand=rng.uniform(-140,140,(20000,2)); cx,cy=cand.T; cr=np.hypot(cx,cy)
pd=kdp.query(cand)[0]; fwv=nd.map_coordinates(FW,[(cy+R)/D,(cx+R)/D],order=0)
sl=slope_at(cx,cy)
ok=(pd>8)&(fwv<0.05)&(cr<140)&(cr>42)
small_i=np.nonzero(ok&(sl<32)&(sl>8))[0][:520]
big_i=np.nonzero(ok&(((cr>50)&(cr<64))|((cr>95)&(sl>20)))&(sl<45))[0][:75]
small=[(cx[i],cy[i],rng.uniform(0.35,1.5)) for i in small_i]
big=[(cx[i],cy[i],min(rng.uniform(2.2,6.0),(pd[i]-4.2)/1.35)) for i in big_i if pd[i]>7.5]
# vents: crater wall base, rim, outer slopes (not on path / flows)
TH1=math.radians(100); THF=TH1+math.radians(120)
vent_specs=[]
for a in [150,200,250,320]:   # crater wall base just outside moat
    t=math.radians(a); x,y=42*math.cos(t),42*math.sin(t)
    if kdp.query([x,y])[0]>7: vent_specs.append((x,y,'crater'))
for a,rr in [(20,80),(300,95),(60,110),(170,75)]:
    t=math.radians(a); x,y=rr*math.cos(t),rr*math.sin(t)
    if kdp.query([x,y])[0]>8: vent_specs.append((x,y,'flank'))
vent_specs.append((57*math.cos(THF),57*math.sin(THF),'spill'))
# ---- mesh helpers
def mkmesh(name,V,F,uv):
    me=bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co',V.astype(np.float32).ravel())
    me.loops.add(F.size); me.loops.foreach_set('vertex_index',F.astype(np.int32).ravel())
    me.polygons.add(len(F)); me.polygons.foreach_set('loop_start',np.arange(0,F.size,3,dtype=np.int32)); me.polygons.foreach_set('loop_total',np.full(len(F),3,np.int32))
    me.update(); me.validate()
    ul=me.uv_layers.new(); ul.data.foreach_set('uv',uv[F.ravel()].astype(np.float32).ravel())
    me.polygons.foreach_set('use_smooth',np.ones(len(F),bool))
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); return o
def grid(step,rmax=147.5,zf=None,mask=None):
    n=int(2*R/step)+1; g=np.linspace(-R,R,n); X,Y=np.meshgrid(g,g)
    Z=hs(X,Y) if zf is None else zf(X,Y)
    V=np.stack([X,Y,Z],-1).reshape(-1,3); idx=np.arange(n*n).reshape(n,n)
    a=idx[:-1,:-1];b=idx[:-1,1:];c=idx[1:,1:];e=idx[1:,:-1]
    rr=np.hypot(X,Y); keep=(rr[:-1,:-1]<rmax)|(rr[1:,1:]<rmax)|(rr[:-1,1:]<rmax)|(rr[1:,:-1]<rmax)
    if mask is not None: keep&=mask(X,Y)[:-1,:-1]|mask(X,Y)[1:,1:]
    F=np.concatenate([np.stack([a,b,c],-1)[keep],np.stack([a,c,e],-1)[keep]])
    used=np.unique(F); remap=-np.ones(n*n,int); remap[used]=np.arange(len(used))
    return V[used],remap[F]
def planar(V): return np.stack([(V[:,0]+R)/(2*R),(V[:,1]+R)/(2*R)],1)
def rock(x,y,s,sub,seed,crag=False):
    bm=bmesh.new(); bmesh.ops.create_icosphere(bm,subdivisions=sub,radius=1.0)
    r2=np.random.default_rng(seed); V=np.array([v.co[:] for v in bm.verts]); F=np.array([[v.index for v in f.verts] for f in bm.faces]); bm.free()
    k=r2.normal(size=(6,3)); w=np.ones(len(V))
    for kk in k: w+=0.12*np.sin(V@kk*2.2+r2.uniform(0,6))
    V=V*w[:,None]*np.array([1,r2.uniform(.7,1.1),r2.uniform(.45,.75)])
    if crag:
        for _ in range(7):
            nrm=r2.normal(size=3); nrm/=np.linalg.norm(nrm); dd=r2.uniform(0.55,0.85)
            p=V@nrm; V=V-np.maximum(0,p-dd)[:,None]*nrm
        V=V*np.array([1,1,r2.uniform(1.1,1.6)])
    V=np.where(V[:,2:3]<-0.35,V*[1,1,0]+[0,0,-0.35],V)  # flat-ish base
    rot=r2.uniform(0,6.28); c,s_=math.cos(rot),math.sin(rot); V=V@np.array([[c,-s_,0],[s_,c,0],[0,0,1]]).T
    zb=hs(x+np.array([0,s,-s,0,0]),y+np.array([0,0,0,s,-s])).min(); V=V*s+[x,y,zb+s*0.2]; return V,F
def vent(x,y,kind,seg):
    h=3.5 if kind!='flank' else 2.6; rb=2.6; rt=0.9
    rings=[(rb,0),(rb*0.8,h*0.25),(rt*1.4,h*0.75),(rt*1.15,h),(rt*0.8,h*0.95),(rt*0.7,h*0.3)]
    r2=np.random.default_rng(int(abs(x*7+y))); V=[]
    ring=[hs(x+rb*1.25*math.cos(t),y+rb*1.25*math.sin(t)) for t in np.linspace(0,6.28,12)]
    z0=float(min(ring))-0.6; h=h+float(max(ring)-min(ring))
    for ri,(rr,zz) in enumerate(rings):
        for k in range(seg):
            t=2*math.pi*k/seg; j=1+0.18*r2.standard_normal()
            V.append([x+rr*j*math.cos(t),y+rr*j*math.sin(t),z0+zz*(1+0.05*r2.standard_normal())])
    F=[]
    for ri in range(len(rings)-1):
        for k in range(seg):
            a=ri*seg+k;b=ri*seg+(k+1)%seg;c=b+seg;e=a+seg;F+=[[a,b,c],[a,c,e]]
    return np.array(V),np.array(F),(x,y,z0+h)
def mat_terrain(sz):
    m=bpy.data.materials.new('volcano_basalt'); m.use_nodes=True; nt=m.node_tree; b=nt.nodes['Principled BSDF']
    def img(f,col=True):
        im=bpy.data.images.load(f'/tmp/volc/{f}_{sz}.png'); 
        if not col: im.colorspace_settings.name='Non-Color'
        n=nt.nodes.new('ShaderNodeTexImage'); n.image=im; return n
    a=img('t_albedo'); nt.links.new(a.outputs[0],b.inputs['Base Color'])
    o=img('t_orm',False); sp=nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(o.outputs[0],sp.inputs[0]); nt.links.new(sp.outputs[1],b.inputs['Roughness']); b.inputs['Metallic'].default_value=0
    nm=img('t_normal',False); nn=nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nm.outputs[0],nn.inputs[1]); nt.links.new(nn.outputs[0],b.inputs['Normal'])
    e=img('t_emissive'); nt.links.new(e.outputs[0],b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value=3.0
    return m
def mat_lava(sz):
    m=bpy.data.materials.new('volcano_lava'); m.use_nodes=True; nt=m.node_tree; b=nt.nodes['Principled BSDF']
    a=nt.nodes.new('ShaderNodeTexImage'); a.image=bpy.data.images.load(f'/tmp/volc/l_albedo_{sz}.png'); nt.links.new(a.outputs[0],b.inputs['Base Color'])
    e=nt.nodes.new('ShaderNodeTexImage'); e.image=bpy.data.images.load(f'/tmp/volc/l_emissive_{sz}.png'); nt.links.new(e.outputs[0],b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value=6.0; b.inputs['Roughness'].default_value=0.6; return m
FLOOR=39.0
def mkmesh2(name,V,F,UVL,mi):
    me=bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co',V.astype(np.float32).ravel())
    me.loops.add(F.size); me.loops.foreach_set('vertex_index',F.astype(np.int32).ravel())
    me.polygons.add(len(F)); me.polygons.foreach_set('loop_start',np.arange(0,F.size,3,dtype=np.int32)); me.polygons.foreach_set('loop_total',np.full(len(F),3,np.int32))
    me.update(); me.validate()
    ul=me.uv_layers.new(); ul.data.foreach_set('uv',UVL.astype(np.float32).ravel())
    me.polygons.foreach_set('use_smooth',np.ones(len(F),bool)); me.polygons.foreach_set('material_index',mi.astype(np.int32))
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); return o
def boxuv(V,F,scale):
    T=V[F]; n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); ax=np.abs(n).argmax(1)
    u=np.where(ax[:,None]==0,T[:,:,1],T[:,:,0]); v=np.where(ax[:,None]==2,T[:,:,1],T[:,:,2])
    return np.stack([u,v],-1).reshape(-1,2)/scale, n
def mat_cliff(sz):
    m=bpy.data.materials.new('volcano_cliff'); m.use_nodes=True; nt=m.node_tree; b=nt.nodes['Principled BSDF']
    a=nt.nodes.new('ShaderNodeTexImage'); a.image=bpy.data.images.load(f'/tmp/volc/c_albedo_{sz}.png'); nt.links.new(a.outputs[0],b.inputs['Base Color'])
    n=nt.nodes.new('ShaderNodeTexImage'); n.image=bpy.data.images.load(f'/tmp/volc/c_normal_{sz}.png'); n.image.colorspace_settings.name='Non-Color'
    nn=nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(n.outputs[0],nn.inputs[1]); nt.links.new(nn.outputs[0],b.inputs['Normal'])
    b.inputs['Roughness'].default_value=0.88; b.inputs['Metallic'].default_value=0; return m
stones=[]
for k in range(0,len(P)-1,1):
    pass
sd=0.0; last=-9
cum=np.concatenate([[0],np.cumsum(np.hypot(*np.diff(P[:,:2],axis=0).T))])
for k in range(len(P)-1):
    if cum[k]-last<3.0: continue
    last=cum[k]; t=P[min(k+1,len(P)-1),:2]-P[k,:2]; t/=np.linalg.norm(t)+1e-9; nrm=np.array([-t[1],t[0]])
    for sgn in (-1,1):
        q=P[k,:2]+nrm*sgn*rng.uniform(3.35,3.7)+t*rng.uniform(-0.8,0.8)
        if np.hypot(*q)<37: continue
        stones.append((q[0],q[1],rng.uniform(0.22,0.42)))
def clearance(lst):
    return min(kdp.query([x,y])[0]-1.35*s for x,y,s in lst)
print('big rock min clearance to path centreline minus radius:',round(clearance(big),2),' small:',round(clearance(small),2))
def build(tag,step,big_sub,small_sub,small_n,stone_sub,tex,lavatex,ctex,vseg):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mt=mat_terrain(tex); mc=mat_cliff(ctex); ml=mat_lava(lavatex)
    V,F=grid(step)
    T=V[F]; n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); nz=np.abs(n[:,2])/np.linalg.norm(n,axis=1)
    gy_,gx_=np.gradient(nd.gaussian_filter(H,3.0),D); SL=np.degrees(np.arctan(np.hypot(gx_,gy_)))
    c=T.mean(1); sl=nd.map_coordinates(SL,[(c[:,1]+R)/D,(c[:,0]+R)/D],order=1)
    steep=(sl>48)|(nz<0.42)
    # same choice for both triangles of a grid quad
    uvp=planar(V)[F.ravel()]
    uvb,_=boxuv(V,F,6.0)
    UV=np.where(np.repeat(steep,3)[:,None],uvb,uvp); MI=steep.astype(int)
    parts=[rock(x,y,s,big_sub,i,crag=True) for i,(x,y,s) in enumerate(big)]
    if small_sub is not None: parts+=[rock(x,y,s,small_sub,1000+i) for i,(x,y,s) in enumerate(small[:small_n])]
    if stone_sub is not None: parts+=[rock(x,y,s,stone_sub,5000+i) for i,(x,y,s) in enumerate(stones)]
    vtops=[]
    for (x,y,k) in vent_specs:
        v,f,top=vent(x,y,k,vseg); parts.append((v,f)); vtops.append((top,k))
    VV=[V];FF=[F];UU=[UV];MM=[MI];off=len(V)
    for v,f in parts:
        u,_=boxuv(v,f,3.0); VV.append(v);FF.append(f+off);UU.append(u);MM.append(np.ones(len(f),int));off+=len(v)
    V=np.concatenate(VV);F=np.concatenate(FF)
    o=mkmesh2('volcano'+tag,V,F,np.concatenate(UU),np.concatenate(MM)); o.data.materials.append(mt); o.data.materials.append(mc)
    def lz(X,Y):
        fw=nd.map_coordinates(FW,[(Y+R)/D,(X+R)/D],order=1); h=hs(X,Y); rr=np.hypot(X,Y)
        return np.where(rr<41.5,FLOOR-1.5,h-0.15+0.7*fw)
    def lm(X,Y):
        mm=nd.binary_dilation(moat,iterations=3); fw=FW>0.12
        return nd.map_coordinates((mm|fw).astype(np.float32),[(Y+R)/D,(X+R)/D],order=0)>0.5
    LV,LF=grid(max(step,0.8),zf=lz,mask=lm)
    lo=mkmesh('volcano_lava'+tag,LV,LF,LV[:,:2]/12.0); lo.data.materials.append(ml)
    print(tag,'terrain',len(T),'parts',len(F)-len(T),'lava',len(LF))
    return o,lo,vtops,len(F)+len(LF)
for f,s in [('t_albedo',[4096,2048,1024]),('t_normal',[4096,2048,1024]),('t_orm',[2048,1024,512]),('t_emissive',[2048,1024,512]),('l_albedo',[1024,512,256]),('l_emissive',[1024,512,256]),('c_albedo',[1024,1024,512]),('c_normal',[1024,1024,512])]:
    from PIL import Image
    im=Image.open(f'/tmp/volc/{f}.png')
    for i,z in enumerate(s):
        key=[4096,2048,1024][i] if f.startswith('t_') else [1024,512,256][i] if f.startswith('l_') else ['h','m','l'][i]
        im.resize((z,z),Image.LANCZOS).save(f'/tmp/volc/{f}_{key}.png')
info={}
def export(path):
    bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',export_image_format='JPEG',export_jpeg_quality=88,export_apply=True,export_yup=True)
for tag,args in [('',(0.8,2,1,300,1,4096,1024,'h',20)),('_lod1',(1.3,1,None,0,None,2048,512,'m',12)),('_lod2',(2.0,1,None,0,None,1024,256,'l',8))]:
    o,lo,vt,tris=build(tag,*args)
    # markers (glTF nodes) for Lucky
    def emp(n,p):
        e=bpy.data.objects.new(n,None); e.location=p; bpy.context.scene.collection.objects.link(e)
    for i,(p,k) in enumerate(vt): emp(f'vent_{i}_{k}',p)
    emp('arena_center',(0,0,FLOOR)); emp('titan_spawn',(0,4,FLOOR)); emp('path_start',tuple(P[0])); emp('path_end',tuple(P[-1])); emp('smoke_plume',(0,0,82))
    export(f'{OUT}/volcano_titan{tag}.glb'); info[tag or 'high']={'tris':tris}; print(tag,tris)
# collision: terrain 2 m + big rocks coarse, one merged node
bpy.ops.wm.read_factory_settings(use_empty=True)
V,F=grid(2.0); off=len(V); VV=[V];FF=[F]
for i,(x,y,s) in enumerate(big):
    v,f=rock(x,y,s,1,i,crag=True); VV.append(v);FF.append(f+off);off+=len(v)
V=np.concatenate(VV);F=np.concatenate(FF); mkmesh('volcano_titan-colonly',V,F,planar(V)); export(f'{OUT}/volcano_titan_col.glb'); info['col']={'tris':len(F)}
json.dump({'tris':info,'vents':[(p,k) for p,k in vt],'big':len(big),'small':len(small)},open('/tmp/volc/build_info.json','w'),default=float)
print(info)
