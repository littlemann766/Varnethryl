"""Beth land1: terrain refinement (mountain ridges/erosion on steep ground only), biome colour blending, terrain mask in COLOR.a.
Reads Lucky's game tidewrack meshes READ-ONLY, writes to OUT/<stage>/meshes/. Walkable ground (<24 deg), docks, POIs, paths, props untouched."""
import sys,os,json,numpy as np,trimesh
from scipy.spatial import cKDTree
sys.path.insert(0,os.path.dirname(__file__)); sys.path.insert(0,'/tmp/land1w')
from glbio import write_glb
from noise import fbm,ridged
from files import G,REG,files,is_terrain
OUT=sys.argv[1]; ONLY=sys.argv[2:] 
L=json.load(open(G+'landings.json')); M=json.load(open(G+'stage5_manifest.json'))
CELL=2.0; X0,Z0,NX=-3300.0,-3300.0,3300
def gidx(xz): return np.clip(((xz-[X0,Z0])/CELL).astype(int),0,NX-1)
def load(f):
    s=trimesh.load(G+f,force='mesh'); s.merge_vertices(); return s
def terrain_faces(s,b):
    if not '_isl_' in b: return np.ones(len(s.faces),bool)
    m=np.zeros(len(s.faces),bool)
    for c in trimesh.graph.connected_components(s.face_adjacency,min_len=1):
        if np.ptp(s.vertices[s.faces[c].ravel()][:,[0,2]],0).max()>60: m[c]=True
    return m
def stamp(grid,xz,r):
    k=int(np.ceil(r/CELL)); ij=gidx(xz)
    for dx in range(-k,k+1):
        for dz in range(-k,k+1):
            if dx*dx+dz*dz<=k*k+1: grid[np.clip(ij[:,0]+dx,0,NX-1),np.clip(ij[:,1]+dz,0,NX-1)]=True
def keepout_grids(r):
    """props: every non-terrain triangle of the region (dilated 4 m); keep: landings, POIs, routes, bridges; isl: island patch footprint"""
    props=np.zeros((NX,NX),bool); keep=np.zeros((NX,NX),bool); isl=np.zeros((NX,NX),bool)
    for f in files(r):
        b=f.split('/')[-1][:-4]
        if b.endswith('_glow') or '_ice_floes' in b: continue
        s=load(f); tm=terrain_faces(s,b) if is_terrain(b) else np.zeros(len(s.faces),bool)
        if (~tm).any():
            tri=s.vertices[s.faces[~tm]]; pts=np.concatenate([tri.mean(1),tri.reshape(-1,3)])[:, [0,2]]
            stamp(props,pts,4.0)
        if '_isl_' in b and tm.any():
            stamp(isl,s.vertices[np.unique(s.faces[tm])][:,[0,2]],2.0)
    for k,v in L.items():
        if v['region']!=r: continue
        for key in ('shore','moor'): stamp(keep,np.array([[v[key][0],v[key][2]]]),30.0)
        if v.get('spawn'): stamp(keep,np.array([[v['spawn'][0],v['spawn'][2]]]),20.0)
    for k,I in M['islands'].items():
        if I['region']!=r: continue
        stamp(keep,np.array([[I['pier_head'][0],I['pier_head'][2]]]),30.0)
        for po in I['pois']:
            stamp(keep,np.array([[po['pos'][0],po['pos'][2]]]),po.get('radius',6)+8)
            if po.get('route'): stamp(keep,np.array(po['route'])[:,[0,2]],4.5)
        for br in I.get('bridges',[]): stamp(keep,np.array([[br['a'][0],br['a'][2]],[br['b'][0],br['b'][2]]]),12)
        if I.get('path'):
            p=np.array(I['path']); p=p.reshape(-1,3) if p.ndim>1 else None
            if p is not None: stamp(keep,p[:,[0,2]],4.5)
    return props,keep,isl
