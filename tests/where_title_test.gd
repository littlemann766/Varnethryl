extends SceneTree
## test 25 (boss: "Arcane Academy of Varnethryl" title stuck while flying far outside). For EVERY building with an
## interior (+ walk-in footprints): the title shows on arrival, then hides on exit, teleport, door use, flying, and
## after ~4 s. Run: VARN_LITE=1 godot --headless --fixed-fps 60 --path . -s res://tests/where_title_test.gd
var m; var fails := 0; var n := 0
func ok(c: bool, msg: String) -> void:
	n += 1
	if not c: fails += 1; print("FAIL ", msg)
func f(k: int) -> void:
	for i in k: await physics_frame; await process_frame
func vis() -> bool: return m.where_label.visible and m.where_label.text != ""
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	m = load("res://main.tscn").instantiate(); root.add_child(m)
	await f(30)
	if m.fly_controls: m.fly_controls.process_mode = Node.PROCESS_MODE_DISABLED   # owner gate is locked in tests; it would land the hero
	var seen := {}; var nb := 0
	for b in m.buildings + m.extra_doors:
		if not m.interiors.has_interior(b.id): continue
		nb += 1
		var tag := "%s/%s" % [b.id, b.name]
		m.interiors.enter(b); await f(3)
		ok(vis(), tag + ": title shows on entry")
		m.interiors.exit(); await f(3)
		ok(not vis(), tag + ": hidden after exit")
		m.interiors.enter(b); await f(3)
		m.flight = true; m.cheat["fly"] = true; await f(2)
		ok(not vis(), tag + ": hidden while flying")
		m.hero.global_position += Vector3(0, 0, 400); await f(4)   # flew far out without the door
		ok(not vis() and not m.interiors.active(), tag + ": hidden + interior dropped when far outside")
		m.flight = false; m.cheat["fly"] = false
		m.interiors.cur = {}; m.interiors.cur_bld = {}; m.interiors.cooldown = 0.0
		m.interiors.enter(b); await f(3)
		m._teleport(Vector3(-6, 0, 30), 0.0); await f(2)
		ok(not vis(), tag + ": hidden after teleport")
		m.interiors.cur = {}; m.interiors.cur_bld = {}
		if not seen.has(b.id):   # timeout once per interior kind
			seen[b.id] = true
			m.interiors.enter(b); await f(3)
			await f(int(4.3 * 60))
			ok(not vis(), tag + ": hidden after ~4 s")
			m.interiors.exit(); await f(2)
		m.interiors.cooldown = 0.0
	# walk-in footprints (main.buildings): standing inside shows the name, then timeout / teleport hide it
	m.interiors.cur = {}; m.interiors.cur_bld = {}
	var names := {}
	for b in m.buildings:
		if names.has(b.name): continue
		names[b.name] = true
		m.hero.global_position = Vector3(0, 0, 400); await f(3)   # step outside first so each arrival is new
		m.interiors.cooldown = 99.0
		var c: Vector3 = (b.node as Node3D).to_global(b.aabb.get_center()); c.y = (b.node as Node3D).to_global(b.aabb.position).y + 0.3
		m.hero.global_position = c; m.hero.velocity = Vector3.ZERO; await f(3)
		if m.where_label.text != b.name: continue
		ok(vis(), b.name + ": footprint title shows"); await f(int(4.3 * 60))
		ok(not vis(), b.name + ": footprint title hidden after ~4 s")
	print("WHERE_TITLE %d buildings, %d checks, %d failed -> %s" % [nb, n, fails, "PASS" if fails == 0 else "FAIL"])
	quit(1 if fails else 0)
