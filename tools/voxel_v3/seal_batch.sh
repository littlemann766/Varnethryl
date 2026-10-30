#!/bin/bash
# $1 = LOD0 glb path; seals LOD0 (K=1) and LOD1 (K=1.5 re-grid from LOD0, like voxel_v3 lod.py)
B=/workspace/tools/blender-4.2.3-linux-x64/blender; f=$1; d=$(dirname $(dirname $f)); n=$(basename $f .glb)
o=$d/glb_sealed; W=/workspace/seal30/w; mkdir -p $o $W
$B -b -P /workspace/vx3/imp.py -- $f $W/${n}_in.blend > $W/$n.imp.log 2>&1
for K in 1 1.5; do m=$n; [ $K = 1.5 ] && m=${n}_lod1
$B -b -P /workspace/seal30/seal.py -- $W/${n}_in.blend $K $o/$m.glb > $W/$m.seal.log 2>&1
mv $o/$m.glb.blend $o/$m.glb.lod.json $W/ 2>/dev/null
echo "$m $(grep -o 'SEAL.*' $W/$m.seal.log)"; done
