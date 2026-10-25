# Paints the shared 1024x1024 kit atlas (4x4 tiles of 256). Deterministic.
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
rng=np.random.default_rng(7); T=256; A=np.zeros((1024,1024,4),np.uint8)
TILES=['bark','leaf','pinecard','grass','flower','rock','wood','iron','snow','ice','basalt','lavacrust','cloth','cobble','imp_oak','imp_pine']
def noise(s=T,oct=5,seed=0):
  r=np.random.default_rng(seed);out=np.zeros((s,s))
  for o in range(oct):
    n=2**(o+2);g=r.random((n,n));im=Image.fromarray((g*255).astype(np.uint8)).resize((s,s),Image.BICUBIC)
    out+=np.asarray(im)/255/(2**o)
  out-=out.min();return out/out.max()
def rgb(h):return np.array([(h>>16)&255,(h>>8)&255,h&255],float)
def mix(a,b,t):return a[None,None,:]*(1-t[...,None])+b[None,None,:]*t[...,None]
def put(i,img):
  y,x=divmod(i,4);A[y*T:(y+1)*T,x*T:(x+1)*T]=img
def solid(c,a=255):
  im=np.zeros((T,T,4),np.uint8);im[...,:3]=np.clip(c,0,255);im[...,3]=a;return im
# bark: vertical streaks
n=noise(seed=1);st=np.asarray(Image.fromarray((noise(seed=2)*255).astype(np.uint8)).resize((16,T)).resize((T,T),Image.BICUBIC))/255
put(0,solid(mix(rgb(0x3e2a18),rgb(0x8a6440),0.55*st+0.45*n)))
# leaf card: clustered leaves, alpha
def card(seed,colA,colB,shape):
  im=Image.new('RGBA',(T,T),(0,0,0,0));d=ImageDraw.Draw(im);r=np.random.default_rng(seed)
  for k in range(shape[0]):
    if shape[1]=='leaf':
      cx,cy=r.normal(128,52,2);rad=r.uniform(9,17)
      if (cx-128)**2+(cy-128)**2>118**2:continue
    elif shape[1]=='needle':
      cx=r.uniform(20,236);cy=r.uniform(10,250)
      w=(1-abs(cx-128)/118);
      if cy>250*w+5 and r.random()<.8:pass
      rad=r.uniform(3,6)
    t=r.random();c=tuple(int(colA[j]*(1-t)+colB[j]*t) for j in range(3))
    if shape[1]=='leaf':d.ellipse([cx-rad,cy-rad*.65,cx+rad,cy+rad*.65],fill=c+(255,))
    else:
      # pine: drooping needle strokes along branches
      d.line([cx,cy,cx+r.uniform(-14,14),cy+r.uniform(6,16)],fill=c+(255,),width=int(rad))
  return np.asarray(im)
put(1,card(3,(0x90,0x98,0x88),(0xff,0xff,0xf0),(1400,'leaf')))
# pine card: triangle silhouette made of strokes
im=Image.new('RGBA',(T,T),(0,0,0,0));d=ImageDraw.Draw(im);r=np.random.default_rng(4)
for k in range(2200):
  y=r.uniform(4,252);half=(y/252)*118;x=128+r.uniform(-half,half);t=r.random()
  c=(int(0x2f+t*0x40),int(0x6a+t*0x50),int(0x3a+t*0x30))
  d.line([x,y,x+r.uniform(-10,10),y+r.uniform(5,13)],fill=c+(255,),width=3)
put(2,np.asarray(im))
# grass card: blades
im=Image.new('RGBA',(T,T),(0,0,0,0));d=ImageDraw.Draw(im);r=np.random.default_rng(5)
for k in range(260):
  x=r.uniform(10,246);h=r.uniform(90,240);lean=r.uniform(-40,40);t=r.random()
  c=(int(0x3f+t*0x45),int(0x7e+t*0x48),int(0x34+t*0x20))
  d.polygon([(x-3,255),(x+3,255),(x+lean,255-h)],fill=c+(255,))
put(3,np.asarray(im))
# flower card: white-ish petals (vertex color tints) on green stems
im=Image.new('RGBA',(T,T),(0,0,0,0));d=ImageDraw.Draw(im);r=np.random.default_rng(6)
for k in range(90):
  x=r.uniform(14,242);h=r.uniform(60,200);lean=r.uniform(-20,20)
  d.line([x,255,x+lean,255-h],fill=(70,130,55,255),width=3)
