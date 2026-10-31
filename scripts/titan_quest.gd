class_name TitanQuest
extends Node3D
## Test 13 (boss via Beth): quest "Stop the volcano from erupting".
## Giver at the volcano path foot -> crossing the crater rim plays the intro (wide camera, Lucian's `intro` climb-out
## rising y 10 -> 26.8 over 3.5 s, lava splash + shake, "ASHEN TITAN" card at the roar, then the boss bar with
## notches at 66/33 %). Three stages swap Beth's arena floor + col + lava hazard, sink him (26.8 / 21.0 / 18.4),
## glow 1.0 / 2.2 / 4.0, ring 7/7/8, shake + burst + more smoke/embers. Win: volcano calms, quest completes.

const QUEST := "Stop the volcano from erupting"
const STAGE_Y := [26.8, 21.0, 18.4]          # Beth, titan root (feet) y per stage, volcano-local (for the 28 m Titan)
const GLOW := [1.0, 2.2, 4.0]
const LAVA_GLOW := [1.0, 1.35, 1.8]
const RING := [7.0, 7.0, 8.0]
const SMOKE := [1.0, 1.8, 3.0]
const EMBERS := [12, 24, 48]
const RISE_FROM := 10.0
const RISE_SEC := 3.5
const INTRO_SEC := 9.233
const HAZARD_LAYER := 1 << 19
const HAZARD_DPS := 0.15                     # share of max HP per second in lava

var m: Node                 # main
var base: Vector3           # volcano origin (cone centre at ground)
var titan: VolcanoTitan
var state := "none"         # none -> active -> intro -> fight -> won
var stage := 0
var stages: Array = []      # [{vis, col, haz}]
var ring: MeshInstance3D
var embers: CPUParticles3D
var smokes: Array = []      # [particles, base amount]
var giver: Node3D
var bar: Control; var bar_fill: ColorRect; var card: Label; var qlabel: Label
var intro_cam: Camera3D
var shake_t := 0.0
var t_intro := 0.0
var hazard_hits := 0.0      # test hook: total lava damage dealt
var _tw: Tween

func setup(main: Node) -> TitanQuest:
	m = main; name = "TitanQuest"; base = m.volc_base
	for e in m.party.director.enemies:
		if e is VolcanoTitan: titan = e
	if titan == null:   # benches/tests run without the default enemy set
		var d: EnemyDirector = m.party.director
		titan = VolcanoTitan.new(); d.add_child(titan); titan.setup_volcano(d.ground); d._wire(titan, m.hero)
		titan.aoe.connect(func(c, r, mm): d._aoe(titan, c, r, mm))
	titan.telegraph.connect(_telegraph)
	titan.died.connect(func(_e): _win())
	_hide_titan()
	titan.lava_veins(int(m.tier) >= 2)   # test 14: Beth's lava veins; fallback material on Low/Medium
	titan.rig.set_death_clip("death_pool")   # Lucian v3: in-pool death (3.03 s, holds), instead of `death`
	for n in 3: stages.append(_load_stage(n + 1))
	_show_stage(1)
	ring = load("res://assets/volcano/titan_lava_ring.glb").instantiate().find_children("*", "MeshInstance3D", true, false)[0].duplicate()
	var rm := StandardMaterial3D.new(); rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; rm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	rm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD; rm.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED; rm.cull_mode = BaseMaterial3D.CULL_DISABLED
	rm.albedo_color = Color(1.0, 0.45, 0.1, 0.8); ring.material_override = rm; ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(ring); ring.position = Vector3(VolcanoTitan.CENTER.x, base.y + 38.03, VolcanoTitan.CENTER.z); ring.visible = false
	embers = _embers(); add_child(embers); embers.emitting = false
	for f in m.volc_fx: if f is CPUParticles3D: smokes.append([f, (f as CPUParticles3D).amount])
	_giver(); _ui()
	if m.has_method("volcano_quest_done") and m.volcano_quest_done(): apply_aftermath()   # test 24: persists across reloads
	return self

## test 24 (boss: "the volcano must stay destroyed while the Titan is out"): the quest-complete aftermath, applied
## instantly from the saved story flag (volcano_done in user://story.cfg). Same end state as _win(): last (most broken)
## arena stage, calm lava, thin smoke, dimmed lava lights, quest Titan gone, giver retired. Re-applied by
## main.apply_quality / _set_time via reapply_aftermath(), so tier swaps and day/night can't bring the eruption back.
## Master has no restore path: nothing un-completes the quest, and defeating the world boss doesn't restore it.
func apply_aftermath() -> void:
	state = "won"; stage = 3
	_show_stage(3)
	titan.active = false; titan.visible = false; titan.glow_strength = 0.25
	if bar: bar.visible = false
	if card: card.visible = false
	if ring: ring.visible = false
	if embers: embers.emitting = false
	if giver: giver.visible = false
	if qlabel: qlabel.visible = false
	reapply_aftermath()
