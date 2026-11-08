extends SceneTree
## Existing hostiles obey the Liongate haven: wolves, trolls, titan AOE.
## Coverage is the walled square only. godot --headless --path . -s res://tests/haven_hostiles_test.gd
var fails := 0
var n := 0

func ok(c: bool, msg: String) -> void:
	n += 1
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1

func _initialize() -> void: _run.call_deferred()

func f(k: int) -> void:
	for _i in k: await physics_frame

func _run() -> void:
	print("COVERAGE %s" % TownHaven.COVERAGE)
	TownHaven.arm(null)
	_spawn_and_cross()
	_hits()
	await _world()
	print("HAVEN_HOSTILES %d checks, %d failed" % [n, fails])
	quit(1 if fails else 0)

func _director(hero: Node3D) -> EnemyDirector:
	var d := EnemyDirector.new()
	root.add_child(d)
	d.ground = func(_x, _z): return 0.0
	d.combat = HeroCombat.new()
	root.add_child(d.combat)
	d.combat.set_hero("aldric")
	d.combat.body = hero
	d.combat.hp = 700.0
	d.combat.max_hp = 700.0
	return d

func _spawn_and_cross() -> void:
	var hero := Node3D.new()
	root.add_child(hero)
	hero.position = Vector3(-6, 1, 26)
	var d := _director(hero)
	var wolf: Enemy = d.spawn("wolf", Vector3(12, 0, 18), hero)
	ok(not TownHaven.body_inside(Vector2(wolf.global_position.x, wolf.global_position.z), wolf.radius), "wolf cannot spawn inside Liongate")
	var troll: Enemy = d.spawn("frosttroll_a", Vector3(0, 0, 40), hero)
	ok(not TownHaven.body_inside(Vector2(troll.global_position.x, troll.global_position.z), troll.radius), "frost troll cannot spawn inside Liongate")
	var stand := TownHaven.stand_off(wolf.radius)
	var gates: Array[Vector2] = [Vector2(0, 1), Vector2(0, -1), Vector2(1, 0), Vector2(-1, 0)]
	for g in gates:
		wolf.global_position = Vector3(g.x, 0, g.y) * (stand + 0.4)
		wolf._step_xz(Vector3(-g.x, 0, -g.y) * 40.0)
		var at := Vector2(wolf.global_position.x, wolf.global_position.z)
		ok(not TownHaven.body_inside(at, wolf.radius), "40 m step through gate %s stays outside (%.2f, %.2f)" % [g, at.x, at.y])
	var corners: Array[Vector2] = [Vector2(1, 1), Vector2(1, -1), Vector2(-1, 1), Vector2(-1, -1)]
	for c in corners:
		var p := c.normalized() * (stand + 1.0)
		wolf.global_position = Vector3(p.x, 0, p.y)
		wolf._step_xz(Vector3(-p.x, 0, -p.y))
		ok(not TownHaven.body_inside(Vector2(wolf.global_position.x, wolf.global_position.z), wolf.radius), "corner seam %s blocks entry" % c)
	# seam itself is not inside; one centimetre in is
	var lim := TownHaven.outer_limit()
	ok(not TownHaven.inside_xz(0.0, lim) and TownHaven.inside_xz(0.0, lim - 0.02), "south gate plane is outside, 2 cm in is inside")
	ok(not TownHaven.inside_xz(lim, lim) and TownHaven.inside_xz(lim - 0.02, lim - 0.02), "outer corner seam is outside, the inner corner is inside")

