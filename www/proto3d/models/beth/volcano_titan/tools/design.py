import numpy as np, json
from scipy import ndimage as nd
from PIL import Image
rng=np.random.default_rng(7)
S=np.load('src.npz'); Hs=S['H']; Cs=S['C']; Ms=S['M']; xs=S['xs']
R=148.0; D=0.5; N=int(2*R/D)+1
g=np.linspace(-R,R,N).astype(np.float32); X,Y=np.meshgrid(g,g)
r=np.hypot(X,Y); th=np.arctan2(Y,X)
def up(a,order=1):  # 2m src grid (-150..150) -> master grid
    f=(g+150)/2.0; jj,ii=np.meshgrid(f,f,indexing='ij')
    return nd.map_coordinates(a,[jj,ii],order=order,mode='nearest')
def fbm(n0,oct,seed,ridged=False,shape=None):
    shape=shape or (N,N); rg=np.random.default_rng(seed); out=np.zeros(shape,np.float32); amp=1; tot=0
    for o in range(oct):
        n=n0*2**o; z=rg.random((n+3,n+3)).astype(np.float32)
        a=nd.zoom(z,(shape[0]/(n+3)*1.0,shape[1]/(n+3)*1.0),order=3)[:shape[0],:shape[1]]
        if ridged: a=1-np.abs(2*a-1); a=a*a
        out+=a*amp; tot+=amp; amp*=0.5
    return out/tot
# 1. his shape, smoothed (his mesh is 341 tris: keep silhouette, lose facets)
Hb=nd.gaussian_filter(np.where(Ms,Hs,0),1.6); Hb=up(Hb,3).astype(np.float32)
Cb=np.stack([up(nd.gaussian_filter(Cs[...,k],1.0),1) for k in range(3)],-1).astype(np.float32)
# 2. crater design (keeps his rim height/radius; floor = arena)
FLOOR=39.0; ARENA_R=33.0; MOAT_IN=33.5; MOAT_OUT=40.0; WALL_TOP=52.0
rimH=np.clip(Hb,60,82)
inner=np.where(r<MOAT_OUT,FLOOR,FLOOR+3+(rimH-FLOOR-3)*np.clip((r-MOAT_OUT)/(WALL_TOP-MOAT_OUT),0,1)**0.7)
blend=np.clip((r-WALL_TOP)/8,0,1)
H=inner*(1-blend)+Hb*blend
H=np.where(r>WALL_TOP+8,Hb,H)
# 3. craggy detail: radial gullies + ridged fbm + strata, scaled by slope band
ang_n=fbm(6,3,11)*2.5
gul=(0.5+0.5*np.sin(th*44+ang_n*3.0+r*0.02))**4*(0.5+1.0*fbm(5,3,13))
outer=np.clip((r-WALL_TOP)/10,0,1)*np.clip((140-r)/30,0,1)
rid=fbm(10,6,3,ridged=True); f2=fbm(40,4,5)
rid2=fbm(28,5,3,ridged=True)
H+= outer*(-gul*2.6 + rid2*1.6 - 0.9) + f2*0.6
crag=np.clip((r-MOAT_OUT)/3,0,1)*np.clip((WALL_TOP+6-r)/4,0,1)
strata=nd.gaussian_filter(np.sin(H*2.6+fbm(12,3,17)*5),1.2)*1.4
H+= crag*(rid*3.5+strata*0.6)
# floor: cracked plates, small relief
fl=r<MOAT_IN
H=np.where(fl,FLOOR+fbm(30,4,9)*0.35,H)
H=H*np.clip((147-r)/12,0,1)**0.8
# 4. path: outer spiral to a breach at TH1, then inner ramp to arena
TH1=np.radians(100.0); HN=60.0
def prof(rr):  # azimuthal mean profile of H
    b=np.clip((r/1.0).astype(int),0,160); s=np.bincount(b.ravel(),H.ravel(),161)/np.maximum(np.bincount(b.ravel(),None,161),1); return np.interp(rr,np.arange(161),s)
T=np.linspace(0,1,1400)
turn=np.radians(250)
rr=143-(143-60)*T; tt=TH1-turn*(1-T)
hp=prof(rr); hp=np.minimum(hp,HN); hp[:8]=0.0
hp=np.maximum.accumulate(hp)  # never descends going up
P1=np.stack([rr*np.cos(tt),rr*np.sin(tt),hp],1)
# breach crossing r 60->48 at HN
rb=np.linspace(60,47,60); P2=np.stack([rb*np.cos(TH1),rb*np.sin(TH1),np.full(60,HN)],1)
# inner ramp along wall, clockwise, 47->37 radius, HN->FLOOR
t3=np.linspace(0,1,600); a3=TH1-np.radians(150)*t3; r3=47-10*t3**1.5; h3=HN-(HN-FLOOR)*t3
P3=np.stack([r3*np.cos(a3),r3*np.sin(a3),h3],1)
P=np.concatenate([P1,P2,P3])
# smooth heights along path, enforce grade <= 0.42 (~23 deg)
s=np.concatenate([[0],np.cumsum(np.hypot(*np.diff(P[:,:2],axis=0).T))])
from scipy.ndimage import uniform_filter1d
P[:,2]=uniform_filter1d(P[:,2],25,mode='nearest')
for k in range(1,len(P)):
    ds=s[k]-s[k-1]; P[k,2]=np.clip(P[k,2],P[k-1,2]-0.42*ds,P[k-1,2]+0.42*ds)
