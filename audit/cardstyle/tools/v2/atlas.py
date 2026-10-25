# Shared trim atlas for card2 buildings: tiling strips (U wraps) + detail cells. One set for ALL buildings.
import numpy as np, os
from PIL import Image, ImageDraw
T='/workspace/beth-world/www/proto3d/models/beth/textures/realmed'
OUT='/workspace/beth-world/www/proto3d/models/beth/hi/buildings_card2/atlas'; os.makedirs(OUT,exist_ok=True)
S=2048
# strips: name -> (y0, h, metres covered by full width, band height m)
STRIPS={'stone':(0,512,6.0,1.5),'plaster':(512,256,6.0,0.75),'slate':(768,256,3.5*2,0.875),'oak':(1024,256,4.0,0.5),
        'beam':(1280,128,4.0,0.25),'iron':(1408,64,2.0,0.06),'gold':(1472,64,2.0,0.06)}
CELLS=['window','door','banner','sign_inn','sign_bread','sign_anvil','flowers','sign_potion']  # 256x512 each at y=1536
def hexc(h): return np.array([int(h[i:i+2],16) for i in(1,3,5)])/255
def noise(n,m,beta,seed):
    r=np.random.default_rng(seed); fy=np.fft.fftfreq(n)[:,None]; fx=np.fft.fftfreq(m)[None,:]
    k=np.sqrt(fx**2+fy**2); k[0,0]=1; s=np.fft.ifft2(np.fft.fft2(r.normal(size=(n,m)))/k**beta).real
    return (s-s.min())/(s.max()-s.min())
def L(n,k,mode='RGB'): return np.asarray(Image.open(f'{T}/{n}_{k}').convert(mode)).astype(np.float32)/255
def nrm(h,st):
    gx=(np.roll(h,-1,1)-np.roll(h,1,1))*st; gy=(np.roll(h,-1,0)-np.roll(h,1,0))*st
    v=np.stack([-gx,gy,np.ones_like(h)],-1); v/=np.linalg.norm(v,axis=-1,keepdims=True); return v*0.5+0.5
