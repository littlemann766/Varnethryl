#!/bin/bash
# run_one.sh <glb_in> <glb_out> <rules_json> <cx cy cz> <tag>
B=/workspace/tools/blender-4.2.3-linux-x64/blender; T=/workspace/vm-noweapon/tools
$B -b -P $T/strip_baked_weapon.py -- "$1" "$2" "$3" 2>&1 | grep -E "REPORT|Error"
$B -b -P $T/render_hand.py -- "$1" /tmp/rn/${7}_before $4 $5 $6 >/dev/null 2>&1
$B -b -P $T/render_hand.py -- "$2" /tmp/rn/${7}_after $4 $5 $6 >/dev/null 2>&1
python3 - /tmp/rn/$7 <<'P'
import sys;from PIL import Image;p=sys.argv[1]
im=Image.new('RGB',(1536,1024))
for i,f in enumerate(['before_body','before_handA','before_handB','after_body','after_handA','after_handB']): im.paste(Image.open(p+'_'+f+'.png').convert('RGB'),((i%3)*512,(i//3)*512))
im.save(p+'_sheet.png')
P