# rasterise path distance + height
from scipy.spatial import cKDTree
kd=cKDTree(P[:,:2]); dist,idx=kd.query(np.stack([X.ravel(),Y.ravel()],1),distance_upper_bound=14)
dist=dist.reshape(N,N); idx=np.minimum(idx,len(P)-1).reshape(N,N); hpath=P[idx,2]
HALF=3.25; BL=5.0
w=np.clip(1-(dist-HALF)/BL,0,1); w=w*w*(3-2*w); w[np.isinf(dist)]=0
pathmask=(dist<=HALF)
H=H*(1-w)+hpath*w
mz=(dist<=HALF+1.5).astype(np.float32); hpath=np.where(mz>0,nd.gaussian_filter(hpath*mz,2.5)/np.maximum(nd.gaussian_filter(mz,2.5),1e-3),hpath)
H=H*(1-w)+hpath*w
H=np.where(dist<=HALF+0.9,hpath+fbm(60,2,21)*0.06,H)
# soften shoulders
sh=(dist>HALF+0.9)&(dist<HALF+4)
Hs_=nd.gaussian_filter(H,1.5); H=np.where(sh,Hs_,H)
# moat (lava ring) except the ramp landing bridge
land=P[-1,:2]; dl=np.hypot(X-land[0],Y-land[1])
moat=(r>MOAT_IN)&(r<MOAT_OUT-0.5)&(dl>9)&(dist>HALF+4)
H=np.where(moat,np.minimum(H,FLOOR-2.6+fbm(30,3,4)*0.3),H)
# 5. lava breach + flows on the side away from the path
THF=TH1+np.radians(120)
spill=np.exp(-((np.angle(np.exp(1j*(th-THF))))*50/1.0)**2/ (2*0.12**2))
H-= spill*np.clip((r-46)/4,0,1)*np.clip((64-r)/4,0,1)*6
H=np.where(r>147,0,H); H=np.maximum(H,0)
# flows: steepest descent from the spill notch, 3 branches
gy,gx=np.gradient(nd.gaussian_filter(H,3),D)
flows=[]
for k,da in enumerate([-0.07,0.0,0.08]):
    p=np.array([58*np.cos(THF+da),58*np.sin(THF+da)]); pts=[]
    for it in range(1600):
        i=int((p[0]+R)/D); j=int((p[1]+R)/D)
        if not(0<i<N-1 and 0<j<N-1) or H[j,i]<1.5 or dist[j,i]<HALF+8: break
        pts.append((p[0],p[1])); v=-np.array([gx[j,i],gy[j,i]]); n=np.linalg.norm(v)
        if n<1e-4: break
        v=v/n+np.array([np.cos(THF),np.sin(THF)])*0.35+ (rng.random(2)-.5)*0.25
        p=p+v/np.linalg.norm(v)*0.6
    flows.append(np.array(pts))
FW=np.zeros((N,N),np.float32)
for f in flows:
    L=len(f); wd=np.linspace(4.5,1.6,L)
    kdf=cKDTree(f); dd,ii=kdf.query(np.stack([X.ravel(),Y.ravel()],1),distance_upper_bound=8)
    dd=dd.reshape(N,N); ii=np.minimum(ii,L-1).reshape(N,N)
    FW=np.maximum(FW,np.clip(1-dd/wd[ii],0,1))
H-=FW*0.9
np.savez_compressed('design.npz',H=H.astype(np.float32),X=g,Cb=Cb,pathmask=pathmask,dist=np.where(np.isinf(dist),99,dist).astype(np.float32),w=w,moat=moat,FW=FW,P=P,flows=np.array(flows,dtype=object),r=r)
# report path grade & cross slope
gy,gx=np.gradient(H,D); slope=np.degrees(np.arctan(np.hypot(gx,gy)))
print('path slope max/p99',slope[pathmask].max(),np.percentile(slope[pathmask],99))
grade=np.degrees(np.arctan(np.abs(np.diff(P[:,2]))/np.maximum(np.diff(s),1e-6))); print('grade max',grade.max(),'len',s[-1],'end',P[-1])
print('arena slope',slope[r<30].max(), 'Hmax',H.max())
json.dump({'P':P[::20].tolist()},open('path.json','w'))
