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
var guards: Array = []     # [{node, rig, a, b, to_b, wait, post, hp, tgt, atk_t, down_t}]
## test 31 (boss: "guards should be high level and attack any incoming monsters"): city defence.
## Level 60 guards (town-area monsters are 5-30, frost trolls 45-52). Each guard: 20,000 HP, swings every 1.1 s for 22% of a
## normal monster's max HP (a wolf/raider/skeleton dies in ~5 swings from one guard), 1.5% for bosses (frost trolls).
## Defence zone: the walled square (|x|,|z| <= 185 m) plus 30 m beyond the walls. Up to 3 nearest guards within 90 m answer each
## intruder; they run (6.1 m/s, run clip), attack with the guard attack clip, give up past the zone + 15 m leash, and go
## back to their posts when it is dead or gone. They only ever target Enemy nodes from the EnemyDirector: never players,
## remote players, companions or townsfolk. The Ashen Titans (enemy "titan"/"titan_volcano" and the WorldBoss) are left out.
const LEVEL := 60
const MAX_HP := 20000.0
const DMG_FRAC := 0.22
const BOSS_FRAC := 0.015
const SWING := 1.1
const RUN := 6.11
const ZONE := 30.0          # m beyond the walls
const LEASH := 15.0
const PER_TARGET := 3
const RESPOND := 90.0       # m: only guards this close to an intruder answer it (others hold their gate)
const IGNORE := ["titan", "titan_volcano"]
var city_half := 185.0
var kills := 0
signal guard_hit(e, dmg)
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
	main = m; name = "TownGuards"; self.city_half = city_half
	var i := 0
	for s in spots(city_half, gates):
		var n := Node3D.new(); n.name = "Guard%d" % i; add_child(n)
		var r := CharacterRig.new().setup(MODEL, HEIGHT)
		r.set_root_speeds(WALK, 6.11, 6.11)
		n.add_child(r)
		var a: Vector3 = s[0]; var b: Vector3 = s[1]
		a.y = _gy(a); b.y = _gy(b)
		var post: Vector3 = a.lerp(b, float(i % 3) / 3.0); n.position = post   # (not in the tree yet: plain position)
		guards.append({"node": n, "rig": r, "a": a, "b": b, "to_b": i % 2 == 0, "wait": float(i % 4) * 0.8, "on": true,
				"post": post, "hp": MAX_HP, "tgt": null, "atk_t": 0.0, "down_t": 0.0, "ret": false})
		i += 1
	return self

func _gy(p: Vector3) -> float:
	if main and main.has_method("ground_y"): return main.ground_y(p.x, p.z)
	if main and main.has_method("height"): return main.height(p.x, p.z)
	return 0.0

func in_zone(p: Vector3, pad := 0.0) -> bool: return maxf(absf(p.x), absf(p.z)) <= city_half + ZONE + pad

func hostiles() -> Array:
	var d = main.party.director if main and main.get("party") and main.party.get("director") else null
	if d == null: return []
	return d.living().filter(func(e): return e is Enemy and not (e.type_id in IGNORE) and in_zone(e.global_position))

## assign each intruder to its PER_TARGET nearest free guards
func _assign() -> void:
	for g in guards:
		var t = g.tgt
		if t != null and (not is_instance_valid(t) or not t.alive() or not in_zone(t.global_position, LEASH)): g.tgt = null; g.ret = true
	for e in hostiles():
		var have := guards.filter(func(g): return g.tgt == e).size()
		if have >= PER_TARGET: continue
		var free := guards.filter(func(g): return g.tgt == null and g.down_t <= 0.0 and (g.post as Vector3).distance_to(e.global_position) < RESPOND)
		free.sort_custom(func(a, b): return (a.node as Node3D).global_position.distance_to(e.global_position) < (b.node as Node3D).global_position.distance_to(e.global_position))
		for g in free.slice(0, PER_TARGET - have): g.tgt = e

func _strike(g: Dictionary, e: Enemy) -> void:
	var dmg := int(ceil(e.max_hp * (BOSS_FRAC if e.is_boss() else DMG_FRAC)))
	e.take_damage(dmg, (g.node as Node3D).global_position)
	guard_hit.emit(e, dmg)
	if not e.alive(): kills += 1
	# the monster hits back at whoever is on it (guards are tough: a skeleton needs ~75 hits)
	g.hp -= float(e.def.get("atk", 50)) * 0.3
	if g.hp <= 0.0: g.hp = MAX_HP; g.down_t = 20.0; g.tgt = null; g.ret = true   # knocked out: walks back, rests 20 s

## returns true when the guard is busy defending (skip the patrol)
func _defend(g: Dictionary, dt: float) -> bool:
	var n: Node3D = g.node; var r: CharacterRig = g.rig
	g.atk_t = maxf(0.0, g.atk_t - dt)
	if g.down_t > 0.0: g.down_t -= dt
	var e = g.tgt
	var goal: Vector3
	if e != null: goal = e.global_position; g.ret = true
	elif g.ret and n.global_position.distance_to(g.post) > 0.6: goal = g.post
	else:
		g.ret = false; g.hp = minf(MAX_HP, g.hp + MAX_HP * 0.05 * dt); return false
	var to := goal - n.global_position; to.y = 0
	var reach: float = (e.radius + 1.4) if e != null else 0.3
	n.rotation.y = lerp_angle(n.rotation.y, atan2(-to.x, -to.z), minf(1.0, dt * 8.0))
	if to.length() > reach:
		var step: float = minf(RUN * dt, to.length() - reach * 0.5)
		n.global_position += to.normalized() * step; n.global_position.y = _gy(n.global_position)
		r.set_move_mps(RUN)
	else:
		r.set_move_mps(0.0)
		if e != null and g.atk_t <= 0.0:
			g.atk_t = SWING; r.play_attack("attack", 1.3); _strike(g, e)
	return true

func _physics_process(dt: float) -> void:
	var hp: Vector3 = main.hero.global_position if main and main.get("hero") else Vector3.ZERO
	_assign()
	for g in guards:
		var n: Node3D = g.node; var r: CharacterRig = g.rig
		var d := Vector2(n.global_position.x - hp.x, n.global_position.z - hp.z).length()
		n.visible = d < SHOW_M
		var on := d < ANIM_M or g.tgt != null
		if on != g.on: g.on = on; r.set_active(on)
		if _defend(g, dt): continue
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
