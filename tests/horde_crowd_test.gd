extends SceneTree
## Identity, haven clamp, and near-actor handoff. Headless. Not a phone result.
## godot --headless --path . -s res://tests/horde_crowd_test.gd
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
	var crowd: HordeCrowd = m.horde.crowd
	ok(crowd.alive_n == HordeCrowd.SIM_DEFAULT, "default simulated count is %d" % crowd.alive_n)
	ok(crowd.near_n <= HordeCrowd.NEAR_CAP, "near pool starts within cap (%d)" % crowd.near_n)
	var ids := {}
	var dup := 0
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0: continue
		if ids.has(crowd.id[i]): dup += 1
		ids[crowd.id[i]] = true
	ok(dup == 0 and ids.size() == crowd.alive_n, "every living zombie has its own id (%d)" % ids.size())
	ok(crowd.inside_count() == 0 and crowd.wedge_count() == 0, "boot positions stay outside the haven and the escape wedge")
	var victim := int(crowd.id[0])
	var victim_hp := crowd.hp[0]
	crowd.kill_id(victim)
	ok(not crowd.id_alive(victim) and crowd.retired.has(victim), "a death retires that id")
	for _i in 30: await physics_frame
	ok(not crowd.id_alive(victim), "the retired id is not alive after later frames")
	var revived := false
	for i in crowd.id.size():
		if crowd.id[i] == victim and (crowd.flags[i] & 1) != 0: revived = true
	ok(not revived, "that id was not reused")
	var actor: HordeZombie = crowd.deploy_actor("shambler")
	ok(actor != null and actor.crowd_id > 0, "promotion hands a stable id to a body")
	var sim_id := actor.crowd_id
	var idx := crowd._index_of(sim_id)
	actor.hp = maxf(1.0, actor.hp - 40.0)
	await physics_frame
	ok(absf(crowd.hp[idx] - actor.hp) < 0.1, "damage on the body is the same record (%.0f vs %.0f)" % [crowd.hp[idx], actor.hp])
	var kept := Vector2(actor.global_position.x, actor.global_position.z)
	m.hero.global_position = Vector3(0, 1, 20)
	for _i in 5: await physics_frame
	var after := crowd._index_of(sim_id)
	ok(after >= 0 and crowd.id_alive(sim_id), "moving the player away keeps the same id")
	ok(Vector2(crowd.px[after], crowd.pz[after]).distance_to(kept) < 30.0, "demotion keeps the place the body had")
	var pushed := -1
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		pushed = i
		break
	crowd.hold_x[pushed] = 0.0
	crowd.hold_z[pushed] = 0.0
	crowd.px[pushed] = 0.0
	crowd.pz[pushed] = TownHaven.outer_limit() + 2.0
	for _i in 40: await physics_frame
	ok(not TownHaven.body_inside(Vector2(crowd.px[pushed], crowd.pz[pushed]), HordeZombie.BODY_R), "a march into town is stopped outside (%.1f, %.1f)" % [crowd.px[pushed], crowd.pz[pushed]])
	await _near_cycle(m, crowd)
	await _hits(m, crowd)
	await _guards(m, crowd)
	await _blocked(m, crowd)
	await _sustain(m, crowd)
	print("CROWD_LOGIC %d checks, %d failed near=%d rendered=%d simulated=%d" % [n, fails, crowd.near_n, crowd.rendered_n, crowd.alive_n])
	quit(1 if fails else 0)

