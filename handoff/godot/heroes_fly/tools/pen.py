import bpy,sys,json,numpy as np,collections,os
from mathutils.bvhtree import BVHTree
exec(open('/workspace/hero-motion/fly/inside_lib.py').read())
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.ops.import_scene.gltf(filepath=a[0])
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; sc=bpy.context.scene
BODY=[o for o in bpy.data.objects if o.type=='MESH' and o.vertex_groups]
for o in bpy.data.objects:
    if o.animation_data:
        o.animation_data.action=None
        for tr in o.animation_data.nla_tracks: tr.mute=True
INFO={}
for o in BODY:
    GN={g.index:g.name for g in o.vertex_groups}
    dom=[GN[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in o.data.vertices]
    INFO[o.name]=dom
def count(detail=False):
    dg=bpy.context.evaluated_depsgraph_get(); allco=[];polys=[];capes=[];doms=[];off=0
    for o in BODY:
        e=o.evaluated_get(dg); m=e.to_mesh(); co=[o.matrix_world@v.co for v in m.vertices]; dom=INFO[o.name]
        body=[d.startswith(('hips','spine','chest','upperChest','thigh','shin','foot','toe')) for d in dom]
        for p in m.polygons:
            if all(body[i] for i in p.vertices): polys.append([i+off for i in p.vertices])
        capes+=[i+off for i,d in enumerate(dom) if d.startswith('cape')]; doms+=dom; allco+=co; off+=len(co); e.to_mesh_clear()
    if not polys or not capes: return 0,{}
    bvh=BVHTree.FromPolygons(allco,polys); c=0; where=collections.Counter()
    for i in capes:
        p=allco[i]; loc,nor,fi,d=bvh.find_nearest(p)
        if is_inside(bvh,p):
            c+=1; where[(doms[i],round(p.z,1))]+=1
    return c,where
for pb in arm.pose.bones: pb.matrix_basis.identity()
arm.animation_data.action=None; sc.frame_set(0); c,w=count(); print('REST',c,w.most_common(6))
pfx=a[1] if len(a)>1 else 'fly_'
out={}
for act in [x for x in bpy.data.actions if x.name.startswith(pfx)]:
    arm.animation_data.action=act; s,e=map(int,act.frame_range); mx=0; ww=None
    for fr in range(s,e+1, int(os.environ.get('STEP','1'))):
        sc.frame_set(fr); c,w=count()
        if c and os.environ.get('FRAMES'): print('FAIL',act.name.split('_Darius')[0].split('_'+arm.name)[0],fr,c)
        if c>mx: mx=c; ww=w
    out[act.name]=mx; print('PEN',act.name,mx,ww.most_common(5) if ww else '')
