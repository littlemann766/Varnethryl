class_name CombatRules
## Pure combat rules (no nodes) so they can be unit-tested headless.
## Port of calc.js DamageCalculator + the controller's gating, with the boss's rules:
##  - basic attack: always allowed after PORT.basic_interval, no cost, no timing/combo window
##  - cooldowns only on skills (slots 1..4); the Owner has none (JS perk: owner skin = no cd, unlimited MP/SP)
##  - only the Owner is overpowered (99,999 per hit, 999,999 HP)

static func is_owner(hero_id: String) -> bool: return hero_id == "owner"

static func max_hp(hero_id: String) -> int:
	var T: Dictionary = CombatData.data().TUNING
	return int(T.owner.hp) if is_owner(hero_id) else int(T.normal.hp)

static func basic_damage(hero_id: String, dmg_pct: float, rng: RandomNumberGenerator) -> Dictionary:
	var d := CombatData.data()
	if is_owner(hero_id): return {"dmg": int(d.SABER.max), "crit": false}
	var base: float = d.UNARMED.min + (d.UNARMED.max - d.UNARMED.min) * rng.randf()
	var crit: bool = rng.randf() < d.PLAYER.crit
	return {"dmg": int(round(base * (1.0 + dmg_pct) * (d.PLAYER.critMult if crit else 1.0))), "crit": crit}

static func skill_damage(hero_id: String, skill: Dictionary, dmg_pct: float, rng: RandomNumberGenerator) -> Dictionary:
	var d := CombatData.data()
	if is_owner(hero_id):
		var mul: float = d.TUNING.skillMul.get(skill.get("id", ""), 1.0)
		return {"dmg": int(d.SABER.max * mul), "crit": false}
	var r := basic_damage(hero_id, dmg_pct, rng)
	r.dmg = int(round(r.dmg * float(skill.get("mult", 1.0))))
	return r

## Can the hero use slot `slot` now? slot 0 = basic. st = {cd:Array[5], mp, sp, fury, basic_t}
static func can_use(hero_id: String, slot: int, skill: Dictionary, st: Dictionary) -> bool:
	if slot == 0: return st.basic_t <= 0.0
	if is_owner(hero_id): return true
	if st.cd[slot] > 0.0: return false
	var cost: Dictionary = skill.get("cost", {})
	if cost.get("mp", 0) > st.mp or cost.get("sp", 0) > st.sp: return false
	if skill.has("fury") and st.fury < float(skill.fury): return false
	return true

## Apply the use: sets cooldowns/costs. Returns the cooldown applied.
static func commit(hero_id: String, slot: int, skill: Dictionary, st: Dictionary) -> float:
	var T: Dictionary = CombatData.data().TUNING
	if slot == 0:
		st.basic_t = CombatData.PORT.basic_interval
		st.fury = min(100.0, st.fury + T.ult.furyPerBasic)
		return 0.0
	if is_owner(hero_id): return 0.0
	var cost: Dictionary = skill.get("cost", {})
	st.mp -= cost.get("mp", 0); st.sp -= cost.get("sp", 0)
	if skill.has("fury"): st.fury = 0.0
	else: st.fury = min(100.0, st.fury + T.ult.furyPerSkill)
	st.cd[slot] = float(skill.get("cd", 0))
	return st.cd[slot]

static func new_state() -> Dictionary:
	return {"cd": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "mp": 100.0, "sp": 100.0, "fury": 0.0, "basic_t": 0.0}

static func tick(st: Dictionary, dt: float) -> void:
	var P: Dictionary = CombatData.data().PLAYER
	for i in st.cd.size(): st.cd[i] = max(0.0, st.cd[i] - dt)
	st.basic_t = max(0.0, st.basic_t - dt)
	st.mp = min(100.0, st.mp + P.mpRegen * dt); st.sp = min(100.0, st.sp + P.spRegen * dt)

## Shape test (melee cone / aoe ring / ranged / line) in metres, XZ plane. fwd is unit Vector2.
const UNIT_M := 1.5 / 1.4205   # JS ranges are x HS(1.5) world units; world units per metre = 0.947 x HS
static func in_shape(skill: Dictionary, from: Vector2, fwd: Vector2, target: Vector2, target_r: float, reach := 1.0) -> bool:
	var rng_m: float = float(skill.get("range", 4.6)) * UNIT_M * reach
	var v := target - from; var d := v.length() - target_r
	if d > rng_m: return false
	var arc: float = float(skill.get("arc", 0.2))
	if arc < 0.0 or v.length() < 0.01: return true
	return fwd.dot(v.normalized()) >= arc
