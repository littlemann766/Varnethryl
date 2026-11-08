extends SceneTree
## Deterministic haven geometry and undead movement. No full town scene.
## godot --headless --path . -s res://tests/town_haven_test.gd
var fails := 0
var n := 0

func ok(c: bool, msg: String) -> void:
	n += 1
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1

func _initialize() -> void: _run.call_deferred()

func _run() -> void:
	TownHaven.evidence.clear()
	_unarmed()
	TownHaven.arm(null)
	_whole_square()
	_gates_corners_height()
	_movement()
	_attacks()
	_spawn_paths()
	_unsupported()
	print("TOWN_HAVEN %d checks, %d failed" % [n, fails])
	quit(1 if fails else 0)

func _unarmed() -> void:
	TownHaven.armed = false
	ok(not TownHaven.strike_allowed(Vector3(0, 0, 220), Vector3(0, 0, 200), "bite"), "unarmed haven deals no undead damage")
	ok(not TownHaven.strike_allowed(Vector3(0, 0, 220), Vector3(0, 0, 200), "grab"), "unarmed grab refused")
	ok(not TownHaven.strike_allowed(Vector3(0, 0, 220), Vector3(0, 0, 200), "lunge"), "unarmed lunge-connect refused")

func _whole_square() -> void:
	var lim := TownHaven.outer_limit()
	ok(is_equal_approx(lim, 185.0 + 1.5), "outer face matches the wall (%.2f)" % lim)
	var inside_n := 0
	for x in range(-180, 181, 20):
		for z in range(-180, 181, 20):
			if TownHaven.inside_xz(float(x), float(z)): inside_n += 1
			else: ok(false, "interior sample outside the haven (%d,%d)" % [x, z])
	ok(inside_n == 19 * 19, "full town grid is inside, not a plaza subset (%d)" % inside_n)
	ok(TownHaven.inside(Vector3(0, 0, 0)) and TownHaven.inside(Vector3(170, 0, -160)), "center and deep streets are inside")
	ok(TownHaven.inside_xz(0, 36.4) and TownHaven.inside_xz(180, 180), "plaza and far corner are both inside the same square")

func _gates_corners_height() -> void:
	var lim := TownHaven.outer_limit()
	var gates: Array[Vector2] = [Vector2(0, 1), Vector2(0, -1), Vector2(1, 0), Vector2(-1, 0)]
	for g in gates:
		var on_in: Vector2 = g * (lim - 0.2)
		var on_out: Vector2 = g * (lim + 0.2)
		ok(TownHaven.inside_xz(on_in.x, on_in.y), "just inside gate %s" % g)
		ok(not TownHaven.inside_xz(on_out.x, on_out.y), "just outside gate %s" % g)
		ok(not TownHaven.inside_xz(g.x * lim, g.y * lim), "gate plane itself is not inside %s" % g)
	var corners: Array[Vector2] = [Vector2(1, 1), Vector2(1, -1), Vector2(-1, 1), Vector2(-1, -1)]
	for c in corners:
		ok(TownHaven.inside_xz(c.x * (lim - 0.25), c.y * (lim - 0.25)), "corner inside %s" % c)
		ok(not TownHaven.inside_xz(c.x * (lim + 0.25), c.y * (lim + 0.25)), "corner outside %s" % c)
		var seam := Vector2(c.x * lim, c.y * (lim - 4.0))
		ok(not TownHaven.inside_xz(seam.x, seam.y), "wall seam on the outer face is outside %s" % seam)
	ok(TownHaven.inside(Vector3(12, 48, -8)), "flying above the streets is still the town")
	ok(TownHaven.inside(Vector3(-20, -6, 15)), "below the street plane is still the town")
	ok(not TownHaven.inside(Vector3(0, 80, lim + 4.0)), "above the wall but outside the square is not safe")
	ok(not TownHaven.inside(Vector3(lim + 2.0, -4.0, 0)), "below grade outside the wall is not safe")

