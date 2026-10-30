extends SceneTree
## Beth: Stage 3 renders: 3 sea-cave interiors (local cells, offset apart) + Sunken Ward underwater. Runtime glTF, Mobile. args: out_dir
## Project layout expected: res://m3 (stage3 meshes), res://sh3 (stage3 shaders), res://ships
var out := ""; var cam: Camera3D; var env: Environment; var sun: DirectionalLight3D; var vc: StandardMaterial3D
var man: Dictionary; var groups := {}; var hi := []; var lo := []; var stats := []
const OFF := {"echo_grotto": Vector3(0, 0, 0), "glasswyrm_cavern": Vector3(1000, 0, 0), "smugglers_throat": Vector3(2000, 0, 0)}
func _initialize() -> void: _run.call_deferred()
func fr(n): for i in n: await process_frame
func glb(p: String) -> Node3D:
	var d := GLTFDocument.new(); var s := GLTFState.new()
	if d.append_from_file(ProjectSettings.globalize_path(p), s) != OK: push_error(p); return Node3D.new()
	return d.generate_scene(s)
func mat_all(n: Node, m: Material, shadow := false) -> void:
	if n is MeshInstance3D:
		n.material_override = m; n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for c in n.get_children(): mat_all(c, m, shadow)
func smat(sh: String) -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = load("res://sh3/%s.gdshader" % sh); return m
func add(g: Node3D, name: String, m: Material, pos := Vector3.ZERO) -> void:
	var h := glb("res://m3/%s.glb" % name); mat_all(h, m); h.position = pos; g.add_child(h)
	if FileAccess.file_exists("res://m3/%s_lod1.glb" % name):
		var l := glb("res://m3/%s_lod1.glb" % name); mat_all(l, m); l.position = pos; l.visible = false; g.add_child(l); hi.append(h); lo.append(l)
func _v(a: Array) -> Vector3: return Vector3(a[0], a[1], a[2])
func show_only(k: String) -> void:
	for g in groups: groups[g].visible = (g == k)
func tier(low: bool) -> void:
	for i in hi.size(): hi[i].visible = not low; lo[i].visible = low
	env.glow_enabled = not low
func shot(name: String, pos: Vector3, look: Vector3, fov := 65.0) -> void:
	cam.fov = fov; cam.position = pos; cam.look_at(look, Vector3.UP)
	await fr(8); RenderingServer.force_draw(); await fr(2)
	root.get_texture().get_image().save_jpg(out + "/" + name + ".jpg", 0.88)
	var dc := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME); var pr := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	stats.append("%s dc=%d prims=%d" % [name, dc, pr]); print("SHOT ", stats[-1])
func cave_env() -> void:
	env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.0, 0.0, 0.01); env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.3, 0.36, 0.42); env.ambient_light_energy = 5.0; env.tonemap_exposure = 1.5; env.fog_enabled = true; env.fog_light_color = Color(0.02, 0.04, 0.05); env.fog_density = 0.006; sun.visible = false
func sea_env(e: Dictionary) -> void:
	env.background_mode = Environment.BG_COLOR; env.background_color = Color(e.fog_color[0], e.fog_color[1], e.fog_color[2]); env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(e.ambient[0], e.ambient[1], e.ambient[2]); env.ambient_light_energy = 0.9; env.tonemap_exposure = 1.0; env.fog_enabled = true
	env.fog_light_color = env.background_color; env.fog_density = float(e.fog_density) * 0.7; sun.visible = true
