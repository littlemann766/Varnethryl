class_name HeroCombat
extends Node
## Player-side combat (port of combat/controller.js essentials). Basic = slot 0, skills 1..3, ultimate 4.
## Rules live in CombatRules (tested headless); this node applies them to the world.

signal used(slot: int, skill: Dictionary)
signal damaged_enemy(e: Enemy, dmg: int, crit: bool)
signal hero_hurt(dmg: int)

var hero_id := "owner"
var kit: Dictionary
var st := CombatRules.new_state()
var hp := 700.0
var max_hp := 700.0
var reduce_t := 0.0
var reduce := 0.0
var rng := RandomNumberGenerator.new()
var body: Node3D            # hero CharacterBody3D
var facing: Node3D          # node whose -Z is the hero's facing (main.hero_vis)
var rig: CharacterRig
var enemies: Callable       # () -> Array[Enemy]
var reach := 1.0            # charscale reach multiplier for giants
var _pending: Array = []    # [time_left, Callable]

func set_hero(id: String) -> void:
	hero_id = id
	kit = CombatData.kit(id)
	max_hp = CombatRules.max_hp(id); hp = max_hp
	st = CombatRules.new_state()

func skill(slot: int) -> Dictionary:
	if slot == 0: return CombatData.data().ABILITIES[0]
	var s: Array = kit.skills
	return s[slot - 1] if slot - 1 < s.size() else {}

func dmg_pct() -> float:
	var w = kit.get("weapon", null)
	return float(w.dmgPct) if w is Dictionary else 0.0

func _fwd() -> Vector2:
	var z := facing.global_transform.basis.z
	return -Vector2(z.x, z.z).normalized()

func _pos2() -> Vector2: return Vector2(body.global_position.x, body.global_position.z)

func _living() -> Array:
	return enemies.call().filter(func(e): return is_instance_valid(e) and e.alive()) if enemies.is_valid() else []

func _nearest(range_m: float) -> Enemy:
	var best: Enemy = null; var bd := range_m
	for e: Enemy in _living():
		var d: float = Vector2(e.global_position.x, e.global_position.z).distance_to(_pos2()) - e.radius
		if d < bd: bd = d; best = e
	return best

func use(slot: int) -> bool:
	var sk := skill(slot)
	if sk.is_empty() or not CombatRules.can_use(hero_id, slot, sk, st): return false
	CombatRules.commit(hero_id, slot, sk, st)
	if rig: rig.play_attack("saber_slash" if hero_id == "owner" and slot > 0 else "", 1.8 if slot == 0 else 1.3)
	# auto-face the nearest enemy (phone friendly)
	var n := _nearest(12.0)
	if n and facing:
		var v := n.global_position - body.global_position
		facing.rotation.y = atan2(-v.x, -v.z)
	var wind := 0.08 if slot == 0 else float(sk.get("windup", 0.18))
	_pending.append([wind, func(): _resolve(slot, sk)])
	used.emit(slot, sk)
	return true

## test 25 (boss: "the owner's ultimate attacks should 1 shot anything"): Owner only, Unholy Destruction + Holy Destruction
const OWNER_ONE_SHOT := ["unholy", "holy"]
static func one_shot(hid: String, sk: Dictionary) -> bool: return hid == "owner" and OWNER_ONE_SHOT.has(str(sk.get("id", "")))

func _hit(e: Enemy, slot: int, sk: Dictionary, mult := 1.0) -> void:
	var r: Dictionary = CombatRules.basic_damage(hero_id, dmg_pct(), rng) if slot == 0 else CombatRules.skill_damage(hero_id, sk, dmg_pct(), rng)
	var dmg := int(r.dmg * mult)
	if slot > 0 and one_shot(hero_id, sk):   # whole HP in one hit (bosses, villain, phases, immunity ignored)
		var full := int(e.max_hp); e.kill_now(body.global_position); damaged_enemy.emit(e, full, true); return
	e.take_damage(dmg, body.global_position)
	damaged_enemy.emit(e, dmg, r.crit)

func _area(sk: Dictionary, slot: int, center: Vector2, fwd: Vector2, mult := 1.0) -> int:
	var n := 0
	for e: Enemy in _living():
		if CombatRules.in_shape(sk, center, fwd, Vector2(e.global_position.x, e.global_position.z), e.radius, reach):
			_hit(e, slot, sk, mult); n += 1
	return n

