class_name HordeCrowd
extends Node
## Data-oriented horde. Thousands are simulated records with stable ids.
## The phone validation budget is SIM_DEFAULT records and NEAR_CAP bodies.
## SIM_MAX is a later device ceiling, not a claim the phone holds 4000.
## Only a small pool becomes HordeZombie bodies for nearby combat.
## Everyone else is a batched placeholder. Dead ids are never reused.

const SIM_DEFAULT := 1000
const NEAR_CAP := 16
## Visible budget matches the sim ceiling. Far capsules stay full world size.
## Detail tiers change how often a zombie is simulated, not how big it is drawn.
const RENDER_CAP := 4096
const MID_RADIUS := 80.0
const RENDER_RADIUS := 260.0
const NEAR_IN := 26.0
const NEAR_OUT := 42.0
const SIM_MAX := 4096
const COLS := 10
const ALONG := 1.7
const ROW := 1.85
const FRONT := 18.0
const BODY_R := 0.46
## Loose field groups. Centers sit on a 26 m grid so packs of 1–6 stay separated.
const GROUP_GAP := 26.0
const GROUP_MAX := 6
const WANDER_R := 5.5
const FIELD_MIN := 36.0
const FIELD_MAX := 680.0

const ROLE_NAME := ["shambler", "runner", "undead_knight", "undead_sailor"]
const ROLE_SPEED := [1.25, 3.35, 1.15, 1.20]
const ROLE_HP := [190.0, 140.0, 260.0, 240.0]
const ROLE_AGGRO := [18.0, 34.0, 18.0, 18.0]
const ROLE_ATK := [18.0, 16.0, 20.0, 18.0]
const BITE_REACH := 1.40
const BITE_HEIGHT := 2.5
const RECOVER := 0.65
## A promoted body stays on screen long enough for the death clip before the slot is released.
const DEATH_HOLD := 1.35
## How many of the packed crowd may swing at the hero at once.
const MAX_CONTACT := 4
const ROLE_WIND := [0.80, 0.80, 0.80, 0.80]
const FAR_RADIUS := 90.0
const FAR_STRIDE := 4

var director: HordeDirector
var target_n := SIM_DEFAULT
var alive_n := 0
var corpse_n := 0
var near_n := 0
var rendered_n := 0
var rendered_mid := 0
var rendered_far := 0
var render_cap := RENDER_CAP
var next_id := 1
var retired: Dictionary = {}

var id: PackedInt32Array = PackedInt32Array()
var px: PackedFloat32Array = PackedFloat32Array()
var pz: PackedFloat32Array = PackedFloat32Array()
var py: PackedFloat32Array = PackedFloat32Array()
var pycell: PackedInt32Array = PackedInt32Array()
var hp: PackedFloat32Array = PackedFloat32Array()
var hold_x: PackedFloat32Array = PackedFloat32Array()
var hold_z: PackedFloat32Array = PackedFloat32Array()
var role: PackedInt32Array = PackedInt32Array()
var gate: PackedInt32Array = PackedInt32Array()
var slot_i: PackedInt32Array = PackedInt32Array()
var flags: PackedInt32Array = PackedInt32Array() # 1 alive, 2 promoted
var pool_i: PackedInt32Array = PackedInt32Array()
var dead_for: PackedFloat32Array = PackedFloat32Array()
var bite_cd: PackedFloat32Array = PackedFloat32Array()
var wind_t: PackedFloat32Array = PackedFloat32Array()
var lock_t: PackedFloat32Array = PackedFloat32Array()
var face: PackedFloat32Array = PackedFloat32Array()
var strike_budget := MAX_CONTACT
var impacts_frame := 0
var impacts_total := 0

var pool: Array = []
var _tick := 0
var _sea = null
var bites := 0
var guard_hits := 0
var prof_us := {"sync": 0, "integrate": 0, "draw": 0, "promote": 0, "frames": 0}
var _meshes: Array = []
var _free: Array = []
var _scratch: Array = []
var _homes: Array[Vector2] = []
var _home_i := 0
var _contact: PackedInt32Array = PackedInt32Array()
var _contact_n := 0
var _sep_idx: PackedInt32Array = PackedInt32Array()

func setup(host: HordeDirector, count: int) -> void:
	director = host
	target_n = clampi(count, 1, SIM_MAX)
	var raw := OS.get_environment("VARN_HORDE_RENDER")
	if raw.is_valid_int(): render_cap = clampi(int(raw), 1, SIM_MAX)
	_build_pool()
	_build_meshes()
	_build_homes(target_n)
	ensure_count(target_n)

func ensure_count(n: int) -> int:
	target_n = clampi(n, alive_n, SIM_MAX)
	var guard := 0
	while alive_n < target_n and guard < target_n + 4:
		_spawn_new(_pick_gate(), -1)
		guard += 1
	return alive_n

