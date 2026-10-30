#!/bin/bash
# fix2.sh name src.glb outglb [lods...]  ; env passed to mfix
set -e; cd /workspace/t32; B=/workspace/tools/blender-4.2.3-linux-x64/blender; T=tools; n=$1; g=$2; o=$3; shift 3; W=w/${n}_2; L=log/${n}_2.log; : > $L
$B -b -P /workspace/vx3/imp.py -- $g $W.blend >>$L 2>&1
[ -f m/${n}_before.json ] && [ "$(python3 -c "import json;print(len(json.load(open('m/${n}_before.json'))['clips'].get('run',{})))")" != 0 ] || $B -b -P $T/meas32.py -- $W.blend m/${n}_before.json "" >>$L 2>&1
$B -b -P $T/mfix.py -- $W.blend ${W}_fin.blend >>$L 2>&1; cp ${W}_fin.blend.mfix.json m/${n}_2.mfix.json; rm -f $W.blend*
$B -b -P $T/meas32.py -- ${W}_fin.blend m/${n}_after.json "" >>$L 2>&1
CL=$(python3 -c "import json;print(','.join(json.load(open('m/${n}_after.json'))['clips']))")
$B -b -P /workspace/vx3/check1.py -- ${W}_fin.blend $CL m/${n}_check.json >>$L 2>&1
$B -b -P /workspace/vx3/exp.py -- ${W}_fin.blend $o >>$L 2>&1; rm -f $o.blend
for lg in "$@"; do b=$(basename $lg .glb); od=$(dirname $o)
 $B -b -P $T/lodcopy.py -- $lg ${W}_fin.blend $od/$b.glb >>$L 2>&1
 $B -b -P /workspace/vx3/check1.py -- $od/$b.glb.blend $CL m/${b}_check.json >>$L 2>&1; $B -b -P $T/meas32.py -- $od/$b.glb.blend m/${b}_after.json "" >>$L 2>&1; rm -f $od/$b.glb.blend*
done; rm -f ${W}_fin.blend*; echo "- $(date +%H:%M) fix2 $n -> $o" >> progress.md
