extends SceneTree
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var a := OS.get_cmdline_user_args(); get_root().size = Vector2i(1280, 720)
	var M: Node3D = load(a[0]).new()
	M.noise.seed = 7; M.noise.frequency = 0.0035; M.noise.fractal_octaves = 4
	M._terrain(); M._roads(); M._walls_and_gate()
	M._hi_terrain()
	var top := Node3D.new(); get_root().add_child(top)
	for c in M.get_children(): M.remove_child(c); top.add_child(c)
	var we := WorldEnvironment.new(); var env := Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.7, 0.78, 0.88)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.7, 0.7, 0.72); env.ambient_light_energy = 0.6
	load("res://tp/fog_v2.gd").apply(env, Color(0.75, 0.82, 0.9)); we.environment = env; get_root().add_child(we)
	var sun := DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-40, 40, 0); get_root().add_child(sun)
	var cam := Camera3D.new(); get_root().add_child(cam); cam.far = 3000; cam.current = true; cam.fov = 60
	var V := [["lake", Vector3(150, 70, -110), Vector3(265, 0, -210)], ["coast", Vector3(-380, 40, 330), Vector3(-450, 0, 430)]]
	for v in V:
		cam.look_at_from_position(v[1], v[2], Vector3.UP)
		for i in 8: await process_frame
		get_root().get_texture().get_image().save_jpg("/tmp/rp/s8/c8b_%s_%s.jpg" % [v[0], a[1]], 0.88)
	quit()
