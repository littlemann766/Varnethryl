set -e
SK=$(python3 -c "import json;print(json.load(open('res2.json'))['lunara']['seck'])")
echo '{}' > lun_extra.json
for it in 1 2 3 4 5 6; do
 SECK=$SK REWEIGHT=1 CHAINW=1 SEAM=1 RFM=0.015 EXTRA=lun_extra.json $B -b -P fly.py -- /workspace/rigged/lunara_h.glb out/lunara_fly_v5.glb > /tmp/lf.log 2>&1; cp out/lunara_fly_v5.glb out/lun_it$it.glb; cp lun_extra.json lun_extra_it$it.json; true 2>&1
 FRAMES=1 STEP=1 $B -b -P pen.py -- out/lunara_fly_v5.glb fly_ 2>&1 | grep FAIL > /tmp/fails.txt || true
 echo "iter $it fails $(wc -l < /tmp/fails.txt)"; cat /tmp/fails.txt | awk '{print $2}' | sort | uniq -c
 [ -s /tmp/fails.txt ] || break
 python3 - <<'P'
import json; e=json.load(open('lun_extra.json'))
for l in open('/tmp/fails.txt'):
    _,c,f,_n=l.split(); d=e.setdefault(c,{}); d[f]=d.get(f,0)+3
json.dump(e,open('lun_extra.json','w'))
P
done
