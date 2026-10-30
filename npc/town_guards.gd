class_name TownGuards
extends Node3D
## voxel-heroes: Lucian's town_guard_voxel (varn-core dcfc9b2 capes_v1) as NPC guards around town.
## 8 guards (they are ~130k tris each; a lighter LOD is coming): a pair flanking each of the 4 gates on the inside,
## walking a short beat in from the gate and back. In-place walk clip at its 1.04 m/s root speed -> 1x playback, no foot slide.
## Phone budget: AnimationTree frozen beyond 60 m, guard hidden beyond 140 m (and inside interiors with the town).
const MODEL := "res://voxel/town_guard_voxel_lod1.glb"   # test 26 capes_v4: LOD1 (38.6k tris, 28%) for the 8 NPC guards
const HEIGHT := 1.905
const WALK := 1.04
const BEAT := 7.0          # m each way
const INSET := 10.0        # m inside the wall
const ANIM_M := 60.0
const SHOW_M := 140.0
var guards: Array = []     # [{node, rig, a, b, to_b, wait}]
var main: Node

static func spots(city_half: float, gates: Array) -> Array:
	var out := []
	for gd in gates:
		var o := Vector3(gd[0].x, 0, gd[0].y); var along := Vector3(o.z, 0, -o.x)
		for sd in [-1, 1]:
			# flank the gate opening (towers sit at +-13.9 m along the wall), walking a beat in from the gate and back
			var c: Vector3 = o * (city_half - INSET) + along * (sd * 4.5)
			out.append([c + o * BEAT * 0.5, c - o * BEAT * 0.5])
	return out

func setup(m: Node, city_half: float, gates: Array) -> TownGuards:
	main = m; name = "TownGuards"
	var i := 0
	for s in spots(city_half, gates):
		var n := Node3D.new(); n.name = "Guard%d" % i; add_child(n)
		var r := CharacterRig.new().setup(MODEL, HEIGHT)
		r.set_root_speeds(WALK, 6.11, 6.11)
		n.add_child(r)
		var a: Vector3 = s[0]; var b: Vector3 = s[1]
		a.y = _gy(a); b.y = _gy(b)
		n.global_position = a.lerp(b, float(i % 3) / 3.0)
		guards.append({"node": n, "rig": r, "a": a, "b": b, "to_b": i % 2 == 0, "wait": float(i % 4) * 0.8, "on": true})
		i += 1
	return self

func _gy(p: Vector3) -> float:
	if main and main.has_method("ground_y"): return main.ground_y(p.x, p.z)
	if main and main.has_method("height"): return main.height(p.x, p.z)
	return 0.0

func _physics_process(dt: float) -> void:
	var hp: Vector3 = main.hero.global_position if main and main.get("hero") else Vector3.ZERO
	for g in guards:
		var n: Node3D = g.node; var r: CharacterRig = g.rig
		var d := Vector2(n.global_position.x - hp.x, n.global_position.z - hp.z).length()
		n.visible = d < SHOW_M
		var on := d < ANIM_M
		if on != g.on: g.on = on; r.set_active(on)
		if not on: continue
		if g.wait > 0.0:
			g.wait -= dt; r.set_move_mps(0.0); continue
		var goal: Vector3 = g.b if g.to_b else g.a
		var to := goal - n.global_position; to.y = 0
		if to.length() < 0.15:
			g.to_b = not g.to_b; g.wait = 2.5; r.set_move_mps(0.0); continue
		var step: float = minf(WALK * dt, to.length())
		n.global_position += to.normalized() * step
		n.global_position.y = _gy(n.global_position)
		n.rotation.y = lerp_angle(n.rotation.y, atan2(-to.x, -to.z), minf(1.0, dt * 6.0))
		r.set_move_mps(WALK)