func _hits() -> void:
	var hero := Node3D.new()
	root.add_child(hero)
	var d := _director(hero)
	var stand := TownHaven.stand_off(0.6)
	var wolf: Enemy = d.spawn("wolf", Vector3(0, 0, stand + 2.0), hero)
	wolf.global_position = Vector3(0, 0, stand + 0.5)
	hero.position = Vector3(0, 1, stand + 1.3)
	d.combat.hp = 700.0
	d._on_attack(wolf, {"shape": "ring", "reach": 30.0})
	ok(d.combat.hp < 700.0, "wolf melee lands outside the wall (hp %.0f)" % d.combat.hp)
	var outside_hp := d.combat.hp
	hero.position = Vector3(0, 1, 30)
	d._on_attack(wolf, {"shape": "ring", "reach": 30.0})
	ok(is_equal_approx(d.combat.hp, outside_hp), "same swing does not land once the hero is inside")
	# in flight: telegraph already running, hero steps in before the hit frame
	hero.position = Vector3(0, 1, stand + 1.2)
	wolf.global_position = Vector3(0, 0, stand + 0.4)
	wolf.pattern = {"shape": "ring", "reach": 40.0, "tele": 0.6}
	wolf.def["tele"] = 0.6
	wolf.set_state("telegraph")
	wolf.t_state = 0.35
	wolf.target = hero
	d.combat.hp = 700.0
	wolf._physics_process(0.1)
	ok(is_equal_approx(d.combat.hp, 700.0), "telegraph has not struck yet")
	hero.position = Vector3(0, 1, 22)
	wolf._physics_process(0.3)
	ok(is_equal_approx(d.combat.hp, 700.0), "in-flight wolf swing is cancelled when the hero enters")
	ok(not TownHaven.body_inside(Vector2(wolf.global_position.x, wolf.global_position.z), wolf.radius), "wolf did not follow the hero through the gate")
	# titan AOE, including one that was aimed while the hero was still outside
	var titan := Enemy.new()
	root.add_child(titan)
	titan.type_id = "titan"
	titan.def = {"atk": 500.0, "reach": 12.0, "boss": true}
	titan.radius = 3.2
	titan.global_position = Vector3(0, 0, stand + 8.0)
	hero.position = Vector3(0, 1, stand + 4.0)
	d.combat.hp = 700.0
	d.combat._titan_log.clear()
	d._aoe(titan, hero.position, 20.0, 1.0)
	ok(d.combat.hp < 700.0, "titan AOE hurts outside (hp %.0f)" % d.combat.hp)
	var mid := d.combat.hp
	hero.position = Vector3(4, 1, 16)
	d._aoe(titan, Vector3(0, 1, stand + 4.0), 80.0, 1.0)
	ok(is_equal_approx(d.combat.hp, mid), "titan AOE aimed outside does not hit a hero who has entered")
	d.combat.titan_hit(0.12)
	ok(is_equal_approx(d.combat.hp, mid), "direct titan_hit is refused inside Liongate")
	hero.position = Vector3(0, 1, 400)
	var far := d.combat.hp
	d.combat.titan_hit(0.12)
	ok(d.combat.hp < far, "the same titan_hit lands far outside town")

