#!/bin/bash
# per hero: base = retime35 if present else game voxel/; clips jump|swim|run|walk; commit+push after each hero
B=/workspace/tools/blender-4.2.3-linux-x64/blender; V=/workspace/varn-core; O=$V/handoff/godot/voxel_trial/armfix35; mkdir -p $O
id=$1
for s in "" _lod1 _lod2; do n=${id}_voxel$s; f=$V/handoff/godot/voxel_trial/retime35/$n.glb; [ -f $f ] || f=/workspace/godot-voxel/voxel/$n.glb; [ -f $f ] || continue
 $B -b -P $V/tools/capes/armfix34.py -- $f $O/$n.glb 40 '^(jump|jump_land|jump_start|swim_stroke|swim_tread|run|walk)$' > $O/$n.log 2>&1; done
cd $V; ( flock 9; git add $O/${id}_voxel*.glb $O/${id}_voxel*.armfix34.json && git commit -qm "armfix35: $id jump/swim/run/walk arm-in-leg" && git push -q origin heroes-motion-pass ) 9>/tmp/t35/git.lock
echo DONE $id >> /tmp/t35/af35_done.txt
