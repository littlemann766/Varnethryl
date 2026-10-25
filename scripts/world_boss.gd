class_name WorldBoss
extends Node3D
## World-boss Ashen Titan TEST (godot-test-worldboss1). Single-player preview, no net sync.
## Roams the main map OUTSIDE the walls on a ring of waypoints (r 330 m, never inside the city), 114 m tall (x5.440).
## Placeholder motion: in-place walk clip slowed to 0.3x, glided at 3 m/s. Rituals: Fissure Slam (12 s) and Lava Wave (10 s),
## interrupted by damaging the 6 weak-point crystals. Art: Beth's worldboss kit (assets/volcano/worldboss) + lava veins.

const SCALE := 5.440
const SPEED := 3.0
const WB := "res://assets/volcano/worldboss/"
const LAVA := "res://assets/volcano/worldboss/titan/"
const RING_R := 330.0
const MAX_HP := 3000.0
const CRYSTAL_HP := 90.0           # 3 %
const INTERRUPT := 120.0           # 4 % (solo floor of 8% x sqrt(n)/2)
const SHAKE_FULL := 120.0
const SHAKE_ZERO := 250.0
const BAR_RANGE := 400.0
const STEP_FRAC := [0.475, 0.925]  # walk clip footfalls (L, R), measured from foot bone minima

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
var wave: MeshInstance3D
var strip: MeshInstance3D
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
	for i in 6:
		var a := i / 6.0 * TAU + 0.2
		waypoints.append(Vector3(cos(a) * RING_R, 0, sin(a) * RING_R))
	body = (load(WB + "titan/ashentitan_volcano_glow_lod1.glb") as PackedScene).instantiate()
	body.scale = Vector3.ONE * SCALE
	add_child(body)
	ap = body.find_children("*", "AnimationPlayer", true, false)[0]
	skel = body.find_children("*", "Skeleton3D", true, false)[0]
	for c in ["walk", "idle", "windup"]:
		if ap.has_animation(c): ap.get_animation(c).loop_mode = Animation.LOOP_LINEAR
	for mi: MeshInstance3D in body.find_children("*", "MeshInstance3D", true, false):
		mi.extra_cull_margin = 40.0
	_veins(); _crystals(); _telegraphs(); _ui()
	dust_scene = load(WB + "wb_dust_burst.tscn")
	place_at(0)
	return self

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

func _gy(x: float, z: float) -> float:
	return float(m.call("height", x, z)) if m and m.has_method("height") else 0.0

# ---------- art ----------
func _veins() -> void:
	lava_mat = (load(WB + "titan/" + ("titan_lava_material_volcano_glow_lod1.tres" if hq else "titan_lava_fallback_volcano_glow_lod1.tres")) as Material).duplicate()
	for mi: MeshInstance3D in body.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = lava_mat
	if lava_mat is ShaderMaterial: (lava_mat as ShaderMaterial).set_shader_parameter("glow_strength", 2.2)
	elif lava_mat is StandardMaterial3D: (lava_mat as StandardMaterial3D).emission_energy_multiplier = 4.4
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
	wave = MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 1.0; cm.bottom_radius = 1.0; cm.height = 1.0
	cm.cap_top = false; cm.cap_bottom = false; cm.radial_segments = 48; wave.mesh = cm
	wave.material_override = (load(WB + "materials/wb_lava_ring_mat.tres") as Material).duplicate()
	wave.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; wave.top_level = true; wave.visible = false; add_child(wave)
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
	for i in 6:
		var pp := ColorRect.new(); pp.size = Vector2(14, 14); pp.position = Vector2(500 + i * 26, 56); pp.color = Color(1, 0.6, 0.2); r.add_child(pp); pips.append(pp)
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

func _warn(t: String) -> void:
	warn.text = t; warn.visible = true; warn.modulate.a = 1.0
	var tw := create_tween(); tw.tween_interval(2.0); tw.tween_property(warn, "modulate:a", 0.0, 0.6); tw.tween_callback(func(): warn.visible = false)

# ---------- loop ----------
func _set_state(s: String) -> void:
	state = s; t_state = 0.0
	match s:
		"walk": _play("walk", 0.3)
		"idle", "cool": _play("idle", 0.6); _crystal_glow(1.0)
		"windup": _play("windup", 0.5)
		"release": _play("eruption_slam" if ritual == "fissure" else "volcano_roar", 0.6)
		"stagger": _play("hit", 0.35)

func _play(c: String, sp: float) -> void:
	if ap.has_animation(c): ap.play(c, 0.4); ap.speed_scale = sp

func _hero() -> Node3D: return m.get("hero") as Node3D
func _hero_d() -> float:
	var h := _hero(); return h.global_position.distance_to(global_position) if h else 1e9

func _process(dt: float) -> void:
	if not visible: return
	t_state += dt
	match state:
		"walk": _walk(dt)
		"idle":
			if t_state > 6.0: _start_ritual()
		"windup": _windup(dt)
		"release":
			if t_state > 4.0: _end_ritual_fx(); _set_state("cool")
		"stagger":
			if t_state > 8.0: _set_state("cool")
		"cool":
			if t_state > 10.0: _set_state("walk")
	_update_crystals(dt); _update_prints(dt); _update_adds(dt); _update_ui(); _do_shake(dt)

