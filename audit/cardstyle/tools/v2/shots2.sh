#!/bin/bash
# usage: shots2.sh name cardfile x0 y0 x1 y1
O=/workspace/beth-world/audit/cardstyle/shots; M=/workspace/beth-world/www/proto3d/models/beth/hi/buildings_card2
n=$1
(cd /workspace/cardstyle-godot && timeout 300 xvfb-run -a -s "-screen 0 1600x900x24" godot --path . --resolution 1600x900 res://cmp2.tscn -- x $M/bld_${n}_card2.glb $O/raw2_$n.png ${F:-1.0} 2.2 ${Y:-28} >/dev/null 2>&1)
python3 - "$@" <<'P'
import sys
from PIL import Image,ImageDraw,ImageFont
n,card,x0,y0,x1,y1=sys.argv[1],sys.argv[2],*map(int,sys.argv[3:7])
O='/workspace/beth-world/audit/cardstyle/shots'
c=Image.open(f'/workspace/beth-world/audit/cardstyle/cards/{card}').convert('RGB').crop((x0,y0,x1,y1)); c=c.resize((int(c.width*900/c.height),900),Image.LANCZOS)
r=Image.open(f'{O}/raw2_{n}.png').convert('RGB')
W=Image.new('RGB',(c.width+r.width,900)); W.paste(c,(0,0)); W.paste(r,(c.width,0)); d=ImageDraw.Draw(W)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',28)
for x,t in((10,'CARD (front view)'),(c.width+10,f'GODOT: bld_{n}_card2.glb')): d.rectangle([x-6,8,x+len(t)*18,48],fill=(0,0,0)); d.text((x,12),t,font=f,fill=(255,230,170))
W.save(f'{O}/compare_{n}_v2.png'); print('SHOT',n)
P