func _world() -> void:
	OS.set_environment("VARN_LITE", "1")
	OS.set_environment("VARN_NO_HORDE", "1")
	var m = load("res://main.tscn").instantiate()
	root.add_child(m)
	if m.cheats:
		m.cheats.flags.god = false
		m.cheats.flags.bump = false
	var ui = root.get_node_or_null("VUI")
	if ui and ui.get("title"): ui.title.hide()
	ok(TownHaven.armed, "Liongate haven is armed before the first awaited frame")
	ok(is_equal_approx(TownGuards.RESPOND, 90.0), "a post farther than 90 m still does not answer")
	ok(is_equal_approx(TownGuards.effective_acquire(), 60.0), "effective acquisition is the 60 m leash, not 90 m")
	for e in m.party.director.living():
		e.kill_now(Vector3.ZERO)
	await f(3)
	# Inside the old defence zone (walls + 30 m) and farther than the rejected 34 m post filter.
	var wolf: Enemy = m.party.director.spawn("wolf", Vector3(30, 0, 210), m.hero)
	var nearest := 1.0e9
	for g in m.guards.guards:
		nearest = minf(nearest, (g.post as Vector3).distance_to(wolf.global_position))
	ok(nearest > 34.0 and nearest <= TownGuards.POST_LEASH, "this wolf is outside the old 34 m bubble and inside the post leash (%.1f m)" % nearest)
	m.hero.global_position = Vector3(0, 0.4, 24)
	m.party.combat.hp = m.party.combat.max_hp
	await f(20)
	var answered := 0
	var wandered := 0.0
	for g in m.guards.guards:
		if g.tgt == wolf: answered += 1
		wandered = maxf(wandered, (g.node as Node3D).global_position.distance_to(g.post))
	ok(answered > 0, "south-gate guards acquire a wolf ~45 m out (%d)" % answered)
	ok(wandered <= TownGuards.POST_LEASH + 1.5, "those guards stayed within the post leash (%.1f m)" % wandered)
	wolf.global_position = Vector3(0, 0, 340)
	await f(15)
	var still := 0
	for g in m.guards.guards:
		if g.tgt == wolf: still += 1
	ok(still == 0, "a wolf past the post leash is dropped")
	# crossing under a long frame while guards are down
	for g in m.guards.guards:
		g.down_t = 30.0
		g.tgt = null
	wolf.global_position = Vector3(0, 0, TownHaven.stand_off(wolf.radius) + 0.3)
	wolf.home = wolf.global_position
	wolf.target = m.hero
	wolf.set_state("chase")
	m.hero.global_position = Vector3(0, 0.4, 20)
	var hp0: float = m.party.combat.hp
	wolf._physics_process(1.0)
	m.undead_boundary.sweep()
	ok(not TownHaven.body_inside(Vector2(wolf.global_position.x, wolf.global_position.z), wolf.radius), "a 1 s wolf chase does not enter while guards are down")
	m.party.director._on_attack(wolf, {"shape": "ring", "reach": 80.0})
	m.party.director._aoe(wolf, m.hero.global_position, 100.0, 2.0)
	ok(is_equal_approx(m.party.combat.hp, hp0), "downed guards are not what blocks wolf hits inside")
	m.guards.queue_free()
	m.guards = null
	wolf.global_position = Vector3(0, 0, 30)
	m.undead_boundary.sweep()
	ok(not TownHaven.inside(wolf.global_position), "with no guard node a planted wolf is expelled")
	m.party.director._aoe(wolf, m.hero.global_position, 100.0, 2.0)
	ok(is_equal_approx(m.party.combat.hp, hp0), "absent guards still leave the interior safe")
	# travel recomputes
	m._on_travel("town")
	ok(TownHaven.hero_safe(m.hero.global_position), "travel to town is inside the haven")
	m.party.director._aoe(wolf, m.hero.global_position, 50.0, 1.0)
	ok(is_equal_approx(m.party.combat.hp, hp0), "travel to town does not leave a sticky hole for AOE")
	m._teleport(Vector3(260, 0, 20), 0.3)
	ok(not TownHaven.hero_safe(m.hero.global_position), "leaving town is vulnerable again")
	var out_hp: float = m.party.combat.hp
	wolf.global_position = m.hero.global_position + Vector3(0, 0, 1.2)
	m.party.director._on_attack(wolf, {"shape": "ring", "reach": 8.0})
	ok(m.party.combat.hp < out_hp, "outside, the wolf hits again (%.0f -> %.0f)" % [out_hp, m.party.combat.hp])
	# load: exact inside position, protection before the next hit
	var vs = root.get_node("VSave")
	vs.dir = "user://haven_hostile_save/"
	DirAccess.make_dir_recursive_absolute(vs.dir)
	ok(vs.write_snapshot({"x": -6.25, "z": 26.5, "yaw": 0.4, "zone": "village", "hero": int(vs.state.get("active", 0)), "at_sea": false, "at_interior": false}), "inside save wrote")
	var disk: Dictionary = vs.read_save().state
	ok(is_equal_approx(float(disk.p3d.x), -6.25) and is_equal_approx(float(disk.p3d.z), 26.5), "saved coordinates stayed exact")
	ok(not disk.has("horde"), "save still has no horde blob")
	m.queue_free()
	await f(6)
	vs.state = vs.load_state()
	var m2 = load("res://main.tscn").instantiate()
	root.add_child(m2)
	if m2.cheats:
		m2.cheats.flags.god = false
		m2.cheats.flags.bump = false
	ok(TownHaven.armed, "relaunch arms the haven during ready")
	var planted: Enemy = m2.party.director.spawn("wolf", Vector3(0, 0, 10), m2.hero)
	planted.global_position = m2.hero.global_position
	var hero_at := Vector2(m2.hero.position.x, m2.hero.position.z)
	var hp_load: float = m2.party.combat.hp
	m2.undead_boundary.sweep()
	ok(not TownHaven.body_inside(Vector2(planted.global_position.x, planted.global_position.z), planted.radius), "loaded wolf planted inside is expelled before AI")
	ok(Vector2(m2.hero.position.x, m2.hero.position.z).distance_to(hero_at) < 0.001, "expulsion does not move the hero")
	m2._on_play_solo()
	var at := Vector2(m2.hero.position.x, m2.hero.position.z)
	ok(is_equal_approx(at.x, -6.25) and is_equal_approx(at.y, 26.5), "play resumed the inside point (%.2f, %.2f)" % [at.x, at.y])
	m2.party.director._aoe(planted, m2.hero.global_position, 40.0, 3.0)
	ok(is_equal_approx(m2.party.combat.hp, hp_load) or m2.party.combat.hp == m2.party.combat.max_hp, "no hostile damage on the resumed inside spot")
	m2.queue_free()