func step(dt: float) -> void:
	if director == null or director.main == null or director.main.hero == null: return
	var hero: Vector3 = director.main.hero.global_position
	var hero_safe := TownHaven.hero_safe(hero)
	strike_budget = MAX_CONTACT
	impacts_frame = 0
	var t0 := Time.get_ticks_usec()
	_sync_promoted()
	_settle_illegal()
	_demote_far(hero)
	_reap(dt)
	prof_us.sync += int(Time.get_ticks_usec() - t0)
	t0 = Time.get_ticks_usec()
	_integrate(dt, hero, hero_safe)
	_guard_contact()
	prof_us.integrate += int(Time.get_ticks_usec() - t0)
	t0 = Time.get_ticks_usec()
	_promote(hero)
	prof_us.promote += int(Time.get_ticks_usec() - t0)
	t0 = Time.get_ticks_usec()
	_draw(hero)
	prof_us.draw += int(Time.get_ticks_usec() - t0)
	prof_us.frames += 1
	if alive_n < target_n and OS.get_environment("VARN_NO_HORDE_REFILL") == "":
		director.refill_t -= dt
		if director.refill_t <= 0.0:
			director.refill_t = HordeDirector.REFILL_SEC
			_spawn_new(_pick_gate(), -1)

func damage_index(i: int, dmg: int) -> bool:
	if i < 0 or i >= flags.size(): return false
	if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: return false
	_hurt(i, dmg)
	return true

func nearest_unpromoted(origin: Vector2, range_m: float) -> int:
	var best := -1
	var bd := range_m
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		var d := Vector2(px[i], pz[i]).distance_to(origin) - BODY_R
		if d < bd:
			bd = d
			best = i
	return best

func damage_shape(sk: Dictionary, center: Vector2, fwd: Vector2, reach: float, dmg: int) -> int:
	var hit := 0
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		if CombatRules.in_shape(sk, center, fwd, Vector2(px[i], pz[i]), BODY_R, reach):
			_hurt(i, dmg)
			hit += 1
	return hit

func kill_disk(center: Vector2, radius: float) -> int:
	var hit := 0
	var r2 := radius * radius
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		var dx := px[i] - center.x
		var dz := pz[i] - center.y
		if dx * dx + dz * dz <= r2:
			_kill(i)
			hit += 1
	return hit

func role_counts() -> Dictionary:
	var c := {"shambler": 0, "runner": 0, "undead_knight": 0, "undead_sailor": 0}
	for i in id.size():
		if (flags[i] & 1) == 0: continue
		c[ROLE_NAME[role[i]]] += 1
	return c

func inside_count() -> int:
	var n := 0
	for i in id.size():
		if (flags[i] & 1) == 0: continue
		if TownHaven.body_inside(Vector2(px[i], pz[i]), BODY_R): n += 1
	return n

func count_near(eye: Vector3, radius: float) -> int:
	var n := 0
	var r2 := radius * radius
	for i in id.size():
		if (flags[i] & 1) == 0: continue
		var dx := px[i] - eye.x
		var dz := pz[i] - eye.z
		if dx * dx + dz * dz <= r2: n += 1
	return n

func count_through_south(eye: Vector3) -> int:
	var n := 0
	var lim := TownHaven.outer_limit()
	var half := TownHaven.gate_half() + 0.6
	for i in id.size():
		if (flags[i] & 1) == 0: continue
		if pz[i] <= lim: continue
		var denom := pz[i] - eye.z
		if absf(denom) < 0.001: continue
		var t := (lim - eye.z) / denom
		if t <= 0.0 or t >= 1.0: continue
		var x_hit := eye.x + (px[i] - eye.x) * t
		if absf(x_hit) <= half: n += 1
	return n

func wedge_count() -> int:
	var n := 0
	for i in id.size():
		if (flags[i] & 1) == 0: continue
		if TownHaven.in_escape_wedge(Vector2(px[i], pz[i])): n += 1
	return n

func id_alive(sim_id: int) -> bool:
	var i := _index_of(sim_id)
	return i >= 0 and (flags[i] & 1) != 0

func kill_id(sim_id: int) -> void:
	var i := _index_of(sim_id)
	if i >= 0 and (flags[i] & 1) != 0: _kill(i)

func deploy_actor(role_name: String) -> HordeZombie:
	for i in id.size():
		if (flags[i] & 1) == 0: continue
		if ROLE_NAME[role[i]] != role_name: continue
		_promote_index(i, director.main.hero.global_position)
		return pool[pool_i[i]]
	return null

