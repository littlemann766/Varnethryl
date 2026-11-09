extends SceneTree
## Adversarial crowd combat on the live scene. Headless. Not a phone result.
## godot --headless --path . -s res://tests/horde_fair_combat_test.gd
var fails := 0
var n := 0

func ok(c: bool, msg: String) -> void:
	n += 1
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1

func _initialize() -> void: _run.call_deferred()

func _run() -> void:
	OS.set_environment("VARN_LITE", "1")
	OS.set_environment("VARN_NO_FLOWERS", "1")
	OS.set_environment("VARN_NO_HORDE_REFILL", "1")
	await process_frame
	var m = load("res://main.tscn").instantiate()
	root.add_child(m)
	if m.cheats:
		m.cheats.flags.god = false
		m.cheats.flags.bump = false
	for _i in 20: await physics_frame
	for g in m.guards.guards:
		g.down_t = 999.0
		g.tgt = null
	var crowd: HordeCrowd = m.horde.crowd
	ok(crowd.alive_n == HordeCrowd.SIM_DEFAULT, "packed probe starts from the 1000 sim (%d)" % crowd.alive_n)
	await _cooldown(m, crowd)
	await _packed(m, crowd)
	await _elevated(m, crowd)
	await _inside(m, crowd)
	await _obstacle(m, crowd)
	await _haven_plant(m, crowd)
	await _sea_plant(m, crowd)
	await _promoted_invalid(m, crowd)
	await _slots(m, crowd)
	await _respawn(m, crowd)
	await _player_hits(m, crowd)
	print("FAIR_COMBAT %d checks, %d failed bites=%d" % [n, fails, crowd.bites])
	quit(1 if fails else 0)

func _park(crowd: HordeCrowd, z0: float) -> void:
	var d: EnemyDirector = crowd.director.main.party.director
	for z in crowd.pool:
		if z.crowd_id < 0: continue
		d.enemies.erase(z)
		z.release_crowd()
	for i in crowd.id.size():
		if (crowd.flags[i] & 2) == 0: continue
		crowd.flags[i] = crowd.flags[i] & ~2
		crowd.pool_i[i] = -1
	crowd.near_n = 0
	var placed := 0
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0: continue
		crowd.px[i] = 80.0 + float(placed % 40) * 1.8
		crowd.pz[i] = z0 + float(int(placed / 40)) * 1.8
		crowd.hold_x[i] = crowd.px[i]
		crowd.hold_z[i] = crowd.pz[i]
		crowd.wind_t[i] = 0.0
		crowd.lock_t[i] = 0.0
		placed += 1

func _stack(crowd: HordeCrowd, at: Vector3, count: int) -> int:
	var placed := 0
	for i in crowd.id.size():
		if placed >= count: break
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		var ang := float(placed) * 0.37
		crowd.px[i] = at.x + cos(ang) * 0.25
		crowd.pz[i] = at.z + sin(ang) * 0.25
		crowd.hold_x[i] = crowd.px[i]
		crowd.hold_z[i] = crowd.pz[i]
		crowd.wind_t[i] = 0.0
		crowd.lock_t[i] = 0.0
		placed += 1
	return placed

func _piled(crowd: HordeCrowd, at: Vector3, reach: float) -> int:
	var c := 0
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		if Vector2(crowd.px[i] - at.x, crowd.pz[i] - at.z).length() <= reach: c += 1
	return c

