import os,shutil,hashlib,subprocess,json,numpy as np
from lib import *
from handtool import process
W='/workspace/';BK=W+'backups/titan_hands_20261025/'
T=['varn-core/handoff/godot/ashentitan_pool/ashentitan_volcano_glow.glb','varn-core/handoff/godot/ashentitan_pool/ashentitan_volcano_glow_lod1.glb',
'varn-core/handoff/godot/ashentitan/ashentitan_volcano_lod1.glb','varn-core/handoff/godot/ashentitan/ashentitan_lod1.glb',
'godot-art/volcano/titan/ashentitan_volcano_glow.glb','godot-art/volcano/titan/ashentitan_volcano_glow_lod1.glb',
'godot-art/characters/ashentitan.glb','godot-art/characters/ashentitan_lod1.glb','godot-art/characters/ashentitan_lod2.glb',
'godot-art/characters/ashentitan_volcano.glb','godot-art/characters/ashentitan_volcano_lod1.glb','godot-art/characters/ashentitan_volcano_lod2.glb',
'varn-core/www/proto3d/models-new/ashentitan_cl_arms.glb','beth-world/www/proto3d/models/beth/volcano/ashentitan_volcano_11x.glb','beth-world/www/proto3d/models-new/ashentitan_cl_arms.glb']
res={}
for t in T:
    src=W+t;bk=BK+t;os.makedirs(os.path.dirname(bk),exist_ok=True)
    if not os.path.exists(bk):shutil.copy2(src,bk)
    j,b=load(bk);n=j['accessors'][j['meshes'][0]['primitives'][0]['attributes']['POSITION']]['count']
    sides,rm=(10,1) if n>20000 else (6,0.5) if n>10000 else (3,0.34)
    tris=process(bk,src,sides,rm)
    subprocess.run(['python3','/tmp/th/dropq.py',src])
    j2,b2=load(src);p=j2['meshes'][0]['primitives'][0]
    h=hashlib.md5(acc(j2,b2,p['attributes']['TEXCOORD_0']).tobytes()).hexdigest()[:6]
    res[t]={'tris':int(j2['accessors'][p['indices']]['count']//3),'tris_before':int(j['accessors'][j['meshes'][0]['primitives'][0]['indices']]['count']//3),'uvset':h}
json.dump(res,open('batch.json','w'),indent=1);print(json.dumps(res,indent=1))