func ids_snapshot() -> PackedInt32Array:
	var out := PackedInt32Array()
	for i in id.size():
		if (flags[i] & 1) != 0: out.append(id[i])
	return out

static func gate_dir(g: int) -> Vector2:
	match g:
		1: return Vector2(0, -1)
		2: return Vector2(1, 0)
		3: return Vector2(-1, 0)
		_: return Vector2(0, 1)

static func formation_xz(g: int, slot: int) -> Vector2:
	var col := slot % COLS
	var row := int(slot / COLS)
	var along := (float(col) - float(COLS - 1) * 0.5) * ALONG
	var out := FRONT + float(row) * ROW
	var dir := gate_dir(g)
	var side := Vector2(-dir.y, dir.x)
	var p := dir * (TownHaven.outer_limit() + out) + side * along
	if TownHaven.in_escape_wedge(p):
		p += side * (8.0 if along >= 0.0 else -8.0)
	if TownHaven.body_inside(p, BODY_R) or TownHaven.obstacle_hit(p, BODY_R):
		p = TownHaven.nearest_outside(p, BODY_R)
	return p

func _build_pool() -> void:
	if pool.size() > 0: return
	var ground: Callable = director.main.party.director.ground if director.main and director.main.get("party") else Callable()
	var hero: Node3D = director.main.hero
	for i in NEAR_CAP:
		var z := HordeZombie.new()
		z.name = "HordePool%d" % i
		add_child(z)
		z.bind_crowd("shambler", Vector3(0, -40, 0), 1.0, hero, ground, Vector2.ZERO, -1)
		z.release_crowd()
		pool.append(z)

func _build_meshes() -> void:
	if _meshes.size() > 0: return
	for r in ROLE_NAME.size():
		var mi := MultiMeshInstance3D.new()
		mi.name = "HordeBatch_%s" % ROLE_NAME[r]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_custom_data = true
		var card := QuadMesh.new()
		card.size = Vector2(1.0687, 2.1374)
		card.center_offset = Vector3(0.0, 1.0687, 0.0)
		var mat := ShaderMaterial.new()
		mat.shader = load("res://validation/hooded_male/impostor_billboard.gdshader")
		mat.set_shader_parameter("atlas", load("res://assets/hooded_candidate/far_impostor/impostor_atlas_8dir_1024.png"))
		mat.set_shader_parameter("view_bias", 4.0)
		card.material = mat
		mm.mesh = card
		mm.instance_count = maxi(render_cap, 1)
		mm.visible_instance_count = 0
		mi.multimesh = mm
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_meshes.append(mi)

func _spawn_new(g: int, slot: int) -> int:
	var use := -1
	if _free.size() > 0:
		use = int(_free.pop_back())
	else:
		use = id.size()
		id.push_back(0)
		px.push_back(0.0)
		pz.push_back(0.0)
		py.push_back(0.7)
		pycell.push_back(1 << 30)
		hp.push_back(0.0)
		hold_x.push_back(0.0)
		hold_z.push_back(0.0)
		role.push_back(0)
		gate.push_back(0)
		slot_i.push_back(0)
		flags.push_back(0)
		pool_i.push_back(-1)
		dead_for.push_back(0.0)
		bite_cd.push_back(0.0)
		wind_t.push_back(0.0)
		lock_t.push_back(0.0)
		face.push_back(0.0)
	if slot < 0: slot = _home_i
	var sim := next_id
	next_id += 1
	var rr := _role_for_id(sim)
	var hold := _next_home()
	pycell[use] = 1 << 30
	id[use] = sim
	role[use] = rr
	gate[use] = g
	slot_i[use] = slot
	hold_x[use] = hold.x
	hold_z[use] = hold.y
	px[use] = hold.x
	pz[use] = hold.y
	hp[use] = ROLE_HP[rr]
	flags[use] = 1
	pool_i[use] = -1
	dead_for[use] = 0.0
	bite_cd[use] = 0.0
	wind_t[use] = 0.0
	lock_t[use] = 0.0
	face[use] = 0.0
	alive_n += 1
	return sim

func _gate_share(g: int) -> int:
	var south := int(target_n * 0.5)
	var north := int(target_n * 0.18)
	var east := int(target_n * 0.16)
	var west := target_n - south - north - east
	match g:
		1: return north
		2: return east
		3: return west
		_: return south

func _pick_gate() -> int:
	var best := 0
	var best_n := -1000000
	for g in 4:
		var have := 0
		for i in id.size():
			if (flags[i] & 1) != 0 and gate[i] == g: have += 1
		var room := _gate_share(g) - have
		if room > best_n:
			best_n = room
			best = g
	return best

func _next_slot(g: int) -> int:
	var used := {}
	for i in id.size():
		if gate[i] == g and (flags[i] & 1) != 0: used[slot_i[i]] = true
	var s := 0
	while used.has(s): s += 1
	return s

