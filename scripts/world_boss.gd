class_name WorldBoss
extends Node3D
## World-boss Ashen Titan TEST (godot-test-worldboss2). Single-player preview, no net sync.
## Roams the main map OUTSIDE the walls on a ring of waypoints (r 330 m, never inside the city), 114 m tall (x5.440).
## Motion: Lucian ac97cb3 (knee fix) wb_walk in place (root stripped), node driven at 2.96 m/s on a smooth outskirts loop. Rituals: Fissure Slam (12 s) and Lava Wave (10 s),
## interrupted by damaging the 6 weak-point crystals. Art: Beth's worldboss kit (assets/volcano/worldboss) + lava veins.

const SCALE := 5.440
## titan-voxel: Lucian's voxel Ashen Titan (varn-core c7ad026 handoff/godot/ashentitan_wb_voxel, LOD0 High/Ultra,
## LOD1 Low/Medium). Its wb_walk (3.0 s cycle) covers ROOT_U model units/s (30.2 m/s at 114 m); the node walks at
## SPEED, so the clip plays at SPEED / (ROOT_U * SCALE) and the planted feet don't slide.
const ROOT_U := 5.60
const WALK_TRIM := 1.04   # wb_walk_check slip m/m: 0.39x +0.154, 0.40x +0.085, 0.41x +0.007, 0.42x -0.054
const VOXEL_BODY := "titan/ashentitan_wb_voxel"
const SPEED := 12.0          # titan-voxel: was 5.2 (old rig). 12 m/s -> wb_walk at 0.39x (7.6 s per stride cycle)
const _OLD_SPEED := 5.2           # test 22 (boss: "walks funny, like he's slow"): was 2.96 m/s, one step per 4-5 s; now ~2x the cadence.
##                             was: Lucian ac97cb3 (timing unchanged from f2ea516): feet hold at 2.96 m/s walk (root motion stripped)
const WALK_RATE := 1.2 * 5.2 / 2.96   # test 22: same foot-plant ratio at the new SPEED (was 1.2 at 2.96 m/s); test 17: wb_walk play rate at SPEED, tuned with tests/wb_lite.tscn (planted-foot slip +0.06 m per m walked; 1.0 gave +0.17, 0.8 +0.43)
const RUN_SPEED := 8.1       # wb_run, root motion stripped
const WB := "res://assets/volcano/worldboss/"
const LAVA := "res://assets/volcano/worldboss/titan/"
const RING_R := 470.0         # worldboss2: outskirts loop (mountains start ~520 m)
const TURN_DEG := 27.5        # titan-voxel: turn circle r = 12 / rad(27.5) ~ 25 m (was 18 deg/s at 5.2 m/s, ~16.5 m)
const _OLD_TURN := 18.0        # test 23: turn circle r = SPEED / rad(TURN_DEG) ~ 16.5 m
const ARRIVE_R := 12.0
const PASS_R := 40.0
const ROUTE_N := 64           # many waypoints -> gentle arcs, no snapping
const STATION_EVERY := 8      # stop (stomp/ritual) only every 8th waypoint
const WEST_LIMIT := -400.0    # coast/port sea is west of x = -440
const MAX_HP := 3000.0
const CRYSTAL_HP := 90.0           # 3 %
const INTERRUPT := 120.0           # 4 % (solo floor of 8% x sqrt(n)/2)
# test 18 (boss: "a way to destroy them without letting others fly"): ground players break the leg crystals
# (ankles: melee, knees: ranged), which drops him into a ~20 s kneel/slump that brings chest/back/forearms down
# within ranged reach. He then rises, his leg crystals regrow, and he resumes the outskirts loop. Nobody needs flight.
const MELEE_R := 12.0              # basic attack reach to a crystal (3D, giant scale)
const RANGED_R := 35.0             # skills/projectiles reach to a crystal (3D, terrain line of sight)
const KNEEL_TIME := 20.0
const KNEEL_RANGED_R := 75.0      # test 19: kneeling upright he is ~114 m tall, so exposed chest/back/forearm crystals (30-66 m up) take ranged hits from 75 m
const KNEEL_BLEND := 1.0           # test 19: seconds to blend into / out of the one-knee pose
const LEGS := ["ankle_L", "ankle_R", "knee_L", "knee_R"]
const ANKLES := {"ankle_L": "foot_L", "ankle_R": "foot_R"}   # extra crystals (Beth's knee crystal art) on the feet
var last_warn := ""
var kneels := 0
const SHAKE_FULL := 120.0
const SHAKE_ZERO := 250.0
const BAR_RANGE := 400.0
var steps: Array = []              # Lucian worldboss_events.json: wb_walk [[t, "L"|"R"], ...]
var sub := ""                      # ritual sub-phase: in / loop / release

var m: Node
var body: Node3D
var ap: AnimationPlayer
var skel: Skeleton3D
var hp := MAX_HP
var waypoints: Array[Vector3] = []
var wp := 0
var state := "walk"
var t_state := 0.0
var ritual := ""
var rituals_done := 0
var pressure := 0
var dmg_window := 0.0
var lava_mat: Material
var hq := true
var crystals: Array = []           # {name, node, hi, lo, mat, hp, broken, t_broken, ground}
var hand_glows: Array[ShaderMaterial] = []
var hand_quads: Array[MeshInstance3D] = []
var crack: MeshInstance3D
var fissures: Array[MeshInstance3D] = []
var wave: Node3D   # Beth pass 3: wb_lava_wave.tscn (wall/crest/skirt/spray/gap posts, wb_lava_wave.gd)
var wave_rng := RandomNumberGenerator.new()
const WAVE_R0 := 80.0
const WAVE_R1 := 170.0
var strip: MeshInstance3D
## test 17 (boss: footprints that fade): glowing scorched print at every foot plant, held 70 s, smooth 15 s fade, max 24
const PRINT_HOLD := 70.0
const PRINT_FADE := 15.0
const PRINT_CAP := 24
var prints_made := 0
var footprints: Array = []         # [node, mat, age]
var dust_scene: PackedScene
var adds: Array = []
var add_t := 20.0
var last_frac := 0.0
var shake_t := 0.0
var shake_amp := 0.0
# UI
var ui: CanvasLayer
var bar: Control
var bar_fill: ColorRect
var bar_txt: Label
var pips: Array[ColorRect] = []
var cast: Control
var cast_fill: TextureRect
var cast_lbl: Label
var cast_icon: TextureRect
var warn: Label

func setup(main: Node) -> WorldBoss:
	m = main
	name = "WorldBoss"
	hq = int(m.get("tier")) >= 2
	_build_route()
	_pick_stations()
	body = (load(WB + VOXEL_BODY + ("" if hq else "_lod1") + ".glb") as PackedScene).instantiate()
	body.scale = Vector3.ONE * SCALE
	add_child(body)
	ap = body.find_children("*", "AnimationPlayer", true, false)[0]
	skel = body.find_children("*", "Skeleton3D", true, false)[0]
	ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL   # test 17: we advance it, then ground the feet on the fresh pose
	_orient_and_measure()
	_build_kneel()
	for c in ["wb_walk", "wb_idle", "wb_ritual_fissure_loop", "wb_ritual_lavawave_loop", "wb_stagger_loop", "wb_down_loop"]:
		if ap.has_animation(c): ap.get_animation(c).loop_mode = Animation.LOOP_LINEAR
	_strip_root_xz("wb_walk")
	if ap.has_animation("wb_run"): _strip_root_xz("wb_run")
	var ev = JSON.parse_string(FileAccess.get_file_as_string(WB + "titan/worldboss_events.json"))
	steps = ev.events.wb_walk
	contact = ev.get("contact", {})   # titan-voxel: Lucian 6578e07 ground-contact frames (slam waves / dust on contact)
	ap.animation_finished.connect(_on_anim_done)
	for mi: MeshInstance3D in body.find_children("*", "MeshInstance3D", true, false):
		mi.extra_cull_margin = 40.0
		for si in mi.mesh.get_surface_count():   # titan-voxel: palette cubes = plain NEAREST, no mip blending (test 25 speckle fix)
			var vm := mi.get_active_material(si)
			if vm is BaseMaterial3D:
				var dm := (vm as BaseMaterial3D).duplicate() as BaseMaterial3D; dm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
				mi.set_surface_override_material(si, dm)
	_veins(); _crystals(); _telegraphs(); _ui(); _ash_fx()
	dust_scene = load(WB + "wb_dust_burst.tscn")
	place_at(0)
	return self

