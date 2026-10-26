SK=$(python3 -c "import json;print(json.load(open('res2.json'))['lunara']['seck'])")
for TR in 0.02b; do
 [ -f out/lun_t$TR.done ] && continue
 SECK=$SK REWEIGHT=1 CHAINW=1 SEAM=1 RFM=0.015 TFIX=lun_tfix.json TR=0.02 $B -b -P fly.py -- /workspace/rigged/lunara_h.glb out/lun_t$TR.glb > /tmp/lt$TR.log 2>&1
 grep TFIX /tmp/lt$TR.log; echo T$TR; FRAMES=1 STEP=1 $B -b -P pen.py -- out/lun_t$TR.glb fly_ 2>&1 | grep -E "FAIL|REST" | awk '{print $1,$2}' | uniq -c
 touch out/lun_t$TR.done
done; echo ALLDONE
