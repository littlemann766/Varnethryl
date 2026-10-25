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

func has_interior(id: String) -> bool: return DEF.D.has(id)
func active() -> bool: return not cur.is_empty()
func current_name() -> String: return cur.get("name", "")

func get_info(id: String, size: Vector3) -> Dictionary:
	if not built.has(id):
		var info := B.build(id, DEF.D[id], size)
		var i := DEF.D.keys().find(id)
		info.node.position = FAR + Vector3(i * STEP, 0, 0)
		add_child(info.node)
		built[id] = info
	return built[id]

func door_world(b: Dictionary) -> Vector3:
	return b.node.global_transform * Vector3(0, 0, b.aabb.end.z)

func _physics_process(dt: float) -> void:
	if main == null or main.hero == null: return
	cooldown -= dt
	var hero: CharacterBody3D = main.hero
	if cur.is_empty():
		if cooldown > 0: return
		for b in main.buildings:
			if not has_interior(b.id): continue
			var dp: Vector3 = door_world(b); var lp: Vector3 = b.node.global_transform.affine_inverse() * hero.global_position
			var hv := Vector2(hero.velocity.x, hero.velocity.z)
			var into: Vector3 = b.node.global_transform.basis * Vector3(0, 0, -1)
			if Vector2(hero.global_position.x - dp.x, hero.global_position.z - dp.z).length() < 2.2 and absf(lp.x) < 2.0 and hv.dot(Vector2(into.x, into.z)) > 0.5:
				enter(b); return
	else:
		var lp2: Vector3 = cur.node.to_local(hero.global_position)
		if cooldown <= 0 and lp2.z > cur.exit_z and absf(lp2.x) < 2.0: exit(); return
		_update_floors(lp2.y)

func enter(b: Dictionary) -> void:
	cur_bld = b; cur = get_info(b.id, b.aabb.size)
	_teleport(cur.node.to_global(cur.spawn), cur.node.global_rotation.y)
	if main.sun: main.sun.visible = false
	cooldown = 0.8

func exit() -> void:
	var b := cur_bld; cur = {}; cur_bld = {}
	var out: Vector3 = b.node.global_transform * Vector3(0, 0, b.aabb.end.z + 2.0)
	out.y = main.height(out.x, out.z) + 0.1
	_teleport(out, b.node.global_rotation.y + PI)
	if main.sun: main.sun.visible = true
	cooldown = 1.0

func _teleport(p: Vector3, facing: float) -> void:
	var hero: CharacterBody3D = main.hero
	hero.global_position = p; hero.velocity = Vector3.ZERO
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