def build():
    A=np.zeros((S,S,3),np.float32); H=np.full((S,S),0.5,np.float32); R=np.full((S,S),0.8,np.float32); E=np.zeros((S,S,3),np.float32); M=np.zeros((S,S),np.float32)
    def put_tile(name,ys,h,tint=1.0):
        a=L(name,'albedo.jpg'); hh=L(name,'height.png','L'); r=L(name,'rough.png','L')
        a2=np.tile(a,(1,2,1))[:h]; A[ys:ys+h]=a2*tint; H[ys:ys+h]=np.tile(hh,(1,2))[:h]; R[ys:ys+h]=np.tile(r,(1,2))[:h]
    put_tile('fieldstone',0,512)
    pn=noise(256,S,1.6,4); pf=noise(256,S,1.1,5)
    A[512:768]=hexc('#E2CFAA')*0.80*(0.85+0.15*pn[...,None])*(0.92+0.08*pf[...,None]); H[512:768]=0.4+0.1*pf; R[512:768]=0.9
    sl=L('slate','albedo.jpg'); put_tile('slate',768,256,(hexc('#46638F')/hexc('#4a5664')))
    put_tile('oak',1024,256,hexc('#784F23')/hexc('#3a2a1d')*0.6)
    g=noise(128,S,1.0,9); gr=np.sin((np.arange(128)[:,None]/128*14+g*5)*np.pi)*0.5+0.5
    A[1280:1408]=hexc('#4A3220')*(0.6+0.5*gr[...,None]); H[1280:1408]=0.5+0.2*gr; R[1280:1408]=0.75
    A[1408:1472]=hexc('#2A2A2E')*(0.8+0.4*noise(64,S,1.2,11)[...,None]); R[1408:1472]=0.5; M[1408:1472]=1
    A[1472:1536]=hexc('#C8A240')*(0.85+0.25*noise(64,S,1.2,12)[...,None]); R[1472:1536]=0.35; M[1472:1536]=1
    # cells
    im=Image.fromarray((A*255).astype(np.uint8)); d=ImageDraw.Draw(im); em=Image.new('RGB',(S,S)); de=ImageDraw.Draw(em)
    OAK=(70,48,30); GOLD=(200,162,64); NAVY=(32,53,82); IR=(40,40,44)
    for i,c in enumerate(CELLS):
        x0,y0=i*256,1536; x1,y1=x0+255,y0+511
        if c=='window':
            d.rectangle([x0,y0,x1,y1],fill=OAK); d.rectangle([x0+22,y0+22,x1-22,y1-22],fill=(224,160,64)); de.rectangle([x0+22,y0+22,x1-22,y1-22],fill=(255,178,74))
            for k in range(-12,13):
                d.line([(x0+22+k*36,y0+22),(x0+22+k*36+470,y0+22+470)],fill=(60,45,30),width=3); d.line([(x1-22-k*36,y0+22),(x1-22-k*36-470,y0+22+470)],fill=(60,45,30),width=3)
            d.rectangle([x0,y0,x0+22,y1],fill=OAK);d.rectangle([x1-22,y0,x1,y1],fill=OAK);d.rectangle([x0,y0,x1,y0+22],fill=OAK);d.rectangle([x0,y1-22,x1,y1],fill=OAK)
            d.rectangle([x0+118,y0,x0+138,y1],fill=OAK); d.rectangle([x0,y0+246,x1,y0+266],fill=OAK); de.rectangle([x0+118,y0,x0+138,y1],fill=0); de.rectangle([x0,y0+246,x1,y0+266],fill=0)
        elif c=='door':
            # stone surround (from stone strip) then arched oak door
            st=im.crop((x0,0,x0+256,512)); im.paste(st,(x0,y0)); d=ImageDraw.Draw(im)
            d.ellipse([x0+20,y0+20,x1-20,y0+236],fill=(150,140,125)); d.rectangle([x0+20,y0+128,x1-20,y1],fill=(150,140,125))
            d.ellipse([x0+40,y0+40,x1-40,y0+216],fill=OAK); d.rectangle([x0+40,y0+128,x1-40,y1],fill=OAK)
            for k in range(1,5): d.line([(x0+40+k*35,y0+40),(x0+40+k*35,y1)],fill=(45,30,20),width=4)
            for yy in(y0+170,y0+400): d.rectangle([x0+44,yy,x1-44,yy+14],fill=IR)
            d.ellipse([x0+170,y0+290,x0+186,y0+306],fill=GOLD)
        elif c=='banner':
            L2=Image.new('RGB',(512,1024),(31,60,122)); dl=ImageDraw.Draw(L2); G=(214,172,64); Gd=(150,110,35)
            nz=noise(1024,512,1.6,77); L2=Image.fromarray((np.asarray(L2)*(0.85+0.25*nz[...,None])).clip(0,255).astype(np.uint8)); dl=ImageDraw.Draw(L2)
            dl.rectangle([0,0,511,40],fill=G); dl.rectangle([0,0,26,880],fill=G); dl.rectangle([485,0,511,880],fill=G)
            dl.polygon([(0,880),(256,1010),(511,880),(511,860),(256,985),(0,860)],fill=G)
            for k in range(14): dl.line([(18+k*34,40),(18+k*34,52)],fill=Gd,width=6)
            # rampant lion facing left, scaled up
            import math
            def P(pts): return [(x*1.0+20,y*1.0+60) for x,y in pts]
            body=P([(250,330),(300,300),(330,360),(320,470),(300,560),(260,610),(220,600),(205,520),(215,420)])
            dl.polygon(body,fill=G)
            mane=[(200+70*math.cos(a)*(1.25 if k%2 else 1.0),300+75*math.sin(a)*(1.25 if k%2 else 1.0)) for k,a in enumerate(np.linspace(0,2*np.pi,22,endpoint=False))]
            dl.polygon(P(mane),fill=G); dl.ellipse(P([(150,255),(235,340)]),fill=G)
            dl.polygon(P([(150,285),(105,300),(110,325),(150,330)]),fill=G)  # muzzle
            dl.ellipse(P([(170,282),(184,296)]),fill=(31,60,122)); dl.polygon(P([(115,318),(145,322),(130,345)]),fill=(170,40,40)) # eye, tongue
            dl.polygon(P([(160,230),(170,180),(190,215),(205,170),(220,215),(240,180),(245,235)]),fill=G)  # crown
            for (sx,sy,ex,ey) in((240,360,120,300),(250,410,110,420)):
                dl.line(P([(sx,sy),(ex,ey)]),fill=G,width=34); dl.polygon(P([(ex-10,ey-20),(ex-45,ey-30),(ex-40,ey),(ex-45,ey+25),(ex-5,ey+20)]),fill=G)
            dl.line(P([(250,580),(190,690),(210,780)]),fill=G,width=38); dl.polygon(P([(190,770),(150,800),(240,800),(235,770)]),fill=G)
            dl.line(P([(300,570),(330,680),(300,770)]),fill=G,width=34); dl.polygon(P([(280,760),(260,790),(340,790),(320,760)]),fill=G)
            dl.line(P([(320,520),(400,560),(390,430),(430,360)]),fill=G,width=16); dl.polygon(P([(420,340),(460,300),(450,370),(470,390),(425,380)]),fill=G)
            for k in range(3): dl.line(P([(225,430+k*40),(300,420+k*40)]),fill=Gd,width=5)
            im.paste(L2.resize((256,512),Image.LANCZOS),(x0,y0)); d=ImageDraw.Draw(im)
        elif c.startswith('sign'):
            d.rectangle([x0,y0,x1,y1],fill=NAVY); d.rectangle([x0+10,y0+10,x1-10,y1-10],outline=GOLD,width=14)
            cx,cy=x0+128,y0+256
            if c=='sign_inn': d.rectangle([cx-50,cy-60,cx+40,cy+70],fill=GOLD); d.ellipse([cx+20,cy-30,cx+80,cy+40],outline=GOLD,width=16); d.ellipse([cx-60,cy-90,cx+50,cy-40],fill=(240,232,210))
            if c=='sign_bread': d.ellipse([cx-90,cy-50,cx+90,cy+60],fill=GOLD); [d.line([(cx-50+k*35,cy-40),(cx-30+k*35,cy+40)],fill=(140,100,40),width=8) for k in range(4)]
            if c=='sign_anvil': d.polygon([(cx-90,cy-40),(cx+90,cy-40),(cx+40,cy),(cx+30,cy+60),(cx-30,cy+60),(cx-40,cy)],fill=GOLD); d.rectangle([cx-60,cy+60,cx+60,cy+80],fill=GOLD)
            if c=='sign_potion': d.ellipse([cx-70,cy-20,cx+70,cy+110],fill=GOLD); d.rectangle([cx-20,cy-90,cx+20,cy-10],fill=GOLD); d.ellipse([cx-40,cy+20,cx+40,cy+90],fill=(60,140,90))
        elif c=='flowers':
            d.rectangle([x0,y0,x1,y1],fill=(52,72,34)); r=np.random.default_rng(3)
            for k in range(260):
                x=x0+r.integers(0,256); y=y0+r.integers(0,512); col=[(200,40,50),(230,120,160),(240,210,80),(250,250,240),(150,60,160)][r.integers(0,5)]
                d.ellipse([x-9,y-9,x+9,y+9],fill=col) if r.random()<0.6 else d.ellipse([x-12,y-6,x+12,y+6],fill=(70,105,40))
    A=np.asarray(im).astype(np.float32)/255; E=np.asarray(em).astype(np.float32)/255
    cy=slice(1536,2048); H[cy]=0.5+0.3*(A[cy].mean(-1)-0.3); R[cy]=0.7
    R[1536:2048,0:256][E[1536:2048,0:256].max(-1)>0.1]=0.25
    N=nrm(H,6.0)
    O=np.stack([np.ones_like(R),R,M],-1)
    sv=lambda a,f,q=90:Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)).save(f'{OUT}/{f}',quality=q)
    sv(A,'card2_albedo.jpg');sv(N,'card2_normal.jpg',94);sv(O,'card2_orm.jpg');sv(E,'card2_emissive.jpg')
    return A,N,O,E
if __name__=='__main__': build(); print('atlas ok')
