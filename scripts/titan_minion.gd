class_name TitanMinion
extends Node3D
## test 34 (Lucian ashentitan_minions, heroes-motion-pass ddd4bca): the world boss's adds now move and fight.
## Ash fiend / ember wisp: chase the nearest hero (feet on _gy, wisp hovers 2 m), face it, walk/run at the clip speed,
## attack in range and land damage ONCE at the clip's hit frame (minion_events.json). Damage is modest and goes through
## HeroCombat.titan_hit (<= TITAN_HIT per hit, TITAN_WIN_CAP per 5 s) so they never one-shot anyone. HP, hit + death clips,
## freed ~4 s after death (no fixed 90 s lifetime). Enemy-like API (alive/take_damage/radius/max_hp/def) so the city guards
## treat them as monsters.
const EV_PATH := "res://assets/volcano/worldboss/minion_events.json"
const STATS := {"fiend": {"hp": 60.0, "speed": 4.2, "frac": 0.03, "cd": 2.4, "radius": 0.6, "atk": 30},
	"wisp": {"hp": 35.0, "speed": 3.6, "frac": 0.02, "cd": 2.8, "radius": 0.45, "atk": 20}}
static var _ev: Dictionary = {}
var kind := "fiend"
var type_id := "titan_minion"
var boss: Node
var ap: AnimationPlayer
var hp := 1.0
var max_hp := 1.0
var radius := 0.6
var def := {}
var state := "chase"   # chase / attack / hit / dead
var clip := ""
var atk_t := 0.0       # seconds into the current attack
var atk_hit := 0.0     # hit_time of the current attack
var atk_reach := 1.5
var atk_aoe := false
var atk_done := false
var cd := 0.0
var st_t := 0.0
var dead_t := 0.0
var hits_landed := 0
func alive() -> bool: return state != "dead"
func is_boss() -> bool: return false
static func events() -> Dictionary:
	if _ev.is_empty(): _ev = JSON.parse_string(FileAccess.get_file_as_string(EV_PATH))
	return _ev
func clips() -> Dictionary: return events()["wb_ember_wisp" if kind == "wisp" else "wb_ash_fiend"].clips
func setup(b: Node, k: String, scene: PackedScene, mat: Material) -> TitanMinion:
	boss = b; kind = k; name = "Minion_" + k
	var v: Node3D = scene.instantiate(); add_child(v)
	for mi: MeshInstance3D in v.find_children("*", "MeshInstance3D", true, false): mi.material_override = mat
	var aps := v.find_children("*", "AnimationPlayer", true, false)
	if aps.size() > 0:
		ap = aps[0]
		for c in ["idle", "walk", "run"]:
			if ap.has_animation(c): ap.get_animation(c).loop_mode = Animation.LOOP_LINEAR
	var s: Dictionary = STATS[k]; hp = s.hp; max_hp = s.hp; radius = s.radius; def = {"atk": s.atk}
	cd = randf_range(0.3, 1.2)
	_play("idle")
	return self
func _play(c: String, spd := 1.0) -> void:
	if ap == null or not ap.has_animation(c): return
	if clip != c or not ap.is_playing(): ap.play(c, 0.12); clip = c
	ap.speed_scale = spd
func _hero() -> Node3D: return boss._hero()
func ground_y(p: Vector3) -> float: return boss._gy(p.x, p.z) + (2.0 if kind == "wisp" else 0.0)
func take_damage(dmg: float, _from := Vector3.ZERO) -> void:
	if state == "dead": return
	hp = maxf(0.0, hp - float(dmg))
	if hp <= 0.0:
		state = "dead"; dead_t = 0.0; _play("death"); return
	if state != "attack": state = "hit"; st_t = 0.0; _play("hit"); ap.seek(0.0, true) if ap else null
func tick(dt: float) -> bool:   # false = free me
	if state == "dead":
		dead_t += dt
		if ap and clip == "death" and not ap.is_playing(): ap.play("death"); ap.seek(ap.current_animation_length - 0.01, true); ap.pause()   # hold the last frame
		return dead_t < 4.0
	cd = maxf(0.0, cd - dt)
	var h := _hero()
	if h == null: _play("idle"); return true
	var to := h.global_position - global_position; to.y = 0.0
	var d := to.length()
	if d > 0.01: rotation.y = lerp_angle(rotation.y, atan2(to.x, to.z), minf(1.0, dt * 8.0))   # +Z forward
	var C := clips()
	match state:
		"hit":
			st_t += dt
			if st_t >= float(C.hit.seconds): state = "chase"
		"attack":
			atk_t += dt
			if not atk_done and atk_t >= atk_hit:
				atk_done = true
				var hd := Vector2(h.global_position.x - global_position.x, h.global_position.z - global_position.z).length()
				if hd <= atk_reach + 0.6: _land_hit()
			if atk_t >= float(C[clip].seconds) if C.has(clip) else 1.0: state = "chase"; cd = float(STATS[kind].cd)
		"chase":
			var reach := 1.4 if kind == "fiend" else 1.2
			if d <= reach + 0.4 and cd <= 0.0: _start_attack(d)
			elif d > reach:
				var spd: float = STATS[kind].speed if d > 6.0 else 1.6
				global_position += to.normalized() * minf(spd * dt, d - reach * 0.8)
				var run := spd > 2.0
				var cs: float = float(C.run.get("root_speed_mps", C.run.get("suggested_speed_mps", 6.0)) if C.run.get("root_speed_mps") != null else C.run.get("suggested_speed_mps", 6.0)) if run else float(C.walk.get("root_speed_mps") if C.walk.get("root_speed_mps") != null else C.walk.get("suggested_speed_mps", 2.5))
				_play("run" if run else "walk", clampf(spd / maxf(cs, 0.1), 0.4, 2.0))
			else: _play("idle")
	global_position.y = ground_y(global_position)
	return true
func _start_attack(d: float) -> void:
	var C := clips(); var opts := []
	for c in ["attack", "attack2", "attack3"]:
		if C.has(c): opts.append(c)
	var c: String = opts[randi() % opts.size()]
	if kind == "fiend" and d > 1.5: c = "attack2"   # the long hook reaches 2.27 m
	state = "attack"; atk_t = 0.0; atk_done = false; atk_hit = float(C[c].hit_time)
	atk_aoe = C[c].get("aoe_radius_m") != null
	atk_reach = float(C[c].get("aoe_radius_m")) if atk_aoe else float(C[c].get("reach_m", 1.5))
	clip = ""; _play(c); if ap: ap.seek(0.0, true)
func _land_hit() -> void:
	var m = boss.m
	if bool(m.get("cheat").get("god", false)): return
	var party = m.get("party")
	if party and party.combat: party.combat.titan_hit(float(STATS[kind].frac)); hits_landed += 1
