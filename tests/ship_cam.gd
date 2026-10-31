extends Node
## test 29: (1) the boss's camera: Owner flying ~10 m up beside the sea galleon, looking across it; (2) orthographic side/bow
## of the galleon actually drawn at that range (LOD band), for measuring keel/deck/masts. -- --shipcam  (VOX_TAG)
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	var out := "/workspace/shots/voxel29/"; DirAccess.make_dir_recursive_absolute(out); var tag := OS.get_environment("VOX_TAG")
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0); m.party._set_companions([]); m.party.set_hero("owner")
	var s7: Node3D = m.get_node("Ship7_tidewrack_sailing_ship")
	var side: Vector3 = s7.global_basis.x.normalized(); var fwd: Vector3 = s7.global_basis.z.normalized()
	# which LOD mesh is visible at the boss's range
	var p: Vector3 = s7.global_position + side * 30.0 - fwd * 6.0
	m.hero.position = Vector3(p.x, 10.0, p.z); m.fly_alt = 10.0 - m.height(p.x, p.z)
	var to := s7.global_position - p; m.yaw = atan2(-to.x, -to.z) + 0.35; m.pitch = -0.12; m.cam_arm.spring_length = 4.0
	for i in 90:
		m.cheat["fly"] = true; m.flight = true; await get_tree().process_frame
	var cam_p := get_viewport().get_camera_3d().global_position
	for mi in s7.find_children("*", "MeshInstance3D", true, false):
		var d: float = cam_p.distance_to(s7.global_position)
		print("LODBAND %s begin=%.0f end=%.0f cam_dist=%.1f drawn=%s" % [mi.mesh.resource_path.get_file() if mi.mesh else mi.name, mi.visibility_range_begin, mi.visibility_range_end, d, d >= mi.visibility_range_begin and d < mi.visibility_range_end])
	get_viewport().get_texture().get_image().save_png(out + "boss_cam_%s.png" % tag); print("SHOT boss_cam")
	var cam := Camera3D.new(); cam.projection = Camera3D.PROJECTION_ORTHOGONAL; cam.size = 34.0; m.add_child(cam)
	var c := s7.global_position + Vector3(0, 5.5, 0)
	for v in [["ortho_side", side], ["ortho_bow", fwd]]:
		cam.look_at_from_position(c + v[1] * 60.0, c, Vector3.UP); cam.current = true
		await frames(15); get_viewport().get_texture().get_image().save_png(out + "%s_%s.png" % [v[0], tag]); print("SHOT ", v[0])
	get_tree().quit(0)
