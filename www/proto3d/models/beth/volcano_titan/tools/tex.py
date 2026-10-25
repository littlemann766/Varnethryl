import numpy as np
from scipy import ndimage as nd
from PIL import Image
d=np.load('design.npz',allow_pickle=True); H=d['H']; N=H.shape[0]; R=148.0
T=4096; px=2*R/T
z=lambda a,o=1: nd.zoom(a.astype(np.float32),T/N,order=o)[:T,:T]
def fbm(n0,oct,seed,ridged=False):
    rg=np.random.default_rng(seed); out=np.zeros((T,T),np.float32); amp=1; tot=0
    for o in range(oct):
        n=n0*2**o; a=nd.zoom(rg.random((n+3,n+3)).astype(np.float32),T/(n+3),order=3)[:T,:T]
        if ridged: a=(1-np.abs(2*a-1))**2
        out+=a*amp; tot+=amp; amp*=.5
    return out/tot
Hh=z(H,3); Cb=np.stack([z(d['Cb'][...,k]) for k in range(3)],-1)**2.2
pm=z(d['pathmask'].astype(np.float32))>0.5; moat=z(d['moat'].astype(np.float32)); FW=z(d['FW'])
g=np.linspace(-R,R,T); X,Y=np.meshgrid(g,g); r=np.hypot(X,Y); del X,Y
fine=fbm(64,5,1); cr=fbm(48,4,2,ridged=True); grain=np.random.default_rng(3).random((T,T)).astype(np.float32)
Hd=Hh+fine*0.35+grain*0.03-np.clip(cr-0.82,0,1)*1.2
gy,gx=np.gradient(nd.gaussian_filter(Hh,2),px); slope=np.degrees(np.arctan(np.hypot(gx,gy))); del gx,gy
cav=nd.gaussian_filter(Hh,6)-Hh  # >0 in hollows
def C(*c): return np.array(c,np.float32)
base=C(.17,.155,.145)[None,None]*(0.75+0.5*fine[...,None])
dark=C(.10,.095,.09)[None,None]*(0.8+0.4*fbm(30,4,7)[...,None])
strat=0.5+0.5*np.sin(Hh*2.9+fbm(16,3,8)*6)
dark=dark*(0.95+0.1*strat[...,None])
ash=C(.40,.385,.36)[None,None]*(0.85+0.3*fbm(80,3,9)[...,None])
ox=C(.38,.19,.12)[None,None]*(0.8+0.4*fine[...,None])
col=base
ws=np.clip((slope-28)/18,0,1)[...,None]; col=col*(1-ws)+dark*ws
wa=(np.clip((22-slope)/14,0,1)*np.clip(cav*0.6+0.3+ (Hh/80)*0.4,0,1)*(0.6+0.6*fbm(12,4,10)))[...,None]
wa=np.clip(wa*0.55,0,1); col=col*(1-wa)+ash*wa
wf=np.clip((34.5-r)/1.5,0,1)[...,None]; col=col*(1-wf)+C(.085,.075,.07)*(0.7+0.6*fine[...,None])*wf
wo=(np.clip(1-np.abs(r-44)/14,0,1)*0.7)[...,None]*(0.5+fbm(20,3,11)[...,None]); col=col*(1-wo)+ox*wo
# keep his look: green skirt and his overall hue
wg=(np.clip((14-Hh)/10,0,1)*np.clip((30-slope)/15,0,1))[...,None]
grass=Cb*0.9*(0.8+0.4*fine[...,None]); col=col*(1-wg)+grass*wg
lum=Cb.mean(-1,keepdims=True)+1e-3; col=col*(0.8+0.2*Cb/lum)
# his model's mossy grey-green on the outer flanks (keeps his look); crater + crags stay basalt
wh=(np.clip((r-62)/14,0,1)*np.clip((55-slope)/20,0,1)*0.97)[...,None]
moss=C(.30,.36,.22)[None,None]; mf=np.clip(fbm(24,4,31)*1.6-0.45,0,1)[...,None]*np.clip((30-slope)/15,0,1)[...,None]
his=(Cb*1.05*(1-mf*0.55)+moss*mf*0.55)*(0.72+0.56*fine[...,None])*(1+0.25*np.clip(cav,-1,1)[...,None])
col=col*(1-wh)+his*1.25*wh
# scorched rims around flows and moat, path gravel
sc=np.clip(nd.gaussian_filter(np.maximum(FW,moat),8)*2.2,0,1)[...,None]; col=col*(1-0.75*sc)
dist=z(d['dist']); pn=fbm(120,3,41)
pg=C(.33,.27,.21)[None,None]*(0.8+0.25*pn[...,None]+0.1*grain[...,None])
rut=np.clip(1-np.abs(np.abs(dist)-1.15)/0.35,0,1)*(0.6+0.4*pn); pg=pg*(1-0.35*rut[...,None])
edge=np.clip((dist-2.4)/0.8,0,1); pg=pg*(1-edge[...,None])+C(.2,.19,.18)*(0.7+0.6*grain[...,None])*edge[...,None]
pmf=np.clip((3.6-dist)/0.8,0,1)[...,None]; col=col*(1-pmf)+pg*pmf
col=col*(0.75+0.25*np.clip(1-cav*0.4,0.4,1.3))[...,None]
# glowing cracks
crack=np.clip((cr-0.86)/0.06,0,1)
em_mask=np.clip((33.5-r)/2,0,1)*0.9+np.clip(1-np.abs(r-38)/5,0,1)+np.clip(nd.gaussian_filter(FW,14)*3,0,1)
em_mask*= (1-pmf[...,0])
glow=crack*np.clip(em_mask,0,1)
col=col*(1-glow[...,None])+C(.9,.35,.08)*glow[...,None]
E=np.clip(glow[...,None]*C(1.0,.38,.06)*1.0,0,1)
Image.fromarray((np.clip(np.flipud(col),0,1)**(1/2.2)*255).astype(np.uint8)).save('t_albedo.png')
Image.fromarray((np.flipud(E)*255).astype(np.uint8)).save('t_emissive.png')
Hd=Hd-np.clip(1-np.abs(z(d['dist'])-1.15)/0.35,0,1)*0.08*(z(d['dist'])<3)+np.where(z(d['dist'])<3.3,grain*0.04,0)
gy,gx=np.gradient(Hd,px); n=np.dstack([-gx,-gy,np.ones_like(gx)*1.0]); n/=np.linalg.norm(n,axis=2,keepdims=True)
# tangent space for planar UV (u=+x, v=+y after flip) -> OpenGL normal
Image.fromarray(((np.flipud(n)*0.5+0.5)*255).astype(np.uint8)).save('t_normal.png')
rough=np.clip(0.82+0.12*fine-0.25*glow-0.1*ws[...,0],0,1); ao=np.clip(1-cav*0.08,0.5,1)
Image.fromarray((np.flipud(np.dstack([ao,rough,np.zeros_like(rough)]))*255).astype(np.uint8)).save('t_orm.png')
# lava tile 1024
L=1024; rg=np.random.default_rng(5)
def f2(n0,oct,seed,ridged=False):
    rg=np.random.default_rng(seed); out=np.zeros((L,L),np.float32);amp=1;tot=0
    for o in range(oct):
        n=n0*2**o; z0=rg.random((n,n)).astype(np.float32); z0=np.tile(z0,(3,3))
        a=nd.zoom(z0,L*3/(3*n),order=3)[L:2*L,L:2*L]
        if ridged:a=(1-np.abs(2*a-1))**2
        out+=a*amp;tot+=amp;amp*=.5
    return out/tot