for k in range(90):
  x=r.uniform(18,238);y=r.uniform(56,190);rad=r.uniform(7,13)
  for a in range(5):
    ang=a*1.2566+r.random();px=x+np.cos(ang)*rad*.7;py=y+np.sin(ang)*rad*.7
    d.ellipse([px-rad*.5,py-rad*.5,px+rad*.5,py+rad*.5],fill=(250,248,240,255))
  d.ellipse([x-3,y-3,x+3,y+3],fill=(240,200,60,255))
put(4,np.asarray(im))
# rock: grey strata + speckle (vertex colour tints toward palettes)
n=noise(seed=8);sp=rng.random((T,T))
put(5,solid(mix(rgb(0x6b707a),rgb(0xb4b8bc),0.7*n+0.3*sp)))
# wood planks
yy=np.arange(T)[:,None]*np.ones((1,T));grain=np.asarray(Image.fromarray((noise(seed=9)*255).astype(np.uint8)).resize((T,24)).resize((T,T),Image.BICUBIC))/255
seam=((yy%64)<3).astype(float)
put(6,solid(mix(rgb(0x5a3a20),rgb(0x9a6a40),0.8*grain*(1-seam))))
put(7,solid(mix(rgb(0x2a2c30),rgb(0x5a5e66),noise(seed=10))))
put(8,solid(mix(rgb(0xc8d4e0),rgb(0xf4f8fc),noise(seed=11))))
put(9,solid(mix(rgb(0x5a86a8),rgb(0xb8d8ee),noise(seed=12)**0.7)))
put(10,solid(mix(rgb(0x2a2426),rgb(0x5a4c4e),noise(seed=13))))
# lava crust: dark plates with orange-red cracks painted in albedo (no emissive)
n=noise(seed=14);cr=np.abs(np.sin(noise(seed=15)*28))<0.12
im=mix(rgb(0x2e2628),rgb(0x564648),n);im[cr]=rgb(0xc8501c)*(0.8+0.2*n[cr,None])
put(11,solid(im))
put(12,solid(mix(rgb(0xb8a888),rgb(0xe8dcc0),noise(seed=16))))
# cobble: voronoi-ish stones
pts=rng.random((60,2))*T;Y,X=np.mgrid[0:T,0:T];dd=np.full((T,T),1e9);d2=np.full((T,T),1e9)
for p in pts:
  for ox in (-T,0,T):
    for oy in (-T,0,T):
      q=(X-p[0]-ox)**2+(Y-p[1]-oy)**2;d2=np.where(q<dd,dd,np.minimum(d2,q));dd=np.minimum(dd,q)
edge=np.clip((np.sqrt(d2)-np.sqrt(dd))/6,0,1)
put(13,solid(mix(rgb(0x5a5248),rgb(0xa89a88),edge*(0.6+0.4*noise(seed=17)))))
# impostors: painted canopy silhouettes
def imp(kind):
  im=Image.new('RGBA',(T,T),(0,0,0,0));d=ImageDraw.Draw(im);r=np.random.default_rng(20)
  d.rectangle([122,170,134,255],fill=(0x5a,0x3e,0x24,255))
  if kind=='oak':
    for k in range(500):
      cx,cy=r.normal(128,46),r.normal(100,40);rad=r.uniform(10,20);t=r.random()
      if (cx-128)**2/1.0+(cy-100)**2>100**2:continue
      d.ellipse([cx-rad,cy-rad,cx+rad,cy+rad],fill=(int(0x2f+t*0x50),int(0x6e+t*0x50),int(0x30+t*0x20),255))
  else:
    for k in range(1600):
      y=r.uniform(4,215);half=(y/215)*80;x=128+r.uniform(-half,half);t=r.random()
      d.line([x,y,x+r.uniform(-8,8),y+r.uniform(4,10)],fill=(int(0x1d+t*0x40),int(0x4a+t*0x50),int(0x2c+t*0x30),255),width=3)
  return np.asarray(im)
put(14,imp('oak'));put(15,imp('pine'))
# bleed alpha-card colours into transparent texels so mip filtering doesn't halo
img=Image.fromarray(A,'RGBA')
rgbim=img.convert('RGB').filter(ImageFilter.MaxFilter(5));base=Image.fromarray(A[...,:3]);
out=np.asarray(img).copy();m=out[...,3]==0;out[m,:3]=np.asarray(rgbim)[m]
Image.fromarray(out,'RGBA').save('atlas.png');Image.fromarray(out,'RGBA').save('atlas.webp',quality=88,method=6)
import json;json.dump({'tile':T,'grid':4,'tiles':TILES},open('atlas.json','w'),indent=1)
print('ok')
