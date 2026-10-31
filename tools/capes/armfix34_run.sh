#!/bin/bash
# usage: armfix34_run.sh <in_dir(test34 models)> <out_dir> [ids...]
# Arm-in-leg fix on top of existing files. Only upperArm/foreArm rotations of the chosen clips change; cape bones, mesh and other clips are untouched.
# Clips: jump|swim for all ids; fly_bank also for garruk. Per-clip counts -> <out>/<id>.armfix34.json
B=/workspace/tools/blender-4.2.3-linux-x64/blender; I=$1; O=$2; shift 2; mkdir -p $O
for id in "$@"; do for f in $I/${id}_voxel.glb $I/${id}_voxel_lod1.glb; do [ -f $f ] || continue
  C='jump|swim'; [ $id = garruk ] && C='jump|swim|fly_bank'; [ $id = wren ] && C='jump|swim|fly_bank|fly_fast'
  $B -b -P $(dirname $0)/armfix34.py -- $f $O/$(basename $f) 40 "$C" > $O/$(basename $f .glb).log 2>&1
done; done
