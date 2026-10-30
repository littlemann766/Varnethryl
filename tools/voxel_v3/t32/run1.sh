#!/bin/bash
# usage: run1.sh name lod0.glb outdir newclips(1/0) [lod1.glb lod2.glb ...]
case "$1" in pip|phoenix) echo "- skip $1 (own rig) in humanoid batch" >> progress.md; exit 0;; esac
set -e; cd /workspace/t32; B=/workspace/tools/blender-4.2.3-linux-x64/blender; T=tools
n=$1; g=$2; od=$3; nc=$4; shift 4; mkdir -p $od m; W=w/$n; L=log/$n.log; mkdir -p log; : > $L
$B -b -P /workspace/vx3/imp.py -- $g $W.blend >>$L 2>&1
$B -b -P $T/meas32.py -- $W.blend m/${n}_before.json "" >>$L 2>&1
if [ $nc = 1 ]; then
 CLIPS="jump_start:Jump_Start,jump_loop:Jump_Loop,jump_land:Jump_Land,swim_tread:Swim_Idle_Loop,swim_stroke:Swim_Fwd_Loop" NOLOCK=jump_loop,swim_tread,swim_stroke $B -b -P $T/rt3.py -- $W.blend ${W}_rt x >>$L 2>&1
 $B -b -P $T/newclips.py -- ${W}_rt.blend ${W}_nc.blend >>$L 2>&1; rm -f ${W}_rt.blend*
 $B -b -P $T/handfix.py -- ${W}_nc.blend x m/${n}_q.json compute >>$L 2>&1
 python3 - m/${n}_q.json <<'P'
import json,sys;Q=json.load(open(sys.argv[1]))
for k,v in Q.items():
  for s in v.values(): s['fix']= k in('jump','jump_start','jump_loop','jump_land','swim_tread','swim_stroke') and s['mean_offset_deg']>30
json.dump(Q,open(sys.argv[1],'w'),indent=1)
P
 $B -b -P $T/handfix.py -- ${W}_nc.blend ${W}_hf.glb m/${n}_q.json apply >>$L 2>&1; rm -f ${W}_nc.blend* ${W}_hf.glb
 S=${W}_hf.glb.blend; LC=run,walk,jump,jump_start,jump_land
else S=$W.blend; LC=run,walk; fi
LEGCLIPS=$LC $B -b -P $T/mfix.py -- $S ${W}_fin.blend >>$L 2>&1; cp ${W}_fin.blend.mfix.json m/${n}.mfix.json
rm -f ${W}_hf.glb.blend* $W.blend*
$B -b -P $T/meas32.py -- ${W}_fin.blend m/${n}_after.json "" >>$L 2>&1
CL=$(python3 -c "import json;print(','.join(json.load(open('m/${n}_after.json'))['clips']))")
$B -b -P /workspace/vx3/check1.py -- ${W}_fin.blend $CL m/${n}_check.json >>$L 2>&1 || echo checkfail >>$L
$B -b -P /workspace/vx3/exp.py -- ${W}_fin.blend $od/$(basename $g) >>$L 2>&1; rm -f $od/$(basename $g).blend
for lg in "$@"; do b=$(basename $lg .glb)
 $B -b -P $T/lodcopy.py -- $lg ${W}_fin.blend $od/$b.glb >>$L 2>&1; $B -b -P /workspace/vx3/check1.py -- $od/$b.glb.blend $CL m/${b}_check.json >>$L 2>&1 || echo checkfail >>$L; $B -b -P $T/meas32.py -- $od/$b.glb.blend m/${b}_after.json "" >>$L 2>&1; rm -f $od/$b.glb.blend*
done
rm -f ${W}_fin.blend*; echo "- $(date +%H:%M) done $n -> $od" >> progress.md