func _cooldown(m, crowd: HordeCrowd) -> void:
	_park(crowd, 500.0)
	m.hero.global_position = Vector3(0, 1.0, 210)
	var idx := -1
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0 or crowd.role[i] != 0: continue
		idx = i
		break
	ok(idx >= 0, "a shambler record is free for the cooldown handoff")
	if idx < 0: return
	crowd.px[idx] = 0.6
	crowd.pz[idx] = 210.0
	crowd.hold_x[idx] = 0.6
	crowd.hold_z[idx] = 210.0
	crowd.wind_t[idx] = 0.0
	crowd.lock_t[idx] = 5.0
	crowd.hp[idx] = 190.0
	var sim := int(crowd.id[idx])
	ok(crowd._promote_index(idx, m.hero.global_position), "the locked record promotes")
	var body: HordeZombie = crowd.pool[crowd.pool_i[idx]]
	ok(body.crowd_lock >= 4.9, "promotion keeps the 5 s cooldown on the body (%.2f)" % body.crowd_lock)
	m.party.combat.hp = m.party.combat.max_hp
	var hp0: float = m.party.combat.hp
	for _i in 40: await physics_frame
	ok(is_equal_approx(m.party.combat.hp, hp0), "a promoted body does not swing through a 5 s cooldown (hp %.0f)" % m.party.combat.hp)
	ok(body.crowd_lock > 4.0, "the body still has most of that cooldown (%.2f)" % body.crowd_lock)
	m.hero.global_position = Vector3(0, 1.0, 20)
	for _i in 8: await physics_frame
	var back := crowd._index_of(sim)
	ok(back >= 0 and (crowd.flags[back] & 2) == 0, "walking away demotes the locked body")
	ok(crowd.lock_t[back] > 3.5, "demotion keeps the remaining cooldown (%.2f)" % crowd.lock_t[back])
	m.hero.global_position = Vector3(0.6, 1.0, 210.0)
	for _i in 6: await physics_frame
	back = crowd._index_of(sim)
	ok((crowd.flags[back] & 2) != 0, "returning promotes the same id again")
	body = crowd.pool[crowd.pool_i[back]]
	ok(body.crowd_id == sim and body.crowd_lock > 3.0, "the second promotion still carries the cooldown (%.2f)" % body.crowd_lock)
	var hp1: float = m.party.combat.hp
	for _i in 40: await physics_frame
	ok(is_equal_approx(m.party.combat.hp, hp1), "the re-promoted body still cannot bite early")
	body.crowd_lock = 0.0
	body.state = "approach"
	body.t_state = 0.0
	body.pending_kind = ""
	for _i in 50: await physics_frame
	ok(m.party.combat.hp < hp1, "clearing the cooldown lets that body bite (hp %.0f)" % m.party.combat.hp)
	var alive_before := crowd.id_alive(sim)
	body.kill_now(Vector3.ZERO)
	for _i in 20: await physics_frame
	ok(alive_before and not crowd.id_alive(sim) and crowd.retired.has(sim), "killing the body retires the id")

func _packed(m, crowd: HordeCrowd) -> void:
	_park(crowd, 500.0)
	m.hero.global_position = Vector3(0, 1.0, 210)
	m.party.combat.hp = m.party.combat.max_hp
	for _i in 2: await physics_frame
	var placed := _stack(crowd, m.hero.global_position, 200)
	ok(placed == 200, "200 unpromoted records start inside 0.4 m (%d)" % placed)
	ok(_piled(crowd, m.hero.global_position, 0.4) == 200, "the pack is really piled before physics")
	var bites0: int = crowd.bites
	var hp0: float = m.party.combat.hp
	await physics_frame
	ok(crowd.bites == bites0 and is_equal_approx(m.party.combat.hp, hp0), "the piled crowd does not bite on the first frame")
	var prev_b := crowd.bites
	var prev_h: float = m.party.combat.hp
	var max_b := 0
	var max_drop := 0.0
	for _i in 90:
		await physics_frame
		max_b = maxi(max_b, crowd.bites - prev_b)
		max_drop = maxf(max_drop, prev_h - m.party.combat.hp)
		prev_b = crowd.bites
		prev_h = m.party.combat.hp
	var piled := _piled(crowd, m.hero.global_position, 0.4)
	print("PACKED bites=%d max_per_frame=%d max_hp_drop=%.0f piled=%d hp %.0f->%.0f near=%d" % [crowd.bites - bites0, max_b, max_drop, piled, hp0, m.party.combat.hp, crowd.near_n])
	ok(max_b <= HordeCrowd.MAX_CONTACT, "record bites in one frame stay within the contact cap (%d)" % max_b)
	ok(max_drop <= float(HordeCrowd.MAX_CONTACT) * 30.0, "one frame cannot dump the whole pack onto the hero (%.0f)" % max_drop)
	ok(crowd.bites - bites0 <= HordeCrowd.MAX_CONTACT * 3, "the pack does not volley every piled body (%d bites)" % (crowd.bites - bites0))
	ok(m.party.combat.hp < hp0 and m.party.combat.hp > 80.0, "the horde still hurts, and it does not erase the hero (%.0f -> %.0f)" % [hp0, m.party.combat.hp])
	ok(piled <= 2, "separation breaks the 0.4 m pile (%d still inside)" % piled)
	ok(crowd.near_n <= HordeCrowd.NEAR_CAP, "the pack still promotes only the near pool (%d)" % crowd.near_n)
	ok(crowd.inside_count() == 0, "the outside pack never enters the haven")

