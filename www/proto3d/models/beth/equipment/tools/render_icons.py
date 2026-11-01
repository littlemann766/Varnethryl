import bpy,sys,json,os,math
sys.path.insert(0,'/workspace/godot-art/loot3_tools'); import bl
from mathutils import Vector
E_="/tmp/l3/www/proto3d/models/beth/"; OUT="/tmp/l3w/icons_raw"; os.makedirs(OUT,exist_ok=True)
apps=json.load(open(E_+"equipment/appearances.json"))["appearances"]
k,n=int(sys.argv[-2]),int(sys.argv[-1])
jobs=sorted([a for a,e in apps.items() if e["kind"] in("wearable","held","companion") and (e.get("mesh") or e.get("parts"))])[k::n]
def p2(path): return E_+path.replace("res://","")
for a in jobs:
    e=apps[a]; out=f"{OUT}/{a}.png"
    if os.path.exists(out): continue
    bl.reset()
    files=[]
    if e["kind"]=="wearable":
        ps=[p for p in e["parts"] if not p["mirror_x"]]
        files=[(p2(p["mesh"]),p["attach_part"]) for p in ps]
    else: files=[(p2(e["mesh"]),"x")]
    objs=[]
    for f,part in files:
        bpy.ops.import_scene.gltf(filepath=f); ob=bpy.context.selected_objects[0]
        if part=="boot_foot_L": ob.location=(0,0,-0.30)
        objs.append(ob); bl.srgb_fix_imported([ob])
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box]
    mn=Vector([min(p[i] for p in pts) for i in range(3)]); mx=Vector([max(p[i] for p in pts) for i in range(3)]); c=(mn+mx)/2; d=max(mx-mn)
    if e["kind"]=="held" and (mx-mn).z==d:
        for o in objs: o.rotation_euler=(0,math.radians(-45),0)
        bpy.context.view_layer.update(); pts=[o.matrix_world@Vector(cc) for o in objs for cc in o.bound_box]
        mn=Vector([min(p[i] for p in pts) for i in range(3)]); mx=Vector([max(p[i] for p in pts) for i in range(3)]); c=(mn+mx)/2; d=max(mx-mn)
    for o in objs:
        for m in o.material_slots:
            mt=m.material
            if mt and mt.use_nodes:
                b=mt.node_tree.nodes.get("Principled BSDF")
    cam=bl.rig_scene(res=128,ortho=d*1.25,el=20,yaw=25 if "cloak" not in a else 200,target=tuple(c))
    sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version>=(4,2) else 'BLENDER_EEVEE'; sc.eevee.taa_render_samples=8
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
