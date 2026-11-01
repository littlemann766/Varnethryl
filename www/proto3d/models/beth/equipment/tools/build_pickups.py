import bpy,sys,os,json
sys.path.insert(0,'/workspace/godot-art/loot3_tools')
import bl, pickups3d as P, greedy
O="/tmp/l3/www/proto3d/models/beth/equipment/meshes/pickups"; os.makedirs(O,exist_ok=True); st={}
for a,f in P.all_items():
    v,vs,piv=P.build(f); n=a[4:]
    hi=len(greedy.quads(v.g)); vv=v.down(); k=2
    for lod,(gg,s) in enumerate(((v,vs),(vv,vs*k))):
        bl.reset(); bl.MATS.clear(); nm=n+("_lod1" if lod else "")
        ob,tr=bl.mesh_g(gg,nm,s,origin=tuple(-c*vs for c in piv)); bl.export(f"{O}/{nm}.glb",[ob]); st.setdefault(n,[]).append(tr)
json.dump(st,open("/tmp/l3w/pickup_stats.json","w"))
