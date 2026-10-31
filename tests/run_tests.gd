extends SceneTree
## Headless tests: heights + combat rules.
## Run: godot --headless -s res://tests/run_tests.gd   (exit code 0 = all pass)
var fails := 0
var passes := 0

func ok(c: bool, msg: String) -> void:
	if c: passes += 1
	else: fails += 1; print("FAIL: ", msg)

func near(a: float, b: float, tol: float) -> bool: return absf(a - b) <= tol

func _init() -> void:
	test_heights()
	test_anim()
	test_combat()
	test_net()
	# test 33: HUD test number == export_presets version/code - 1 (one setting to bump)
	var cf := ConfigFile.new(); var vc := -1
	if cf.load("res://export_presets.cfg") == OK: vc = int(cf.get_value("preset.0.options", "version/code", -1))
	var tb := str(ProjectSettings.get_setting("application/config/test_build", "?"))
	ok(vc > 0 and tb == str(vc - 1), "HUD test number %s == version/code %d - 1" % [tb, vc])
	print("RESULT %d passed, %d failed" % [passes, fails])
	quit(1 if fails else 0)

func test_heights() -> void:
	for id in HeroRoster.APPROVED: ok(HeroRoster.height(id) == HeroRoster.APPROVED[id], "approved height table " + id)
	ok(HeroRoster.height("pip") == 0.52 and HeroRoster.height("phoenix") == 0.756 and HeroRoster.height("wren") == 1.35 and HeroRoster.height("owner") == 1.905, "approved values")
	ok(near(HeroRoster.height("garruk"), 2.02, 1e-6), "garruk from Beth's index (test 6; charscale said 2.083)")
	for id in HeroRoster.ORDER:
		var r := CharacterRig.new().setup(HeroRoster.model(id), HeroRoster.height(id))
		root.add_child(r)
		var h := CharacterRig.measure(r) # skinned rest height of the rig incl. applied scale
		# test 6: Beth's models carry their size on the armature root -> never rescaled. Our skinned rest-pose
		# measure includes hair/wings/props, so allow 6% vs Beth's height_m (deviations printed + reported).
		ok(r.applied_scale == 1.0 or r.voxel, "%s loaded at scale 1 (size baked; voxel heroes fit to roster height)" % id)
		ok(near(h, HeroRoster.height(id), 0.06 * HeroRoster.height(id)), "%s rendered height %.3f vs %.3f" % [id, h, HeroRoster.height(id)])
		print("HEIGHT %-10s %.3f m (target %.3f, scale %.3f)" % [id, h, HeroRoster.height(id), r.applied_scale])
		r.free()
	var M := {"frosttroll_a": 5.715, "frosttroll_b": 5.715, "titan": 11.43, "titan_volcano": 28.0, "stonetroll": 5.715}
	for t in M:
		var T: Dictionary = Enemy.TYPES[t]
		var r2 := CharacterRig.new().setup(T.model, T.height)
		root.add_child(r2)
		var h2 := CharacterRig.measure(r2) * _idle_root_scale(r2) * (VolcanoTitan.TITAN_SCALE if t == "titan_volcano" else 1.0)   # test 13: boss chose 28 m (x1.3362 on the node)   # root-bone scale tracks are stripped: size is on the armature root
		ok(r2.applied_scale == 1.0, "%s loaded at scale 1 (size baked)" % t)
		ok(near(h2, M[t], 0.06 * M[t]), "%s height %.3f vs %.3f" % [t, h2, M[t]])
		print("HEIGHT %-14s %.3f m (target %.3f, scale %.3f)" % [t, h2, M[t], r2.applied_scale])
		if t == "titan_volcano": ok(r2.applied_scale == 1.0, "volcano titan loaded at scale 1")
		r2.free()
	ok(near(Enemy.TYPES.frosttroll_a.height / 1.905, 3.0, 1e-6), "troll = 3x player")
	ok(near(Enemy.TYPES.titan.height / 1.905, 6.0, 1e-6), "titan = 6x")

func test_anim() -> void:
	for id in ["owner", "pip", "wren", "aldric"]:
		var r := CharacterRig.new().setup(HeroRoster.model(id), HeroRoster.height(id))
		root.add_child(r)
		ok(r.tree != null and r.tree.active, id + " has active AnimationTree")
		var bt: AnimationNodeBlendTree = r.tree.tree_root
		for n in ["loco", "attack", "hit", "dead"]: ok(bt.has_node(n), "%s tree node %s" % [id, n])
		for c in ["idle", "walk", "attack", "hit"]: ok(r.clips.has(c), "%s clip %s" % [id, c])
		ok(r.anim_player.get_animation("idle").loop_mode == Animation.LOOP_LINEAR, id + " idle loops")
		ok(r.anim_player.get_animation("attack").loop_mode == Animation.LOOP_NONE, id + " attack one-shot")
		r.free()