## Smooth outskirts loop: ring r 470 clamped east of the coast, pushed away from farmstead/port/lake/volcano/city,
## then relaxed so the curvature is gentle everywhere.
func _build_route() -> void:
	var avoid := [[Vector2(-290, -288), 120.0], [Vector2(-425.6, 392), 130.0], [Vector2(250, -200), 110.0], [Vector2(405, -402), 120.0], [Vector2(-486, 304), 150.0]]   # test 15: + SW harbor district
	var pts: Array[Vector2] = []
	for i in ROUTE_N:
		var a := i / float(ROUTE_N) * TAU + 0.2
		var p := Vector2(cos(a), sin(a)) * RING_R
		pts.append(p)
	for it in 30:
		for i in ROUTE_N:
			var p := pts[i]
			for b in avoid:
				var d: Vector2 = p - b[0]
				if d.length() < b[1]: p = b[0] + d.normalized() * b[1]
			p.x = maxf(p.x, WEST_LIMIT)
			if maxf(absf(p.x), absf(p.y)) < 300.0: p = p.normalized() * 330.0
			pts[i] = p
		var sm: Array[Vector2] = []
		for i in ROUTE_N:
			sm.append(pts[(i - 1 + ROUTE_N) % ROUTE_N] * 0.25 + pts[i] * 0.5 + pts[(i + 1) % ROUTE_N] * 0.25)
		pts = sm
	for p in pts: waypoints.append(Vector3(p.x, 0, p.y))

## test 24 (boss: "the crystals are hard to get to"): his weak-point crystals are the only crystals in the world and
## players reach them when he stops at a station (stomp/ritual/kneel). Stations used to be every 8th waypoint wherever
## that fell (hills/back slopes). Now each station is the loop point nearest an outskirts road, nudged to sit
## STATION_ROAD_D m beside it (neighbours eased so the loop stays smooth), plus regular fill-ins where the gap is long.
const STATION_ROAD_D := 14.0
const STATION_MAX_SHIFT := 60.0
const STATION_MIN_GAP := 3
const STATION_MAX_GAP := 64   # fill-ins off: every station must be beside a road (gaps over open hills are fine, he keeps walking)
var stations: Array[int] = []
var stations_old: Array[int] = []
var waypoints_old: Array[Vector3] = []   # before the station nudge (test/report only)
func _roads() -> Array:
	var sc: Script = m.get_script() if m else null
	return sc.get_script_constant_map().get("ROADS", []) if sc else []
func _road_near(p: Vector2, roads: Array) -> Vector2:
	var best := Vector2.INF; var bd := 1e9
	for r in roads:
		for i in range(1, r.size()):
			var q := Geometry2D.get_closest_point_to_segment(p, Vector2(r[i-1][0], r[i-1][1]), Vector2(r[i][0], r[i][1]))
			if q.distance_to(p) < bd: bd = q.distance_to(p); best = q
	return best
func _pick_stations() -> void:
	var n := waypoints.size(); waypoints_old = waypoints.duplicate()
	for i in n: if i % STATION_EVERY == 0: stations_old.append(i)
	var roads := _roads()
	if roads.is_empty(): stations = stations_old.duplicate(); return
	var d: Array[float] = []
	for w in waypoints: var p := Vector2(w.x, w.z); d.append(p.distance_to(_road_near(p, roads)))
	var cand := range(n).filter(func(i): return d[i] < STATION_MAX_SHIFT + STATION_ROAD_D and d[i] <= d[(i - 1 + n) % n] and d[i] <= d[(i + 1) % n])
	cand.sort_custom(func(a, b): return d[a] < d[b])
	var gap := func(a: int, b: int) -> int: return mini(absi(a - b), n - absi(a - b))
	for c in cand:
		if stations.all(func(s): return gap.call(s, c) >= STATION_MIN_GAP): stations.append(c)
	stations.sort()
	var fill := true
	while fill:
		fill = false
		for k in stations.size():
			var a := stations[k]; var b := stations[(k + 1) % stations.size()] + (n if k == stations.size() - 1 else 0)
			if b - a > STATION_MAX_GAP: stations.append(((a + b) / 2) % n); stations.sort(); fill = true; break
	if stations.is_empty(): stations = stations_old.duplicate()
	for s in stations:   # nudge beside the road
		var p := Vector2(waypoints[s].x, waypoints[s].z); var q := _road_near(p, roads)
		var dd := p.distance_to(q)
		if dd <= STATION_ROAD_D or dd - STATION_ROAD_D > STATION_MAX_SHIFT: continue
		var np := q + (p - q).normalized() * STATION_ROAD_D
		if maxf(absf(np.x), absf(np.y)) < 300.0 or np.x < WEST_LIMIT: continue
		var sh := np - p
		for o: int in [-2, -1, 0, 1, 2]:
			var j := (s + o + n) % n
			if o != 0 and stations.has(j): continue
			var k: float = [0.25, 0.6, 1.0, 0.6, 0.25][o + 2]
			waypoints[j] += Vector3(sh.x, 0, sh.y) * k

const GLOW_IDLE := 4.5
const GLOW_CAST := 7.5
var embers: Node3D
var scorch: MeshInstance3D
var markers: Array = []          # [Label, crystal]
var env_base := {}

## Beth's body ash/embers: sibling of the Titan (world metres, not under the x5.44 node); follows the chest bone x/z.
func _ash_fx() -> void:
	embers = (load(WB + "wb_body_ash_embers.tscn") as PackedScene).instantiate()
	embers.top_level = true; add_child(embers)
	_ember_ratio(0.5)
	# scorched ground + ash around him (volcanic read on the ritual stretch instead of snowy meadow)
	var sm := ShaderMaterial.new(); sm.shader = load("res://assets/volcano/worldboss/shaders/wb_scorch.gdshader")
	scorch = _plane(sm, Vector3(240, 1, 240)); scorch.visible = true
	for c in crystals:
		var l := Label.new(); l.text = "◆"; l.add_theme_font_size_override("font_size", 30)
		l.add_theme_color_override("font_color", Color(1, 0.62, 0.15)); l.add_theme_constant_override("outline_size", 8)
		l.visible = false; ui.add_child(l); markers.append([l, c])

func _ember_ratio(r: float) -> void:
	# CPUParticles3D has no amount_ratio: scale amount from the authored count (restarts only on state change)
	var ps: Array = embers.find_children("*", "CPUParticles3D", true, false)
	if embers is CPUParticles3D: ps.append(embers)
	for p: CPUParticles3D in ps:
		if not p.has_meta("base"): p.set_meta("base", p.amount)
		var n := maxi(1, int(int(p.get_meta("base")) * r))
		if p.amount != n: p.amount = n

func _lava(param: String, v: float) -> void:
	if lava_mat is ShaderMaterial: (lava_mat as ShaderMaterial).set_shader_parameter(param, v)

func _update_fx(dt: float) -> void:
	var cb := skel.find_bone("chest")
	var cp := (skel.global_transform * skel.get_bone_global_pose(cb)).origin if cb >= 0 else global_position
	embers.global_position = Vector3(cp.x, global_position.y, cp.z)
	if not scorch.has_meta("at") or (scorch.get_meta("at") as Vector3).distance_to(global_position) > 12.0:
		scorch.global_position = Vector3(global_position.x, _gy(global_position.x, global_position.z), global_position.z)
		scorch.set_meta("at", global_position); _drape(scorch, 32, 0.25)
	# fog washes him out: thin the fog and darken/ash the sky near him
	var e := m.get("env") as Environment
	if e:
		if env_base.is_empty(): env_base = {"fd": e.fog_density, "fc": e.fog_light_color, "ae": e.ambient_light_energy, "bg": e.background_energy_multiplier}
		var k := 1.0 - clampf((_hero_d() - 150.0) / 250.0, 0.0, 1.0)
		e.fog_density = lerpf(env_base.fd, env_base.fd * 0.15, k)
		e.fog_light_color = (env_base.fc as Color).lerp(Color(0.22, 0.17, 0.15), k)
		e.background_energy_multiplier = lerpf(env_base.bg, env_base.bg * 0.45, k)
	# weak-point markers beyond ~80 m
	var cam := get_viewport().get_camera_3d()
	for mk in markers:
		var l: Label = mk[0]; var c = mk[1]
		var wpn: Node3D = c.get("node")
		var show: bool = cam != null and wpn != null and crystal_available(c) and visible
		if show:
			var wpos := wpn.global_position
			# test 18 (boss: diamonds seen over hills from across the map): screen-space labels had no depth and no
			# range (shown at >80 m only). Now: close range only, fading 40 -> 60 m, and hidden when terrain blocks the line.
			var d := cam.global_position.distance_to(wpos)
			show = d < MARKER_FAR and not cam.is_position_behind(wpos) and not _terrain_blocks(cam.global_position, wpos)
			if show:
				l.position = cam.unproject_position(wpos) - Vector2(10, 20)
				l.modulate.a = 1.0 - smoothstep(MARKER_NEAR, MARKER_FAR, d)
		l.visible = show

