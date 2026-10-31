#!/bin/bash
# guard melee set: retarget (UAL1/UAL2, foot lock, shield-arm hold, arm<=30, wrist twist<=45) -> despike (non-arm) -> constant wrist clearance -> armfix (arm-in-leg) -> checks
set -e
B=/workspace/tools/blender-4.2.3-linux-x64/blender; T=/workspace/varn-core/tools/guard_attacks
SRC=$1; OUT=$2; W=$3; mkdir -p $W
A=attack_slash,attack_backhand,attack_overhead,attack_shield_bash,block,guard_stance,combat_idle,hit
RE='^(attack_slash|attack_backhand|attack_overhead|attack_shield_bash|block|guard_stance|combat_idle|hit)$'
CLIPS=$T/clips.json $B -b --python $T/retarget_attacks.py -- $SRC $W/r town_guard 2>&1 | grep -E "^CLIP|Error|Traceback" || true
SKIP=LeftArm,RightArm,LeftShoulder,RightShoulder,LeftHand,RightHand $B -b --python $T/despike.py -- $W/r.blend $A $W/d.blend 2>&1 | grep DESPIKE > $W/despike.log || true
$B -b --python $T/handclear.py -- $W/d.blend $A $W/h 2>&1 | grep -E "^HC" > $W/handclear.log || true
$B -b --python $T/blend2glb.py -- $W/h.blend $W/h.glb >/dev/null 2>&1
ABMAX=0 $B -b --python $T/armfix_guard.py -- $W/h.glb $OUT 40 "$RE" 2>&1 | grep -E "^CLIP|SUMMARY" > $W/armfix.log || true
$B -b --python $T/glb2blend.py -- $OUT $W/final.blend >/dev/null 2>&1
$B -b --python $T/motion_checks.py -- $W/final.blend $A,attack,idle,walk,run $W/motion_checks.json 2>&1 | grep "^MC" > $W/motion_checks.log || true
$B -b --python /workspace/varn-core/tools/voxel_v3/check1.py -- $W/final.blend $A $W/check1.json 2>&1 | grep "^CHECK" > $W/check1.log || true
echo DONE $OUT
