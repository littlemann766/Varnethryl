extends SceneTree
## fix 5 shot: camera-following water grid (+ optional far ring) over region A islands. args: out.jpg ring(0/1)
func glb(p: String) -> Node3D:
	var d := GLTFDocument.new(); var s := GLTFState.new()
	if d.append_from_file(p, s) != OK: return null
	return d.generate_scene(s)
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var a := OS.get_cmdline_user_args(); get_root().size = Vector2i(1280, 720); var top := Node3D.new(); get_root().add_child(top)
	var vc := StandardMaterial3D.new(); vc.vertex_color_use_as_albedo = true; vc.roughness = 0.9
	for f in ["arch_islands_lod1.glb", "arch_shore_rocks_lod1.glb", "arch_isl_gullhaven_lod1.glb", "arch_isl_lantern_rock_lod1.glb"]:
		var n := glb(ProjectSettings.globalize_path("res://tidewrack/stage1/meshes/" + f))
		if n: top.add_child(n); for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false): mi.material_override = vc
	var cams := [[Vector3(400, 500, 900), Vector3(0, 0, 0)], [Vector3(-300, 60, 500), Vector3(-900, 20, -200)]]
	var we := WorldEnvironment.new(); var env := Environment.new(); var sky := Sky.new(); var sm := ProceduralSkyMaterial.new(); sky.sky_material = sm
	sm.sky_top_color = Color(0.22, 0.45, 0.85); sm.sky_horizon_color = Color(0.75, 0.82, 0.9); sm.ground_horizon_color = sm.sky_horizon_color; sm.ground_bottom_color = Color(0.2, 0.22, 0.2)
	env.background_mode = Environment.BG_SKY; env.sky = sky; env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.tonemap_mode = Environment.TONE_MAPPER_ACES
	load("res://tp/fog_v2.gd").apply(env, sm.sky_horizon_color); we.environment = env; top.add_child(we)
	var sun := DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-40, 40, 0); top.add_child(sun)
	var water := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(1600, 1600); pm.subdivide_width = 120; pm.subdivide_depth = 120; water.mesh = pm
	var wm := ShaderMaterial.new(); wm.shader = load("res://tidewrack/stage1/shaders/ocean_water.gdshader"); wm.set_shader_parameter("shore_dist", load("res://tidewrack/stage1/shaders/arch_shore_dist.png")); water.material_override = wm; top.add_child(water)
	if a[1] == "1":
		var ring := glb(ProjectSettings.globalize_path("res://tp/ocean_far_ring.glb")); water.add_child(ring)
		var rm := ShaderMaterial.new(); rm.shader = load("res://tp/ocean_far.gdshader"); rm.set_shader_parameter("horizon", sm.sky_horizon_color.lerp(Color(0.62, 0.70, 0.80), 0.35))
		for mi: MeshInstance3D in ring.find_children("*", "MeshInstance3D", true, false): mi.material_override = rm
	var cam := Camera3D.new(); top.add_child(cam); cam.current = true; cam.far = 12000; cam.fov = 60
	var k := 0
	for c in cams:
		cam.look_at_from_position(c[0], c[1], Vector3.UP); water.global_position = Vector3(snappedf(c[0].x, 8.0), 0, snappedf(c[0].z, 8.0))
		for i in 6: await process_frame
		get_root().get_texture().get_image().save_jpg(a[0].replace(".jpg", "_%d.jpg" % k), 0.88); k += 1
	quit()
