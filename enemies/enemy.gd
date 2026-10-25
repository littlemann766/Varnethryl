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
	"titan_volcano": {"model": "res://characters/ashentitan_volcano_lod1.glb", "height": 0.0, "data": "titan_volcano", "patterns": "", "r": 5.5},
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
	aggro_m = float(def.aggro) * CombatRules.UNIT_M
	leash_m = aggro_m * 2.0
	speed_mps = float(def.speed) * CombatRules.UNIT_M * 0.6
	name = "%s_%d" % [tid, get_instance_id()]
	return self

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

func set_state(s: String) -> void: state = s; t_state = 0.0

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
			if d <= reach_m() and atk_cd <= 0.0: set_state("telegraph")
			_face(dir, dt)
		"telegraph":
			var tele: float = float(pattern.get("tele", def.tele)) * (0.75 if phase == 2 else 1.0)
			if t_state >= tele:
				set_state("attack"); rig.play_attack("", 1.0); attacked.emit(self, pattern)
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
	rig.set_locomotion(moving)

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