def slope_deg(n): return np.degrees(np.arccos(np.clip(np.abs(n[:,1]),0,1)))
def refine(V,F,C,A,mark):
    """red-green midpoint refinement of marked faces (closure: faces with >=2 split edges split fully)"""
    E=np.sort(np.stack([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],1),axis=2)  # (nf,3,2)
    key=E[:,:,0].astype(np.int64)*(len(V)+1)+E[:,:,1]
    split=set(key[mark].ravel().tolist())
    while True:
        s=np.isin(key,np.fromiter(split,np.int64)).sum(1)
        add=(s==2)
        if not add.any(): break
        split.update(key[add].ravel().tolist())
    sk=np.fromiter(split,np.int64); sk.sort()
    a=sk//(len(V)+1); b=sk%(len(V)+1)
    mid=np.arange(len(V),len(V)+len(sk))
    V2=np.concatenate([V,(V[a]+V[b])/2]); C2=np.concatenate([C,(C[a]+C[b])/2]); A2=np.concatenate([A,np.minimum(A[a],A[b])])
    def m(e): 
        i=np.searchsorted(sk,e); ok=(i<len(sk))&(sk[np.minimum(i,len(sk)-1)]==e); return np.where(ok,mid[np.minimum(i,len(sk)-1)],-1)
    k01,k12,k20=[F[:,i].astype(np.int64)*0 for i in range(3)]
    def ek(u,v): lo=np.minimum(u,v); hi=np.maximum(u,v); return lo.astype(np.int64)*(len(V)+1)+hi
    m01=m(ek(F[:,0],F[:,1])); m12=m(ek(F[:,1],F[:,2])); m20=m(ek(F[:,2],F[:,0]))
    out=[]; fa=[]
    n=(m01>=0).astype(int)+(m12>=0)+(m20>=0)
    for i in np.nonzero(n==0)[0]: pass
    out.append(F[n==0]); fa.append(np.nonzero(n==0)[0])
    s3=n==3; f=F[s3]; a,b_,c=m01[s3],m12[s3],m20[s3]
    out+= [np.stack([f[:,0],a,c],1),np.stack([a,f[:,1],b_],1),np.stack([c,b_,f[:,2]],1),np.stack([a,b_,c],1)]; fa+=[np.nonzero(s3)[0]]*4
    s1=n==1
    for mm,(i0,i1,i2) in ((m01,(0,1,2)),(m12,(1,2,0)),(m20,(2,0,1))):
        sel=s1&(mm>=0); f=F[sel]; x=mm[sel]
        out+=[np.stack([f[:,i0],x,f[:,i2]],1),np.stack([x,f[:,i1],f[:,i2]],1)]; fa+=[np.nonzero(sel)[0]]*2
    return V2,np.concatenate(out).astype(np.int64),C2,A2,np.concatenate(fa)
def vnormals(V,F):
    fn=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]); N=np.zeros_like(V)
    for i in range(3): np.add.at(N,F[:,i],fn)
    N/=np.linalg.norm(N,axis=1,keepdims=True)+1e-12; N[N[:,1]<0]*=-1; return N
