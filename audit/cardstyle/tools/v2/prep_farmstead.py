# Farmstead fix: the farmhouse and barn are ONE welded building on card_farmhouse_barn; the old plane split (x=-0.095 src)
# left a slice of the house on the barn. Rebuild farmhouse_tripo as the whole building from farmstead_full_game.glb
# (user_1025.glb x40), minus the fence_paddock and 2 stray rail faces; centred X/Z, base y=0; LODs via deci.
import numpy as np, trimesh, json, shutil, sys
from PIL import Image
from deci import decimate
SRC='/workspace/beth-world/www/proto3d/models/beth/tripo2/farmstead_full_game.glb'; D='/workspace/godot-art/buildings'
m=trimesh.load(SRC,force='mesh',process=False); c=m.triangles_center
fence=(c[:,0]<-7.0)&(c[:,2]>-1.2)&(c[:,1]>0.5)&(c[:,1]<2.9)&((c[:,0]<-15)|(c[:,2]>6.5))
V=m.vertices[m.faces]; stray=(V[:,:,2].max(1)>6.2)|(V[:,:,0].min(1)<-15.6)
m=m.submesh([np.where(~(fence|stray))[0]],append=True)
b=m.bounds; off=np.array([-(b[0,0]+b[1,0])/2,-b[0,1],-(b[0,2]+b[1,2])/2]); m.vertices=m.vertices+off
mat=m.visual.material; tex=mat.baseColorTexture
def save(mesh,path): mesh.export(path)
out={}
for nm in ('farmhouse_tripo','barn_stable_tripo'):
    base=f'{D}/tripo/bld_{nm}'; save(m,base+'.glb'); n=len(m.faces); out[nm]=[n]
P=m.vertices[m.faces].reshape(-1,3); UV=m.visual.uv[m.faces].reshape(-1,2); F=np.arange(len(P)).reshape(-1,3)
for k,fr,ts in ((1,0.5,1024),(2,0.2,512)):
    P2,F2,UV2=decimate(P,F,UV,int(len(m.faces)*fr*0.97))
    mt=trimesh.visual.material.PBRMaterial(name=mat.name,baseColorTexture=tex.resize((ts,ts),Image.LANCZOS),metallicFactor=0.0,roughnessFactor=0.9)
    l=trimesh.Trimesh(P2,F2,process=False,visual=trimesh.visual.TextureVisuals(uv=UV2,material=mt))
    for nm in out: save(l,f'{D}/tripo/bld_{nm}_lod{k}.glb'); out[nm].append(len(F2))
print('offset',off.round(3),'bounds',m.bounds.round(2).tolist(),out)
json.dump(dict(offset=off.tolist(),tris=out['farmhouse_tripo'],bmin=m.bounds[0].tolist(),bmax=m.bounds[1].tolist()),open('/tmp/farm_fix.json','w'))
