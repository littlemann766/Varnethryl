extends SceneTree
## Beth: Stage 4 (region C, the Straits) renders. Runtime glTF load, Mobile renderer. args after --: out_dir. Project: res://m4 res://shaders res://s1 res://ships
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
var groups := {}; var cur: Node3D; var wmat_hi := {}; var wmat_lo := {}; var fogm := {}
func gprop(g: Node3D, name: String, pos := Vector3.ZERO, rot := 0.0, shadow := true, mat: Material = null, scl := 1.0) -> void:
	var h := glb("res://m4/%s.glb" % name); if mat: _mat_all(h, mat)
	else: vcize(h, shadow)
	h.position = pos; h.rotation.y = rot; h.scale = Vector3.ONE * scl; g.add_child(h); hi_nodes.append(h)
	if FileAccess.file_exists("res://m4/%s_lod1.glb" % name):
		var l := glb("res://m4/%s_lod1.glb" % name); if mat: _mat_all(l, mat)
		else: vcize(l, false)
		l.position = pos; l.rotation.y = rot; l.scale = h.scale; l.visible = false; g.add_child(l); lo_nodes.append(l)
	else: lo_nodes.append(null)
func smat(p: String) -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = load("res://shaders/%s.gdshader" % p); return m
func col3(a: Array) -> Color: return Color(a[0], a[1], a[2])
func region(k: String) -> void:
	for g in groups: groups[g].visible = (g == k)
	water_hi.material_override = wmat_hi[k]; water_lo.material_override = wmat_lo[k]
	var sm: ProceduralSkyMaterial = env.sky.sky_material
	if k == "frost":
		sm.sky_top_color = Color(0.42, 0.56, 0.74); sm.sky_horizon_color = Color(0.82, 0.87, 0.92); sm.ground_horizon_color = sm.sky_horizon_color
		env.fog_light_color = Color(0.82, 0.87, 0.92); env.fog_density = 0.0007; sun.rotation_degrees = Vector3(-18, 140, 0); sun.light_color = Color(1.0, 0.92, 0.86); env.ambient_light_energy = 1.0
	else:
		sm.sky_top_color = Color(0.22, 0.22, 0.25); sm.sky_horizon_color = Color(0.36, 0.33, 0.32); sm.ground_horizon_color = sm.sky_horizon_color
		env.fog_light_color = Color(0.30, 0.28, 0.28); env.fog_density = 0.00035; sun.rotation_degrees = Vector3(-30, 70, 0); sun.light_color = Color(1.0, 0.86, 0.74); env.ambient_light_energy = 1.1
