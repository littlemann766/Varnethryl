extends SceneTree
## World probes for the horde prototype: exclusion, gates, leash, saves, interior.
## VARN_LITE=1 is set here. godot --headless --path . -s res://tests/horde_world_test.gd
const SAVE := "user://guildbound_rpg_save_v1.json"
var fails := 0
var n := 0
var VSave

func ok(c: bool, msg: String) -> void:
	n += 1
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1

func _initialize() -> void: _run.call_deferred()

func f(k: int) -> void:
	for _i in k:
		await physics_frame

func _run() -> void:
	OS.set_environment("VARN_LITE", "1")
	OS.set_environment("VARN_NO_HORDE", "")
	await process_frame
	VSave = root.get_node("VSave")
	var had := FileAccess.file_exists(SAVE)
	var bytes := FileAccess.get_file_as_bytes(SAVE) if had else PackedByteArray()
	var d := "user://horde_review_save/"
	DirAccess.make_dir_recursive_absolute(d)
	for name in DirAccess.get_files_at(d): DirAccess.remove_absolute(d + name)
	VSave.dir = d
	VSave.state = VSave.fresh_state()
	var m = _boot()
	_calm(m)
	_open_play(m)
	await _immediate(m)
	await _crowd(m)
	await _lane(m)
	await _damage_cycle(m)
	await _guards(m)
	await _interior(m)
	_lips(m)
	await _resume(m)
	await f(4)
	if had:
		var out := FileAccess.open(SAVE, FileAccess.WRITE)
		if out: out.store_buffer(bytes); out.close()
	else:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE))
	var ev := "/opt/cursor/artifacts/horde_evidence.json"
	DirAccess.make_dir_recursive_absolute("/opt/cursor/artifacts")
	TownHaven.write_evidence(ev)
	print("TOWN_WORLD %d checks, %d failed" % [n, fails])
	quit(1 if fails else 0)

func _boot():
	var ps: PackedScene = load("res://main.tscn")
	var m = ps.instantiate()
	root.add_child(m)
	return m

func _calm(m) -> void:
	if m.cheats:
		m.cheats.flags.god = false
		m.cheats.flags.bump = false
	if m.party and m.party.combat:
		m.party.combat.hp = m.party.combat.max_hp

func _immediate(m) -> void:
	ok(TownHaven.armed, "haven is armed before the first awaited physics frame")
	ok(m.undead_boundary != null, "boundary sweep exists at load")
	var hero_at := Vector2(m.hero.position.x, m.hero.position.z)
	var hp0: float = m.party.combat.hp
	var inside := 0
	for e in m.party.director.enemies:
		if TownHaven.is_undead_enemy(e) and TownHaven.body_inside(Vector2(e.global_position.x, e.global_position.z), e.radius):
			inside += 1
	ok(inside == 0, "ready() left no undead inside (%d)" % inside)
	var planted: Enemy = m.party.director.spawn("undead_knight", m.hero.global_position, m.hero)
	planted.global_position = m.hero.global_position
	(planted as HordeZombie).last_safe = Vector3(0, 0, 230)
	var expelled: int = m.undead_boundary.sweep()
	ok(expelled >= 1, "sweep expels a scripted interior undead before AI (%d)" % expelled)
	ok(not TownHaven.inside(planted.global_position), "expelled knight is outside")
	ok(Vector2(m.hero.position.x, m.hero.position.z).distance_to(hero_at) < 0.001, "sweep does not move the hero")
	ok(is_equal_approx(m.party.combat.hp, hp0), "no damage before the first physics frame")
	TownHaven.note({"e": "load_guard", "hero_x": hero_at.x, "hero_z": hero_at.y, "hp": hp0, "expelled": expelled})
	if planted.alive(): planted.kill_now(Vector3.ZERO)

func _open_play(m) -> void:
	var ui = root.get_node("VUI")
	if ui and ui.title: ui.title.hide()
	if ui and ui.hud: ui.hud.visible = true

