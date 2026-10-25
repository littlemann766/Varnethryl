import bpy,sys,json,numpy as np
a=sys.argv[sys.argv.index('--')+1:]; PFX=a[1] if len(a)>1 else 'fly_'
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.vertex_groups]
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.animation_data:
        o.animation_data.action=None
        for tr in o.animation_data.nla_tracks: tr.mute=True
EI={o.name:np.array([e.vertices[:] for e in o.data.edges]) for o in meshes}
def cur(o):
    me=o.evaluated_get(bpy.context.evaluated_depsgraph_get());md=me.to_mesh();R=np.empty(len(md.vertices)*3);md.vertices.foreach_get('co',R);me.to_mesh_clear();return R.reshape(-1,3)
def L(o,R): e=EI[o.name]; return np.linalg.norm(R[e[:,0]]-R[e[:,1]],axis=1)
for pb in arm.pose.bones: pb.matrix_basis.identity()
sc.frame_set(0); L0={o.name:L(o,np.array([v.co[:] for v in o.data.vertices])) for o in meshes}
out={}
for act in [x for x in bpy.data.actions if x.name.startswith(PFX)]:
    arm.animation_data.action=act; s,e=map(int,act.frame_range); res={}
    for fr in range(s,e+1,2):
        sc.frame_set(fr)
        for o in meshes:
            l0=L0[o.name]; ok=l0>1e-4; r=L(o,cur(o))[ok]/l0[ok]-1
            res[o.name]=max(res.get(o.name,0),float(np.percentile(r,99)))
    out[act.name]={k:round(v*100,1) for k,v in res.items()}
print('STR',json.dumps(out))
