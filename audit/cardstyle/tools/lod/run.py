import json,shutil,os
from decim import decim
D='/workspace/godot-art/buildings'; S='/workspace/beth-world/www/proto3d/models/beth/hi/buildings_card2'
idx=json.load(open(D+'/index.json')); E={e['id']:e for e in idx['buildings']}
JOBS={'guildhall':['lod1'],'port':['lod1','lod2'],'colosseum':['lod1','lod2'],'library':['lod2'],'mage_academy':['lod1','lod2'],'temple':['lod2']}
for k,lv in JOBS.items():
    H=E[k]['high']['tris']
    for l in lv:
        f=f'bld_{k}_card2_{l}.glb'; t=H*(0.47 if l=='lod1' else 0.185)
        a,b=decim('/tmp/lodbak/'+f,D+'/'+f,t); shutil.copy2(D+'/'+f,S+'/'+f); print(k,l,'before',E[k]['medium' if l=='lod1' else 'low']['tris'],'after',b,'of high',H,round(b/H,3),flush=True)
