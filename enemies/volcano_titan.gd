class_name VolcanoTitan
extends Enemy
## Volcano Ashen Titan (test 13, Beth's "Titan in the lava"): stands IN the central 20 m lava pool of the caldera,
## never walks (root motion stripped from walk/run), turns to face the player and attacks from the pool.
## Size: ONE constant, TITAN_SCALE (boss chose 28 m = Beth's x1.3362 on the 20.955 m rig). Reach scales with it.
## Stage 1 rock throws + melee, stage 2 + lava slam, stage 3 + falling-rock rain and +25% speed (TitanQuest sets stage).

signal aoe(center: Vector3, radius: float, dmg_mult: float)
signal telegraph(at: Vector3, radius: float, sec: float)

const BASE_H := 20.955
const TITAN_SCALE := 1.3362                  # 28.0 m (boss, test 13). Change here only.
const REACH_M := 17.0 * TITAN_SCALE / 1.3362   # Beth: ~17 m horizontal at x1.3362
const PLATE_Y := 39.05                       # plate tops, volcano-local
const LAVA_Y := 38.0
static var CENTER := Vector3(405, 0, -402)   # main: volcano base + titan_pool centre (xz); y = volcano base
static var BODY_LEASH := 0.0
static var CHASE_BREAK := 75.0               # player further than this from CENTER -> idle (rim r 33 + slack)
var J: Dictionary
var cds := {"eruption_slam": 0.0, "boulder_hurl": 0.0, "magma_sweep": 0.0, "volcano_roar": 0.0, "attack": 0.0, "rain": 4.0}
var seq: Array = []
var clip_t := 0.0
var cur_clip := ""
var fired := {}
var projectiles: Array = []
var _proj_scenes := {}
var stage := 1
var active := false                          # TitanQuest enables him after the intro
var skel: Skeleton3D
var hands := [-1, -1]
var body_r := 7.0
var glow_mats: Array[BaseMaterial3D] = []

static func height_m() -> float: return BASE_H * TITAN_SCALE

func setup_volcano(ground: Callable) -> VolcanoTitan:
	setup("titan_volcano", CENTER, ground)
	J = JSON.parse_string(FileAccess.get_file_as_string("res://characters/sidecars/ashentitan_volcano__ashentitan_volcano_11x.json"))
	aggro_m = CHASE_BREAK; speed_mps = 0.0
	rig.scale = Vector3.ONE * TITAN_SCALE
	radius = body_r
	for k in ["volcanic_boulder", "lava_blob", "ember_rock_small"]:
		_proj_scenes[k] = load("res://enemies/models/%s.glb" % k)
	_no_root_motion()
	skel = _find_skel(rig)
	if skel: hands = [skel.find_bone("hand_L"), skel.find_bone("hand_R")]
	for mi in rig.find_children("*", "MeshInstance3D", true, false):
		var m3 := mi as MeshInstance3D
		for si in m3.mesh.get_surface_count():
			var m := m3.get_active_material(si) as BaseMaterial3D
			if m: m = m.duplicate(); m.emission_enabled = true; m3.set_surface_override_material(si, m); glow_mats.append(m)
	set_glow(1.0)
	return self

func set_glow(e: float) -> void:
	for m in glow_mats: m.emission_energy_multiplier = e

# ---------- test 14: Beth's lava veins (effects only; the GLB is untouched) ----------
const LAVA_DIR := "res://assets/volcano/titan_lava/"
const VEIN_SCALE := [0.85, 1.0, 1.2]
const DRIPS_STAGE1 := 8
var lava_mat: Material            # per-instance duplicate of titan_lava_material (High/Ultra) or titan_lava_fallback (Low/Medium)
var lava_hq := false
var drips: Array[GPUParticles3D] = []
var chest_light: OmniLight3D
var glow_strength := 1.0:
	set(v):
		glow_strength = v
		if lava_mat is ShaderMaterial: (lava_mat as ShaderMaterial).set_shader_parameter("glow_strength", v)
		elif lava_mat is StandardMaterial3D: (lava_mat as StandardMaterial3D).emission_energy_multiplier = 2.0 * v
		if chest_light: chest_light.light_energy = 1.2 + 0.9 * v

