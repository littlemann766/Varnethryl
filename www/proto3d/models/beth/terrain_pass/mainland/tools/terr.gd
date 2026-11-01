extends SceneTree
## terrain pass: build only main._terrain() from main.gd (before) or main_tp.gd (after) and shoot views. args: script out_prefix
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var a := OS.get_cmdline_user_args()
	get_root().size = Vector2i(1280, 720)
	var M: Node3D = load(a[0]).new()
	M.noise.seed = 7; M.noise.frequency = 0.0035; M.noise.fractal_octaves = 4
	M._terrain()
	var top := Node3D.new(); get_root().add_child(top)
	for c in M.get_children(): M.remove_child(c); top.add_child(c)
	var we := WorldEnvironment.new(); var env := Environment.new(); var sky := Sky.new(); var sm := ProceduralSkyMaterial.new(); sky.sky_material = sm
	sm.sky_top_color = Color(0.22, 0.45, 0.85); sm.sky_horizon_color = Color(0.75, 0.82, 0.9); sm.ground_horizon_color = sm.sky_horizon_color; sm.ground_bottom_color = Color(0.2, 0.22, 0.2)
	env.background_mode = Environment.BG_SKY; env.sky = sky; env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.ambient_light_color = Color(0.75, 0.68, 0.58); env.ambient_light_sky_contribution = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_ACES; env.tonemap_white = 6.0; env.adjustment_enabled = true; env.adjustment_contrast = 1.08; env.adjustment_saturation = 1.12
	env.glow_enabled = true; env.glow_intensity = 0.6; env.glow_bloom = 0.08; env.glow_hdr_threshold = 1.0
	var mode: String = a[2] if a.size() > 2 else "fog1"
	if mode == "fog2": load("res://tp/fog_v2.gd").apply(env, sm.sky_horizon_color)
	else:
		env.fog_enabled = true; env.fog_density = float(OS.get_environment("FOGD")) if OS.get_environment("FOGD") != "" else 0.0011; env.fog_aerial_perspective = 0.5; env.fog_sky_affect = 0.25; env.fog_light_color = sm.sky_horizon_color
	we.environment = env; top.add_child(we)
	var sun := DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-40, 40, 0); sun.light_energy = 1.1; top.add_child(sun)
	var cam := Camera3D.new(); top.add_child(cam); cam.far = 4000; cam.current = true
	var V := [["mountains_n", Vector3(0, 70, -700), Vector3(0, 140, -1000)], ["foothills_e", Vector3(560, 40, 60), Vector3(820, 70, 0)], ["ring_w", Vector3(-700, 80, 200), Vector3(-1000, 120, 300)], ["wide", Vector3(0, 160, 300), Vector3(0, 40, -500)]]
	for v in V:
		var f: Vector3 = v[1]; f.y += M.height(f.x, f.z); var t: Vector3 = v[2]
		cam.fov = 60; cam.look_at_from_position(f, t, Vector3.UP)
		for i in 6: await process_frame
		get_root().get_texture().get_image().save_jpg("%s_%s.jpg" % [a[1], v[0]], 0.88)
	quit()
