import bpy,numpy as np
bpy.ops.wm.open_mainfile(filepath='work/fiend_post.blend'); sc=bpy.context.scene
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; me=[o for o in bpy.data.objects if o.type=='MESH' and 'lod1' not in o.name][0]
AG=[g.index for g in me.vertex_groups if any(k in g.name for k in ('upperArm','foreArm','hand','fingers'))]
LG=[g.index for g in me.vertex_groups if any(k in g.name for k in ('thigh','shin'))]
av=np.array([v.index for v in me.data.vertices if sum(g.weight for g in v.groups if g.group in AG)>0.6]); lv=np.array([v.index for v in me.data.vertices if sum(g.weight for g in v.groups if g.group in LG)>0.6])
from mathutils.kdtree import KDTree
for act in bpy.data.actions:
    arm.animation_data.action=act; mn=9
    for f in range(0,int(act.frame_range[1])+1,2):
        sc.frame_set(f); dg=bpy.context.evaluated_depsgraph_get(); ev=me.evaluated_get(dg); m=ev.to_mesh(); co=np.empty(len(m.vertices)*3); m.vertices.foreach_get('co',co); co=co.reshape(-1,3); ev.to_mesh_clear()
        L=co[lv]; kd=KDTree(len(L))
        for i,p in enumerate(L): kd.insert(p,i)
        kd.balance(); A=co[av][::4]
        mn=min(mn,min(kd.find(p)[2] for p in A))
    print('MIND',act.name,round(mn,3),len(av),len(lv))
