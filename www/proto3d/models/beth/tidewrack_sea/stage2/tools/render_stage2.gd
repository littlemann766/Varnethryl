extends SceneTree
## Beth: Stage 2 (Saltglass Coast) renders. Runtime glTF load (no import), Mobile renderer. args after --: out_dir
var out := ""; var cam: Camera3D; var sun: DirectionalLight3D; var env: Environment
var water_hi: MeshInstance3D; var water_lo: MeshInstance3D; var vc: StandardMaterial3D
var hi_nodes := []; var lo_nodes := []; var man: Dictionary; var stats := []
func _initialize() -> void: _run.call_deferred()
func fr(n): for i in n: await process_frame
func glb(p: String) -> Node3D:
	var d := GLTFDocument.new(); var s := GLTFState.new(); var e := d.append_from_file(ProjectSettings.globalize_path(p), s)
	if e != OK: push_error(p); return Node3D.new()
	return d.generate_scene(s)
func vcize(n: Node, shadow := true) -> void:
	if n is MeshInstance3D:
		n.material_override = vc; n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for c in n.get_children(): vcize(c, shadow)
func noshadow(n: Node) -> void:
	if n is GeometryInstance3D: n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for c in n.get_children(): noshadow(c)
func prop(name: String, pos := Vector3.ZERO, rot := 0.0, shadow := true) -> void:
	var h := glb("res://%s.glb" % name); vcize(h, shadow); h.position = pos; h.rotation.y = rot; root.add_child(h); hi_nodes.append(h)
	if FileAccess.file_exists("res://%s_lod1.glb" % name):
		var l := glb("res://%s_lod1.glb" % name); vcize(l, false); l.position = pos; l.rotation.y = rot; root.add_child(l); l.visible = false; lo_nodes.append(l)
	else: lo_nodes.append(null)
func ship(kind: String, tier: int, pos: Vector3, yaw: float) -> Node3D:
	var n := Node3D.new(); n.position = pos; n.rotation.y = yaw; root.add_child(n)
	var base := "ship_tidewrack_sailing_ship_lod1" if kind == "galleon" else "ship_boat_sail"
	var h := glb("res://ships/%s.glb" % base); noshadow(h); n.add_child(h)
	if tier > 0:
		var u := glb("res://s1/upg_%s_t%d.glb" % [kind, tier]); vcize(u, false); n.add_child(u)
	return n
func set_tier(low: bool) -> void:
	for i in hi_nodes.size():
		if lo_nodes[i] != null: hi_nodes[i].visible = not low; lo_nodes[i].visible = low
	water_hi.visible = not low; water_lo.visible = low; sun.shadow_enabled = not low; env.glow_enabled = not low
func shot(name: String, pos: Vector3, look: Vector3, fov := 60.0) -> void:
	cam.fov = fov; cam.position = pos; cam.look_at(look, Vector3.UP)
	water_hi.position = Vector3(pos.x, 0, pos.z).snapped(Vector3(8, 1, 8)); water_lo.position = water_hi.position
	await fr(8); RenderingServer.force_draw(); await fr(2)
	var img := root.get_texture().get_image(); img.save_jpg(out + "/" + name + ".jpg", 0.9)
	var dc := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME); var pr := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	stats.append("%s dc=%d prims=%d" % [name, dc, pr]); print("SHOT ", stats[-1])
func _v(a: Array) -> Vector3: return Vector3(a[0], a[1], a[2])
func _mat_all(n: Node, m: Material) -> void:
	if n is MeshInstance3D:
		n.material_override = m; n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for c in n.get_children(): _mat_all(c, m)
