class_name Enemy
extends Node3D
## Basic enemy AI ported from combat/ai.js: idle -> chase -> telegraph -> attack -> recover, stagger,
## defeated, and return-home leash for bosses. Boss/elite patterns rotate in order (BOSS_PATTERNS).
## Real skins via CharacterRig at fixed heights (approved: trolls 3x = 5.715 m, Ashen Titan 6x = 11.43 m).

signal died(e: Enemy)
signal attacked(e: Enemy, pattern: Dictionary)

const HERO_M := 1.905
const TYPES := {
	"frosttroll_a": {"model": "res://characters/frosttroll_a_lod1.glb", "height": 3.0 * HERO_M, "data": "frosttroll", "patterns": "frosttroll_a", "r": 1.9},
	"frosttroll_b": {"model": "res://characters/frosttroll_b_lod1.glb", "height": 3.0 * HERO_M, "data": "frosttroll", "patterns": "frosttroll_b", "r": 1.9},
	"titan": {"model": "res://characters/ashentitan_lod1.glb", "height": 6.0 * HERO_M, "data": "titan", "patterns": "titan", "r": 3.2},
	"wolf": {"model": "res://characters/wolf_lod1.glb", "height": 0.0, "data": "wolf", "patterns": "", "r": 0.6},
	"titan_volcano": {"model": "res://characters/ashentitan_volcano_glow_lod1.glb", "height": 0.0, "data": "titan_volcano", "patterns": "", "r": 5.5},
	# voxel-heroes: Lucian's holyknight_villain_voxel (varn-core dcfc9b2 capes_v1), a raider-class bad guy
	"holyknight_villain": {"model": "res://voxel/holyknight_villain_voxel_lod1.glb", "height": HERO_M, "data": "raider", "patterns": "", "r": 0.6},
	"stonetroll": {"model": "res://characters/stonetroll_lod1.glb", "height": 3.0 * HERO_M, "data": "frosttroll", "patterns": "", "r": 1.6},
}

var type_id := ""
var def: Dictionary
var rig: CharacterRig
var hp := 1.0
var max_hp := 1.0
var state := "idle"
var t_state := 0.0
var atk_cd := 1.0
var home := Vector3.ZERO
var pattern: Dictionary = {}
var pat_i := 0
var phase := 1
var radius := 1.0
var height_fn: Callable          # f(x,z)->ground y (main.height)
var target: Node3D               # the hero
var aggro_m := 30.0
var leash_m := 60.0
var speed_mps := 3.0
var poise_dmg := 0.0
var _far := false

func setup(tid: String, pos: Vector3, ground: Callable) -> Enemy:
	type_id = tid
	var T: Dictionary = TYPES[tid]
	def = CombatData.enemy(T.data)
	hp = def.hp; max_hp = hp
	radius = T.r
	height_fn = ground
	position = pos; home = pos
	rig = CharacterRig.new().setup(T.model, T.height)
	add_child(rig)
	if rig.voxel and HeroRoster.ROOT_SPEED.has(tid): rig.set_root_speeds(HeroRoster.ROOT_SPEED[tid][0], HeroRoster.ROOT_SPEED[tid][1], 4.0)
	aggro_m = float(def.aggro) * CombatRules.UNIT_M
	leash_m = aggro_m * 2.0
	speed_mps = float(def.speed) * CombatRules.UNIT_M * 0.6
	name = "%s_%d" % [tid, get_instance_id()]
	return self

func bump_r() -> float: return radius   # body push radius (the volcano Titan's hurtbox can be wider)
func is_boss() -> bool: return def.get("boss", false)
func alive() -> bool: return state != "defeated"
func reach_m() -> float: return float(pattern.get("reach", def.reach)) * CombatRules.UNIT_M + radius

func take_damage(dmg: int, from: Vector3) -> void:
	if not alive(): return
	hp = max(0.0, hp - dmg)
	rig.play_hit()
	if state == "idle" or state == "return": set_state("chase")
	if is_boss() and phase == 1 and hp / max_hp < 0.5: phase = 2
	poise_dmg += dmg
	if poise_dmg >= max_hp * 0.2 and not is_boss() and state != "telegraph":
		poise_dmg = 0.0; set_state("stagger")
	if hp <= 0.0:
		set_state("defeated"); rig.set_dead(true); died.emit(self)

## test 25: Owner ultimate one-shot - bypasses every guard (inactive/intro bosses, phases, poise)
func kill_now(from: Vector3) -> void:
	if not alive(): return
	hp = 0.0; set_state("defeated"); rig.set_dead(true); died.emit(self)

func set_state(s: String) -> void: state = s; t_state = 0.0

