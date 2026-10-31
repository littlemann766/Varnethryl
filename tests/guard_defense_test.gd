extends SceneTree
## test 31: a monster walks toward the South Gate; the gate guards engage, kill it with their attack clip and go back to
## their posts. Guards never target the player (even standing next to them / hitting monsters) and ignore monsters far
## outside the walls and the Titans. VARN_LITE=1 godot --headless --fixed-fps 60 --path . -s res://tests/guard_defense_test.gd
var m; var fails := 0; var n := 0
func ok(c: bool, msg: String) -> void:
	n += 1; print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1
func f(k: int) -> void:
	for i in k: await physics_frame; await process_frame
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	m = load("res://main.tscn").instantiate(); root.add_child(m)
	await f(30)
	var G: TownGuards = m.guards; var d: EnemyDirector = m.party.director
	ok(G != null and G.guards.size() >= 6, "guards present: %d" % (G.guards.size() if G else 0))
	ok(TownGuards.LEVEL >= 60 and TownGuards.MAX_HP >= 20000.0, "guards level %d, %d HP" % [TownGuards.LEVEL, TownGuards.MAX_HP])
	for e in d.living(): e.kill_now(Vector3.ZERO)   # clear spawned field monsters
	await f(5)
	var hp0: float = m.party.combat.hp
	# player stands among the south-gate guards for 5 s: nobody targets him, he takes no damage
	var g0: Dictionary = G.guards[0]
	m.hero.global_position = (g0.node as Node3D).global_position + Vector3(1.5, 0, 0); await f(300)
	ok(G.guards.all(func(g): return g.tgt == null), "guards ignore the player")
	ok(m.party.combat.hp >= hp0, "player took no guard damage")
	# far monster (beyond zone): ignored
	var far: Enemy = d.spawn("wolf", Vector3(0, 0, 185 + 90), m.hero); far.target = m.hero
	m.hero.global_position = Vector3(0, 0, 0); await f(60)
	ok(G.guards.all(func(g): return g.tgt != far), "monster 90 m outside the wall: ignored")
	far.kill_now(Vector3.ZERO)
	# titan: ignored
	var ti: Enemy = d.spawn("titan", Vector3(0, 0, 185 + 10), m.hero)
	await f(30); ok(G.guards.all(func(g): return g.tgt != ti), "Titan left to the players")
	ti.kill_now(Vector3.ZERO); await f(5)
	# a stone troll walks to the South Gate (hero inside the city as its target)
	var posts := G.guards.map(func(g): return g.post)
	var e: Enemy = d.spawn("stonetroll", Vector3(4, 0, 185 + 45), m.hero); e.target = m.hero; e.set_state("chase")
	m.hero.global_position = Vector3(0, 0, 120)
	var hits := [0]; G.guard_hit.connect(func(en, dm): if en == e: hits[0] += 1)
	var engaged := false; var t := 0
	while e.alive() and t < 60 * 90:
		await f(1); t += 1
		if G.guards.any(func(g): return g.tgt == e): engaged = true
		m.party.combat.hp = m.party.combat.max_hp   # keep the bait alive
	ok(engaged, "guards engaged the stone troll")
	ok(not e.alive(), "stone troll killed by guards in %.1f s (%d guard hits, hp %.0f/%.0f)" % [t / 60.0, hits[0], e.hp, e.max_hp])
	ok(hits[0] > 0, "guards used their attack (hits %d)" % hits[0])
	ok(e.global_position.z > 185 - 40, "killed at the gate, not deep in town (z %.1f)" % e.global_position.z)
	await f(60 * 30)
	var back := 0
	for i in G.guards.size():
		var g: Dictionary = G.guards[i]
		if g.tgt == null and not g.ret: back += 1
	ok(back == G.guards.size(), "all guards back on duty at their posts/patrols: %d/%d" % [back, G.guards.size()])
	var near := 0
	for i in G.guards.size(): if (G.guards[i].node as Node3D).global_position.distance_to(posts[i]) < 9.0: near += 1
	ok(near == G.guards.size(), "guards within their beat of the post: %d/%d" % [near, G.guards.size()])
	print("GUARD_DEFENSE %d checks, %d failed -> %s" % [n, fails, "PASS" if fails == 0 else "FAIL"])
	quit(1 if fails else 0)
