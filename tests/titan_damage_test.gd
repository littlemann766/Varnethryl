extends SceneTree
## test 26: Titan attacks do a little damage (<= ~12-15% of a normal hero's 700 HP per hit) and no combo/overlap
## kills a full-HP hero. VARN_LITE=1 godot --headless --path . -s res://tests/titan_damage_test.gd
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
	var party: Party = m.party; var c: HeroCombat = party.combat
	var REF := HeroCombat.titan_ref_hp()
	party.set_hero("darius"); await f(2)
	m.spawn_world_boss(true); await f(5)
	var wb: WorldBoss = m.world_boss
	for r in ["fissure", "wave"]:
		c.hp = c.max_hp; c._titan_log.clear()
		wb.ritual = r; m.hero.global_position = wb.crack.global_position if r == "fissure" else wb.global_position + Vector3(30, 0, 0)
		var h0 := c.hp; wb._complete(); await f(2)
		var d := h0 - c.hp
		ok(d > 0.0 and d <= 0.15 * REF, "world boss %s: %.0f dmg (%.1f%% of %d)" % [r, d, 100.0 * d / REF, REF])
	# overlap: 12 slams + waves in the same second
	c.hp = c.max_hp; c._titan_log.clear()
	for i in 12:
		wb.ritual = "fissure" if i % 2 == 0 else "wave"; m.hero.global_position = wb.crack.global_position; wb._complete()
	await f(2)
	ok(c.hp > 0.0 and c.max_hp - c.hp <= 0.35 * REF + 1.0, "12 overlapping world-boss slams: hp %.0f/%.0f (lost %.1f%%)" % [c.hp, c.max_hp, 100.0 * (c.max_hp - c.hp) / REF])
	# enemy Titans (6x roaming Titan + volcano Titan): every pattern + aoe, spammed
	var d2: EnemyDirector = party.director
	var t: Enemy = d2.spawn("titan", m.hero.global_position + Vector3(0, 0, -6), m.hero)
	var vts := d2.enemies.filter(func(e): return e is VolcanoTitan)
	for e in [t] + vts:
		c.hp = c.max_hp; c._titan_log.clear(); c.reduce_t = 0.0
		var h1 := c.hp
		d2._aoe(e, m.hero.global_position, 50.0, 3.0); var one := h1 - c.hp
		ok(one > 0.0 and one <= 0.15 * REF, "%s aoe: %.0f dmg (%.1f%%)" % [e.type_id, one, 100.0 * one / REF])
		for i in 30:
			d2._aoe(e, m.hero.global_position, 50.0, 3.0)
			e.global_position = m.hero.global_position + Vector3(0, 0, -3); e.look_at(m.hero.global_position, Vector3.UP)
			d2._on_attack(e, {"shape": "ring", "reach": 99, "dmg": 2.5})
		ok(c.hp > 0.0, "%s: 60 stacked stomps/swats/sweeps -> hero alive, hp %.0f/%.0f" % [e.type_id, c.hp, c.max_hp])
	# Owner: cheat HP irrelevant, same absolute small hits
	party.set_hero("owner"); await f(2); c._titan_log.clear()
	var o0 := c.hp; wb.ritual = "fissure"; m.hero.global_position = wb.crack.global_position; wb._complete(); await f(2)
	ok(o0 - c.hp <= 0.15 * REF, "owner takes the same small hit (%.0f)" % (o0 - c.hp))
	# other enemies unchanged (frost troll still uses its normal damage)
	party.set_hero("darius"); await f(2); c.hp = c.max_hp
	var tr: Enemy = d2.spawn("frosttroll_a", m.hero.global_position + Vector3(0, 0, -4), m.hero)
	var h2 := c.hp; d2._aoe(tr, m.hero.global_position, 50.0, 1.0)
	ok(h2 - c.hp > 0.15 * REF, "frost troll damage unchanged (%.0f)" % (h2 - c.hp))
	print("TITAN_DMG %d checks, %d failed -> %s" % [n, fails, "PASS" if fails == 0 else "FAIL"])
	quit(1 if fails else 0)
