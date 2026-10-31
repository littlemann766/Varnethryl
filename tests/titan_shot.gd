extends SceneTree
## test 34: front/back shot of the world-boss voxel Titan GLB. -s tests/titan_shot.gd -- <res glb> <out prefix>
func _init() -> void:
	var a := OS.get_cmdline_user_args(); var root := Node3D.new(); get_root().add_child(root)
	var v: Node3D = load(a[0]).instantiate(); root.add_child(v)
	var ap: AnimationPlayer = v.find_children("*", "AnimationPlayer", true, false)[0] if v.find_children("*", "AnimationPlayer", true, false).size() > 0 else null
	if ap and ap.has_animation("wb_idle"): ap.play("wb_idle"); ap.seek(0.5, true)
	var env := WorldEnvironment.new(); var e := Environment.new(); e.background_mode = Environment.BG_COLOR; e.background_color = Color(0.12, 0.12, 0.14)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color = Color(0.6, 0.6, 0.65); e.ambient_light_energy = 0.8; env.environment = e; root.add_child(env)
	var sun := DirectionalLight3D.new(); root.add_child(sun); sun.rotation_degrees = Vector3(-40, 30, 0)
	var bb := AABB(); var first := true
	for mi: MeshInstance3D in v.find_children("*", "MeshInstance3D", true, false):
		var b: AABB = mi.global_transform * mi.get_aabb(); bb = b if first else bb.merge(b); first = false
	var c := bb.get_center(); var d := bb.size.length() * 1.35
	var cam := Camera3D.new(); root.add_child(cam); cam.fov = 45
	for side in [["front", 1.0], ["back", -1.0]]:
		cam.look_at_from_position(c + Vector3(0, bb.size.y * 0.05, d * side[1]), c, Vector3.UP); cam.current = true
		for i in 12: await process_frame
		get_root().get_texture().get_image().save_png(a[1] + "_" + side[0] + ".png")
	quit()