const MARKER_NEAR := 75.0   # test 19: kneeling chest/back sit 58-66 m up, so ground players need ~90 m
const MARKER_FAR := 90.0
func _terrain_blocks(a: Vector3, b: Vector3) -> bool:
	for i in range(1, 16):
		var q := a.lerp(b, i / 16.0)
		if _gy(q.x, q.z) > q.y + 0.3: return true
	return false

func place_at(i: int) -> void:
	wp = i % waypoints.size()
	var p := waypoints[wp]
	position = Vector3(p.x, _gy(p.x, p.z), p.z)
	wp = (wp + 1) % waypoints.size()
	hp = MAX_HP; _set_state("walk")
	for c in crystals: _crystal_restore(c, false)

## owner cheat: put him on the waypoint nearest-but-not-too-near the hero
func spawn_near(hero_pos: Vector3) -> void:
	visible = true
	var best := 0; var bd := 1e9
	for i in waypoints.size():
		var d := absf(waypoints[i].distance_to(Vector3(hero_pos.x, 0, hero_pos.z)) - 180.0)
		if d < bd: bd = d; best = i
	place_at(best)
	_warn("The Titan rises")   # test 19: only on an actual spawn

func _gy(x: float, z: float) -> float:
	return float(m.call("height", x, z)) if m and m.has_method("height") else 0.0

# ---------- art ----------
func _veins() -> void:
	# titan-voxel: the voxel body keeps its own palette + emissive palette (*_vox_emis) material; the old lava shader's
	# UVs belong to the sculpted mesh, so no override. Glow is the material's emission energy.
	for mi: MeshInstance3D in body.find_children("*", "MeshInstance3D", true, false):
		var vm := mi.get_surface_override_material(0)
		if vm: lava_mat = vm; break
	if lava_mat is StandardMaterial3D: (lava_mat as StandardMaterial3D).emission_energy_multiplier = 1.6
	var j = JSON.parse_string(FileAccess.get_file_as_string(LAVA + "titan_drip_points.json"))
	var scene: PackedScene = load(LAVA + "titan_drip_particles.tscn")
	var n := 0
	for p in j.points:
		if not hq and n >= 8: break
		if skel.find_bone(p.bone) < 0: continue
		var ba := BoneAttachment3D.new(); ba.bone_name = p.bone; skel.add_child(ba)
		var at := Node3D.new(); at.position = Vector3(p.offset[0], p.offset[1], p.offset[2]); ba.add_child(at)
		var d: Node3D = scene.instantiate(); at.add_child(d); n += 1
	var ca := BoneAttachment3D.new(); ca.bone_name = "chest"; skel.add_child(ca)
	var l := OmniLight3D.new(); l.light_color = Color(1.0, 0.5, 0.15); l.light_energy = 3.0; l.omni_range = 16.0
	l.shadow_enabled = false; l.position = Vector3(0, 0, 1.2); ca.add_child(l)

func _crystals() -> void:
	var j = JSON.parse_string(FileAccess.get_file_as_string(WB + "attach_points.json"))
	var base_mat: ShaderMaterial = load(WB + "materials/wb_crystal_mat.tres")
	for key in j.points:
		var p: Dictionary = j.points[key]
		if skel.find_bone(p.bone) < 0: push_warning("WB: no bone " + str(p.bone)); continue
		var ba := BoneAttachment3D.new(); ba.name = "WP_" + key; ba.bone_name = p.bone; skel.add_child(ba)
		var q: Array = p.rotation_quat; var o: Array = p.offset
		var nd := Node3D.new(); nd.transform = Transform3D(Basis(Quaternion(q[0], q[1], q[2], q[3])).scaled(Vector3.ONE * float(p.scale)), Vector3(o[0], o[1], o[2]))
		ba.add_child(nd)
		var stem := str(p.crystal).get_basename()
		var c := {"name": key, "node": nd, "stem": stem, "mat": base_mat.duplicate(), "hp": CRYSTAL_HP, "broken": false, "t_broken": 0.0,
			"ground": key.begins_with("forearm") or key.begins_with("knee"), "hi": null, "lo": null}
		_crystal_meshes(c, false)
		crystals.append(c)
	for key in ANKLES:
		if skel.find_bone(ANKLES[key]) < 0: continue
		var ba := BoneAttachment3D.new(); ba.name = "WP_" + key; ba.bone_name = ANKLES[key]; skel.add_child(ba)
		var nd := Node3D.new(); nd.transform = Transform3D(Basis.from_euler(Vector3(-1.2, 0, 0)).scaled(Vector3.ONE * 0.8), Vector3(0, 0.25, 0.35)); ba.add_child(nd)
		var c := {"name": key, "node": nd, "stem": "wb_crystal_knee", "mat": base_mat.duplicate(), "hp": CRYSTAL_HP, "broken": false, "t_broken": 0.0, "ground": true, "hi": null, "lo": null}
		_crystal_meshes(c, false)
		crystals.append(c)

func _crystal_meshes(c: Dictionary, broken: bool) -> void:
	for k in ["hi", "lo"]:
		if c[k]: (c[k] as Node).queue_free(); c[k] = null
	var suf := "_broken" if broken else ""
	var lo: Node3D = (load(WB + c.stem + suf + "_lod1.glb") as PackedScene).instantiate()
	(c.node as Node3D).add_child(lo); c.lo = lo
	var mat: Material = (load(WB + "materials/wb_crystal_broken_mat.tres") as Material).duplicate() if broken else c.mat
	if hq:
		var hi: Node3D = (load(WB + c.stem + suf + ".glb") as PackedScene).instantiate()
		(c.node as Node3D).add_child(hi); c.hi = hi
		for mi: MeshInstance3D in hi.find_children("*", "MeshInstance3D", true, false):
			mi.visibility_range_end = 120.0; mi.set_surface_override_material(0, mat)
		for mi: MeshInstance3D in lo.find_children("*", "MeshInstance3D", true, false):
			mi.visibility_range_begin = 120.0
	for mi: MeshInstance3D in lo.find_children("*", "MeshInstance3D", true, false):
		mi.set_surface_override_material(0, mat)

func _crystal_restore(c: Dictionary, tween := true) -> void:
	if c.broken: _crystal_meshes(c, false)
	c.broken = false; c.hp = CRYSTAL_HP
	var mat: ShaderMaterial = c.mat
	mat.set_shader_parameter("broken", 0.0)
	if tween and is_inside_tree():
		mat.set_shader_parameter("glow", 0.0)
		create_tween().tween_method(func(v): mat.set_shader_parameter("glow", v), 0.0, 1.0, 1.5)
	else: mat.set_shader_parameter("glow", 1.0)

func _crystal_glow(g: float) -> void:
	for c in crystals:
		if not c.broken: (c.mat as ShaderMaterial).set_shader_parameter("glow", g)

func _plane(mat: Material, sz: Vector3) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2.ONE; mi.mesh = pm
	mi.material_override = mat; mi.scale = sz; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.top_level = true; mi.visible = false; add_child(mi); return mi

func _telegraphs() -> void:
	crack = _plane((load(WB + "materials/wb_crack_radial_mat.tres") as Material).duplicate(), Vector3(120, 1, 120))
	for i in 3: fissures.append(_plane((load(WB + "materials/wb_crack_fissure_mat.tres") as Material).duplicate(), Vector3(12, 1, 60)))
	strip = _plane((load(WB + "materials/wb_lava_strip_mat.tres") as Material).duplicate(), Vector3(170, 1, 170))
	wave = (load(WB + "wb_lava_wave.tscn") as PackedScene).instantiate()
	wave.height_provider = func(w: Vector3) -> float: return _gy(w.x, w.z)   # v3.2: heightmap terrain, no raycasts
	wave.top_level = true; wave.visible = false; add_child(wave)
	var gm: Material = load(WB + "materials/wb_hand_glow_mat.tres")
	for b in ["hand_L", "hand_R", "upperChest"]:
		if skel.find_bone(b) < 0: continue
		var ba := BoneAttachment3D.new(); ba.bone_name = b; skel.add_child(ba)
		var q := MeshInstance3D.new(); var qm := QuadMesh.new(); qm.size = Vector2.ONE * 3.5; q.mesh = qm
		var mm: ShaderMaterial = gm.duplicate(); q.material_override = mm; q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		ba.add_child(q); hand_glows.append(mm); hand_quads.append(q); q.visible = false
		q.set_meta("chest", b == "upperChest")

func _set_glow_charge(v: float, chest := false) -> void:
	for i in hand_glows.size():
		var is_chest := i == hand_glows.size() - 1
		var c := v if is_chest == chest else 0.0
		hand_glows[i].set_shader_parameter("charge", c)
		hand_quads[i].visible = c > 0.01

