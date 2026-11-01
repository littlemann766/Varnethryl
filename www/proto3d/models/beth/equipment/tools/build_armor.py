import bpy,sys,json,os
sys.path.insert(0,'/workspace/godot-art/loot3_tools')
import bl, armor3d as A
from edata import RARITIES
O="/tmp/l3/www/proto3d/models/beth/equipment/meshes"
fams=sys.argv[sys.argv.index('--')+1:]
stats={}
for fam in fams:
    os.makedirs(f"{O}/{fam}",exist_ok=True)
    for slot in A.PARTS:
        for r in RARITIES:
            for part,v,vs,piv in A.build(slot,fam,r):
                n=f"{fam}_{r}_{part}"; st=[0,0]
                import greedy
                hi=len(greedy.quads(v.g)); vv=v.down(); k=2
                while len(greedy.quads(vv.g))>0.5*hi and k<8: vv=vv.down(); k*=2
                for lod,(gg,s) in enumerate(((v,vs),(vv,vs*k))):
                    bl.reset(); bl.MATS.clear()
                    org=tuple(-c*vs for c in piv)
                    ob,tr=bl.mesh_g(gg,n+("_lod1" if lod else ""),s,origin=org)
                    if fam=="plate": ob,tr=bl.smooth_plate(ob,gg,s,org)   # polish: no voxel stair-steps on plate
                    bl.export(f"{O}/{fam}/{n}{'_lod1' if lod else ''}.glb",[ob]); st[lod]=tr
                stats[n]=st
json.dump(stats,open(f"/tmp/l3w/armor_stats_{'_'.join(fams)}.json","w"))