func _near_cycle(m, crowd: HordeCrowd) -> void:
	m.hero.global_position = Vector3(0, 1.0, 198)
	for _i in 45: await physics_frame
	print("NEAR_OUTSIDE near=%d rendered=%d simulated=%d" % [crowd.near_n, crowd.rendered_n, crowd.alive_n])
	ok(crowd.near_n == HordeCrowd.NEAR_CAP, "standing in the south press promotes the full pool (%d)" % crowd.near_n)
	var tracked: Array = []
	for i in crowd.id.size():
		if (crowd.flags[i] & 2) == 0: continue
		tracked.append({"id": crowd.id[i], "hp": crowd.hp[i], "x": crowd.px[i], "z": crowd.pz[i]})
	ok(tracked.size() == HordeCrowd.NEAR_CAP, "tracked every promoted id")
	var focus: Dictionary = tracked[0]
	var actor: HordeZombie = null
	for z in crowd.pool:
		if z.crowd_id == int(focus.id): actor = z
	ok(actor != null, "the focused id has a body")
	if actor == null: return
	actor.hp = maxf(1.0, actor.hp - 25.0)
	var hurt := actor.hp
	m.hero.global_position = Vector3(0, 1.0, 30)
	for _i in 20: await physics_frame
	var back := crowd._index_of(int(focus.id))
	ok(crowd.near_n == 0, "back inside town, the pool is clear (%d)" % crowd.near_n)
	ok(back >= 0 and crowd.id_alive(int(focus.id)), "demotion keeps the id")
	ok(absf(crowd.hp[back] - hurt) < 0.2, "demotion keeps the wounded hp (%.0f)" % crowd.hp[back])
	ok(not TownHaven.inside(Vector3(crowd.px[back], 0, crowd.pz[back])), "demotion does not drop the body inside town (%.1f, %.1f)" % [crowd.px[back], crowd.pz[back]])
	m.hero.global_position = Vector3(crowd.px[back], 1.0, crowd.pz[back] - 6.0)
	for _i in 30: await physics_frame
	var again := crowd._index_of(int(focus.id))
	ok(again >= 0 and (crowd.flags[again] & 2) != 0, "a second approach promotes the same id")
	ok(absf(crowd.hp[again] - hurt) < 1.0, "the second promotion still has the wound")
	m.hero.global_position = Vector3(0, 1.0, 24)
	for _i in 15: await physics_frame
	ok(crowd.id_alive(int(focus.id)) and crowd.near_n == 0, "the second return clears the pool and keeps the id")

func _hits(m, crowd: HordeCrowd) -> void:
	for g in m.guards.guards:
		g.down_t = 60.0
		g.tgt = null
	var stand := TownHaven.stand_off(HordeZombie.BODY_R)
	var actor: HordeZombie = crowd.deploy_actor("shambler")
	ok(actor != null, "a shambler is deployed for the bite")
	if actor == null: return
	actor.global_position = Vector3(0, 0.2, stand + 0.35)
	actor.last_safe = actor.global_position
	m.hero.global_position = Vector3(0.2, 0.2, stand + 1.15)
	m.party.combat.hp = m.party.combat.max_hp
	var hp_out: float = m.party.combat.hp
	for _i in 90: await physics_frame
	ok(m.party.combat.hp < hp_out, "horde melee lands outside (%.0f -> %.0f)" % [hp_out, m.party.combat.hp])
	var mid: float = m.party.combat.hp
	m.hero.global_position = Vector3(0.2, 0.2, 30)
	for _i in 40: await physics_frame
	ok(is_equal_approx(m.party.combat.hp, mid), "the same melee does not land inside")
	actor = crowd.deploy_actor("shambler")
	ok(actor != null and actor.crowd_id > 0, "a body is promoted again for the hero swing")
	if actor == null: return
	actor.global_position = Vector3(0, 0.2, stand + 0.4)
	m.hero.global_position = actor.global_position + Vector3(0, 0, 1.0)
	var body_i := crowd._index_of(actor.crowd_id)
	var rec_before: float = actor.hp
	var neighbor := -1
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		neighbor = i
		crowd.px[i] = actor.global_position.x + 1.5
		crowd.pz[i] = actor.global_position.z
		break
	ok(neighbor >= 0, "a simulated record is placed in the swing")
	var neigh_before: float = crowd.hp[neighbor] if neighbor >= 0 else 0.0
	var hits := [0]
	m.party.combat.damaged_enemy.connect(func(e, _d, _c):
		if e == actor: hits[0] += 1)
	var sk := {"range": 30.0, "arc": -1.0}
	m.party.combat._area(sk, 0, Vector2(m.hero.global_position.x, m.hero.global_position.z), Vector2(0, -1), 1.0)
	for _i in 2: await physics_frame
	ok(hits[0] == 1, "the pooled body is damaged once (%d signals)" % hits[0])
	if body_i >= 0:
		ok(absf(crowd.hp[body_i] - actor.hp) < 0.2, "the record matches the body after one swing (%.0f vs %.0f)" % [crowd.hp[body_i], actor.hp])
		ok(crowd.hp[body_i] < rec_before, "the swing actually wounded the body record")
	if neighbor >= 0:
		ok(crowd.hp[neighbor] < neigh_before and crowd.hp[neighbor] > neigh_before - 400.0, "the nearby record lost one hit (%.0f -> %.0f)" % [neigh_before, crowd.hp[neighbor]])
	var ult_i := -1
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		ult_i = i
		break
	ok(ult_i >= 0, "an unpromoted record is still alive for the ultimate")
	if ult_i >= 0:
		var ult_id := int(crowd.id[ult_i])
		crowd.px[ult_i] = actor.global_position.x + 1.0
		crowd.pz[ult_i] = actor.global_position.z
		var killed: int = crowd.kill_disk(Vector2(actor.global_position.x, actor.global_position.z), 6.0)
		ok(killed >= 1, "the ultimate disk hit the pinned record once (%d)" % killed)
		ok(not crowd.id_alive(ult_id) and crowd.retired.has(ult_id), "that disk retires the id")
		var again: int = crowd.kill_disk(Vector2(actor.global_position.x, actor.global_position.z), 6.0)
		ok(again == 0, "a second disk does not hit the retired id")