func _crowd(m) -> void:
	var slow := 0
	var runners := 0
	var knights := 0
	var sailors := 0
	for e in m.party.director.enemies:
		if not (e is HordeZombie) or not e.alive(): continue
		if e.role == "runner": runners += 1
		elif e.role == "undead_knight": knights += 1
		elif e.role == "undead_sailor": sailors += 1
		else: slow += 1
	ok(slow >= 8 and knights == 2 and sailors == 2 and runners == 4, "crowd %d shambler / %d knight / %d sailor / %d runner" % [slow, knights, sailors, runners])
	ok(runners < slow + knights + sailors, "mostly shamblers")
	var wedge_slots := 0
	for spec in HordeDirector.ROSTER:
		var p: Vector3 = HordeDirector.spawn_pos(spec)
		if TownHaven.in_escape_wedge(Vector2(p.x, p.z)): wedge_slots += 1
	ok(wedge_slots == 0, "no roster slot seals the northeast escape wedge")
	m.horde.hear(Vector3(8, 0, 12), 36.0)
	ok(not TownHaven.inside_xz(m.horde.noise_at.x, m.horde.noise_at.y), "noise inside town is heard on the outside perimeter")
	var hp0: float = m.party.combat.hp
	m.hero.position = Vector3(-6, m.hero.position.y, 26)
	await f(180)
	var bad := 0
	var in_wedge := 0
	for e in m.party.director.enemies:
		if not (e is HordeZombie) or not e.alive(): continue
		if TownHaven.body_inside(Vector2(e.global_position.x, e.global_position.z), e.radius): bad += 1
		if TownHaven.in_escape_wedge(Vector2(e.global_position.x, e.global_position.z)): in_wedge += 1
	ok(bad == 0, "after 3s none of the crowd entered (%d)" % bad)
	ok(in_wedge == 0, "escape wedge stayed open while the hero was in town (%d)" % in_wedge)
	ok(is_equal_approx(m.party.combat.hp, hp0), "town interior took no horde damage")
	ok(m.horde.alive_count() <= HordeDirector.CAP and m.horde.corpse_count() <= HordeDirector.CORPSE_CAP, "caps held (alive %d corpses %d)" % [m.horde.alive_count(), m.horde.corpse_count()])

func _lane(m) -> void:
	var blocked := 0
	var lim := TownHaven.outer_limit()
	for z in [lim + 2.0, lim + 8.0, lim + 14.0]:
		if m.town_defense.lane_blocked(Vector2(0, z), 0.4): blocked += 1
		if m.town_defense.lane_blocked(Vector2(z, 0), 0.4): blocked += 1
		if m.town_defense.lane_blocked(Vector2(0, -z), 0.4): blocked += 1
		if m.town_defense.lane_blocked(Vector2(-z, 0), 0.4): blocked += 1
	ok(blocked == 0, "gate center lanes are clear of barricades (%d blocked samples)" % blocked)
	m.hero.position = Vector3(0, 0.2, lim + 16.0)
	m.hero.velocity = Vector3.ZERO
	m.yaw = 0.0
	m.joy_vec = Vector2(0, -1)
	var z0: float = m.hero.position.z
	await f(220)
	m.joy_vec = Vector2.ZERO
	ok(m.hero.position.z < lim - 2.0, "hero walked in through the south gate (%.1f -> %.1f)" % [z0, m.hero.position.z])
	ok(TownHaven.inside(m.hero.position), "arrived inside the town")