func _walk(dt: float) -> void:
	var tgt := waypoints[wp]
	var flat := Vector3(tgt.x - position.x, 0, tgt.z - position.z)
	if flat.length() < 4.0:
		wp = (wp + 1) % waypoints.size()
		_stomp(1.0, true); _set_state("idle"); return
	var want := atan2(flat.x, flat.z)           # Titan faces +Z
	rotation.y = rotate_toward(rotation.y, want, deg_to_rad(8.0) * dt)
	var fwd := Vector3(sin(rotation.y), 0, cos(rotation.y))
	var np := position + fwd * SPEED * dt
	if maxf(absf(np.x), absf(np.z)) < 260.0: np = position     # hard rule: never enters the town
	position = Vector3(np.x, _gy(np.x, np.z), np.z)
	# footfalls from the clip phase
	var a := ap.get_animation("walk")
	var f := fmod(ap.current_animation_position, a.length) / a.length
	for i in 2:
		var s: float = STEP_FRAC[i]
		if (last_frac < s and f >= s) or (last_frac > f and s > last_frac): _footfall(i)
	last_frac = f

func _footfall(i: int) -> void:
	var b := skel.find_bone(["foot_L", "foot_R"][i])
	var p := (skel.global_transform * skel.get_bone_global_pose(b)).origin
	_print_at(p); _stomp(0.55, false, p)

func _print_at(p: Vector3) -> void:
	var mat: ShaderMaterial = (load(WB + "materials/wb_footprint_mat.tres") as Material).duplicate()
	var fp := _plane(mat, Vector3(48, 1, 48)); fp.visible = true
	fp.global_position = Vector3(p.x, _gy(p.x, p.z) + 0.4, p.z); fp.rotation.y = rotation.y
	footprints.append([fp, mat, 0.0])
	while footprints.size() > 14: (footprints.pop_front()[0] as Node).queue_free()

func _stomp(amp: float, arrive: bool, at := Vector3.INF) -> void:
	if at == Vector3.INF: at = global_position
	var d: Node3D = dust_scene.instantiate(); d.top_level = true; add_child(d)
	d.global_position = Vector3(at.x, _gy(at.x, at.z) + 0.3, at.z)
	if arrive: d.scale = Vector3.ONE * 2.0
	for p in d.find_children("*", "CPUParticles3D", true, true) + ([d] if d is CPUParticles3D else []): (p as CPUParticles3D).restart()
	get_tree().create_timer(4.0).timeout.connect(d.queue_free)
	shake(amp, 0.9 if arrive else 0.5)

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
		var a := shake_amp * clampf(shake_t / 0.4, 0.0, 1.0)
		cam.h_offset = randf_range(-1, 1) * a; cam.v_offset = randf_range(-1, 1) * a
		if shake_t <= 0.0: cam.h_offset = 0.0; cam.v_offset = 0.0

func _start_ritual() -> void:
	ritual = "fissure" if rituals_done % 2 == 0 else "wave"
	dmg_window = 0.0
	_set_state("windup"); _crystal_glow(2.0)
	var fwd := Vector3(sin(rotation.y), 0, cos(rotation.y))
	if ritual == "fissure":
		cast_icon.texture = load(WB + "tex/wb_icon_fissure_slam.png"); cast_lbl.text = "FISSURE SLAM"
		_ground(crack, global_position + fwd * 6.0, rotation.y)
		for i in 3:
			var yw := rotation.y + deg_to_rad([-40.0, 0.0, 40.0][i])
			var d := Vector3(sin(yw), 0, cos(yw))
			_ground(fissures[i], global_position + d * 30.0, yw)
		_warn("The Titan gathers fire: FISSURE SLAM")
	else:
		cast_icon.texture = load(WB + "tex/wb_icon_lava_wave.png"); cast_lbl.text = "LAVA WAVE"
		_ground(strip, global_position, 0.0)
		wave.visible = true; wave.global_position = global_position; wave.scale = Vector3(80, 12, 80)
		wave.global_position.y = _gy(global_position.x, global_position.z) + 6.0
		(wave.material_override as ShaderMaterial).set_shader_parameter("rise", 0.0)
		_warn("The Titan's core blazes: LAVA WAVE")

func _ground(mi: MeshInstance3D, p: Vector3, yaw: float) -> void:
	mi.visible = true; mi.global_position = Vector3(p.x, _gy(p.x, p.z) + 0.5, p.z); mi.rotation = Vector3(0, yaw, 0)
	var sm := mi.material_override as ShaderMaterial
	for k in ["progress", "erupt", "rise"]: sm.set_shader_parameter(k, 0.0)

func _wind_len() -> float: return 12.0 if ritual == "fissure" else 10.0

