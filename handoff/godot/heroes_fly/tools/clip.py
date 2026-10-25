import bpy,sys,json,numpy as np
from mathutils.kdtree import KDTree
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; sc=bpy.context.scene
o=max([o for o in bpy.data.objects if o.type=='MESH' and o.vertex_groups],key=lambda o:len(o.data.vertices))
GN={g.index:g.name for g in o.vertex_groups}
dom=[GN[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in o.data.vertices]
cl=np.array([d.startswith(('cape','coat')) for d in dom]); lg=np.array([d.startswith(('thigh','shin','foot','toe')) for d in dom])
out={}
if cl.sum()==0: print('CLIP none'); sys.exit()
for act in [x for x in bpy.data.actions if x.name.startswith('fly_')]:
    arm.animation_data.action=act; s,e=map(int,act.frame_range); worst=0
    for fr in range(s,e+1,4):
        sc.frame_set(fr); me=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m=me.to_mesh()
        co=np.array([v.co[:] for v in m.vertices]); no=np.array([v.normal[:] for v in m.vertices]); me.to_mesh_clear()
        li=np.where(lg)[0]; kd=KDTree(len(li))
        for k,i in enumerate(li): kd.insert(co[i],k)
        kd.balance(); c=0
        for i in np.where(cl)[0]:
            p,k,d=kd.find(co[i])
            if d<0.08 and np.dot(co[i]-co[li[k]],no[li[k]])< -0.01: c+=1
        worst=max(worst,c)
    out[act.name.split('_')[0]+'_'+act.name.split('_')[1]+('_'+act.name.split('_')[2] if 'bank' in act.name else '')]=worst
print('CLIP',int(cl.sum()),json.dumps(out))