func _damage_cycle(m) -> void:
	var stand := TownHaven.stand_off(HordeZombie.BODY_R)
	var z: HordeZombie = null
	for e in m.party.director.enemies:
		if e is HordeZombie and e.alive() and e.role == "shambler":
			z = e
			break
	ok(z != null, "a shambler is available")
	if z == null: return
	for g in m.guards.guards:
		g.down_t = 20.0
		g.tgt = null
	z.global_position = Vector3(0, 0, stand + 0.35)
	z.last_safe = z.global_position
	z.anchor = Vector2(0, stand + 0.45)
	m.hero.position = Vector3(0.2, 0.2, stand + 1.15)
	m.party.combat.hp = m.party.combat.max_hp
	var hp_out: float = m.party.combat.hp
	await f(90)
	ok(m.party.combat.hp < hp_out, "outside the gate the horde can hurt (%.0f -> %.0f)" % [hp_out, m.party.combat.hp])
	var mid: float = m.party.combat.hp
	m.hero.position = Vector3(0.2, 0.2, 40)
	await f(90)
	ok(is_equal_approx(m.party.combat.hp, mid), "back inside, damage stops (%.0f)" % m.party.combat.hp)
	z.global_position = Vector3(0, 0, stand + 0.35)
	z.last_safe = z.global_position
	m.hero.position = Vector3(0.2, 0.2, stand + 1.15)
	await f(90)
	ok(m.party.combat.hp < mid, "stepping back out is vulnerable again (%.0f)" % m.party.combat.hp)
	TownHaven.note({"e": "hp_cycle", "outside": hp_out, "after_out": mid, "after_in": mid, "after_reexit": m.party.combat.hp})

func _guards(m) -> void:
	ok(m.guards != null and m.guards.guards.size() >= 6, "guards still man the gates")
	for g in m.guards.guards:
		g.down_t = 0.0
		g.tgt = null
		g.hp = TownGuards.MAX_HP
		g.ret = false
	for e in m.party.director.living():
		if e is HordeZombie: e.kill_now(Vector3.ZERO)
	await f(5)
	var runner: HordeZombie = m.party.director.spawn("runner", Vector3(0, 0, 260), m.hero)
	m.hero.position = Vector3(0, 0.2, 40)
	await f(30)
	var chasing := 0
	for g in m.guards.guards:
		if g.tgt == runner: chasing += 1
	ok(chasing == 0, "a runner 75 m past the post does not pull guards (%d)" % chasing)
	runner.global_position = Vector3(0, 0, 200)
	runner.last_safe = runner.global_position
	await f(45)
	var answered := 0
	for g in m.guards.guards:
		if g.tgt == runner: answered += 1
	ok(answered > 0 and answered <= 3, "nearby approach is answered by a few guards (%d)" % answered)
	var posts := []
	for g in m.guards.guards:
		posts.append(g.post)
	runner.global_position = Vector3(0, 0, 280)
	runner.last_safe = runner.global_position
	await f(40)
	var still := 0
	for g in m.guards.guards:
		if g.tgt == runner: still += 1
	ok(still == 0, "kiting past the leash drops the target")
	if m.horde: m.horde.refill_t = 10000.0
	for e in m.party.director.living():
		if e != runner: e.kill_now(Vector3.ZERO)
	await f(700)
	var home := 0
	var busy := 0
	var farthest := 0.0
	for i in m.guards.guards.size():
		var g: Dictionary = m.guards.guards[i]
		var dist: float = (g.node as Node3D).global_position.distance_to(posts[i])
		farthest = maxf(farthest, dist)
		if g.tgt != null: busy += 1
		if g.tgt == null and dist < 12.0: home += 1
	ok(busy == 0 and farthest < 18.0, "guards are back on the gate beat, not out at the leash (farthest %.1f m, busy %d, on beat %d/%d)" % [farthest, busy, home, m.guards.guards.size()])
	for g in m.guards.guards:
		g.down_t = 30.0
		g.tgt = null
		g.hp = 0.0
	m.hero.position = Vector3(3, 0.2, 20)
	m.party.combat.hp = m.party.combat.max_hp
	var hp_dead: float = m.party.combat.hp
	await f(60)
	ok(is_equal_approx(m.party.combat.hp, hp_dead), "town stays safe while every guard is down")
	var bad := 0
	for e in m.party.director.enemies:
		if TownHaven.is_undead_enemy(e) and e.alive() and TownHaven.body_inside(Vector2(e.global_position.x, e.global_position.z), e.radius):
			bad += 1
	ok(bad == 0, "downed guards are not what keeps undead out (%d inside)" % bad)
	m.guards.queue_free()
	m.guards = null
	await f(30)
	ok(is_equal_approx(m.party.combat.hp, hp_dead), "town stays safe with no guard node at all")

