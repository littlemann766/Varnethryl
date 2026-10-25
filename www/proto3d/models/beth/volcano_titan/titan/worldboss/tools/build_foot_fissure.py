# v2 footprint (traced from the Titan's left sole, toes = +V/up in texture = +Z) and v2 thick jagged fissure.
import numpy as np, math, random, os, trimesh
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage
O=os.path.join(os.path.dirname(__file__),'..','tex'); rnd=random.Random(11)
s=trimesh.load(os.path.join(os.path.dirname(__file__),'../../ashentitan_volcano_glow.glb'),force='mesh')
v=np.asarray(s.vertices); f=v[(v[:,1]<0.6)&(v[:,0]>0)]
lo=f[:,[0,2]].min(0); hi=f[:,[0,2]].max(0); c=(lo+hi)/2+np.array([0,-1.2]); span=(hi-lo).max()*1.6
S=512; im=Image.new('L',(S,S),0); d=ImageDraw.Draw(im)
for x,z in f[:,[0,2]]:
    px=(x-c[0])/span*S+S/2; pz=S/2-(z-c[1])/span*S; d.ellipse((px-10,pz-10,px+10,pz+10),fill=255)
d2=ImageDraw.Draw(im); ys_,xs_=np.nonzero(np.asarray(im)>128); top=ys_.min(); cxx=xs_[ys_<top+60].mean()
for k,dx in enumerate((-70,-5,60)):   # 3 blunt stone toes + claw gouges at the front (texture top before flip)
    tx=cxx+dx*0.9; ty=top+18+abs(dx)*0.35; d2.ellipse((tx-34,ty-46,tx+34,ty+30),fill=255)
    d2.polygon([(tx-12,ty-40),(tx+12,ty-40),(tx+dx*0.15,ty-95)],fill=255)
m=np.asarray(im)>128; m=ndimage.binary_closing(m,iterations=6); m=ndimage.binary_fill_holes(m); m=ndimage.binary_opening(m,iterations=3)
sil=Image.fromarray((m*255).astype(np.uint8))
dep=np.asarray(sil.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255           # pressed depth
edge=np.asarray(sil.filter(ImageFilter.GaussianBlur(26))).astype(np.float32)/255
rim=np.clip(edge*1.6-dep*1.3,0,1)                                                    # pushed-up ring of earth
# toe pads: local maxima of distance transform in the front half -> deeper
dt=ndimage.distance_transform_edt(m).astype(np.float32); dt/=dt.max()
# radial cracks from the edge
cr=Image.new('L',(S,S),0); dc=ImageDraw.Draw(cr); ys,xs=np.nonzero(ndimage.binary_dilation(m,iterations=2)&~m)
cy,cx=np.mean(np.nonzero(m),axis=1)
for i in range(0,len(xs),max(1,len(xs)//34)):
    x,y=float(xs[i]),float(ys[i]); a=math.atan2(y-cy,x-cx); w=4
    for k in range(rnd.randint(5,11)):
        a+=rnd.uniform(-.4,.4); nx=x+math.cos(a)*9; ny=y+math.sin(a)*9; dc.line((x,y,nx,ny),fill=255,width=max(1,int(w))); x,y=nx,ny; w*=0.82
cr=np.asarray(cr.filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32)/255
inner=np.asarray(sil.filter(ImageFilter.GaussianBlur(3))).astype(np.float32)/255
R=np.clip(dep*0.6+dt*0.6,0,1)*inner
A=np.clip(inner*0.95+rim*1.2+cr,0,1)
Image.fromarray((np.dstack([R,rim,cr,A])*255).astype(np.uint8),'RGBA').transpose(Image.FLIP_TOP_BOTTOM).save(f'{O}/wb_footprint.png')
print('sole size (native m):', span/1.8654, 'texture covers', span/1.8654)
# fissure: thick jagged chasm 256x1024, R crack, G length 0..1, B halo
W,H=256,1024; im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im); x=W/2; L=[];Rr=[]
for y in range(0,H+12,12):
    x=min(max(x+rnd.uniform(-16,16),70),W-70); w=(1-y/H)*30+10+rnd.uniform(-5,5); L.append((x-w*rnd.uniform(.6,1),y)); Rr.append((x+w*rnd.uniform(.6,1),y))
d.polygon(L+Rr[::-1],fill=255)
for k in range(28):  # side branches
    i=rnd.randrange(len(L)); s_=rnd.choice([-1,1]); p=(L if s_<0 else Rr)[i]; bx,by=p; w=7
    for j in range(rnd.randint(4,9)):
        nbx=bx+s_*rnd.uniform(6,12); nby=by+rnd.uniform(-8,10); d.line((bx,by,nbx,nby),fill=255,width=max(1,int(w))); bx,by=nbx,nby; w*=0.75
c=np.asarray(im.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32)
h=np.asarray(im.filter(ImageFilter.GaussianBlur(16))).astype(np.float32)
g=np.repeat(np.linspace(0,255,H)[:,None],W,1)
Image.fromarray(np.dstack([c,g,np.clip(h*2.2,0,255)]).astype(np.uint8)).save(f'{O}/wb_crack_fissure.png'); print('ok')
