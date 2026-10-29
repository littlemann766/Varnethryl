#!/bin/bash
B=/workspace/tools/blender-4.2.3-linux-x64/blender; n=$1; bl=$2
mkdir -p /workspace/mocap/sw
for abd in ${ABDS:-0}; do
 tag=${n}_a${abd}_h${HOLD//[:,]/}${HOLD_MODE}i${ABD_IDLE}
 [ -f /workspace/mocap/sw/$tag.checks.json ] && continue
 ABD_IDLE=${ABD_IDLE:-$abd} HOLD_MODE=$HOLD_MODE HOLD=$HOLD ABD=$abd $B -b -P /workspace/mocap/retarget.py -- $bl /workspace/mocap/sw/$tag $n >/dev/null 2>&1
 $B -b -P /workspace/mocap/check.py -- /workspace/mocap/sw/$tag.blend walk,run,idle /workspace/mocap/sw/$tag.checks.json >/dev/null 2>&1
 python3 -c "import json;d=json.load(open('/workspace/mocap/sw/$tag.checks.json'));print('$tag',{k:(v.get('arm_in_leg_verts_max'),v.get('cape_in_body_verts_max')) for k,v in d.items() if k!='rest_baseline'})"
 rm -f /workspace/mocap/sw/$tag.glb
done
