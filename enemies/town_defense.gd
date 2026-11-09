class_name TownDefense
extends Node
## Existing crate, barrel and fence props set outside each gate as a chicane.
## The center of every gate stays a clear walking lane. These props are not the haven:
## undead are stopped by the perimeter even if a prop is missing.

const LANE_HALF := 2.4
const LANE_LEN := 18.0
const PROP := {
	"crate_stack": "res://assets/card2/prop_crate_stack_lod1.glb",
	"barrel_group": "res://assets/card2/prop_barrel_group_lod1.glb",
	"fence": "res://assets/card2/prop_fence_lod1.glb",
}

var main: Node
var lane_rects: Array = []

func build(m: Node) -> void:
	main = m
	name = "TownDefense"
	TownHaven.clear_obstacles()
	lane_rects.clear()
	var gates: Array = load("res://scripts/main.gd").GATES
	for gd in gates:
		var out := Vector3(gd[0].x, 0, gd[0].y)
		var along := Vector3(out.z, 0, -out.x)
		var lane := _lane_rect(out)
		lane_rects.append(lane)
		_place("crate_stack", out, along, -1.0, 6.0, lane)
		_place("barrel_group", out, along, 1.0, 9.5, lane)
		_place("fence", out, along, -1.0, 13.0, lane)
func _lane_rect(out: Vector3) -> Rect2:
	var lim := TownHaven.outer_limit()
	if absf(out.z) > 0.5:
		var z0 := lim if out.z > 0.0 else -(lim + LANE_LEN)
		return Rect2(-LANE_HALF, z0, LANE_HALF * 2.0, LANE_LEN)
	var x0 := lim if out.x > 0.0 else -(lim + LANE_LEN)
	return Rect2(x0, -LANE_HALF, LANE_LEN, LANE_HALF * 2.0)

func _place(kind: String, out: Vector3, along: Vector3, side: float, dist: float, lane: Rect2) -> void:
	var path: String = PROP[kind]
	if not ResourceLoader.exists(path): return
	var pos := out * (TownHaven.outer_limit() + dist) + along * (side * 5.2)
	var yaw := atan2(out.x, out.z)
	if kind == "fence": yaw += PI * 0.5
	var root := Node3D.new()
	root.name = "def_%s" % kind
	add_child(root)
	var vis: Node3D = (load(path) as PackedScene).instantiate()
	root.add_child(vis)
	var box := _aabb(vis)
	var guard := 0
	while guard < 10 and _overlaps_lane(pos, box, lane):
		pos += along * side * 0.7
		guard += 1
	root.position = Vector3(pos.x, _gy(pos.x, pos.z), pos.z)
	root.rotation.y = yaw
	var rect := Rect2(pos.x - box.x * 0.5, pos.z - box.y * 0.5, box.x, box.y)
	# Fence meshes are long; keep the registered blocker on the flank, never the lane.
	if lane.intersects(rect):
		rect = Rect2(pos.x - 0.45, pos.z - 0.45, 0.9, 0.9)
	TownHaven.add_obstacle(rect)
	var sb := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(maxf(rect.size.x, 0.4), 1.3, maxf(rect.size.y, 0.4))
	cs.shape = sh
	cs.position.y = 0.65
	sb.add_child(cs)
	root.add_child(sb)

func _overlaps_lane(pos: Vector3, box: Vector2, lane: Rect2) -> bool:
	var rect := Rect2(pos.x - box.x * 0.5, pos.z - box.y * 0.5, box.x, box.y)
	return lane.intersects(rect)

func _aabb(n: Node) -> Vector2:
	var ab := AABB()
	var first := true
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var mesh_ab: AABB = (mi as MeshInstance3D).get_aabb()
		ab = mesh_ab if first else ab.merge(mesh_ab)
		first = false
	if first or ab.size.length() < 0.05: return Vector2(1.2, 1.2)
	return Vector2(clampf(ab.size.x, 0.6, 2.4), clampf(ab.size.z, 0.4, 2.4))

func _gy(x: float, z: float) -> float:
	if main and main.has_method("ground_y"): return float(main.ground_y(x, z))
	if main and main.has_method("height"): return float(main.height(x, z))
	return 0.0

func lane_blocked(sample: Vector2, pad := 0.35) -> bool:
	var probe := Rect2(sample.x - pad, sample.y - pad, pad * 2.0, pad * 2.0)
	for r in TownHaven.obstacles:
		if r.intersects(probe): return true
	return false
