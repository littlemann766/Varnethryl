extends SceneTree
## Full-game check: for every building with an interior, enter it through InteriorManager in the real main scene,
## make sure the hero lands on a floor inside the room (not trapped / not bounced out) and can walk 2 m into the room.
## godot --headless -s res://tests/game_enter_test.gd
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var m = load("res://main.tscn").instantiate(); root.add_child(m)
	for i in 30: await process_frame
	var fails := 0; var n := 0
	for b in m.buildings + m.extra_doors:
		if not m.interiors.has_interior(b.id): continue
		n += 1
		m.interiors.enter(b)
		var info: Dictionary = m.interiors.cur
		for i in 20: await physics_frame
		var hero: CharacterBody3D = m.hero
		var lp: Vector3 = info.node.to_local(hero.global_position)
		var p0 := lp
		# walk into the room by moving the hero body directly (input-independent)
		for i in 40:
			hero.velocity = info.node.global_transform.basis * Vector3(0, -1, -3.0); hero.move_and_slide(); await physics_frame
		lp = info.node.to_local(hero.global_position)
		var ok: bool = m.interiors.active() and absf(lp.y) < 0.5 and absf(lp.x) < info.W / 2 and p0.z - lp.z > 1.5 and info.W > 3.0
		print("%s %s W%.1f D%.1f spawn %s moved %.2f" % ["OK  " if ok else "FAIL", b.id, info.W, info.D, p0, p0.z - lp.z])
		if not ok: fails += 1
		m.interiors.exit()
		for i in 5: await physics_frame
	print("GAME_ENTER %d buildings, %d failed" % [n, fails])
	quit()
