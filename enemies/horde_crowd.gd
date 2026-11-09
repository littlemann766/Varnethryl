class_name HordeCrowd
extends Node
## Data-oriented horde. Thousands are simulated records with stable ids.
## Only a small pool becomes HordeZombie bodies for nearby combat.
## Everyone else is a batched placeholder. Dead ids are never reused.

const SIM_DEFAULT := 192
const NEAR_CAP := 16
## Visible budget matches the sim ceiling. Software GL drew 4096 placeholder
## capsules at about 6 ms/frame on this desktop. The boot crowd is still 192.
## The expensive part of a 4000 crowd is the simulation step, not the draw upload.
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

const ROLE_NAME := ["shambler", "runner", "undead_knight", "undead_sailor"]
const ROLE_SPEED := [1.25, 3.35, 1.15, 1.20]
const ROLE_HP := [190.0, 140.0, 260.0, 240.0]
const ROLE_AGGRO := [18.0, 34.0, 18.0, 18.0]

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
var hp: PackedFloat32Array = PackedFloat32Array()
var hold_x: PackedFloat32Array = PackedFloat32Array()
var hold_z: PackedFloat32Array = PackedFloat32Array()
var role: PackedInt32Array = PackedInt32Array()
var gate: PackedInt32Array = PackedInt32Array()
var slot_i: PackedInt32Array = PackedInt32Array()
var flags: PackedInt32Array = PackedInt32Array() # 1 alive, 2 promoted
var pool_i: PackedInt32Array = PackedInt32Array()
var dead_for: PackedFloat32Array = PackedFloat32Array()

var pool: Array = []
var _meshes: Array = []
var _free: Array = []

func setup(host: HordeDirector, count: int) -> void:
	director = host
	target_n = clampi(count, 1, SIM_MAX)
	var raw := OS.get_environment("VARN_HORDE_RENDER")
	if raw.is_valid_int(): render_cap = clampi(int(raw), 1, SIM_MAX)
	_build_pool()
	_build_meshes()
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
	_sync_promoted()
	_demote_far(hero)
	_reap(dt)
	_integrate(dt, hero, hero_safe)
	_promote(hero)
	_draw(hero)
	if alive_n < target_n and OS.get_environment("VARN_NO_HORDE_REFILL") == "":
		director.refill_t -= dt
		if director.refill_t <= 0.0:
			director.refill_t = HordeDirector.REFILL_SEC
			_spawn_new(_pick_gate(), -1)

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
		var cap := CapsuleMesh.new()
		cap.radius = 0.28
		cap.height = 1.35
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		match r:
			1: mat.albedo_color = Color(0.74, 0.62, 0.16)
			2: mat.albedo_color = Color(0.42, 0.48, 0.56)
			3: mat.albedo_color = Color(0.18, 0.46, 0.5)
			_: mat.albedo_color = Color(0.4, 0.55, 0.32)
		cap.material = mat
		mm.mesh = cap
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
		hp.push_back(0.0)
		hold_x.push_back(0.0)
		hold_z.push_back(0.0)
		role.push_back(0)
		gate.push_back(0)
		slot_i.push_back(0)
		flags.push_back(0)
		pool_i.push_back(-1)
		dead_for.push_back(0.0)
	if slot < 0: slot = _next_slot(g)
	var sim := next_id
	next_id += 1
	var rr := _role_for(g, slot)
	var hold := formation_xz(g, slot)
	var dir := gate_dir(g)
	var back := 0.0
	if slot >= _gate_share(g) / 2: back = 22.0
	var spawn := hold + dir * back
	if TownHaven.body_inside(spawn, BODY_R) or TownHaven.in_escape_wedge(spawn):
		spawn = hold
	id[use] = sim
	role[use] = rr
	gate[use] = g
	slot_i[use] = slot
	hold_x[use] = hold.x
	hold_z[use] = hold.y
	px[use] = spawn.x
	pz[use] = spawn.y
	hp[use] = ROLE_HP[rr]
	flags[use] = 1
	pool_i[use] = -1
	dead_for[use] = 0.0
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
			_kill(i)
			continue
		px[i] = z.global_position.x
		pz[i] = z.global_position.z
		hp[i] = z.hp
		near_n += 1