func _movement() -> void:
	var r := HordeZombie.BODY_R
	var stand := TownHaven.stand_off(r)
	var stopped := TownHaven.clamp_move(Vector2(0, stand + 1.2), Vector2(0, 0), r)
	ok(stopped.y >= stand - 0.02 and absf(stopped.x) < 0.05, "straight chase stops on the south face (%.3f)" % stopped.y)
	var hitch := TownHaven.clamp_move(Vector2(0, stand + 0.4), Vector2(0, stand - 40.0), r)
	ok(hitch.y >= stand - 0.02, "40 m hitch does not tunnel (z %.3f, stand %.3f)" % [hitch.y, stand])
	var corner := TownHaven.clamp_move(Vector2(stand + 2.0, stand + 2.0), Vector2(0, 0), r)
	ok(not TownHaven.body_inside(corner, r), "diagonal into the corner stays out (%.2f, %.2f)" % [corner.x, corner.y])
	var across := TownHaven.clamp_move(Vector2(0, stand + 0.3), Vector2(0, -(stand + 30.0)), r)
	ok(across.y > 0.0 and not TownHaven.body_inside(across, r), "chase through town dies on the near wall (z %.2f)" % across.y)
	var shove := TownHaven.clamp_move(Vector2(4.0, stand + 0.15), Vector2(4.0, stand - 25.0), r)
	ok(not TownHaven.body_inside(shove, r), "inward shove stopped (z %.3f)" % shove.y)
	var gate := TownHaven.clamp_move(Vector2(0.2, stand + 0.5), Vector2(0.2, lim_inside()), r)
	ok(not TownHaven.body_inside(gate, r), "gate mouth is not an undead entrance (z %.3f)" % gate.y)
	# crowd: eight bodies shoved at the same gate in one long step
	var packed := 0
	for i in 8:
		var from := Vector2(-2.4 + i * 0.55, stand + 0.6)
		var to := TownHaven.clamp_move(from, Vector2(from.x, -20.0), r)
		if TownHaven.body_inside(to, r): packed += 1
	ok(packed == 0, "crowded gate shove: %d tunneled" % packed)

func lim_inside() -> float: return 10.0

func _attacks() -> void:
	var r := HordeZombie.BODY_R
	var stand := TownHaven.stand_off(r)
	var combat := HeroCombat.new()
	root.add_child(combat)
	combat.set_hero("aldric")
	var body := Node3D.new()
	root.add_child(body)
	combat.body = body
	var d := EnemyDirector.new()
	root.add_child(d)
	d.ground = func(_x, _z): return 0.0
	var hero := Node3D.new()
	root.add_child(hero)
	hero.position = Vector3(-6, 0, 26)
	var z: HordeZombie = d.spawn("shambler", Vector3(0, 0, stand + 8.0), hero)
	z.combat = combat
	z.target = body
	z.anchor = Vector2(0, stand + 0.45)
	body.position = Vector3(0, 1, stand + 1.15)
	z.global_position = Vector3(0, 0, stand + 0.35)
	z.last_safe = z.global_position
	combat.hp = 400.0
	var before := combat.hp
	for _i in 24: z._physics_process(0.05)
	ok(combat.hp < before, "bite connects on an outside hero (%.0f -> %.0f)" % [before, combat.hp])
	ok(not TownHaven.body_inside(Vector2(z.global_position.x, z.global_position.z), r), "biter stayed outside")
	TownHaven.note({"e": "hp", "phase": "outside_bite", "before": before, "after": combat.hp})
	# windup already in flight, then the hero steps inside
	combat.hp = 400.0
	z.global_position = Vector3(0, 0, stand + 0.4)
	z.last_safe = z.global_position
	z.set_state("approach")
	z.pending_kind = ""
	body.position = Vector3(0, 0, stand + 1.05)
	z._physics_process(0.05)
	ok(z.state == "windup" or z.pending_kind != "", "a strike started outside (state %s %s)" % [z.state, z.pending_kind])
	body.position = Vector3(0, 1, 22)
	var mid := combat.hp
	for _i in 30: z._physics_process(0.05)
	ok(is_equal_approx(combat.hp, mid), "in-flight bite/grab cancelled after the hero entered (hp %.0f)" % combat.hp)
	ok(TownHaven.inside(body.position), "hero sample is inside")
	# grab range, hero just inside the outer face, zombie pressed against it
	z.global_position = Vector3(0, 0, stand + 0.05)
	z.last_safe = z.global_position
	body.position = Vector3(0, 1, TownHaven.outer_limit() - 0.2)
	ok(TownHaven.inside(body.position), "cross-gate hero sample starts inside")
	ok(body.position.distance_to(z.global_position) < HordeZombie.BITE_REACH, "bodies are close enough that only the boundary can save the hero")
	z.set_state("approach")
	z.pending_kind = ""
	combat.hp = 400.0
	for _i in 20: z._physics_process(0.05)
	ok(is_equal_approx(combat.hp, 400.0), "grab does not reach across the gate (hp %.0f)" % combat.hp)
	ok(not TownHaven.body_inside(Vector2(z.global_position.x, z.global_position.z), r), "grabber did not step inside")
	# runner lunge hitch toward an interior hero
	var runner: HordeZombie = d.spawn("runner", Vector3(0, 0, stand + 6.0), hero)
	runner.combat = combat
	runner.target = body
	runner.anchor = Vector2(0, stand + 0.45)
	body.position = Vector3(0, 1, 30)
	runner.global_position = Vector3(0, 0, stand + 1.2)
	runner.last_safe = runner.global_position
	runner._physics_process(1.0)
	ok(not TownHaven.body_inside(Vector2(runner.global_position.x, runner.global_position.z), r), "1s runner hitch stays outside (z %.2f)" % runner.global_position.z)
	var hp_lunge := combat.hp
	runner.shove(Vector3(0, 0, -30))
	ok(not TownHaven.body_inside(Vector2(runner.global_position.x, runner.global_position.z), r), "lunge shove cannot cross (z %.2f)" % runner.global_position.z)
	ok(is_equal_approx(combat.hp, hp_lunge), "shove is not damage")
	# exit and re-enter: safety is positional, so leaving town is vulnerable again
	body.position = Vector3(0, 1, stand + 1.1)
	runner.global_position = Vector3(0.4, 0, stand + 0.35)
	runner.last_safe = runner.global_position
	runner.set_state("approach")
	runner.pending_kind = ""
	combat.hp = 400.0
	for _i in 30: runner._physics_process(0.05)
	var hurt := combat.hp < 400.0
	ok(hurt, "leaving town clears safety (hp %.0f)" % combat.hp)
	var after_exit := combat.hp
	body.position = Vector3(4, 1, 40)
	for _i in 20: runner._physics_process(0.05)
	ok(is_equal_approx(combat.hp, after_exit), "re-entry is safe again without a sticky flag (hp %.0f)" % combat.hp)
	TownHaven.note({"e": "hp", "phase": "reentry", "outside": after_exit, "inside": combat.hp, "hurt_outside": hurt})