func lava_veins(hq: bool) -> void:
	lava_hq = hq
	lava_mat = (load(LAVA_DIR + ("titan_lava_material_volcano_glow_lod1.tres" if hq else "titan_lava_fallback_volcano_glow_lod1.tres")) as Material).duplicate()   # Beth remapped set (75c0682 fist UVs)
	for mi: MeshInstance3D in rig.find_children("*", "MeshInstance3D", true, false):
		if String(mi.name).to_lower().contains("ashentitan") or mi.skin != null: mi.material_override = lava_mat
	if skel == null: return
	if drips.is_empty():
		var j = JSON.parse_string(FileAccess.get_file_as_string(LAVA_DIR + "titan_drip_points.json"))
		var scene: PackedScene = load(LAVA_DIR + "titan_drip_particles.tscn")
		for p in j.points:
			var bi := skel.find_bone(p.bone)
			if bi < 0: continue
			var ba := BoneAttachment3D.new(); ba.name = "Drip_" + p.name; ba.bone_name = p.bone; skel.add_child(ba)
			var at := Node3D.new(); at.position = Vector3(p.offset[0], p.offset[1], p.offset[2]); ba.add_child(at)
			var d: GPUParticles3D = scene.instantiate(); at.add_child(d); d.emitting = drips.size() < DRIPS_STAGE1; drips.append(d)
		var cb := skel.find_bone("chest")
		if cb >= 0:
			var ca := BoneAttachment3D.new(); ca.name = "ChestGlow"; ca.bone_name = "chest"; skel.add_child(ca)
			chest_light = OmniLight3D.new(); chest_light.light_color = Color(1.0, 0.5, 0.15); chest_light.omni_range = 16.0
			chest_light.shadow_enabled = false; chest_light.position = Vector3(0, 0, 1.2); ca.add_child(chest_light)
	glow_strength = glow_strength

## stage 1/2/3: glow 1.0 / 2.2 / 4.0 tweened over 1.2 s, veins grow, 8 drips then all 16
func lava_stage(n: int, tween := true) -> void:
	var g: float = [1.0, 2.2, 4.0][n - 1]
	if tween and is_inside_tree(): create_tween().tween_property(self, "glow_strength", g, 1.2).set_trans(Tween.TRANS_SINE)
	else: glow_strength = g
	if lava_mat is ShaderMaterial: (lava_mat as ShaderMaterial).set_shader_parameter("vein_scale", VEIN_SCALE[n - 1])
	for i in drips.size(): drips[i].emitting = n >= 2 or i < DRIPS_STAGE1

## walk/run were authored with travel on root/hips: drop their XZ so he stays in the pool
func _no_root_motion() -> void:
	if rig.anim_player == null: return
	for c in ["walk", "run"]:
		if not rig.anim_player.has_animation(c): continue
		var a := rig.anim_player.get_animation(c)
		for t in a.get_track_count():
			var p := str(a.track_get_path(t))
			if a.track_get_type(t) == Animation.TYPE_POSITION_3D and (p.ends_with(":root") or p.ends_with(":hips")):
				var y0: Vector3 = a.track_get_key_value(t, 0)
				for k in a.track_get_key_count(t):
					var v: Vector3 = a.track_get_key_value(t, k); a.track_set_key_value(t, k, Vector3(y0.x, v.y, y0.z))

func _find_skel(n: Node) -> Skeleton3D:
	if n is Skeleton3D: return n
	for c in n.get_children():
		var s := _find_skel(c)
		if s: return s
	return null

func hand_pos(i: int) -> Vector3:
	if skel == null or hands[i] < 0: return global_position + Vector3(0, 20, 0)
	return skel.global_transform * skel.get_bone_global_pose(hands[i]).origin

func reach_m() -> float: return REACH_M
func bump_r() -> float: return body_r

## player hurtbox: body (torso/head above the lava, radius body_r) + the arms while an attack lifts them
func _hurt_radius() -> float:
	var r := body_r
	if state == "attack":
		for i in 2:
			var h := hand_pos(i)
			if h.y > CENTER.y + LAVA_Y: r = maxf(r, Vector2(h.x - global_position.x, h.z - global_position.z).length() + 2.0)
	return r

func take_damage(dmg: int, from: Vector3) -> void:
	if not active: return
	super.take_damage(dmg, from)

## test 14: Lucian v8 (75c0682) clip hit frames; Beth's events keep their spacing, re-anchored on his impact frame
const LUCIAN_HIT := {"eruption_slam": 1.288, "magma_sweep": 0.976, "boulder_hurl": 2.383}
const MELEE_HIT := {"attack1": 1.2, "attack2": 1.1, "attack3": 1.3}
var _ev_cache := {}
func _events(clip: String) -> Array:
	if _ev_cache.has(clip): return _ev_cache[clip]
	var ev: Array = J.attackEvents.filter(func(e): return e.clip == clip)
	if LUCIAN_HIT.has(clip) and rig.clips.has(clip) and not ev.is_empty():
		var t0 := float(ev[0].t); var out := []
		for e in ev: var e2: Dictionary = e.duplicate(); e2.t = LUCIAN_HIT[clip] + float(e.t) - t0; out.append(e2)
		ev = out
	_ev_cache[clip] = ev
	return ev