## test 14: Lucian's v4 frost trolls (A 0986577, B 349a02f): hit frame (s into attack1/2/3) per BOSS_PATTERNS order
const CLIP_HITS := {"frosttroll_a": [1.1, 1.5, 1.3], "frosttroll_b": [1.1, 1.6, 1.3]}
func _pattern_index() -> int:
	var L: Array = CombatData.patterns(TYPES[type_id].patterns)
	for i in L.size(): if L[i].get("id") == pattern.get("id"): return mini(i, 2)
	return 0

func _pick_pattern() -> Dictionary:
	var L: Array = CombatData.patterns(TYPES[type_id].patterns)
	if L.is_empty(): return {}
	var A := L.filter(func(p): return int(p.get("phase", 1)) <= phase)
	pat_i += 1
	return A[(pat_i - 1) % A.size()]

func _physics_process(dt: float) -> void:
	if target == null: return
	var to := target.global_position - global_position; to.y = 0
	var d := to.length()
	# phone budget: far enemies freeze their AnimationTree and skip AI
	var far := d > 120.0 and state == "idle"
	if far != _far: _far = far; rig.set_active(not far)
	if far: return
	t_state += dt; atk_cd = max(0.0, atk_cd - dt)
	ai_step(dt, to, d)

func ai_step(dt: float, to: Vector3, d: float) -> void:
	var dir: Vector3 = to / maxf(d, 0.001)
	var moving := 0.0
	match state:
		"idle":
			if d < aggro_m: set_state("chase")
		"chase":
			if (global_position - home).length() > leash_m or d > leash_m * 1.5: set_state("return"); return
			if pattern.is_empty(): pattern = _pick_pattern()
			if d > reach_m() * 0.8:
				position += dir * speed_mps * (1.25 if phase == 2 else 1.0) * dt; moving = 1.0
			if d <= reach_m() and atk_cd <= 0.0:
				set_state("telegraph")
				if CLIP_HITS.has(type_id):   # test 14: Lucian's attackN plays from the wind-up; damage lands on its hit frame
					var k := _pattern_index(); var sp := 1.0 / (0.75 if phase == 2 else 1.0)
					rig.play_attack("attack%d" % (k + 1), sp)
			_face(dir, dt)
		"telegraph":
			var tele: float = float(pattern.get("tele", def.tele)) * (0.75 if phase == 2 else 1.0)
			if CLIP_HITS.has(type_id): tele = float(CLIP_HITS[type_id][_pattern_index()]) * (0.75 if phase == 2 else 1.0)
			if t_state >= tele:
				set_state("attack")
				if not CLIP_HITS.has(type_id): rig.play_attack("", 1.0)
				attacked.emit(self, pattern)
		"attack":
			if t_state >= 0.18:
				atk_cd = float(def.atkMs) / 1000.0 * (0.8 if phase == 2 else 1.0); pattern = {}; set_state("recover")
		"recover":
			if t_state >= 0.45: set_state("chase")
		"stagger":
			if t_state >= float(def.stagger): set_state("chase")
		"return":
			var h := home - global_position; h.y = 0
			if h.length() < 1.6: hp = max_hp; phase = 1; pat_i = 0; set_state("idle")
			else: position += h.normalized() * speed_mps * dt; moving = 1.0; _face(h.normalized(), dt)
	if height_fn.is_valid(): position.y = height_fn.call(position.x, position.z)
	if rig.root_walk > 0.0: rig.set_move_mps(moving * speed_mps * (1.25 if phase == 2 and state == "chase" else 1.0))
	else: rig.set_locomotion(moving)

func _face(dir: Vector3, dt: float) -> void:
	var yaw := atan2(-dir.x, -dir.z)
	rotation.y = lerp_angle(rotation.y, yaw, min(1.0, dt * (2.4 if is_boss() else 7.0)))

## Does the current/just-fired pattern hit a point? (ring / cone / line), metres.
func pattern_hits(p: Dictionary, pt: Vector3) -> bool:
	var v := Vector2(pt.x - global_position.x, pt.z - global_position.z)
	var reach := float(p.get("reach", def.reach)) * CombatRules.UNIT_M + radius
	var fwd := Vector2(-sin(rotation.y), -cos(rotation.y))
	match p.get("shape", "cone"):
		"ring": return v.length() <= reach
		"line":
			var along := v.dot(fwd); var side := absf(v.cross(fwd))
			return along >= 0.0 and along <= reach and side <= float(p.get("width", 3.0)) * 0.5 * CombatRules.UNIT_M
		_:
			return v.length() <= reach and (v.length() < 0.01 or fwd.dot(v.normalized()) >= float(p.get("cos", 0.3)))