func _elevated(m, crowd: HordeCrowd) -> void:
	_park(crowd, 500.0)
	m.hero.global_position = Vector3(0, 40.0, 210)
	for _i in 3: await physics_frame
	var placed := _stack(crowd, Vector3(0, 0, 210), 200)
	ok(placed == 200, "200 records sit under the elevated hero")
	m.party.combat.hp = m.party.combat.max_hp
	var hp0: float = m.party.combat.hp
	var bites0: int = crowd.bites
	for _i in 70: await physics_frame
	print("ELEVATED bites=%d hp %.0f" % [crowd.bites - bites0, m.party.combat.hp])
	ok(crowd.bites == bites0 and is_equal_approx(m.party.combat.hp, hp0), "40 m up is outside bite height")

func _inside(m, crowd: HordeCrowd) -> void:
	_park(crowd, 500.0)
	m.hero.global_position = Vector3(0, 1.0, 24)
	for _i in 3: await physics_frame
	var placed := _stack(crowd, m.hero.global_position, 200)
	ok(placed == 200, "200 records are stacked on the hero inside town")
	m.party.combat.hp = m.party.combat.max_hp
	var hp0: float = m.party.combat.hp
	var bites0: int = crowd.bites
	for _i in 45: await physics_frame
	print("INSIDE bites=%d hp %.0f" % [crowd.bites - bites0, m.party.combat.hp])
	ok(crowd.bites == bites0 and is_equal_approx(m.party.combat.hp, hp0), "a packed crowd cannot bite inside the haven")

func _quiet(m, crowd: HordeCrowd) -> Vector3:
	_park(crowd, 700.0)
	var at := Vector3(220.0, 1.0, -80.0)
	m.hero.global_position = at
	for _i in 2: await physics_frame
	return m.hero.global_position

func _free_index(crowd: HordeCrowd) -> int:
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		return i
	return -1

func _obstacle(m, crowd: HordeCrowd) -> void:
	var hero_at := await _quiet(m, crowd)
	var idx := _free_index(crowd)
	ok(idx >= 0, "a record is free for the slab")
	if idx < 0: return
	m.hero.global_position = Vector3(0, 1.0, 200.0)
	crowd.px[idx] = 0.0
	crowd.pz[idx] = 201.35
	crowd.hold_x[idx] = 0.0
	crowd.hold_z[idx] = 200.0
	crowd.wind_t[idx] = 0.0
	crowd.lock_t[idx] = 0.0
	crowd.hp[idx] = 190.0
	TownHaven.add_obstacle(Rect2(-3.0, 200.45, 6.0, 0.4))
	var blocked: bool = not TownHaven.strike_allowed(Vector3(0, 0, 201.35), m.hero.global_position, "bite")
	ok(blocked, "the slab is between the record and the hero")
	m.party.combat.hp = m.party.combat.max_hp
	var hp0: float = m.party.combat.hp
	var bites0: int = crowd.bites
	for _i in 40: await physics_frame
	print("SLAB bites=%d z=%.2f hp %.0f" % [crowd.bites - bites0, crowd.pz[idx], m.party.combat.hp])
	ok(crowd.bites == bites0 and is_equal_approx(m.party.combat.hp, hp0), "a bite does not pass through the slab")
	ok(crowd.pz[idx] > 200.9, "the record does not walk through the slab (z %.2f)" % crowd.pz[idx])
	TownHaven.clear_obstacles()
	crowd.px[idx] = 0.0
	crowd.pz[idx] = 201.35
	crowd.wind_t[idx] = 0.0
	crowd.lock_t[idx] = 0.0
	if (crowd.flags[idx] & 2) != 0 and crowd.pool_i[idx] >= 0:
		var slab_body: HordeZombie = crowd.pool[crowd.pool_i[idx]]
		slab_body.global_position = Vector3(0, 0.2, 201.35)
		slab_body.crowd_lock = 0.0
		slab_body.state = "approach"
		slab_body.pending_kind = ""
	for _i in 120: await physics_frame
	ok(m.party.combat.hp < hp0, "without the slab the same spacing bites (hp %.0f)" % m.party.combat.hp)
	m.hero.global_position = hero_at

