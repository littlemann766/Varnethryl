extends SceneTree
## Connected harbour waterfront plus the guard leash. Liongate stays in force.
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
	var row_gaps := 0
	var samples := 0
	var tavern := Vector2(-405.0, 300.0)
	var gap := Vector2(-430.0, 350.0)
	var road := Vector2(-387.0, 322.0)
	var light := Vector2(-440.2, 453.3)
	var stops: Array[Vector2] = [tavern, road, gap]
	for pd in InteriorExtraDoors.PORT_DOORS:
		var spot: Vector2 = load("res://scripts/main.gd").harbour_spot()[0]
		var d: Vector3 = pd[1]
		stops.append(Vector2(spot.x - d.z, spot.y + d.x))
	stops.append(light)
	for i in stops.size() - 1:
		var a: Vector2 = stops[i]
		var b: Vector2 = stops[i + 1]
		var steps := int(ceil(a.distance_to(b) / 2.0))
		for s in steps + 1:
			var p: Vector2 = a.lerp(b, float(s) / float(maxi(steps, 1)))
			samples += 1
			if not TownHaven.harbour_inside(p.x, p.y): row_gaps += 1
	ok(row_gaps == 0, "land route tavern -> road mouth -> cottages -> lighthouse has no gap (%d/%d)" % [row_gaps, samples])
	ok(samples > 40, "route was sampled every 2 m (%d)" % samples)
	ok(not TownHaven.harbour_inside(hd.PIERS[0], hd.SHORE_Z + 28.0), "a pier over the water is not shielded")
	ok(not TownHaven.inside_xz(-520.0, 450.0), "open sea is not the haven")
	ok(TownHaven.harbour_inside(-430.0, 350.0), "the dry land between the tavern and the cottages is inside")
	ok(TownHaven.harbour_inside(-387.0, 322.0), "the Tidewrack road mouth is inside the district")
	ok(not TownHaven.harbour_inside(-336.0, 269.0), "the road back toward the city stays outside")
	ok(not TownHaven.harbour_inside(-370.0, 280.0), "ground east of the warehouses stays outside")
	ok(not TownHaven.harbour_inside(-385.0, 450.0), "ground east of the lighthouse stays outside")
	var sea_east: float = float(load("res://scripts/main.gd").SEA_COAST_X) - 1.0
	var offshore: float = sea_east - TownHaven.WATERFRONT_WEST
	print("OFFSHORE sea_plane_east=%.1f west_edge=%.1f width=%.1f" % [sea_east, TownHaven.WATERFRONT_WEST, offshore])
	ok(is_equal_approx(offshore, 11.4), "waterfront covers 11.4 m of the sea plane (measured %.1f)" % offshore)
	for z in [330.0, 350.0, 400.0, 453.3, 470.0]:
		ok(TownHaven.harbour_inside(sea_east - 11.0, z), "11 m offshore is inside along the waterfront at z %.1f" % z)
		ok(not TownHaven.harbour_inside(sea_east - 12.0, z), "12 m offshore is outside along the waterfront at z %.1f" % z)
	ok(not TownHaven.harbour_inside(-468.0, 400.0), "water west of the lighthouse rock stays outside")
	ok(TownHaven.harbour_inside(-440.2, 453.3), "the lighthouse door is inside the waterfront")
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
	ok(TownHaven.hero_safe(m.hero.global_position), "the land between the tavern and the cottages stays safe after leaving the interior")
	var gap_hp: float = m.party.combat.hp
	wolf.global_position = m.hero.global_position + Vector3(0, 0, 1.1)
	m.party.director._on_attack(wolf, {"shape": "ring", "reach": 8.0})
	ok(is_equal_approx(m.party.combat.hp, gap_hp), "wolf ring does not land on that land point")
	await _walk_route(m)
	var lh := {}
	for b in m.extra_doors:
		if str(b.get("id", "")) == "lighthouse": lh = b
	ok(not lh.is_empty(), "lighthouse door is registered")
	if not lh.is_empty():
		var door: Vector3 = m.interiors.door_world(lh)
		ok(TownHaven.harbour_inside(door.x, door.z), "lighthouse door threshold is inside (%.1f, %.1f)" % [door.x, door.z])
		m._teleport(door, 0.0)
		ok(TownHaven.hero_safe(m.hero.global_position), "standing on the lighthouse threshold is safe")
		m.interiors.enter(lh)
		await f(8)
		ok(TownHaven.town_interior_active() and TownHaven.hero_safe(m.hero.global_position), "lighthouse interior follows a safe exterior")
		var lh_hp: float = m.party.combat.hp
		wolf.global_position = m.hero.global_position + Vector3(0.6, 0, 0)
		m.party.director._on_attack(wolf, {"shape": "ring", "reach": 20.0})
		ok(is_equal_approx(m.party.combat.hp, lh_hp), "wolf ring inside the lighthouse does no damage")
		m.interiors.exit()
		await f(3)
	m._teleport(hd_pier(), 0.0)
	ok(not TownHaven.hero_safe(m.hero.global_position), "a pier is outside")
	var pier_hp: float = m.party.combat.hp
	wolf.global_position = m.hero.global_position + Vector3(1.0, 0, 0)
	m.party.director._on_attack(wolf, {"shape": "ring", "reach": 8.0})
	ok(m.party.combat.hp < pier_hp, "wolf ring lands on the pier (%.0f -> %.0f)" % [pier_hp, m.party.combat.hp])
	m._teleport(Vector3(-430, 0, 350), 0.0)
	ok(TownHaven.hero_safe(m.hero.global_position), "returning from the pier to the land route is safe again")
	var back_hp: float = m.party.combat.hp
	m.party.director._on_attack(wolf, {"shape": "ring", "reach": 30.0})
	ok(is_equal_approx(m.party.combat.hp, back_hp), "no sticky vulnerability after the pier")
	await _guard_ranges(m, wolf)
	await _save_route(m)

