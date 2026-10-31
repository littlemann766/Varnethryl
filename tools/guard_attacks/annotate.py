import json,sys
from PIL import Image,ImageDraw
d=sys.argv[1]; M=json.load(open(d+'/manifest.json'))
for g,an,cam,f,hit in M:
    p=f'{d}/f{g:05d}.png'; im=Image.open(p).convert('RGB'); dr=ImageDraw.Draw(im)
    dr.rectangle([0,0,480,22],fill=(20,20,30)); dr.text((6,5),f'town guard  {an}  [{cam}]  frame {f}',fill=(255,255,255))
    if hit: dr.rectangle([0,24,480,48],fill=(200,30,30)); dr.text((200,30),'HIT',fill=(255,255,255))
    im.save(p)
