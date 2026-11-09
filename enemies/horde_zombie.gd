class_name HordeZombie
extends Enemy
## Placeholder undead. Shamblers, runners, undead knights and undead sailors share this zombie
## brain: they advance, herd, and bite. They do not telegraph, duel, or use soldier patterns.
## Beth's meshes are not in this build. MODEL_HOOK is the swap point; leave it empty until then.

const BODY_R := 0.46
const BITE_REACH := 1.40
const BITE_HEIGHT := 2.5
const GRAB_REACH := 0.95
const SEPARATION := 0.82
const RECOVER := 0.65
const MODEL_HOOK := {
	"shambler": "",
	"runner": "",
	"undead_knight": "",
	"undead_sailor": "",
}
static var _mats := {}

var role := "shambler"
var runner := false
var anchor := Vector2.ZERO
var combat: HeroCombat
var last_safe := Vector3.ZERO
var pending_kind := ""
var windup_need := 0.45
var dead_for := 0.0
var allow_wedge := false
var crowd_id := -1
var crowd_lock := 0.0
var _visual_ready := false
var _label: Label3D

static func body_radius(_tid := "") -> float: return BODY_R

static func profile(tid: String) -> Dictionary:
	match tid:
		"runner", "horde_runner":
			return {"speed": 3.35, "hp": 140, "atk": 16.0, "role": "runner", "runner": true, "windup": 0.28}
		"undead_knight":
			return {"speed": 1.15, "hp": 260, "atk": 20.0, "role": "undead_knight", "runner": false, "windup": 0.5}
		"undead_sailor":
			return {"speed": 1.20, "hp": 240, "atk": 18.0, "role": "undead_sailor", "runner": false, "windup": 0.48}
		"skeleton":
			return {"speed": 1.25, "hp": 190, "atk": 18.0, "role": "shambler", "runner": false, "windup": 0.45}
		_:
			return {"speed": 1.25, "hp": 190, "atk": 18.0, "role": "shambler", "runner": false, "windup": 0.45}

static func _mat(role_name: String) -> StandardMaterial3D:
	if _mats.has(role_name): return _mats[role_name]
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	match role_name:
		"runner": m.albedo_color = Color(0.74, 0.62, 0.16)
		"undead_knight": m.albedo_color = Color(0.42, 0.48, 0.56)
		"undead_sailor": m.albedo_color = Color(0.18, 0.46, 0.5)
		_: m.albedo_color = Color(0.4, 0.55, 0.32)
	_mats[role_name] = m
	return m

func setup_horde(tid: String, pos: Vector3, ground: Callable) -> HordeZombie:
	var spec := profile(tid)
	type_id = tid
	role = str(spec.role)
	runner = bool(spec.runner)
	def = {"hp": int(spec.hp), "atk": float(spec.atk), "boss": false, "reach": 1.2, "stagger": 0.4, "name": role}
	hp = float(spec.hp)
	max_hp = hp
	radius = BODY_R
	speed_mps = float(spec.speed)
	windup_need = float(spec.windup)
	height_fn = ground
	position = pos
	home = pos
	last_safe = pos
	anchor = Vector2(pos.x, pos.z)
	state = "approach"
	name = "%s_%d" % [tid, get_instance_id()]
	_build_visual()
	_visual_ready = true
	return self