func _haven_plant(m, crowd: HordeCrowd) -> void:
	await _quiet(m, crowd)
	var idx := _free_index(crowd)
	ok(idx >= 0, "a record is free to plant in the harbour")
	if idx < 0: return
	m.hero.global_position = Vector3(-452.6, 1.0, 400.0)
	crowd.px[idx] = -451.2
	crowd.pz[idx] = 400.0
	crowd.hold_x[idx] = -451.2
	crowd.hold_z[idx] = 400.0
	crowd.wind_t[idx] = 0.0
	crowd.lock_t[idx] = 0.0
	ok(TownHaven.body_inside(Vector2(-451.2, 400.0), HordeZombie.BODY_R), "the planted record starts inside the haven")
	ok(not TownHaven.strike_allowed(Vector3(-451.2, 0, 400), m.hero.global_position, "bite"), "a haven source cannot strike an outside hero")
	m.party.combat.hp = m.party.combat.max_hp
	var hp0: float = m.party.combat.hp
	var bites0: int = crowd.bites
	await physics_frame
	ok(crowd.bites == bites0 and is_equal_approx(m.party.combat.hp, hp0), "the planted record does not bite before it is expelled")
	for _i in 8: await physics_frame
	print("HAVEN_PLANT bites=%d pos (%.1f, %.1f) inside %s" % [crowd.bites - bites0, crowd.px[idx], crowd.pz[idx], TownHaven.body_inside(Vector2(crowd.px[idx], crowd.pz[idx]), HordeZombie.BODY_R)])
	ok(crowd.bites == bites0 and is_equal_approx(m.party.combat.hp, hp0), "the planted record still has not bitten")
	ok(not TownHaven.body_inside(Vector2(crowd.px[idx], crowd.pz[idx]), HordeZombie.BODY_R), "the planted record is expelled from the haven")

func _expect_dry(crowd: HordeCrowd, idx: int, label: String) -> void:
	var p := Vector2(crowd.px[idx], crowd.pz[idx])
	var sea: bool = crowd.on_sea(p.x, p.y)
	var inside: bool = TownHaven.body_inside(p, HordeZombie.BODY_R)
	print("DRY %s (%.1f, %.1f) sea %s inside %s" % [label, p.x, p.y, sea, inside])
	ok(not sea and not inside, "%s lands on dry ground outside the haven (%.1f, %.1f)" % [label, p.x, p.y])

func _plant_sea(crowd: HordeCrowd, idx: int, at: Vector2) -> void:
	crowd.px[idx] = at.x
	crowd.pz[idx] = at.y
	crowd.hold_x[idx] = at.x
	crowd.hold_z[idx] = at.y
	crowd.wind_t[idx] = 0.0
	crowd.lock_t[idx] = 0.0

func _sea_plant(m, crowd: HordeCrowd) -> void:
	await _quiet(m, crowd)
	m.hero.global_position = Vector3(200, 1, -200)
	var spots: Array[Vector2] = [Vector2(-500, 360), Vector2(-1200, 800), Vector2(-2000, 2200), Vector2(-430, 400)]
	var labels := ["sea -500,360", "far sea -1200,800", "far sea -2000,2200", "waterfront -430,400"]
	for s in spots.size():
		var idx := _free_index(crowd)
		ok(idx >= 0, "a record is free for %s" % labels[s])
		if idx < 0: return
		_plant_sea(crowd, idx, spots[s])
		var bites0: int = crowd.bites
		var hp0: float = m.party.combat.hp
		for _f in 2: await physics_frame
		_expect_dry(crowd, idx, labels[s])
		ok(crowd.bites == bites0 and is_equal_approx(m.party.combat.hp, hp0), "%s does not bite while it is corrected" % labels[s])
		ok(Vector2(crowd.px[idx], crowd.pz[idx]).distance_to(spots[s]) > 2.0, "%s does not stay on the illegal point" % labels[s])
	var coast := float(load("res://scripts/main.gd").coast_x(520.0))
	var walker := _free_index(crowd)
	ok(walker >= 0, "a record is free for the land march")
	if walker < 0: return
	var start := Vector2(coast - 1.0, 520.0)
	_plant_sea(crowd, walker, start)
	crowd.hold_x[walker] = coast - 40.0
	crowd.hold_z[walker] = 520.0
	for _i in 2: await physics_frame
	ok(not crowd.on_sea(crowd.px[walker], crowd.pz[walker]) and not TownHaven.body_inside(Vector2(crowd.px[walker], crowd.pz[walker]), HordeZombie.BODY_R), "the march starts on dry ground outside the haven (%.1f, %.1f)" % [crowd.px[walker], crowd.pz[walker]])
	var x0: float = crowd.px[walker]
	for _i in 180: await physics_frame
	print("LAND_MARCH (%.1f, %.1f) from %.1f coast %.1f sea %s" % [crowd.px[walker], crowd.pz[walker], x0, coast, crowd.on_sea(crowd.px[walker], crowd.pz[walker])])
	ok(crowd.px[walker] < x0 - 0.4, "the land march actually moves toward the sea (%.2f -> %.2f)" % [x0, crowd.px[walker]])
	ok(not crowd.on_sea(crowd.px[walker], crowd.pz[walker]), "the land march stops on the shore (%.1f, %.1f)" % [crowd.px[walker], crowd.pz[walker]])
	ok(not TownHaven.body_inside(Vector2(crowd.px[walker], crowd.pz[walker]), HordeZombie.BODY_R), "the land march stays outside the haven")

