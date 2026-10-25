# Telegraph textures: radial crack (R=crack mask, G=normalised radius for reveal, B=width), footprint, cast bar frame, ritual icons, sky tint LUT.
import numpy as np, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os; O=os.path.join(os.path.dirname(__file__),'..','tex'); os.makedirs(O,exist_ok=True)
rnd=random.Random(3); S=1024
# radial cracks
im=Image.new('L',(S,S),0); d=ImageDraw.Draw(im)
def branch(x,y,a,L,w,depth):
    for _ in range(int(L)):
        a+=rnd.uniform(-0.35,0.35); nx=x+math.cos(a)*6; ny=y+math.sin(a)*6
        d.line((x,y,nx,ny),fill=255,width=max(1,int(w))); x,y=nx,ny; w*=0.993
        if depth<3 and rnd.random()<0.03: branch(x,y,a+rnd.choice([-1,1])*rnd.uniform(0.4,0.9),L*0.45,w*0.6,depth+1)
        if math.hypot(x-S/2,y-S/2)>S/2-8: break
for i in range(14): branch(S/2,S/2,i*6.283/14+rnd.uniform(-.2,.2),90,9,0)
d.ellipse((S/2-40,S/2-40,S/2+40,S/2+40),fill=255)
crack=np.asarray(im.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32)
halo=np.asarray(im.filter(ImageFilter.GaussianBlur(9))).astype(np.float32)
yy,xx=np.mgrid[0:S,0:S]; r=np.hypot(xx-S/2,yy-S/2)/(S/2)
rgb=np.dstack([crack, np.clip(r,0,1)*255+np.random.RandomState(1).rand(S,S)*6, np.clip(halo*2.5,0,255)]).clip(0,255).astype(np.uint8)
Image.fromarray(rgb).save(f'{O}/wb_crack_radial.png')
# fissure line (long strip) 256x1024: R crack, G along-length 0..1
W,H=256,1024; im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im); x=W/2; 
for y in range(0,H,6):
    nx=x+rnd.uniform(-7,7); nx=min(max(nx,60),W-60); d.line((x,y,nx,y+6),fill=255,width=int(14-10*y/H)+3); x=nx
    if rnd.random()<0.05:
        bx,by=x,y; a=rnd.choice([-1,1])
        for k in range(12): nbx=bx+a*rnd.uniform(3,8); d.line((bx,by,nbx,by+5),fill=255,width=2); bx,by=nbx,by+5