func _run() -> void:
	out = OS.get_cmdline_user_args()[0]; root.size = Vector2i(1280, 720); root.mesh_lod_threshold = 0.0
	man = JSON.parse_string(FileAccess.get_file_as_string("res://m4/stage4_manifest.json")); var P: Dictionary = man.props
	vc = StandardMaterial3D.new(); vc.vertex_color_use_as_albedo = true; vc.roughness = 0.9; vc.metallic_specular = 0.15   # low spec: dark basalt otherwise mirrors the hazy sky (reads beige)
	var we := WorldEnvironment.new(); env = Environment.new(); var sky := Sky.new(); var sm := ProceduralSkyMaterial.new(); sky.sky_material = sm
	env.background_mode = Environment.BG_SKY; env.sky = sky; env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.fog_enabled = true; env.glow_enabled = true; we.environment = env; root.add_child(we)
	sun = DirectionalLight3D.new(); sun.shadow_enabled = true; sun.directional_shadow_max_distance = 60; root.add_child(sun)
	for k in ["frost", "ash"]:
		var R: Dictionary = man.regions[k]; var rc: Array = R.rect; var W: Dictionary = R.water
		var tex := ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://shaders/%s_shore_dist.png" % k)))
		var rect := Vector4(rc[0], rc[1], float(rc[2]) - float(rc[0]), float(rc[3]) - float(rc[1]))
		var wh := smat("ocean_water"); wh.set_shader_parameter("shore_dist", tex); wh.set_shader_parameter("shore_rect", rect); wh.set_shader_parameter("ice", W.ice)
		wh.set_shader_parameter("deep", col3(W.deep)); wh.set_shader_parameter("shallow", col3(W.shallow)); wh.set_shader_parameter("wind_dir", Vector2(0.1, 1.0) if k == "frost" else Vector2(0.0, -1.0)); wmat_hi[k] = wh
		var wl := smat("ocean_water_low" if k == "frost" else "ocean_water_low_straits"); wl.set_shader_parameter("shore_dist", tex); wl.set_shader_parameter("shore_rect", rect); wl.set_shader_parameter("deep", col3(W.deep)); wl.set_shader_parameter("shallow", col3(W.shallow)); if k == "ash": wl.set_shader_parameter("deep", Color(0.05, 0.13, 0.15)); wl.set_shader_parameter("shallow", Color(0.12, 0.32, 0.32)); wl.set_shader_parameter("sheen", Color(0.12, 0.24, 0.27))   # Low has no wave lighting, so lift it toward the High teal
		wmat_lo[k] = wl
		var g := Node3D.new(); root.add_child(g); groups[k] = g
		for t in man.tiles[k].high: gprop(g, t[0])
		var fm := smat("fog_layers"); fm.set_shader_parameter("fog_col", col3(man.fog[k].fog_col)); fm.set_shader_parameter("fog_dark", col3(man.fog[k].fog_dark)); fogm[k] = fm
		var fl := glb("res://m4/%s_fog_layers.glb" % k); _mat_all(fl, fm); g.add_child(fl)
		var ss := glb("res://m4/%s_storm_sky.glb" % k); _mat_all(ss, smat("storm_sky")); g.add_child(ss)
		var se := glb("res://m4/%s_storm_sea.glb" % k); _mat_all(se, smat("storm_sea")); g.add_child(se)
	var G: Node3D = groups.frost
	for n in ["frost_ice_floes", "frost_icicles", "frost_harbour", "frost_hidden_spots"]: gprop(G, n)
	gprop(G, "frost_glow", Vector3.ZERO, 0.0, false, smat("glow_vc"))
	for b in man.icebergs: gprop(G, b.mesh, _v(b.pos), float(b.yaw), true, null, float(b.scale))
	var A: Node3D = groups.ash
	for n in ["ash_offshore_rocks", "ash_vents", "ash_harbour", "ash_hidden_spots"]: gprop(A, n)
	gprop(A, "ash_glow", Vector3.ZERO, 0.0, false, smat("glow_vc")); gprop(A, "ash_lava_seams", Vector3.ZERO, 0.0, false, smat("lava_seam")); gprop(A, "ash_steam", Vector3.ZERO, 0.0, false, smat("steam_plume"))
	water_hi = MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(1600, 1600); pm.subdivide_width = 200; pm.subdivide_depth = 200; water_hi.mesh = pm; water_hi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(water_hi)
	water_lo = MeshInstance3D.new(); var pl := PlaneMesh.new(); pl.size = Vector2(1600, 1600); pl.subdivide_width = 32; pl.subdivide_depth = 32; water_lo.mesh = pl; water_lo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(water_lo)
	cam = Camera3D.new(); cam.far = 4000; root.add_child(cam); cam.current = true
	var fd: Dictionary = P.frostreach_ice_dock; var vh: Dictionary = P.vent_harbour
	ship("galleon", 2, _v(fd.anchor), float(fd.yaw) + PI / 2).reparent(G); ship("galleon", 3, _v(vh.anchor), float(vh.yaw) + PI / 2).reparent(A)
	var mw := _v(P.rimefang_maw.pos); var mc := _v(P.rimefang_maw.cam); ship("skiff", 1, mw.lerp(Vector3(mc.x, 0, mc.z), 0.55), 0.0).reparent(G)
	var CH: Dictionary = man.channels; var rn: Array = CH.rimefang_narrows.path; var cg: Array = CH.cinder_gate.path
	var nar := func(p: Array, i: int) -> Vector3: return Vector3(p[i][0], 0, p[i][1])
	await fr(4)
	for low in [false, true]:
		set_tier(low); var sfx := "_Low" if low else "_High"
		region("frost")
		env.fog_enabled = false; water_hi.scale = Vector3(3, 1, 3); water_lo.scale = Vector3(3, 1, 3)
		await shot("F0_frost_overview" + sfx, Vector3(-450, 900, -900), Vector3(-450, 0, -2250), 62)
		env.fog_enabled = true; water_hi.scale = Vector3.ONE; water_lo.scale = Vector3.ONE
		await shot("F1_frostreach_ice_dock" + sfx, _v(fd.cam), _v(fd.pos) + Vector3(0, 6, 0), 60)
		var i0 := int(rn.size() * 0.42); await shot("F2_rimefang_narrows" + sfx, nar.call(rn, i0) + Vector3(0, 9, 0), nar.call(rn, i0 + 8) + Vector3(0, 8, 0), 64)
		if not low:
			var b0: Dictionary = man.icebergs[0]; await shot("F3_icebergs_floes" + sfx, _v(b0.pos) + Vector3(-110, 14, 90), _v(b0.pos) + Vector3(0, 10, 0), 60)
			await shot("F4_frozen_cliffs" + sfx, nar.call(rn, 12) + Vector3(0, 6, 0), nar.call(rn, 20) + Vector3(0, 14, 0), 64)
			await shot("F5_rimefang_maw" + sfx, _v(P.rimefang_maw.cam), _v(P.rimefang_maw.pos) + Vector3(0, 6, 0), 58)
			await shot("F6_frozen_wreck" + sfx, _v(P.frozen_wreck.cam), _v(P.frozen_wreck.pos) + Vector3(0, 4, 0), 58)
			await shot("F7_aurora_arch" + sfx, _v(P.aurora_arch.cam), _v(P.aurora_arch.pos) + Vector3(0, 20, 0), 60)
			await shot("F8_frost_fog_border" + sfx, Vector3(1150, 12, -1750), Vector3(1500, 30, -1700), 64)
		region("ash")
		env.fog_enabled = false; water_hi.scale = Vector3(3, 1, 3); water_lo.scale = Vector3(3, 1, 3)
		await shot("A0_ash_overview" + sfx, Vector3(-150, 800, 1300), Vector3(-150, 0, 2300), 62)
		env.fog_enabled = true; water_hi.scale = Vector3.ONE; water_lo.scale = Vector3.ONE
		await shot("A1_vent_harbour" + sfx, _v(vh.cam), _v(vh.pos) + Vector3(0, 6, 0), 60)
		await shot("A2_cinder_gate" + sfx, nar.call(cg, 2) + Vector3(0, 9, 0), nar.call(cg, 14) + Vector3(0, 6, 0), 64)
		if not low:
			await shot("A3_cinderreach_volcano" + sfx, Vector3(60, 40, 2080), Vector3(300, 75, 2250), 64)
			await shot("A4_lava_shore" + sfx, nar.call(cg, 20) + Vector3(15, 7, 0), nar.call(cg, 20) + Vector3(140, 2, 30), 64)
			await shot("A5_obsidian_arch" + sfx, _v(P.obsidian_arch.cam), _v(P.obsidian_arch.pos) + Vector3(0, 10, 0), 58)
			await shot("A6_ember_wreck" + sfx, _v(P.ember_wreck.cam), _v(P.ember_wreck.pos) + Vector3(0, 3, 0), 58)
			await shot("A7_hot_spring_grotto" + sfx, _v(P.hot_spring_grotto.cam), _v(P.hot_spring_grotto.pos) + Vector3(0, 2, 0), 58)
			await shot("A8_ash_fog_border" + sfx, Vector3(-200, 12, 2800), Vector3(-200, 30, 3000), 64)
	var f := FileAccess.open(out + "/drawcalls.txt", FileAccess.WRITE); f.store_string("\n".join(stats)); f.close(); quit()