func _interior(m) -> void:
	var inn: Dictionary = {}
	var farm: Dictionary = {}
	for b in m.buildings:
		if str(b.id) == "inn": inn = b
		if str(b.id) == "farmhouse": farm = b
		var p: Vector3 = (b.node as Node3D).global_position
		var want: bool = maxf(absf(p.x), absf(p.z)) < TownHaven.outer_limit()
		if TownHaven.inside(p) != want:
			ok(false, "building %s haven mismatch" % b.id)
	ok(not inn.is_empty() and TownHaven.inside((inn.node as Node3D).global_position), "the inn sits in the protected town")
	ok(not farm.is_empty() and not TownHaven.inside((farm.node as Node3D).global_position), "the farmhouse is outside the walls and is not the haven")
	m.interiors.enter(inn)
	await f(5)
	ok(TownHaven.town_interior_active() and TownHaven.hero_safe(m.hero.global_position), "inside the inn the hero is safe even though the cell is parked far away")
	var hp0: float = m.party.combat.hp
	var biter: HordeZombie = m.party.director.spawn("shambler", m.hero.global_position, m.hero)
	biter.global_position = m.hero.global_position + Vector3(0.6, 0, 0)
	biter.last_safe = Vector3(0, 0, 230)
	await f(40)
	ok(is_equal_approx(m.party.combat.hp, hp0), "a biter placed in the inn cell cannot hurt")
	ok(not TownHaven.far_parking(Vector2(biter.global_position.x, biter.global_position.z)), "that biter was expelled from the interior parking cell")
	m.interiors.exit()
	await f(5)
	ok(not TownHaven.town_interior_active(), "leaving the inn clears the interior flag")
	m._on_travel("town")
	ok(TownHaven.hero_safe(m.hero.global_position), "travel to town is safe")
	m._teleport(Vector3(240, 0, 30), 0.2)
	ok(not TownHaven.hero_safe(m.hero.global_position), "travel back outside is vulnerable again")
	m._on_travel("town")
	ok(TownHaven.hero_safe(m.hero.global_position), "a second return to town is safe again")

func _lips(m) -> void:
	var lim := TownHaven.city_half()
	var hi := 0.0
	var over := 0
	for side in 4:
		for i in 9:
			var t := -1.0 + 2.0 * float(i) / 8.0
			var p := Vector2.ZERO
			match side:
				0: p = Vector2(t * lim, lim)
				1: p = Vector2(t * lim, -lim)
				2: p = Vector2(lim, t * lim)
				_: p = Vector2(-lim, t * lim)
			if m._gate_mouth(p): continue
			var gy: float = m.height(p.x, p.y)
			hi = maxf(hi, gy)
			if gy > TownHaven.wall_h() - 2.5: over += 1
	print("TERRAIN_LIP max_ground=%.2f wall_top=%.1f samples_over=%d seals=%d" % [hi, TownHaven.wall_h(), over, m.wall_lip_count])
	ok(hi > 4.0 and hi < 20.0, "perimeter ground is real terrain, not flat zero (%.2f m)" % hi)
	ok(hi <= TownHaven.wall_h() - 2.5 or m.wall_lip_count >= 1, "ground within 2.5 m of the parapet got a stone cap (ground %.2f, seals %d)" % [hi, m.wall_lip_count])
	TownHaven.note({"e": "terrain_lip", "max_ground": hi, "wall_top": TownHaven.wall_h(), "seals": m.wall_lip_count})

