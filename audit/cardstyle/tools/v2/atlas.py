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
            L2=Image.new('RGB',(512,1024),(31,60,122)); dl=ImageDraw.Draw(L2); G=(214,172,64); Gd=(150,110,35)
            nz=noise(1024,512,1.6,77); L2=Image.fromarray((np.asarray(L2)*(0.85+0.25*nz[...,None])).clip(0,255).astype(np.uint8)); dl=ImageDraw.Draw(L2)
            dl.rectangle([0,0,511,40],fill=G); dl.rectangle([0,0,26,880],fill=G); dl.rectangle([485,0,511,880],fill=G)
            dl.polygon([(0,880),(256,1010),(511,880),(511,860),(256,985),(0,860)],fill=G)
            for k in range(14): dl.line([(18+k*34,40),(18+k*34,52)],fill=Gd,width=6)
            # heraldic lion rampant (facing the hoist, viewer's left), drawn 4x supersampled with a dark-gold outline
            import math
            SS=4; Z=Image.new('L',(512*SS,1024*SS),0); O=Image.new('L',(512*SS,1024*SS),0); dz=ImageDraw.Draw(Z); do=ImageDraw.Draw(O)
            def T(p): return (p[0]*SS,(p[1]+40)*SS)
            def limb(pts,w):
                for D,ww in((do,w+18),(dz,w)):
                    q=[T(p) for p in pts]; D.line(q,fill=255,width=ww*SS,joint='curve')
                    for p in q: D.ellipse([p[0]-ww*SS/2,p[1]-ww*SS/2,p[0]+ww*SS/2,p[1]+ww*SS/2],fill=255)
            def blob(pts,o=True):
                q=[T(p) for p in pts]
                if o: do.polygon(q,fill=255,outline=255,width=18*SS)
                dz.polygon(q,fill=255)
            def claws(p,ang):
                for k in(-1,0,1):
                    a2=ang+k*0.45; e=(p[0]+38*math.cos(a2),p[1]+38*math.sin(a2)); limb([p,e],9)
            # tail: S-curve rising behind, ending in a flame tuft
            limb([(300,560),(350,600),(395,560),(400,470),(370,400),(385,330)],22)
            blob([(385,330),(350,270),(390,300),(400,240),(420,300),(450,260),(430,330),(400,350)])
            # hind legs: one planted, one striding forward
            limb([(290,560),(330,650),(300,740),(330,800)],52); claws((330,805),0.2)
            limb([(250,560),(200,640),(150,700),(110,720)],48); claws((105,722),3.0)
            # torso: deep chest tapering to narrow waist and haunch
            blob([(160,300),(250,270),(300,330),(310,430),(330,520),(320,590),(260,600),(220,540),(200,450),(150,380)])
            # forelegs raised, paws out with claws
            limb([(195,330),(110,320),(55,270)],44); claws((50,262),-2.4)
            limb([(205,410),(120,430),(60,400)],40); claws((52,396),-2.9)
            # mane: ring of flame-like locks round the head and down the chest
            cx,cy=200,205
            for k in range(16):
                a2=-math.pi*0.15+k*(2*math.pi/16); r0=62; r1=112 if k%2 else 94
                blob([(cx+r0*math.cos(a2-0.22),cy+r0*math.sin(a2-0.22)),(cx+r1*math.cos(a2),cy+r1*math.sin(a2)),(cx+r0*math.cos(a2+0.22),cy+r0*math.sin(a2+0.22))])
            dz.ellipse([T((cx-70,cy-70))[0],T((cx-70,cy-70))[1],T((cx+70,cy+70))[0],T((cx+70,cy+70))[1]],fill=255)
            # head: snout open to the left, tongue, ears and a crown
            blob([(150,170),(105,178),(88,200),(98,218),(128,220),(108,234),(132,250),(175,245)])
            blob([(185,140),(195,108),(215,138)])
            blob([(160,95),(165,40),(185,70),(205,25),(225,70),(245,40),(250,95)])
            Zs=Z.resize((512,1024),Image.LANCZOS); Os=O.resize((512,1024),Image.LANCZOS)
            L2.paste(Image.new('RGB',(512,1024),Gd),(0,0),Os); L2.paste(Image.new('RGB',(512,1024),G),(0,0),Zs)
            dl=ImageDraw.Draw(L2)
            dl.ellipse([150,222,166,238],fill=(31,60,122)); dl.polygon([(100,262),(128,262),(112,282)],fill=(170,40,40))   # eye, tongue
            for k in range(4): dl.arc([170,330+k*38,300,400+k*38],200,330,fill=Gd,width=5)      # ribs/fur shading
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
    R[1536:2048,0:256][E[1536:2048,0:256].max(-1)>0.1]=0.25; R[656:768,0:128][E[656:768,0:128].max(-1)>0.1]=0.2
    N=nrm(H,6.0)
    O=np.stack([np.ones_like(R),R,M],-1)
    sv=lambda a,f,q=90:Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)).save(f'{OUT}/{f}',quality=q)
    sv(A,'card2_albedo.jpg');sv(N,'card2_normal.jpg',94);sv(O,'card2_orm.jpg');sv(E,'card2_emissive.jpg')
    return A,N,O,E
if __name__=='__main__': build(); print('atlas ok')
