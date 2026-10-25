# street-dressing kit -> /workspace/godot-art/props_street (shared card2 atlas copied to props_street/atlas)
import sys,os,json,shutil,glob,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kit2, detail, deci
from geo import Mesh
from writer import write_glb
D='/workspace/godot-art/props_street'; A='/workspace/beth-world/www/proto3d/models/beth/hi/buildings_card2/atlas'
os.makedirs(D+'/atlas',exist_ok=True)
for f in glob.glob(A+'/card2_*.jpg'): shutil.copy2(f,D+'/atlas/')
IDX=[]
for name,fn in detail.PROPS.items():
    e=dict(id=name); hi=None
    for q,(lv,suf) in enumerate((('high',''),('medium','_lod1'),('low','_lod2'))):
        kit2.Q=q; m=Mesh(); fn(m); P,F,UV,N=m.arrays(-1)
        if q==0: hi=len(F)
        else:
            cap=max(12,int(hi*(0.5 if q==1 else 0.2)*0.97))
            if len(F)>cap: P,F,UV=deci.decimate(P,F,UV,cap); N=deci.normals(P,F)
        f=f'{D}/prop_{name}{suf}.glb'; write_glb(f,P,F,UV,N,'prop_'+name,'atlas')
        e[lv]=dict(file=os.path.basename(f),tris=len(F),bbox_min=P.min(0).round(2).tolist(),bbox_max=P.max(0).round(2).tolist())
    e['phone_high_lod']='high'; IDX.append(e); print(name,hi,e['medium']['tris'],e['low']['tris'],flush=True)
kit2.Q=0
json.dump(dict(note='Beth street-dressing kit on the shared card2 atlas (atlas/, 2048, one material). Origin at ground centre, +Z front, metres. no suffix=High, _lod1<=50%, _lod2<=20%.',props=IDX),open(D+'/index.json','w'),indent=1)
