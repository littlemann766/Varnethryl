#!/bin/bash
B=/workspace/beth-world/www/proto3d/models/beth/hi/buildings; O=/workspace/beth-world/audit/cardstyle/shots
for n in "$@"; do
 if [[ $n == house_* ]]; then T=/workspace/beth-world/www/proto3d/models/beth/tripo; a=$T/${n}_game.glb; c=$T/${n}_card.glb; else a=$B/bld_$n.glb; c=$B/bld_${n}_card.glb; fi
 (cd /workspace/cardstyle-godot && timeout 300 xvfb-run -a -s "-screen 0 1600x900x24" godot --path . --resolution 1600x900 -- $a $c $O/raw_$n.png 1.3 0.45 >/dev/null 2>&1)
 python3 -c "
from PIL import Image,ImageDraw,ImageFont
im=Image.open('$O/raw_$n.png').convert('RGB');d=ImageDraw.Draw(im)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',30)
for x,t in((20,'BEFORE (round 4)'),(820,'AFTER (card style)')): d.rectangle([x-8,12,x+330,56],fill=(0,0,0)); d.text((x,16),t,font=f,fill=(255,230,170))
d.text((20,860),'$n',font=f,fill=(255,255,255))
im.save('$O/compare_$n.png')" && echo "SHOT $n"
done