def process(r,f,props,keep,isl,seed):
    b=f.split('/')[-1][:-4]; s=load(f)
    V=np.array(s.vertices,np.float64); F=np.array(s.faces,np.int64); C=np.array(s.visual.vertex_colors,np.float64)/255.0
    tm=terrain_faces(s,b); A=np.zeros(len(V)); A[np.unique(F[tm])]=1.0
    nf0=len(F)
    fixed=props[tuple(gidx(V[:,[0,2]]).T)]|keep[tuple(gidx(V[:,[0,2]]).T)]
    if '_isl_' not in b: fixed|=isl[tuple(gidx(V[:,[0,2]]).T)]   # base ground under an island patch stays put (patch rim tucks 0.25 m under it)
    # boundary verts stay (tile seams)
    ed=np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),1); u,cnt=np.unique(ed,axis=0,return_counts=True); bv=np.unique(u[cnt==1]); fixed[bv]=True
    if '_isl_' in b: fixed[:]=True   # hand-built island patches (arches, POIs, benches): colour/mask only, no reshaping
    fn0=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]); rn=np.zeros_like(V)
    for i in range(3): np.add.at(rn,F[:,i],fn0)
    rn/=np.linalg.norm(rn,axis=1,keepdims=True)+1e-12; fixed|=rn[:,1]<0.15   # overhangs / arches / sheer faces keep their shape
    for lvl,(sl,ymin) in enumerate([(26,4.0),(36,12.0)]):
        fn=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]); fn/=np.linalg.norm(fn,axis=1,keepdims=True)+1e-12
        el=np.linalg.norm(V[F[:,1]]-V[F[:,0]],axis=1)
        mk=(A[F].min(1)>0.5)&(slope_deg(fn)>sl)&(V[F][:,:,1].max(1)>ymin)&(~fixed[F].any(1))&(el>(1.2 if '_isl_' in b else 3.0))
        if not mk.any(): continue
        nv=len(V); V,F,C,A,_=refine(V,F,C,A,mk)
        # new midpoints inherit 'fixed' only if both ends fixed -> recompute: fixed if any end fixed (safe)
        fx=np.zeros(len(V),bool); fx[:nv]=fixed
        ed=np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),1); u,cnt=np.unique(ed,axis=0,return_counts=True); fx[np.unique(u[cnt==1])]=True
        fx[nv:]|=props[tuple(gidx(V[nv:,[0,2]]).T)]|keep[tuple(gidx(V[nv:,[0,2]]).T)]
        if '_isl_' not in b: fx[nv:]|=isl[tuple(gidx(V[nv:,[0,2]]).T)]
        fixed=fx
    N=vnormals(V,F); sd=slope_deg(N)
    # displacement weight: steep + elevated + land + not fixed; walkable ground (<24 deg) weight 0
    w=np.clip((sd-24)/16,0,1)*np.clip((V[:,1]-3)/10,0,1)*(A>0.5)*(~fixed)
    sc=1.0 if '_isl_' in b else 2.6
    P=V*[1/22.0,1/9.0,1/22.0]   # gullies: stretched vertically
    rid=ridged(V/38.0,4,seed); gul=fbm(P,3,seed+7); strata=np.sin(V[:,1]*0.55+fbm(V/30.0,2,seed+3)*3.0)
    hn=N.copy(); hn[:,1]=0; hn/=np.linalg.norm(hn,axis=1,keepdims=True)+1e-9
    off=(rid-0.35)*2.2+gul*1.4+strata*0.45
    V=V+(hn*(off*sc*w)[:,None])+np.array([0,1,0])*((rid-0.3)*1.2*sc*w*np.clip((V[:,1]-15)/25,0,1))[:,None]
    N=vnormals(V,F); sd=slope_deg(N)
    # colour: world-space gaussian blend of the biome colours (soft region borders), terrain only
    t=np.nonzero(A>0.5)[0]
    if len(t):
        kd=cKDTree(V[t][:,[0,2]]); rad=6.0 if '_isl_' in b else 16.0
        nb=kd.query_ball_point(V[t][:,[0,2]],rad)
        Ct=C[t,:3]; blur=np.array([Ct[n].mean(0) if len(n) else Ct[i] for i,n in enumerate(nb)])
        # keep paths: verts whose colour differs a lot from blur but sit in a 'keep' cell stay sharp
        kk=keep[tuple(gidx(V[t][:,[0,2]]).T)]
        mix=np.where(kk,0.25,0.6)[:,None]
        C[t,:3]=Ct*(1-mix)+blur*mix
        # rock on refined cliffs: pull toward the region's rock colour where steep
        rock={'A':[0.36,0.34,0.31],'B':[0.5,0.47,0.43],'frost':[0.55,0.6,0.66],'ash':[0.14,0.13,0.13]}[r]
        rk=np.clip((sd[t]-30)/18,0,1)[:,None]*0.55
        C[t,:3]=C[t,:3]*(1-rk)+np.array(rock)*rk
    C[:,3]=A
    return b,V,F,C,N,nf0,fixed
def main():
    stats={}
    for r in REG:
        if ONLY and r not in ONLY: continue
        props,keep,isl=keepout_grids(r)
        np.savez_compressed(f'/tmp/land1w/grids_{r}.npz',props=np.packbits(props),keep=np.packbits(keep),isl=np.packbits(isl))
        for i,f in enumerate(files(r)):
            b=f.split('/')[-1][:-4]
            if not is_terrain(b): continue
            b,V,F,C,N,nf0,fixed=process(r,f,props,keep,isl,i*11+3)
            od=OUT+'/'+REG[r][0]; os.makedirs(od,exist_ok=True)
            write_glb(od+b+'.glb',V,F,C,N,b)
            # lod1: original lod1 geometry, colours+mask transferred from the new High (nearest vertex)
            lo=G+REG[r][0]+b+'_lod1.glb'; nl=None
            if os.path.exists(lo):
                s=trimesh.load(lo,force='mesh'); s.merge_vertices(); kd=cKDTree(V); _,ii=kd.query(s.vertices)
                Cl=C[ii].copy(); write_glb(od+b+'_lod1.glb',s.vertices,s.faces,Cl,vnormals(np.array(s.vertices),np.array(s.faces)),b+'_lod1'); nl=len(s.faces)
            stats[b]=dict(region=r,tris_before=nf0,tris_high=len(F),tris_lod1=nl,moved_verts=int((~fixed).sum()))
            print(r,b,nf0,'->',len(F),'lod1',nl,flush=True)
    json.dump(stats,open(OUT+'/terrain_stats_'+('_'.join(ONLY) or 'all')+'.json','w'),indent=1)
main()