func _build_visual() -> void:
	var mat := _mat(role)
	var hook := str(MODEL_HOOK.get(role, ""))
	if hook != "" and ResourceLoader.exists(hook):
		var packed: PackedScene = load(hook)
		var mdl := packed.instantiate()
		add_child(mdl)
	else:
		var body := MeshInstance3D.new()
		var cap := CapsuleMesh.new()
		cap.radius = 0.28 if not runner else 0.24
		cap.height = 1.28 if not runner else 1.45
		cap.material = mat
		body.mesh = cap
		body.position.y = 0.72
		body.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(body)
		var head := MeshInstance3D.new()
		var sph := SphereMesh.new()
		sph.radius = 0.18
		sph.height = 0.36
		sph.material = mat
		head.mesh = sph
		head.position.y = 1.48
		head.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(head)
		if role == "undead_knight":
			var helm := MeshInstance3D.new()
			var box := BoxMesh.new()
			box.size = Vector3(0.36, 0.14, 0.36)
			box.material = mat
			helm.mesh = box
			helm.position.y = 1.66
			add_child(helm)
		elif role == "undead_sailor":
			var brim := MeshInstance3D.new()
			var cyl := CylinderMesh.new()
			cyl.top_radius = 0.26
			cyl.bottom_radius = 0.26
			cyl.height = 0.05
			cyl.material = mat
			brim.mesh = cyl
			brim.position.y = 1.62
			add_child(brim)
	_label = Label3D.new()
	_label.text = "PLACEHOLDER\n%s\nnot Beth's model" % _pretty(role)
	_label.font_size = 42
	_label.pixel_size = 0.0022
	_label.position = Vector3(0, 2.15, 0)
	_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_label.modulate = Color(1, 0.96, 0.72)
	_label.outline_size = 6
	_label.outline_modulate = Color(0, 0, 0, 1)
	add_child(_label)

func _pretty(r: String) -> String:
	match r:
		"undead_knight": return "UNDEAD KNIGHT"
		"undead_sailor": return "UNDEAD SAILOR"
		"runner": return "RUNNER"
		_: return "SHAMBLER"

func is_boss() -> bool: return false

func pattern_hits(_p: Dictionary, _pt: Vector3) -> bool: return false

func take_damage(dmg: int, _from: Vector3) -> void:
	if not alive(): return
	hp = maxf(0.0, hp - float(dmg))
	if hp <= 0.0: _die()

func kill_now(_from: Vector3) -> void:
	if not alive(): return
	hp = 0.0
	_die()

## Bind a pooled body to one simulated crowd member. The sim id stays the identity.
func bind_crowd(tid: String, pos: Vector3, hp_now: float, hero: Node3D, ground: Callable, hold: Vector2, sim_id: int, wind: float = 0.0, lock: float = 0.0) -> void:
	var spec := profile(tid)
	var new_role := str(spec.role)
	type_id = tid
	runner = bool(spec.runner)
	def = {"hp": int(spec.hp), "atk": float(spec.atk), "boss": false, "reach": 1.2, "stagger": 0.4, "name": new_role}
	max_hp = float(spec.hp)
	hp = hp_now
	radius = BODY_R
	speed_mps = float(spec.speed)
	windup_need = float(spec.windup)
	height_fn = ground
	crowd_id = sim_id
	if not _visual_ready or role != new_role:
		role = new_role
		_clear_visual()
		_build_visual()
		_visual_ready = true
	else:
		role = new_role
	global_position = pos
	if height_fn.is_valid(): global_position.y = float(height_fn.call(pos.x, pos.z))
	home = global_position
	last_safe = global_position
	anchor = hold
	target = hero
	visible = true
	dead_for = 0.0
	crowd_lock = maxf(0.0, lock)
	if wind > 0.0 and crowd_lock <= 0.0:
		pending_kind = "bite"
		state = "windup"
		t_state = wind
	else:
		pending_kind = ""
		state = "approach"
		t_state = 0.0

func release_crowd() -> void:
	crowd_id = -1
	crowd_lock = 0.0
	target = null
	pending_kind = ""
	visible = false
	set_state("defeated")

func _clear_visual() -> void:
	for c in get_children():
		remove_child(c)
		c.free()
	_label = null

func _die() -> void:
	cancel_strike()
	set_state("defeated")
	dead_for = 0.0
	if _label: _label.text = "PLACEHOLDER\nCORPSE"
	died.emit(self)

func cancel_strike() -> void: pending_kind = ""

