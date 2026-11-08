class_name TownHaven
extends RefCounted
## Walled-town haven for the horde prototype. The protected volume is the whole square inside the
## outer face of the existing walls (scripts/main.gd CITY_HALF + WALL_T/2), at every height.
## It is not a plaza radius. Undead may not spawn, stand, be pushed, or land a hit inside it.
## Legacy non-undead enemies are intentionally unchanged.

const EVIDENCE_MAX := 800
const SUBSTEP_M := 0.2
const MAX_SWEEP_M := 80.0
## Northeast outside corridor left open so a crowd cannot seal every exit. Degrees, 0 = south (+Z).
const WEDGE_A := 115.0
const WEDGE_B := 155.0

static var armed := false
static var main_node: Node = null
static var obstacles: Array = [] # Rect2 footprints in world XZ
static var evidence: Array = []

static func _ms() -> GDScript:
	return load("res://scripts/main.gd")

static func city_half() -> float: return float(_ms().CITY_HALF)
static func wall_t() -> float: return float(_ms().WALL_T)
static func wall_h() -> float: return float(_ms().WALL_H)
static func gate_half() -> float: return float(_ms().GATE_HALF)

## Outer face of the wall square. Inside this, any Y, is the town.
static func outer_limit() -> float: return city_half() + wall_t() * 0.5

## Closest an undead center may stand without its body crossing the outer face.
static func stand_off(body_r: float) -> float: return outer_limit() + maxf(body_r, 0.0)

static func arm(m: Node = null) -> void:
	armed = true
	main_node = m
	obstacles.clear()

static func clear_obstacles() -> void: obstacles.clear()

static func add_obstacle(rect: Rect2) -> void:
	if rect.size.x > 0.01 and rect.size.y > 0.01: obstacles.append(rect)

static func inside_xz(x: float, z: float) -> bool:
	return maxf(absf(x), absf(z)) < outer_limit()

static func inside(p: Vector3) -> bool: return inside_xz(p.x, p.z)

static func body_inside(p: Vector2, body_r: float) -> bool:
	return maxf(absf(p.x), absf(p.y)) < stand_off(body_r) - 1e-4

static func obstacle_hit(p: Vector2, body_r: float) -> bool:
	for r in obstacles:
		var grow := Rect2(r.position - Vector2(body_r, body_r), r.size + Vector2(body_r * 2.0, body_r * 2.0))
		if grow.has_point(p): return true
	return false

static func blocked(p: Vector2, body_r: float) -> bool:
	return body_inside(p, body_r) or obstacle_hit(p, body_r)

## Fail closed until the scene arms the haven, then recompute from the hero's position every hit.
## A town building interior (the inn, the keep, ...) counts even though its cell is parked at x=4000.
## The farmhouse is outside the walls, so its interior is not this haven.
static func town_interior_active() -> bool:
	var m := main_node
	if m == null: return false
	var interiors = m.get("interiors")
	if interiors == null or not interiors.has_method("active") or not interiors.active(): return false
	var b = interiors.get("cur_bld")
	if typeof(b) != TYPE_DICTIONARY: return false
	var node = b.get("node", null)
	if node == null or not is_instance_valid(node): return false
	return inside(node.global_position)

static func hero_safe(world_pos: Vector3) -> bool:
	if not armed: return true # damage path still refuses; this flag is geometric only when armed
	if town_interior_active(): return true
	return inside(world_pos)

static func is_undead_type(tid: String) -> bool:
	var s := tid.to_lower()
	if s in ["skeleton", "shambler", "runner", "horde_shambler", "horde_runner", "undead_knight", "undead_sailor"]:
		return true
	if s.contains("undead") or s.contains("zombie") or s.contains("shambler") or s.contains("skeleton"):
		return true
	return false

static func is_undead_enemy(e) -> bool:
	if e == null or not is_instance_valid(e): return false
	if e is HordeZombie: return true
	return is_undead_type(str(e.get("type_id")))

static func in_escape_wedge(p: Vector2) -> bool:
	if p.length() < outer_limit() + 3.0: return false
	var ang := rad_to_deg(atan2(p.x, p.y))
	if ang < 0.0: ang += 360.0
	return ang >= WEDGE_A and ang <= WEDGE_B

## Interior cells and the sea sit far from the mainland. Undead do not spawn there.
const WORLD_EDGE := 1500.0

static func far_parking(p: Vector2) -> bool:
	return absf(p.x) > WORLD_EDGE or absf(p.y) > WORLD_EDGE

static func nearest_outside(p: Vector2, body_r: float) -> Vector2:
	if far_parking(p): p = Vector2(0.0, stand_off(body_r) + 12.0)
	var lim := stand_off(body_r)
	var ax := absf(p.x)
	var az := absf(p.y)
	var out := p
	if maxf(ax, az) >= lim and not obstacle_hit(p, body_r): return p
	if ax >= az:
		out.x = signf(p.x if ax > 0.001 else 1.0) * lim
		out.y = clampf(p.y, -lim + 0.05, lim - 0.05)
	else:
		out.y = signf(p.y if az > 0.001 else 1.0) * lim
		out.x = clampf(p.x, -lim + 0.05, lim - 0.05)
	if body_inside(out, body_r):
		out = Vector2(0.0, lim)
	return _nudge_obstacles(out, body_r)

