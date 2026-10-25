import numpy as np
from PIL import Image
N=1024; rng=np.random.default_rng(1905)
def tnoise(sc,oct=5,seed=0):
    r=np.random.default_rng(seed); out=np.zeros((N,N)); amp=1; tot=0
    for o in range(oct):
        g=sc*2**o; G=r.random((g,g))
        G=np.pad(G,((0,1),(0,1)),mode='wrap')
        x=np.linspace(0,g,N,endpoint=False); i=x.astype(int); f=x-i; f=f*f*(3-2*f)
        a=G[i][:,i]*(1-f)[None,:]+G[i][:,i+1]*f[None,:]; b=G[i+1][:,i]*(1-f)[None,:]+G[i+1][:,i+1]*f[None,:]
        out+=amp*(a*(1-f)[:,None]+b*f[:,None]); tot+=amp; amp*=0.5
    return out/tot
def normal(h,s):
    dx=(np.roll(h,-1,1)-np.roll(h,1,1))*s; dy=(np.roll(h,-1,0)-np.roll(h,1,0))*s
    n=np.dstack([-dx,dy,np.ones_like(h)]); n/=np.linalg.norm(n,axis=2,keepdims=True); return ((n*0.5+0.5)*255).astype(np.uint8)
def save(name,col,h,rough,s):
    Image.fromarray((np.clip(col,0,1)*255).astype(np.uint8)).save(f'textures/{name}_albedo.png')
    Image.fromarray(normal(h,s)).save(f'textures/{name}_normal.png')
    Image.fromarray((np.clip(rough,0,1)*255).astype(np.uint8)).save(f'textures/{name}_rough.png')
# ---- dirt: packed earth, two wheel ruts (u across: rows=v along, cols=u), pebbles
u=np.linspace(0,1,N,endpoint=False)[None,:].repeat(N,0)
n1=tnoise(4,6,1); n2=tnoise(16,4,2); n3=tnoise(64,3,3)
rut=np.exp(-((u-0.32)/0.06)**2)+np.exp(-((u-0.68)/0.06)**2)
crown=np.exp(-((u-0.5)/0.08)**2)*0.6
h=0.5*n1+0.3*n2+0.2*n3-0.35*rut*(0.7+0.3*n2)+0.1*crown
base=np.array([0.47,0.37,0.26]); dark=np.array([0.33,0.25,0.17]); light=np.array([0.60,0.50,0.37])
t=np.clip((n1-0.35)*2,0,1)[...,None]
col=dark*(1-t)+light*t; col=col*(0.85+0.3*n3[...,None]); col=col*(1-0.30*rut[...,None])
# grassy tufts along the crown and edges
gm=np.clip((tnoise(24,3,9)-0.62)*6,0,1)*np.clip(crown*1.5+np.clip((np.abs(u-0.5)-0.40)*12,0,1),0,1)
col=col*(1-gm[...,None])+np.array([0.30,0.40,0.16])*gm[...,None]*(0.8+0.4*n3[...,None])
# pebbles
for _ in range(900):
    cx,cy=rng.integers(0,N,2); r=rng.uniform(2,6); yy,xx=np.ogrid[-8:9,-8:9]; m=np.clip(1-(xx**2+yy**2)/r**2,0,1)
    ys=(np.arange(cy-8,cy+9)%N)[:,None]; xs=(np.arange(cx-8,cx+9)%N)[None,:]
    g=rng.uniform(0.30,0.48); col[ys,xs]=col[ys,xs]*(1-m[...,None])+g*np.array([1,0.95,0.88])*m[...,None]; h[ys,xs]+=m*0.25
save('dirt',col,h,0.92-0.1*rut-0.05*n3,6)
# ---- cobble: voronoi stones, square-ish sett rows
pts=[]; rows=22
for r in range(rows):
    y=(r+0.5)/rows; off=0.5*(r%2)
    for c in range(rows):
        pts.append(((c+off+rng.uniform(-0.18,0.18))/rows%1,(y+rng.uniform(-0.12,0.12)/rows)%1))
P=np.array(pts)*N
yy,xx=np.mgrid[0:N,0:N].astype(float)
d1=np.full((N,N),1e9); d2=np.full((N,N),1e9); idx=np.zeros((N,N),int)
for k,(px,py) in enumerate(P):
    for ox in (-N,0,N):
        for oy in (-N,0,N):
            if abs(px+ox-N/2)>N*0.75 or abs(py+oy-N/2)>N*0.75: continue
            d=np.hypot(xx-px-ox,yy-py-oy); m=d<d1; d2=np.where(m,d1,np.minimum(d2,d)); idx=np.where(m,k,idx); d1=np.where(m,d,d1)
edge=d2-d1
stone=np.clip(edge/7,0,1)
tint=rng.uniform(0.75,1.15,len(P))[idx]; hue=rng.uniform(-0.04,0.04,len(P))[idx]
sc=np.dstack([0.50+hue,np.full_like(hue,0.47),0.42-hue])*tint[...,None]*(0.85+0.3*n3[...,None])
mortar=np.array([0.36,0.30,0.22])*(0.8+0.4*n2[...,None])
col=sc*stone[...,None]+mortar*(1-stone[...,None])
moss=np.clip((tnoise(12,3,5)-0.55)*5,0,1)*(1-stone)
col=col*(1-moss[...,None])+np.array([0.25,0.34,0.14])*moss[...,None]
h=np.sqrt(stone)*0.9+0.1*n3
save('cobble',col,h,0.8+0.15*(1-stone),10)
# ---- grass edge alpha mask noise (tileable)
Image.fromarray((tnoise(8,5,11)*255).astype(np.uint8)).save('textures/edge_noise.png')
print('ok')
