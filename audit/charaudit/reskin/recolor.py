import numpy as np,sys
from PIL import Image
def hsv(n):
    im=Image.open(f'{n}_base.png').convert('RGB'); a=np.asarray(im.convert('HSV')).astype(float)/255; return np.asarray(im).astype(float)/255,a
def tohsvimg(H,S,V):
    return Image.fromarray(np.dstack([(np.clip(x,0,1)*255).astype(np.uint8) for x in (H,S,V)]),'HSV').convert('RGB')
def hd(h,c): d=np.abs(h-c); return np.minimum(d,1-d)
def smooth(x,a,b): return np.clip((x-a)/(b-a),0,1)
def run(n):
    rgb,a=hsv(n); H,S,V=a[...,0],a[...,1],a[...,2]; L=np.load(f'lab_{n}.npy')
    head=(L==1); hand=(L==6)
    skin=(hd(H,0.06)<0.05)&(S>0.2)&(S<0.65)&(V>0.35)
    nH,nS,nV=H.copy(),S.copy(),V.copy()
    def setc(m,h,s,vg=1.0,vadd=0.0,smul=None):
        m=m.astype(float)
        th=h; nH[:]=np.where(m>0.5,th,nH); 
        tS=s if smul is None else np.clip(S*smul,0,1)
        nS[:]=nS*(1-m)+tS*m; nV[:]=nV*(1-m)+np.clip(V*vg+vadd,0,1)*m
    gold=(hd(H,0.12)<0.05)&(S>0.35)&(V>0.4)
    body=~head&~hand
    if n=='rook':
        legs=(L==10)|(L==11)|(L==12)
        cloak=body&~gold&~skin&(S<0.45)&~legs
        setc(cloak,0.3,0.38,1.12,0.02)
        setc(body&legs&~gold,0.075,0.45,1.0)
        leather=body&(hd(H,0.07)<0.06)&(S>=0.45)&~gold
        setc(leather,0.07,0.55,1.1)
    if n=='talia':
        m=body&~gold&~skin
        w=smooth(V,0.22,0.5)
        nH[m]=0.48; nS[m]=(0.5*(1-w)+0.07*w)[m]; nV[m]=np.clip(V*1.25+0.1,0,1)[m]
    if n=='cedric':
        red=body&((H<0.03)|(H>0.93))&(S>0.2)
        setc(red,0.985,0.78,1.45,0.04)
        blue=body&~red&~gold&~skin&(V<0.5)&(L!=9)&((L==2)|(L==3)|(L==4)|(L==5)|(L==7))&~((hd(H,0.07)<0.05)&(S>0.4))
        setc(blue,0.62,0.6,1.6,0.06)
    if n=='morwen':
        m=body&~gold&~skin
        setc(m,0.76,0.42,1.6,0.05)
        hm=head&~skin&(V<0.35)
        setc(hm,0.76,0.35,1.5,0.03)
    if n=='nyx':
        m=body&~gold&~skin
        cape=m&((L==7)|(L==10)|(L==3))&(S<0.4)&(V<0.35)
        setc(m,H.mean(),None,1.3,0.03,smul=1.0)
        red=m&((H<0.04)|(H>0.93))&(S>0.25)
        setc(red,0.99,0.8,1.6,0.05)
    if n=='garruk':
        sk=skin&body
        setc(sk,0.055,None,1.12,0.02,smul=1.1)
        red=body&((H<0.03)|(H>0.93))&(S>0.3)
        setc(red,0.995,None,1.2,0.02,smul=1.1)
    out=tohsvimg(nH,nS,nV)
    out.save(f'new_{n}.png')
for n in sys.argv[1:]: run(n)