func _role_for_id(sim: int) -> int:
	var roll := sim % 20
	if roll == 0: return 2
	if roll == 1: return 3
	if roll < 5: return 1
	return 0

func _home_ok(p: Vector2) -> bool:
	if p.length() < TownHaven.outer_limit() + FIELD_MIN: return false
	if p.length() > FIELD_MAX: return false
	if TownHaven.body_inside(p, BODY_R): return false
	if TownHaven.in_escape_wedge(p): return false
	if TownHaven.far_parking(p): return false
	if TownHaven.obstacle_hit(p, BODY_R): return false
	return not _on_sea(p.x, p.y)

func _build_homes(n: int) -> void:
	if _homes.size() >= n: return
	var rng := RandomNumberGenerator.new()
	rng.seed = 60060
	var cells: Array[Vector2] = []
	var x := -FIELD_MAX
	while x <= FIELD_MAX:
		var z := -FIELD_MAX
		while z <= FIELD_MAX:
			var c := Vector2(x, z)
			if _home_ok(c): cells.append(c)
			z += GROUP_GAP
		x += GROUP_GAP
	for i in range(cells.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var swap: Vector2 = cells[i]
		cells[i] = cells[j]
		cells[j] = swap
	var ci := 0
	while _homes.size() < n and ci < cells.size():
		var center: Vector2 = cells[ci]
		ci += 1
		var room := mini(rng.randi_range(1, GROUP_MAX), n - _homes.size())
		for m in room:
			var spot := center
			if m > 0:
				var ang := rng.randf() * TAU
				var rad := rng.randf_range(1.8, 5.0)
				var try_p := center + Vector2(cos(ang), sin(ang)) * rad
				if _home_ok(try_p): spot = try_p
			_homes.append(spot)
	var extra := 0
	while _homes.size() < n and extra < n * 4:
		extra += 1
		var ang := rng.randf() * TAU
		var rad := rng.randf_range(TownHaven.outer_limit() + FIELD_MIN + 8.0, FIELD_MAX - 8.0)
		var p := Vector2(cos(ang), sin(ang)) * rad
		if not _home_ok(p): continue
		var crowded := false
		for h in _homes:
			if h.distance_to(p) < GROUP_GAP * 0.85:
				crowded = true
				break
		if not crowded: _homes.append(p)

func _next_home() -> Vector2:
	if _home_i >= _homes.size(): _build_homes(_homes.size() + 32)
	if _home_i >= _homes.size():
		return Vector2(0.0, TownHaven.outer_limit() + FIELD_MIN + 8.0)
	var h: Vector2 = _homes[_home_i]
	_home_i += 1
	return h

func _wander_at(i: int) -> Vector2:
	var phase := float(id[i]) * 0.37 + float(_tick) * 0.035
	var w := Vector2(hold_x[i] + cos(phase) * WANDER_R, hold_z[i] + sin(phase * 0.81) * WANDER_R)
	if not _home_ok(w): return Vector2(hold_x[i], hold_z[i])
	return w

func _role_for(g: int, slot: int) -> int:
	if g == 1 and slot < 2: return 2
	if g == 2 and slot < 2: return 3
	if slot % 7 == 3: return 1
	return 0

func _sync_promoted() -> void:
	near_n = 0
	for i in id.size():
		if (flags[i] & 2) == 0: continue
		var z: HordeZombie = pool[pool_i[i]]
		if not is_instance_valid(z) or z.crowd_id != id[i]:
			flags[i] = flags[i] & ~2
			pool_i[i] = -1
			continue
		if not z.alive():
			if z.dead_for < DEATH_HOLD:
				near_n += 1
				continue
			_kill(i)
			continue
		px[i] = z.global_position.x
		pz[i] = z.global_position.z
		hp[i] = z.hp
		_copy_attack(i, z)
		near_n += 1

func _demote_far(hero: Vector3) -> void:
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) == 0: continue
		if Vector2(px[i] - hero.x, pz[i] - hero.z).length() <= NEAR_OUT: continue
		var z: HordeZombie = pool[pool_i[i]]
		if is_instance_valid(z) and not z.alive(): continue
		if is_instance_valid(z) and z.alive():
			px[i] = z.global_position.x
			pz[i] = z.global_position.z
			hp[i] = z.hp
			_copy_attack(i, z)
			var d: EnemyDirector = director.main.party.director
			d.enemies.erase(z)
			z.release_crowd()
		flags[i] = flags[i] & ~2
		pool_i[i] = -1
		near_n = maxi(0, near_n - 1)

