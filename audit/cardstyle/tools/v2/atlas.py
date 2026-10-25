# Shared trim atlas for card2 buildings: tiling strips (U wraps) + detail cells. One set for ALL buildings.
import numpy as np, os
from PIL import Image, ImageDraw
T='/workspace/beth-world/www/proto3d/models/beth/textures/realmed'
OUT='/workspace/beth-world/www/proto3d/models/beth/hi/buildings_card2/atlas'; os.makedirs(OUT,exist_ok=True)
S=2048
# strips: name -> (y0, h, metres covered by full width, band height m)
STRIPS={'stone':(0,384,6.0,1.125),'ashlar':(384,96,12.0,0.8),'statue':(480,16,3.0,1.0),'rock':(496,16,4.0,1.5),'plaster':(512,128,6.0,0.75),'bluestone':(640,16,3.0,1.0),'slate':(768,256,3.5*2,0.875),'oak':(1024,256,4.0,0.5),
        'beam':(1280,128,4.0,0.25),'iron':(1408,64,2.0,0.06),'gold':(1472,64,2.0,0.06)}
RECTS={'bluewin':(0,656,128,112),'water':(384,656,1664,112),'leaf':(256,656,128,112),'sign_book':(128,656,64,112),'sign_sword':(192,656,64,112)}  # extra detail rects (x,y,w,h)
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
    put_tile('fieldstone',0,384)
    # cream cut-stone (ashlar) strip: 2 courses per band, staggered blocks, recessed mortar; U-periodic
    r=np.random.default_rng(21); ys,h=384,96; cream=hexc('#DCCBA6'); nz=noise(h,S,1.4,31); nf=noise(h,S,0.8,32)
    a=np.zeros((h,S,3),np.float32); hh=np.ones((h,S),np.float32)*0.7
    for row in range(2):
        y0,y1=row*48,row*48+48; x=int(r.integers(0,120)); xs=[]
        while x<S+x: 
            xs.append(x); x+=int(r.integers(90,175))
            if x>=S: break
        xs=[0]+[v for v in xs if 20<v<S-20]+[S]
        for i in range(len(xs)-1):
            tint=cream*(0.88+0.16*r.random())*np.array([1,0.99+0.02*r.random(),0.97+0.05*r.random()])
            a[y0:y1,xs[i]:xs[i+1]]=tint
            hh[y0:y1,xs[i]:xs[i]+3]=0.25; hh[y0:y1,xs[i+1]-2:xs[i+1]]=0.4
        hh[y0:y0+3]=0.25; hh[y1-2:y1]=0.4; a[y0:y0+3]=hexc('#9C9078'); 
        for i in range(len(xs)): a[y0:y1,max(0,xs[i]-1):xs[i]+3]=hexc('#9C9078')
    a*= (0.82+0.25*nz[...,None])*(0.94+0.1*nf[...,None]); A[ys:ys+h]=a; H[ys:ys+h]=hh*(0.85+0.15*nf); R[ys:ys+h]=0.82
    st=noise(16,S,1.2,41); A[480:496]=hexc('#BDB6A8')*(0.9+0.15*st[...,None]); H[480:496]=0.5+0.05*st; R[480:496]=0.6
    rk=noise(16,S,1.0,43); rm=noise(16,S,1.6,44)
    A[496:512]=hexc('#5E5850')*(0.65+0.6*rk[...,None]); moss=(rm>0.62)[...,None]; A[496:512]=np.where(moss,hexc('#4E5A30')*(0.8+0.3*rk[...,None]),A[496:512]); H[496:512]=0.3+0.5*rk; R[496:512]=0.92
    pn=noise(256,S,1.6,4); pf=noise(256,S,1.1,5)
    A[512:768]=hexc('#E2CFAA')*0.80*(0.85+0.15*pn[...,None])*(0.92+0.08*pf[...,None]); H[512:768]=0.4+0.1*pf; R[512:768]=0.9
    bs=noise(16,S,1.2,51); A[640:656]=hexc('#6F7E8E')*(0.8+0.35*bs[...,None]); H[640:656]=0.5+0.1*bs; R[640:656]=0.5
    # water: deep teal with ripple height + foam streaks
    wx=np.arange(1792)[None,:]; wy=np.arange(112)[:,None]; wn=noise(112,1792,1.3,61); wf=noise(112,1792,0.9,62)
    rip=0.5+0.18*np.sin(wx*0.09+wn*9)*np.cos(wy*0.21+wx*0.02)+0.25*(wn-0.5)
    foam=np.clip((wf-0.68)*5,0,1)*(np.sin(wx*0.05+wn*12)>0.3)
    col=hexc('#1E4A5C')*(0.75+0.5*rip[...,None]); col=col*(1-foam[...,None])+hexc('#E8EEEA')*foam[...,None]
    A[656:768,384:2048]=col[:,:1664]; H[656:768,384:2048]=rip[:,:1664]; R[656:768,384:2048]=(0.08+0.5*foam)[:,:1664]
    # ivy leaf: one pointed leaf filling the rect on a dark-green surround (no alpha needed: leaves are cut as geometry)
    lx=np.linspace(-1,1,128)[None,:]; ly=np.linspace(-1,1,112)[:,None]; ln=noise(112,128,1.2,71)
    leafm=(np.abs(lx)<(1-np.abs(ly))**0.7*0.95); vein=np.exp(-(lx/0.04)**2)+0.5*np.exp(-((np.abs(lx)-(0.5*(ly+1)*0.6))/0.03)**2)*(np.abs(lx)<0.6)
    lc=hexc('#3F6B2A')*(0.75+0.45*ln[...,None])+hexc('#9BBF5A')[None,None,:]*0.25*vein[...,None]
    A[656:768,256:384]=np.where(leafm[...,None],lc,hexc('#2C4A1E')); H[656:768,256:384]=0.5+0.15*leafm-0.1*vein; R[656:768,256:384]=0.55
    sl=L('slate','albedo.jpg'); put_tile('slate',768,256,(hexc('#46638F')/hexc('#4a5664')))
    put_tile('oak',1024,256,hexc('#784F23')/hexc('#3a2a1d')*0.6)
    g=noise(128,S,1.0,9); gr=np.sin((np.arange(128)[:,None]/128*14+g*5)*np.pi)*0.5+0.5
    A[1280:1408]=hexc('#4A3220')*(0.6+0.5*gr[...,None]); H[1280:1408]=0.5+0.2*gr; R[1280:1408]=0.75
    A[1408:1472]=hexc('#2A2A2E')*(0.8+0.4*noise(64,S,1.2,11)[...,None]); R[1408:1472]=0.5; M[1408:1472]=1
    A[1472:1536]=hexc('#C8A240')*(0.85+0.25*noise(64,S,1.2,12)[...,None]); R[1472:1536]=0.35; M[1472:1536]=1
    # cells
    im=Image.fromarray((A*255).astype(np.uint8)); d=ImageDraw.Draw(im); em=Image.new('RGB',(S,S)); de=ImageDraw.Draw(em)
    OAK=(70,48,30); GOLD=(200,162,64); NAVY=(32,53,82); IR=(40,40,44)
    x0,y0,w,h=RECTS['bluewin']; x1,y1=x0+w-1,y0+h-1; BL=(85,155,255); dB=(30,40,70)
    d.rectangle([x0,y0,x1,y1],fill=(60,62,70)); d.rectangle([x0+8,y0+8,x1-8,y1-8],fill=BL); de.rectangle([x0+8,y0+8,x1-8,y1-8],fill=(70,150,255))
    for k in range(-8,9): d.line([(x0+8+k*14,y0+8),(x0+8+k*14+100,y0+108)],fill=dB,width=2); d.line([(x1-8-k*14,y0+8),(x1-8-k*14-100,y0+108)],fill=dB,width=2)
    d.rectangle([x0+60,y0,x0+67,y1],fill=(60,62,70)); de.rectangle([x0+60,y0,x0+67,y1],fill=0); d.rectangle([x0,y0,x0+8,y1],fill=(60,62,70)); d.rectangle([x1-8,y0,x1,y1],fill=(60,62,70))
    for nm in('sign_book','sign_sword'):
        x0,y0,w,h=RECTS[nm]; x1,y1=x0+w-1,y0+h-1; cx,cy=x0+w//2,y0+h//2
        d.rectangle([x0,y0,x1,y1],fill=NAVY); d.rectangle([x0+3,y0+3,x1-3,y1-3],outline=GOLD,width=4)
        if nm=='sign_book': d.polygon([(cx-22,cy-14),(cx,cy-8),(cx+22,cy-14),(cx+22,cy+18),(cx,cy+24),(cx-22,cy+18)],fill=(236,226,200)); d.line([(cx,cy-8),(cx,cy+24)],fill=GOLD,width=3); d.rectangle([cx-24,cy+18,cx+24,cy+22],fill=GOLD)
        else: d.line([(cx,cy-38),(cx,cy+26)],fill=(210,214,222),width=7); d.rectangle([cx-16,cy+20,cx+16,cy+26],fill=GOLD); d.rectangle([cx-3,cy+26,cx+3,cy+40],fill=(90,60,30)); d.polygon([(cx-4,cy-38),(cx,cy-46),(cx+4,cy-38)],fill=(210,214,222))
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
            st=im.crop((x0,0,x0+256,384)).resize((256,512)); im.paste(st,(x0,y0)); d=ImageDraw.Draw(im)
            d.ellipse([x0+20,y0+20,x1-20,y0+236],fill=(150,140,125)); d.rectangle([x0+20,y0+128,x1-20,y1],fill=(150,140,125))
            d.ellipse([x0+40,y0+40,x1-40,y0+216],fill=OAK); d.rectangle([x0+40,y0+128,x1-40,y1],fill=OAK)
            for k in range(1,5): d.line([(x0+40+k*35,y0+40),(x0+40+k*35,y1)],fill=(45,30,20),width=4)
            for yy in(y0+170,y0+400): d.rectangle([x0+44,yy,x1-44,yy+14],fill=IR)
            d.ellipse([x0+170,y0+290,x0+186,y0+306],fill=GOLD)
        elif c=='banner':
            # heraldic gold lion rampant on royal blue (art/lion_banner_src.jpg, flat front-on source), downsampled with sharpening
            import os
            from PIL import ImageFilter
            src=Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'art','lion_banner_src.jpg')).convert('RGB')
            src=src.resize((256,512),Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2,percent=80,threshold=2))
            im.paste(src,(x0,y0)); d=ImageDraw.Draw(im)
        elif c.startswith('sign'):
            d.rectangle([x0,y0,x1,y1],fill=NAVY); d.rectangle([x0+10,y0+10,x1-10,y1-10],outline=GOLD,width=14)
            cx,cy=x0+128,y0+256
            if c=='sign_inn': d.rectangle([cx-50,cy-60,cx+40,cy+70],fill=GOLD); d.ellipse([cx+20,cy-30,cx+80,cy+40],outline=GOLD,width=16); d.ellipse([cx-60,cy-90,cx+50,cy-40],fill=(240,232,210))
            if c=='sign_bread': d.ellipse([cx-90,cy-50,cx+90,cy+60],fill=GOLD); [d.line([(cx-50+k*35,cy-40),(cx-30+k*35,cy+40)],fill=(140,100,40),width=8) for k in range(4)]
            if c=='sign_anvil': d.polygon([(cx-90,cy-40),(cx+90,cy-40),(cx+40,cy),(cx+30,cy+60),(cx-30,cy+60),(cx-40,cy)],fill=GOLD); d.rectangle([cx-60,cy+60,cx+60,cy+80],fill=GOLD)
            if c=='sign_potion': d.ellipse([cx-70,cy-20,cx+70,cy+110],fill=GOLD); d.rectangle([cx-20,cy-90,cx+20,cy-10],fill=GOLD); d.ellipse([cx-40,cy+20,cx+40,cy+90],fill=(60,140,90))
        elif c=='flowers':
            # top 320px: foliage with clear pointed leaves + readable 5-petal blooms (bushes / pots);
            # bottom 192px: four flower-head swatches (red, pink, yellow, white) on leaf green for modelled flower heads
            import math
            SS=3; F=Image.new('RGB',(256*SS,512*SS),(46,70,30)); df=ImageDraw.Draw(F); r=np.random.default_rng(3)
            LG=[(58,92,38),(76,112,44),(96,134,54),(48,80,32)]
            def leafp(cx,cy,L,a,col):
                pts=[(cx+L*math.cos(a)*t-L*0.32*math.sin(a)*math.sin(math.pi*t)*s,cy+L*math.sin(a)*t+L*0.32*math.cos(a)*math.sin(math.pi*t)*s) for s in(1,-1) for t in (np.linspace(0,1,8) if s>0 else np.linspace(1,0,8))]
                df.polygon(pts,fill=col); df.line([(cx,cy),(cx+L*math.cos(a)*0.95,cy+L*math.sin(a)*0.95)],fill=tuple(int(v*0.7) for v in col),width=2*SS)
            def bloom(cx,cy,R,col):
                for k in range(5):
                    a=k*2*math.pi/5-math.pi/2; px,py=cx+R*0.55*math.cos(a),cy+R*0.55*math.sin(a)
                    df.ellipse([px-R*0.5,py-R*0.5,px+R*0.5,py+R*0.5],fill=col,outline=tuple(int(v*0.75) for v in col),width=SS)
                df.ellipse([cx-R*0.28,cy-R*0.28,cx+R*0.28,cy+R*0.28],fill=(235,190,60) if col!=(245,205,70) else (170,90,30))
            for k in range(420): leafp(r.uniform(0,256*SS),r.uniform(0,320*SS),r.uniform(14,26)*SS,r.uniform(0,2*math.pi),LG[r.integers(0,4)])
            COL=[(200,40,55),(232,120,165),(245,205,70),(248,246,236),(150,70,170)]
            for k in range(34): bloom(r.uniform(12,244)*SS,r.uniform(12,308)*SS,r.uniform(11,16)*SS,COL[r.integers(0,5)])
            for q,col in enumerate(COL[:4]):
                sx,sy=(q%2)*128*SS,(320+(q//2)*96)*SS
                df.rectangle([sx,sy,sx+128*SS,sy+96*SS],fill=(52,82,34)); bloom(sx+64*SS,sy+48*SS,40*SS,col)
            im.paste(F.resize((256,512),Image.LANCZOS),(x0,y0))
    A=np.asarray(im).astype(np.float32)/255; E=np.asarray(em).astype(np.float32)/255
    cy=slice(1536,2048); H[cy]=0.5+0.3*(A[cy].mean(-1)-0.3); R[cy]=0.7
    R[1536:2048,0:256][E[1536:2048,0:256].max(-1)>0.1]=0.25; R[656:768,0:128][E[656:768,0:128].max(-1)>0.1]=0.2
    N=nrm(H,6.0)
    O=np.stack([np.ones_like(R),R,M],-1)
    sv=lambda a,f,q=90:Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)).save(f'{OUT}/{f}',quality=q)
    sv(A,'card2_albedo.jpg');sv(N,'card2_normal.jpg',94);sv(O,'card2_orm.jpg');sv(E,'card2_emissive.jpg')
    return A,N,O,E
if __name__=='__main__': build(); print('atlas ok')
