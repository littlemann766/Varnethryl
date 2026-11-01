import bpy,sys,json,math
sys.path.insert(0,'/workspace/godot-art/loot3_tools'); import bl
P=json.load(open('/tmp/l3/www/proto3d/models/beth/loot/merchants/PLACEMENT_merchants.json'))
M="/workspace/vmain/tidewrack/stage4/meshes/"; L="/tmp/l3/www/proto3d/models/beth/"
for it in P['items']:
    if 'position_v0' not in it: continue
    bl.reset(); pre="frost" if "frost" in it['shop'] else "ash"
    for f in [M+pre+"_harbour.glb",M+pre+"_terrain_col.glb"]: bpy.ops.import_scene.gltf(filepath=f)
    for o in bpy.context.scene.objects:
        if "col" in o.name.lower() or "terrain" in o.name.lower():
            m=bpy.data.materials.new("t"); m.diffuse_color=(0.45,0.45,0.42,1); o.data.materials.clear(); o.data.materials.append(m)
    def put(f,pos,yaw,tag):
        bpy.ops.import_scene.gltf(filepath=f); ob=bpy.context.selected_objects[0]
        x,y,z=pos; ob.location=(x,-z,y if y is not None else 1.6); ob.rotation_euler=(0,0,yaw)
    put(L+it['file'],it['position'],it['yaw'],'new')
    put(L+it['npc']['file'],[it['position'][0]+it['npc']['local_offset'][0],it['position'][1],it['position'][2]+it['npc']['local_offset'][2]],it['yaw'],'npc')
    x,y,z=it['position']
    for k,(el,orth) in enumerate([(70,26),(25,14)]):
        cam=bl.rig_scene(res=640,ortho=orth,el=el,yaw=30,target=(x,-z,y)); sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE'; sc.eevee.taa_render_samples=6
        e=bpy.data.objects.new("mk",None); 
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15,depth=4,location=(it['position_v0'][0],-it['position_v0'][2],y+2)); mk=bpy.context.object; mm=bpy.data.materials.new("r"); mm.diffuse_color=(1,0.1,0.1,1); mk.data.materials.append(mm)
        sc.render.filepath=f"/tmp/l3w/stall_{it['shop']}_{k}.png"; bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam)
