"""Builds www/assets/world/*.webp from raw generated art (chroma-key magenta, crop, feather, resize).
Usage: python3 tools/build_world_art.py <raw_dir>   (raw_dir has sky/far/mid/fore/ground/props/buildings .jpg|.png)"""
import sys,os,numpy as np
from PIL import Image,ImageFilter
from scipy import ndimage as ndi
R=sys.argv[1];O=os.path.join(os.path.dirname(__file__),'..','www','assets','world')
def ld(n):
    """load raw art"""
    for e in('png','jpg'):
        p=os.path.join(R,n+'.'+e)
        if os.path.exists(p):return Image.open(p).convert('RGB')
def key(im):
    a=np.asarray(im).astype(float);r,g,b=a[...,0],a[...,1],a[...,2]
    bd=np.concatenate([a[:6].reshape(-1,3),a[-6:].reshape(-1,3),a[:,:6].reshape(-1,3),a[:,-6:].reshape(-1,3)]);kc=np.median(bd,0)
    d=np.sqrt((r-kc[0])**2+(g-kc[1])**2+(b-kc[2])**2)
    al=np.clip((d-90)/80,0,1)
    # despill: pull magenta fringe toward neutral
    spill=np.clip((np.minimum(r,b)-g)/255,0,1)*(1-al*0.0)
    m=(al<1)&(al>0)
    r2=np.where(m,np.minimum(r,g+ (r-g)*0.25),r);b2=np.where(m,np.minimum(b,g+(b-g)*0.25),b)
    inner=ndi.binary_erosion(al>.99,iterations=3);ring=(al>0)&~inner
    b2=np.where(ring,np.minimum(b2,(r+g)/2*0.9),b2);r2=np.where(ring,np.minimum(r2,g*1.12+8),r2)
    out=np.dstack([r2,g,b2,al*255]).astype(np.uint8)
    A=Image.fromarray(out,'RGBA')
    al_i=Image.fromarray(out[...,3]).filter(ImageFilter.GaussianBlur(.8))
    A.putalpha(al_i);return A
def trim(im,pad=2):
    bb=im.getchannel('A').point(lambda v:255 if v>20 else 0).getbbox();return im.crop(bb)
def save(im,name,w=None,q=80):
    if w and im.width>w:im=im.resize((w,round(im.height*w/im.width)),Image.LANCZOS)
    p=os.path.join(O,name);im.save(p,'WEBP',quality=q,method=6);print(name,im.size,os.path.getsize(p)//1024,'KB')
def fade(im,top=0,bottom=0):
    a=np.asarray(im.getchannel('A')).astype(float);h=a.shape[0]
    if top:a*=np.clip(np.arange(h)/(h*top),0,1)[:,None]
    if bottom:a*=np.clip((h-1-np.arange(h))/(h*bottom),0,1)[:,None]
    im=im.copy();im.putalpha(Image.fromarray(a.astype(np.uint8)));return im
os.makedirs(O,exist_ok=True)
save(ld('sky').convert('RGBA'),'sky.webp',1600,70)
far=ld('far').convert('RGBA').crop((0,37,1280,650));far=fade(far,top=.10,bottom=.0);save(far,'far.webp',1600,78)
# midground clumps from keyed mid
mid=key(ld('mid'))
save(fade(trim(mid.crop((12,37,525,650))),bottom=.12),'mid-left.webp',700,78)
fore=key(ld('fore'));fore=trim(fore);save(fore,'fore.webp',1600,78)
g=ld('ground').convert('RGBA');g=fade(g,top=.38);save(g,'ground.webp',1600,74)
# prop sprites by connected components
def comps(sheet,names,minarea=4000):
    k=key(ld(sheet));al=np.asarray(k.getchannel('A'))>40
    dil=ndi.binary_dilation(al,iterations=6);lab,n=ndi.label(dil)
    objs=[(s,ndi.find_objects(lab)[i]) for i,s in enumerate(ndi.sum(al,lab,range(1,n+1)))]
    objs=[o for o in objs if o[0]>minarea];objs.sort(key=lambda o:(o[1][0].start//250,o[1][1].start))
    print(sheet,len(objs))
    for (s,sl),nm in zip(objs,names):
        c=trim(k.crop((sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)));save(c,nm+'.webp',420 if sheet=='props' else 560,82)
comps('props',['oak','pine','arch','banner','stones','lupine'])
comps('buildings',['guildhall','forge','market'],minarea=15000)