func test_combat() -> void:
	var rng := RandomNumberGenerator.new(); rng.seed = 7
	# basic: spammable, no cost, no timing window; only the short fixed interval
	var st := CombatRules.new_state()
	var basic: Dictionary = CombatData.data().ABILITIES[0]
	var n := 0
	for i in 20:
		if CombatRules.can_use("aldric", 0, basic, st): CombatRules.commit("aldric", 0, basic, st); n += 1
		CombatRules.tick(st, 0.3)
	ok(n == 20, "basic attack usable every 0.3 s (got %d/20)" % n)
	ok(st.mp == 100.0 and st.sp == 100.0, "basic attack costs nothing")
	ok(st.cd[0] == 0.0, "basic has no skill cooldown")
	# skills have cooldowns (non-owner)
	var hero_ids: Array = CombatData.data().KITS.keys()
	ok(hero_ids.size() == 20, "20 hero kits ported (%d)" % hero_ids.size())
	for id in hero_ids:
		var kit := CombatData.kit(id)
		ok(kit.skills.size() == 4, id + " has 3 skills + ult")
		var s2 := CombatRules.new_state(); s2.fury = 100.0
		var sk: Dictionary = kit.skills[0]
		ok(CombatRules.can_use(id, 1, sk, s2), id + " skill1 usable fresh")
		CombatRules.commit(id, 1, sk, s2)
		ok(s2.cd[1] > 0.0 and not CombatRules.can_use(id, 1, sk, s2), id + " skill1 on cooldown after use")
	for id in ["pip", "phoenix", "wren"]: ok(CombatData.kit(id).skills.size() == 4, id + " generic kit")
	# Owner: overpowered, no cooldowns, 99,999 per hit
	var so := CombatRules.new_state()
	var ok_kit := CombatData.kit("owner")
	for i in 5:
		ok(CombatRules.can_use("owner", 1, ok_kit.skills[0], so), "owner skill no cooldown #%d" % i)
		CombatRules.commit("owner", 1, ok_kit.skills[0], so)
	ok(CombatRules.basic_damage("owner", 0, rng).dmg == 99999, "owner basic 99,999")
	ok(CombatRules.skill_damage("owner", ok_kit.skills[0], 0, rng).dmg == 99999 * 3, "owner Royal Slash 300%")
	ok(CombatRules.max_hp("owner") == 999999 and CombatRules.max_hp("aldric") == 700, "hp owner vs normal")
	# semi-slow: normal heroes need several hits, nobody but the owner one-shots
	for key in ["wolf", "frosttroll_a", "titan", "titan_volcano"]:
		var e := CombatData.enemy(key)
		var hp: float = e.hp; var hits := 0
		while hp > 0 and hits < 100000: hp -= CombatRules.basic_damage("garruk", 0.08, rng).dmg; hits += 1
		ok(hits >= 5, "%s takes several hits (%d)" % [key, hits])
		print("HITS %-14s hp %d -> %d basic hits for a normal hero (%.1f s at 0.3 s)" % [key, e.hp, hits, hits * 0.3])
		if key == "wolf": ok(CombatRules.basic_damage("owner", 0, rng).dmg >= e.hp, "owner one-shots normal enemies")
	for id in hero_ids:
		var best := 0.0
		for s in CombatData.kit(id).skills: best = max(best, float(s.get("mult", 1)))
		ok(48 * 1.55 * 1.08 * best < 99999, id + " is not overpowered")
	# shapes
	ok(CombatRules.in_shape(basic, Vector2.ZERO, Vector2(0, -1), Vector2(0, -3), 0.5), "melee hits in front")
	ok(not CombatRules.in_shape(basic, Vector2.ZERO, Vector2(0, -1), Vector2(0, 3), 0.5), "melee misses behind")

func test_net() -> void:
	ok(RemotePlayer.skin_id("n:owner_pika1") == "owner" and RemotePlayer.skin_id("wren") == "wren" and RemotePlayer.skin_id("zzz") == "aldric", "remote skin mapping")

## Beth's volcano titan carries its size as a scale key on the root bone of every clip (rest pose = 11 m).
func _idle_root_scale(r: CharacterRig) -> float:
	if r.anim_player == null or not r.anim_player.has_animation("idle"): return 1.0
	var a: Animation = r.anim_player.get_animation("idle")
	for t in a.get_track_count():
		if a.track_get_type(t) == Animation.TYPE_SCALE_3D and str(a.track_get_path(t)).ends_with(":root"):
			return a.scale_track_interpolate(t, 0.0).y
	return 1.0
