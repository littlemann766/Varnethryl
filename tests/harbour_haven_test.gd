extends SceneTree
## Inhabited harbour pads plus the guard leash. Liongate stays in force.
## godot --headless --path . -s res://tests/harbour_haven_test.gd
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
	_bounds()
	_push()
	await _world()
	print("HARBOUR_HAVEN %d checks, %d failed" % [n, fails])
	quit(1 if fails else 0)

func _bounds() -> void:
	var hd = load("res://scripts/harbor_district.gd")
	ok(TownHaven.liongate_inside(0, 0) and TownHaven.inside(Vector3(0, 30, 0)), "Liongate square is still safe at height")
	ok(TownHaven.harbour_inside(-447.0, 300.0), "Harbour Master pad is inside")
	ok(TownHaven.harbour_inside(-405.0, 300.0), "Salty Anchor tavern is inside")
	ok(TownHaven.harbour_inside(-428.0, 291.0), "fish market is inside")
	var row: Rect2 = TownHaven.port_row()
	for pd in InteriorExtraDoors.PORT_DOORS:
		var spot: Vector2 = load("res://scripts/main.gd").harbour_spot()[0]
		var d: Vector3 = pd[1]
		var w := Vector2(spot.x - d.z, spot.y + d.x)
		ok(TownHaven.harbour_inside(w.x, w.y), "%s door is inside the coast row (%.1f, %.1f)" % [pd[0], w.x, w.y])
		ok(row.has_point(w), "%s door sits in the computed row" % pd[0])
	ok(not TownHaven.harbour_inside(hd.PIERS[0], hd.SHORE_Z + 28.0), "a pier over the water is not shielded")
	ok(not TownHaven.inside_xz(-520.0, 450.0), "open sea is not the haven")
	ok(not TownHaven.harbour_inside(-430.0, 350.0), "shore road between the pads is not shielded")
	ok(not TownHaven.inside_xz(-290.0, -288.0), "farmhouse stays outside")
	ok(TownHaven.harbour_inside(hd.X0 + 0.2, 300.0) and not TownHaven.harbour_inside(hd.X0 - 0.5, 300.0), "west district edge is the bound")
	ok(TownHaven.harbour_inside(-480.0, hd.Z0 + 0.2) and not TownHaven.harbour_inside(-480.0, hd.Z0 - 0.5), "inland district edge is the bound")
	ok(TownHaven.inside(Vector3(-447, 40, 300)) and TownHaven.inside(Vector3(-447, -4, 300)), "harbour safety is the whole column, not only the street")
	var lim := TownHaven.outer_limit()
	ok(not TownHaven.liongate_inside(0, lim) and TownHaven.liongate_inside(0, lim - 0.02), "Liongate gate plane is unchanged")

func _push() -> void:
	var hero := Node3D.new()
	root.add_child(hero)
	hero.position = Vector3(-447, 1, 300)
	var d := EnemyDirector.new()
	root.add_child(d)
	d.ground = func(_x, _z): return 0.0
	d.combat = HeroCombat.new()
	root.add_child(d.combat)
	d.combat.set_hero("aldric")
	d.combat.body = hero
	d.combat.hp = 700
	d.combat.max_hp = 700
	var wolf: Enemy = d.spawn("wolf", Vector3(-447, 0, 300), hero)
	ok(not TownHaven.body_inside(Vector2(wolf.global_position.x, wolf.global_position.z), wolf.radius), "wolf spawn on the Harbour Master is pushed out (%s)" % wolf.global_position)
	var from := Vector2(-480, HarborDistrict.Z0 - 12.0)
	var stopped := TownHaven.clamp_move(from, Vector2(-480, 300), wolf.radius)
	ok(not TownHaven.body_inside(stopped, wolf.radius), "40 m step into the district stops at the edge (%.1f, %.1f)" % [stopped.x, stopped.y])
	hero.position = Vector3(-480, 1, HarborDistrict.Z0 - 4.0)
	d.combat.hp = 700
	wolf.global_position = hero.position + Vector3(0, 0, 1.0)
	d._on_attack(wolf, {"shape": "ring", "reach": 12.0})
	ok(d.combat.hp < 700.0, "wolf ring lands just inland of the district (hp %.0f)" % d.combat.hp)
	var mid := d.combat.hp
	hero.position = Vector3(-447, 1, 300)
	d._aoe(wolf, hero.position, 30.0, 2.0)
	ok(is_equal_approx(d.combat.hp, mid), "same ring does not land after stepping into the district")
	var titan := Enemy.new()
	root.add_child(titan)
	titan.type_id = "titan"
	titan.def = {"atk": 400.0}
	titan.radius = 3.0
	d.combat._titan_log.clear()
	d._aoe(titan, hero.position, 40.0, 1.0)
	ok(is_equal_approx(d.combat.hp, mid), "titan AOE does not land in the harbour district")
	hero.position = Vector3(hd_pier())
	var out_hp := d.combat.hp
	d.combat._titan_log.clear()
	d._aoe(titan, hero.position, 20.0, 1.0)
	ok(d.combat.hp < out_hp, "titan AOE still lands on a pier (hp %.0f)" % d.combat.hp)
	hero.position = Vector3(-447, 8, 300)
	var back := d.combat.hp
	d._aoe(titan, hero.position, 20.0, 1.0)
	ok(is_equal_approx(d.combat.hp, back), "returning to the district clears the pier hit, no sticky immunity")