func _integrate(dt: float, hero: Vector3, hero_safe: bool) -> void:
	_tick += 1
	var noise := director.noise_r > 0.0
	var nx0 := director.noise_at.x
	var nz0 := director.noise_at.y
	var nr := director.noise_r
	var phase := _tick & 3
	var far2 := FAR_RADIUS * FAR_RADIUS
	var combat = director.main.party.combat if director.main.get("party") else null
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		var dx := hero.x - px[i]
		var dz := hero.z - pz[i]
		var d2 := dx * dx + dz * dz
		var border := _near_hazard(px[i], pz[i])
		var far := d2 > far2 and not border
		if far and (i & 3) != phase: continue
		var used := dt * (float(FAR_STRIDE) if far else 1.0)
		if lock_t[i] > 0.0: lock_t[i] = maxf(0.0, lock_t[i] - used)
		var dist := sqrt(d2)
		var tx := hold_x[i]
		var tz := hold_z[i]
		var rr: int = role[i]
		if not hero_safe and dist <= ROLE_AGGRO[rr] and absf(hero.y - _feet_y(i)) <= BITE_HEIGHT:
			tx = hero.x
			tz = hero.z
		elif noise:
			var ndx := px[i] - nx0
			var ndz := pz[i] - nz0
			if ndx * ndx + ndz * ndz <= nr * nr:
				tx = nx0
				tz = nz0
		else:
			var wander := _wander_at(i)
			tx = wander.x
			tz = wander.y
		var fdx := tx - px[i]
		var fdz := tz - pz[i]
		if fdx * fdx + fdz * fdz > 0.0004:
			face[i] = atan2(-fdx, -fdz)
		var mx := tx - px[i]
		var mz := tz - pz[i]
		var md2 := mx * mx + mz * mz
		if md2 < 0.014: continue
		var md := sqrt(md2)
		var step := minf(ROLE_SPEED[rr] * used, md)
		var nxt := _constrain(px[i], pz[i], px[i] + mx / md * step, pz[i] + mz / md * step)
		px[i] = nxt.x
		pz[i] = nxt.y
	if hero_safe:
		_clear_wind()
		return
	_pick_contact(hero)
	_separate_cluster(hero)
	_record_attacks(dt, hero, combat)

func claim_strike() -> bool:
	if strike_budget <= 0: return false
	strike_budget -= 1
	impacts_frame += 1
	impacts_total += 1
	return true

func _clear_wind() -> void:
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		wind_t[i] = 0.0

func _feet_y(i: int) -> float:
	return _sample_y(i) - 0.7

func _in_bite(i: int, hero: Vector3) -> bool:
	var dx := hero.x - px[i]
	var dz := hero.z - pz[i]
	if dx * dx + dz * dz > BITE_REACH * BITE_REACH: return false
	if absf(hero.y - _feet_y(i)) > BITE_HEIGHT: return false
	if TownHaven.body_inside(Vector2(px[i], pz[i]), BODY_R): return false
	return TownHaven.strike_allowed(Vector3(px[i], _feet_y(i), pz[i]), hero, "bite")

func _can_swing(i: int) -> bool:
	return (flags[i] & 1) != 0 and (flags[i] & 2) == 0 and lock_t[i] <= 0.0

func _is_contact(i: int) -> bool:
	for k in _contact_n:
		if _contact[k] == i: return true
	return false

func _pick_contact(hero: Vector3) -> void:
	if _contact.size() < MAX_CONTACT: _contact.resize(MAX_CONTACT)
	var kept := PackedInt32Array()
	for k in _contact_n:
		var prev: int = _contact[k]
		if prev < 0 or prev >= id.size(): continue
		if (flags[prev] & 1) == 0 or (flags[prev] & 2) != 0: continue
		if not _in_bite(prev, hero): continue
		kept.append(prev)
	_contact_n = 0
	for prev in kept:
		_contact[_contact_n] = prev
		_contact_n += 1
		if _contact_n >= MAX_CONTACT: return
	for i in id.size():
		if not _can_swing(i) or wind_t[i] <= 0.0: continue
		if _is_contact(i) or not _in_bite(i, hero): continue
		_contact[_contact_n] = i
		_contact_n += 1
		if _contact_n >= MAX_CONTACT: return
	var room := MAX_CONTACT - _contact_n
	var pick_i := PackedInt32Array()
	var pick_d := PackedFloat32Array()
	pick_i.resize(room)
	pick_d.resize(room)
	var have := 0
	for i in id.size():
		if not _can_swing(i) or _is_contact(i): continue
		if not _in_bite(i, hero): continue
		var d := Vector2(px[i] - hero.x, pz[i] - hero.z).length()
		if have < room:
			pick_i[have] = i
			pick_d[have] = d
			have += 1
			continue
		var worst := 0
		for k in room:
			if pick_d[k] > pick_d[worst]: worst = k
		if d < pick_d[worst]:
			pick_d[worst] = d
			pick_i[worst] = i
	for k in have:
		_contact[_contact_n] = pick_i[k]
		_contact_n += 1

