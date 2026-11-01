import bpy,sys,json,os
sys.path.insert(0,'/workspace/godot-art/loot3_tools')
import bl, weapons3d as W, greedy
from edata import RARITIES
O="/tmp/l3/www/proto3d/models/beth/equipment/meshes/weapons"; os.makedirs(O,exist_ok=True)
jobs=[(f,r) for f in W.FAM for r in RARITIES]+[(n,None) for n in ['worldbreaker','winters_end','soulrender','dawnbringer','voidfang','serpents_kiss','eternal_cinder']]
k,n=int(sys.argv[-2]),int(sys.argv[-1]); st={}
for f,r in jobs[k::n]:
    v,vs,piv=W.build(f,r) if r else W.named(f); name=f"{f}_{r}" if r else f"named_{f}"
    hi=len(greedy.quads(v.g)); vv=v.down(); kk=2
    while len(greedy.quads(vv.g))>0.5*hi and kk<8: vv=vv.down(); kk*=2
    s=[0,0]
    for lod,(gg,sz) in enumerate(((v,vs),(vv,vs*kk))):
        bl.reset(); bl.MATS.clear(); nm=name+("_lod1" if lod else "")
        ob,tr=bl.mesh_g(gg,nm,sz,origin=tuple(-c*vs for c in piv)); bl.export(f"{O}/{nm}.glb",[ob]); s[lod]=tr
    st[name]=s
json.dump(st,open(f"/tmp/l3w/wstats_{k}.json","w"))