# ---------- UI ----------
func _ui() -> void:
	ui = CanvasLayer.new(); ui.layer = 5; add_child(ui)
	bar = Control.new(); bar.set_anchors_preset(Control.PRESET_CENTER_TOP); bar.visible = false; ui.add_child(bar)
	var r := Control.new(); r.position = Vector2(-330, 10); bar.add_child(r)
	var nm := Label.new(); nm.text = "WORLD BOSS · ASHEN TITAN"; nm.add_theme_font_size_override("font_size", 20)
	nm.add_theme_color_override("font_color", Color(1, 0.7, 0.35)); nm.add_theme_constant_override("outline_size", 6); r.add_child(nm)
	var bg := ColorRect.new(); bg.color = Color(0.08, 0.03, 0.02, 0.9); bg.position = Vector2(0, 30); bg.size = Vector2(660, 22); r.add_child(bg)
	bar_fill = ColorRect.new(); bar_fill.color = Color(0.95, 0.3, 0.06); bar_fill.position = Vector2(2, 32); bar_fill.size = Vector2(656, 18); r.add_child(bar_fill)
	bar_txt = Label.new(); bar_txt.position = Vector2(0, 54); bar_txt.add_theme_font_size_override("font_size", 14)
	bar_txt.add_theme_constant_override("outline_size", 5); r.add_child(bar_txt)
	for i in crystals.size():   # test 18: 8 weak points (2 ankles added)
		var pp := ColorRect.new(); pp.size = Vector2(14, 14); pp.position = Vector2(530 + i * 20, 56); pp.color = Color(1, 0.6, 0.2); r.add_child(pp); pips.append(pp)
	cast = Control.new(); cast.set_anchors_preset(Control.PRESET_CENTER); cast.visible = false; ui.add_child(cast)
	var cr := Control.new(); cr.position = Vector2(-260, 120); cast.add_child(cr)
	var frame := NinePatchRect.new(); frame.texture = load(WB + "tex/wb_castbar_frame.png")
	for s in [SIDE_LEFT, SIDE_RIGHT, SIDE_TOP, SIDE_BOTTOM]: frame.set_patch_margin(s, 48)
	frame.size = Vector2(520, 64); frame.position = Vector2(0, 0); cr.add_child(frame)
	cast_fill = TextureRect.new(); cast_fill.texture = load(WB + "tex/wb_castbar_fill.png"); cast_fill.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	cast_fill.stretch_mode = TextureRect.STRETCH_SCALE; cast_fill.position = Vector2(18, 18); cast_fill.size = Vector2(484, 28); cr.add_child(cast_fill)
	cast_icon = TextureRect.new(); cast_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; cast_icon.size = Vector2(72, 72); cast_icon.position = Vector2(-82, -4); cr.add_child(cast_icon)
	cast_lbl = Label.new(); cast_lbl.position = Vector2(0, -30); cast_lbl.add_theme_font_size_override("font_size", 20)
	cast_lbl.add_theme_constant_override("outline_size", 6); cast_lbl.add_theme_color_override("font_color", Color(1, 0.8, 0.4)); cr.add_child(cast_lbl)
	warn = Label.new(); warn.set_anchors_preset(Control.PRESET_CENTER); warn.position = Vector2(-400, -60); warn.size = Vector2(800, 60)
	warn.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; warn.add_theme_font_size_override("font_size", 34)
	warn.add_theme_color_override("font_color", Color(1, 0.35, 0.1)); warn.add_theme_constant_override("outline_size", 10); warn.visible = false; ui.add_child(warn)

## test 32: no mainland world-boss popups/cast bar while the player is out in the Tidewrack Sea
func _at_sea() -> bool:
	var sc := get_tree().current_scene
	var s = sc.get("sea") if sc else null
	return s != null and bool(s.active)
func _warn(t: String) -> void:
	last_warn = t
	if _at_sea(): return
	warn.text = t; warn.visible = true; warn.modulate.a = 1.0
	var tw := create_tween(); tw.tween_interval(2.0); tw.tween_property(warn, "modulate:a", 0.0, 0.6); tw.tween_callback(func(): warn.visible = false)

# ---------- loop ----------
func _set_state(s: String) -> void:
	state = s; t_state = 0.0
	_lava("stagger_dim", 1.0 if s in ["stagger", "knockdown", "kneel"] else 0.0)
	if s != "windup": _lava("glow_strength", GLOW_IDLE)
	if embers: _ember_ratio(1.0 if s in ["windup", "release"] else 0.5)
	match s:
		"walk": _play("wb_walk")
		"arrive": _play("wb_stomp")
		"idle", "cool": _play("wb_idle"); _crystal_glow(1.0)
		"windup": sub = "in"; _play("wb_ritual_%s_in" % _rid())
		"release": _play("wb_ritual_%s_release" % _rid())
		"stagger": _play("wb_stagger")
		"knockdown": _play("wb_knockdown")
		"kneel": if ap.has_animation("wb_kneel"): ap.play("wb_kneel", KNEEL_BLEND); ap.speed_scale = 1.0

func _rid() -> String: return "fissure" if ritual == "fissure" else "lavawave"

func _on_anim_done(a: StringName) -> void:
	match String(a):
		"wb_stomp": if state == "arrive": _set_state("idle")
		"wb_ritual_fissure_in", "wb_ritual_lavawave_in": if state == "windup": sub = "loop"; _play("wb_ritual_%s_loop" % _rid())
		"wb_stagger": if state == "stagger": _play("wb_stagger_loop")
		"wb_knockdown": if state in ["knockdown", "kneel"]: _play("wb_down")
		"wb_getup": if state == "knockdown":
			for c in crystals: _crystal_restore(c)   # full cycle done: all weak points regrow
			_set_state("cool")

func _strip_root_xz(c: String) -> void:
	if not ap.has_animation(c): return
	var a := ap.get_animation(c)
	for t in a.get_track_count():
		if a.track_get_type(t) == Animation.TYPE_POSITION_3D and str(a.track_get_path(t)).ends_with(":root"):
			var p0: Vector3 = a.track_get_key_value(t, 0)
			for k in a.track_get_key_count(t):
				var v: Vector3 = a.track_get_key_value(t, k); a.track_set_key_value(t, k, Vector3(p0.x, v.y, p0.z))

func _play(c: String, _sp := 1.0) -> void:
	if ap.has_animation(c): ap.play(c, 0.5); ap.speed_scale = 1.0
	else: push_warning("WB: missing clip " + c)

func _hero() -> Node3D: return m.get("hero") as Node3D
func _hero_d() -> float:
	var h := _hero(); return h.global_position.distance_to(global_position) if h else 1e9

func _process(dt: float) -> void:
	if ui: ui.visible = not _at_sea()
	if not visible: return
	t_state += dt
	match state:
		"walk": _walk(dt)
		"idle":
			if t_state > 6.0: _start_ritual()
		"windup": _windup(dt)
		"arrive":
			if t_state - dt < _ct("wb_stomp", 2.4) and t_state >= _ct("wb_stomp", 2.4): _stomp(1.0, true)
		"release":
			var hit_t := _ct("wb_ritual_fissure_release", 0.9) if ritual == "fissure" else _ct("wb_ritual_lavawave_release", 1.3)
			if t_state - dt < hit_t and t_state >= hit_t: _complete()
			if t_state > 4.0: _end_ritual_fx(); _set_state("cool")
		"stagger":
			if t_state > 8.0: _play("wb_idle"); _set_state("cool")
		"knockdown":
			if t_state - dt < _ct("wb_knockdown", 2.4) and t_state >= _ct("wb_knockdown", 2.4): _stomp(0.8, true)
			if t_state > 22.0 and ap.current_animation != "wb_getup": _play("wb_getup")
		"kneel": _kneel(dt)
		"cool":
			if t_state > 10.0: _set_state("walk")
	if _rate_pending and is_inside_tree():
		_rate_pending = false; _clip_rate("wb_walk", SPEED)   # clip_speed kept for the report
		walk_rate = SPEED / (ROOT_U * SCALE) * WALK_TRIM   # titan-voxel: authored root speed (0.394x), trimmed on the slip check
		if OS.get_environment("WB_RATE") != "": walk_rate = float(OS.get_environment("WB_RATE"))
	_ik_restore()
	ap.advance(dt)
	if state == "walk" and ap.current_animation == "wb_walk" and OS.get_environment("WB_NOIK") == "": _straight_legs(dt)   # test 22
	_ground_feet(dt)
	_update_crystals(dt); _update_prints(dt); _update_adds(dt); _update_ui(); _update_fx(dt); _do_shake(dt)

func _kneel(dt: float) -> void:
	if t_state - dt < KNEEL_TIME and t_state >= KNEEL_TIME: ap.play("wb_idle", KNEEL_BLEND)   # stand back up (1 s blend)
	if t_state > KNEEL_TIME + KNEEL_BLEND + 0.5:
		for c in crystals: if c.name in LEGS and c.broken: _crystal_restore(c)   # legs regrow: repeat the cycle
		_set_state("cool")

