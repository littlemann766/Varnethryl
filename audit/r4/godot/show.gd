extends Node3D
# Beth r4 showcase: buildings, terrain, trees at a tier suffix ("" High, "_lod1" Medium, "_lod2" Low). Day + night shots + stats.
var cam: Camera3D
var sun: DirectionalLight3D
var env: Environment
var sfx := ""
var stats := {}
func _place(path: String, pos: Vector3, yaw := 0.0) -> Node3D:
	var ps = load(path)
	if ps == null:
		print("FAIL ", path); return null
	var n: Node3D = ps.instantiate(); n.position = pos; n.rotation.y = yaw; add_child(n); return n
func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0: sfx = args[0]
	var we := WorldEnvironment.new(); env = Environment.new(); env.background_mode = Environment.BG_SKY
	var sky := Sky.new(); var sm := ProceduralSkyMaterial.new(); sky.sky_material = sm; env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.glow_enabled = true; env.glow_intensity = 0.6; env.glow_hdr_threshold = 0.9
	env.ssao_enabled = true; env.fog_enabled = true; env.fog_density = 0.0015
	we.environment = env; add_child(we)
	sun = DirectionalLight3D.new(); sun.rotation = Vector3(-0.75, 0.9, 0); sun.shadow_enabled = true; sun.directional_shadow_max_distance = 260; add_child(sun)
	var g := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(1600, 1600); g.mesh = pm
	var gm := StandardMaterial3D.new(); gm.albedo_color = Color(0.32, 0.45, 0.26); gm.roughness = 1.0; g.material_override = gm; add_child(g)
	cam = Camera3D.new(); cam.far = 3000; cam.fov = 60; add_child(cam)
	var B := "res://r4/hi/buildings/"
	var ids := ["mage","temple","colosseum","keep","guildhall","inn","library","townhall","lighthouse","windmill","smithy","apothecary","market","treasury","crypt","bakery","training","observatory","house1","house2","house3","house4","farmhouse","barn","stables","thieves","gate_tower"]
	for i in ids.size():
		_place(B + "bld_%s%s.glb" % [ids[i], sfx], Vector3((i % 6) * 62 - 155, 0, -(i / 6) * 62))
	var T := "res://r4/hi/terrain/"
	var tr := [["peak_snow_hi", Vector3(-160, 0, -520)], ["peak_bare_hi", Vector3(-20, 0, -560)], ["volcano_flank_hi", Vector3(150, 0, -540)], ["cliff_strata_hi", Vector3(-80, 0, -420)], ["shore_edge_hi", Vector3(60, 0, -400)], ["boulder_strata_hi", Vector3(0, 0, -380)]]
	for t in tr: _place(T + t[0] + sfx + ".glb", t[1])
	var water := MeshInstance3D.new(); var wp := PlaneMesh.new(); wp.size = Vector2(60, 30); water.mesh = wp; water.position = Vector3(60, 0.0, -412)
	var wm := StandardMaterial3D.new(); wm.albedo_color = Color(0.15, 0.32, 0.42, 0.75); wm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; wm.roughness = 0.05; water.material_override = wm; add_child(water)
	var TR := "res://r4/hi/trees/"
	var trees := ["oak_hi","oak_autumn_hi","oak_deep_hi","birch_hi","blossom_hi","pine_hi","pine_snow_hi","bush_hi","bush_autumn_hi","grass_clump_hi"]
	var rng := RandomNumberGenerator.new(); rng.seed = 7
	for k in 60:
		var t: String = trees[k % trees.size()]
		var s2 := sfx
		if sfx == "_lod2" and (t.begins_with("bush") or t.begins_with("grass")): s2 = "_lod1"
		_place(TR + t + s2 + ".glb", Vector3(rng.randf_range(-45, 45), 0, rng.randf_range(95, 150)), rng.randf() * TAU)
	await _shots()
	var fa := FileAccess.open("res://r4/stats%s_%s.json" % [sfx, RenderingServer.get_current_rendering_method()], FileAccess.WRITE); fa.store_string(JSON.stringify(stats, "  ")); fa.close()
	get_tree().quit()
func _shot(name: String, p: Vector3, t: Vector3) -> void:
	cam.position = p; cam.look_at(t)
	for i in 20: await get_tree().process_frame
	var t0 := Time.get_ticks_usec()
	for i in 10: await get_tree().process_frame
	var ms := (Time.get_ticks_usec() - t0) / 10000.0
	stats[name] = {"draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), "primitives": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), "objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME), "frame_ms_llvmpipe": ms, "vram_MB": Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0}
	get_viewport().get_texture().get_image().save_png("res://r4/shot%s_%s_%s.png" % [sfx, RenderingServer.get_current_rendering_method(), name])
func _night() -> void:
	sun.light_energy = 0.04; sun.light_color = Color(0.6, 0.7, 1.0); env.background_energy_multiplier = 0.04; env.ambient_light_energy = 0.12; env.glow_intensity = 1.2
func _shots() -> void:
	await _shot("hero_mage_temple", Vector3(-115, 22, 55), Vector3(-110, 10, 0))
	await _shot("hero_colosseum_keep", Vector3(-15, 30, 55), Vector3(-30, 6, 0))
	await _shot("row2", Vector3(-60, 26, -10), Vector3(-60, 6, -70))
	await _shot("houses", Vector3(-30, 22, -140), Vector3(-30, 5, -200))
	await _shot("terrain", Vector3(-60, 55, -420), Vector3(-150, 35, -520))
	await _shot("peak_bare", Vector3(40, 40, -470), Vector3(-20, 25, -560))
	await _shot("volcano", Vector3(120, 38, -465), Vector3(150, 18, -540))
	await _shot("shore", Vector3(62, 9, -378), Vector3(58, 0, -402))
	await _shot("cliff", Vector3(-70, 18, -370), Vector3(-80, 14, -425))
	await _shot("trees", Vector3(0, 7, 82), Vector3(0, 5, 125))
	await _shot("closeup_mage", Vector3(-128, 14, 42), Vector3(-155, 10, 0))
	await _shot("closeup_temple", Vector3(-78, 10, 40), Vector3(-93, 9, 0))
	await _shot("closeup_inn", Vector3(170, 9, 32), Vector3(155, 5, 0))
	_night()
	await _shot("night_closeup_mage", Vector3(-128, 14, 42), Vector3(-155, 10, 0))
	await _shot("night_town", Vector3(-15, 30, 55), Vector3(-30, 6, 0))
	await _shot("night_closeup_inn", Vector3(170, 9, 32), Vector3(155, 5, 0))
	await _shot("night_volcano", Vector3(120, 38, -465), Vector3(150, 18, -540))
