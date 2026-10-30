extends SceneTree
## Beth: Stage 1 renders. Runtime glTF load (no import), Mobile renderer. args after --: out_dir
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
	var h := glb("res://meshes/%s.glb" % name); vcize(h, shadow); h.position = pos; h.rotation.y = rot; root.add_child(h); hi_nodes.append(h)
	if FileAccess.file_exists("res://meshes/%s_lod1.glb" % name):
		var l := glb("res://meshes/%s_lod1.glb" % name); vcize(l, false); l.position = pos; l.rotation.y = rot; root.add_child(l); l.visible = false; lo_nodes.append(l)
	else: lo_nodes.append(null)
func ship(kind: String, tier: int, pos: Vector3, yaw: float) -> Node3D:
	var n := Node3D.new(); n.position = pos; n.rotation.y = yaw; root.add_child(n)
	var base := "ship_tidewrack_sailing_ship_lod1" if kind == "galleon" else "ship_boat_sail"
	var h := glb("res://ships/%s.glb" % base); noshadow(h); n.add_child(h)
	if tier > 0:
		var u := glb("res://meshes/upg_%s_t%d.glb" % [kind, tier]); vcize(u, false); n.add_child(u)
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
	out = OS.get_cmdline_user_args()[0]; root.size = Vector2i(1280, 720); root.mesh_lod_threshold = 0.0  # we ship our own lod1; Godot auto-LOD made slivers on the island mesh
	man = JSON.parse_string(FileAccess.get_file_as_string("res://meshes/stage1_manifest.json"))
	vc = StandardMaterial3D.new(); vc.vertex_color_use_as_albedo = true; vc.roughness = 0.9
	var we := WorldEnvironment.new(); env = Environment.new(); var sky := Sky.new(); var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.28, 0.5, 0.8); sm.sky_horizon_color = Color(0.72, 0.82, 0.9); sm.ground_horizon_color = Color(0.72, 0.82, 0.9); sm.ground_bottom_color = Color(0.5, 0.62, 0.72); sky.sky_material = sm
	env.background_mode = Environment.BG_SKY; env.sky = sky; env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.fog_enabled = true; env.fog_light_color = Color(0.72, 0.82, 0.9); env.fog_density = 0.0005; env.glow_enabled = true; we.environment = env; root.add_child(we)
	sun = DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-38, -35, 0); sun.light_color = Color(1, 0.95, 0.85); sun.shadow_enabled = true; sun.directional_shadow_max_distance = 60; root.add_child(sun)
	var tex := ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://shaders/arch_shore_dist.png")))
	var whi := ShaderMaterial.new(); whi.shader = load("res://shaders/ocean_water.gdshader"); whi.set_shader_parameter("shore_dist", tex)
	var wlo := ShaderMaterial.new(); wlo.shader = load("res://shaders/ocean_water_low.gdshader"); wlo.set_shader_parameter("shore_dist", tex)
	water_hi = MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(1600, 1600); pm.subdivide_width = 200; pm.subdivide_depth = 200; water_hi.mesh = pm; water_hi.material_override = whi; water_hi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(water_hi)
	water_lo = MeshInstance3D.new(); var pl := PlaneMesh.new(); pl.size = Vector2(1600, 1600); pl.subdivide_width = 32; pl.subdivide_depth = 32; water_lo.mesh = pl; water_lo.material_override = wlo; water_lo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(water_lo)
	cam = Camera3D.new(); cam.far = 2500; root.add_child(cam); cam.current = true
	prop("arch_islands"); prop("arch_shore_rocks"); prop("arch_gullhaven_port"); prop("arch_lantern_rock"); prop("arch_wreck_reef"); prop("arch_saltwatch_keep"); prop("arch_coil_arena")
	var storm := glb("res://meshes/arch_storm_wall.glb"); var smat := ShaderMaterial.new(); smat.shader = load("res://shaders/storm_wall.gdshader"); _mat_all(storm, smat); root.add_child(storm)
	var fog := glb("res://meshes/arch_fog_bank.glb"); var fmat := ShaderMaterial.new(); fmat.shader = load("res://shaders/fog_bank.gdshader"); _mat_all(fog, fmat); root.add_child(fog)
	var coil := glb("res://meshes/brinecrown_coil_hero.glb"); vcize(coil); var ap: Array = man.props.coil_arena.pos; coil.position = Vector3(ap[0], 0, ap[2]); root.add_child(coil)
	var g: Array = man.props.gullhaven.pos; var gy: float = man.props.gullhaven.yaw; var sd := Vector3(sin(gy), 0, cos(gy)); var sx := Vector3(sd.z, 0, -sd.x)
	var an: Array = man.props.gullhaven.anchor; var gal := ship("galleon", 3, Vector3(an[0], 0, an[2]), gy + PI / 2)
	ship("skiff", 2, Vector3(g[0], 0, g[2]).lerp(Vector3(an[0], 0, an[2]), 0.45) + sx * 10, gy)
	var wr: Array = man.props.wreck_reef.pos; var wc: Array = man.props.wreck_reef.cam; ship("skiff", 1, Vector3(wr[0], 0, wr[2]).lerp(_v(wc) * Vector3(1, 0, 1), 0.45), 2.3)
	var ks: Array = man.props.saltwatch_keep.dive_bell
	for b in [["buoy_route", Vector3(300, 0, 40)], ["buoy_route", Vector3(860, 0, -820)], ["buoy_skiff", Vector3(wr[0] + 70, 0, wr[2] + 70)], ["buoy_dive", Vector3(ks[0] + 18, 0, ks[2] + 10)]]: prop(b[0], b[1])
	await fr(4)
	var gp := Vector3(g[0], 0, g[2]); var lr: Array = man.props.lantern_rock.pos
	for low in [false, true]:
		set_tier(low); var sfx := "_Low" if low else "_High"
		var gv := (gal.position - gp).normalized(); var gs := Vector3(gv.z, 0, -gv.x)
		await shot("A1_archipelago_hero" + sfx, gal.position + gv * 110 + gs * 60 + Vector3(0, 45, 0), gp.lerp(gal.position, 0.4) + Vector3(0, 4, 0), 62)
		await shot("A6_brinecrown_coil_arena" + sfx, _v(man.props.coil_arena.cam), Vector3(ap[0], 8, ap[2]), 62)
		if low: continue
		await shot("A2_gullhaven_port" + sfx, gal.position + gv * 30 - gs * 30 + Vector3(0, 10, 0), gp + Vector3(0, 5, 0), 60)
		await shot("A3_lantern_rock" + sfx, _v(man.props.lantern_rock.cam), Vector3(lr[0], 16, lr[2]), 55)
		await shot("A4_wreck_reef" + sfx, _v(man.props.wreck_reef.cam), Vector3(wr[0], 0, wr[2]), 58)
		await shot("A5_saltwatch_dive_bell" + sfx, _v(man.props.saltwatch_keep.cam), Vector3(ks[0], 5, ks[2]), 55)
		await shot("A7_storm_wall_border" + sfx, Vector3(1200, 25, 900), Vector3(1460, 50, 1260), 65)
		env.fog_enabled = false; water_hi.scale = Vector3(3, 1, 3); water_lo.scale = Vector3(3, 1, 3)
		await shot("A8_region_overview" + sfx, Vector3(150, 900, 1500), Vector3(150, 0, 0), 60)
	set_tier(false); env.fog_enabled = true; water_hi.scale = Vector3.ONE; water_lo.scale = Vector3.ONE
	var rest := glb("res://meshes/brinecrown_coil_rest.glb"); vcize(rest); rest.position = Vector3(1300, 4, 1100); root.add_child(rest); coil.visible = false
	await shot("B1_coil_rest_pose_side", Vector3(1300 + 75, 12, 1100 - 48), Vector3(1300, 4, 1100 - 48), 62)
	await shot("B2_coil_rest_pose_head", Vector3(1300 + 9, 9, 1100 + 9), Vector3(1300, 5, 1100), 55)
	rest.visible = false
	for kind in ["galleon", "skiff"]:
		for t in 4:
			var s := ship(kind, t, Vector3(1300, 0, 1100), 0.0)
			var dd := 30.0 if kind == "galleon" else 9.0
			await shot("U_%s_t%d" % [kind, t], Vector3(1300 + dd * 0.9, dd * 0.28, 1100 + dd * 0.55), Vector3(1300, dd * 0.15, 1100), 50)
			s.queue_free(); await fr(2)
	var f := FileAccess.open(out + "/drawcalls.txt", FileAccess.WRITE); f.store_string("\n".join(stats)); f.close(); quit()