func _promoted_invalid(m, crowd: HordeCrowd) -> void:
	await _quiet(m, crowd)
	for g in m.guards.guards:
		g.down_t = 999.0
		g.tgt = null
	var idx := _free_index(crowd)
	ok(idx >= 0, "a record can be promoted for the invalid-body checks")
	if idx < 0: return
	var shore := Vector2(-389.6, 360.0)
	m.hero.global_position = Vector3(shore.x, 1.0, shore.y)
	crowd.px[idx] = shore.x + 1.0
	crowd.pz[idx] = shore.y
	crowd.hold_x[idx] = crowd.px[idx]
	crowd.hold_z[idx] = crowd.pz[idx]
	crowd.hp[idx] = 150.0
	crowd.lock_t[idx] = 5.0
	crowd.wind_t[idx] = 0.2
	var sim := int(crowd.id[idx])
	ok(crowd._promote_index(idx, m.hero.global_position), "the shore record promotes")
	var body: HordeZombie = crowd.pool[crowd.pool_i[idx]]
	for _i in 20: await physics_frame
	var drifted := Vector2(body.global_position.x, body.global_position.z).distance_to(Vector2(shore.x + 1.0, shore.y))
	print("PROMOTED_SHORE (%.1f, %.1f) drift %.2f lock %.2f" % [body.global_position.x, body.global_position.z, drifted, body.crowd_lock])
	ok(drifted < 6.0, "a valid shore body is not teleported (%.2f m)" % drifted)
	ok(not crowd.on_sea(body.global_position.x, body.global_position.z), "the valid shore body stays on land")
	ok(not TownHaven.body_inside(Vector2(body.global_position.x, body.global_position.z), HordeZombie.BODY_R), "the valid shore body stays outside the haven")
	ok(body.crowd_id == sim and crowd.id[idx] == sim, "the shore body keeps its id")
	body.global_position = Vector3(-500, body.global_position.y, 360)
	body.crowd_lock = 5.0
	crowd.lock_t[idx] = 5.0
	body.hp = 150.0
	crowd.hp[idx] = 150.0
	for _i in 2: await physics_frame
	var bp := Vector2(body.global_position.x, body.global_position.z)
	var rp := Vector2(crowd.px[idx], crowd.pz[idx])
	print("PROMOTED_SEA body (%.1f, %.1f) record (%.1f, %.1f) lock %.2f hp %.0f" % [bp.x, bp.y, rp.x, rp.y, body.crowd_lock, body.hp])
	ok(not crowd.on_sea(bp.x, bp.y) and not crowd.on_sea(rp.x, rp.y), "a promoted sea plant is dry on both the body and the record")
	ok(not TownHaven.body_inside(bp, HordeZombie.BODY_R) and not TownHaven.body_inside(rp, HordeZombie.BODY_R), "a promoted sea plant is outside the haven on both sides")
	ok(bp.distance_to(rp) < 1.5, "the body and the record do not split after the sea correction (%.2f m)" % bp.distance_to(rp))
	ok(body.crowd_id == sim and crowd.id_alive(sim), "the sea correction keeps the same id")
	ok(is_equal_approx(body.hp, 150.0) and is_equal_approx(crowd.hp[idx], 150.0), "the sea correction keeps HP")
	ok(body.crowd_lock > 4.5, "the sea correction keeps the cooldown (%.2f)" % body.crowd_lock)
	var prom := (crowd.flags[idx] & 2) != 0
	var flips := 0
	for _i in 8:
		await physics_frame
		var now := (crowd.flags[idx] & 2) != 0
		if now != prom:
			flips += 1
			prom = now
	ok(flips <= 1, "promotion does not oscillate after the sea correction (%d flips)" % flips)
	ok(not crowd.on_sea(crowd.px[idx], crowd.pz[idx]), "the record is still dry after the sea correction settles")
	m.hero.global_position = Vector3(-389.6, 1.0, 400.0)
	body.global_position = Vector3(-430, body.global_position.y, 400)
	body.crowd_lock = 5.0
	body.hp = 150.0
	for _i in 2: await physics_frame
	bp = Vector2(body.global_position.x, body.global_position.z)
	var back := crowd._index_of(sim)
	ok(back >= 0, "the haven plant still has its record")
	if back < 0: return
	rp = Vector2(crowd.px[back], crowd.pz[back])
	print("PROMOTED_HAVEN body (%.1f, %.1f) record (%.1f, %.1f)" % [bp.x, bp.y, rp.x, rp.y])
	ok(not crowd.on_sea(bp.x, bp.y) and not crowd.on_sea(rp.x, rp.y), "a promoted haven plant is dry on both sides")
	ok(not TownHaven.body_inside(bp, HordeZombie.BODY_R) and not TownHaven.body_inside(rp, HordeZombie.BODY_R), "a promoted haven plant is outside the haven on both sides")
	ok(bp.distance_to(rp) < 1.5, "the body and the record match after the haven correction")
	ok(crowd.id[back] == sim and is_equal_approx(body.hp, 150.0), "the haven correction keeps id and HP")
	ok(body.crowd_lock > 4.5, "the haven correction keeps the cooldown (%.2f)" % body.crowd_lock)
	m.hero.global_position = Vector3(220, 1, -80)
	for _i in 12: await physics_frame
	back = crowd._index_of(sim)
	ok(back >= 0 and (crowd.flags[back] & 2) == 0, "walking away demotes the corrected body")
	ok(not crowd.on_sea(crowd.px[back], crowd.pz[back]) and not TownHaven.body_inside(Vector2(crowd.px[back], crowd.pz[back]), HordeZombie.BODY_R), "the demoted record stays on dry ground outside the haven")
	ok(crowd.id_alive(sim) and is_equal_approx(crowd.hp[back], 150.0), "demotion keeps the same id and HP")
	m.hero.global_position = Vector3(crowd.px[back], 1.0, crowd.pz[back])
	for _i in 8: await physics_frame
	back = crowd._index_of(sim)
	ok(back >= 0 and (crowd.flags[back] & 2) != 0, "returning promotes the same id again")
	var again: HordeZombie = crowd.pool[crowd.pool_i[back]]
	ok(again.crowd_id == sim, "the new body is the same crowd id")
	ok(not crowd.on_sea(again.global_position.x, again.global_position.z) and not TownHaven.body_inside(Vector2(again.global_position.x, again.global_position.z), HordeZombie.BODY_R), "the re-promoted body is still on dry ground outside the haven")

