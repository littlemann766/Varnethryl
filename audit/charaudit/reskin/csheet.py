from PIL import Image,ImageDraw
import sys; sys.path.insert(0,'/workspace/beth-world/audit/charaudit')
cards=Image.open('/workspace/cards.jpg'); W,H=cards.size
order=['aldric','elira','thorne','nyx','rowan','seraphine','garruk','mirelle','cedric','morwen','kael','vesper','talia','orin','selene','darius','finn','brynn','asha','rook']
def card(n):
    i=order.index(n); cw,ch=W/5,H/4; x,y=i%5,i//5
    return cards.crop((int(x*cw),int(y*ch),int((x+1)*cw),int((y+1)*ch))).resize((220,300))
ns='garruk rook talia cedric morwen nyx'.split()
cols=['card','old_idle0_front','old_idle0_back','new_idle0_front','new_idle0_back','new_run0.3_q','new_run0.7_q','new_attack10.5_q']
S=Image.new('RGB',(90+220*len(cols),30+300*len(ns)),(30,30,36)); d=ImageDraw.Draw(S)
for c,k in enumerate(['card','OLD front','OLD back','NEW front','NEW back','NEW run 30%','NEW run 70%','NEW attack1']): d.text((90+220*c+60,10),k,fill='white')
for r,n in enumerate(ns):
    d.text((5,30+300*r+140),n,fill='white')
    for c,k in enumerate(cols):
        im=card(n) if k=='card' else Image.open(f'sh/{n}_{k}.png').convert('RGB')
        S.paste(im,(90+220*c,30+300*r))
S.save('reskin_contact.jpg',quality=88)
