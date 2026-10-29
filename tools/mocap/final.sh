#!/bin/bash
B=/workspace/tools/blender-4.2.3-linux-x64/blender; cd /workspace/mocap
run(){ n=$1; bl=$2; shift 2; env "$@" $B -b -P retarget.py -- $bl /workspace/mocap/out/$n $n >/dev/null 2>&1; $B -b -P check.py -- out/$n.blend walk,run,idle out/$n.checks.json >/dev/null 2>&1; $B -b -P slide.py -- $n 2>&1 | grep SLIDE > out/$n.slide.txt; echo "$n done $(cat out/$n.checks.json | tr -d ' \n' | cut -c1-300) $(cat out/$n.slide.txt)"; }
run owner /workspace/voxel/v2_owner_voxel.blend ABD=0 &
run selene /workspace/voxel/v2_selene_voxel.blend ABD=0 &
run darius /workspace/voxel/v2_darius_voxel.blend ABD=14 ABD_IDLE=18 HOLD_MODE=world HOLD=hand_R &
run town_guard /workspace/voxel/npc/town_guard_voxel.blend ABD=20 ABD_IDLE=20 HOLD_MODE=world HOLD=mixamorig:RightForeArm,mixamorig:RightHand &
run holyknight_villain /workspace/voxel/npc/holyknight_villain_voxel.blend ABD=26 ABD_IDLE=18 HOLD_MODE=world HOLD=mixamorig:RightHand,mixamorig:LeftHand &
wait