func _windup(_dt: float) -> void:
	var k := clampf(t_state / _wind_len(), 0.0, 1.0)
	_set_glow_charge(k, ritual == "wave")
	if ritual == "fissure":
		(crack.material_override as ShaderMaterial).set_shader_parameter("progress", k)
		for f in fissures: (f.material_override as ShaderMaterial).set_shader_parameter("progress", k)
	else:
		(wave.material_override as ShaderMaterial).set_shader_parameter("rise", k)
		(strip.material_override as ShaderMaterial).set_shader_parameter("rise", k)
	if t_state - _dt < _wind_len() - 3.0 and t_state >= _wind_len() - 3.0: _warn("3 SECONDS! Break his crystals!")
	if dmg_window >= INTERRUPT:
		_warn("INTERRUPTED! The Titan staggers"); _end_ritual_fx(); _set_glow_charge(0.0); _set_state("stagger"); return
	if t_state >= _wind_len(): _complete()

func _complete() -> void:
	rituals_done += 1; pressure += 1
	_set_glow_charge(0.0)
	var h := _hero()
	var hit := false
	if ritual == "fissure":
		(crack.material_override as ShaderMaterial).set_shader_parameter("erupt", 1.0)
		for f in fissures: (f.material_override as ShaderMaterial).set_shader_parameter("erupt", 1.0)
		if h and Vector2(h.global_position.x - crack.global_position.x, h.global_position.z - crack.global_position.z).length() < 60.0: hit = true
		shake(1.0, 1.2); _warn("FISSURE SLAM!")
	else:
		create_tween().tween_property(wave, "scale", Vector3(170, 12, 170), 3.0)
		if h and _hero_d() < 170.0 and not bool(m.get("cheat").get("fly", false)): hit = true
		shake(0.8, 1.5); _warn("LAVA WAVE!")
	if pressure >= 3: pressure = 0; _warn("VOLCANO PRESSURE PEAKS - lava bombs rain on the region")
	var party = m.get("party")
	if hit and party and party.combat and not bool(m.get("cheat").get("god", false)):
		var c = party.combat
		c.hp = maxf(1.0, c.hp - c.max_hp * (0.4 if ritual == "fissure" else 0.5)); c.hero_hurt.emit(int(c.max_hp * 0.4))
	_set_state("release")

func _end_ritual_fx() -> void:
	for mi in [crack, strip] + fissures:
		var sm := (mi as MeshInstance3D).material_override as ShaderMaterial
		var tw := create_tween(); tw.tween_method(func(v): sm.set_shader_parameter("progress", v), 1.0, 0.0, 1.5)
		tw.tween_callback(func(): (mi as MeshInstance3D).visible = false)
	wave.visible = false

# ---------- damage (hooked to HeroCombat.used) ----------
func on_hero_used(slot: int, _sk: Dictionary) -> void:
	if not visible: return
	var h := _hero(); if h == null: return
	var dmg := 10.0 if slot == 0 else 25.0
	var hp3 := h.global_position
	var best = null; var bd := 1e9
	for c in crystals:
		if c.broken: continue
		var cp: Vector3 = (c.node as Node3D).global_position
		var d3 := hp3.distance_to(cp)
		var dh := Vector2(hp3.x - cp.x, hp3.z - cp.z).length()
		var ok: bool = d3 < 22.0 or (bool(c.ground) and dh < 30.0)
		if ok and d3 < bd: bd = d3; best = c
	if best: _hit_crystal(best, dmg)
	elif Vector2(hp3.x - global_position.x, hp3.z - global_position.z).length() < 45.0: _damage(dmg * 0.1)

func _hit_crystal(c: Dictionary, dmg: float) -> void:
	var mult := 2.0 if state == "stagger" else 1.0
	c.hp -= dmg * mult
	_damage(dmg * mult)
	if state == "windup": dmg_window += dmg * mult
	var mat: ShaderMaterial = c.mat
	mat.set_shader_parameter("hit_flash", 1.0)
	create_tween().tween_method(func(v): mat.set_shader_parameter("hit_flash", v), 1.0, 0.0, 0.15)
	if c.hp <= 0.0:
		c.broken = true; c.t_broken = 0.0; _crystal_meshes(c, true); _spawn_adds(c.node.global_position)
		if crystals.all(func(x): return x.broken): _warn("ALL WEAK POINTS BROKEN - KNOCKDOWN"); _end_ritual_fx(); _set_state("stagger")

func _damage(v: float) -> void:
	hp = maxf(0.0, hp - v)
	if hp <= 0.0:
		_warn("THE ASHEN TITAN FALLS"); _play("death", 0.5); state = "dead"
		get_tree().create_timer(20.0).timeout.connect(func(): place_at(wp))

func _update_crystals(dt: float) -> void:
	for c in crystals:
		if c.broken:
			c.t_broken += dt
			if c.t_broken > 60.0: _crystal_restore(c)

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
		if add_t <= 0.0: add_t = 45.0; _spawn_adds(global_position + Vector3(sin(rotation.y), 0, cos(rotation.y)) * 50.0)
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
		mat.set_shader_parameter("fade", clampf(1.0 - (f[2] - 100.0) / 20.0, 0.0, 1.0))
	while footprints.size() > 0 and footprints[0][2] > 120.0: (footprints.pop_front()[0] as Node).queue_free()

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