var contact := {}
func _ct(clip: String, dflt: float) -> float: return float(contact.get(clip, dflt))

func leg_crystals_up() -> bool:
	for c in crystals: if c.name in LEGS and not c.broken: return true
	return false

## where a crystal is hittable from: available = legs any time, everything else only while he is down
func crystal_available(c: Dictionary) -> bool:
	return not c.broken and (c.name in LEGS or state in ["kneel", "knockdown"])

func _walk(dt: float) -> void:
	var tgt := waypoints[wp]
	var flat := Vector3(tgt.x - position.x, 0, tgt.z - position.z)
	# test 23 (boss: "walks in a small circle"): at test 22's 5.2 m/s the old 6 deg/s turn gave a ~50 m turn circle,
	# wider than the 25 m arrival radius, so he orbited a waypoint forever. Now: turn rate sized to SPEED (~16 m circle),
	# and a waypoint also counts as reached once it is behind him (passed), so he can never orbit one.
	var fwd0 := _fwd()
	if flat.length() < ARRIVE_R or (flat.length() < PASS_R and fwd0.dot(flat) < 0.0):
		var station := stations.has(wp)
		wp = (wp + 1) % waypoints.size()
		if station: _set_state("arrive"); return
		tgt = waypoints[wp]; flat = Vector3(tgt.x - position.x, 0, tgt.z - position.z)
	var want := atan2(-flat.x, -flat.z)         # Lucian's rig faces -Z
	rotation.y = rotate_toward(rotation.y, want, deg_to_rad(TURN_DEG) * dt)
	var fwd := _fwd()
	var np := position + fwd * SPEED * dt
	if maxf(absf(np.x), absf(np.z)) < 260.0:   # hard rule: never enters the town (test 23: slide along the edge instead of freezing)
		var out := Vector2(np.x, np.z).normalized() * 260.5; np = Vector3(out.x, np.y, out.y)
	position = Vector3(np.x, _gy(np.x, np.z) + ground_off, np.z)
	if ap.current_animation == "wb_walk": ap.speed_scale = walk_rate   # test 17: clip cadence matched to SPEED (no foot slide)
	# footfalls from the clip phase
	if ap.current_animation != "wb_walk": return
	var f := ap.current_animation_position
	for e in steps:
		var s: float = e[0]
		if (last_frac < s and f >= s) or (f < last_frac and (s > last_frac or s <= f)): _footfall(0 if e[1] == "L" else 1)
	last_frac = f

func _fwd() -> Vector3: return -Vector3(sin(rotation.y), 0, cos(rotation.y))

func _footfall(i: int) -> void:
	var b := skel.find_bone(["foot_L", "foot_R"][i])
	var p := (skel.global_transform * skel.get_bone_global_pose(b)).origin
	await get_tree().create_timer(0.1).timeout
	_print_at(p); _stomp(0.45, false, p, false)   # test 22: heavier footfall shake near the player (full within 120 m)

func _print_at(p: Vector3) -> void:
	var mat: ShaderMaterial = (load(WB + "materials/wb_footprint_mat.tres") as Material).duplicate()
	var fp := _plane(mat, Vector3(48, 1, 48)); fp.visible = true
	fp.global_position = Vector3(p.x, _gy(p.x, p.z) + 0.4, p.z); fp.rotation.y = rotation.y + PI   # plane toes = +Z, Titan faces -Z
	_drape(fp, 8, 0.35)
	footprints.append([fp, mat, 0.0]); prints_made += 1
	while footprints.size() > PRINT_CAP: (footprints.pop_front()[0] as Node).queue_free()

func _stomp(amp: float, arrive: bool, at := Vector3.INF, delay := true) -> void:
	if at == Vector3.INF: at = global_position
	if delay: await get_tree().create_timer(0.1).timeout   # contact + 0.1 s: dust, print and shake together
	var d: Node3D = dust_scene.instantiate(); d.top_level = true; add_child(d)
	d.global_position = Vector3(at.x, _gy(at.x, at.z) + 0.3, at.z)
	if arrive: d.scale = Vector3.ONE * 2.0
	for p in d.find_children("*", "CPUParticles3D", true, true) + ([d] if d is CPUParticles3D else []): (p as CPUParticles3D).restart()
	get_tree().create_timer(4.0).timeout.connect(d.queue_free)
	shake(amp, 1.2)

## distance-gated camera shake: full within 120 m, linear to 0 at 250 m
func shake(amp: float, sec: float) -> void:
	var k := 1.0 - clampf((_hero_d() - SHAKE_FULL) / (SHAKE_ZERO - SHAKE_FULL), 0.0, 1.0)
	if k <= 0.0: return
	shake_amp = maxf(shake_amp if shake_t > 0.0 else 0.0, amp * k); shake_t = maxf(shake_t, sec)

func _do_shake(dt: float) -> void:
	var cam := m.get("cam") as Camera3D
	if cam == null: return
	if shake_t > 0.0:
		shake_t -= dt
		var a := shake_amp * clampf(shake_t / 1.2, 0.0, 1.0)   # linear fade over 1.2 s
		cam.h_offset = randf_range(-1, 1) * a; cam.v_offset = randf_range(-1, 1) * a
		if shake_t <= 0.0: cam.h_offset = 0.0; cam.v_offset = 0.0

func _start_ritual() -> void:
	ritual = "fissure" if rituals_done % 2 == 0 else "wave"
	dmg_window = 0.0
	_set_state("windup"); _crystal_glow(2.0)
	var fwd := _fwd()
	if ritual == "fissure":
		cast_icon.texture = load(WB + "tex/wb_icon_fissure_slam.png"); cast_lbl.text = "FISSURE SLAM"
		_ground(crack, global_position + fwd * 6.0, rotation.y)
		for i in 3:
			var yw := rotation.y + PI + deg_to_rad([-40.0, 0.0, 40.0][i])
			var d := Vector3(sin(yw), 0, cos(yw))
			_ground(fissures[i], global_position + d * 30.0, yw)
		_warn("The Titan gathers fire: FISSURE SLAM")
	else:
		cast_icon.texture = load(WB + "tex/wb_icon_lava_wave.png"); cast_lbl.text = "LAVA WAVE"
		wave.visible = true; wave.scale = Vector3.ONE
		wave.global_position = Vector3(global_position.x, _gy(global_position.x, global_position.z), global_position.z)
		wave.gap_count = 3 if wave_rng.randi() % 2 == 0 else 4; wave.randomize_gaps(wave_rng)   # new safe openings every cast
		wave.rise = 0.0; wave.sample_ground()   # v3.2: wall/crest/skirt/posts follow the hills
		_warn("The Titan's core blazes: LAVA WAVE")

## Lava Wave wall: open cylinder whose base follows the terrain at every angle (was a flat cylinder that cut through
## hills and hung in the air over valleys). Rebuilt while it grows. UV like CylinderMesh (v: 0 top -> 1 bottom).
func _drape_wave() -> void:
	# Wall (unit cylinder, node scale 80/24/80 at y 12) and Skirt (2x2 plane, scale 80) rebuilt so their base follows the
	# terrain at the current expansion radius. Local XZ stays on the unit circle so the gap shaders (atan of local xz) still line up.
	var c := wave.global_position; var R := WAVE_R0 * wave.scale.x; var n := 64
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in n + 1:
		var a := i / float(n) * TAU; var d := Vector3(sin(a), 0, cos(a))
		var w := c + d * R; var yb := (_gy(w.x, w.z) - 1.0 - c.y - 12.0) / 24.0
		for t in 2:
			st.set_uv(Vector2(i / float(n), 1.0 - t)); st.set_normal(d); st.add_vertex(Vector3(d.x, yb + t, d.z))
	for i in n:
		var a := i * 2
		for k in [a, a + 1, a + 2, a + 1, a + 3, a + 2]: st.add_index(k)
	(wave.get_node("Wall") as MeshInstance3D).mesh = st.commit()
	var g := 16; var sk := SurfaceTool.new(); sk.begin(Mesh.PRIMITIVE_TRIANGLES)
	for j in g + 1:
		for i in g + 1:
			var u := i / float(g); var v := j / float(g)
			var lx := u * 2.0 - 1.0; var lz := v * 2.0 - 1.0
			var wx := c.x + lx * R; var wz := c.z + lz * R
			sk.set_uv(Vector2(u, v)); sk.set_normal(Vector3.UP); sk.add_vertex(Vector3(lx, _gy(wx, wz) + 0.3 - c.y, lz))
	for j in g:
		for i in g:
			var a := j * (g + 1) + i
			for k in [a, a + 1, a + g + 1, a + 1, a + g + 2, a + g + 1]: sk.add_index(k)
	(wave.get_node("Skirt") as MeshInstance3D).mesh = sk.commit()