func _resume(m) -> void:
	var inside := {"x": -6.25, "z": 26.5, "yaw": 0.4}
	var outside := {"x": 240.0, "z": 30.0, "yaw": -0.25}
	TownHaven.note({"e": "save_pre", "x": inside.x, "z": inside.z, "yaw": inside.yaw})
	ok(VSave.write_snapshot({"x": inside.x, "z": inside.z, "yaw": inside.yaw, "zone": "village", "hero": int(VSave.state.get("active", 0)), "at_sea": false, "at_interior": false}), "inside snapshot wrote")
	var disk: Dictionary = VSave.read_save().state
	ok(is_equal_approx(float(disk.p3d.x), inside.x) and is_equal_approx(float(disk.p3d.z), inside.z) and is_equal_approx(float(disk.p3d.yaw), inside.yaw), "saved inside position is exact on the 0.01 grid")
	ok(not disk.has("horde") and not disk.has("undead"), "save gained no horde blob")
	m.queue_free()
	await f(8)
	VSave.state = VSave.load_state()
	var m2 = _boot()
	_open_play(m2)
	_calm(m2)
	ok(TownHaven.armed, "relaunch arms the haven during ready, before play")
	var leaked := 0
	for e in m2.party.director.enemies:
		if TownHaven.is_undead_enemy(e) and TownHaven.body_inside(Vector2(e.global_position.x, e.global_position.z), e.radius): leaked += 1
	ok(leaked == 0 and is_equal_approx(m2.party.combat.hp, m2.party.combat.max_hp), "relaunch has not let undead inside or dealt damage")
	var before_play := Vector2(m2.hero.position.x, m2.hero.position.z)
	m2._on_play_solo()
	var at := Vector2(m2.hero.position.x, m2.hero.position.z)
	ok(is_equal_approx(at.x, inside.x) and is_equal_approx(at.y, inside.z), "play resumed the exact inside position (%.2f, %.2f)" % [at.x, at.y])
	ok(is_equal_approx(m2.yaw, inside.yaw), "yaw restored")
	ok(before_play.distance_to(at) > 0.5 or is_equal_approx(before_play.x, inside.x), "resume applied the save")
	ok(TownHaven.hero_safe(m2.hero.global_position), "resumed inside position is protected")
	var hp0: float = m2.party.combat.hp
	await f(30)
	ok(is_equal_approx(m2.party.combat.hp, hp0), "standing on the resumed inside spot takes no damage")
	TownHaven.note({"e": "save_post", "x": at.x, "z": at.y, "yaw": m2.yaw, "hp": m2.party.combat.hp})
	ok(VSave.write_snapshot({"x": outside.x, "z": outside.z, "yaw": outside.yaw, "zone": "village", "hero": int(VSave.state.get("active", 0)), "at_sea": false, "at_interior": false}), "outside snapshot wrote")
	VSave.state = VSave.load_state()
	m2._on_play_solo()
	var out2 := Vector2(m2.hero.position.x, m2.hero.position.z)
	ok(is_equal_approx(out2.x, outside.x) and is_equal_approx(out2.y, outside.z), "outside save stayed outside (%.2f, %.2f)" % [out2.x, out2.y])
	ok(not TownHaven.hero_safe(m2.hero.global_position), "outside resume is not sticky-safe")
	# the saved spot is far from the walls; bring one shambler to it
	var z: HordeZombie = null
	for e in m2.party.director.enemies:
		if e is HordeZombie and e.alive():
			z = e
			break
	if z:
		z.global_position = Vector3(outside.x, 0, outside.z + 0.8)
		z.last_safe = z.global_position
		z.anchor = Vector2(outside.x, outside.z + 0.8)
	m2.party.combat.hp = m2.party.combat.max_hp
	var hp_far: float = m2.party.combat.hp
	await f(80)
	ok(m2.party.combat.hp < hp_far, "the same horde hurts on an outside resume (%.0f -> %.0f)" % [hp_far, m2.party.combat.hp])
	ok(VSave.write_snapshot({"x": inside.x, "z": inside.z, "yaw": inside.yaw, "zone": "village", "hero": int(VSave.state.get("active", 0)), "at_sea": false, "at_interior": false}), "return snapshot wrote")
	VSave.state = VSave.load_state()
	m2._on_play_solo()
	ok(TownHaven.hero_safe(m2.hero.global_position), "resume back inside is protected again")
	var back: float = m2.party.combat.hp
	await f(40)
	ok(is_equal_approx(m2.party.combat.hp, back), "no lingering hit after the return")
	m2.queue_free()
