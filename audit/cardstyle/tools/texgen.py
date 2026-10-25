# Tileable realistic medieval PBR sets (albedo, normal, roughness, height) at N px.
import numpy as np, os
from PIL import Image
from scipy import ndimage
N=1024; R=np.random.default_rng(7)
OUT='/workspace/beth-world/www/proto3d/models/beth/textures/realmed'; os.makedirs(OUT,exist_ok=True)
def noise(n,beta,seed):
    r=np.random.default_rng(seed); f=np.fft.fftfreq(n)
    k=np.sqrt(f[:,None]**2+f[None,:]**2); k[0,0]=1
    s=np.fft.ifft2(np.fft.fft2(r.normal(size=(n,n)))/k**beta).real
    return (s-s.min())/(s.max()-s.min())
def voronoi(n,cells,seed,aspect=1.0,jit=0.8):
    # tileable voronoi: returns F1,F2-F1 edge dist, cell id
    r=np.random.default_rng(seed); pts=[]
    gx=int(np.sqrt(cells*aspect)); gy=max(1,cells//gx)
    for i in range(gx):
        for j in range(gy):
            pts.append(((i+0.5+jit*(r.random()-0.5))/gx,(j+0.5+jit*(r.random()-0.5))/gy))
    pts=np.array(pts); P=np.concatenate([pts+[dx,dy] for dx in(-1,0,1) for dy in(-1,0,1)])
    ids=np.tile(np.arange(len(pts)),9)
    y,x=np.mgrid[0:n,0:n]/n; xy=np.stack([x.ravel(),y.ravel()],1)
    from scipy.spatial import cKDTree
    d,i=cKDTree(P*[1,1/aspect if aspect!=1 else 1]).query(xy*[1,1/aspect if aspect!=1 else 1],k=2)
    return (d[:,1]-d[:,0]).reshape(n,n), ids[i[:,0]].reshape(n,n)
def nrm(h,strength):
    gx=(np.roll(h,-1,1)-np.roll(h,1,1))*strength; gy=(np.roll(h,-1,0)-np.roll(h,1,0))*strength
    v=np.stack([-gx,gy,np.ones_like(h)],-1); v/=np.linalg.norm(v,axis=-1,keepdims=True)
    return ((v*0.5+0.5)*255).astype(np.uint8)
def hexc(h): return np.array([int(h[i:i+2],16) for i in(1,3,5)])/255
def save(name,alb,h,rough,ns=6.0):
    Image.fromarray((np.clip(alb,0,1)*255).astype(np.uint8)).save(f'{OUT}/{name}_albedo.jpg',quality=90)
    Image.fromarray(nrm(h,ns*N/1024)).save(f'{OUT}/{name}_normal.png')
    Image.fromarray((np.clip(rough,0,1)*255).astype(np.uint8)).save(f'{OUT}/{name}_rough.png')
    Image.fromarray((np.clip(h,0,1)*255).astype(np.uint8)).save(f'{OUT}/{name}_height.png')
fine=noise(N,1.2,1); mid=noise(N,1.6,2); big=noise(N,2.2,3)
def stones(name,cells,palette,mortar,aspect,seed,gap=0.012,moss=0.0):
    e,cid=voronoi(N,cells,seed,aspect)
    pal=np.array([hexc(c) for c in palette]); rr=np.random.default_rng(seed)
    col=pal[rr.integers(0,len(pal),cid.max()+1)][cid]*(0.85+0.3*rr.random(cid.max()+1)[cid])[...,None]
    bulge=np.clip(e/0.05,0,1)**0.5; m=e<gap
    h=bulge*0.7+fine*0.2+mid*0.1; h[m]=fine[m]*0.15
    alb=col*(0.75+0.35*fine[...,None])*(0.85+0.15*bulge[...,None])
    alb[m]=hexc(mortar)*(0.8+0.3*fine[m,None])
    if moss: mk=(big>1-moss)&(bulge<0.6); alb[mk]=alb[mk]*0.4+hexc('#4f5a2c')*0.6*(0.7+0.5*fine[mk,None])
    rough=0.82+0.12*fine-0.1*bulge; rough[m]=0.95
    save(name,alb,h,rough,8); return alb,h,rough
fs=stones('fieldstone',140,['#8a8577','#6f6c64','#9a9283','#7b7466','#a39c8c','#5f5d58'],'#57534b',1.0,11,moss=0.18)
cb=stones('cobblestone',420,['#6e6a62','#7f786c','#5d5a55','#8a8273','#66625a'],'#3e3a33',1.0,12,gap=0.016,moss=0.08)
# slate: overlapping rows of shingles, 16 rows
y,x=np.mgrid[0:N,0:N]/N; rows=16; ry=(y*rows)%1; ri=(y*rows).astype(int)
cols=24; sx=(x*cols+0.5*(ri%2))%1; si=((x*cols+0.5*(ri%2)).astype(int)%cols)+ri*cols
rv=np.random.default_rng(5).random(rows*cols+cols)
h=(1-ry)*0.6+0.25*(np.minimum(sx,1-sx)>0.04)+0.15*fine; h[ry>0.97]=0.05
base=np.array([hexc('#4a5664'),hexc('#3d4652'),hexc('#56606b'),hexc('#434b57')])
alb=base[(rv[si]*4).astype(int)]*(0.8+0.3*fine[...,None])*(0.75+0.3*(1-ry)[...,None])
mk=(big>0.78); alb[mk]=alb[mk]*0.55+hexc('#5b6233')*0.45
save('slate',alb,h,0.55+0.25*fine+0.1*(rv[si]>0.5),7); sl=(alb,h)
# oak wood (vertical grain)
g=noise(N,1.0,9); grain=(np.sin((x*60+g*6+big*3)*np.pi*2)*0.5+0.5)
wd=hexc('#3a2a1d')*(0.7+0.5*grain[...,None]*(0.6+0.4*fine[...,None]))
planks=(x*8)%1; h=0.6*grain*0.3+0.7*(np.minimum(planks,1-planks)>0.02)+0.1*fine
save('oak',wd,h,0.7+0.2*fine,5)
# plaster + timber framing panel (one bay per tile: posts, rail, braces)
pl=hexc('#d9cdb2')*(0.82+0.18*mid[...,None])*(0.9+0.1*fine[...,None])
stain=noise(N,2.0,21); pl=pl*(1-0.25*(stain>0.7)[...,None]*stain[...,None])
streak=noise(N,1.0,33)[:,:]; st=np.clip((np.roll(np.repeat(streak[:1],N,0),0,0)-0.55)*3,0,1)*(1-y)  # rain streaks from top
pl=pl*(1-0.22*st[...,None])
tim=np.zeros((N,N),bool); tw=0.06
tim|=(x<tw)|(x>1-tw)|(np.abs(y-0.5)<tw/2)|(y<tw/2)|(y>1-tw/2)
for s in(1,-1):
    d=np.abs((y-0.5)-s*(x-0.5)); tim|=(d<tw*0.6)&(y>0.5)
hh=np.where(tim,0.85+0.1*grain,0.35+0.1*mid+0.05*fine)
alb=np.where(tim[...,None],wd*0.8,pl)
save('plaster_timber',alb,hh,np.where(tim,0.75,0.9)+0.05*fine,9); pt=(alb,hh)
# lion banner (not tiling): blue field, gold rampant-lion silhouette, gold border, fringe
B=np.ones((1024,512,3))*hexc('#1f3c7a')*(0.85+0.2*mid[:,:512,None]); yy,xx=np.mgrid[0:1024,0:512]
border=(xx<24)|(xx>487)|(yy<24); B[border]=hexc('#c9a13b')
B[(yy>940)&(((xx//32)+(yy>980))%2==0)]=hexc('#c9a13b')
from PIL import ImageDraw
im=Image.fromarray((B*255).astype(np.uint8)); d=ImageDraw.Draw(im); G=(214,170,62)
d.ellipse([200,300,330,420],fill=G); d.polygon([(250,360),(180,560),(210,760),(320,780),(340,560),(320,400)],fill=G) # head, body
d.polygon([(320,420),(420,330),(440,350),(340,470)],fill=G); d.polygon([(310,520),(430,470),(440,495),(320,560)],fill=G) # forelegs raised
d.polygon([(210,740),(160,880),(190,890),(250,760)],fill=G); d.polygon([(300,760),(340,890),(370,880),(320,740)],fill=G) # hind legs
d.line([(200,700),(110,620),(120,520),(90,480)],fill=G,width=16); d.ellipse([70,455,115,500],fill=G) # tail
d.polygon([(330,330),(360,300),(345,345)],fill=G); d.polygon([(205,315),(240,250),(270,300)],fill=G) # crown/mane tufts
im.save(f'{OUT}/banner_lion_albedo.jpg',quality=92)
print('ok')