func _ground(mi: MeshInstance3D, p: Vector3, yaw: float) -> void:
	mi.visible = true; mi.global_position = Vector3(p.x, _gy(p.x, p.z) + 0.5, p.z); mi.rotation = Vector3(0, yaw, 0)
	_drape(mi)

## worldboss2: flat decal planes floated over / sank under the hilly outskirts (the "crack/ring in the sky" bug).
## Rebuild the unit plane as a grid whose vertices follow the terrain (UVs unchanged), lift `lift` m.
func _drape(mi: MeshInstance3D, n := 24, lift := 0.6) -> void:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var xf := mi.global_transform; var y0 := xf.origin.y; var sy := maxf(mi.scale.y, 0.001)
	for j in n + 1:
		for i in n + 1:
			var u := i / float(n); var v := j / float(n)
			var lp := Vector3(u - 0.5, 0, v - 0.5)
			var w := xf * lp
			lp.y = (_gy(w.x, w.z) + lift - y0) / sy
			st.set_uv(Vector2(u, v)); st.set_normal(Vector3.UP); st.add_vertex(lp)
	for j in n:
		for i in n:
			var a := j * (n + 1) + i
			for k in [a, a + 1, a + n + 1, a + 1, a + n + 2, a + n + 1]: st.add_index(k)
	mi.mesh = st.commit()
	var sm := mi.material_override as ShaderMaterial
	for k in ["progress", "erupt", "rise"]: sm.set_shader_parameter(k, 0.0)

func _wind_len() -> float: return 12.0 if ritual == "fissure" else 10.0

func _windup(_dt: float) -> void:
	var k := clampf(t_state / _wind_len(), 0.0, 1.0)
	_set_glow_charge(k, ritual == "wave")
	_lava("glow_strength", lerpf(GLOW_IDLE, GLOW_CAST, k))
	if ritual == "fissure":
		(crack.material_override as ShaderMaterial).set_shader_parameter("progress", k)
		for f in fissures: (f.material_override as ShaderMaterial).set_shader_parameter("progress", k)
	else:
		wave.rise = k
	if t_state - _dt < _wind_len() - 3.0 and t_state >= _wind_len() - 3.0: _warn("3 SECONDS! Break his crystals!")
	if dmg_window >= INTERRUPT:
		_warn("INTERRUPTED! The Titan staggers"); _end_ritual_fx(); _set_glow_charge(0.0); _set_state("stagger"); return
	if t_state >= _wind_len(): _set_glow_charge(0.0); _set_state("release")

func _complete() -> void:
	rituals_done += 1; pressure += 1
	_set_glow_charge(0.0)
	var h := _hero()
	var hit := false
	if ritual == "fissure":
		(crack.material_override as ShaderMaterial).set_shader_parameter("erupt", 1.0)
		for f in fissures: (f.material_override as ShaderMaterial).set_shader_parameter("erupt", 1.0)
		if h and Vector2(h.global_position.x - crack.global_position.x, h.global_position.z - crack.global_position.z).length() < 60.0: hit = true
		_stomp(1.0, true, crack.global_position); _warn("FISSURE SLAM!")
	else:
		var g := WAVE_R1 / WAVE_R0
		create_tween().tween_property(wave, "scale", Vector3(g, 1.0, g), 3.0)
		# skip damage for a hero standing in one of the safe gaps (angle-only test, valid while it expands)
		if h and _hero_d() < WAVE_R1 and not bool(m.get("cheat").get("fly", false)) and not wave.is_in_gap(h.global_position): hit = true
		_stomp(0.8, true); _warn("LAVA WAVE!")
	if pressure >= 3: pressure = 0; _warn("VOLCANO PRESSURE PEAKS - lava bombs rain on the region")
	var party = m.get("party")
	if hit and party and party.combat and not bool(m.get("cheat").get("god", false)):
		var c = party.combat
		c.titan_hit(HeroCombat.TITAN_HIT)   # test 26: was 40-50% of max HP per slam/wave

func _end_ritual_fx() -> void:
	for mi in [crack, strip] + fissures:
		var sm := (mi as MeshInstance3D).material_override as ShaderMaterial
		var tw := create_tween(); tw.tween_method(func(v): sm.set_shader_parameter("progress", v), 1.0, 0.0, 1.5)
		tw.tween_callback(func(): (mi as MeshInstance3D).visible = false)
	wave.visible = false

# ---------- damage (hooked to HeroCombat.used) ----------
func on_hero_used(slot: int, _sk: Dictionary, hero_id := "") -> void:
	if not visible: return
	var h := _hero(); if h == null: return
	# test 25: the Owner's ultimates (Unholy + Holy Destruction) kill the Titan in one hit when it lands
	# (a crystal in reach, or the Titan's body within the ult radius / 45 m, whichever is larger)
	if slot > 0 and HeroCombat.one_shot(hero_id, _sk) and state != "dead":
		var R := maxf(45.0, float(CombatData.data().TUNING.ult.radius) * CombatRules.UNIT_M)
		var hp2 := Vector2(h.global_position.x - global_position.x, h.global_position.z - global_position.z).length()
		var near_c := false
		for c in crystals:
			if crystal_available(c) and h.global_position.distance_to((c.node as Node3D).global_position) < KNEEL_RANGED_R: near_c = true
		if hp2 < R or near_c: _damage(hp + 1.0); return
	hit_from(h.global_position + Vector3(0, 1.5, 0), slot)

## test 18: slot 0 = basic melee (MELEE_R), skills = ranged/projectile (RANGED_R + terrain line of sight). Returns the crystal hit.
func hit_from(eye: Vector3, slot: int):
	var dmg := 10.0 if slot == 0 else 25.0
	var best = null; var bd := 1e9
	for c in crystals:
		if not crystal_available(c): continue
		var reach := MELEE_R if slot == 0 else (KNEEL_RANGED_R if not (c.name in LEGS) else RANGED_R)
		var cp: Vector3 = (c.node as Node3D).global_position
		var d3 := eye.distance_to(cp)
		if d3 < reach and d3 < bd and (slot == 0 or not _terrain_blocks(eye, cp)): bd = d3; best = c
	if best: _hit_crystal(best, dmg)
	elif Vector2(eye.x - global_position.x, eye.z - global_position.z).length() < 45.0: _damage(dmg * 0.1)
	return best

func _hit_crystal(c: Dictionary, dmg: float) -> void:
	var mult := 3.0 if state == "knockdown" else (2.0 if state == "stagger" else 1.0)
	c.hp -= dmg * mult
	_damage(dmg * mult)
	if state == "windup": dmg_window += dmg * mult
	var mat: ShaderMaterial = c.mat
	mat.set_shader_parameter("hit_flash", 1.0)
	create_tween().tween_method(func(v): mat.set_shader_parameter("hit_flash", v), 1.0, 0.0, 0.15)
	if c.hp <= 0.0:
		c.broken = true; c.t_broken = 0.0; _crystal_meshes(c, true); _spawn_adds(c.node.global_position)
		if crystals.all(func(x): return x.broken): _warn("ALL WEAK POINTS BROKEN - KNOCKDOWN"); _end_ritual_fx(); _set_glow_charge(0.0); _set_state("knockdown")
		elif state != "kneel" and state != "knockdown" and not leg_crystals_up():
			kneels += 1; _warn("The Titan staggers!"); _end_ritual_fx(); _set_glow_charge(0.0); _set_state("kneel")

func _damage(v: float) -> void:
	hp = maxf(0.0, hp - v)
	if hp <= 0.0:
		_warn("THE ASHEN TITAN FALLS"); _play("death"); state = "dead"
		get_tree().create_timer(20.0).timeout.connect(func(): place_at(wp))

func _update_crystals(dt: float) -> void:
	for c in crystals:
		if c.broken:
			c.t_broken += dt
			if c.t_broken > 60.0 and state == "dead": _crystal_restore(c)

# ---------- adds (static blockouts: fiend unrigged, wisp bobs) ----------
func _spawn_adds(at: Vector3) -> void:
	var live := adds.filter(func(a): return is_instance_valid(a[0]))
	adds = live
	for i in 5:
		if adds.size() >= 12: break
		var wisp := i >= 3
		var n: Node3D = (load(WB + ("wb_ember_wisp" if wisp else "wb_ash_fiend") + ("_lod1.glb")) as PackedScene).instantiate()
		var mat: Material = load(WB + "materials/" + ("wb_wisp_mat.tres" if wisp else "wb_fiend_mat.tres"))
		for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false): mi.material_override = mat
		n.top_level = true; add_child(n)
		var a := randf() * TAU; var r := randf_range(8.0, 18.0)
		var p := Vector3(at.x + cos(a) * r, 0, at.z + sin(a) * r)
		n.global_position = Vector3(p.x, _gy(p.x, p.z) + (2.0 if wisp else 0.0), p.z)
		var h := _hero(); if h: n.rotation.y = atan2(h.global_position.x - p.x, h.global_position.z - p.z)
		adds.append([n, wisp, 0.0, n.global_position.y])