func _slots(m, crowd: HordeCrowd) -> void:
	await _quiet(m, crowd)
	for g in m.guards.guards:
		g.down_t = 999.0
		g.tgt = null
	m.hero.global_position = Vector3(0, 1.0, 200)
	m.party.combat.hp = m.party.combat.max_hp
	var ring: Array[int] = []
	var placed := 0
	for i in crowd.id.size():
		if placed >= 24: break
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		var ang := float(placed) / 24.0 * TAU
		crowd.px[i] = m.hero.global_position.x + cos(ang) * 1.0
		crowd.pz[i] = m.hero.global_position.z + sin(ang) * 1.0
		crowd.hold_x[i] = crowd.px[i]
		crowd.hold_z[i] = crowd.pz[i]
		crowd.wind_t[i] = 0.0
		crowd.lock_t[i] = 0.0
		crowd.hp[i] = 190.0
		ring.append(i)
		placed += 1
	ok(placed == 24, "24 attackers stand in bite range (%d)" % placed)
	var max_imp := 0
	var total := 0
	var near_peak := 0
	for _i in 180:
		await physics_frame
		max_imp = maxi(max_imp, crowd.impacts_frame)
		total += crowd.impacts_frame
		near_peak = maxi(near_peak, crowd.near_n)
	print("SLOTS frames=180 max_impacts=%d total=%d near_peak=%d hp %.0f" % [max_imp, total, near_peak, m.party.combat.hp])
	ok(max_imp <= HordeCrowd.MAX_CONTACT, "bodies and records together stay within 4 impacts in one frame (%d)" % max_imp)
	ok(max_imp > 0 and total > 0 and m.party.combat.hp < m.party.combat.max_hp, "the shared slots still land hits (total %d)" % total)
	ok(near_peak == HordeCrowd.NEAR_CAP and crowd.near_n == HordeCrowd.NEAR_CAP, "the fight fills the body pool (%d)" % crowd.near_n)
	var killed: Array[int] = []
	var bodies := 0
	var loose := 0
	for i in ring:
		if not crowd.id_alive(int(crowd.id[i])): continue
		if (crowd.flags[i] & 2) != 0 and bodies < 2:
			killed.append(int(crowd.id[i]))
			crowd.kill_id(int(crowd.id[i]))
			bodies += 1
		elif (crowd.flags[i] & 2) == 0 and loose < 1:
			killed.append(int(crowd.id[i]))
			crowd.kill_id(int(crowd.id[i]))
			loose += 1
	ok(bodies == 2 and loose == 1, "two bodies and one record were killed")
	for _i in 40: await physics_frame
	var held := true
	for sim in killed:
		if crowd.id_alive(sim) or not crowd.retired.has(sim): held = false
	print("SLOT_DEATH held %s near %d" % [held, crowd.near_n])
	ok(held, "killed crowd ids stay retired")
	ok(crowd.near_n == HordeCrowd.NEAR_CAP, "a freed body slot is filled from the ring (%d)" % crowd.near_n)
	var before: int = crowd.impacts_total
	m.hero.global_position = Vector3(0, 1.0, 24)
	for _i in 25: await physics_frame
	ok(crowd.near_n == 0, "leaving the press demotes the pool (%d)" % crowd.near_n)
	ok(crowd.impacts_total == before, "no horde impact lands after the hero is inside")
	ok(crowd.inside_count() == 0, "the ring never enters the town")

