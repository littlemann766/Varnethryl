#!/bin/bash
# retime_run.sh <in_dir> <out_dir> ids...   ref = godot-art batch*/glb_sealed_v3 of same file
B=/workspace/tools/blender-4.2.3-linux-x64/blender; I=$1; O=$2; shift 2; mkdir -p $O
for id in "$@"; do for s in "" _lod1; do f=$I/${id}_voxel$s.glb; [ -f $f ] || continue
 r=$(ls /workspace/godot-art/voxel_cast/batch*/glb_sealed_v3/${id}_voxel$s.glb 2>/dev/null | head -1)
 $B -b -P $(dirname $0)/retime.py -- $f $O/${id}_voxel$s.glb $r > $O/${id}_voxel$s.retime.log 2>&1; done; done
