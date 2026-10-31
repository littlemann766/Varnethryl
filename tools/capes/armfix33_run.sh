#!/bin/bash
B=/workspace/tools/blender-4.2.3-linux-x64/blender; G=/workspace/godot-art/voxel_cast/cape_fix32
O=/workspace/varn-core/handoff/godot/voxel_trial/armfix33; mkdir -p $O/logs
f=$1; src=$G/glb/$f.glb; [ -f $G/robes/glb/$f.glb ] && src=$G/robes/glb/$f.glb
timeout 2400 $B -b -P /tmp/af33/armfix.py -- $src $O/$f.glb 40 > $O/logs/$f.log 2>&1; echo "DONE $f $?" >> /tmp/af33/done.txt
