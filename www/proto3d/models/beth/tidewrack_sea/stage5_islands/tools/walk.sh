#!/bin/bash
# refresh manifest landings + run walk test; args: out.json [ids]
S=/workspace/godot-art/ocean_stage5_islands; python3 - <<'P'
import json
p='/workspace/godot-art/ocean_stage5_islands/stage5_manifest.json'; m=json.load(open(p)); m['landings']=json.load(open('/workspace/godot-art/ocean_stage5_islands/landings_v1.json')); json.dump(m,open(p,'w'),indent=1)
P
out=$1; shift; timeout 700 godot --headless --fixed-fps 60 --path /tmp/s5w -s walk5.gd -- $S/stage5_manifest.json $out "$@" 2>&1 | grep -E "ISLAND|SCRIPT ERR"
python3 - $out <<'P'
import json,sys
r=json.load(open(sys.argv[1])); t=o=0
for k,v in r.items():
  for n,x in v.items():
    if n=='pier_boards': continue
    t+=1; o+=x['ok']
    if not x['ok']: print(' ',k,'|',n,x['why'],x['at'],'wp',x.get('wp'),'/',x.get('of'),(x.get('hits') or [''])[0])
print('TOTAL',o,'/',t)
P
