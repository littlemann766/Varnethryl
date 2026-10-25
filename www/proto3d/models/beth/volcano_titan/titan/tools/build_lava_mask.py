import numpy as np
from PIL import Image
from scipy import ndimage as nd
z=np.load('an.npz');UV=z['UV'];F=z['F'];P=z['P']
S=2048
sc=np.array(Image.open('flaw_score.png')).astype(float)/255
# rasterize rest positions
pos=np.zeros((S,S,3));cov=np.zeros((S,S),bool)
for f in F:
    u=UV[f]*S;x0,y0=np.floor(u.min(0)).astype(int);x1,y1=np.ceil(u.max(0)).astype(int)+1
    x0=max(x0,0);y0=max(y0,0);x1=min(x1,S);y1=min(y1,S)
    if x1<=x0 or y1<=y0:continue
    yy,xx=np.mgrid[y0:y1,x0:x1]+0.5
    a,b_,c=u;den=(b_[1]-c[1])*(a[0]-c[0])+(c[0]-b_[0])*(a[1]-c[1])
    if abs(den)<1e-12:continue
    l1=((b_[1]-c[1])*(xx-c[0])+(c[0]-b_[0])*(yy-c[1]))/den
    l2=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;l3=1-l1-l2
    m=(l1>=-0.02)&(l2>=-0.02)&(l3>=-0.02)
    if not m.any():continue
    p=l1[...,None]*P[f[0]]+l2[...,None]*P[f[1]]+l3[...,None]*P[f[2]]
    sl=(slice(y0,y1),slice(x0,x1));pos[sl][m]=p[m];cov[sl]|=m
# pad pos
m=cov.copy()
for _ in range(10):
    for c in range(3):
        dl=nd.grey_dilation(pos[...,c],size=3)*(~m)+0;pos[...,c]=np.where(m,pos[...,c],np.where(nd.binary_dilation(m),nd.maximum_filter(pos[...,c]*m,3)+nd.minimum_filter(np.where(m,pos[...,c],1e9),3)*0,pos[...,c]))
    m=nd.binary_dilation(m)
H=P.max(0)-P.min(0);print('height',H)
rng=np.random.default_rng(3);G=rng.random((64,64,64))
def vnoise(p):
    i=np.floor(p).astype(int);f=p-i;f=f*f*(3-2*f);o=0
    for dx in(0,1):
        for dy in(0,1):
            for dz in(0,1):
                w=(f[...,0] if dx else 1-f[...,0])*(f[...,1] if dy else 1-f[...,1])*(f[...,2] if dz else 1-f[...,2])
                o=o+w*G[(i[...,0]+dx)%64,(i[...,1]+dy)%64,(i[...,2]+dz)%64]
    return o
def fbm(p,o=4):
    s=0;a=1;t=0
    for k in range(o):s+=a*vnoise(p*2**k);t+=a;a*=.5
    return s/t
q=pos/H[1]*9.0  # ~9 cells per body height
warp=np.stack([fbm(q+11),fbm(q+23),fbm(q+37)],-1)
r1=np.abs(fbm(q+warp*1.2,4)-0.5)
r2=np.abs(fbm(q*2.7+warp,3)-0.5)
w1=0.006+0.055*sc**1.2; w2=0.004+0.018*sc
vein=np.maximum(np.clip(1-r1/w1,0,1)**0.6, np.clip(1-r2/w2,0,1)**0.8*(0.35+0.65*sc))
pool=np.clip((sc-0.7)/0.2,0,1)*np.clip((fbm(q*3+5)-0.45)*5,0,1)
vein=np.maximum(vein,pool)*m
halo=np.clip(nd.gaussian_filter(nd.grey_dilation(vein,size=9),3)*1.5,0,1)
flow=fbm(q*0.6+3,3)
em=np.array(Image.open('img0.png').convert('L').resize((S,S)))/255.
out=(np.clip(np.dstack([vein,halo,flow,em]),0,1)*255).astype(np.uint8)
Image.fromarray(out,'RGBA').save('titan_lava_mask.png')
al=np.array(Image.open('img2.png').resize((S,S))).astype(float)/255
crust=np.array([0.05,0.04,0.035])
alb=al*(1-0.8*halo[...,None])+crust*0.8*halo[...,None];alb=alb*(1-vein[...,None])+np.array([0.9,0.35,0.05])*vein[...,None]
Image.fromarray((np.clip(alb,0,1)*255).astype(np.uint8)).save('titan_lava_albedo.png')
e0=np.array(Image.open('img0.png').resize((S,S))).astype(float)/255
emi=np.maximum(e0,vein[...,None]*np.array([1.0,0.42,0.06]))
Image.fromarray((emi*255).astype(np.uint8)).save('titan_lava_emissive.png')
print('cover',(vein>0.3)[cov].mean())
