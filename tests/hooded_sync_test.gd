extends SceneTree
## Attack damage lines up with the hooded bite, and the near body is not a capsule.
## Headless. Not a phone result.
## godot --headless --path . -s res://tests/hooded_sync_test.gd
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
	for _i in 12: await physics_frame
	for g in m.guards.guards:
		g.down_t = 999.0
		g.tgt = null
	var crowd: HordeCrowd = m.horde.crowd
	var card_ok := true
	for mi in crowd._meshes:
		var mesh: Mesh = (mi as MultiMeshInstance3D).multimesh.mesh
		if not (mesh is QuadMesh): card_ok = false
	ok(card_ok, "far crowd batches are billboard cards, not capsules")
	m.hero.global_position = Vector3(0, 1.0, 210)
	m.party.combat.hp = m.party.combat.max_hp
	var sham := await _time_strike(m, crowd, "shambler")
	print("STRIKE_SHAMBLER frames=%d sec=%.3f" % [sham, sham / 60.0])
	ok(sham >= 44 and sham <= 54, "shambler damage waits for the bite reach (%.2f s)" % (sham / 60.0))
	m.party.combat.hp = m.party.combat.max_hp
	var run := await _time_strike(m, crowd, "runner")
	print("STRIKE_RUNNER frames=%d sec=%.3f" % [run, run / 60.0])
	ok(run >= 44 and run <= 54, "runner damage waits for the same bite reach (%.2f s)" % (run / 60.0))
	await _interrupt(m, crowd)
	await _death_and_again(m, crowd)
	print("HOODED_SYNC %d checks, %d failed" % [n, fails])
	quit(1 if fails else 0)

func _time_strike(m, crowd: HordeCrowd, role_name: String) -> int:
	var idx := _free(crowd)
	crowd.px[idx] = m.hero.global_position.x
	crowd.pz[idx] = m.hero.global_position.z + 1.0
	crowd.hold_x[idx] = crowd.px[idx]
	crowd.hold_z[idx] = crowd.pz[idx]
	crowd.role[idx] = 1 if role_name == "runner" else 0
	crowd.hp[idx] = 190.0
	crowd.lock_t[idx] = 0.0
	crowd.wind_t[idx] = 0.0
	ok(crowd._promote_index(idx, m.hero.global_position), "%s promotes onto the hooded body" % role_name)
	var body: HordeZombie = crowd.pool[crowd.pool_i[idx]]
	body.global_position = Vector3(crowd.px[idx], 0.2, crowd.pz[idx])
	body.crowd_lock = 0.0
	body.state = "approach"
	body.pending_kind = ""
	var hood := body.get_node_or_null("Hooded")
	ok(hood is HoodedPresenter, "%s near body is the hooded presenter, not a capsule" % role_name)
	print("WINDUP %s need=%.2f state=%s lock=%.2f" % [role_name, body.windup_need, body.state, body.crowd_lock])
	var hp0: float = m.party.combat.hp
	var t0 := Engine.get_physics_frames()
	var frames := 0
	while frames < 90 and is_equal_approx(m.party.combat.hp, hp0):
		await physics_frame
		frames = Engine.get_physics_frames() - t0
	for _i in 4: await process_frame
	if hood is HoodedPresenter:
		ok(str(hood.clip) == "attack2" or str(hood.clip) == "recover" or m.party.combat.hp < hp0, "%s presenter entered the bite clip (%s)" % [role_name, hood.clip])
	body.crowd_lock = 30.0
	return frames

func _interrupt(m, crowd: HordeCrowd) -> void:
	m.party.combat.hp = m.party.combat.max_hp
	var idx := _free(crowd)
	if idx < 0: return
	crowd.px[idx] = m.hero.global_position.x
	crowd.pz[idx] = m.hero.global_position.z + 1.0
	crowd.role[idx] = 0
	crowd.lock_t[idx] = 0.0
	crowd.wind_t[idx] = 0.0
	if not crowd._promote_index(idx, m.hero.global_position):
		ok(false, "interrupt body promoted")
		return
	var body: HordeZombie = crowd.pool[crowd.pool_i[idx]]
	body.global_position = Vector3(crowd.px[idx], 0.2, crowd.pz[idx])
	body.crowd_lock = 0.0
	body.state = "approach"
	for _i in 12:
		await physics_frame
	ok(body.state == "windup", "the bite has started before the reach")
	var hp0: float = m.party.combat.hp
	body.take_damage(30, Vector3.ZERO)
	ok(body.state != "windup", "a hit interrupts the bite")
	for _i in 50:
		await physics_frame
		await process_frame
	ok(is_equal_approx(m.party.combat.hp, hp0), "the interrupted bite does not land damage")
	var hood := body.get_node_or_null("Hooded")
	if hood is HoodedPresenter:
		ok(str(hood.clip) == "hit" or str(hood.clip) == "idle" or str(hood.clip) == "walk", "the presenter left the bite for the flinch (%s)" % hood.clip)
	body.crowd_lock = 30.0

func _death_and_again(m, crowd: HordeCrowd) -> void:
	var idx := _free(crowd)
	if idx < 0: return
	crowd.px[idx] = m.hero.global_position.x + 3.0
	crowd.pz[idx] = m.hero.global_position.z
	crowd.lock_t[idx] = 5.0
	var sim := int(crowd.id[idx])
	if not crowd._promote_index(idx, m.hero.global_position):
		ok(false, "death body promoted")
		return
	var body: HordeZombie = crowd.pool[crowd.pool_i[idx]]
	body.hp = 40.0
	body.kill_now(Vector3.ZERO)
	for _i in 5:
		await physics_frame
		await process_frame
	var hood := body.get_node_or_null("Hooded")
	ok(body.state == "defeated", "death sets the defeated state")
	if hood is HoodedPresenter:
		ok(str(hood.clip) == "death", "death plays the death clip and holds it (%s)" % hood.clip)
	ok(not crowd.id_alive(sim), "the killed id stays retired")
	var again := crowd.deploy_actor("shambler")
	ok(again != null and again.get_node_or_null("Hooded") is HoodedPresenter, "the next promotion reuses a hooded body")
	m.hero.global_position = Vector3(400, 1, 400)
	for _i in 8: await physics_frame
	ok(crowd.near_n <= HordeCrowd.NEAR_CAP, "demotion keeps the near cap (%d)" % crowd.near_n)

func _free(crowd: HordeCrowd) -> int:
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		return i
	return -1
