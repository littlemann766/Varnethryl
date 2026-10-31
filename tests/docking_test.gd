extends Node
## test 34: every landing point: sail up -> "Go ashore" -> ship parked level at the moor, hero + Pip + companions ashore ->
## walk 20 m inland on the real colliders (never below the sea, never stuck) -> back to the pier -> "Board ship" -> on deck.
## Also: mainland Tidewrack pier "Go ashore", map markers + fog. Shots with a display. Run: -- --docking
var m: Node
var sea: TidewrackSea
var npass := 0
var nfail := 0
var out := "/workspace/shots/t34/dock/"
func ok(c: bool, t: String) -> void:
	if c: npass += 1; print("DK PASS ", t)
	else: nfail += 1; print("DK FAIL ", t)
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func shot(n: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await frames(25); get_viewport().get_texture().get_image().save_png(out + "dock_%s.png" % n); print("DK SHOT ", n)
func fade_wait() -> void:
	await get_tree().create_timer(1.4).timeout; await frames(3)
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(out)
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0); m.party.set_hero("aldric"); m.party._set_companions(["garruk"])
	sea = m.sea; sea.save.discovered_ports = ["tidewrack"]
	sea.enter("galleon"); sea.unlock_all = true; await frames(5)
	var L: Dictionary = sea._landings()
	ok(L.size() >= 13, "landings.json has %d landing points" % L.size())
	var shots := ["gullhaven", "lantern_rock", "saltglass", "frostreach", "vent", "aurora_arch"]
	var only := OS.get_environment("DK_ONLY")
	for k in L:
		if only != "" and not (k in only.split(",")): continue
		var d: Dictionary = L[k]; var moor := sea._v3(d.moor)
		sea.cur_region = d.region; sea.ship.position = moor - sea._inland(d) * 20.0; sea.ship.speed = 0.0; sea.ship.alt = 0.0
		for i in 3000:
			if sea._region_ready(d.region): break
			await get_tree().process_frame
		await frames(10)
		sea.ship.position = moor - sea._inland(d) * 15.0; sea.ship.speed = 0.0; await frames(3)
		ok(sea.ui.prompt.visible and sea.ui.prompt.text == "Go ashore", "%s: Go ashore prompt near the moor (got '%s')" % [k, sea.ui.prompt.text])
		sea.go_ashore(k); await fade_wait()
		ok(sea.ashore == k, "%s: ashore" % k)
		ok(sea.ship.position.distance_to(Vector3(moor.x, 0, moor.z)) < 0.5 and absf(sea.ship.rotation.x) < 0.001 and absf(sea.ship.rotation.z) < 0.001 and sea.ship.position.y == 0.0, "%s: ship parked level at the moor" % k)
		var hp := sea.to_local(m.hero.global_position)
		ok(hp.distance_to(sea.pier_head(d)) < 2.5, "%s: hero on the pier head (%.1f m)" % [k, hp.distance_to(sea.pier_head(d))])
		ok(m.pip.global_position.distance_to(m.hero.global_position) < 4.0 and not m.party.riding, "%s: Pip + companions ashore with the hero" % k)
		var inl := sea._inland(d)
		m.yaw = atan2(inl.x, inl.z)   # camera looks inland: fwd = (-sin, -cos) = -inl, so the shot frames hero + pier + ship behind
		if k in shots: await shot(k + "_ashore")
		var start := sea.to_local(m.hero.global_position); var minh := 1e9; var resets := 0
		var fw := Vector3(-sin(m.yaw), 0, -cos(m.yaw))
		var iy := -1.0 if fw.dot(inl) > 0 else 1.0
		for i in 900:
			sea.drive(Vector2(0, iy), 1.0 / 60.0)
			var lp := sea.to_local(m.hero.global_position); minh = minf(minh, lp.y)
			if sea.ui.msg.text.begins_with("Careful"): resets += 1; sea.ui.msg.text = ""
			if Vector2(lp.x - start.x, lp.z - start.z).length() >= 20.0: break
			await get_tree().physics_frame
		var endp := sea.to_local(m.hero.global_position)
		var dist := Vector2(endp.x - start.x, endp.z - start.z).length()
		ok(dist >= 20.0 and minh > 0.0 and resets == 0, "%s: walked %.1f m inland on foot (min y %.2f, resets %d)" % [k, dist, minh, resets])
		await frames(30)
		var c0: Vector3 = m.party.companions[0].node.global_position if m.party.companions.size() > 0 else m.pip.global_position
		ok(c0.distance_to(m.hero.global_position) < 8.0, "%s: companion followed ashore (%.1f m)" % [k, c0.distance_to(m.hero.global_position)])
		if k in shots:
			m.yaw = atan2(-inl.x, -inl.z); await shot(k + "_inland")
		m.hero.global_position = sea.to_global(sea.pier_head(d) + Vector3(0, 0.6, 0)); await frames(4); sea.drive(Vector2.ZERO, 1.0 / 60.0)
		ok(sea.ui.prompt.text == "Board ship", "%s: Board ship prompt at the pier" % k)
		sea.board_ship(); await fade_wait()
		for i in 3: sea.drive(Vector2.ZERO, 1.0 / 60.0)
		var deck: Vector3 = m.hero.global_position - sea.ship.global_position
		ok(sea.ashore == "" and deck.length() < 6.0 and deck.y > 1.0 and m.party.riding, "%s: re-boarded at the same spot, crew on deck" % k)
	var wm = m.world_map
	var lw := Vector2(L.coil_isle.shore[0], L.coil_isle.shore[2])
	ok(wm.revealed(lw), "map: visited landing (Coil Isle) revealed on the fogged map")
	ok(not wm.revealed(Vector2(-2900, -2900)), "map: unvisited corner stays fogged")
	sea.cur_region = "A"; sea.ship.position = Vector3(1300, 0, 300); sea.ship.speed = 0.0; await frames(3); sea._contexts()
	ok(sea.ui.prompt.text == "Go ashore", "mainland Tidewrack pier: Go ashore prompt at the bay mouth")
	sea.ui._cb.call(); await fade_wait()
	ok(not sea.active and m.hero.global_position.distance_to(m._galleon_pier()[0]) < 3.0, "mainland: ashore on the Tidewrack pier beside the galleon")
	await frames(5)
	ok(sea.ui.prompt.text == "Set sail", "mainland: Set sail again from the same pier")
	await shot("mainland_pier")
	print("DK DONE pass=%d fail=%d" % [npass, nfail]); get_tree().quit(0 if nfail == 0 else 1)