c=np.asarray(im.filter(ImageFilter.GaussianBlur(1))).astype(np.float32); h=np.asarray(im.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)
g=np.repeat(np.linspace(0,255,H)[:,None],W,1)
Image.fromarray(np.dstack([c,g,np.clip(h*2.5,0,255)]).astype(np.uint8)).save(f'{O}/wb_crack_fissure.png')
# footprint 512: R depth (1=deep), A coverage. Giant 4-toed stone foot.
S2=512; im=Image.new('L',(S2,S2),0); d=ImageDraw.Draw(im)
d.ellipse((150,190,362,470),fill=200); d.ellipse((170,140,342,300),fill=230)
for i,(cx,cy) in enumerate([(178,110),(232,82),(290,84),(342,116)]): d.ellipse((cx-34,cy-44,cx+34,cy+40),fill=255)
dep=np.asarray(im.filter(ImageFilter.GaussianBlur(14))).astype(np.float32)/255
n=np.random.RandomState(4).rand(S2//8,S2//8); n=np.asarray(Image.fromarray((n*255).astype(np.uint8)).resize((S2,S2),Image.BICUBIC))/255
rim=np.clip(np.asarray(im.filter(ImageFilter.GaussianBlur(30))).astype(np.float32)/255-dep*0.9,0,1)
cr=Image.new('L',(S2,S2),0); dc=ImageDraw.Draw(cr)
for i in range(18):
    a=i*6.283/18; x,y=256+math.cos(a)*120,280+math.sin(a)*150
    for k in range(10): nx=x+math.cos(a)*14+rnd.uniform(-6,6); ny=y+math.sin(a)*14+rnd.uniform(-6,6); dc.line((x,y,nx,ny),fill=255,width=2); x,y=nx,ny
cr=np.asarray(cr.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32)/255
R=dep*(0.8+0.2*n); A=np.clip(dep*1.6+rim*1.5+cr,0,1)
Image.fromarray((np.dstack([R,rim,cr,A])*255).astype(np.uint8),'RGBA').save(f'{O}/wb_footprint.png')
# cast bar frame 1024x128 (9-slice: 48px margins) + 3 icons 256
def frame():
    W,H=1024,128; im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((4,14,W-4,H-14),radius=22,fill=(24,10,6,235),outline=(255,140,40,255),width=6)
    d.rounded_rectangle((16,26,W-16,H-26),radius=14,outline=(120,40,10,255),width=3)
    for x in (4,W-4):
        d.polygon([(x,H/2-34),(x+(26 if x<10 else -26),H/2),(x,H/2+34)],fill=(255,170,60,255))
    im.save(f'{O}/wb_castbar_frame.png')
    im=Image.new('RGBA',(W-64,64),(0,0,0,0)); d=ImageDraw.Draw(im)
    for x in range(W-64):
        t=x/(W-64); d.line((x,0,x,63),fill=(255,int(90+130*t),int(20+40*t),255))
    im.save(f'{O}/wb_castbar_fill.png')
frame()
def icon(name,draw):
    im=Image.new('RGBA',(256,256),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.ellipse((8,8,248,248),fill=(30,12,8,255),outline=(255,140,40,255),width=10)
    draw(d); im=im.filter(ImageFilter.SMOOTH); im.save(f'{O}/wb_icon_{name}.png')
def fissure(d):
    d.polygon([(128,40),(150,70),(140,72),(170,110),(118,90),(128,130),(96,100),(88,60)],fill=(255,200,90))
    for a in range(5):
        x,y=128,170; aa=math.pi+a*math.pi/4
        for k in range(5): nx=x+math.cos(aa)*14+rnd.uniform(-5,5); ny=y-math.sin(aa)*10*0+rnd.uniform(-3,8)*(1 if a%2 else -1); d.line((x,y,nx,ny),fill=(255,110,20),width=7); x,y=nx,ny
    d.line((50,175,206,175),fill=(255,150,40),width=6)
def meteor(d):
    for i,(x,y) in enumerate([(160,90),(110,130),(180,150)]):
        d.line((x+40,y-50,x,y),fill=(255,150,40),width=14-3*i); d.ellipse((x-16,y-16,x+16,y+16),fill=(255,220,120))
    d.ellipse((60,185,196,215),outline=(255,60,30),width=6)
def wave(d):
    for k,yy in enumerate((110,150,190)):
        pts=[(40+x,yy+math.sin(x/18+k)*14) for x in range(0,177,4)]
        d.line(pts,fill=(255,120-25*k,20),width=14)
    d.ellipse((108,48,148,88),fill=(255,220,120))
icon('fissure_slam',fissure); icon('meteor_call',meteor); icon('lava_wave',wave)
# sky tint LUT: 16^3 strip (256x16) remap toward ash-red; Godot Texture3D via Environment adjustment_color_correction (slice 16x16 horiz)
N=16; lut=np.zeros((N,N*N,3))
for b in range(N):
    for g in range(N):
        for rr in range(N):
            c=np.array([rr,g,b])/(N-1); l=c@np.array([.3,.59,.11])
            t=np.array([min(1,l*1.35+0.08),l*0.55,l*0.35]); lut[g,b*N+rr]=c*0.35+t*0.65
Image.fromarray((lut*255).astype(np.uint8)).save(f'{O}/wb_sky_tint_lut.png')
print('ok')
