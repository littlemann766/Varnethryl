import sys,glob
from PIL import Image,ImageDraw
out=sys.argv[1]; rows=sys.argv[2:]
ims=[(r.split('|')[1] if '|' in r else r, sorted(glob.glob(r.split('|')[0]+'_*.png'))) for r in rows]
ims=[x for x in ims if x[1]]
w,h=Image.open(ims[0][1][0]).size; W=max(len(x[1]) for x in ims)
c=Image.new('RGB',(w*W,(h+16)*len(ims)),'white'); d=ImageDraw.Draw(c)
for j,(lab,fs) in enumerate(ims):
  d.text((3,j*(h+16)+2),lab,fill='black')
  for i,f in enumerate(fs): c.paste(Image.open(f).convert('RGB'),(i*w,j*(h+16)+16))
c.save(out,quality=85)