func _resolve(slot: int, sk: Dictionary) -> void:
	var kind: String = sk.get("kind", "melee")
	var fwd := _fwd()
	match kind:
		"melee", "aoe", "line": _area(sk, slot, _pos2(), fwd)
		"ranged":
			var e := _nearest(float(sk.get("range", 16)) * CombatRules.UNIT_M * reach)
			if e: _hit(e, slot, sk)
		"dash":
			var d := float(sk.get("dist", 8)) * CombatRules.UNIT_M
			body.global_position += Vector3(fwd.x, 0, fwd.y) * d * 0.6
			_area(sk, slot, _pos2(), fwd)
		"blink":
			var e2 := _nearest(float(sk.get("range", 14)) * CombatRules.UNIT_M)
			if e2:
				var back := (e2.global_position - body.global_position); back.y = 0
				body.global_position = e2.global_position + back.normalized() * (e2.radius + 0.8)
				_hit(e2, slot, sk)
		"storm":
			for i in 3: _pending.append([0.25 * i, func(): _area(sk, slot, _pos2(), _fwd(), 1.0 / 3.0)])
		"meteor":
			if sk.get("mode", "") != "" or one_shot(hero_id, sk):     # Owner Holy/Unholy Destruction: kills everything hostile in radius
				var R := float(CombatData.data().TUNING.ult.radius) * CombatRules.UNIT_M
				for e: Enemy in _living():
					if e.global_position.distance_to(body.global_position) <= R:
						if one_shot(hero_id, sk): e.kill_now(body.global_position)
						else: e.take_damage(int(e.hp) + 1, body.global_position)
						damaged_enemy.emit(e, int(e.max_hp), true)
			else:
				var c := _pos2() + fwd * 6.0
				var s2 := sk.duplicate(); s2.range = float(sk.get("radius", 8)); s2.arc = -1
				_pending.append([float(sk.get("delay", 1.2)), func(): _area(s2, slot, c, fwd)])
		"heal": hp = min(max_hp, hp + max_hp * float(sk.get("heal", 0.3)))
		"shield", "buff":
			reduce = float(sk.get("reduce", sk.get("buff", {}).get("reduce", 0.3))); reduce_t = float(sk.get("dur", sk.get("buff", {}).get("dur", 4)))
		"chain":
			_area(sk, slot, _pos2(), fwd)
	if sk.has("heal") and kind != "heal": hp = min(max_hp, hp + max_hp * float(sk.heal))

## enemy -> hero (calc.js fallback formula atk*1000/(1000+def), min 12)
## test 26 (boss: the Titan "needs to do a little bit of damage ... so it doesn't one shot people"): every Ashen Titan
## attack (world boss slams/waves, the volcano Titan and the 6x Titan's stomps/swats/sweeps) does at most TITAN_HIT of a
## normal hero's max HP (700), and all Titan hits inside TITAN_WIN seconds together at most TITAN_WIN_CAP, so no combo
## or overlap can take a full-HP hero down in one go. Owner cheat HP is irrelevant (fixed reference HP).
const TITAN_HIT := 0.12
const TITAN_WIN := 5.0
const TITAN_WIN_CAP := 0.35
var _titan_log: Array = []   # [time_s, dmg]
static func titan_ref_hp() -> float: return float(CombatData.data().PLAYER.hp)
func titan_hit(frac := TITAN_HIT) -> int:
	if hp <= 0.0: return 0
	var now := Time.get_ticks_msec() / 1000.0
	_titan_log = _titan_log.filter(func(e): return now - float(e[0]) < TITAN_WIN)
	var used_ := 0.0
	for e in _titan_log: used_ += float(e[1])
	var h := minf(clampf(frac, 0.0, TITAN_HIT), maxf(0.0, TITAN_WIN_CAP - used_ / titan_ref_hp())) * titan_ref_hp()
	if reduce_t > 0.0: h *= (1.0 - reduce)
	h = roundf(h)
	if h <= 0.0: return 0
	_titan_log.append([now, h])
	hp = max(0.0, hp - h)
	if rig: rig.play_hit()
	hero_hurt.emit(int(h))
	if hp <= 0.0:
		if rig: rig.set_dead(true)
		_pending.append([float(CombatData.data().PLAYER.respawn), _respawn])
	return int(h)

func take_hit(atk: float, mult := 1.0) -> int:
	if hp <= 0.0: return 0
	var P: Dictionary = CombatData.data().PLAYER
	var h := maxf(12.0, round(atk * mult * 1000.0 / (1000.0 + float(P.def))))
	if reduce_t > 0.0: h *= (1.0 - reduce)
	hp = max(0.0, hp - h)
	if rig: rig.play_hit()
	hero_hurt.emit(int(h))
	if hp <= 0.0:
		if rig: rig.set_dead(true)
		_pending.append([float(P.respawn), _respawn])
	return int(h)

func _respawn() -> void:
	hp = max_hp
	if rig: rig.set_dead(false)

func _process(dt: float) -> void:
	CombatRules.tick(st, dt)
	reduce_t = max(0.0, reduce_t - dt)
	for i in range(_pending.size() - 1, -1, -1):
		_pending[i][0] -= dt
		if _pending[i][0] <= 0.0:
			var cb: Callable = _pending[i][1]; _pending.remove_at(i); cb.call()
