# Decal atlas 512 (4x4 x 128), RGBA alpha-cut: moss, cracks, dirt, grime, leaf litter, puddle. Painted albedo only.
import numpy as np,json,sys,os
from PIL import Image,ImageDraw,ImageFilter
T=128;A=Image.new('RGBA',(512,512),(0,0,0,0));OUT=sys.argv[1]
TILES=['d_moss','d_moss2','d_crack','d_crack2','d_dirt','d_dirt2','d_grime','d_leaves','d_puddle','d_soot']
def noise(seed):
  g=np.random.default_rng(seed);o=np.zeros((T,T))
  for k in range(5):n=2**(k+1);o+=np.asarray(Image.fromarray((g.random((n,n))*255).astype(np.uint8)).resize((T,T),Image.BICUBIC))/255/2**k
  o-=o.min();return o/o.max()
Y,X=np.mgrid[0:T,0:T]/T-.5;R=np.sqrt(X*X+Y*Y)*2
def splat(col,seed,edge=.55,cut=.5,vert=None):
  n=noise(seed);f=(1-R)+n*edge-cut
  if vert:f=np.minimum(f,(.5-Y)*vert+n*.4-.1)  # grows from the bottom edge
  a=np.clip(f*8,0,1)*255;c=np.array(col)[None,None,:]*(.75+.5*noise(seed+9)[...,None])
  return Image.fromarray(np.dstack([np.clip(c,0,255),a]).astype(np.uint8),'RGBA')
def crack(seed):
  im=Image.new('RGBA',(T,T),(0,0,0,0));d=ImageDraw.Draw(im);g=np.random.default_rng(seed)
  for b in range(4):
    p=np.array([T/2,T/2]);a=g.uniform(0,6.28)
    for s in range(9):q=p+np.array([np.cos(a),np.sin(a)])*g.uniform(5,10);d.line([*p,*q],fill=(30,28,26,255),width=int(3-s*.25)+1);p=q;a+=g.uniform(-.6,.6)
  return im
def put(i,im):y,x=divmod(i,4);A.paste(im,(x*T,y*T))
put(0,splat((70,96,40),1));put(1,splat((86,104,48),2,vert=2.2));put(2,crack(3));put(3,crack(4))
put(4,splat((92,76,56),5,.7,.6));put(5,splat((110,92,66),6,vert=1.8));put(6,splat((44,42,40),7,.6,.55,vert=1.5))
im=Image.new('RGBA',(T,T),(0,0,0,0));d=ImageDraw.Draw(im);g=np.random.default_rng(8)
for k in range(60):x,y=g.uniform(10,118,2);c=[(150,90,40),(170,120,50),(120,70,30)][k%3];d.ellipse([x-5,y-3,x+5,y+3],fill=c+(255,))
put(7,im);put(8,splat((70,80,92),9,.4,.45));put(9,splat((30,28,28),10,.6,.5,vert=1.2))
D=os.path.join(OUT,'decals','atlas');A.save(D+'/atlas.png');A.save(D+'/atlas.webp',quality=90,method=6,lossless=False)
json.dump({'tile':T,'grid':4,'tiles':TILES},open(D+'/atlas.json','w'));print('decals ok')