func cancel_if_hero_safe() -> void:
	if target != null and is_instance_valid(target) and TownHaven.hero_safe(target.global_position):
		cancel_strike()

func shove(delta: Vector3) -> void:
	var a := Vector2(global_position.x, global_position.z)
	var nxt := TownHaven.clamp_move(a, a + Vector2(delta.x, delta.z), radius)
	nxt = _wedge(nxt)
	_commit(nxt)

func _physics_process(dt: float) -> void:
	if not alive():
		dead_for += dt
		return
	if crowd_lock > 0.0: crowd_lock = maxf(0.0, crowd_lock - dt)
	if target == null or not is_instance_valid(target): return
	# Far undead tick every 4th frame. The playable ring around town is inside this.
	var flat := Vector2(global_position.x - target.global_position.x, global_position.z - target.global_position.z).length()
	if flat > 100.0 and Engine.get_physics_frames() % 4 != 0 and pending_kind == "": return
	var step_dt := minf(dt, 0.25) # a hitch does not become one giant unswept leap; remainder is extra swept steps
	var left := dt
	while left > 0.0:
		var slice := minf(step_dt, left)
		_step(slice)
		left -= slice

func _step(dt: float) -> void:
	var hero_p := target.global_position
	var here := Vector2(global_position.x, global_position.z)
	var goal := _goal(hero_p, here)
	var to := goal - here
	var dest := here
	if to.length() > 0.08:
		dest = here + to.normalized() * minf(speed_mps * dt, to.length())
	if pending_kind == "lunge":
		var lung := Vector2(hero_p.x, hero_p.z) - here
		if lung.length() > 0.05 and not TownHaven.inside(hero_p):
			dest = here + lung.normalized() * minf(2.4 * dt / maxf(windup_need, 0.05) + speed_mps * dt, lung.length())
	dest = _separate(dest)
	var nxt := TownHaven.clamp_move(here, dest, radius)
	allow_wedge = _hero_in_wedge(hero_p, here)
	nxt = _wedge(nxt)
	_commit(nxt)
	_face_toward(goal - here, dt)
	_attack(dt, hero_p)

func _goal(hero_p: Vector3, here: Vector2) -> Vector2:
	var hp := Vector2(hero_p.x, hero_p.z)
	var aggro := 34.0 if runner else 18.0
	# A hero inside a town building is parked far from the map. Keep pressing the walls.
	if not TownHaven.town_interior_active() and not TownHaven.inside(hero_p) and not TownHaven.far_parking(hp) and here.distance_to(hp) <= aggro:
		return hp
	var horde := _horde()
	if horde != null and horde.noise_r > 0.0 and here.distance_to(horde.noise_at) <= horde.noise_r * (1.15 if runner else 1.0):
		return horde.noise_at
	return anchor

func _hero_in_wedge(hero_p: Vector3, here: Vector2) -> bool:
	if TownHaven.inside(hero_p): return false
	var hp := Vector2(hero_p.x, hero_p.z)
	if not TownHaven.in_escape_wedge(hp): return false
	var aggro := 34.0 if runner else 18.0
	return here.distance_to(hp) <= aggro

func _wedge(p: Vector2) -> Vector2:
	if allow_wedge or not TownHaven.in_escape_wedge(p): return p
	var ang := rad_to_deg(atan2(p.x, p.y))
	if ang < 0.0: ang += 360.0
	var edge := 114.0 if absf(ang - TownHaven.WEDGE_A) <= absf(ang - TownHaven.WEDGE_B) else 156.0
	var rad := maxf(p.length(), TownHaven.stand_off(radius))
	var a := deg_to_rad(edge)
	var out := Vector2(sin(a), cos(a)) * rad
	if TownHaven.blocked(out, radius): out = TownHaven.nearest_outside(out, radius)
	return out

