# SDF sculptures (marching cubes + quadric decimation) for statues; cached per (name,target tris)
import numpy as np, functools
from skimage.measure import marching_cubes
import pymeshlab
def smin(a,b,k):
    h=np.clip(0.5+0.5*(b-a)/k,0,1); return b*(1-h)+a*h-k*h*(1-h)
def ell(P,c,r):
    q=(P-np.array(c))/np.array(r); k0=np.linalg.norm(q,axis=-1); k1=np.linalg.norm(q/np.array(r),axis=-1)
    return k0*(k0-1)/(k1+1e-9)
def cap(P,a,b,r,r2=None):
    a=np.array(a,float);b=np.array(b,float); pa=P-a; ba=b-a; h=np.clip((pa@ba)/(ba@ba),0,1)
    rr=r if r2 is None else r+(r2-r)*h
    return np.linalg.norm(pa-h[...,None]*ba,axis=-1)-rr
def lion_sdf(P):
    # seated lion facing +z, origin at base centre, ~2.6 m tall (scale 1)
    d=ell(P,(0,0.75,-0.25),(0.62,0.7,0.85))                      # haunches/body
    d=smin(d,ell(P,(0,1.35,0.2),(0.5,0.75,0.5)),0.25)             # chest, upright
    for s in(-1,1):
        d=smin(d,cap(P,(s*0.24,1.2,0.45),(s*0.25,0.15,0.55),0.15,0.12),0.12)   # forelegs
        d=smin(d,ell(P,(s*0.25,0.1,0.68),(0.17,0.11,0.24)),0.08)               # front paws
        d=smin(d,ell(P,(s*0.48,0.45,-0.25),(0.22,0.42,0.55)),0.15)             # hind thighs
        d=smin(d,ell(P,(s*0.5,0.09,0.12),(0.17,0.1,0.32)),0.08)                # hind paws
    # mane: lumpy sphere
    q=P-np.array([0,2.0,0.3]); rr=np.linalg.norm(q,axis=-1)+1e-9
    lump=0.05*np.sin(9*q[...,0]/rr*3)*np.sin(9*q[...,1]/rr*3)*np.sin(7*q[...,2]/rr*3)
    d=smin(d,ell(P,(0,2.0,0.25),(0.62,0.66,0.55))-lump,0.2)
    d=smin(d,ell(P,(0,2.05,0.62),(0.33,0.36,0.33)),0.12)          # face
    d=smin(d,ell(P,(0,1.95,0.88),(0.2,0.17,0.2)),0.08)            # muzzle
    d=smin(d,ell(P,(0,1.83,0.82),(0.15,0.08,0.15)),0.05)          # jaw
    for s in(-1,1): d=smin(d,ell(P,(s*0.25,2.45,0.35),(0.09,0.11,0.06)),0.05)  # ears
    d=smin(d,cap(P,(0,0.3,-1.0),(0.55,0.12,-0.55),0.07),0.08)     # tail
    d=smin(d,ell(P,(0.62,0.12,-0.45),(0.12,0.09,0.12)),0.05)
    # eye sockets / brow
    for s in(-1,1): d=np.maximum(d,-ell(P,(s*0.13,2.12,0.9),(0.06,0.04,0.05)))
    return d
def robed_sdf(P):
    # robed saint, hands joined, ~2.1 m, faces +z
    d=cap(P,(0,0.05,0),(0,1.45,0),0.42,0.24)                      # robe cone
    d=smin(d,ell(P,(0,1.5,0),(0.3,0.22,0.22)),0.12)               # shoulders
    d=smin(d,ell(P,(0,1.83,0.02),(0.14,0.17,0.15)),0.06)          # head
    d=smin(d,ell(P,(0,1.86,-0.04),(0.19,0.22,0.19)),0.03)         # hood
    for s in(-1,1): d=smin(d,cap(P,(s*0.27,1.45,0.02),(s*0.06,1.05,0.25),0.09,0.08),0.08)  # arms
    d=smin(d,ell(P,(0,1.05,0.27),(0.1,0.12,0.08)),0.05)           # hands
    fold=0.015*np.sin(np.arctan2(P[...,0],P[...,2])*9)*(P[...,1]<1.3)
    return d-fold
def rock_sdf(seed):
    r=np.random.default_rng(seed); ph=r.uniform(0,6.3,9); fr=r.uniform(2.0,4.5,9)
    def f(P):
        d=ell(P,(0,0.35,0),(1.0,0.75,0.9))
        for k in range(3): d=smin(d,ell(P,(r.uniform(-0.5,0.5),0.3,r.uniform(-0.4,0.4)) if False else ((k-1)*0.45,0.25+0.1*k,(k%2-0.5)*0.5),(0.6,0.55,0.55)),0.2)
        n=sum(0.16/(1+i*0.5)*np.abs(np.sin(fr[i]*(1+i*0.35)*P[...,i%3]+ph[i])*np.sin(fr[i]*0.8*P[...,(i+1)%3]+ph[(i+3)%9])) for i in range(9))-0.25
        n=n+0.12*np.floor(P[...,1]*3.0+np.sin(P[...,0]*2+ph[0]))/3.0*0
        return np.maximum(d+n,-P[...,1])   # flat base
    return f
SDF=dict(**{f'rock{i}':(rock_sdf(i),(-1.6,-0.05,-1.4),(1.6,1.4,1.4)) for i in range(4)},lion=(lion_sdf,(-0.9,-0.02,-1.2),(0.9,2.75,1.15)),robed=(robed_sdf,(-0.5,-0.02,-0.5),(0.5,2.1,0.5)))
@functools.lru_cache(None)
def get(name,tris):
    f,lo,hi=SDF[name]; n=72 if name=='lion' else (32 if name.startswith('rock') else 48)
    xs=[np.linspace(lo[i],hi[i],n) for i in range(3)]; G=np.stack(np.meshgrid(*xs,indexing='ij'),-1)
    vol=f(G); sp=[(hi[i]-lo[i])/(n-1) for i in range(3)]
    V,F,_,_=marching_cubes(vol,0.0,spacing=sp); V=V+np.array(lo)
    ms=pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(V,F))
    ms.apply_coord_laplacian_smoothing(stepsmoothnum=2)
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=tris,preservenormal=True,qualitythr=0.5)
    m=ms.current_mesh(); V,F=m.vertex_matrix(),m.face_matrix()
    T=V[F]; n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); c=T.mean(1)-V.mean(0)
    if (n*c).sum()<0: F=F[:,::-1]
    return V,F.copy()
if __name__=='__main__':
    for nm,t in(('lion',3000),('robed',700)): V,F=get(nm,t); print(nm,len(F),V.min(0),V.max(0))