func _separate_cluster(hero: Vector3) -> void:
	var n := 0
	var reach2 := 4.0 * 4.0
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		var dx := px[i] - hero.x
		var dz := pz[i] - hero.z
		if dx * dx + dz * dz > reach2: continue
		if _sep_idx.size() == n: _sep_idx.append(i)
		else: _sep_idx[n] = i
		n += 1
		if n >= 256: break
	if n < 2: return
	var sep := HordeZombie.SEPARATION
	for a in n:
		var i: int = _sep_idx[a]
		var pushx := 0.0
		var pushz := 0.0
		for b in n:
			if a == b: continue
			var j: int = _sep_idx[b]
			var ox := px[i] - px[j]
			var oz := pz[i] - pz[j]
			var d2 := ox * ox + oz * oz
			if d2 >= sep * sep: continue
			if d2 <= 0.0001:
				ox = 0.17 if (i & 1) == 0 else -0.13
				oz = 0.09 if (i & 2) == 0 else -0.11
				d2 = ox * ox + oz * oz
			var d := sqrt(d2)
			var overlap := sep - d
			pushx += ox / d * overlap
			pushz += oz / d * overlap
		var pl := sqrt(pushx * pushx + pushz * pushz)
		if pl < 0.001: continue
		if pl > 0.55:
			pushx = pushx / pl * 0.55
			pushz = pushz / pl * 0.55
		var nx := px[i] + pushx
		var nz := pz[i] + pushz
		if _is_contact(i):
			var hx := nx - hero.x
			var hz := nz - hero.z
			var hd := sqrt(hx * hx + hz * hz)
			var keep := BITE_REACH * 0.72
			if hd > keep and hd > 0.001:
				nx = hero.x + hx / hd * keep
				nz = hero.z + hz / hd * keep
		var nxt := _constrain(px[i], pz[i], nx, nz)
		px[i] = nxt.x
		pz[i] = nxt.y

func _record_attacks(dt: float, hero: Vector3, combat) -> void:
	for c in _contact_n:
		var i: int = _contact[c]
		if not _can_swing(i) or not _in_bite(i, hero): continue
		wind_t[i] += dt
		var need: float = ROLE_WIND[role[i]]
		if wind_t[i] < need: continue
		if not claim_strike():
			wind_t[i] = need
			continue
		wind_t[i] = 0.0
		lock_t[i] = RECOVER
		if combat != null: combat.take_hit(ROLE_ATK[role[i]], 1.0)
		bites += 1

func _copy_attack(i: int, z: HordeZombie) -> void:
	if z.crowd_lock > 0.0:
		lock_t[i] = z.crowd_lock
		wind_t[i] = 0.0
	elif z.state == "windup":
		wind_t[i] = z.t_state
		lock_t[i] = 0.0
	elif z.state == "recover":
		wind_t[i] = 0.0
		lock_t[i] = maxf(0.0, RECOVER - z.t_state)
	else:
		wind_t[i] = 0.0
		lock_t[i] = 0.0

func _near_hazard(x: float, z: float) -> bool:
	var lim := TownHaven.outer_limit()
	var m := maxf(absf(x), absf(z))
	if m > lim - 8.0 and m < lim + 24.0: return true
	if x < -380.0 and z > 250.0: return true
	return TownHaven.obstacles.size() > 0

func on_sea(x: float, z: float) -> bool:
	return _on_sea(x, z)

func illegal_at(x: float, z: float) -> bool:
	return _illegal(x, z)

func safe_point(x: float, z: float) -> Vector2:
	return _safe_point(x, z)

## One correction for a record and its body. Does not change id, HP, or cooldown.
func _settle_illegal() -> void:
	for i in id.size():
		if (flags[i] & 1) == 0: continue
		var zx := px[i]
		var zz := pz[i]
		var z: HordeZombie = null
		if (flags[i] & 2) != 0 and pool_i[i] >= 0:
			z = pool[pool_i[i]]
			if is_instance_valid(z) and z.alive():
				zx = z.global_position.x
				zz = z.global_position.z
			else:
				z = null
		if not _illegal(zx, zz): continue
		var safe := _safe_point(zx, zz)
		px[i] = safe.x
		pz[i] = safe.y
		pycell[i] = 1 << 30
		if z == null: continue
		z.global_position.x = safe.x
		z.global_position.z = safe.y
		if z.height_fn.is_valid(): z.global_position.y = float(z.height_fn.call(safe.x, safe.y))
		z.last_safe = z.global_position

