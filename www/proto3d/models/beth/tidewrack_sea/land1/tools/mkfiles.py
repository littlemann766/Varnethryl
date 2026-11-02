import json,os,glob
from files import *
O='/tmp/land1o/'
d={}
for r in REG:
    L=[]
    for f in files(r):
        b=f.split('/')[-1][:-4]; p=O+f if os.path.exists(O+f) else G+f
        L.append(dict(path=p,terrain=is_terrain(b)))
    for p in sorted(glob.glob(O+REG[r][0]+REG[r][1]+'land_*.glb')):
        if not p.endswith('_lod1.glb') and not p.endswith('_col.glb'): L.append(dict(path=p,terrain=False))
    d[r]=L
json.dump(d,open('files_after.json','w'))