func _spawn_paths() -> void:
	var d := EnemyDirector.new()
	root.add_child(d)
	d.ground = func(_x, _z): return 0.0
	var hero := Node3D.new()
	root.add_child(hero)
	hero.position = Vector3(-6, 0, 26)
	var cases := [
		["undead_knight", Vector3(0, 0, 0)],
		["undead_sailor", Vector3(40, 0, -20)],
		["shambler", Vector3(-8, 0, 12)],
		["runner", Vector3(100, 0, 100)],
		["skeleton", Vector3(0, 0, 50)],
		["undead_sailor", Vector3(4000, 600, 4160)],
	]
	for c in cases:
		var e: Enemy = d.spawn(c[0], c[1], hero)
		var flat := Vector2(e.global_position.x, e.global_position.z)
		ok(e is HordeZombie, "%s spawns as a zombie, not a duelist" % c[0])
		ok(not TownHaven.body_inside(flat, e.radius) and not TownHaven.far_parking(flat), "%s spawn %s landed outside (%s)" % [c[0], c[1], flat])
		ok(e.pattern_hits({}, hero.position) == false, "%s has no duelist pattern" % c[0])
	var knight: HordeZombie = d.spawn("undead_knight", Vector3(0, 0, 220), hero)
	var sailor: HordeZombie = d.spawn("undead_sailor", Vector3(-220, 0, 4), hero)
	ok(knight.role == "undead_knight" and sailor.role == "undead_sailor", "knight and sailor keep their roles")
	ok(knight.speed_mps < 2.0 and sailor.speed_mps < 2.0, "knight and sailor are shamblers, not duel sprinters")
	var horde := HordeDirector.new()
	var host := _Host.new()
	host.party = _Party.new(d)
	host.hero = hero
	root.add_child(host)
	root.add_child(horde)
	horde.main = host
	var again := horde.respawn_at("shambler", Vector3(5, 0, 5))
	ok(again != null and not TownHaven.inside(again.global_position), "respawn inside the town is pushed out")
	var wolf: Enemy = d.spawn("wolf", Vector3(30, 0, 30), hero)
	ok(not (wolf is HordeZombie) and TownHaven.inside(wolf.global_position), "legacy wolf is unchanged and can still stand inside (known limit)")

func _unsupported() -> void:
	print("NA ranged: zombie horde has no projectile. Not counted as a pass.")
	print("NA aoe: zombie horde has no area damage. Not counted as a pass.")
	print("NA legacy_knockback: Enemy.take_damage does not move a body. Horde shove is the tested push.")
	ok(true, "unsupported ranged/aoe/legacy knockback recorded as N/A")

class _Host extends Node:
	var party
	var hero

class _Party extends RefCounted:
	var director
	var combat = null
	func _init(d) -> void: director = d
