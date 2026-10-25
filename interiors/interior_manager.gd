class_name InteriorManager extends Node3D
## Walk-in interiors. Each interior is built once (lazily) far from the world at FAR + i*STEP and the hero is
## teleported through the door. Inside: sun off, floors above the hero hidden and drawn as an outline only.
## Hooks into main.gd: setup(main) after buildings+hero exist; climb(hero, dir, dt) before move_and_slide;
## current_name() for the HUD; active() to keep followers off the terrain height.
const B := preload("res://interiors/interior_builder.gd")
const DEF := preload("res://interiors/interior_defs.gd")
const FAR := Vector3(4000, 600, 4000)
const STEP := 160.0
var main: Node
var built := {}         # id -> info
var cur: Dictionary = {}
var cur_bld: Dictionary = {}
var cooldown := 0.0
var climbing := false
var sun_mask := 0

func setup(m: Node) -> void:
	main = m
	if main.sun: main.sun.light_cull_mask &= ~InteriorKit.LAYER

## library/farmhouse (and mage/colosseum) report a zero AABB in the game (lazy-loaded shells); interiors now build from
## DEF.SIZE (see get_info), so nothing is closed any more. Keep the list for emergencies.
const CLOSED := []
func has_interior(id: String) -> bool: return DEF.D.has(id) and not CLOSED.has(id)
func active() -> bool: return not cur.is_empty()
func current_name() -> String: return cur.get("name", "")

func get_info(id: String, size: Vector3) -> Dictionary:
	if not built.has(id):
		# always build from the tested size table: the live exterior AABB can change when a shell is re-exported
		# (e.g. library/farmhouse), which re-laid the interior around an untested footprint and trapped the hero at spawn
		var info := B.build(id, DEF.D[id], DEF.SIZE.get(id, size))
		var i := DEF.D.keys().find(id)
		info.node.position = FAR + Vector3(i * STEP, 0, 0)
		add_child(info.node)
		built[id] = info
	return built[id]

## door in building-local coords: card2 exteriors use the probed facade (tests/door_probe.gd), old shells the AABB front
func door_local(b: Dictionary) -> Vector3:
	if b.has("door"): return b.door   # second entrance (farmstead barn doors)
	var d = load("res://scripts/main.gd").card2_door(b.id)   # Beth's door_points for card2/Tripo exteriors
	if d != null: return d
	return DEF.DOORS.get(b.id, Vector3(0, 0, b.aabb.end.z))

func door_world(b: Dictionary) -> Vector3:
	return b.node.global_transform * door_local(b)

func _physics_process(dt: float) -> void:
	if main == null or main.hero == null: return
	cooldown -= dt
	var hero: CharacterBody3D = main.hero
	if cur.is_empty():
		if cooldown > 0: return
		for b in main.buildings + main.get("extra_doors"):
			if not has_interior(b.id): continue
			var dl: Vector3 = door_local(b); var lp: Vector3 = b.node.global_transform.affine_inverse() * hero.global_position
			var hv := Vector2(hero.velocity.x, hero.velocity.z)
			var into: Vector3 = b.node.global_transform.basis * Vector3(0, 0, -1)
			# blocked by porch steps/colliders in front of the facade (training hall): accept up to 2.5 m out when pressed against them
			var reach_z: float = maxf(dl.z + 1.4, b.aabb.end.z + (2.5 if hero.is_on_wall() else 0.8))
			if absf(lp.x - dl.x) < 1.8 and lp.z < reach_z and lp.z > dl.z - 1.0 and absf(lp.y) < 3.0 and (hv.dot(Vector2(into.x, into.z)) > 0.5 or (hero.is_on_wall() and hero.get_wall_normal().dot(into) < -0.5)):
				enter(b); return
	else:
		var lp2: Vector3 = cur.node.to_local(hero.global_position)
		# leave through the door; also when walking back onto the entry spot (some refit rooms put props by exit_z)
		var back_z: float = minf(cur.exit_z, cur.spawn.z + 0.6)
		var hv2: Vector3 = cur.node.global_transform.basis.inverse() * hero.velocity
		if cooldown <= 0 and absf(lp2.x - cur.spawn.x * float(lp2.z <= cur.exit_z)) < 2.0 and (lp2.z > cur.exit_z or (lp2.z > back_z and hv2.z > 0.5)): exit(); return
		_update_floors(lp2.y)

