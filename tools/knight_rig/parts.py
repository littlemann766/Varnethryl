import bpy,numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/workspace/uploads/ref_armor.glb')
o=[x for x in bpy.data.objects if x.type=='MESH'][0]
bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
me=o.data; co=np.array([v.co[:] for v in me.vertices])
par=np.arange(len(co))
def f(i):
    r=i
    while par[r]!=r: r=par[r]
    while par[i]!=r: par[i],i=r,par[i]
    return r
for p in me.polygons:
    vs=list(p.vertices); r=f(vs[0])
    for v in vs[1:]:
        rv=f(v)
        if rv!=r: par[rv]=r
roots=np.array([f(i) for i in range(len(co))]); u,inv=np.unique(roots,return_inverse=True); K=len(u)
cnt=np.bincount(inv); cen=np.stack([np.bincount(inv,co[:,d])/cnt for d in range(3)],1)
mn=np.full((K,3),1e9); mx=np.full((K,3),-1e9)
np.minimum.at(mn,inv,co); np.maximum.at(mx,inv,co)
np.savez('/tmp/kr/parts.npz',inv=inv,cen=cen,cnt=cnt,mn=mn,mx=mx)
print('K',K)
for k in np.where((cen[:,0]>-8)&(cen[:,0]<12))[0]: print(k,cnt[k],cen[k].round(1),mn[k].round(1),mx[k].round(1))