func hd_pier() -> Vector3:
	return Vector3(HarborDistrict.PIERS[1], 1.0, HarborDistrict.SHORE_Z + 26.0)

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
	var hm := {}
	for b in m.extra_doors:
		if str(b.get("name", "")) == "Harbour Master": hm = b
	ok(not hm.is_empty() and TownHaven.harbour_inside(hm.node.global_position.x, hm.node.global_position.z), "Harbour Master exterior is in the haven")
	for e in m.party.director.living(): e.kill_now(Vector3.ZERO)
	await f(2)
	var wolf: Enemy = m.party.director.spawn("wolf", Vector3(-520, 0, 250), m.hero)
	m.interiors.enter(hm)
	await f(8)
	ok(TownHaven.town_interior_active(), "Harbour Master interior is active")
	ok(TownHaven.hero_safe(m.hero.global_position), "hero in that interior is safe even though the cell is parked far away")
	m.party.combat.hp = m.party.combat.max_hp
	var hp0: float = m.party.combat.hp
	wolf.global_position = m.hero.global_position + Vector3(0.7, 0, 0)
	m.party.director._on_attack(wolf, {"shape": "ring", "reach": 40.0})
	m.party.director._aoe(wolf, m.hero.global_position, 20.0, 3.0)
	ok(is_equal_approx(m.party.combat.hp, hp0), "wolf ring inside the Harbour Master does no damage")
	m.interiors.exit()
	await f(4)
	m._teleport(Vector3(-430, 0, 350), 0.2)
	ok(not TownHaven.hero_safe(m.hero.global_position), "the shore road is outside after leaving the interior")
	var road: float = m.party.combat.hp
	wolf.global_position = m.hero.global_position + Vector3(0, 0, 1.1)
	m.party.director._on_attack(wolf, {"shape": "ring", "reach": 8.0})
	ok(m.party.combat.hp < road, "wolf ring lands on the road (%.0f -> %.0f)" % [road, m.party.combat.hp])
	m.interiors.enter(hm)
	await f(6)
	var inside_hp: float = m.party.combat.hp
	wolf.global_position = m.hero.global_position + Vector3(0.6, 0, 0)
	m.party.director._on_attack(wolf, {"shape": "ring", "reach": 20.0})
	ok(is_equal_approx(m.party.combat.hp, inside_hp), "re-entering the Harbour Master is safe again")
	m.interiors.exit()
	await f(3)
	m._teleport(hd_pier(), 0.0)
	ok(not TownHaven.hero_safe(m.hero.global_position), "a pier is outside")
	var pier_hp: float = m.party.combat.hp
	wolf.global_position = m.hero.global_position + Vector3(1.0, 0, 0)
	m.party.director._on_attack(wolf, {"shape": "ring", "reach": 8.0})
	ok(m.party.combat.hp < pier_hp, "wolf ring lands on the pier (%.0f -> %.0f)" % [pier_hp, m.party.combat.hp])
	await _guard_hold(m, wolf)

func _guard_hold(m, wolf: Enemy) -> void:
	for e in m.party.director.living():
		if e != wolf: e.kill_now(Vector3.ZERO)
	var guard: Dictionary = {}
	for g in m.guards.guards:
		var p: Vector3 = g.post
		if p.z > 150.0 and absf(p.x) < 30.0:
			guard = g
			break
	ok(not guard.is_empty(), "south-gate post found")
	if guard.is_empty(): return
	var anchor: Vector3 = guard.post
	var dir := Vector2(1.0, 0.35).normalized()
	var spot := anchor
	var found := false
	for step in range(50, 95):
		var try_p := anchor + Vector3(dir.x, 0, dir.y) * float(step)
		var nearest := 1.0e9
		for g in m.guards.guards:
			nearest = minf(nearest, (g.post as Vector3).distance_to(try_p))
		if nearest > TownGuards.POST_LEASH + 1.5 and nearest < TownGuards.RESPOND - 2.0 and m.guards.in_zone(try_p):
			spot = try_p
			found = true
			break
	ok(found, "found a living-target spot outside every post leash and inside 90 m")
	if not found: return
	var dist := 1.0e9
	for g in m.guards.guards:
		dist = minf(dist, (g.post as Vector3).distance_to(spot))
	ok(dist > TownGuards.POST_LEASH and dist < TownGuards.RESPOND, "probe target is outside the leash and inside 90 m (%.2f m)" % dist)
	ok(m.guards.in_zone(spot), "probe target is still in the defence zone")
	wolf.global_position = spot
	wolf.hp = wolf.max_hp
	wolf.target = null
	wolf.set_state("idle")
	m.hero.global_position = Vector3(0, 0.4, 20)
	for g in m.guards.guards:
		g.tgt = null
		g.ret = false
		g.down_t = 0.0
	await f(180)
	var tracked := 0
	var farthest := 0.0
	for g in m.guards.guards:
		if g.tgt == wolf: tracked += 1
		farthest = maxf(farthest, (g.node as Node3D).global_position.distance_to(g.post))
	ok(wolf.alive(), "target outside the leash is still alive")
	ok(tracked == 0, "no guard keeps the capped target (%d)" % tracked)
	ok(farthest < 16.0, "guards held or returned to the post (farthest %.1f m)" % farthest)
	await f(60)
	tracked = 0
	farthest = 0.0
	for g in m.guards.guards:
		if g.tgt == wolf: tracked += 1
		farthest = maxf(farthest, (g.node as Node3D).global_position.distance_to(g.post))
	ok(tracked == 0 and wolf.alive() and farthest < 16.0, "they do not reacquire it on the next second (farthest %.1f m)" % farthest)