func _separate(p: Vector2) -> Vector2:
	var dir := Vector2.ZERO
	var seen := 0
	var parent := get_parent()
	if parent == null or parent.get("enemies") == null: return p
	for e in parent.enemies:
		if seen >= 6: break
		if e == self or not is_instance_valid(e) or not (e is HordeZombie) or not e.alive(): continue
		var o := Vector2(e.global_position.x, e.global_position.z)
		var d := p - o
		var dist := d.length()
		if dist < 0.001:
			d = Vector2(0.17, 0.09)
			dist = d.length()
		if dist < SEPARATION:
			dir += d / dist * (SEPARATION - dist)
			seen += 1
	return p + dir

func _commit(nxt: Vector2) -> void:
	global_position.x = nxt.x
	global_position.z = nxt.y
	if height_fn.is_valid(): global_position.y = float(height_fn.call(global_position.x, global_position.z))
	var flat := Vector2(global_position.x, global_position.z)
	if not TownHaven.blocked(flat, radius) and not TownHaven.far_parking(flat): last_safe = global_position

func _face_toward(to: Vector2, dt: float) -> void:
	if to.length() < 0.05: return
	var yaw := atan2(-to.x, -to.y)
	rotation.y = lerp_angle(rotation.y, yaw, minf(1.0, dt * 5.0))

func _height_ok(hero_p: Vector3) -> bool:
	return absf(hero_p.y - global_position.y) <= BITE_HEIGHT

func _attack(dt: float, hero_p: Vector3) -> void:
	var d := Vector2(hero_p.x - global_position.x, hero_p.z - global_position.z).length()
	if crowd_lock > 0.0:
		if state == "windup" or state == "recover":
			cancel_strike()
			state = "approach"
			t_state = 0.0
		return
	if state == "recover":
		t_state += dt
		if t_state >= RECOVER:
			set_state("approach")
		return
	if state != "windup":
		if d <= BITE_REACH and _height_ok(hero_p) and TownHaven.strike_allowed(global_position, hero_p, "bite"):
			pending_kind = "lunge" if runner and d > GRAB_REACH else ("grab" if d <= GRAB_REACH else "bite")
			set_state("windup")
		return
	t_state += dt
	if TownHaven.hero_safe(hero_p):
		cancel_strike()
		set_state("approach")
		return
	if t_state < windup_need: return
	if _resolve(hero_p): set_state("recover")

func _crowd() -> HordeCrowd:
	var p := get_parent()
	if p is HordeCrowd: return p
	return null

func _resolve(hero_p: Vector3) -> bool:
	var kind := pending_kind
	var c := _combat()
	if c == null:
		pending_kind = ""
		return true
	var allowed := TownHaven.strike_allowed(global_position, hero_p, kind)
	var reach := BITE_REACH + 0.15
	var dist := Vector2(hero_p.x - global_position.x, hero_p.z - global_position.z).length()
	var hp_before := c.hp
	var dealt := 0
	var connected := allowed and dist <= reach and _height_ok(hero_p) and kind != ""
	if connected:
		var horde := _crowd()
		if horde != null and not horde.claim_strike(): return false
		var atk := float(def.atk) + (6.0 if kind == "grab" else 0.0)
		dealt = c.take_hit(atk, 1.0)
	pending_kind = ""
	TownHaven.note({
		"e": "strike", "kind": kind, "allowed": allowed, "dealt": dealt,
		"hp_before": hp_before, "hp_after": c.hp,
		"ax": snappedf(global_position.x, 0.01), "az": snappedf(global_position.z, 0.01),
		"tx": snappedf(hero_p.x, 0.01), "tz": snappedf(hero_p.z, 0.01),
		"hero_inside": TownHaven.inside(hero_p),
	})
	return true

func _combat() -> HeroCombat:
	if combat != null and is_instance_valid(combat): return combat
	var m = TownHaven.main_node
	if m != null and m.get("party") != null and m.party.get("combat") != null: return m.party.combat
	return null

func _horde() -> HordeDirector:
	var m = TownHaven.main_node
	if m != null and m.get("horde") is HordeDirector: return m.horde
	return null