## Dry ground outside the haven. The west sea's first dry cells sit inside the waterfront,
## so a short ray from open water stops in that strip and would keep the sea point.
## One coast jump, then a capped inland walk. Not used for records that are already legal.
func nearest_land(x: float, z: float) -> Vector2:
	var origin := Vector2(x, z)
	if _safe_ground(origin): return origin
	if _sea == null: _sea = load("res://scripts/main.gd")
	var cx := float(_sea.coast_x(z)) + 2.0
	var nz := float(_sea.shore_z(x)) - 2.0
	var seeds: Array[Vector2] = [Vector2(cx, z), Vector2(x, nz), Vector2(cx, nz)]
	var dirs: Array[Vector2] = [Vector2(1, 0), Vector2(0, -1)]
	for seed in seeds:
		for dir in dirs:
			var p := seed
			for _i in 48:
				if _safe_ground(p): return p
				p += dir * 8.0
	var fallback := Vector2(-370.0, 280.0)
	if _safe_ground(fallback): return fallback
	return Vector2(0.0, TownHaven.stand_off(BODY_R) + 24.0)

func _safe_ground(p: Vector2) -> bool:
	return not _on_sea(p.x, p.y) and not TownHaven.body_inside(p, BODY_R) and not TownHaven.obstacle_hit(p, BODY_R)

func _illegal(x: float, z: float) -> bool:
	if TownHaven.obstacles.size() > 0 and TownHaven.obstacle_hit(Vector2(x, z), BODY_R): return true
	if _on_sea(x, z): return true
	if x < -380.0 and z > 250.0: return TownHaven.body_inside(Vector2(x, z), BODY_R)
	if maxf(absf(x), absf(z)) < TownHaven.outer_limit() + 1.0: return TownHaven.body_inside(Vector2(x, z), BODY_R)
	return false

func _safe_point(x: float, z: float) -> Vector2:
	var p := Vector2(x, z)
	if TownHaven.body_inside(p, BODY_R) or TownHaven.obstacle_hit(p, BODY_R) or TownHaven.far_parking(p):
		p = TownHaven.nearest_outside(p, BODY_R)
	if _on_sea(p.x, p.y): p = nearest_land(p.x, p.y)
	return p

func _on_sea(x: float, z: float) -> bool:
	if z < 300.0 and x > -400.0: return false
	if _sea == null: _sea = load("res://scripts/main.gd")
	return float(_sea.sea_mask(x, z)) > 0.5

func _constrain(x0: float, z0: float, x1: float, z1: float) -> Vector2:
	var sea := _on_sea(x1, z1)
	var cur := Vector2(x0, z0)
	var nxt := Vector2(x1, z1)
	if not sea and not _near_hazard(x1, z1) and not _near_hazard(x0, z0):
		return nxt
	if sea and not TownHaven.body_inside(nxt, BODY_R):
		return cur
	if TownHaven.body_inside(nxt, BODY_R) or TownHaven.body_inside(cur, BODY_R) or TownHaven.obstacle_hit(nxt, BODY_R) or TownHaven.obstacle_hit(cur, BODY_R) or sea:
		return TownHaven.clamp_move(cur, nxt, BODY_R)
	return nxt

func nearest_in_leash(post: Vector3, leash: float) -> int:
	var best := -1
	var best_d := leash * leash
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		var dx := px[i] - post.x
		var dz := pz[i] - post.z
		var d2 := dx * dx + dz * dz
		if d2 < best_d:
			best_d = d2
			best = i
	return best

func _guard_contact() -> void:
	var guards = director.main.get("guards")
	if guards == null: return
	for g in guards.guards:
		if float(g.down_t) > 0.0: continue
		var n: Node3D = g.node
		var post: Vector3 = g.post
		var gx := n.global_position.x
		var gz := n.global_position.z
		for i in id.size():
			if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
			var dx := px[i] - gx
			var dz := pz[i] - gz
			if dx * dx + dz * dz > 2.56: continue
			var pdx := px[i] - post.x
			var pdz := pz[i] - post.z
			if pdx * pdx + pdz * pdz > TownGuards.POST_LEASH * TownGuards.POST_LEASH: continue
			if bite_cd[i] > 0.0:
				bite_cd[i] = maxf(0.0, bite_cd[i] - 0.016)
				continue
			bite_cd[i] = 1.1
			_hurt(i, int(ceil(ROLE_HP[role[i]] * TownGuards.DMG_FRAC)))
			guard_hits += 1
			g.hp = float(g.hp) - ROLE_ATK[role[i]] * 0.3
			if float(g.hp) <= 0.0:
				g.hp = TownGuards.MAX_HP
				g.down_t = 20.0
				g.tgt = null
				g.ret = true
			break

