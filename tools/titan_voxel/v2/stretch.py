import bpy,sys,json,numpy as np
a=sys.argv[sys.argv.index('--')+1:]; src,outp=a
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
body=max([o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==arm],key=lambda o:len(o.data.vertices))
E=np.array([e.vertices[:] for e in body.data.edges])
def co():
    dg=bpy.context.evaluated_depsgraph_get(); e=body.evaluated_get(dg); m=e.to_mesh(); c=np.empty(len(m.vertices)*3); m.vertices.foreach_get('co',c); e.to_mesh_clear(); return c.reshape(-1,3)
arm.animation_data_create(); arm.animation_data.action=None; arm.data.pose_position='REST'; bpy.context.view_layer.update()
r=co(); L0=np.linalg.norm(r[E[:,0]]-r[E[:,1]],axis=1); ok=L0>1e-6
arm.data.pose_position='POSE'; res={}
for act in bpy.data.actions:
    arm.animation_data.action=act; f0,f1=[int(round(x)) for x in act.frame_range]; vals=[]
    for f in range(f0,f1+1,3):
        sc.frame_set(f); c=co(); L=np.linalg.norm(c[E[:,0]]-c[E[:,1]],axis=1); vals.append(np.abs(L[ok]/L0[ok]-1))
    v=np.concatenate(vals); res[act.name.split('_'+arm.name)[0]]=round(float(np.percentile(v,99))*100,2)
json.dump(res,open(outp,'w')); print('STRETCH max-clip p99 %',max(res.values()),sorted(res.items(),key=lambda x:-x[1])[:5])