c=f2(6,5,1,True); h=f2(4,5,2)
crust=np.clip((0.72-c)/0.25,0,1)*np.clip(h*1.4,0,1)
hot=1-crust
lc=crust[...,None]*C(.08,.05,.04)+hot[...,None]*(C(1,.55,.12)*(0.6+0.4*h[...,None])+C(.2,.0,0)*(1-h[...,None]))
Image.fromarray((np.clip(lc,0,1)**(1/2.2)*255).astype(np.uint8)).save('l_albedo.png')
Image.fromarray((np.clip(hot[...,None]*C(1,.45,.08)*(0.5+0.6*h[...,None]),0,1)*255).astype(np.uint8)).save('l_emissive.png')
print('ok')

cc=f2(8,6,61,True); cs=f2(6,6,62); cj=f2(16,4,65,True)
yy=np.linspace(0,1,L,endpoint=False)[:,None]; xx=np.linspace(0,1,L,endpoint=False)[None,:]
strat=(np.sin(2*np.pi*(yy*7+cs*0.8))*0.5+0.5)**3
joint=np.clip(1-np.abs(np.sin(np.pi*(xx*11+cs*1.5)))/0.06,0,1)
ch=cs*0.8+cc*0.6-strat*0.35-joint*0.5-np.clip(cj-0.8,0,1)*2
ch=(ch-ch.min())/(ch.max()-ch.min())
ca=C(.04,.04,.035)+C(.20,.20,.18)*ch[...,None]**1.3
moss2=np.clip(f2(6,4,64)*1.8-1.05,0,1)[...,None]*(1-strat[...,None]*0.5); ca=ca*(1-moss2*0.6)+C(.13,.17,.08)*moss2*0.6
Image.fromarray((np.clip(ca,0,1)**(1/2.2)*255).astype(np.uint8)).save('c_albedo.png')
gy,gx=np.gradient(ch*3.0,1.0/L*8); n=np.dstack([-gx,gy,np.ones_like(gx)*1.0]); n/=np.linalg.norm(n,axis=2,keepdims=True)
Image.fromarray(((n*0.5+0.5)*255).astype(np.uint8)).save('c_normal.png')
print('cliff ok')