func _run() -> void:
	out = OS.get_cmdline_user_args()[0]; root.size = Vector2i(1280, 720); root.mesh_lod_threshold = 0.0
	man = JSON.parse_string(FileAccess.get_file_as_string("res://m3/stage3_manifest.json"))
	vc = StandardMaterial3D.new(); vc.vertex_color_use_as_albedo = true; vc.roughness = 0.88; vc.cull_mode = BaseMaterial3D.CULL_DISABLED
	var we := WorldEnvironment.new(); env = Environment.new(); env.tonemap_mode = Environment.TONE_MAPPER_ACES; env.glow_enabled = true; env.glow_intensity = 0.9; env.glow_bloom = 0.15; we.environment = env; root.add_child(we)
	sun = DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-62, 30, 0); sun.light_color = Color(0.7, 0.95, 0.9); sun.light_energy = 0.8; root.add_child(sun)
	cam = Camera3D.new(); cam.far = 600; root.add_child(cam); cam.current = true
	var LC := {"echo_grotto": Color(0.45, 0.85, 1.0), "glasswyrm_cavern": Color(0.5, 1.0, 0.8), "smugglers_throat": Color(1.0, 0.62, 0.3)}
	for k in OFF:
		var g := Node3D.new(); g.position = OFF[k]; root.add_child(g); groups[k] = g; var b: String = "cave_" + k
		add(g, b + "_shell", vc); add(g, b + "_props", vc); add(g, b + "_glow", smat("glow_vc"))
		var wm := smat("cave_water"); wm.set_shader_parameter("glow_tint", LC[k]); add(g, b + "_water", wm); add(g, b + "_portal", smat("cave_portal"))
		var C: Dictionary = man.caves[k]; var L: Array = C.get("lanterns", C.get("lights", []))
		for p in L.slice(0, 6):
			var o := OmniLight3D.new(); o.position = _v(p) + Vector3(0, 4.0 if k != "smugglers_throat" else 0.3, 0); o.light_color = LC[k]; o.light_energy = 14.0; o.omni_range = 50; o.omni_attenuation = 0.6; o.shadow_enabled = false; g.add_child(o)
		var sk := glb("res://ships/ship_boat_sail.glb"); mat_all(sk, vc); var sp: Array = C.skiff_path; sk.position = _v(sp[3]); sk.scale = Vector3.ONE * 0.6
		sk.look_at_from_position(sk.position, _v(sp[4]), Vector3.UP); g.add_child(sk)
	var sw := Node3D.new(); root.add_child(sw); groups["sw"] = sw
	for n in ["sw_seabed", "sw_buildings", "sw_landmarks", "sw_rubble"]: add(sw, n, smat("seabed_caustics"))
	add(sw, "sw_kelp", smat("kelp_sway")); add(sw, "sw_light_shafts", smat("light_shaft")); add(sw, "sw_surface_under", smat("surface_under"))
	for t in [false, true]:
		tier(t); var T := "Low" if t else "High"; cave_env()
		for k in OFF:
			show_only(k); var sp: Array = man.caves[k].skiff_path; var o: Vector3 = OFF[k]; var n: int = sp.size()
			await shot("I_%s_1entrance_%s" % [k, T], o + _v(sp[1]) + Vector3(0, 4, 6), o + _v(sp[4]) + Vector3(0, 2, 0))
			await shot("I_%s_2mid_%s" % [k, T], o + _v(sp[n / 2 - 2]) + Vector3(0, 3.5, 0), o + _v(sp[n / 2 + 1]) + Vector3(0, 3, 0))
			await shot("I_%s_3end_%s" % [k, T], o + _v(sp[n - 4]) + Vector3(0, 6, 0), o + _v(sp[n - 1]) + Vector3(0, 2, -10))
			await shot("I_%s_4lookback_%s" % [k, T], o + _v(sp[n / 2]) + Vector3(0, 4, 0), o + _v(sp[1]) + Vector3(0, 3, 0))
		var S: Dictionary = man.sunken_ward; sea_env(S.env); show_only("sw"); var d: Vector3 = _v(S.dome)
		await shot("U_1dive_down_%s" % T, _v(S.dive_start) + Vector3(0, -4, 0), d + Vector3(0, 0, 0))
		await shot("U_2street_%s" % T, Vector3(-1395, -26.0, 450), Vector3(-1300, -25.0, 450))
		await shot("U_3dome_%s" % T, d + Vector3(-28, -24 + 30 - 22, -30), d + Vector3(0, 10, 0))
		await shot("U_4kelp_shafts_%s" % T, Vector3(-1240, -20, 450), Vector3(-1280, -14, 400))
		await shot("U_5inside_dome_%s" % T, d + Vector3(0, -26 + 30, 6), d + Vector3(0, 18, -2), 75)
		await shot("U_6look_up_%s" % T, Vector3(-1320, -24, 360), Vector3(-1310, 0, 370), 70)
	FileAccess.open(out + "/stats.txt", FileAccess.WRITE).store_string("\n".join(stats)); quit()