func reapply_aftermath() -> void:
	if state != "won": return
	if m.lava_mat(): m.lava_mat().set_shader_parameter("glow", 0.12); m.lava_mat().set_shader_parameter("calm", 1.0)
	for s in smokes: (s[0] as CPUParticles3D).amount = maxi(2, int(s[1] * 0.3))
	for l in m.pool_lights: (l as OmniLight3D).light_energy = 0.5
	for f in m.volc_fx:
		if f is OmniLight3D and not m.pool_lights.has(f):
			if not f.has_meta("e0"): f.set_meta("e0", (f as OmniLight3D).light_energy)
			(f as OmniLight3D).light_energy = float(f.get_meta("e0")) * 0.4

# ---------- arena ----------
func _load_stage(n: int) -> Dictionary:
	var root := Node3D.new(); root.name = "ArenaStage%d" % n; root.position = base; add_child(root)
	var bands := [[0.0, 260.0], [260.0, 0.0]]
	for k in 2:
		var v: Node3D = load("res://assets/volcano/stages/volcano_arena_stage%d_lod%d.glb" % [n, k + 1]).instantiate(); root.add_child(v)
		for mi in v.find_children("*", "MeshInstance3D", true, false):
			mi.visibility_range_begin = bands[k][0]; mi.visibility_range_end = bands[k][1]
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var col: Node3D = load("res://assets/volcano/stages/volcano_arena_stage%d_col.glb" % n).instantiate(); col.position = base; add_child(col)
	for mi in col.find_children("*", "MeshInstance3D", true, false): mi.visible = false
	# lava hazard: Beth's flat polys (y 37.05..38.05) as a query-only body on its own layer
	var hz := StaticBody3D.new(); hz.name = "Hazard%d" % n; hz.collision_layer = 0; hz.collision_mask = 0; hz.position = base; add_child(hz)
	var hv: Node3D = load("res://assets/volcano/stages/volcano_arena_stage%d_hazard.glb" % n).instantiate()
	for mi: MeshInstance3D in hv.find_children("*", "MeshInstance3D", true, false):
		var cs := CollisionShape3D.new(); cs.shape = mi.mesh.create_trimesh_shape(); cs.transform = mi.global_transform if mi.is_inside_tree() else _rel(hv, mi); hz.add_child(cs)
	hv.free()
	return {"vis": root, "col": col, "haz": hz}

func _rel(r: Node, n: Node3D) -> Transform3D:
	var x: Node = n; var t := Transform3D.IDENTITY
	while x and x != r:
		if x is Node3D: t = (x as Node3D).transform * t
		x = x.get_parent()
	return t

func _show_stage(n: int) -> void:
	stage = n
	for i in 3:
		var on := i == n - 1; var s: Dictionary = stages[i]
		(s.vis as Node3D).visible = on
		for b in (s.col as Node).find_children("*", "CollisionObject3D", true, false): (b as CollisionObject3D).collision_layer = 1 if on else 0
		if s.col is CollisionObject3D: (s.col as CollisionObject3D).collision_layer = 1 if on else 0
		(s.haz as StaticBody3D).collision_layer = HAZARD_LAYER if on else 0
	titan.stage = n
	titan.set_glow(GLOW[n - 1])
	titan.lava_stage(n)
	if m.lava_mat(): m.lava_mat().set_shader_parameter("glow", LAVA_GLOW[n - 1])
	if ring: ring.scale = Vector3(RING[n - 1], 1.0, RING[n - 1])
	for s in smokes: (s[0] as CPUParticles3D).amount = int(s[1] * SMOKE[n - 1])
	if embers: embers.amount = EMBERS[n - 1]

func in_lava(p: Vector3) -> bool:
	var q := PhysicsRayQueryParameters3D.create(p + Vector3(0, 1.2, 0), p - Vector3(0, 2.5, 0), HAZARD_LAYER)
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if hit.is_empty(): return p.y < base.y + 38.0 and _in_crater(p)
	# a plate above the lava wins: only lava if no walkable col is between the feet and the hazard
	var q2 := PhysicsRayQueryParameters3D.create(p + Vector3(0, 1.2, 0), p - Vector3(0, 2.5, 0), 1)
	var h2 := get_world_3d().direct_space_state.intersect_ray(q2)
	return h2.is_empty() or (h2.position as Vector3).y < (hit.position as Vector3).y + 0.3

