exec(open('pen.py').read().split("for pb in arm.pose.bones")[0])
import os
act=[x for x in bpy.data.actions if x.name.startswith(a[1])][0]; arm.animation_data.action=act
s,e=map(int,act.frame_range)
o=BODY[0]; GN={g.index:g.name for g in o.vertex_groups}
TORSO=('hips','spine','chest','upperChest','thigh','shin','foot','toe')
for fr in range(s,e):
    sc.frame_set(fr); dg=bpy.context.evaluated_depsgraph_get(); m=o.evaluated_get(dg).to_mesh()
    co=[v.co.copy() for v in m.vertices]; dom=INFO[o.name]
    body=[d.startswith(TORSO) for d in dom]
    polys=[list(p.vertices) for p in m.polygons if all(body[i] for i in p.vertices)]
    bvh=BVHTree.FromPolygons(co,polys)
    for i,d in enumerate(dom):
        if d.startswith('cape') and is_inside(bvh,co[i]):
            loc,nor,fi,dist=bvh.find_nearest(co[i])
            print('F',fr,i,round(dist,4),'face',dom[polys[fi][0]],sorted([(round(g.weight,2),GN[g.group]) for g in o.data.vertices[i].groups],reverse=True)[:4])
    o.evaluated_get(dg).to_mesh_clear()