func _update_adds(dt: float) -> void:
	if state != "walk" and _hero_d() < 200.0:
		add_t -= dt
		if add_t <= 0.0: add_t = 45.0; _spawn_adds(global_position + _fwd() * 50.0)
	for a in adds:
		if not is_instance_valid(a[0]): continue
		a[2] += dt
		if a[1]: (a[0] as Node3D).global_position.y = a[3] + sin(a[2] * 2.0) * 0.4; (a[0] as Node3D).rotation.y += dt * 0.6
		if a[2] > 90.0: (a[0] as Node).queue_free()

func _update_prints(dt: float) -> void:
	for f in footprints:
		f[2] += dt
		var mat: ShaderMaterial = f[1]
		mat.set_shader_parameter("heat", clampf(1.0 - f[2] / 10.0, 0.0, 1.0))
		mat.set_shader_parameter("fade", clampf(1.0 - (f[2] - PRINT_HOLD) / PRINT_FADE, 0.0, 1.0))
	while footprints.size() > 0 and footprints[0][2] > PRINT_HOLD + PRINT_FADE: (footprints.pop_front()[0] as Node).queue_free()

func _update_ui() -> void:
	var near := _hero_d() < BAR_RANGE
	bar.visible = near
	if near:
		bar_fill.size.x = 656.0 * hp / MAX_HP
		bar_txt.text = "%d / %d    Volcano pressure %d/3    weak points" % [hp, MAX_HP, pressure]
		for i in mini(pips.size(), crystals.size()): pips[i].color = Color(0.2, 0.15, 0.12) if crystals[i].broken else Color(1, 0.6, 0.2)
	cast.visible = near and state == "windup"
	if cast.visible:
		var k := clampf(t_state / _wind_len(), 0.0, 1.0)
		cast_fill.size.x = 484.0 * k
		cast_lbl.text = "%s   %.1fs   interrupt %d%%" % ["FISSURE SLAM" if ritual == "fissure" else "LAVA WAVE", _wind_len() - t_state, int(100.0 * dmg_window / INTERRUPT)]


# ---------- test 17 (boss: world boss floats / moon-walks backwards) ----------
var ground_off := 0.0        # node y relative to the terrain under his origin, so the lowest sole touches the ground
var sole_clear := 0.0        # rest-pose height of the toe bones above the soles (world metres at SCALE)
var walk_rate := 1.0         # AnimationPlayer speed for wb_walk so stance feet stay planted at SPEED
var foot_gap := 0.0          # last measured lowest-sole-to-terrain gap (m), for the check
const FEET := ["toe_L", "toe_R", "foot_L", "foot_R"]

## The node moves along -Z (_fwd). Find which way the rig's toes point in node space and turn the body to match,
## then measure sole clearance and the walk clip's own ground speed.
func _orient_and_measure() -> void:
	var fl := skel.find_bone("foot_L"); var tl := skel.find_bone("toe_L")
	if fl >= 0 and tl >= 0:
		var to_node := global_transform.affine_inverse() * skel.global_transform
		var d := to_node * skel.get_bone_global_rest(tl).origin - to_node * skel.get_bone_global_rest(fl).origin
		if d.z > 0.0: body.rotation.y += PI
		if OS.get_environment("WB_FLIP") != "": body.rotation.y += PI     # toes point +Z (glTF front) but he walks -Z: turn the model around
	var to_node2 := global_transform.affine_inverse() * skel.global_transform
	var lo := INF
	for bn in ["toe_L", "toe_R"]:
		var b := skel.find_bone(bn)
		if b >= 0: lo = minf(lo, (to_node2 * skel.get_bone_global_rest(b).origin).y)
	var root_y := (to_node2 * skel.get_bone_global_rest(maxi(skel.find_bone("root"), 0)).origin).y
	sole_clear = maxf(0.0, lo - root_y) if lo < INF else 0.0
	walk_rate = 1.0   # measured on the first walking frame (_rate_pending)
	_rate_pending = true
	if OS.get_environment("WB_RATE") != "": walk_rate = float(OS.get_environment("WB_RATE"))

## wb_walk is in place (root stripped): sample the clip on the real skeleton and measure how fast the
## planted (lowest) toe travels backwards in node space; play rate = SPEED / that speed so stance feet stay put.
func _clip_rate(clip: String, speed: float) -> float:
	if not ap.has_animation(clip): return 1.0
	var prev := ap.current_animation; var prev_t := ap.current_animation_position if prev != "" else 0.0
	ap.play(clip); var L := ap.get_animation(clip).length; var n := 60
	var inv := global_transform.affine_inverse()
	var pts := {"toe_L": [], "toe_R": []}
	for i in n + 1:
		ap.seek(L * i / n, true); ap.advance(0.0)
		for bn in pts:
			var bi := skel.find_bone(bn)
			if bi >= 0: pts[bn].append(inv * skel.global_transform * skel.get_bone_global_pose(bi).origin)
	# stance = foot moving backwards (+Z, the model faces -Z after the turn... measured in node space, so use the
	# direction opposite to travel) while near its own lowest height; clip ground speed = mean stance speed
	var spd := []
	for bn in pts:
		var ps: Array = pts[bn]; if ps.size() < 2: continue
		var ymin := INF; for q in ps: ymin = minf(ymin, q.y)
		for i in ps.size() - 1:
			var dz: float = (ps[i + 1].z - ps[i].z) / (L / n)   # node fwd is -Z, so a planted foot moves +Z
			if dz > 0.0 and ps[i].y < ymin + 2.0: spd.append(dz)
	spd.sort()
	clip_speed = spd[spd.size() / 2] if spd.size() > 0 else 0.0
	if prev != "": ap.play(prev); ap.seek(prev_t, true)
	return clampf(speed / clip_speed, 0.25, 4.0) if clip_speed > 0.05 else 1.0
var clip_speed := 0.0
var _rate_pending := false

## lowest sole world height vs the terrain right under it
func sole_gap() -> float:
	var g := INF
	for bn in ["toe_L", "toe_R"]:
		var b := skel.find_bone(bn); if b < 0: continue
		var p := skel.global_transform * skel.get_bone_global_pose(b).origin
		g = minf(g, p.y - sole_clear - _gy(p.x, p.z))
	return g if g < INF else 0.0

func _ground_feet(dt: float) -> void:
	if state in ["knockdown", "kneel"]:
		var lo := INF
		for b in range(1, skel.get_bone_count()):   # skip the root bone: it stays at the origin while the body moves
			var q := skel.global_transform * skel.get_bone_global_pose(b).origin
			lo = minf(lo, q.y - _gy(q.x, q.z))
		foot_gap = lo; ground_off -= lo; position.y = _gy(position.x, position.z) + ground_off
		return
	foot_gap = sole_gap()
	ground_off -= foot_gap   # per-frame snap: the lowest sole sits on the terrain under it
	ground_off = clampf(ground_off, -20.0, 20.0)
	position.y = _gy(position.x, position.z) + ground_off
	foot_gap = sole_gap()   # residual after the snap (what the player sees)


# ---------- test 22: heavy giant walk (boss: "his knees are bent too much") ----------
## Lucian's wb_walk keeps both knees bent 55-85 deg (crouched look). After the clip pose each frame: lift the hips
## until the planted (lower) leg is near-straight (STANCE_BEND), then two-bone IK both legs back onto the clip's own
## foot positions (skeleton space). Feet land exactly where the clip put them, so plant timing / slip are unchanged;
## the swing leg still bends because its foot is lifted. The hip lift follows the stride = heavy up/down body bob;
## a small hip roll over the planted leg adds the weight shift.
const STANCE_BEND := 4.0      # deg, IK target for the planted knee (measured ~19 avg with smoothing / double support; was 55)
const LIFT_MIX := 0.0           # 0 = lift only as far as the planted leg needing the least lift (no over-stretch, no slip)
const HIP_ROLL := 2.5          # deg, hips lean over the planted leg
var _hip_lift := 0.0
var _leg_len := {}
var _ik_saved := {}   # bone -> clip pose before our IK; put back before the next ap.advance() so the mixer (blends / unkeyed tracks) never feeds on the IK pose
func _ik_restore() -> void:
	for b in _ik_saved:
		var sv: Array = _ik_saved[b]
		skel.set_bone_pose_position(b, sv[0]); skel.set_bone_pose_rotation(b, sv[1]); skel.set_bone_pose_scale(b, sv[2])
	_ik_saved.clear()
