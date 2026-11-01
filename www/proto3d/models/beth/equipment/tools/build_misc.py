import bpy,sys,os
sys.path.insert(0,'/workspace/godot-art/loot3_tools')
import bl, gmodels as G, armor3d as A, greedy
from edata import RARITIES
O="/tmp/l3/www/proto3d/models/beth/equipment/meshes/companion"; os.makedirs(O,exist_ok=True)
for i,r in enumerate(RARITIES):
    p=A.pal("leather",r); v,vs,piv=G.collar(p,A.tval(i))
    if i>=4: A.filigree(v,p)
    if i==5: A.molten(v,p)
    vv=v.down(); k=2
    for lod,(gg,s) in enumerate(((v,vs),(vv,vs*k))):
        bl.reset(); bl.MATS.clear(); n=f"collar_{r}"+("_lod1" if lod else "")
        ob,tr=bl.mesh_g(gg,n,s,origin=tuple(-c*vs for c in piv)); bl.export(f"{O}/{n}.glb",[ob]); print(n,tr)
