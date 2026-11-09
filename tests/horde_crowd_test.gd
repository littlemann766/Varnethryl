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
	print("CROWD_LOGIC %d checks, %d failed" % [n, fails])
	quit(1 if fails else 0)
