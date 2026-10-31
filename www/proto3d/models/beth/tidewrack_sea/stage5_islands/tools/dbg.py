import json,trimesh,numpy as np,glob,sys
r=json.load(open('walk3.json'));m=json.load(open('/workspace/godot-art/ocean_stage5_islands/stage5_manifest.json'))
D={'A':'stage1','B':'stage2','frost':'stage4','ash':'stage4'};P={'A':'arch_','B':'coast_','frost':'frost_','ash':'ash_'}
for k,v in r.items():
  bad=[(n,x) for n,x in v.items() if not x['ok']]
  if not bad: continue
  I=m['islands'][k];reg=I['region']
  base=trimesh.util.concatenate([trimesh.load(f,force='mesh') for f in glob.glob(f'tw/{D[reg]}/{P[reg]}*_col.glb') if 'storm' not in f])
  isl=trimesh.load(f"/workspace/godot-art/ocean_stage5_islands/meshes/{reg}/{I['files']['col']}.glb",force='mesh')
  for n,x in bad:
    a=np.array(x['at']);out=[]
    for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]:
      o=np.array([[a[0]+dx,a[1]+6,a[2]+dz]]);hs=[]
      for nm,mm in (('B',base),('I',isl)):
        loc,_,_=mm.ray.intersects_location(o,[[0,-1,0]]);hs+= [f"{nm}{y:.1f}" for y in sorted(np.asarray(loc).reshape(-1,3)[:,1],reverse=True)[:3]]
      out.append(' '.join(hs))
    print(k,n,x['why'],a.tolist(),'wp',x['wp'],'|',' ; '.join(out))