func ai_step(dt: float, to: Vector3, d: float) -> void:
	radius = _hurt_radius()
	_step_projectiles(dt)
	if not active or state == "defeated": return
	for k in cds: cds[k] = max(0.0, cds[k] - dt * (1.25 if stage == 3 else 1.0))
	var tp := target.global_position
	var pfc := Vector2(tp.x - CENTER.x, tp.z - CENTER.z).length()
	if not seq.is_empty(): _run_seq(dt); return
	if pfc > CHASE_BREAK: set_state("idle"); rig.set_locomotion(0.0); return
	if state == "idle": set_state("chase")
	_face(to / maxf(d, 0.001), dt)
	if stage == 3 and cds.rain <= 0.0: cds.rain = 4.0; _rain(6)
	var c := ""
	if stage >= 2 and d < REACH_M + 2.0 and cds.eruption_slam <= 0.0: c = "eruption_slam"
	elif d < REACH_M and cds.attack <= 0.0: c = "attack"
	elif d < REACH_M + 8.0 and cds.magma_sweep <= 0.0: c = "magma_sweep"
	elif stage == 3 and cds.volcano_roar <= 0.0: c = "volcano_roar"
	elif d > 8.0 and cds.boulder_hurl <= 0.0: c = "boulder_hurl"
	if c != "": _start(c)
	rig.set_locomotion(0.0)

func _start(clip: String) -> void:
	var cd: Dictionary = J.attackSequenceSuggestion.cooldownsSec
	cds[clip] = float(cd.get(clip, 4)) * (0.75 if stage == 3 else 1.0)
	# v8 clips carry their own anticipation: no separate windup for the slam / hurl
	var wind := {"volcano_roar": 1.5}
	seq = []
	if wind.has(clip): seq.append(["windup", wind[clip] / (1.25 if stage == 3 else 1.0)])
	if clip == "attack":
		var ms := MELEE_HIT.keys().filter(func(k): return rig.clips.has(k))
		if not ms.is_empty(): clip = ms[randi() % ms.size()]
	var dur := rig.clip_length(clip) if rig.clip_length(clip) > 0.0 else (float(J.clips[clip].durationSec) if J.clips.has(clip) else 2.0)
	seq.append([clip, maxf(dur, 1.0) / (1.25 if stage == 3 else 1.0)])
	cur_clip = ""; set_state("attack")

func _run_seq(dt: float) -> void:
	var spd := 1.25 if stage == 3 else 1.0
	if cur_clip != seq[0][0]:
		cur_clip = seq[0][0]; clip_t = 0.0; fired = {}
		rig.play_attack(cur_clip, spd)
		if cur_clip != "windup": attacked.emit(self, {"id": cur_clip, "name": cur_clip.capitalize()})
		if cur_clip == "attack" or MELEE_HIT.has(cur_clip): _telegraph_hand(float(MELEE_HIT.get(cur_clip, 0.9)) / spd)
	clip_t += dt * spd
	if (cur_clip == "attack" or MELEE_HIT.has(cur_clip)) and not fired.has("melee") and clip_t >= float(MELEE_HIT.get(cur_clip, 0.9)):
		fired["melee"] = true; _hand_hit(5.0, 1.6)
	for i in _events(cur_clip).size():
		var e: Dictionary = _events(cur_clip)[i]
		if not fired.has(i) and clip_t >= float(e.t): fired[i] = true; _fire(e)
	if clip_t >= seq[0][1] * spd:
		seq.pop_front(); cur_clip = ""
		if seq.is_empty(): set_state("chase")

func _plate(p: Vector3) -> Vector3: return Vector3(p.x, CENTER.y + PLATE_Y, p.z)

## slam lands at plate height under the hand nearest the player (clips were authored on flat ground)
func _near_hand() -> Vector3:
	var tp := target.global_position; var a := hand_pos(0); var b := hand_pos(1)
	var da := Vector2(a.x - tp.x, a.z - tp.z).length(); var db := Vector2(b.x - tp.x, b.z - tp.z).length()
	return a if da < db else b

func _hand_hit(r: float, mult: float) -> void:
	for i in 2: aoe.emit(_plate(hand_pos(i)), r, mult * 0.5)