func _promote(hero: Vector3) -> void:
	if near_n >= NEAR_CAP: return
	var best: Array = []
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		var d := Vector2(px[i] - hero.x, pz[i] - hero.z).length()
		if d > NEAR_IN: continue
		best.append({"i": i, "d": d})
	best.sort_custom(func(a, b): return float(a.d) < float(b.d))
	var room := NEAR_CAP - near_n
	for item in best:
		if room <= 0: break
		if _promote_index(int(item.i), hero):
			room -= 1
			near_n += 1

func _promote_index(i: int, hero: Vector3) -> bool:
	if (flags[i] & 2) != 0: return false
	var slot := -1
	for p in pool.size():
		var z: HordeZombie = pool[p]
		if z.crowd_id < 0:
			slot = p
			break
	if slot < 0: return false
	if _illegal(px[i], pz[i]):
		var safe := _safe_point(px[i], pz[i])
		px[i] = safe.x
		pz[i] = safe.y
	var z: HordeZombie = pool[slot]
	var ground: Callable = director.main.party.director.ground
	var pos := Vector3(px[i], 0.0, pz[i])
	z.bind_crowd(ROLE_NAME[role[i]], pos, hp[i], director.main.hero, ground, Vector2(hold_x[i], hold_z[i]), id[i], wind_t[i], lock_t[i])
	var d: EnemyDirector = director.main.party.director
	if d.enemies.find(z) < 0: d.enemies.append(z)
	flags[i] = flags[i] | 2
	pool_i[i] = slot
	return true

func _draw(hero: Vector3) -> void:
	var far2 := RENDER_RADIUS * RENDER_RADIUS
	var n := 0
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		var dx := px[i] - hero.x
		var dz := pz[i] - hero.z
		var d2 := dx * dx + dz * dz
		if d2 > far2: continue
		if n >= _scratch.size(): _scratch.append(Vector2(float(i), d2))
		else: _scratch[n] = Vector2(float(i), d2)
		n += 1
	if n > render_cap:
		var head := _scratch.slice(0, n)
		head.sort_custom(func(a, b): return float(a.y) < float(b.y))
		for k in render_cap: _scratch[k] = head[k]
		n = render_cap
	rendered_mid = 0
	rendered_far = 0
	rendered_n = n
	var mid2 := MID_RADIUS * MID_RADIUS
	for r in 4:
		var count := 0
		for k in n:
			if role[int(_scratch[k].x)] == r: count += 1
		var mm: MultiMesh = (_meshes[r] as MultiMeshInstance3D).multimesh
		mm.visible_instance_count = count
		var w := 0
		for k in n:
			var i: int = int(_scratch[k].x)
			if role[i] != r: continue
			var feet := _sample_y(i) - 0.7
			mm.set_instance_transform(w, Transform3D(Basis(), Vector3(px[i], feet, pz[i])))
			mm.set_instance_custom_data(w, Color(face[i], 0.0, 0.0, 1.0))
			w += 1
			if _scratch[k].y <= mid2: rendered_mid += 1
			else: rendered_far += 1

func _sample_y(i: int) -> float:
	var cell := ((int(px[i]) >> 2) << 16) ^ (int(pz[i]) >> 2)
	if pycell[i] == cell: return py[i]
	pycell[i] = cell
	var y := 0.7
	if director.main.has_method("height"): y = float(director.main.height(px[i], pz[i])) + 0.7
	py[i] = y
	return y

func _hurt(i: int, dmg: int) -> void:
	hp[i] = maxf(0.0, hp[i] - float(dmg))
	if hp[i] <= 0.0: _kill(i)

func _kill(i: int) -> void:
	if (flags[i] & 1) == 0: return
	var sim := id[i]
	retired[sim] = true
	if (flags[i] & 2) != 0:
		var z: HordeZombie = pool[pool_i[i]]
		if is_instance_valid(z):
			var d: EnemyDirector = director.main.party.director
			d.enemies.erase(z)
			if z.alive(): z.kill_now(Vector3.ZERO)
			z.release_crowd()
	flags[i] = 0
	pool_i[i] = -1
	dead_for[i] = 0.0
	alive_n -= 1
	corpse_n += 1

func _reap(dt: float) -> void:
	for i in id.size():
		if (flags[i] & 1) != 0: continue
		if id[i] == 0: continue
		dead_for[i] += dt
		if dead_for[i] < HordeDirector.CORPSE_SEC: continue
		id[i] = 0
		corpse_n = maxi(0, corpse_n - 1)
		_free.append(i)

func _index_of(sim_id: int) -> int:
	for i in id.size():
		if id[i] == sim_id: return i
	return -1
