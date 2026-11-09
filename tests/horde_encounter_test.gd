extends SceneTree
## Gate sightline and close guard defence. Headless scene boot, not a phone and not a rendered frame.
## godot --headless --path . -s res://tests/horde_encounter_test.gd
var fails := 0
var n := 0

func ok(c: bool, msg: String) -> void:
	n += 1
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1

func f(k: int) -> void:
	for _i in k: await physics_frame

func _initialize() -> void: _run.call_deferred()

func _run() -> void:
	OS.set_environment("VARN_LITE", "1")
	OS.set_environment("VARN_NO_FLOWERS", "1")
	OS.set_environment("VARN_NO_HORDE", "")
	await process_frame
	var m = load("res://main.tscn").instantiate()
	root.add_child(m)
	if m.cheats:
		m.cheats.flags.god = false
		m.cheats.flags.bump = false
	for _i in 30: await physics_frame
	var rc: Dictionary = m.horde.crowd.role_counts()
	ok(int(rc.shambler) > int(rc.runner) and int(rc.undead_knight) >= 2 and int(rc.undead_sailor) >= 2, "roster shambler %d runner %d knight %d sailor %d" % [rc.shambler, rc.runner, rc.undead_knight, rc.undead_sailor])
	ok(m.horde.alive_count() == HordeCrowd.SIM_DEFAULT, "simulated crowd is the boot default (%d)" % m.horde.alive_count())
	ok(m.horde.near_count() <= HordeCrowd.NEAR_CAP, "near combat actors stay pooled (%d)" % m.horde.near_count())
	print("COUNTS simulated=%d rendered=%d near=%d" % [m.horde.alive_count(), m.horde.rendered_count(), m.horde.near_count()])
	ok(m.horde.rendered_count() < 400, "the field is spread, not a gate-sized draw (%d rendered of %d simulated)" % [m.horde.rendered_count(), m.horde.alive_count()])
	var south_eye := Vector3(0, 1.7, 160)
	var through: int = m.horde.crowd.count_through_south(south_eye)
	var south_pack: int = m.horde.crowd.count_near(Vector3(0, 1, 200), 32.0)
	print("ENCOUNTER through_south_gate=%d near_outside_south=%d alive=%d" % [through, south_pack, m.horde.alive_count()])
	ok(through < 200, "the gate looks onto scattered field zombies, not the old packed mass (%d)" % through)
	ok(south_pack <= 12, "the south road holds at most a small group (%d)" % south_pack)
	var from_spawn: int = m.horde.crowd.count_through_south(Vector3(-6, 1.7, 26))
	ok(from_spawn <= 24, "town spawn does not look out on a packed gate (%d)" % from_spawn)
	var inside := 0
	var wedge := 0
	for e in m.party.director.enemies:
		if not (e is HordeZombie) or not e.alive(): continue
		if TownHaven.body_inside(Vector2(e.global_position.x, e.global_position.z), e.radius): inside += 1
		if TownHaven.in_escape_wedge(Vector2(e.global_position.x, e.global_position.z)): wedge += 1
	ok(inside == 0, "the crowd is outside the haven")
	ok(wedge == 0, "the northeast escape wedge is empty")
	var wolves := 0
	for e in m.party.director.enemies:
		if e is Enemy and not (e is HordeZombie) and e.alive() and str(e.type_id) == "wolf": wolves += 1
	ok(wolves == 3, "the wolf pack is still in the world (%d)" % wolves)
	m.hero.position = Vector3(0, m.hero.position.y, 150)
	m.yaw = PI
	var hp0: float = m.party.combat.hp
	for _i in 480: await physics_frame
	var far := 0.0
	var busy := 0
	for g in m.guards.guards:
		var d: float = (g.node as Node3D).global_position.distance_to(g.post)
		far = maxf(far, d)
		if g.tgt != null: busy += 1
	var still_through: int = m.horde.crowd.count_through_south(south_eye)
	print("GUARDS_HOLD farthest=%.2f busy=%d leash=%.0f through=%d alive=%d" % [far, busy, TownGuards.POST_LEASH, still_through, m.horde.alive_count()])
	ok(far <= TownGuards.POST_LEASH + 0.35, "guards stayed on the apron (farthest %.2f m)" % far)
	ok(busy == 0, "guards did not acquire the gathered horde (%d)" % busy)
	ok(still_through < 200, "the gate view stays the scattered field, not a horde (%d)" % still_through)
	ok(is_equal_approx(m.party.combat.hp, hp0), "standing inside the gate took no damage")
	print("HORDE_ENCOUNTER %d checks, %d failed" % [n, fails])
	quit(1 if fails else 0)

func _count_through(m, eye: Vector3) -> int:
	var c := 0
	for e in m.party.director.enemies:
		if e is HordeZombie and e.alive() and _through_gate(eye, e.global_position): c += 1
	return c

func _count_near(m, eye: Vector3, radius: float) -> int:
	var c := 0
	for e in m.party.director.enemies:
		if not (e is HordeZombie) or not e.alive(): continue
		if Vector2(e.global_position.x - eye.x, e.global_position.z - eye.z).length() <= radius: c += 1
	return c

func _through_gate(eye: Vector3, p: Vector3) -> bool:
	var lim := TownHaven.outer_limit()
	var half := TownHaven.gate_half() + 0.6
	var gates: Array[Vector2] = [Vector2(0, 1), Vector2(0, -1), Vector2(1, 0), Vector2(-1, 0)]
	for g in gates:
		var wall := g * lim
		var along := Vector2(-g.y, g.x)
		var eye2 := Vector2(eye.x, eye.z)
		var p2 := Vector2(p.x, p.z)
		var inward := -g
		if (eye2 - wall).dot(inward) <= 1.0: continue
		if (p2 - wall).dot(inward) >= -0.5: continue
		var denom: float = (p2 - eye2).dot(g)
		if absf(denom) < 0.001: continue
		var t: float = (wall - eye2).dot(g) / denom
		if t <= 0.0 or t >= 1.0: continue
		var hit: Vector2 = eye2 + (p2 - eye2) * t
		if absf((hit - wall).dot(along)) <= half: return true
	return false