func _respawn(m, crowd: HordeCrowd) -> void:
	await _quiet(m, crowd)
	var shore := Vector3(-370.0, 0.0, 280.0)
	var body = m.horde.respawn_at("shambler", shore)
	ok(body != null, "a shore respawn returns a body")
	if body != null:
		var at := Vector2(body.global_position.x, body.global_position.z)
		print("RESPAWN_SHORE (%.1f, %.1f) id %s" % [at.x, at.y, body.crowd_id])
		ok(at.distance_to(Vector2(shore.x, shore.z)) < 4.0, "the shore body stands on the requested ground (%.1f, %.1f)" % [at.x, at.y])
		ok(at.distance_to(Vector2(7.7, 204.5)) > 80.0, "the shore body is not the south-gate formation")
		ok(not TownHaven.body_inside(at, HordeZombie.BODY_R), "the shore body is outside the haven")
	var door := Vector3(-440.2, 0.0, 453.3)
	var light = m.horde.respawn_at("shambler", door)
	ok(light != null, "a lighthouse respawn returns a body")
	if light != null:
		var at2 := Vector2(light.global_position.x, light.global_position.z)
		print("RESPAWN_LIGHT (%.1f, %.1f)" % [at2.x, at2.y])
		ok(not TownHaven.body_inside(at2, HordeZombie.BODY_R), "the lighthouse body is pushed outside the tower haven")
		ok(not crowd.on_sea(at2.x, at2.y), "the lighthouse body is not left in the sea")
		ok(at2.distance_to(Vector2(7.7, 204.5)) > 80.0, "the lighthouse body is not redirected to the south gate")
		ok(at2.distance_to(Vector2(door.x, door.z)) < 80.0, "the lighthouse body stays near the requested door (%.1f m)" % at2.distance_to(Vector2(door.x, door.z)))

