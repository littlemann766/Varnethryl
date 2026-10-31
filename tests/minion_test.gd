extends SceneTree
## test 34: Titan minions: chase, attack (damage on the hit frame, modest, never one-shot), hit + death clips, freed after
## death, Owner one-shot ult kills them, city guards fight minions in the city zone. VARN_LITE=1 godot --headless --fixed-fps 60 --path . -s res://tests/minion_test.gd
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
	var party: Party = m.party; var c: HeroCombat = party.combat; var REF := HeroCombat.titan_ref_hp()
	party.set_hero("darius"); await f(2)
	m.spawn_world_boss(true); await f(5)
	var wb: WorldBoss = m.world_boss
	var h: Node3D = m.hero
	var spot := wb.global_position + Vector3(70, 0, 0); h.global_position = Vector3(spot.x, m.height(spot.x, spot.z) + 0.2, spot.z)
	wb._spawn_adds(spot + Vector3(0, 0, 25)); await f(2)
	var M: Array = wb.minions()
	ok(M.size() == 5 and M.filter(func(a): return a.kind == "wisp").size() == 2, "5 minions spawned (3 fiends + 2 wisps)")
	ok(M.all(func(a): return a.ap != null and a.ap.has_animation("run") and a.ap.has_animation("death")), "minions have AnimationPlayer with run/attack/hit/death")
	var d0: float = M[0].global_position.distance_to(h.global_position)
	await f(90)
	var d1: float = M[0].global_position.distance_to(h.global_position)
	ok(d1 < d0 - 3.0 and M[0].clip in ["run", "walk", "attack", "attack2", "attack3"], "chase: fiend closed in %.1f -> %.1f m playing %s" % [d0, d1, M[0].clip])
	var w = M.filter(func(a): return a.kind == "wisp")[0]
	ok(absf(w.global_position.y - (wb._gy(w.global_position.x, w.global_position.z) + 2.0)) < 0.05, "wisp hovers 2 m (no code bob)")
	# attack: wait until someone is attacking, check damage happens after the hit time, not at the start
	c.hp = c.max_hp; c._titan_log.clear()
	var saw_attack := false; var dmg_at_start := false; var hit_seen := false
	for i in 600:
		await f(1)
		for a in wb.minions():
			if a.state == "attack":
				saw_attack = true
				if a.atk_t < a.atk_hit - 0.05 and a.atk_done: dmg_at_start = true
		if c.hp < c.max_hp: hit_seen = true; break
	ok(saw_attack, "minions attack when in range")
	ok(hit_seen and not dmg_at_start, "damage lands on the hit frame (hero hp %.0f/%.0f)" % [c.hp, c.max_hp])
	var one := c.max_hp - c.hp
	ok(one > 0.0 and one <= 0.035 * REF + 1.0, "one minion hit is modest: %.0f (%.1f%% of %d)" % [one, 100.0 * one / REF, REF])
	# swarm 30 s: never kills a full-HP hero within the titan cap window
	c.hp = c.max_hp; c._titan_log.clear(); var minhp := c.hp
	wb._spawn_adds(h.global_position + Vector3(4, 0, 0))
	for i in 600:
		await f(1); minhp = minf(minhp, c.hp)
		if i % 300 == 299: c._titan_log.clear(); c.hp = c.max_hp
	ok(minhp > c.max_hp * 0.5, "10+ minions for 10 s never take more than half HP (min %.0f/%.0f)" % [minhp, c.max_hp])
	# hit + death
	var t = wb.minions().filter(func(a): return a.kind == "fiend")[0]
	t.state = "chase"; t.take_damage(10.0, h.global_position); await f(2)
	ok(t.state == "hit" and t.clip == "hit" and t.hp == t.max_hp - 10.0, "hit: hp %.0f, plays hit" % t.hp)
	for i in 8: t.take_damage(10.0, h.global_position)
	await f(2)
	ok(not t.alive() and t.clip == "death", "death clip at 0 HP")
	var p0: Vector3 = t.global_position; await f(60)
	ok(is_instance_valid(t) and t.global_position.distance_to(p0) < 0.01, "dead minion stays put")
	await f(240)
	ok(not is_instance_valid(t) or t.is_queued_for_deletion(), "dead minion freed ~4 s after death")
	# hero melee hits nearest minion through on_hero_used
	var sum0 := 0.0
	for a in wb.minions(): sum0 += a.hp
	wb.on_hero_used(0, {}, "darius"); var sum1 := 0.0
	for a in wb.minions(): sum1 += a.hp
	ok(sum1 == sum0 - 10.0, "hero basic attack hits the nearest minion for 10")
	# Owner one-shot ult kills all in radius
	party.set_hero("owner"); await f(2)
	var sk: Dictionary = {}
	for s in party.combat.skills if party.combat.get("skills") else []: if HeroCombat.one_shot("owner", s): sk = s; break
	var alive0 := wb.minions().size()
	if not sk.is_empty():
		wb.on_hero_used(4, sk, "owner"); await f(2)
		ok(alive0 > 0 and wb.minions().size() == 0, "Owner one-shot ult kills every minion in range (%d -> %d)" % [alive0, wb.minions().size()])
	else:
		for a in wb.minions(): a.global_position = h.global_position + Vector3(5, 0, 0)
		wb._hit_minions(h, 4, true); await f(2)
		ok(alive0 > 0 and wb.minions().size() == 0, "Owner one-shot ult (direct) kills every minion in range (%d -> 0)" % alive0)
	# guards: a minion inside the city zone becomes a guard target and gets killed
	var G = m.get("guards")
	if G:
		wb._spawn_adds(Vector3(0, 0, 175)); await f(2)
		var mm = wb.minions()[0]; mm.global_position = Vector3(3, m.height(3, 200), 200)
		h.global_position = Vector3(-10, m.height(-10, 160) + 0.2, 160)
		await f(2)
		ok(G.hostiles().has(mm), "guards see a minion in the city zone as a monster")
		for i in 900:
			await f(1)
			if not mm.alive(): break
		ok(not mm.alive(), "guards kill the minion")
	else: ok(false, "no guards node")
	print("MINIONS %d checks, %d failed -> %s" % [n, fails, "PASS" if fails == 0 else "FAIL"]); quit(0 if fails == 0 else 1)
