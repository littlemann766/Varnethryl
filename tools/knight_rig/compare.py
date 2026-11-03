import bpy,sys,math,numpy as np
from mathutils import Vector
G=sys.argv[-2]; WHICH=sys.argv[-1]; OD='/tmp/kr/cmp'; import os; os.makedirs(OD,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
if WHICH=='orig':
    bpy.ops.import_scene.gltf(filepath='/workspace/uploads/ref_armor.glb')
    o=[x for x in bpy.data.objects if x.type=='MESH'][0]
    d=np.load('/tmp/kr/parts.npz'); INV=d['inv']; male=d['cen'][:,0]<5.0
    import bmesh; bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    mw=o.matrix_world.copy()
    keep=male[INV] if G=='male' else ~male[INV]
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not keep[v.index]],context='VERTS'); bm.to_mesh(o.data); bm.free()
else:
    bpy.ops.import_scene.gltf(filepath=f'/tmp/kr/{G}/knight_{G}.glb')
    for a in bpy.data.objects:
        if a.type=='ARMATURE':
            a.data.pose_position='REST'
            if a.animation_data: a.animation_data.action=None
    ms=[x for x in bpy.data.objects if x.type=='MESH']; o=max(ms,key=lambda x:len(x.data.vertices))
    for x in ms:
        if x is not o: bpy.data.objects.remove(x)
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get(); ev=o.evaluated_get(dg); m=ev.to_mesh()
V=np.array([o.matrix_world@v.co for v in m.vertices]); ev.to_mesh_clear()
lo,hi=V.min(0),V.max(0); c=(lo+hi)/2; h=hi[2]-lo[2]
sc.render.engine='BLENDER_EEVEE'; sc.eevee.taa_render_samples=32; sc.render.resolution_x=600; sc.render.resolution_y=800; sc.view_settings.view_transform='Standard'
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.57,0.6,1); w.node_tree.nodes['Background'].inputs[1].default_value=0.9
sun=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN')); sc.collection.objects.link(sun); sun.rotation_euler=(math.radians(50),0,math.radians(-30)); sun.data.energy=3.5
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.type='ORTHO'
for yaw,tag,zoom in ((20,'front',1.0),(200,'back',1.0),(15,'helm',0.28),(60,'shoulder',0.35)):
    t=Vector(c) if tag in('front','back') else Vector((c[0],c[1],lo[2]+h*(0.90 if tag=='helm' else 0.78)))
    cam.data.ortho_scale=h*1.08*zoom
    d_=h*3; cam.location=t+Vector((math.sin(math.radians(yaw))*d_,-math.cos(math.radians(yaw))*d_,h*0.12)); cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.clip_end=d_*3
    sc.render.filepath=f'{OD}/{G}_{WHICH}_{tag}.png'; bpy.ops.render.render(write_still=True)
print('BBOX',G,WHICH,np.round(lo,3),np.round(hi,3))