func enter(b: Dictionary) -> void:
	cur_bld = b; cur = get_info(b.id, b.aabb.size)
	_teleport(cur.node.to_global(cur.spawn), cur.node.global_rotation.y)
	if main.sun: main.sun.visible = false
	_env_inside(true)
	cooldown = 0.8

func exit() -> void:
	var b := cur_bld; cur = {}; cur_bld = {}
	var dl: Vector3 = door_local(b)
	var out: Vector3 = b.node.global_transform * Vector3(dl.x, 0, maxf(dl.z + 2.0, b.aabb.end.z + 1.0))
	out.y = main.height(out.x, out.z) + 0.1
	_teleport(out, b.node.global_rotation.y + PI)
	if main.sun: main.sun.visible = true
	_env_inside(false)
	cooldown = 1.0

func _teleport(p: Vector3, facing: float) -> void:
	var hero: CharacterBody3D = main.hero
	hero.global_position = p + Vector3(0, 0.12, 0); hero.velocity = Vector3.ZERO   # never start embedded in a raised floor/threshold
	if main.get("yaw") != null: main.yaw = facing
	if main.get("party") and main.party:
		main.party.trail = PackedVector3Array()
		for c in main.party.companions: c.node.global_position = p + Vector3(0.8, 0, 0.8)

func floor_of(info: Dictionary, local_y: float) -> int:
	var k := 0
	for i in info.floors.size():
		if local_y >= info.floors[i].y - 0.6: k = i
	return k

func _update_floors(local_y: float) -> void:
	var k := floor_of(cur, local_y)
	for i in cur.floors.size():
		var F: Dictionary = cur.floors[i]
		F.node.visible = i <= k
		F.outline.visible = i > k

## Ladders: climbing only while the player pushes into the ladder (never automatic). Returns true if it set velocity.
func climb(hero: CharacterBody3D, dir: Vector3, _dt: float) -> bool:
	if cur.is_empty(): climbing = false; return false
	var lp: Vector3 = cur.node.to_local(hero.global_position)
	var ldir: Vector3 = cur.node.global_transform.basis.inverse() * dir
	for l in cur.ladders:
		var rel: Vector3 = lp - l.pos
		var s: float = rel.x * l.dir.x + rel.z * l.dir.z               # along climb direction (ladder at s=0)
		var lat: float = absf(rel.x * -l.dir.z + rel.z * l.dir.x)
		if lat > 0.6 or s < -1.1 or s > 0.7 or lp.y < l.pos.y - 0.3 or lp.y > l.top + 0.4: continue
		var push: float = ldir.x * l.dir.x + ldir.z * l.dir.z
		if push > 0.4 and lp.y < l.top + 0.05 and s < 0.05:       # climb up
			climbing = true; hero.velocity = Vector3(0, 2.4, 0) + cur.node.global_transform.basis * (l.dir * clampf((-0.5 - s) * 3.0, -1.0, 1.0))
			return true
		if push > 0.4 and lp.y >= l.top - 0.05: climbing = false; return false   # step off onto the loft
		if push < -0.4 and lp.y > l.pos.y + 0.15 and s < 0.7:      # climb down
			climbing = true; hero.velocity = Vector3(0, -2.4, 0)
			hero.velocity += cur.node.global_transform.basis * (l.dir * clampf((-0.5 - s) * 3.0, -1.5, 1.5))
			return true
		if climbing and lp.y > l.pos.y + 0.15 and s < 0.0:
			hero.velocity = Vector3.ZERO; return true                  # hang
	climbing = false
	return false

var _env_saved := []
func _env_inside(on: bool) -> void:
	var env: Environment = main.get("env")
	if env == null: return
	if on:
		_env_saved = [env.ambient_light_source, env.ambient_light_color, env.fog_enabled]
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.56, 0.54, 0.5); env.fog_enabled = false
	elif _env_saved.size():
		env.ambient_light_source = _env_saved[0]; env.ambient_light_color = _env_saved[1]; env.fog_enabled = _env_saved[2]

func _process(_dt: float) -> void:
	# main._set_time() dims ambient at night; interiors keep a steady indoor level (runs after main: child node)
	if not cur.is_empty() and main and main.get("env"): main.env.ambient_light_energy = 0.9