func _in_crater(p: Vector3) -> bool:
	return Vector2(p.x - VolcanoTitan.CENTER.x, p.z - VolcanoTitan.CENTER.z).length() < 40.0

# ---------- quest giver + trigger ----------
func _giver() -> void:
	var ps: Array = m.volc_vj.path.start
	giver = Node3D.new(); giver.name = "EmberWarden"; add_child(giver)
	var gp := base + Vector3(ps[0] - 6.0, 0, ps[2] - 4.0); gp.y = m.height(gp.x, gp.z)
	giver.position = gp
	var st := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 0.35; cm.bottom_radius = 0.6; cm.height = 2.6; st.mesh = cm
	var sm := StandardMaterial3D.new(); sm.albedo_color = Color(0.18, 0.16, 0.15); sm.emission_enabled = true; sm.emission = Color(1, 0.4, 0.1); sm.emission_energy_multiplier = 0.4
	st.material_override = sm; st.position.y = 1.3; giver.add_child(st)
	var lb := Label3D.new(); lb.text = "!  Ember Warden"; lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED; lb.font_size = 64; lb.pixel_size = 0.01
	lb.modulate = Color(1, 0.8, 0.3); lb.outline_size = 12; lb.position.y = 3.4; giver.add_child(lb)

func accept() -> void:
	if state != "none": return
	state = "active"; qlabel.text = "Quest: " + QUEST + "\nClimb the volcano and enter the crater."; qlabel.visible = true
	if m.has_method("_toast"): m._toast("New quest: " + QUEST)

func _physics_process(dt: float) -> void:
	if titan == null or m.hero == null: return
	var hp: Vector3 = m.hero.global_position
	match state:
		"none":
			if hp.distance_to(giver.global_position) < 6.0: accept()
			elif _crossed_rim(hp): accept(); start_intro()
		"active":
			if _crossed_rim(hp): start_intro()
		"intro":
			t_intro += dt
		"fight":
			var f := titan.hp / titan.max_hp
			if stage == 1 and f <= 0.66: swap_stage(2)
			elif stage == 2 and f <= 0.33: swap_stage(3)
			bar_fill.size.x = 420.0 * f
	if state in ["intro", "fight"] and in_lava(hp): _burn(dt)
	_shake(dt)

func _crossed_rim(p: Vector3) -> bool:
	return _in_crater(p) and Vector2(p.x - VolcanoTitan.CENTER.x, p.z - VolcanoTitan.CENTER.z).length() < 36.0 and p.y > base.y + 36.0

func _burn(dt: float) -> void:
	var c: HeroCombat = m.party.combat
	var d := c.max_hp * HAZARD_DPS * dt; c.hp = maxf(0.0, c.hp - d); hazard_hits += d
	if m.hero.global_position.y < base.y + 38.0:   # push up onto the crust
		m.hero.global_position.y = base.y + 39.2; m.hero.velocity.y = 4.0

# ---------- intro ----------
func _hide_titan() -> void:
	titan.active = false; titan.visible = false
	titan.position = Vector3(VolcanoTitan.CENTER.x, base.y + RISE_FROM, VolcanoTitan.CENTER.z)
	titan.rotation.y = deg_to_rad(float(m.volc_vj.titan_spawn.get("yaw_deg", 40.0)))
	titan.height_fn = Callable()

func start_intro() -> void:
	if state == "intro" or state == "fight" or state == "won": return
	state = "intro"; t_intro = 0.0; qlabel.text = "Quest: " + QUEST + "\nDefeat the Ashen Titan."
	titan.visible = true; ring.visible = true; embers.emitting = true
	# wide camera over the crater, looking at the pool from the ramp side
	intro_cam = Camera3D.new(); intro_cam.far = 1500; add_child(intro_cam)
	var c := VolcanoTitan.CENTER
	var hp: Vector3 = m.hero.global_position; var away := Vector2(hp.x - c.x, hp.z - c.z).normalized()
	if away.length() < 0.5: away = Vector2(0.6, 0.8)
	intro_cam.look_at_from_position(Vector3(c.x + away.x * 27.0, base.y + 64.0, c.z + away.y * 27.0), Vector3(c.x, base.y + 44.0, c.z))
	intro_cam.current = true
	titan.rig.play_attack("intro", 1.0)
	_splash(18); shake(0.5, 0.6)
	_tw = create_tween()
	# Lucian v3: his palm plants assume a LINEAR rise y 10 -> 26.8 over 0-3.5 s
	_tw.tween_property(titan, "position:y", base.y + STAGE_Y[0], RISE_SEC).set_trans(Tween.TRANS_LINEAR)
	_tw.tween_callback(func(): _splash(12); shake(0.35, 0.5))          # 3.5 s: hands brace on the lava
	_tw.tween_interval(0.4)
	_tw.tween_callback(func(): shake(0.25, 1.4))                       # 3.9-5.5 heave
	_tw.tween_interval(2.1)
	_tw.tween_callback(func(): _card(true); shake(0.3, 2.0))           # 6.0 roar -> name card
	_tw.tween_interval(2.8)
	_tw.tween_callback(func(): _card(false))
	_tw.tween_interval(INTRO_SEC - 8.8)
	_tw.tween_callback(_begin_fight)

