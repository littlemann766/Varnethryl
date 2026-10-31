extends SceneTree
## test 25 (boss: "the owner's ultimate attacks should 1 shot anything"): Owner's Unholy Destruction (slot 4) and Holy
## Destruction (slot 5, new button) kill everything they hit in one hit: villain, frost troll boss, Ashen Titan,
## the world boss. Wrath and other heroes' ultimates do NOT one-shot. VARN_LITE=1 godot --headless --path . -s res://tests/owner_ult_test.gd
var m; var fails := 0; var n := 0
func ok(c: bool, msg: String) -> void:
	n += 1; print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1
func f(k: int) -> void:
	for i in k: await physics_frame; await process_frame
func _initialize() -> void: _run.call_deferred()
func _spawn(p: Vector3) -> Array:
	var d: EnemyDirector = m.party.director; var hp: Vector3 = m.hero.global_position
	var out := []
	for t in ["holyknight_villain", "frosttroll_a", "titan", "wolf"]:
		var e: Enemy = d.spawn(t, hp + Vector3(randf_range(-6, 6), 0, -8 - randf() * 4), m.hero); out.append(e)
		e.max_hp = 1.0e9; e.hp = 1.0e9   # far more HP than any normal hit can remove: only a true one-shot kills
	return out
func _run() -> void:
	m = load("res://main.tscn").instantiate(); root.add_child(m)
	await f(30)
	var party: Party = m.party; var c: HeroCombat = party.combat
	party.set_hero("owner"); await f(3)
	var hud = party.hud
	ok(c.skill(4).get("id", "") == "holy" and c.skill(3).get("id", "") == "unholy" and c.skill(5).is_empty(), "owner kit: unholy 3, holy 4, no Wrath")
	await f(3)
	ok(hud.btns[4].visible and String(hud.btns[4].text).contains("Holy"), "Holy Destruction has a button: " + String(hud.btns[4].text))
	ok(hud.btns[3].visible and String(hud.btns[3].text).contains("Unholy"), "Unholy Destruction has a button")
	ok(not hud.btns[5].visible and not String(hud.btns[3].text + hud.btns[4].text).contains("Wrath"), "no Sovereign's Wrath button")
	var fc = m.fly_controls
	if fc and fc.jump_btn:
		var jr: Rect2 = fc.jump_btn.get_global_rect()
		for i in 6:
			if hud.btns[i].visible: ok(not jr.intersects(hud.btns[i].get_global_rect()), "Jump clear of skill button %d" % i)
	for slot in [3, 4]:
		m.hero.global_position = Vector3(30, m.height(30, 240), 240); await f(2)
		var es := _spawn(m.hero.global_position)
		m.spawn_world_boss(true); await f(5)
		var wb: WorldBoss = m.world_boss
		wb.state = "walk"; wb.hp = 1.0e9
		wb.global_position = m.hero.global_position + Vector3(0, 0, -30)
		await f(2)
		ok(c.use(slot), "slot %d (%s) fires" % [slot, c.skill(slot).name])
		await f(40)
		for e in es: ok(not e.alive(), "slot %d one-shots %s (hp %d/%d)" % [slot, e.type_id, e.hp, e.max_hp])
		ok(wb.state == "dead" or wb.hp <= 0.0, "slot %d one-shots the world boss (hp %.0f)" % [slot, wb.hp])
		await f(5)
	# negatives: Wrath stays as it was; another hero's ultimate is not a one-shot
	m.hero.global_position = Vector3(30, m.height(30, 240), 240); await f(2)
	var es2 := _spawn(m.hero.global_position)
	c.use(1); await f(40)
	ok(es2[1].alive(), "Royal Slash: no one-shot (troll hp %.0f)" % es2[1].hp)
	party.set_hero("darius"); await f(3)
	c.st.fury = 100.0; c.st.mp = 999; c.st.sp = 999; c.st.cd[4] = 0.0
	c.use(4); await f(40)
	ok(es2[1].alive(), "darius's ultimate: no one-shot (troll hp %.0f)" % es2[1].hp)
	ok(not HeroCombat.one_shot("darius", {"id": "unholy"}) and not HeroCombat.one_shot("owner", {"id": "wrath"}), "one_shot only owner unholy/holy")
	print("OWNER_ULT %d checks, %d failed -> %s" % [n, fails, "PASS" if fails == 0 else "FAIL"])
	quit(1 if fails else 0)
