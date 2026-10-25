class_name VolcanoTitan
extends Enemy
## Volcano-only Ashen Titan boss, 11x Owner (Beth's ashentitan_volcano_11x.glb, 20.955 m, loaded at scale 1).
## Attacks are driven by the clip events in ashentitan_volcano_11x.json (aoe + spawn_projectile),
## sequences/cooldowns from attackSequenceSuggestion, leash from TITAN_CENTER (bossregions.js).

signal aoe(center: Vector3, radius: float, dmg_mult: float)

const CENTER := Vector3(405, 0, -402)
const BODY_LEASH := 107.0      # titan centre stays within this of CENTER
const CHASE_BREAK := 162.0     # player further than this from CENTER -> go home, keep hurling boulders
var J: Dictionary
var cds := {"eruption_slam": 0.0, "boulder_hurl": 0.0, "magma_sweep": 0.0, "volcano_roar": 0.0}
var seq: Array = []            # [[clip, duration]]
var clip_t := 0.0
var cur_clip := ""
var fired := {}
var projectiles: Array = []    # [{node, vel, dmg, r, life}]
var _proj_scenes := {}

func setup_volcano(ground: Callable) -> VolcanoTitan:
	setup("titan_volcano", CENTER, ground)
	J = JSON.parse_string(FileAccess.get_file_as_string("res://enemies/models/ashentitan_volcano_11x.json"))
	aggro_m = 90.0
	speed_mps = float(J.clips.walk.get("groundSpeedMps", 5.47)) * 0.6
	for k in ["volcanic_boulder", "lava_blob", "ember_rock_small"]:
		_proj_scenes[k] = load("res://enemies/models/%s.glb" % k)
	return self

func reach_m() -> float: return 16.0

func _events(clip: String) -> Array:
	return J.attackEvents.filter(func(e): return e.clip == clip)

func ai_step(dt: float, to: Vector3, d: float) -> void:
	for k in cds: cds[k] = max(0.0, cds[k] - dt)
	_step_projectiles(dt)
	var tp := target.global_position
	var player_from_center := Vector2(tp.x - CENTER.x, tp.z - CENTER.z).length()
	if state == "defeated": return
	if not seq.is_empty():
		_run_seq(dt); return
	var dir: Vector3 = to / maxf(d, 0.001)
	var moving := 0.0
	if state == "idle":
		if d < aggro_m and player_from_center < CHASE_BREAK: set_state("chase")
	elif player_from_center > CHASE_BREAK:
		# leash: walk home, keep throwing boulders while the player is within maxRange
		var h := CENTER - global_position; h.y = 0
		if h.length() > 2.0: position += h.normalized() * speed_mps * dt; moving = 1.0; _face(h.normalized(), dt)
		elif d > 110.0: set_state("idle")
		if d <= 110.0 and cds.boulder_hurl <= 0.0: _start("boulder_hurl")
	else:
		_face(dir, dt)
		var choice := ""
		if d < 14.0 and cds.eruption_slam <= 0.0: choice = "eruption_slam"
		elif d < 30.0 and cds.magma_sweep <= 0.0: choice = "magma_sweep"
		elif cds.volcano_roar <= 0.0 and phase == 2: choice = "volcano_roar"
		elif d > 20.0 and d <= 110.0 and cds.boulder_hurl <= 0.0: choice = "boulder_hurl"
		if choice != "": _start(choice)
		elif d > 12.0:
			var np := global_position + dir * speed_mps * dt
			if Vector2(np.x - CENTER.x, np.z - CENTER.z).length() <= BODY_LEASH: position = np; moving = 1.0
	if height_fn.is_valid(): position.y = height_fn.call(position.x, position.z)
	rig.set_locomotion(moving)

func _start(clip: String) -> void:
	var cd: Dictionary = J.attackSequenceSuggestion.cooldownsSec
	cds[clip] = float(cd.get(clip, 6)) * (0.8 if phase == 2 else 1.0)
	var wind := {"eruption_slam": 1.2, "boulder_hurl": 0.8, "volcano_roar": 1.5}
	seq = []
	if wind.has(clip): seq.append(["windup", wind[clip]])
	seq.append([clip, float(J.clips[clip].durationSec)])
	cur_clip = ""; set_state("attack")

func _run_seq(dt: float) -> void:
	if cur_clip != seq[0][0]:
		cur_clip = seq[0][0]; clip_t = 0.0; fired = {}
		rig.play_attack(cur_clip, 1.0)
		if cur_clip != "windup": attacked.emit(self, {"id": cur_clip, "name": cur_clip.capitalize()})
	clip_t += dt
	var evs := _events(cur_clip)
	for i in evs.size():
		var e: Dictionary = evs[i]
		if not fired.has(i) and clip_t >= float(e.t):
			fired[i] = true; _fire(e)
	if clip_t >= seq[0][1]:
		seq.pop_front(); cur_clip = ""
		if seq.is_empty(): set_state("chase")

func _local(off: Array) -> Vector3:
	# glTF +Z forward; our node faces -Z with the rig rotated PI, so local +Z (gltf) = -Z (node)
	return global_transform * Vector3(-float(off[0]), float(off[1]), -float(off[2]))

func _fire(e: Dictionary) -> void:
	if e.type == "aoe":
		aoe.emit(_local(e.center), float(e.radius), float(e.damageMult))
	elif e.type == "spawn_projectile":
		var origin := _local(e.spawn.offset)
		var n: int = int(e.get("count", 1))
		for i in n:
			var land: Vector3
			if e.get("target", "") == "player":
				land = target.global_position + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)) * float(e.get("spread", 0))
			else:
				var lr: Array = e.get("landRadius", [10, 20])
				var a := (TAU * i / n) if e.get("pattern", "") == "ring" else (rotation.y + PI + deg_to_rad(randf_range(-25, 25)))
				var r := randf_range(lr[0], lr[1])
				land = global_position + Vector3(-sin(a), 0, -cos(a)) * r if e.get("pattern", "") != "ring" else global_position + Vector3(cos(a), 0, sin(a)) * r
			if height_fn.is_valid(): land.y = height_fn.call(land.x, land.z)
			_spawn(e.projectile, float(e.get("projectileScale", 1)), origin, land, float(e.damageMult), float(e.get("impactRadius", 2)))

func _spawn(kind: String, sc: float, from: Vector3, to: Vector3, mult: float, impact_r: float) -> void:
	if projectiles.size() > 40: return     # phone budget
	var node: Node3D = _proj_scenes[kind].instantiate()
	node.scale = Vector3.ONE * sc
	get_parent().add_child(node); node.global_position = from
	var T: float = clamp(Vector2(to.x - from.x, to.z - from.z).length() / 18.0, 1.0, 2.6)
	var g := 9.81
	var v := Vector3((to.x - from.x) / T, (to.y - from.y + 0.5 * g * T * T) / T, (to.z - from.z) / T)
	projectiles.append({"node": node, "vel": v, "mult": mult, "r": impact_r, "life": T})

func _step_projectiles(dt: float) -> void:
	for i in range(projectiles.size() - 1, -1, -1):
		var p: Dictionary = projectiles[i]
		p.vel.y -= 9.81 * dt
		p.node.global_position += p.vel * dt
		p.life -= dt
		if p.life <= 0.0:
			aoe.emit(p.node.global_position, p.r, p.mult)
			p.node.queue_free(); projectiles.remove_at(i)
