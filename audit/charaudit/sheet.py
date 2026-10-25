from PIL import Image,ImageDraw
import os,glob,sys
cards=Image.open('/workspace/cards.jpg'); W,H=cards.size
order=['aldric','elira','thorne','nyx','rowan','seraphine','garruk','mirelle','cedric','morwen','kael','vesper','talia','orin','selene','darius','finn','brynn','asha','rook']
def card(n):
    if n not in order: return None
    i=order.index(n); cw,ch=W/5,H/4; x,y=i%5,i//5
    return cards.crop((int(x*cw),int(y*ch),int((x+1)*cw),int((y+1)*ch))).resize((220,300))
names=sorted({f.split('_game')[0] for f in os.listdir('out') if '_game_' in f})
cols=['card','src_idle0_front','src_idle0_back','game_idle0_front','game_idle0_back','game_run0.3_q','game_run0.7_q','game_attack10.5_q']
def build(ns,path):
    S=Image.new('RGB',(220*len(cols)+120,300*len(ns)),(30,30,36)); d=ImageDraw.Draw(S)
    for r,n in enumerate(ns):
        d.text((5,300*r+140),n,fill='white')
        for c,k in enumerate(cols):
            im=card(n) if k=='card' else (Image.open(f'out/{n}_{k}.png').convert('RGB') if os.path.exists(f'out/{n}_{k}.png') else None)
            if k=='game_attack10.5_q' and im is None and os.path.exists(f'out/{n}_game_attack0.5_q.png'): im=Image.open(f'out/{n}_game_attack0.5_q.png').convert('RGB')
            if im: S.paste(im,(120+220*c,300*r))
    S.save(path,quality=85)
for i in range(0,len(names),8): build(names[i:i+8],f'sheet_{i//8}.jpg')
print(names)
