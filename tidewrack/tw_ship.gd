class_name TwShip
extends CharacterBody3D
## test 32: Tidewrack Sea sailing controller (port of the JS sailing controller, stats from stage1/SHIP_UPGRADES.md).
## Rudder + throttle with coasting, wind factor, shallows cap, gust charm, Gerstner bob (High) / script bob (Low).
## The hull collides (layer 10, mask 1) with the island/coast/terrain colliders and the invisible storm-border boxes.
const STATS := {
	"galleon": [[13.0, 1.2, 14.0], [16.0, 1.5, 16.0], [20.0, 1.9, 18.0], [26.0, 2.4, 20.0]],   # top m/s, accel m/s2, turn deg/s
	"skiff": [[9.0, 2.0, 40.0], [11.0, 2.4, 44.0], [13.5, 2.9, 48.0], [17.0, 3.5, 52.0]]}
const GUST := [[0.0, 0.0, 0.0], [0.15, 6.0, 40.0], [0.20, 7.0, 35.0], [0.30, 8.0, 30.0]]    # bonus, seconds, cooldown
const MODEL := {"galleon": ["res://assets/ships/ship_tidewrack_sailing_ship_lod1.glb", -0.35], "skiff": ["res://assets/ships/ship_boat_sail_lod1.glb", 0.35]}
const WAVES := [[38.0, 0.55, 0.0], [17.0, 0.25, 0.7], [7.0, 0.08, -0.5]]   # L m, A m, angle offset from wind (rad)
var kind := "galleon"
var tier := 0
var heading := 0.0          # yaw, bow = +Z model -> world dir (sin h, cos h)
var speed := 0.0
var throttle := 0.0
var gust_t := 0.0
var gust_cd := 0.0
var high := true
var wind := Vector2(0.8, 0.6)
var shallow_fn: Callable    # (local Vector2) -> metres to land
var vis: Node3D
var addon: Node3D
var bob_t := 0.0

func setup(k: String, t: int, hi: bool) -> TwShip:
	kind = k; tier = t; high = hi; name = "TwShip_" + k
	collision_layer = 1 << 9; collision_mask = 1; motion_mode = CharacterBody3D.MOTION_MODE_FLOATING
	var cs := CollisionShape3D.new(); var bs := BoxShape3D.new()
	bs.size = Vector3(8.0, 4.0, 28.0) if k == "galleon" else Vector3(2.4, 2.0, 7.0); cs.shape = bs; cs.position.y = 2.0 if k == "galleon" else 1.0
	add_child(cs)
	vis = Node3D.new(); add_child(vis)
	var v: Node3D = load(MODEL[k][0]).instantiate(); vis.add_child(v); vis.position.y = MODEL[k][1]
	for mi: MeshInstance3D in v.find_children("*", "MeshInstance3D", true, false):
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for si in mi.mesh.get_surface_count():
			var sm = mi.mesh.surface_get_material(si)
			if sm is BaseMaterial3D:   # same as the harbour ships (test 26): solid, both-sided sails
				sm = sm.duplicate(); sm.cull_mode = BaseMaterial3D.CULL_DISABLED; sm.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED; mi.set_surface_override_material(si, sm)
	set_tier(t)
	return self

func set_tier(t: int) -> void:
	tier = clampi(t, 0, 3)
	if addon: addon.queue_free(); addon = null
	if tier == 0: return
	addon = load("res://tidewrack/stage1/meshes/upg_%s_t%d%s.glb" % [kind, tier, "" if high else "_lod1"]).instantiate()
	for mi: MeshInstance3D in addon.find_children("*", "MeshInstance3D", true, false):
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; mi.material_override = load("res://tidewrack/stage1/shaders/vc_lit.tres")
	vis.add_child(addon)   # identity transform on the ship root (same origin, bow +Z, waterline 0)

func stats() -> Array: return STATS[kind][tier]
func top_speed() -> float:
	var s: Array = stats(); var dir := Vector2(sin(heading), cos(heading))
	var a := clampf(dir.dot(wind.normalized()) * 0.5 + 0.5, 0.0, 1.0)
	var v: float = s[0] * lerpf(0.55, 1.15, a)
	if gust_t > 0.0: v *= 1.0 + GUST[tier][0]
	if kind == "galleon" and alt <= 0.0 and shallow_fn.is_valid() and float(shallow_fn.call(Vector2(position.x, position.z))) < 25.0: v *= 0.4
	return v

func gust() -> bool:
	if tier == 0 or gust_cd > 0.0: return false
	gust_t = GUST[tier][1]; gust_cd = GUST[tier][2]; return true

func wave_h(p: Vector2, t: float) -> float:
	var h := 0.0; var wa := atan2(wind.y, wind.x)
	for w in WAVES:
		var d := Vector2(cos(wa + w[2]), sin(wa + w[2])); var k: float = TAU / w[0]; var c := sqrt(9.8 / k)
		h += w[1] * sin(k * (d.dot(p) - c * t))
	return h

## test 33: skiff model offset -0.3 -> +0.35: its floor (model y 0.25) sat at the waterline, so the sea showed through the hull.
## test 33 (boss): fly cheat lifts the whole ship; speed cheat scales sailing speed. Set by TidewrackSea.drive().
var alt := 0.0          # metres above the sea (0 = afloat)
var speed_mul := 1.0
func drive(inp: Vector2, dt: float) -> void:
	var s: Array = stats()
	if absf(inp.y) > 0.15: throttle = clampf(throttle - inp.y * dt * 0.7, -0.25, 1.0)   # coasting: the sail setting holds
	var want := top_speed() * throttle * speed_mul
	speed = move_toward(speed, want, s[1] * dt * (1.0 if absf(want) > absf(speed) else 0.6))
	var steer := clampf(absf(speed) / (s[0] * 0.3), 0.25, 1.0)
	heading -= deg_to_rad(s[2]) * inp.x * steer * dt
	gust_t = maxf(0.0, gust_t - dt); gust_cd = maxf(0.0, gust_cd - dt)
	var dir := Vector3(sin(heading), 0.0, cos(heading))
	velocity = dir * speed; velocity.y = 0.0
	move_and_slide()
	if get_slide_collision_count() > 0: speed *= 0.5   # bumped the shore / a border box: lose way
	bob_t += dt
	var p := Vector2(global_position.x, global_position.z)
	var h := wave_h(p, bob_t) if high else sin(bob_t * 0.9) * 0.18
	if alt > 0.0: h *= clampf(1.0 - alt / 3.0, 0.0, 1.0)   # no wave bob once airborne
	vis.position.y = MODEL[kind][1] + h * 0.8
	position.y = alt
	rotation = Vector3(0.0, heading, 0.0)