func _player_hits(m, crowd: HordeCrowd) -> void:
	var hero_at := await _quiet(m, crowd)
	var hero := Vector2(hero_at.x, hero_at.z)
	var close := _free_index(crowd)
	var far := -1
	for i in crowd.id.size():
		if i == close or (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		far = i
		break
	ok(close >= 0 and far >= 0, "two records are clear of the formation")
	if close < 0 or far < 0: return
	crowd.px[close] = hero.x
	crowd.pz[close] = hero.y + 2.0
	crowd.hp[close] = 190.0
	crowd.px[far] = hero.x
	crowd.pz[far] = hero.y + 8.0
	crowd.hp[far] = 190.0
	var close_id := int(crowd.id[close])
	var far_hp: float = crowd.hp[far]
	var ranged := {"kind": "ranged", "range": 20.0, "id": "probe.ranged", "mult": 1.0}
	var picked := crowd.nearest_unpromoted(hero, 21.0)
	ok(picked == close, "the closer unpromoted record is the ranged candidate")
	m.party.combat._resolve(1, ranged)
	print("RANGED close_alive %s hp %s far_hp %.0f" % [crowd.id_alive(close_id), crowd.hp[close] if close < crowd.hp.size() else -1, crowd.hp[far]])
	ok(crowd.hp[close] < 190.0, "ranged damages the closer unpromoted record (%.0f)" % crowd.hp[close])
	ok(is_equal_approx(crowd.hp[far], far_hp), "the farther record is not hit by that shot")
	var body_i := far
	var rec := _free_index(crowd)
	ok(rec >= 0, "a record remains beside the promoted body")
	if rec < 0: return
	crowd.px[body_i] = hero.x
	crowd.pz[body_i] = hero.y + 2.0
	crowd.hp[body_i] = 190.0
	crowd.px[rec] = hero.x
	crowd.pz[rec] = hero.y + 8.0
	crowd.hp[rec] = 190.0
	var rec_hp: float = crowd.hp[rec]
	ok(crowd._promote_index(body_i, m.hero.global_position), "the nearer zombie is promoted")
	var body: HordeZombie = crowd.pool[crowd.pool_i[body_i]]
	body.global_position = Vector3(hero.x, 0.0, hero.y + 2.0)
	body.hp = 190.0
	crowd.hp[body_i] = 190.0
	m.party.combat._resolve(1, ranged)
	await physics_frame
	print("RANGED_BODY hp %.0f record %.0f" % [body.hp, crowd.hp[rec]])
	ok(body.hp < 190.0 or not body.alive(), "ranged hits the closer body (%.0f)" % body.hp)
	ok(is_equal_approx(crowd.hp[rec], rec_hp), "the farther unpromoted record stays at 190 when the body is closer")
	rec = _free_index(crowd)
	ok(rec >= 0 and (crowd.flags[rec] & 2) == 0, "melee still has an unpromoted record")
	if rec < 0: return
	crowd.px[rec] = hero.x
	crowd.pz[rec] = hero.y + 1.5
	crowd.hp[rec] = 190.0
	crowd.hold_x[rec] = crowd.px[rec]
	crowd.hold_z[rec] = crowd.pz[rec]
	var melee := {"kind": "melee", "range": 6.0, "arc": -1.0}
	var melee_before: float = crowd.hp[rec]
	m.party.combat._area(melee, 0, hero, Vector2(0, 1), 1.0)
	var melee_mid: float = crowd.hp[rec]
	ok(melee_mid < melee_before, "melee hits the unpromoted record (%.0f -> %.0f)" % [melee_before, melee_mid])
	m.party.combat._area(melee, 0, hero, Vector2(0, 1), 1.0)
	ok(crowd.hp[rec] < melee_mid, "a second melee hits that record again (%.0f)" % crowd.hp[rec])
	var one_swing := melee_before - melee_mid
	var two_swing := melee_before - crowd.hp[rec]
	ok(two_swing < one_swing * 3.5, "two melees are two hits, not a stacked application (%.0f vs %.0f)" % [one_swing, two_swing])
	for z in crowd.pool:
		if z.crowd_id >= 0: z.global_position = Vector3(500, 0, 500)
	var blink_i := _free_index(crowd)
	ok(blink_i >= 0, "a record remains for blink")
	if blink_i < 0: return
	crowd.px[blink_i] = hero.x + 4.0
	crowd.pz[blink_i] = hero.y
	crowd.hp[blink_i] = 190.0
	var blink_id := int(crowd.id[blink_i])
	var blink := {"kind": "blink", "range": 14.0, "id": "probe.blink", "mult": 1.0}
	var blink_hp: float = crowd.hp[blink_i]
	m.party.combat._resolve(1, blink)
	ok(not crowd.id_alive(blink_id) or crowd.hp[blink_i] < blink_hp, "blink strikes the unpromoted record it lands on")
	ok(m.hero.global_position.distance_to(Vector3(hero.x + 4.0, m.hero.global_position.y, hero.y)) < 3.0, "blink moves to that record")