func _walk_route(m) -> void:
	var stops: Array[Vector2] = [Vector2(-405, 300), Vector2(-420, 327), Vector2(-430, 350), Vector2(-433, 390), Vector2(-440, 430), Vector2(-440.2, 453.3)]
	var unsafe := 0
	var nsteps := 0
	for i in stops.size() - 1:
		var a: Vector2 = stops[i]
		var b: Vector2 = stops[i + 1]
		var steps := int(ceil(a.distance_to(b) / 4.0))
		for s in steps + 1:
			var p: Vector2 = a.lerp(b, float(s) / float(maxi(steps, 1)))
			m._teleport(Vector3(p.x, 0, p.y), 0.0)
			nsteps += 1
			if not TownHaven.hero_safe(m.hero.global_position): unsafe += 1
	ok(unsafe == 0, "hero can be stood on every 4 m of the settlement route (%d steps, %d unsafe)" % [nsteps, unsafe])
	m.hero.position = Vector3(-420, 0.4, 310)
	m.hero.velocity = Vector3.ZERO
	m.yaw = PI
	m.joy_vec = Vector2(0, -1)
	var z0: float = m.hero.position.z
	await f(40)
	m.joy_vec = Vector2.ZERO
	ok(m.hero.position.z > z0 + 1.0, "hero walked south along the waterfront (%.1f -> %.1f)" % [z0, m.hero.position.z])
	ok(TownHaven.hero_safe(m.hero.global_position), "that walk stayed inside the haven")

func _save_route(m) -> void:
	var vs = root.get_node("VSave")
	vs.dir = "user://harbour_route_save/"
	DirAccess.make_dir_recursive_absolute(vs.dir)
	ok(vs.write_snapshot({"x": -430.0, "z": 350.0, "yaw": 0.25, "zone": "village", "hero": int(vs.state.get("active", 0)), "at_sea": false, "at_interior": false}), "harbour land point saved")
	var disk: Dictionary = vs.read_save().state
	ok(is_equal_approx(float(disk.p3d.x), -430.0) and is_equal_approx(float(disk.p3d.z), 350.0), "saved harbour coordinates stayed exact")
	m.queue_free()
	await f(6)
	vs.state = vs.load_state()
	var m2 = load("res://main.tscn").instantiate()
	root.add_child(m2)
	if m2.cheats:
		m2.cheats.flags.god = false
		m2.cheats.flags.bump = false
	m2._on_play_solo()
	var at := Vector2(m2.hero.position.x, m2.hero.position.z)
	ok(is_equal_approx(at.x, -430.0) and is_equal_approx(at.y, 350.0), "play resumed on the harbour land route (%.2f, %.2f)" % [at.x, at.y])
	ok(TownHaven.hero_safe(m2.hero.global_position), "the resumed point is safe")
	var wolf: Enemy = m2.party.director.spawn("wolf", Vector3(-520, 0, 250), m2.hero)
	m2.party.combat.hp = m2.party.combat.max_hp
	var hp0: float = m2.party.combat.hp
	m2.party.director._on_attack(wolf, {"shape": "ring", "reach": 80.0})
	ok(is_equal_approx(m2.party.combat.hp, hp0), "a wolf ring does not land on the resumed harbour point")
	m2._on_travel("town")
	ok(TownHaven.hero_safe(m2.hero.global_position), "travel back to Liongate is safe")
	m2._teleport(Vector3(-520, 0, 450), 0.0)
	ok(not TownHaven.hero_safe(m2.hero.global_position), "travel out to sea is not sticky-safe")
	var sea_hp: float = m2.party.combat.hp
	wolf.global_position = m2.hero.global_position + Vector3(1, 0, 0)
	m2.party.director._on_attack(wolf, {"shape": "ring", "reach": 8.0})
	ok(m2.party.combat.hp < sea_hp, "the wolf hits again at sea")
	m2.queue_free()