func _guards(m, crowd: HordeCrowd) -> void:
	for g in m.guards.guards:
		g.down_t = 0.0
		g.tgt = null
		g.hp = TownGuards.MAX_HP
	m.hero.global_position = Vector3(0, 1.0, 192)
	for _i in 90: await physics_frame
	var busy := 0
	var horde_tgt := 0
	var far := 0.0
	for g in m.guards.guards:
		var d: float = (g.node as Node3D).global_position.distance_to(g.post)
		far = maxf(far, d)
		if g.tgt != null:
			busy += 1
			if g.tgt is HordeZombie: horde_tgt += 1
	print("GUARD_CROWD busy=%d horde_tgt=%d farthest=%.2f near=%d" % [busy, horde_tgt, far, crowd.near_n])
	ok(horde_tgt > 0, "guards take nearby crowd bodies (%d)" % horde_tgt)
	ok(far <= TownGuards.POST_LEASH + 0.5, "those guards stay inside the apron (%.2f m)" % far)
	ok(crowd.near_n <= HordeCrowd.NEAR_CAP, "combat bodies stay at the pool cap during the fight")

func _blocked(m, crowd: HordeCrowd) -> void:
	TownHaven.add_obstacle(Rect2(-6.0, 206.0, 12.0, 5.0))
	var walker := -1
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		walker = i
		break
	ok(walker >= 0, "an unpromoted walker is available")
	if walker < 0: return
	crowd.px[walker] = 0.0
	crowd.pz[walker] = 200.0
	crowd.hold_x[walker] = 0.0
	crowd.hold_z[walker] = 240.0
	m.hero.global_position = Vector3(400, 1, 400)
	for _i in 90: await physics_frame
	var rect := Rect2(-6.0, 206.0, 12.0, 5.0)
	ok(not rect.has_point(Vector2(crowd.px[walker], crowd.pz[walker])), "the march does not cross the obstacle (%.1f, %.1f)" % [crowd.px[walker], crowd.pz[walker]])
	ok(crowd.pz[walker] < 206.5, "the walker stops on the near side of the obstacle (z %.1f)" % crowd.pz[walker])
	TownHaven.clear_obstacles()
	crowd.px[walker] = -430.0
	crowd.pz[walker] = 340.0
	crowd.hold_x[walker] = -520.0
	crowd.hold_z[walker] = 420.0
	for _i in 120: await physics_frame
	var on_sea := float(load("res://scripts/main.gd").sea_mask(crowd.px[walker], crowd.pz[walker])) > 0.5
	ok(not on_sea, "the march does not enter the sea (%.1f, %.1f)" % [crowd.px[walker], crowd.pz[walker]])

func _sustain(m, crowd: HordeCrowd) -> void:
	var before: int = crowd.alive_n
	m.hero.global_position = Vector3(0, 1.0, 198)
	var peak_near := 0
	var peak_list := 0
	for _i in 180:
		await physics_frame
		peak_near = maxi(peak_near, crowd.near_n)
		peak_list = maxi(peak_list, m.party.director.enemies.size())
	print("SUSTAIN frames=180 near_peak=%d list_peak=%d alive=%d inside=%d" % [peak_near, peak_list, crowd.alive_n, crowd.inside_count()])
	ok(peak_near == HordeCrowd.NEAR_CAP, "the fight stays at the pool cap for 3 s (%d)" % peak_near)
	ok(peak_list <= HordeCrowd.NEAR_CAP + 16, "the enemy list does not grow with the simulated crowd (%d)" % peak_list)
	ok(crowd.alive_n <= before, "no extra zombies appear while refill is off (%d -> %d)" % [before, crowd.alive_n])
	ok(crowd.inside_count() == 0, "the sustained fight stays outside the haven")
