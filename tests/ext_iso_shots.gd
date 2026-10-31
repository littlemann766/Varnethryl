extends SceneTree
## test 22: Beth's exterior pass before/after, day + night (window glow), one card2 building at a time (light on RAM).
## Run: godot --path . -s res://tests/ext_iso_shots.gd -- [after] [low] [night] out=dir
func _initialize() -> void: _run.call_deferred()
func fr(n): for i in n: await process_frame
func _run() -> void:
	root.size = Vector2i(800, 450)
	var a := OS.get_cmdline_user_args(); var after := a.has("after"); var low := a.has("low"); var night := a.has("night")
	var out := "/tmp/ext"
	for x in a: if x.begins_with("out="): out = x.substr(4)
	DirAccess.make_dir_recursive_absolute(out)
	var we := WorldEnvironment.new(); var env := Environment.new(); var sky := Sky.new(); var sm := ProceduralSkyMaterial.new(); sky.sky_material = sm
	env.background_mode = Environment.BG_SKY; env.sky = sky; env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.glow_enabled = true; env.glow_hdr_threshold = 1.0
	if night:
		sm.sky_top_color = Color(0.01, 0.02, 0.06); sm.sky_horizon_color = Color(0.05, 0.07, 0.14); sm.ground_horizon_color = sm.sky_horizon_color; sm.ground_bottom_color = Color(0.01, 0.01, 0.02)
		env.ambient_light_energy = 0.4; env.tonemap_exposure = 1.15
	we.environment = env; root.add_child(we)
	var sun := DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-38, 35, 0); sun.shadow_enabled = true; sun.light_energy = 0.08 if night else 1.1
	if night: sun.light_color = Color(0.6, 0.7, 1.0)
	root.add_child(sun)
	var g := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(300, 300); g.mesh = pm; var gmat := StandardMaterial3D.new(); gmat.albedo_color = Color(0.36, 0.4, 0.28); g.material_override = gmat; root.add_child(g)
	var cam := Camera3D.new(); cam.fov = 55; root.add_child(cam); cam.current = true
	for id in ["inn", "townhall", "bakery", "house1", "smithy", "temple"]:
		var f := "res://assets/card2/bld_%s_card2_lod1.glb" % id
		if not ResourceLoader.exists(f): continue
		var n: Node3D = load(f).instantiate(); root.add_child(n)
		var ab := AABB(); var first := true
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var bb: AABB = mi.global_transform * mi.get_aabb(); ab = bb if first else ab.merge(bb); first = false
			if night and not after:
				for s in mi.mesh.get_surface_count():
					var mm = mi.get_active_material(s)
					if mm is BaseMaterial3D and mm.emission_texture: mm.emission_enabled = true; mm.emission = Color(1.0, 0.72, 0.38); mm.emission_energy_multiplier = 3.0
		if after:
			ExteriorDressing.apply(n, "low" if low else "high")
			if night: ExteriorDressing._proxy.emission_energy_multiplier = 3.0
		var c := ab.get_center()
		cam.position = c + Vector3(ab.size.x * 0.45, -c.y + 1.7, ab.size.z / 2 + maxf(ab.size.x, ab.size.y) * 0.75); cam.look_at(c + Vector3(0, -ab.size.y * 0.1, 0))
		await fr(8); root.get_viewport().get_texture().get_image().save_jpg("%s/%s.jpg" % [out, id], 0.85)
		n.queue_free(); await fr(2)
	quit()