static func sanitize_spawn(pos: Vector3, body_r: float) -> Vector3:
	var out := nearest_outside(Vector2(pos.x, pos.z), body_r)
	return Vector3(out.x, pos.y, out.y)

## Swept move. A long step (low FPS, a shove, a lunge) is walked in short pieces.
## Anything past MAX_SWEEP_M is dropped instead of teleporting through the wall.
static func clamp_move(from: Vector2, to: Vector2, body_r: float) -> Vector2:
	if far_parking(from) or far_parking(to):
		return nearest_outside(from, body_r)
	var delta := to - from
	var dist := delta.length()
	if dist < 1e-6: return nearest_outside(from, body_r)
	if dist > MAX_SWEEP_M:
		to = from + delta * (MAX_SWEEP_M / dist)
		dist = MAX_SWEEP_M
	var steps := int(ceil(dist / SUBSTEP_M))
	steps = clampi(steps, 1, 400)
	var pos := from
	if blocked(pos, body_r): pos = nearest_outside(pos, body_r)
	for i in steps:
		var nxt: Vector2 = from.lerp(to, float(i + 1) / float(steps))
		if blocked(nxt, body_r):
			nxt = _stop_and_slide(pos, nxt, body_r)
		if blocked(nxt, body_r): nxt = pos
		pos = nxt
	return pos

static func _stop_and_slide(from: Vector2, to: Vector2, body_r: float) -> Vector2:
	var lo := 0.0
	var hi := 1.0
	var ok := from
	for _i in 14:
		var mid := (lo + hi) * 0.5
		var p: Vector2 = from.lerp(to, mid)
		if blocked(p, body_r): hi = mid
		else:
			lo = mid
			ok = p
	var rest := to - ok
	if rest.length() < 1e-4: return ok
	var n := _outward_normal(ok)
	var slid := ok + Vector2(-n.y, n.x) * rest.dot(Vector2(-n.y, n.x))
	if blocked(slid, body_r):
		slid = ok
	return slid

static func _outward_normal(p: Vector2) -> Vector2:
	if absf(p.x) > absf(p.y): return Vector2(signf(p.x if absf(p.x) > 0.001 else 1.0), 0.0)
	return Vector2(0.0, signf(p.y if absf(p.y) > 0.001 else 1.0))

static func _nudge_obstacles(p: Vector2, body_r: float) -> Vector2:
	var cur := p
	for _k in 6:
		if not obstacle_hit(cur, body_r): return cur
		var push := Vector2.ZERO
		for r in obstacles:
			var grow := Rect2(r.position - Vector2(body_r, body_r), r.size + Vector2(body_r * 2.0, body_r * 2.0))
			if not grow.has_point(cur): continue
			var c := grow.get_center()
			var away := cur - c
			if away.length() < 0.001: away = _outward_normal(cur)
			push += away.normalized()
		if push.length() < 0.001: push = _outward_normal(cur)
		cur += push.normalized() * 0.35
		if body_inside(cur, body_r): cur = nearest_outside(cur, body_r)
	return cur if not blocked(cur, body_r) else p

## True when the open town square contains any point of the segment.
static func segment_enters(a: Vector2, b: Vector2) -> bool:
	if inside_xz(a.x, a.y) or inside_xz(b.x, b.y): return true
	var lim := outer_limit() - 1e-4
	var t0 := 0.0
	var t1 := 1.0
	var dx := b.x - a.x
	var dz := b.y - a.y
	if not _slab(a.x, dx, -lim, lim, t0, t1): return false
	var span: Array = _slab_span(a.x, dx, -lim, lim, 0.0, 1.0)
	if not span[0]: return false
	span = _slab_span(a.y, dz, -lim, lim, float(span[1]), float(span[2]))
	return span[0]

static func _slab(origin: float, delta: float, lo: float, hi: float, t0: float, t1: float) -> bool:
	return _slab_span(origin, delta, lo, hi, t0, t1)[0]

static func _slab_span(origin: float, delta: float, lo: float, hi: float, t0: float, t1: float) -> Array:
	if absf(delta) < 1e-9:
		if origin <= lo or origin >= hi: return [false, t0, t1]
		return [t0 <= t1, t0, t1]
	var inv := 1.0 / delta
	var ta := (lo - origin) * inv
	var tb := (hi - origin) * inv
	if ta > tb:
		var s := ta
		ta = tb
		tb = s
	t0 = maxf(t0, ta)
	t1 = minf(t1, tb)
	return [t0 <= t1, t0, t1]

## Melee, grab, lunge-connect, and any future segment (ranged) all use this.
## Returns false when the haven is not armed yet, so a load cannot deal damage first.
static func strike_allowed(attacker: Vector3, target: Vector3, kind: String) -> bool:
	if not armed: return false
	if hero_safe(target): return false
	if inside(attacker): return false
	if segment_enters(Vector2(attacker.x, attacker.z), Vector2(target.x, target.z)): return false
	if kind == "": return false
	return true

static func note(ev: Dictionary) -> void:
	if evidence.size() >= EVIDENCE_MAX: return
	ev["n"] = evidence.size()
	evidence.append(ev)
	print("HAVEN_EV %s" % JSON.stringify(ev))

static func write_evidence(path: String) -> bool:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null: return false
	f.store_string(JSON.stringify(evidence, "\t"))
	f.close()
	return true
