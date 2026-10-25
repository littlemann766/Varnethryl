import bpy,numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/workspace/beth-world/www/proto3d/models/beth/tripo/volcano_game.glb')
o=[o for o in bpy.data.objects if o.type=='MESH'][0]
dg=bpy.context.evaluated_depsgraph_get(); bvh=BVHTree.FromObject(o,dg)
me=o.data; uvl=me.uv_layers.active.data
img=bpy.data.images[0]; W,Hh=img.size; px=np.array(img.pixels[:],dtype=np.float32).reshape(Hh,W,4)
N=151; xs=np.linspace(-150,150,N)
H=np.zeros((N,N),np.float32); C=np.zeros((N,N,3),np.float32); M=np.zeros((N,N),bool)
mw=o.matrix_world; inv=mw.inverted()
for j,y in enumerate(xs):
  for i,x in enumerate(xs):
    org=inv@Vector((x,y,500)); d=(inv.to_3x3()@Vector((0,0,-1))).normalized()
    loc,nor,fi,dist=bvh.ray_cast(org,d)
    if loc is None: continue
    w=mw@loc; H[j,i]=w.z; M[j,i]=True
    p=me.polygons[fi]; vs=[me.vertices[v].co for v in p.vertices]
    import mathutils
    bc=mathutils.geometry.intersect_point_tri(loc,*vs[:3]) 
    # barycentric
    a,b,c=vs[:3]; v0=b-a; v1=c-a; v2=loc-a
    d00=v0.dot(v0);d01=v0.dot(v1);d11=v1.dot(v1);d20=v2.dot(v0);d21=v2.dot(v1);den=d00*d11-d01*d01 or 1e-9
    vv=(d11*d20-d01*d21)/den; ww=(d00*d21-d01*d20)/den; uu=1-vv-ww
    li=p.loop_indices; uv=uu*uvl[li[0]].uv+vv*uvl[li[1]].uv+ww*uvl[li[2]].uv
    C[j,i]=px[int(np.clip(uv.y,0,1)*(Hh-1)),int(np.clip(uv.x,0,1)*(W-1)),:3]
np.savez('src.npz',H=H,C=C,M=M,xs=xs)
print(M.sum(),H.max(), C[M].mean(0))