func _run() -> void:
	out = OS.get_cmdline_user_args()[0]; root.size = Vector2i(1280, 720); root.mesh_lod_threshold = 0.0
	man = JSON.parse_string(FileAccess.get_file_as_string("res://meshes/stage2_manifest.json")); var P: Dictionary = man.props
	vc = StandardMaterial3D.new(); vc.vertex_color_use_as_albedo = true; vc.roughness = 0.9
	var we := WorldEnvironment.new(); env = Environment.new(); var sky := Sky.new(); var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.3, 0.48, 0.72); sm.sky_horizon_color = Color(0.74, 0.8, 0.86); sm.ground_horizon_color = Color(0.74, 0.8, 0.86); sm.ground_bottom_color = Color(0.5, 0.62, 0.72); sky.sky_material = sm
	env.background_mode = Environment.BG_SKY; env.sky = sky; env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.fog_enabled = true; env.fog_light_color = Color(0.74, 0.8, 0.86); env.fog_density = 0.0005; env.glow_enabled = true; we.environment = env; root.add_child(we)
	sun = DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-30, 60, 0); sun.light_color = Color(1, 0.92, 0.8); sun.shadow_enabled = true; sun.directional_shadow_max_distance = 60; root.add_child(sun)
	var tex := ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://shaders/coast_shore_dist.png")))
	var rect := Vector4(-3000, -1500, 1800, 3200)
	var whi := ShaderMaterial.new(); whi.shader = load("res://shaders/ocean_water.gdshader"); whi.set_shader_parameter("shore_dist", tex); whi.set_shader_parameter("shore_rect", rect); whi.set_shader_parameter("wind_dir", Vector2(1.0, 0.1))
	var wlo := ShaderMaterial.new(); wlo.shader = load("res://shaders/ocean_water_low.gdshader"); wlo.set_shader_parameter("shore_dist", tex); wlo.set_shader_parameter("shore_rect", rect)
	water_hi = MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(1600, 1600); pm.subdivide_width = 200; pm.subdivide_depth = 200; water_hi.mesh = pm; water_hi.material_override = whi; water_hi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(water_hi)
	water_lo = MeshInstance3D.new(); var pl := PlaneMesh.new(); pl.size = Vector2(1600, 1600); pl.subdivide_width = 32; pl.subdivide_depth = 32; water_lo.mesh = pl; water_lo.material_override = wlo; water_lo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(water_lo)
	cam = Camera3D.new(); cam.far = 3000; root.add_child(cam); cam.current = true
	for t in man.tiles.high: prop("meshes/" + t[0])
	for n in ["coast_offshore_rocks", "coast_saltglass_landing", "coast_echo_grotto", "coast_glasswyrm_cavern", "coast_smugglers_throat", "coast_sunken_ward_surface", "coast_saltglass_crystals", "coast_beach_dressing"]: prop("meshes/" + n)
	prop("s1/arch_islands"); prop("s1/arch_shore_rocks")   # Stage 1 next door: the seam
	# storm border v2: soft layered fog + storm sky + choppy dark sea (the old slab wall is gone; the blocker is coast_storm_col.glb, invisible)
	var storm := Node3D.new(); root.add_child(storm); var fog := Node3D.new(); root.add_child(fog)
	for pair in [["coast_storm_sea", "storm_sea"], ["coast_storm_sky", "storm_sky"]]:
		var n := glb("res://meshes/%s.glb" % pair[0]); var m := ShaderMaterial.new(); m.shader = load("res://shaders/%s.gdshader" % pair[1]); _mat_all(n, m); storm.add_child(n)
	var fl := glb("res://meshes/coast_fog_layers.glb"); var flm := ShaderMaterial.new(); flm.shader = load("res://shaders/fog_layers.gdshader"); _mat_all(fl, flm); fog.add_child(fl)
	var la: Dictionary = P.saltglass_landing; var an := _v(la.anchor); var lp := _v(la.pos)
	var gal := ship("galleon", 2, an, float(la.yaw) + PI / 2)
	var eg: Dictionary = P.coast_echo_grotto; var ep := _v(eg.pos); var ec := _v(eg.cam)
	ship("skiff", 1, ep.lerp(Vector3(ec.x, 0, ec.z), 0.45), float(eg.yaw) + PI)
	var swd: Dictionary = P.sunken_ward; var db := _v(swd.dive_buoy)
	prop("s1/buoy_dive", db); prop("s1/buoy_dive", db + Vector3(30, 0, 0)); prop("s1/buoy_dive", db + Vector3(-30, 0, 0)); prop("s1/buoy_dive", db + Vector3(0, 0, 30)); prop("s1/buoy_dive", db + Vector3(0, 0, -30))
	prop("s1/buoy_skiff", ep.lerp(Vector3(ec.x, 0, ec.z), 0.8)); prop("s1/buoy_route", an + Vector3(60, 0, 0))
	var sk2 := ship("skiff", 3, db + Vector3(22, 0, 18), 0.6)
	await fr(4)
	for low in [false, true]:
		set_tier(low); var sfx := "_Low" if low else "_High"
		env.fog_enabled = false; water_hi.scale = Vector3(3, 1, 3); water_lo.scale = Vector3(3, 1, 3)
		await shot("C0_coast_overview" + sfx, Vector3(-1500, 1100, 1350), Vector3(-2150, 0, 100), 62)
		env.fog_enabled = true; water_hi.scale = Vector3.ONE; water_lo.scale = Vector3.ONE
		await shot("C1_saltglass_landing" + sfx, an + (an - lp).normalized() * 60 + Vector3(0, 22, 0) + Vector3((an - lp).z, 0, -(an - lp).x).normalized() * 50, lp + Vector3(0, 12, 0), 60)
		if low: continue
		await shot("C2_cliff_coast_sailing" + sfx, an + Vector3(70, 26, 120), lp.lerp(an, 0.5) + Vector3(0, 8, 0), 62)
		await shot("C3_echo_grotto" + sfx, ec, ep + Vector3(0, 6, 0), 58)
		var gw: Dictionary = P.coast_glasswyrm_cavern; await shot("C4_glasswyrm_cavern" + sfx, _v(gw.cam), _v(gw.pos) + Vector3(0, 8, 0), 58)
		var st: Dictionary = P.coast_smugglers_throat; await shot("C5_smugglers_throat" + sfx, _v(st.cam), _v(st.pos) + Vector3(0, 7, 0), 58)
		await shot("C6_sunken_ward_dive" + sfx, _v(swd.cam), db + Vector3(0, 0, 60), 60)
		var bw: Dictionary = P.beached_wreck; var bwp := _v(bw.pos); await shot("C7_beach_cove_wreck" + sfx, bwp + Vector3(90, 22, 40), bwp, 58)
		storm.visible = false; fog.visible = false
		await shot("C8_seam_to_archipelago" + sfx, Vector3(-1180, 55, 640), Vector3(-560, 5, 420), 60)
		storm.visible = true; fog.visible = true
		await shot("C9_storm_wall_border" + sfx, Vector3(-1400, 25, 1350), Vector3(-1200, 50, 1700), 65)
		await shot("C9b_storm_fog_sailing_height" + sfx, Vector3(-1560, 9, 1430), Vector3(-1520, 22, 1800), 62)
		await shot("C9c_storm_fog_distance" + sfx, Vector3(-1900, 70, 600), Vector3(-1900, 40, 1700), 60)
		await shot("C9d_storm_fog_inside_bank" + sfx, Vector3(-1750, 8, 1600), Vector3(-1750, 15, 1800), 62)
	var f := FileAccess.open(out + "/drawcalls.txt", FileAccess.WRITE); f.store_string("\n".join(stats)); f.close(); quit()