func skip_intro() -> void:
	if state != "intro": return
	if _tw: _tw.kill()
	titan.position.y = base.y + STAGE_Y[0]; _card(false); _begin_fight()

func _begin_fight() -> void:
	if intro_cam: intro_cam.current = false; intro_cam.queue_free(); intro_cam = null
	if m.cam: m.cam.current = true
	state = "fight"; titan.active = true; titan.set_state("chase"); bar.visible = true

# ---------- stages ----------
func swap_stage(n: int) -> void:
	if n <= stage: return
	shake(0.6, 0.6); _burst()
	titan.rig.play_attack("volcano_roar", 1.0)
	_show_stage(n)
	var tw := create_tween()
	tw.tween_interval(0.2)
	tw.tween_property(titan, "position:y", base.y + STAGE_Y[n - 1], 1.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	if m.has_method("_toast"): m._toast("The Titan sinks deeper - the crater breaks apart!")

# ---------- win ----------
func _win() -> void:
	if state == "won": return
	state = "won"; bar.visible = false; embers.emitting = false
	if m.lava_mat(): m.lava_mat().set_shader_parameter("glow", 0.12); m.lava_mat().set_shader_parameter("calm", 1.0)
	for s in smokes: (s[0] as CPUParticles3D).amount = maxi(2, int(s[1] * 0.3))
	for l in m.pool_lights: (l as OmniLight3D).light_energy = 0.5
	for f in m.volc_fx: if f is OmniLight3D and not m.pool_lights.has(f): f.set_meta("e0", (f as OmniLight3D).light_energy); (f as OmniLight3D).light_energy *= 0.4
	ring.visible = false
	create_tween().tween_property(titan, "glow_strength", 0.25, 3.0)   # veins cool as he falls
	var tw := create_tween(); tw.tween_interval(3.1); tw.tween_property(titan, "position:y", base.y + 2.0, 4.0).set_trans(Tween.TRANS_SINE)
	tw.tween_callback(func(): titan.visible = false)
	qlabel.text = "Quest complete: " + QUEST
	if m.has_method("_toast"): m._toast("Quest complete: the volcano is calm.")
	if m.has_method("on_volcano_quest_done"): m.on_volcano_quest_done()   # test 15: unlocks the world boss

# ---------- FX ----------
func shake(amp: float, sec: float) -> void: shake_t = maxf(shake_t, sec); _shake_amp = maxf(_shake_amp if shake_t > 0 else 0.0, amp)
var _shake_amp := 0.0
func _shake(dt: float) -> void:
	var cam: Camera3D = intro_cam if intro_cam else m.cam
	if cam == null: return
	if shake_t > 0.0:
		shake_t -= dt
		cam.h_offset = randf_range(-1, 1) * _shake_amp; cam.v_offset = randf_range(-1, 1) * _shake_amp
	elif cam.h_offset != 0.0 or cam.v_offset != 0.0: cam.h_offset = 0.0; cam.v_offset = 0.0; _shake_amp = 0.0

func _fx_mat(col: Color) -> StandardMaterial3D:
	var s := StandardMaterial3D.new(); s.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; s.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	s.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES; s.vertex_color_use_as_albedo = true; s.albedo_color = col; s.albedo_texture = m._soft_dot()
	s.blend_mode = BaseMaterial3D.BLEND_MODE_ADD; s.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED; return s

func _embers() -> CPUParticles3D:
	var p := CPUParticles3D.new(); p.name = "Embers"; p.amount = EMBERS[0]; p.lifetime = 5.0
	p.position = Vector3(VolcanoTitan.CENTER.x, base.y + 38.5, VolcanoTitan.CENTER.z)
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE; p.emission_sphere_radius = 30.0
	p.direction = Vector3.UP; p.spread = 25.0; p.gravity = Vector3(0, 1.2, 0); p.initial_velocity_min = 1.5; p.initial_velocity_max = 4.0
	var q := QuadMesh.new(); q.size = Vector2(0.35, 0.35); q.material = _fx_mat(Color(1, 0.55, 0.15)); p.mesh = q
	p.color = Color(1.0, 0.6, 0.2); return p

## one-shot burst of embers + rock chunks at the pool (stage swap / intro splash)
func _burst() -> void: _splash(40)
func _splash(n: int) -> void:
	var p := CPUParticles3D.new(); p.one_shot = true; p.explosiveness = 0.95; p.amount = n; p.lifetime = 2.2
	p.position = Vector3(VolcanoTitan.CENTER.x, base.y + 38.3, VolcanoTitan.CENTER.z)
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_RING; p.emission_ring_radius = 9.0; p.emission_ring_inner_radius = 3.0; p.emission_ring_height = 0.5; p.emission_ring_axis = Vector3.UP
	p.direction = Vector3.UP; p.spread = 35.0; p.initial_velocity_min = 8.0; p.initial_velocity_max = 18.0; p.gravity = Vector3(0, -9.8, 0)
	var q := QuadMesh.new(); q.size = Vector2(1.4, 1.4); q.material = _fx_mat(Color(1, 0.5, 0.12)); p.mesh = q; p.color = Color(1, 0.55, 0.15)
	var cv := Curve.new(); cv.add_point(Vector2(0, 1)); cv.add_point(Vector2(1, 0.2)); p.scale_amount_curve = cv
	add_child(p); p.emitting = true
	get_tree().create_timer(2.6).timeout.connect(p.queue_free)

func _telegraph(at: Vector3, r: float, sec: float) -> void:
	var d := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = r; cm.bottom_radius = r; cm.height = 0.05; cm.radial_segments = 32; d.mesh = cm
	var s := StandardMaterial3D.new(); s.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; s.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	s.albedo_color = Color(1, 0.2, 0.05, 0.22); s.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED; d.material_override = s
	d.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(d); d.global_position = at + Vector3(0, 0.08, 0)
	get_tree().create_timer(maxf(sec, 0.2)).timeout.connect(d.queue_free)

# ---------- UI ----------
func _ui() -> void:
	var cl := CanvasLayer.new(); cl.layer = 4; add_child(cl)
	bar = Control.new(); bar.visible = false; bar.position = Vector2(0, 0); bar.set_anchors_preset(Control.PRESET_CENTER_TOP); cl.add_child(bar)
	var root := Control.new(); root.position = Vector2(-210, 14); bar.add_child(root)
	var nm := Label.new(); nm.text = "ASHEN TITAN"; nm.position = Vector2(0, -2); nm.add_theme_font_size_override("font_size", 16)
	nm.add_theme_color_override("font_color", Color(1, 0.75, 0.45)); root.add_child(nm)
	var bg := ColorRect.new(); bg.color = Color(0.08, 0.04, 0.03, 0.85); bg.position = Vector2(0, 20); bg.size = Vector2(420, 14); root.add_child(bg)
	bar_fill = ColorRect.new(); bar_fill.color = Color(0.95, 0.32, 0.08); bar_fill.position = Vector2(0, 20); bar_fill.size = Vector2(420, 14); root.add_child(bar_fill)
	for f in [0.66, 0.33]:
		var n := ColorRect.new(); n.color = Color(1, 0.95, 0.8); n.position = Vector2(420 * f - 1, 17); n.size = Vector2(2, 20); root.add_child(n)
	card = Label.new(); card.text = "ASHEN TITAN\nHeart of the Volcano"; card.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	card.set_anchors_preset(Control.PRESET_CENTER); card.position = Vector2(-300, 40); card.size = Vector2(600, 120)
	card.add_theme_font_size_override("font_size", 44); card.add_theme_color_override("font_color", Color(1, 0.6, 0.25))
	card.add_theme_color_override("font_outline_color", Color(0.1, 0.02, 0)); card.add_theme_constant_override("outline_size", 10)
	card.visible = false; cl.add_child(card)
	qlabel = Label.new(); qlabel.position = Vector2(12, 205); qlabel.visible = false; qlabel.add_theme_font_size_override("font_size", 14)
	qlabel.add_theme_color_override("font_color", Color(1, 0.85, 0.5)); qlabel.add_theme_constant_override("outline_size", 6); cl.add_child(qlabel)

func _card(on: bool) -> void:
	card.visible = on
	if on: card.modulate.a = 0.0; create_tween().tween_property(card, "modulate:a", 1.0, 0.6)
