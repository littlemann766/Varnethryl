class_name FlyPose
extends SkeletonModifier3D
## test 16 (boss: "my character should fly, not walk on the air"): procedural flight pose layered on the hero skeleton
## while owner/co-owner fly is on. Bone rotations are given about RIG-space axes (rig faces -Z) and converted to each
## bone's parent space, so it works on every humanoid rig (hips/spine/thigh/shin/upperArm/foreArm names).
## Lucian's authored fly_* clips (handoff/godot/heroes_fly/) replace this in a later build.
var rig: Node3D
var w := 0.0          # 0..1 overall flight weight (blends in/out)
var fwd := 0.0        # 0 hover .. 1 fast forward
var bank := 0.0       # -1..1 (turn direction)
var climb := 0.0      # -1 descend .. +1 ascend
var t := 0.0

func _process_modification() -> void:
	var sk := get_skeleton()
	if sk == null or rig == null or w < 0.001: return
	var to_sk := sk.global_basis.inverse() * rig.global_basis
	var X := (to_sk * Vector3.RIGHT).normalized(); var Z := (to_sk * Vector3.BACK).normalized()
	var bob := sin(t * 2.2)
	var f := fwd
	var legs := (0.25 + 0.55 * f + 0.25 * maxf(climb, 0.0) - 0.15 * maxf(-climb, 0.0)) # trail back with speed
	_rot(sk, "thigh_L", X, -w * (legs + 0.05 * bob)); _rot(sk, "thigh_R", X, -w * (legs * 0.9 - 0.05 * bob + 0.06))
	_rot(sk, "shin_L", X, -w * (0.35 - 0.2 * f)); _rot(sk, "shin_R", X, -w * (0.45 - 0.2 * f))   # relaxed knees
	var arms := 0.15 + 0.85 * f
	_rot(sk, "upperArm_L", X, -w * arms); _rot(sk, "upperArm_R", X, -w * arms)
	_rot(sk, "upperArm_L", Z, w * (0.25 - 0.15 * f)); _rot(sk, "upperArm_R", Z, -w * (0.25 - 0.15 * f))   # slightly out from the body
	_rot(sk, "foreArm_L", X, -w * 0.2); _rot(sk, "foreArm_R", X, -w * 0.2)
	_rot(sk, "spine", X, w * (0.12 * f))   # chest lifts / head up while the body is pitched forward

func _rot(sk: Skeleton3D, bn: String, axis_sk: Vector3, ang: float) -> void:
	var b := sk.find_bone(bn)
	if b < 0 or absf(ang) < 1e-4: return
	var p := sk.get_bone_parent(b)
	var pb := sk.get_bone_global_pose(p).basis.orthonormalized() if p >= 0 else Basis()
	var ax := (pb.inverse() * axis_sk).normalized()
	sk.set_bone_pose_rotation(b, Quaternion(ax, ang) * sk.get_bone_pose_rotation(b))