func _ik_bones() -> Array:
	var out := []
	for n in ["hips", "thigh_L", "shin_L", "foot_L", "thigh_R", "shin_R", "foot_R"]:
		var b := skel.find_bone(n); if b >= 0: out.append(b)
	return out
func _straight_legs(dt: float) -> void:
	var hb := skel.find_bone("hips"); if hb < 0: return
	var ikb := _ik_bones(); var clip := {}
	for b in ikb: clip[b] = [skel.get_bone_pose_position(b), skel.get_bone_pose_rotation(b), skel.get_bone_pose_scale(b)]
	var legs := []
	for sd in ["L", "R"]:
		var t := skel.find_bone("thigh_" + sd); var k := skel.find_bone("shin_" + sd); var f := skel.find_bone("foot_" + sd)
		if t < 0 or k < 0 or f < 0: return
		if not _leg_len.has(sd):
			_leg_len[sd] = [(skel.get_bone_global_rest(k).origin - skel.get_bone_global_rest(t).origin).length(), (skel.get_bone_global_rest(f).origin - skel.get_bone_global_rest(k).origin).length()]
		legs.append([t, k, f, skel.get_bone_global_pose(t), skel.get_bone_global_pose(k), skel.get_bone_global_pose(f), _leg_len[sd]])
	# planted legs = feet near the lowest foot (both in double support); lift until the planted leg needing the
	# least lift reaches a STANCE_BEND knee, so no planted leg is ever over-stretched
	var ty := [skel.get_bone_global_pose(skel.find_bone("toe_L")).origin.y, skel.get_bone_global_pose(skel.find_bone("toe_R")).origin.y]
	var lo: float = minf(ty[0], ty[1])
	var want := -1.0; var st: Array = legs[0]; var wmin := INF
	for li in 2:
		var lg: Array = legs[li]
		if ty[li] > lo + 0.12: continue
		var L1: float = lg[6][0]; var L2: float = lg[6][1]
		var d := sqrt(L1 * L1 + L2 * L2 + 2.0 * L1 * L2 * cos(deg_to_rad(STANCE_BEND)))
		var r: Vector3 = lg[5].origin - lg[3].origin
		var rxz := Vector2(r.x, r.z).length_squared()
		var w := maxf(0.0, sqrt(maxf(d * d - rxz, 0.0)) + r.y) if d * d > rxz else 0.0
		if w > want: want = w; st = lg
		wmin = minf(wmin, w)
	want = maxf(lerpf(wmin, want, LIFT_MIX) if wmin < INF else 0.0, 0.0)
	_hip_lift = lerpf(_hip_lift, want, clampf(dt * 25.0, 0.0, 1.0))
	var up := Vector3(0, _hip_lift, 0)
	var hp := skel.get_bone_global_pose(hb)
	var lean := 1.0 if st == legs[0] else -1.0   # +X = his left
	var roll := Basis(Vector3(0, 0, 1), deg_to_rad(HIP_ROLL) * -lean)
	hp.origin += up
	skel.set_bone_global_pose(hb, Transform3D(roll * hp.basis, hp.origin))
	for lg in legs:
		var t: int = lg[0]; var k: int = lg[1]; var f: int = lg[2]
		var A: Vector3 = skel.get_bone_global_pose(t).origin
		var K0: Vector3 = lg[4].origin + up; var C: Vector3 = lg[5].origin
		var a: float = lg[6][0]; var b: float = lg[6][1]
		var ac := C - A; var dist := clampf(ac.length(), absf(a - b) + 0.001, a + b - 0.001)
		var dir := ac.normalized()
		var pole := (K0 - A) - dir * (K0 - A).dot(dir)
		if pole.length() < 0.0001: pole = Vector3(0, 0, 1)   # knee forward fallback
		pole = pole.normalized()
		var x := (a * a - b * b + dist * dist) / (2.0 * dist); var h := sqrt(maxf(a * a - x * x, 0.0))
		var K := A + dir * x + pole * h
		_aim_global(t, k, K - A); _aim_global(k, f, A + dir * dist - K)
		var fp := skel.get_bone_global_pose(f)
		skel.set_bone_global_pose(f, Transform3D(lg[5].basis, fp.origin))   # foot keeps the clip's orientation (flat plant)
	for b in ikb: _ik_saved[b] = clip[b]
	for b in ikb: skel.set_bone_pose_scale(b, clip[b][2])   # IK only rotates/moves: no scale creep
## rotate bone b (global pose) so its child direction points along d
func _aim_global(b: int, c: int, d: Vector3) -> void:
	var g := skel.get_bone_global_pose(b)
	var cur := (skel.get_bone_global_pose(c).origin - g.origin).normalized()
	if cur.length() < 0.5 or d.length() < 0.0001: return
	var q := Quaternion(cur, d.normalized())
	skel.set_bone_global_pose(b, Transform3D(Basis(q) * g.basis, g.origin))

# ---------- test 19: clean one-knee pose (boss: the old knockdown clip + slump looked like a pretzel) ----------
## Built once from the wb_idle pose by aiming bones (skeleton space, +Z = his front, +X = his left):
## left knee down with the shin back along the ground, right foot planted forward, torso upright leaning a
## little forward, left fist on the ground for support, right forearm resting over the right knee.
const KNEEL_AIM := [
	["spine", "spine2", Vector3(0, 1, 0.22)], ["spine2", "chest", Vector3(0, 1, 0.25)], ["chest", "upperChest", Vector3(0, 1, 0.25)],
	["upperChest", "neck", Vector3(0, 1, 0.2)], ["neck", "head", Vector3(0, 1, 0.1)],
	["thigh_L", "shin_L", Vector3(0.15, -1, 0.12)], ["shin_L", "foot_L", Vector3(0.05, -0.12, -1)], ["foot_L", "toe_L", Vector3(0, -0.5, -1)],
	["thigh_R", "shin_R", Vector3(-0.25, -0.12, 1)], ["shin_R", "foot_R", Vector3(-0.05, -1, 0.05)], ["foot_R", "toe_R", Vector3(0, -0.6, 1)],
	["upperArm_L", "foreArm_L", Vector3(0.35, -1, 0.45)], ["foreArm_L", "hand_L", Vector3(0.1, -1, 0.15)],
	["upperArm_R", "foreArm_R", Vector3(-0.25, -0.9, 0.6)], ["foreArm_R", "hand_R", Vector3(0.1, -0.8, 0.6)],
]
func _aim_bone(b: int, c: int, d: Vector3) -> void:
	var gb := skel.get_bone_global_pose(b); var gc := skel.get_bone_global_pose(c)
	var cur := (gc.origin - gb.origin).normalized()
	var q := Quaternion(cur, d.normalized())
	var ng := Basis(q) * gb.basis.orthonormalized()
	var p := skel.get_bone_parent(b)
	var pb := skel.get_bone_global_pose(p).basis.orthonormalized() if p >= 0 else Basis()
	skel.set_bone_pose_rotation(b, (pb.inverse() * ng).get_rotation_quaternion())

func _build_kneel() -> void:
	if not ap.has_animation("wb_idle"): return
	ap.play("wb_idle"); ap.seek(0.0, true); ap.advance(0.0)
	for a in KNEEL_AIM:
		var b := skel.find_bone(a[0]); var c := skel.find_bone(a[1])
		if b >= 0 and c >= 0: _aim_bone(b, c, a[2])
	# drop the hips so the knee / planted foot / fist sit on his ground plane (root bone height)
	var lo := INF
	for n in ["shin_L", "toe_L", "foot_R", "toe_R", "fingers_L"]:
		var bi := skel.find_bone(n); if bi >= 0: lo = minf(lo, skel.get_bone_global_pose(bi).origin.y)
	var hb := skel.find_bone("hips"); var rb := skel.find_bone("root")
	var ry := skel.get_bone_global_pose(rb).origin.y if rb >= 0 else 0.0
	if hb >= 0 and lo < INF: skel.set_bone_pose_position(hb, skel.get_bone_pose_position(hb) - Vector3(0, lo - ry, 0))
	var anim := Animation.new(); anim.length = 1.0; anim.loop_mode = Animation.LOOP_LINEAR
	var sp := ap.get_node(ap.root_node).get_path_to(skel)
	for b in skel.get_bone_count():
		var t := anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(t, NodePath("%s:%s" % [sp, skel.get_bone_name(b)]))
		anim.rotation_track_insert_key(t, 0.0, skel.get_bone_pose_rotation(b))
		var tp := anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(tp, NodePath("%s:%s" % [sp, skel.get_bone_name(b)]))
		anim.position_track_insert_key(tp, 0.0, skel.get_bone_pose_position(b))
	var libs := ap.get_animation_library_list()
	ap.get_animation_library(libs[0]).add_animation("wb_kneel", anim)
	ap.play("wb_idle"); ap.seek(0.0, true); ap.advance(0.0)
