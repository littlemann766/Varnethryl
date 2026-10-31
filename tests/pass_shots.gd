extends SceneTree
## before/after interior shots: VK lavapipe + xvfb. args: only=a,b  tier=high|low  mode=before|after
const B := preload("res://interiors/interior_builder.gd")
const DEF := preload("res://interiors/interior_defs.gd")
var cam: Camera3D
func _initialize() -> void: _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await process_frame
func _run() -> void:
	root.size = Vector2i(800, 450)
	var args := {}
	for a in OS.get_cmdline_user_args(): var kv := a.split("="); args[kv[0]] = kv[1] if kv.size() > 1 else ""
	var we := WorldEnvironment.new(); var env := Environment.new()
	env.background_mode = Environment.BG_COLOR; env.background_color = Color(0, 0, 0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.56, 0.54, 0.5); env.ambient_light_energy = 0.9
	env.tonemap_mode = Environment.TONE_MAPPER_ACES; env.tonemap_white = 6.0
	env.glow_enabled = true; env.glow_intensity = 0.6; env.glow_bloom = 0.08; env.glow_hdr_threshold = 1.0
	we.environment = env; root.add_child(we)
	cam = Camera3D.new(); cam.fov = 70; cam.cull_mask = 0xFFFFF; root.add_child(cam); cam.current = true
	var ids: Array = (args.get("only", "") as String).split(",") if args.has("only") else DEF.D.keys() + InteriorExtraDefs.D.keys()
	var after: bool = args.get("mode", "after") == "after"
	var out: String = args.get("out", "/tmp/keeptest/shots")
	DirAccess.make_dir_recursive_absolute(out)
	var report := []
	for id in ids:
		var def: Dictionary = DEF.D[id] if DEF.D.has(id) else InteriorExtraDefs.D[id]
		var sz: Vector3 = DEF.SIZE.get(id, InteriorExtraDefs.SIZE.get(id, Vector3(10, 6, 10)))
		var info := B.build(id, def, sz); root.add_child(info.node)
		if after:
			var st := InteriorDressing.apply(info, def, args.get("tier", "high"))
			report.append("%s tris=%d lights=%d windows=%d decals=%d" % [id, st.tris, st.lights, st.windows, st.get("decals", 0)])
		# hide floors above 0 (as the game does when the hero is on floor 0)
		var fl := int(args.get("fl", "0"))
		if fl >= info.floors.size(): info.node.queue_free(); await frames(2); continue
		for i in info.floors.size(): info.floors[i].node.visible = i == fl
		var fy: float = info.floors[fl].y
		var W: float = info.W; var D: float = info.D
		# A: eye level from the door looking in and up-left (like the boss's phone shot)
		cam.position = Vector3(W * 0.18, fy + 1.7, D / 2 - 1.2); cam.look_at(Vector3(-W * 0.25, fy + 2.6, -D * 0.2))
		await frames(6); root.get_viewport().get_texture().get_image().save_jpg("%s/%s_a.jpg" % [out, id], 0.85)
		# B: along the right wall, looking up toward the ceiling
		cam.position = Vector3(-W * 0.3, fy + 1.6, D * 0.25); cam.look_at(Vector3(W * 0.45, fy + 3.4, -D * 0.3))
		await frames(6); root.get_viewport().get_texture().get_image().save_jpg("%s/%s_b.jpg" % [out, id], 0.85)
		# C: low by the stair, looking along it (the boss's v1.93 angle)
		if info.stairs.size():
			var st0: Dictionary = info.stairs[0]
			cam.position = st0.base + Vector3(0, 1.5, 0) - st0.dir * 1.5 + Vector3(-st0.dir.z, 0, st0.dir.x) * -1.6
			cam.look_at(st0.base + st0.dir * st0.run * 0.7 + Vector3(0, 2.8, 0))
			await frames(6); root.get_viewport().get_texture().get_image().save_jpg("%s/%s_c.jpg" % [out, id], 0.85)
		info.node.queue_free(); await frames(2)
	if report.size(): FileAccess.open(out + "/report.txt", FileAccess.WRITE).store_string("\n".join(report) + "\n")
	quit()
