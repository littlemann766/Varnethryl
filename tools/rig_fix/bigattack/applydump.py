# Re-key dumped deform matrices on the default-heuristic import (so node rest frames match the original GLB), export clips only.
import bpy, sys, json
from mathutils import Matrix
src, dump, dst = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]; P = arm.pose.bones
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
arm.animation_data_create(); bpy.context.scene.render.fps = 30; bpy.context.scene.render.fps_base = 1.0
DUMP = json.load(open(dump)); order = []
def walk(b):
    order.append(b.name); [walk(c) for c in b.children]
for b in arm.data.bones:
    if b.parent is None: walk(b)
for nm, frames in DUMP.items():
    act = bpy.data.actions.new(nm); act.use_fake_user = True; arm.animation_data.action = act
    for fi, Fm in enumerate(frames):
        for bn in order:
            pb = P[bn]
            if bn in Fm: pb.matrix = Matrix(Fm[bn]) @ pb.bone.matrix_local
            bpy.context.view_layer.update()
        for bn in order:
            pb = P[bn]; pb.keyframe_insert('location', frame=fi+1); pb.keyframe_insert('rotation_quaternion', frame=fi+1); pb.keyframe_insert('scale', frame=fi+1)
    for pb in P: pb.matrix_basis.identity()
arm.animation_data.action = None
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_animation_mode='ACTIONS', export_force_sampling=True, export_skins=True, export_def_bones=False, export_optimize_animation_size=False)
print('APPLY ok', list(DUMP))
