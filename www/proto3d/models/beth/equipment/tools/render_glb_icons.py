import bpy,sys,os,math,json
sys.path.insert(0,'/workspace/godot-art/loot3_tools'); import bl
from mathutils import Vector
L=json.load(open(sys.argv[-3])); k,n=int(sys.argv[-2]),int(sys.argv[-1])
for item in L[k::n]:
    f,out=item[0],item[1]; rot=item[2] if len(item)>2 else -45; res=item[3] if len(item)>3 else 128
    bl.reset(); bpy.ops.import_scene.gltf(filepath=f); objs=list(bpy.context.selected_objects); bl.srgb_fix_imported(objs)
    for o in objs: o.rotation_euler=(0,math.radians(rot),0)
    bpy.context.view_layer.update(); pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box]
    mn=Vector([min(p[i] for p in pts) for i in range(3)]); mx=Vector([max(p[i] for p in pts) for i in range(3)]); c=(mn+mx)/2; d=max(mx-mn)
    cam=bl.rig_scene(res=res,ortho=d*1.2,el=15,yaw=10,target=tuple(c)); sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version>=(4,2) else 'BLENDER_EEVEE'; sc.eevee.taa_render_samples=8
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
