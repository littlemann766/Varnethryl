from PIL import Image, ImageDraw, ImageFont
import os
names=['owner','selene','darius','town_guard','holyknight_villain']
labels=['Owner','Selene','Darius','Town guard','Holy knight (villain)']
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
os.makedirs('/workspace/mocap/comp',exist_ok=True)
for g in range(279):
    W=Image.new('RGB',(1920,880),(20,20,24))
    for c,n in enumerate(names):
        for r,v in enumerate(['side','q']):
            W.paste(Image.open(f'/workspace/mocap/fr/{n}_{v}/f{g:05d}.png').convert('RGB'),(c*384,16+r*432))
    d=ImageDraw.Draw(W)
    for c,l in enumerate(labels): d.text((c*384+8,20),l,font=F,fill='white')
    seg='Walk' if g<120 else ('Run' if g<204 else 'Idle')
    d.text((8,452),'3/4 view',font=F,fill='white'); d.text((8,40),'Side view  -  '+seg,font=F,fill='yellow')
    W.save(f'/workspace/mocap/comp/c{g:05d}.png')