func _guard_ranges(m, wolf: Enemy) -> void:
	for e in m.party.director.living():
		if e != wolf: e.kill_now(Vector3.ZERO)
	var anchor := Vector3.ZERO
	var have := false
	for g in m.guards.guards:
		var p: Vector3 = g.post
		if p.z > 150.0 and absf(p.x) < 30.0:
			anchor = p
			have = true
			break
	ok(have, "south-gate post found")
	if not have: return
	ok(is_equal_approx(TownGuards.effective_acquire(), 60.0), "effective acquisition is 60 m")
	var near := _spot_at(m, anchor, 40.61)
	var far := _spot_at(m, anchor, 62.49)
	ok(near != Vector3.INF and far != Vector3.INF, "placed the 40.61 m and 62.49 m probes")
	if near == Vector3.INF or far == Vector3.INF: return
	ok(absf(_nearest_post(m, near) - 40.61) <= 0.2, "near probe measures %.2f m" % _nearest_post(m, near))
	ok(absf(_nearest_post(m, far) - 62.49) <= 0.2, "far probe measures %.2f m" % _nearest_post(m, far))
	ok(m.guards.in_zone(near) and m.guards.in_zone(far), "both probes stay in the defence zone")
	_reset_posts(m)
	_park(m, wolf, near)
	var engaged := await _watch(m, wolf, 90)
	print("GUARD_NEAR frames=%d tracked=%d peak=%.2f" % [int(engaged.frames), int(engaged.tracked), float(engaged.max)])
	ok(int(engaged.frames) == 90, "40.61 m probe sampled every frame (%d)" % int(engaged.frames))
	ok(int(engaged.tracked) > 0, "a wolf at 40.61 m is acquired (%d of 90 frames)" % int(engaged.tracked))
	ok(float(engaged.max) <= TownGuards.POST_LEASH + 0.35, "that chase stays inside the leash (per-frame max %.2f m)" % float(engaged.max))
	ok(wolf.alive(), "the 40.61 m wolf stays alive")
	_park(m, wolf, far)
	var home := await _watch(m, wolf, 420)
	var series: Array = home.series
	var rose := 0
	for i in range(1, series.size()):
		if float(series[i]) > float(series[i - 1]) + 0.05: rose += 1
	var last: float = float(series[series.size() - 1])
	print("GUARD_FRAMES frames=%d tracked=%d peak=%.2f last=%.2f rises=%d" % [int(home.frames), int(home.tracked), float(home.max), last, rose])
	ok(int(home.frames) == 420, "62.49 m return sampled every frame")
	ok(int(home.tracked) == 0 and wolf.alive(), "the living wolf at 62.49 m is not taken on any frame")
	ok(rose == 0, "distance from post does not start a new chase (rises %d)" % rose)
	ok(last <= TownGuards.BEAT + 0.5, "last frame is on the beat (%.2f m)" % last)

func _reset_posts(m) -> void:
	for g in m.guards.guards:
		(g.node as Node3D).global_position = g.post
		g.tgt = null
		g.ret = false
		g.down_t = 0.0

func _park(m, wolf: Enemy, spot: Vector3) -> void:
	wolf.global_position = spot
	wolf.hp = wolf.max_hp
	wolf.target = null
	wolf.set_state("idle")
	m.hero.global_position = Vector3(0, 0.4, 20)

func _spot_at(m, anchor: Vector3, dist: float) -> Vector3:
	for deg in range(0, 360, 2):
		var a := deg_to_rad(float(deg))
		var try_p := anchor + Vector3(cos(a) * dist, 0, sin(a) * dist)
		if absf(_nearest_post(m, try_p) - dist) <= 0.15 and m.guards.in_zone(try_p) and not TownHaven.inside(try_p):
			return try_p
	return Vector3.INF

func _nearest_post(m, p: Vector3) -> float:
	var best := 1.0e9
	for g in m.guards.guards:
		best = minf(best, (g.post as Vector3).distance_to(p))
	return best

func _watch(m, wolf: Enemy, frames: int) -> Dictionary:
	var max_d := 0.0
	var tracked := 0
	var series: Array = []
	for _i in frames:
		await physics_frame
		var frame_max := 0.0
		var held := false
		for g in m.guards.guards:
			var d: float = (g.node as Node3D).global_position.distance_to(g.post)
			frame_max = maxf(frame_max, d)
			if g.tgt == wolf: held = true
		max_d = maxf(max_d, frame_max)
		if held: tracked += 1
		series.append(frame_max)
	return {"frames": frames, "max": max_d, "tracked": tracked, "series": series}
