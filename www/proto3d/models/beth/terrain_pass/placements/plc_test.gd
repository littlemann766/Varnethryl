extends SceneTree
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var a := OS.get_cmdline_user_args(); get_root().size = Vector2i(1280, 720)
	var M: Node3D = load("res://scripts/main_tp.gd").new()
	M.noise.seed = 7; M.noise.frequency = 0.0035; M.noise.fractal_octaves = 4
	M._terrain(); M._roads(); M._walls_and_gate()
	for d in M.DEFS: M._building(d)
	if a[0] == "1": print("PLC ", load("res://tp/beth_placements.gd").apply(M))
	var top := Node3D.new(); get_root().add_child(top)
	for c in M.get_children(): M.remove_child(c); top.add_child(c)
	var we := WorldEnvironment.new(); var env := Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.7, 0.78, 0.88)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.7, 0.7, 0.72); env.ambient_light_energy = 0.6
	load("res://tp/fog_v2.gd").apply(env, Color(0.75, 0.82, 0.9)); we.environment = env; top.add_child(we)
	var sun := DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-40, 40, 0); top.add_child(sun)
	var cam := Camera3D.new(); top.add_child(cam); cam.far = 3000; cam.current = true; cam.fov = 60
	var V := [["frost", Vector3(0, 40, -170), Vector3(0, 0, -400)], ["volcano", Vector3(200, 60, -220), Vector3(405, 20, -402)], ["hobcamp", Vector3(-260, 30, -120), Vector3(-320, 0, -180)]]
	for v in V:
		var f: Vector3 = v[1]; f.y += M.height(f.x, f.z); cam.look_at_from_position(f, v[2] + Vector3(0, M.height(v[2].x, v[2].z), 0), Vector3.UP)
		for i in 6: await process_frame
		get_root().get_texture().get_image().save_jpg("/tmp/rp/s7/plc2_%s_%s.jpg" % [v[0], a[0]], 0.88)
	quit()
