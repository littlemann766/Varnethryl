extends Node
## test 21 (Beth's interior pass). Run: VARN_LITE=1 godot --path . -- --intcheck   [env INT_TIER=0..3, INT_ONLY=id,id]
## On the real map, after the load warm-up: walks the hero (own physics paused) into every enterable door - the 25
## InteriorDefs buildings + the extra doors (barn, harbour, gate towers, lighthouse) - checks it lands on a floor, that
## the pass ceilings/dressing (+ torches on High) exist, walks back out, checks it is free outside, and counts
## pipeline compiles while inside (must be 0 after the warm-up). Report: /workspace/shots/godot21/intcheck_<tier>.txt
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func pf(n: int) -> void:
	for i in n: await get_tree().physics_frame
func _run() -> void:
	while not m.warmed: await get_tree().process_frame
	if OS.get_environment("INT_TIER") != "":
		m.tier = int(OS.get_environment("INT_TIER")); m.apply_quality(); await m._warm_views(); await m._warm_interiors()
	var only: Array = OS.get_environment("INT_ONLY").split(",", false)
	var mgr = m.interiors; var hero: CharacterBody3D = m.hero
	var entries := []
	for b in m.buildings: if mgr.has_interior(b.id): entries.append(b)
	var shell_seen := {}
	for b in m.extra_doors:
		if b.get("shell", false):   # test 22: one filler per model + the harbour landmarks (INT_ALL_SHELLS=1: every filler)
			var key: String = b.id if String(b.name).begins_with("fill_") else String(b.name)
			if shell_seen.has(key) and OS.get_environment("INT_ALL_SHELLS") == "": continue
			shell_seen[key] = true
		entries.append(b)
	var lines := []; var fails := 0; var ids := {}; var comp_total := 0
	for b in entries:
		if only.size() and not only.has(b.id): continue
		ids[b.id] = true
		var n: Node3D = b.node; var dl: Vector3 = mgr.door_local(b)
		var into: Vector3 = n.global_transform.basis * Vector3(0, 0, -1)
		var reach: float = maxf(2.6, b.aabb.end.z - dl.z + 1.6) if not b.has("door") else 2.6
		hero.global_position = n.global_transform * Vector3(dl.x, dl.y + 0.1, dl.z + reach); hero.velocity = Vector3.ZERO; mgr.cooldown = 0.0
		var entered := false; var t := 0.0
		if b.get("shell", false) and OS.get_environment("INT_SHOTS") != "":
			mgr.set_physics_process(false)
			hero.global_position = n.global_transform * Vector3(dl.x, dl.y + 0.1, dl.z - 2.5); m.yaw = atan2(-into.x, -into.z)
			for k in 8: await get_tree().process_frame
			get_viewport().get_texture().get_image().save_jpg("%s/SHELL_%s_%s.jpg" % [OS.get_environment("INT_SHOTS"), b.id, n.name], 0.8)
			mgr.set_physics_process(true)
			hero.global_position = n.global_transform * Vector3(dl.x, dl.y + 0.1, dl.z + reach); mgr.cooldown = 0.0
			await pf(2)
		while t < 6.0:   # walk in with the game's own controller (joystick forward, camera yaw facing the door)
			m.yaw = atan2(-into.x, -into.z); m.joy_vec = Vector2(0, -1)
			await pf(1); t += 1.0 / 60.0
			if mgr.active(): entered = true; break
		m.joy_vec = Vector2.ZERO
		var pc0: Array = m._pc()   # compiles from the moment the room is entered
		var res := "%s @ %s: " % [mgr.cur.get("id", b.id) if mgr.active() else b.id, n.name]
		if not entered:
			fails += 1; lines.append(res + "FAIL never entered (hero at %s, door %s)" % [n.to_local(hero.global_position), dl]); continue
		await pf(40)
		for k in 6:   # look around the room: four headings + up at the ceiling
			m.yaw += PI / 2; await get_tree().process_frame
		var inode: Node3D = mgr.cur.node
		var ceil_n := inode.find_children("PassCeiling*", "", true, false).size()
		var dress_n := inode.find_children("PassDressing*", "", true, false).size()
		var torches := 0
		for o in inode.find_children("*", "OmniLight3D", true, false): if (o as OmniLight3D).light_color.is_equal_approx(Color(1.0, 0.7, 0.42)): torches += 1
		await get_tree().process_frame; await get_tree().process_frame
		var shot_dir := OS.get_environment("INT_SHOTS")
		if shot_dir != "":
			DirAccess.make_dir_recursive_absolute(shot_dir)
			for k in 2:
				await get_tree().process_frame; await get_tree().process_frame
				get_viewport().get_texture().get_image().save_jpg("%s/%s_%s_%d.jpg" % [shot_dir, mgr.cur.get("id", b.id), n.name, k], 0.8)
				m.yaw += PI
		var dcs := []
		for k in 4:   # draw calls per frame, four headings
			m.yaw += PI / 2; await get_tree().process_frame; await get_tree().process_frame
			dcs.append(int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)))
		var pc1: Array = m._pc(); var comp: int = int(pc1[0] - pc0[0])
		comp_total += comp
		var on_floor := hero.is_on_floor()
		mgr.cooldown = 0.0
		var outv: Vector3 = inode.global_transform.basis * Vector3(0, 0, 1)
		var exited := false; t = 0.0
		while t < 5.0:
			m.yaw = atan2(-outv.x, -outv.z); m.joy_vec = Vector2(0, -1)
			await pf(1); t += 1.0 / 60.0
			if not mgr.active(): exited = true; break
		m.joy_vec = Vector2.ZERO
		await pf(3)
		var stuck := hero.test_move(hero.global_transform, Vector3(0, 0.01, 0)) and hero.test_move(hero.global_transform, Vector3(0.3, 0, 0)) and hero.test_move(hero.global_transform, Vector3(-0.3, 0, 0))
		var ok := on_floor and exited and not stuck and ceil_n > 0 and dress_n > 0
		if not ok: fails += 1
		lines.append(res + ("PASS" if ok else "FAIL") + " floor=%s exited=%s free_outside=%s ceilings=%d dressing=%d torches=%d draw_compiles=%d draw_calls=%d-%d" % [on_floor, exited, not stuck, ceil_n, dress_n, torches, comp, dcs.min(), dcs.max()])
		if mgr.active(): mgr.exit()
		await pf(3)
	lines.append("INTCHECK tier=%d pass_tier=%s entries=%d ids=%d fails=%d draw_compiles_inside=%d" % [m.tier, InteriorManager.pass_tier, lines.size(), ids.size(), fails, comp_total])
	print("\n".join(lines))
	DirAccess.make_dir_recursive_absolute("/workspace/shots/godot21")
	FileAccess.open("/workspace/shots/godot21/intcheck_%d.txt" % m.tier, FileAccess.WRITE).store_string("\n".join(lines) + "\n")
	get_tree().quit(1 if fails else 0)