func _demote_far(hero: Vector3) -> void:
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) == 0: continue
		if Vector2(px[i] - hero.x, pz[i] - hero.z).length() <= NEAR_OUT: continue
		var z: HordeZombie = pool[pool_i[i]]
		if is_instance_valid(z) and z.alive():
			px[i] = z.global_position.x
			pz[i] = z.global_position.z
			hp[i] = z.hp
			var d: EnemyDirector = director.main.party.director
			d.enemies.erase(z)
			z.release_crowd()
		flags[i] = flags[i] & ~2
		pool_i[i] = -1
		near_n = maxi(0, near_n - 1)

func _integrate(dt: float, hero: Vector3, hero_safe: bool) -> void:
	var noise := director.noise_r > 0.0
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		var tx := hold_x[i]
		var tz := hold_z[i]
		var dx := hero.x - px[i]
		var dz := hero.z - pz[i]
		var dist := sqrt(dx * dx + dz * dz)
		var rr: int = role[i]
		if not hero_safe and dist <= ROLE_AGGRO[rr]:
			tx = hero.x
			tz = hero.z
		elif noise and Vector2(px[i], pz[i]).distance_to(director.noise_at) <= director.noise_r:
			tx = director.noise_at.x
			tz = director.noise_at.y
		var mx := tx - px[i]
		var mz := tz - pz[i]
		var md := sqrt(mx * mx + mz * mz)
		if md < 0.12: continue
		var step := minf(ROLE_SPEED[rr] * dt, md)
		var nx := px[i] + mx / md * step
		var nz := pz[i] + mz / md * step
		var nxt := _constrain(Vector2(px[i], pz[i]), Vector2(nx, nz))
		px[i] = nxt.x
		pz[i] = nxt.y

func _on_sea(p: Vector2) -> bool:
	return float(load("res://scripts/main.gd").sea_mask(p.x, p.y)) > 0.5

func _constrain(cur: Vector2, nxt: Vector2) -> Vector2:
	var sea := _on_sea(nxt)
	var blocked := sea or TownHaven.body_inside(nxt, BODY_R) or TownHaven.body_inside(cur, BODY_R) or TownHaven.obstacle_hit(nxt, BODY_R) or TownHaven.obstacle_hit(cur, BODY_R)
	if not blocked: return nxt
	if sea and not TownHaven.body_inside(nxt, BODY_R):
		return cur
	return TownHaven.clamp_move(cur, nxt, BODY_R)

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
	var z: HordeZombie = pool[slot]
	var ground: Callable = director.main.party.director.ground
	var pos := Vector3(px[i], 0.0, pz[i])
	z.bind_crowd(ROLE_NAME[role[i]], pos, hp[i], director.main.hero, ground, Vector2(hold_x[i], hold_z[i]), id[i])
	var d: EnemyDirector = director.main.party.director
	if d.enemies.find(z) < 0: d.enemies.append(z)
	flags[i] = flags[i] | 2
	pool_i[i] = slot
	return true

func _draw(hero: Vector3) -> void:
	var picked: Array = []
	var far2 := RENDER_RADIUS * RENDER_RADIUS
	for i in id.size():
		if (flags[i] & 1) == 0 or (flags[i] & 2) != 0: continue
		var dx := px[i] - hero.x
		var dz := pz[i] - hero.z
		var d2 := dx * dx + dz * dz
		if d2 > far2: continue
		picked.append({"i": i, "d2": d2})
	picked.sort_custom(func(a, b): return float(a.d2) < float(b.d2))
	if picked.size() > render_cap: picked = picked.slice(0, render_cap)
	var buckets: Array = [[], [], [], []]
	rendered_mid = 0
	rendered_far = 0
	var mid2 := MID_RADIUS * MID_RADIUS
	for item in picked:
		var i: int = int(item.i)
		buckets[role[i]].append(item)
		if float(item.d2) <= mid2: rendered_mid += 1
		else: rendered_far += 1
	rendered_n = picked.size()
	var ground_ok := director.main.has_method("height")
	for r in 4:
		var mm: MultiMesh = (_meshes[r] as MultiMeshInstance3D).multimesh
		var list: Array = buckets[r]
		mm.visible_instance_count = list.size()
		for k in list.size():
			var item: Dictionary = list[k]
			var i: int = int(item.i)
			var y := 0.7
			if ground_ok: y = float(director.main.height(px[i], pz[i])) + 0.7
			var scale := 1.0 if float(item.d2) <= mid2 else 0.62
			mm.set_instance_transform(k, Transform3D(Basis().scaled(Vector3(scale, scale, scale)), Vector3(px[i], y, pz[i])))

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
