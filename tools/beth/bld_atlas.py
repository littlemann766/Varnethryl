# Building atlas 1024 (4x4 x 256). Colours follow the current bldkit palette (stone, timber, slate, slateG, darkWood).
import numpy as np, json
from PIL import Image, ImageDraw, ImageFilter
T=256;A=Image.new('RGBA',(1024,1024));r=np.random.default_rng(3)
TILES=['b_stone','b_plaster','b_timber','b_slate','b_cobble','b_thatch','b_planks','b_redplanks','b_window','b_door','b_darkstone','b_shingle','b_white','b_red','b_glass','b_iron']
def noise(seed,s=T):
  g=np.random.default_rng(seed);o=np.zeros((s,s))
  for k in range(5):n=2**(k+2);o+=np.asarray(Image.fromarray((g.random((n,n))*255).astype(np.uint8)).resize((s,s),Image.BICUBIC))/255/2**k
  o-=o.min();return o/o.max()
def tint(base,var,seed,amt=.18):
  n=noise(seed)[...,None];c=np.array(base)[None,None,:]*(1-amt+2*amt*n);return Image.fromarray(np.clip(c,0,255).astype(np.uint8)).convert('RGBA')
def put(i,im):y,x=divmod(i,4);A.paste(im,(x*T,y*T))
def blocks(base,mort,rows,seed,jit=.12,stagger=True):
  im=tint(base,0,seed);d=ImageDraw.Draw(im);h=T/rows;g=np.random.default_rng(seed)
  for j in range(rows):
    y0=j*h;w=T/ (3 if j%2 else 3);off=(w/2 if (stagger and j%2) else 0)
    x=-off
    while x<T:
      ww=w*g.uniform(.8,1.2);f=g.uniform(1-jit,1+jit);c=tuple(int(v*f) for v in base)
      d.rectangle([x+2,y0+2,x+ww-2,y0+h-2],fill=c+(255,));x+=ww
    d.line([0,y0,T,y0],fill=mort+(255,),width=3)
  return Image.fromarray(np.asarray(im)).filter(ImageFilter.SMOOTH)
put(0,blocks((150,146,136),(96,90,82),6,1))
put(1,tint((226,214,188),0,2,.08))
im=tint((92,62,40),0,3,.2);d=ImageDraw.Draw(im)
for x in range(0,T,9):d.line([x,0,x+r.integers(-3,3),T],fill=(70,46,30,255),width=1)
put(2,im)
def roof(base,seed,rows=8,round_=False):
  im=tint(base,0,seed,.1);d=ImageDraw.Draw(im);h=T/rows;g=np.random.default_rng(seed)
  for j in range(rows):
    off=(T/12 if j%2 else 0)
    for i in range(7):
      x=i*T/6-off;f=g.uniform(.82,1.15);c=tuple(int(v*f) for v in base)
      if round_:d.rounded_rectangle([x+1,j*h,x+T/6-1,j*h+h-1],radius=10,fill=c+(255,))
      else:d.rectangle([x+1,j*h,x+T/6-1,j*h+h-2],fill=c+(255,))
    d.line([0,j*h+h-1,T,j*h+h-1],fill=tuple(int(v*.5) for v in base)+(255,),width=3)
  return im
put(3,roof((84,92,108),4))
im=tint((190,160,92),0,6,.12);d=ImageDraw.Draw(im)
for k in range(1600):
  x=r.uniform(0,T);y=r.uniform(0,T);d.line([x,y,x+r.uniform(-3,3),y+r.uniform(14,30)],fill=(int(r.uniform(120,200)),int(r.uniform(96,160)),int(r.uniform(50,90)),255),width=2)
put(5,im)
def planks(base,seed):
  im=tint(base,0,seed,.15);d=ImageDraw.Draw(im);g=np.random.default_rng(seed)
  for x in range(0,T,32):
    f=g.uniform(.85,1.12);c=tuple(int(v*f) for v in base);d.rectangle([x+1,0,x+30,T],fill=c+(255,));d.line([x,0,x,T],fill=tuple(int(v*.45) for v in base)+(255,),width=3)
    for k in range(6):yy=g.uniform(0,T);d.line([x+4,yy,x+28,yy+g.uniform(-2,2)],fill=tuple(int(v*.8) for v in base)+(255,),width=1)
  return im
put(6,planks((128,92,58),7));put(7,planks((150,56,44),8))
# window: frame, mullions, dark-blue glass with highlight
im=Image.new('RGBA',(T,T),(70,48,32,255));d=ImageDraw.Draw(im)
for yy in range(18,T-18):
  f=(yy-18)/(T-36);d.line([18,yy,T-18,yy],fill=(int(250-60*f),int(196-80*f),int(96-50*f),255))
for i in range(14):x=r.uniform(20,T-20);d.line([x,20,x-40,T-20],fill=(255,226,150,255),width=2)
d.rectangle([T//2-7,18,T//2+7,T-18],fill=(70,48,32,255));d.rectangle([18,T//2-7,T-18,T//2+7],fill=(70,48,32,255))
put(8,im)
im=planks((96,64,40),9);d=ImageDraw.Draw(im)
for y in (40,T-50):d.rectangle([6,y,T-6,y+16],fill=(44,44,48,255))
d.ellipse([T-60,T//2-10,T-40,T//2+10],fill=(150,130,70,255));put(9,im)
put(10,blocks((86,84,88),(52,50,54),6,10))
put(11,roof((112,80,54),11,10,True))
put(12,tint((236,232,224),0,12,.05));put(13,tint((168,52,44),0,13,.08))
im=tint((248,226,150),0,14,.08);d=ImageDraw.Draw(im)
for x in range(0,T,64):d.rectangle([x,0,x+6,T],fill=(60,60,64,255))
put(14,im)
pts=r.random((40,2))*T;Y,X=np.mgrid[0:T,0:T];dd=np.full((T,T),1e9);d2=np.full((T,T),1e9)
for p_ in pts:
  for ox in (-T,0,T):
    for oy in (-T,0,T):
      q=(X-p_[0]-ox)**2+(Y-p_[1]-oy)**2;d2=np.where(q<dd,dd,np.minimum(d2,q));dd=np.minimum(dd,q)
e=np.clip((np.sqrt(d2)-np.sqrt(dd))/5,0,1);n=noise(16);c=np.stack([110+50*e*(.7+.3*n),104+48*e*(.7+.3*n),96+44*e*(.7+.3*n)],-1)
put(4,Image.fromarray(c.astype(np.uint8)).convert('RGBA'));put(15,tint((70,72,78),0,15,.2))
A.save('atlas.png');A.save('atlas.webp',quality=88,method=6);json.dump({'tile':T,'grid':4,'tiles':TILES},open('atlas.json','w'),indent=1);print('ok')
