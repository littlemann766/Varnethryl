extends SceneTree
## Headless: godot --headless --path . -s res://tests/test_cheats.gd
## Role enforcement for Owner / CoOwner cheats + every cheat's effect on the real world (main.tscn).
var fails := 0
var n := 0
func ok(c: bool, what: String) -> void:
	n += 1
	if not c: fails += 1
	print(("ok   " if c else "FAIL ") + what)

func _initialize() -> void:
	_run.call_deferred()
	create_timer(200.0).timeout.connect(func(): print("TIMEOUT"); quit(2))

func _run() -> void:
	var VS = root.get_node("VSave"); var V = root.get_node("VUI"); var N = root.get_node("Net")
	DirAccess.make_dir_recursive_absolute("user://test_cheats/"); VS.dir = "user://test_cheats/"
	VS.state = VS.sanitize_party(VS.fresh_state()); VS.write_state()
	var main = load("res://main.tscn").instantiate(); root.add_child(main)
	for i in 10: await process_frame
	var C: Cheats = main.cheats
	ok(C != null and V.cheat_api == C, "cheat api wired to VUI")
	# --- real role provider: nobody unlocked ---
	V.gate.lock(); C.coowner_ok = false
	ok(C.role() == "", "no gate -> no role")
	for k in Cheats.OWNER: ok(not C.request(k, true), "player cannot use '%s'" % k)
	# coowner flag without a live server connection is NOT a role (server-verified only)
	C.coowner_ok = true
	ok(not N.is_online() and C.role() == "", "coowner_ok while offline -> still no role")
	C.coowner_ok = false
	# --- CoOwner (provider injected the way a verified coowner-auth would resolve) ---
	var real_provider := C.role_provider
	C.role_provider = func() -> String: return "coowner"
	var owner_only: Array = Cheats.OWNER.filter(func(k): return not Cheats.COOWNER.has(k))
	var gold0 := int(VS.state.gold); var lv0 = VS.state.heroLevels.duplicate(); var gear0 := int(VS.state.gear.size())
	var enemies0: int = main.party.director.enemies.size(); var cheated0 = VS.state.get("cheated")
	var dmg0 = main.party.combat.kit.get("weapon")
	for k in owner_only:
		ok(not C.allowed(k), "coowner role excludes '%s'" % k)
		var arg = ["weapon", 15] if k == "item" else ("titan" if k in ["spawn_boss", "spawn_enemy"] else ("village" if k == "tp_zone" else true))
		ok(not C.request(k, arg), "coowner request('%s') rejected" % k)
	ok(int(VS.state.gold) == gold0, "coowner: gold unchanged")
	ok(VS.state.heroLevels == lv0, "coowner: hero levels unchanged")
	ok(int(VS.state.gear.size()) == gear0, "coowner: no items spawned")
	ok(main.party.director.enemies.size() == enemies0, "coowner: no enemies/bosses spawned")
	ok(VS.state.get("cheated") == cheated0, "coowner: save not marked/changed")
	ok(main.party.combat.kit.get("weapon") == dmg0, "coowner: weapon/balance unchanged (no bamboo)")
	V.dev_action.emit("time"); var tm: int = main.time_mode
	ok(main.time_mode == tm, "coowner: dev tools blocked")
	# self-only cheats work for her
	for k in ["god", "fly", "noclip", "unlimited", "nocd", "titan_form"]: ok(C.request(k, true), "coowner can use '%s'" % k)
	ok(C.request("speed", 4.0) and is_equal_approx(main.cheat.speed, 4.0), "coowner speed 4x")
	ok(main.hero.collision_mask == 0, "noclip clears collision mask")
	ok(main.cheat.fly, "fly sets flight")
	ok(is_equal_approx(main.hero_vis.scale.x, 3.0), "titan form scales own hero (cosmetic)")
	var c = main.party.combat
	c.hp = 1.0; c.st.mp = 0.0; c.st.cd[1] = 9.0
	await process_frame
	ok(c.hp == c.max_hp and c.st.mp == 100.0 and c.st.cd[1] == 0.0, "god + unlimited + nocd apply each frame")
	ok(C.request("heal"), "coowner heal own party")
	ok(C.request("tp_place", "inn"), "coowner teleport to building")
	ok(C.request("bump", false) and not C.flags.bump, "bump toggle")
	# role revoked -> self cheats switch off
	C.role_provider = func() -> String: return ""
	await process_frame
	ok(not C.flags.god and main.cheat.speed == 1.0 and main.hero.collision_mask == 1 and main.hero_vis.scale.x == 1.0, "locking the role clears active cheats")
	# --- Owner gets everything ---
	C.role_provider = func() -> String: return "owner"
	for k in Cheats.OWNER: ok(C.allowed(k), "owner allowed '%s'" % k)
	ok(C.request("gold", 1000000) and int(VS.state.gold) == gold0 + 1000000, "owner +1M gold")
	ok(C.request("remax") and int(VS.state.heroLevels[str(VS.state.active)]) == 80, "owner remax -> Lv 80")
	ok(C.request("item", ["armor", 7]) and VS.state.gear.size() == gear0 + 1, "owner spawn item")
	ok(C.request("bamboo", true) and float(c.kit.weapon.dmgPct) == 900.0, "owner bamboo stick")
	ok(C.request("spawn_enemy", "frosttroll_a") and main.party.director.enemies.size() == enemies0 + 1, "owner spawn enemy")
	ok(C.request("kill") and main.party.director.living().is_empty(), "owner kill enemies")
	ok(C.request("titan"), "owner spawn titan")
	ok(not C.request("spawn_boss", "titan"), "only one boss at a time")
	ok(VS.state.get("cheated") == true, "owner cheats mark save cheated")
	V.dev_action.emit("time")
	ok(main.time_mode != tm, "owner: dev tools allowed")
	C.role_provider = real_provider
	print("RESULT %d/%d passed" % [n - fails, n])
	quit(1 if fails else 0)
