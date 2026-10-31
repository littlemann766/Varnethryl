class_name CapeClamp
extends SkeletonModifier3D
## Runs after the SpringBoneSimulator3D: limits how far each cape bone may swing away from its rest pose
## (lower bones less), so the cape trails while running but never flares out like a sail.
var bones := PackedInt32Array()
var max_deg := PackedFloat32Array()
## 0..1: at rest the idle clip leans the chest, which tilts the rigid cape out at the hem. With level=1 the cape
## root keeps its bind-pose orientation in skeleton space (hangs plumb down the back) while still riding the collar.
var level := 0.0

func _process_modification_with_delta(_delta: float) -> void:
	var sk := get_skeleton()
	if sk == null: return
	if level > 0.001 and bones.size() > 0:
		var r := bones[0]; var p := sk.get_bone_parent(r)
		if p >= 0:
			var g_rest := sk.get_bone_global_rest(r).basis.get_rotation_quaternion()
			var pq := sk.get_bone_global_pose(p).basis.get_rotation_quaternion()
			var want := pq.inverse() * g_rest
			sk.set_bone_pose_rotation(r, sk.get_bone_pose_rotation(r).slerp(want, level))
	for k in bones.size():
		var b := bones[k]
		var rest := sk.get_bone_rest(b).basis.get_rotation_quaternion()
		var q := sk.get_bone_pose_rotation(b)
		var d := rest.inverse() * q
		var ang := d.get_angle()
		var lim := deg_to_rad(max_deg[k])
		if ang > lim and ang > 0.0001:
			sk.set_bone_pose_rotation(b, rest * Quaternion(d.get_axis(), lim))
