import bpy,sys,math
from mathutils import Vector
f,outp=sys.argv[-2:]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=8; sc.render.resolution_x=260; sc.render.resolution_y=260; sc.cycles.use_denoising=False
bpy.ops.import_scene.gltf(filepath=f)
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.7,0.7,0.75,1); w.node_tree.nodes['Background'].inputs[1].default_value=1.5
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=50
a=bpy.data.actions['run']; arm.animation_data_create(); arm.animation_data.action=a
if getattr(a,'slots',None): arm.animation_data.action_slot=a.slots[0]
r=a.frame_range
info=[]
for fr in (0.3,0.7):
    sc.frame_set(int(r[0]+(r[1]-r[0])*fr))
    for side in 'LR':
        pb=arm.pose.bones[f'hand_{side}']; M=arm.matrix_world@pb.matrix
        p=M.translation
        tw=[]
        for bn in ('upperArm','foreArm','hand'):
            q=arm.pose.bones[f'{bn}_{side}'].matrix_basis.to_quaternion()
            sw,t=q.to_swing_twist('Y'); tw.append(round(math.degrees(t)))
        info.append((fr,side,tw))
        cam.location=p+Vector((0.25 if side=='L' else -0.25,-0.55,0)) ; cam.rotation_euler=(p-cam.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=f'{outp}_{fr}_{side}.png'; bpy.ops.render.render(write_still=True)
print('PALM',info)
