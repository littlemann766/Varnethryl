#!/bin/bash
# run33.sh name mine_lod0.glb outdir beth_lod0.glb [beth_lods...]
set -e; cd /workspace/t32; B=/workspace/tools/blender-4.2.3-linux-x64/blender; T=tools
n=$1; mine=$2; od=$3; beth=$4; shift 4; W=w/${n}_33; L=log/${n}_33.log; : > $L; mkdir -p $od m33
$B -b -P /workspace/vx3/imp.py -- $mine ${W}_m.blend >>$L 2>&1
$B -b -P $T/merge33.py -- $beth ${W}_m.blend ${W}_mg.blend >>$L 2>&1; rm -f ${W}_m.blend*; cp ${W}_mg.blend.merge.json m33/$n.merge.json
DIL=1 ABDLIM=35 $B -b -P $T/alfix2.py -- ${W}_mg.blend ${W}_a1.blend >>$L 2>&1; cp ${W}_a1.blend.alfix.json m33/${n}_pass1.alfix.json; rm -f ${W}_mg.blend*
ABDLIM=50 MAXA=60 $B -b -P $T/alfix2.py -- ${W}_a1.blend ${W}_fin.blend >>$L 2>&1; cp ${W}_fin.blend.alfix.json m33/${n}_pass2.alfix.json; rm -f ${W}_a1.blend*
$B -b -P $T/meas32.py -- ${W}_fin.blend m33/${n}_meas.json "" >>$L 2>&1
CL=$(python3 -c "import json;print(','.join(json.load(open('m33/${n}_meas.json'))['clips']))")
$B -b -P /workspace/vx3/check1.py -- ${W}_fin.blend $CL m33/${n}_check1.json >>$L 2>&1
$B -b -P /workspace/vx3/exp.py -- ${W}_fin.blend $od/$(basename $beth) >>$L 2>&1; rm -f $od/$(basename $beth).blend
for lg in "$@"; do b=$(basename $lg .glb)
 $B -b -P $T/lodcopy.py -- $lg ${W}_fin.blend $od/$b.glb >>$L 2>&1
 ABDLIM=50 MAXA=60 $B -b -P $T/alfix2.py -- $od/$b.glb.blend ${W}_lx.blend >>$L 2>&1; cp ${W}_lx.blend.alfix.json m33/${b}_lod.alfix.json
 rm -f $od/$b.glb.blend*; $B -b -P /workspace/vx3/exp.py -- ${W}_lx.blend $od/$b.glb >>$L 2>&1; rm -f ${W}_lx.blend*
 $B -b -P /workspace/vx3/check1.py -- $od/$b.glb.blend $CL m33/${b}_check1.json >>$L 2>&1
 $B -b -P $T/meas32.py -- $od/$b.glb.blend m33/${b}_meas.json "" >>$L 2>&1; rm -f $od/$b.glb.blend*
done; rm -f ${W}_fin.blend*; echo "- $(date +%H:%M) run33 done $n -> $od" >> progress.md
