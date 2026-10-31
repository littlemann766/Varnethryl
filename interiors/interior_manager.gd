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

signal left_room

func setup(m: Node) -> void:
	main = m
	if main.sun: main.sun.light_cull_mask &= ~InteriorKit.LAYER

## library/farmhouse (and mage/colosseum) report a zero AABB in the game (lazy-loaded shells); interiors now build from
## DEF.SIZE (see get_info), so nothing is closed any more. Keep the list for emergencies.
const CLOSED := []
const EXIT_DY := 1.5   # test 22: max height of the hero above/below the ground floor for the exit door
func has_interior(id: String) -> bool: return (DEF.D.has(id) or InteriorExtraDefs.D.has(id)) and not CLOSED.has(id)
## Beth's interior pass tier: "high" on phone High/Ultra + desktop, "low" on Low/Medium (set from the graphics menu)
static var pass_tier := "high"
func active() -> bool: return not cur.is_empty()
func current_name() -> String: return cur.get("name", "")

func get_info(id: String, size: Vector3) -> Dictionary:
	if not built.has(id):
		# always build from the tested size table: the live exterior AABB can change when a shell is re-exported
		# (e.g. library/farmhouse), which re-laid the interior around an untested footprint and trapped the hero at spawn
		var def: Dictionary = DEF.D[id] if DEF.D.has(id) else InteriorExtraDefs.D[id]
		var info := B.build(id, def, DEF.SIZE.get(id, InteriorExtraDefs.SIZE.get(id, size)))
		InteriorDressing.apply(info, def, pass_tier)
		var i := DEF.D.keys().find(id)
		if i < 0: i = DEF.D.size() + InteriorExtraDefs.D.keys().find(id)
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
	# test 25 (boss: "Arcane Academy of Varnethryl" stuck on screen while flying far outside): left the room without
	# the door (flight, cheat teleport, fall) -> drop the interior state so the HUD and camera know he is outside
	if not cur.is_empty() and cur.has("node") and is_instance_valid(cur.node):
		var lpx: Vector3 = (cur.node as Node3D).global_transform.affine_inverse() * hero.global_position
		var half := maxf(float(cur.get("W", 20.0)), float(cur.get("D", 20.0))) * 0.5 + 8.0
		if absf(lpx.x) > half or absf(lpx.z) > half or lpx.y > 40.0 or lpx.y < -15.0: left_room.emit(); cur = {}; cur_bld = {}
	if cur.is_empty():
		if cooldown > 0: return
		for b in main.buildings + main.get("extra_doors"):
			if not has_interior(b.id): continue
			if (b.node as Node3D).global_position.distance_squared_to(hero.global_position) > 3600.0: continue   # test 22: 200+ shell doors, near ones only
			var dl: Vector3 = door_local(b); var lp: Vector3 = b.node.global_transform.affine_inverse() * hero.global_position
			var hv := Vector2(hero.velocity.x, hero.velocity.z)
			var into: Vector3 = b.node.global_transform.basis * Vector3(0, 0, -1)
			# blocked by porch steps/colliders in front of the facade (training hall): accept up to 2.5 m out when pressed against them
			var reach_z: float = maxf(dl.z + 1.4, b.aabb.end.z + (2.5 if hero.is_on_wall() else 0.8))
			if absf(lp.x - dl.x) < 1.8 and lp.z < reach_z and lp.z > dl.z - 1.0 and absf(lp.y - dl.y) < 3.0 and (hv.dot(Vector2(into.x, into.z)) > 0.5 or (hero.is_on_wall() and hero.get_wall_normal().dot(into) < -0.5)):
				enter(b); return
	else:
		var lp2: Vector3 = cur.node.to_local(hero.global_position)
		# leave through the door; also when walking back onto the entry spot (some refit rooms put props by exit_z)
		var back_z: float = minf(cur.exit_z, cur.spawn.z + 0.6)
		var hv2: Vector3 = cur.node.global_transform.basis.inverse() * hero.velocity
		# test 22 (boss left through the door from the second storey): the exit only works at ground-floor level
		var on_ground_floor: bool = absf(lp2.y - cur.spawn.y) < EXIT_DY
		if cooldown <= 0 and on_ground_floor and absf(lp2.x - cur.spawn.x * float(lp2.z <= cur.exit_z)) < 2.0 and (lp2.z > cur.exit_z or (lp2.z > back_z and hv2.z > 0.5)): exit(); return
		_update_floors(lp2.y)
		_unstick(hero, dt, lp2)

## test 13 (boss trapped beside a Treasury wall chunk): if the player pushes the stick for 1.5 s but the hero moves
## < 0.25 m, step him to the nearest room point / door spot on his floor (always walkable, door-connected).
var _stuck_t := 0.0
var _stuck_from := Vector3.ZERO
var unsticks := 0
func _unstick(hero: CharacterBody3D, dt: float, lp: Vector3) -> void:
	var pushing: bool = main.get("joy_vec") != null and (main.joy_vec as Vector2).length() > 0.5 and not climbing
	if not pushing: _stuck_t = 0.0; _stuck_from = lp; return
	if _stuck_t == 0.0: _stuck_from = lp
	_stuck_t += dt
	if lp.distance_to(_stuck_from) > 0.25: _stuck_t = 0.0; return
	if _stuck_t < 1.0: return
	_stuck_t = 0.0
	# only when boxed in: no direction lets him move 0.8 m (pressing into a plain wall is left alone)
	for k in 8:
		var a := TAU * k / 8.0
		if not hero.test_move(hero.global_transform.translated(Vector3(0, 0.15, 0)), Vector3(cos(a), 0, sin(a)) * 0.8): return
	var fl := floor_of(cur, lp.y); var best: Vector3 = cur.spawn; var bd := INF
	for r in cur.rooms:
		if r.floor == fl and r.pos.distance_to(lp) < bd: bd = r.pos.distance_to(lp); best = r.pos
	if fl == 0 and cur.spawn.distance_to(lp) < bd: best = cur.spawn
	hero.global_position = cur.node.to_global(best + Vector3(0, 0.1, 0)); hero.velocity = Vector3.ZERO; unsticks += 1

func enter(b: Dictionary) -> void:
	if main.has_method("hide_where"): main.hide_where()   # test 25
	cur_bld = b; cur = get_info(b.id, b.aabb.size)
	_teleport(cur.node.to_global(cur.spawn), cur.node.global_rotation.y)
	if main.sun: main.sun.visible = false
	_env_inside(true)
	cooldown = 0.8

func exit() -> void:
	if main.has_method("hide_where"): main.hide_where()   # test 25
	var b := cur_bld; cur = {}; cur_bld = {}
	var dl: Vector3 = door_local(b)
	var out: Vector3 = b.node.global_transform * Vector3(dl.x, 0, maxf(dl.z + 2.0, b.aabb.end.z + 1.0))
	out.y = main.height(out.x, out.z) + 0.1
	# raised doorsteps (harbour quay, lighthouse rock): land on whatever is under the door, not inside it
	var hit := get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(out.x, (b.node.global_transform * dl).y + 3.0, out.z), out + Vector3(0, -2, 0)))
	if hit: out.y = maxf(out.y, hit.position.y + 0.1)
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
