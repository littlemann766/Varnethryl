import bpy,sys,json
import numpy as np
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
def minz():
    dg=bpy.context.evaluated_depsgraph_get(); e=ob.evaluated_get(dg); m=e.to_mesh()
    n=len(m.vertices); c=np.empty(n*3); m.vertices.foreach_get('co',c); c=c.reshape(-1,3)
    W=np.array(ob.matrix_world); z=(c@W[:3,:3].T+W[:3,3])[:,2]; e.to_mesh_clear(); return z.min()
arm.animation_data.action=None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update(); r=minz(); res={}
for an in a[1].split(','):
    act=bpy.data.actions[an]; arm.animation_data.action=act; f1=int(act.frame_range[1]); zs=[]
    for f in range(0,f1+1): sc.frame_set(f); zs.append(minz()-r)
    res[an]={'min_m':round(min(zs),3),'max_lowest_m':round(max(zs),3)}
print('GROUND',json.dumps(res))
