import sys,glob,os
from PIL import Image,ImageDraw
b,a,out,flt=sys.argv[1],sys.argv[2],sys.argv[3],(sys.argv[4] if len(sys.argv)>4 else '')
fs=[os.path.basename(f) for f in sorted(glob.glob(a+'/*.png')) if flt in os.path.basename(f)]
W,H=640,360;S=Image.new('RGB',(W*2,(H+18)*len(fs)),'black');d=ImageDraw.Draw(S)
for i,f in enumerate(fs):
    y=i*(H+18)
    for j,dd in enumerate([b,a]):
        if os.path.exists(dd+'/'+f): S.paste(Image.open(dd+'/'+f).convert('RGB').resize((W,H)),(j*W,y+18))
    d.text((4,y+3),f[:-4]+'   BEFORE | AFTER',fill='white')
S.save(out,quality=85)
