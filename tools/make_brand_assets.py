#!/usr/bin/env python3
"""Generate all Varnethryl icon / splash / brand art from tools/brand-src (Lanczos, never upscaled past source).
Outputs: www/ icons + www/assets/brand, and android-res/ (copied into android/app/src/main/res by tools/apply_android_icons.py)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops
R=Path(__file__).resolve().parents[1]; S=R/'tools/brand-src'; W=R/'www'; A=R/'android-res'; B=W/'assets/brand'
L=Image.LANCZOS
for d in (B,A): d.mkdir(parents=True,exist_ok=True)
tile=Image.open(S/'icon-tile.png').convert('RGB'); C=100
full=tile.crop((C,C,tile.width-C,tile.height-C))          # full-bleed 1054: corners land on the gold frame, no dark outside corners
def rs(im,n): return im.resize((n,n),L) if im.width!=n else im.copy()
def rmask(n,frac):
    m=Image.new('L',(n*4,n*4),0); ImageDraw.Draw(m).rounded_rectangle((0,0,n*4-1,n*4-1),int(n*4*frac),fill=255); return m.resize((n,n),L)
def circ(n):
    m=Image.new('L',(n*4,n*4),0); ImageDraw.Draw(m).ellipse((0,0,n*4-1,n*4-1),fill=255); return m.resize((n,n),L)
def blurbg(n):  # derived dark background from the art itself
    b=full.resize((64,64),L).filter(ImageFilter.GaussianBlur(6)).resize((n,n),Image.BICUBIC)
    return Image.new('RGB',(n,n),(8,6,15))   # solid near-black matched to the art's dark space
def save(im,p,**k): p.parent.mkdir(parents=True,exist_ok=True); im.save(p,**k)
# ---- Android mipmaps
dens={'mdpi':1,'hdpi':1.5,'xhdpi':2,'xxhdpi':3,'xxxhdpi':4}
for d,f in dens.items():
    n=int(48*f); fg=int(108*f); out=A/f'mipmap-{d}'
    sq=rs(full,n); sq.putalpha(rmask(n,.14)); save(sq,out/'ic_launcher.png')
    rd=rs(full,n); rd.putalpha(circ(n)); save(rd,out/'ic_launcher_round.png')
    art=int(fg*.66); a=rs(full,art); a.putalpha(rmask(art,.2))   # art lives in 66% safe zone
    layer=Image.new('RGBA',(fg,fg),(0,0,0,0)); layer.paste(a,((fg-art)//2,)*2,a); save(layer,out/'ic_launcher_foreground.png')
    save(blurbg(fg).convert('RGB'),out/'ic_launcher_background.png')
x=A/'mipmap-anydpi-v26'; x.mkdir(exist_ok=True)
xml='<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n    <background android:drawable="@mipmap/ic_launcher_background"/>\n    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n</adaptive-icon>\n'
(x/'ic_launcher.xml').write_text(xml); (x/'ic_launcher_round.xml').write_text(xml)
save(rs(full,512).convert('RGB'),A/'playstore-icon-512.png')
# ---- Web icons (full-bleed 'any', plus maskable with art in safe zone on derived bg)
for n in (512,192,180,64,32): save(rs(full,n).convert('RGB'),W/f'icon-{n}.png',optimize=True)
def maskable(n):
    bg=blurbg(n).convert('RGB'); art=int(n*.76); a=rs(full,art); a.putalpha(rmask(art,.16)); bg.paste(a,((n-art)//2,)*2,a); return bg
save(maskable(512),W/'icon-maskable-512.png',optimize=True); save(maskable(192),W/'icon-maskable-192.png',optimize=True)
save(rs(full,180).convert('RGB'),W/'apple-touch-icon.png',optimize=True)
# ---- Emblem (transparent) for title screen / small spots
em=Image.open(S/'emblem.png').convert('RGBA'); bb=em.getchannel('A').point(lambda v:255 if v>8 else 0).getbbox(); em=em.crop(bb)
side=max(em.size); sq=Image.new('RGBA',(side,side),(0,0,0,0)); sq.paste(em,((side-em.width)//2,(side-em.height)//2))
sq.thumbnail((1024,1024),L); save(sq,B/'emblem.webp',quality=90,method=6)
e128=sq.resize((128,128),L); save(e128,B/'emblem-128.png',optimize=True)
# ---- Poster / banner for in-game loading
po=Image.open(S/'poster.png').convert('RGB'); ba=Image.open(S/'banner.png').convert('RGB')
save(po,B/'poster.webp',quality=86,method=6); save(ba,B/'banner.webp',quality=86,method=6)
# ---- Native splash
def stretchbg(w,h,src,dark=.3):
    sm=src.resize((48,48),L).filter(ImageFilter.GaussianBlur(3)).resize((w,h),Image.BICUBIC)
    return Image.eval(sm,lambda v:int(v*dark))
def place(w,h,src):
    bg=stretchbg(w,h,src); m=Image.new('L',src.size,255); f=int(src.height*.12); d=ImageDraw.Draw(m)
    for i in range(f): v=int(255*i/f); d.line((0,i,src.width,i),fill=v); d.line((0,src.height-1-i,src.width,src.height-1-i),fill=v)
    fx=int(src.width*.04)
    for i in range(fx):
        v=int(255*i/fx); col=Image.new('L',(1,src.height),v)
        m=ImageChops.multiply(m,Image.new('L',src.size,255)) 
    hm=Image.new('L',src.size,255); dh=ImageDraw.Draw(hm)
    for i in range(fx): v=int(255*i/fx); dh.line((i,0,i,src.height),fill=v); dh.line((src.width-1-i,0,src.width-1-i,src.height),fill=v)
    m=ImageChops.multiply(m,hm); bg.paste(src,((w-src.width)//2,(h-src.height)//2),m); return bg
g=A/'drawable'; 
save(po,A/'drawable-port/splash.png',optimize=True)          # 941x1672 native, centerCrop on phones
save(place(2400,1080,ba),A/'drawable-land/splash.png',optimize=True)
save(place(2732,2732,ba),A/'drawable/splash.png',optimize=True)
for n,im in (('port',po),):
    pass
print('done')