func _telegraph_hand(sec: float) -> void:
	var tp := target.global_position; var g := global_position
	var dir := Vector2(tp.x - g.x, tp.z - g.z); var L := minf(dir.length(), REACH_M)
	var at := Vector3(g.x, 0, g.z) + Vector3(dir.x, 0, dir.y).normalized() * L
	telegraph.emit(_plate(at), 5.0, sec)

func _local(off: Array) -> Vector3:
	return global_transform * (Vector3(-float(off[0]), float(off[1]), -float(off[2])) * TITAN_SCALE)

func _fire(e: Dictionary) -> void:
	if e.type == "aoe":
		var c := global_position if e.name == "roar_blast" else _near_hand()
		aoe.emit(_plate(c), float(e.radius) * TITAN_SCALE / 1.3362, float(e.damageMult))
	elif e.type == "spawn_projectile":
		if e.get("pattern", "") == "rain_zone": return    # stage 3 rain is driven by _rain()
		var origin := _local(e.spawn.offset)
		var n: int = mini(int(e.get("count", 1)), 6)
		for i in n:
			var land: Vector3
			if e.get("target", "") == "player":
				land = target.global_position + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)) * float(e.get("spread", 0))
			else:
				var lr: Array = e.get("landRadius", [10, 20])
				var a := TAU * i / n + randf() * 0.3 if e.get("pattern", "") == "ring" else rotation.y + PI + deg_to_rad(float(e.get("aimYawDeg", 0)) + randf_range(-20, 20))
				var r := clampf(randf_range(lr[0], lr[1]), 11.0, 31.0)
				land = global_position + Vector3(-sin(a), 0, -cos(a)) * r
			land = _plate(land)
			_spawn(e.projectile, float(e.get("projectileScale", 1)), origin, land, float(e.damageMult), float(e.get("impactRadius", 2)))

## stage 3: falling-rock rain, telegraphed circles on the arena (35% biased to the player)
func _rain(n: int) -> void:
	for i in n:
		var p: Vector3
		if randf() < 0.35: p = target.global_position + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3))
		else:
			var a := randf() * TAU; var r := randf_range(11.0, 31.0); p = CENTER + Vector3(cos(a) * r, 0, sin(a) * r)
		p = _plate(p)
		_spawn("volcanic_boulder", 1.2, p + Vector3(0, 45, 0), p, 1.0, 3.0, 1.6)

func _spawn(kind: String, sc: float, from: Vector3, to: Vector3, mult: float, impact_r: float, T := -1.0) -> void:
	if projectiles.size() > 30: return
	var node: Node3D = _proj_scenes[kind].instantiate()
	node.scale = Vector3.ONE * sc
	# Beth's projectile GLBs carry plain white materials (boss: "white low-poly blob"): dark rock / molten blob
	for mi in node.find_children("*", "MeshInstance3D", true, false): (mi as MeshInstance3D).material_override = _proj_mat(kind)
	get_parent().add_child(node); node.global_position = from
	if T <= 0.0: T = clamp(Vector2(to.x - from.x, to.z - from.z).length() / 18.0, 1.0, 2.6)
	var g := 9.81
	var v := Vector3((to.x - from.x) / T, (to.y - from.y + 0.5 * g * T * T) / T, (to.z - from.z) / T)
	projectiles.append({"node": node, "vel": v, "mult": mult, "r": impact_r, "life": T})
	telegraph.emit(to, impact_r, T)

static var _pm := {}
static func _proj_mat(kind: String) -> StandardMaterial3D:
	if not _pm.has(kind):
		var m := StandardMaterial3D.new()
		if kind == "lava_blob":
			m.albedo_color = Color(0.9, 0.3, 0.05); m.emission_enabled = true; m.emission = Color(1.0, 0.42, 0.08); m.emission_energy_multiplier = 3.0
		else:
			m.albedo_color = Color(0.13, 0.1, 0.09); m.roughness = 0.95; m.emission_enabled = true; m.emission = Color(0.9, 0.25, 0.05); m.emission_energy_multiplier = 0.35
		_pm[kind] = m
	return _pm[kind]

func _step_projectiles(dt: float) -> void:
	for i in range(projectiles.size() - 1, -1, -1):
		var p: Dictionary = projectiles[i]
		p.vel.y -= 9.81 * dt
		p.node.global_position += p.vel * dt
		p.life -= dt
		if p.life <= 0.0:
			aoe.emit(p.node.global_position, p.r, p.mult)
			p.node.queue_free(); projectiles.remove_at(i)
