extends Node3D
# Varnethryl Godot test 2: main town from buildings.js BUILDING_DEFS (cx,cz * PK=2.8), Beth r3 art,
# terrain, day/night, quality tiers Low/Medium/High/Ultra (Forward+).

const PK := 2.8
const CITY_HALF := 185.0
const VERSION := "3"
const DEFS := [
	["guildhall",0,-21,0.0,"Guild Hall"], ["library",-24,-27,0.0,"Grand Library"], ["townhall",23,-26,0.0,"Town Hall"],
	["mage",-44,-31,0.0,"Mage Academy"], ["treasury",41,-27,0.0,"Treasury"], ["keep",0,-48,0.0,"Castle Keep"],
	["observatory",-41,-46,0.0,"Observatory"], ["crypt",43,-45,0.0,"Crypt"], ["market",-24,-6,PI/2,"Market Provisioner"],
	["apothecary",-24,9,PI/2,"Apothecary"], ["bakery",-24,21.5,PI/2,"Bakery"], ["inn",24,-8,-PI/2,"Inn"],
	["smithy",24,7,-PI/2,"Blacksmith"], ["temple",46,-8,-PI/2,"Temple"], ["training",45,11,-PI/2,"Training Hall"],
	["colosseum",42,38,0.0,"Colosseum"], ["thieves",-36.5,8,0.0,"Thieves' Den"], ["farmhouse",-42,-9,0.0,"Farmhouse"],
	["barn",-51,21,PI/2,"Barn"], ["stables",-24,42,0.0,"Stables"], ["windmill",20,46,0.0,"Windmill"],
	["house1",-9,19,PI,"Village House"], ["house2",9,19,PI,"Village House"], ["house3",-9,31,PI,"Village House"], ["house4",9,31,PI,"Village House"],
]
const CHIMNEYS := ["house1","house2","house3","house4","bakery","inn","smithy","farmhouse","thieves"]
const PORT := Vector2(-425.6, 392)
const ROADS := [
	[[0,194],[-65,204],[-145,219],[-211,220],[-269,231],[-336,269],[-387,322],[-425.6,375]],
	[[0,-194],[-10,-247],[-42,-283],[-101,-327],[-99,-391],[-68,-439],[-8,-463],[62,-446],[95,-412],[105,-360]],
	[[-558,-6],[-474,-12],[-398,-7],[-322,0],[-270,6],[-232,4],[-185,0]],
	[[-315,0],[-305,-67],[-313,-132],[-330,-203],[-366,-273],[-315,-284]],
	[[185,0],[264,-3],[335,0],[421,-2],[500,0],[558,-7]],
	[[345,0],[377,62],[387,127],[354,190],[309,247],[285,311],[304,356],[269,315],[214,259],[150,225],[76,200],[0,194]],
	[[0,194],[5,265],[9,344],[0,440],[-6,558]],
]
const TIERS := ["Low", "Medium", "High", "Ultra"]

var tier := 2
var fps_cap := 60
var f_btn: Button
var b_btn: Button
var bench_label: Label
var bench_running := false
var ft_acc := 0.0
var ft_n := 0
var ft_max := 0.0
var ft_txt := ""
var probe: ReflectionProbe
var time_mode := 0          # index into TIME_PRESETS last chosen
var speed_x := 1.0
const TIME_PRESETS := [["Morning", 7.5], ["Noon", 12.0], ["Sunset", 18.2], ["Night", 22.5]]
const DAY_SECONDS := 1200.0   # full cycle = 20 real minutes
var s_btn: Button
var tod := 10.0              # hours
var hero: CharacterBody3D
var hero_vis: Node3D
var pip: Node3D
var cam_pivot: Node3D
var cam_arm: SpringArm3D
var cam: Camera3D
var yaw := 0.0
var pitch := -0.35
var buildings := []
var gate_towers := []
var gate_lods := []
var windmill_blades := []
var plaza_glow := []
var tree_lods := []         # [mmi, lod]
var hi_terrain := []        # [node, lod]
var cur_suffix := "?"
var blockers := []           # [Vector2 center, radius]
var blades: Node3D
var hud_label: Label
var where_label: Label
var q_btn: Button
var t_btn: Button
var joy_vec := Vector2.ZERO
var joy_touch := -1
var cam_touch := -1
var joy_center := Vector2.ZERO
var joy_base: Control
var joy_knob: Control
var walk_t := 0.0
var limbs := []
var bench := false
var rng := RandomNumberGenerator.new()
var noise := FastNoiseLite.new()
var env: Environment
var sun: DirectionalLight3D
var sky_mat: ProceduralSkyMaterial
var emissive_mats := []
var lamp_lights := []        # [OmniLight3D, min_tier]
var glow_mm: Array = []      # lantern glow multimeshes
var glow_mat: StandardMaterial3D
var grass_chunks := []
var fx_day := []             # [node, min_tier]
var fx_night := []
var fx_any := []
var tree_mmis := []
var terrain_lods := []       # [node, lod]
var shot_dir := "user://"

func _ready() -> void:
	rng.seed = 1905
	noise.seed = 7; noise.frequency = 0.0035; noise.fractal_octaves = 4
	var args := OS.get_cmdline_user_args()
	bench = args.has("--bench")
	_load_settings()
	_env()
	_terrain()
	_roads()
	_fountain()
	_pond()
	_walls_and_gate()
	for d in DEFS: _building(d)
	_dressing()
	_hi_terrain()
	_showcase()
	_foliage()
	_grass()
	_hero()
	_fx()
	_hud()
	apply_quality()
	if bench: _run_bench()

# ---------- settings ----------
func _load_settings() -> void:
	var cf := ConfigFile.new()
	if cf.load("user://settings.cfg") == OK:
		tier = int(cf.get_value("gfx", "tier3", 2)); time_mode = int(cf.get_value("gfx", "time", 0)) % 4
		fps_cap = int(cf.get_value("gfx", "fps", 60))

func _save_settings() -> void:
	var cf := ConfigFile.new(); cf.set_value("gfx", "tier3", tier); cf.set_value("gfx", "fps", fps_cap); cf.set_value("gfx", "time", time_mode); cf.save("user://settings.cfg")

# ---------- terrain ----------
func height(x: float, z: float) -> float:
	var r := Vector2(x, z).length()
	if r < 215.0: return 0.0
	var ld := Vector2(x, z).distance_to(LAKE)
	if ld < 100.0: return lerp(-4.0, _height_raw(x, z, r), smoothstep(45.0, 100.0, ld))
	return _height_raw(x, z, r)

func _height_raw(x: float, z: float, r: float) -> float:
	var t := smoothstep(215.0, 340.0, r)
	var n := noise.get_noise_2d(x, z) * 0.5 + 0.5
	var h := t * (4.0 + 30.0 * n) + smoothstep(430.0, 650.0, r) * 55.0 * (0.6 + n)
	# keep roads gentle: pull terrain down near outskirt roads
	var rd := _road_dist(Vector2(x, z))
	h *= lerp(0.35, 1.0, smoothstep(6.0, 40.0, rd))
	return h

func _road_dist(p: Vector2) -> float:
	var best := 1e9
	for r in ROADS:
		for i in range(1, r.size()):
			var a := Vector2(r[i-1][0], r[i-1][1]); var b := Vector2(r[i][0], r[i][1])
			var ab := b - a; var t: float = clamp((p - a).dot(ab) / max(ab.length_squared(), 0.001), 0.0, 1.0)
			best = min(best, p.distance_to(a + ab * t))
	return best

func _terrain() -> void:
	var N := 140; var S := 1400.0; var step := S / N
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var hs := PackedFloat32Array(); hs.resize((N + 1) * (N + 1))
	for j in N + 1:
		for i in N + 1:
			hs[j * (N + 1) + i] = height(-S / 2 + i * step, -S / 2 + j * step)
	for j in N + 1:
		for i in N + 1:
			st.set_uv(Vector2(i, j)); st.add_vertex(Vector3(-S / 2 + i * step, hs[j * (N + 1) + i], -S / 2 + j * step))
	for j in N:
		for i in N:
			var a := j * (N + 1) + i
			st.add_index(a); st.add_index(a + 1); st.add_index(a + N + 1)
			st.add_index(a + 1); st.add_index(a + N + 2); st.add_index(a + N + 1)
	st.generate_normals()
	var mi := MeshInstance3D.new(); mi.mesh = st.commit()
	var m := ShaderMaterial.new(); m.shader = load("res://scripts/ground.gdshader"); mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(mi)
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var hm := HeightMapShape3D.new()
	hm.map_width = N + 1; hm.map_depth = N + 1; hm.map_data = hs; cs.shape = hm; cs.scale = Vector3(step, 1, step)
	sb.add_child(cs); add_child(sb)

func _roads() -> void:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for r in ROADS:
		var pts := []
		for i in range(1, r.size()):
			var a := Vector2(r[i-1][0], r[i-1][1]); var b := Vector2(r[i][0], r[i][1])
			var n := int(ceil(a.distance_to(b) / 4.0))
			for k in n: pts.append(a.lerp(b, float(k) / n))
		pts.append(Vector2(r[-1][0], r[-1][1]))
		for i in range(pts.size() - 1):
			var a: Vector2 = pts[i]; var b: Vector2 = pts[i + 1]
			var dir := (b - a).normalized(); var side := Vector2(-dir.y, dir.x) * 4.4
			var q := [a - side, a + side, b + side, b - side]
			var v := []
			for p in q: v.append(Vector3(p.x, height(p.x, p.y) + 0.12, p.y))
			for idx in [0, 1, 2, 0, 2, 3]:
				st.set_normal(Vector3.UP); st.set_uv(Vector2(v[idx].x, v[idx].z) * 0.25); st.add_vertex(v[idx])
	var mi := MeshInstance3D.new(); mi.mesh = st.commit()
	var m := _mat(Color(0.55, 0.49, 0.40), 0.9); m.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = m; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(mi)

# ---------- environment / lighting ----------
func _env() -> void:
	var we := WorldEnvironment.new(); env = Environment.new()
	var sky := Sky.new(); sky_mat = ProceduralSkyMaterial.new(); sky.sky_material = sky_mat
	sky_mat.sky_cover = _star_tex()
	env.background_mode = Environment.BG_SKY; env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_color = Color(0.75, 0.68, 0.58); env.ambient_light_sky_contribution = 0.55
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES; env.tonemap_exposure = 1.0; env.tonemap_white = 6.0
	env.fog_enabled = true; env.fog_density = 0.0022; env.fog_aerial_perspective = 0.5; env.fog_sky_affect = 0.25
	env.glow_enabled = true; env.glow_intensity = 0.6; env.glow_bloom = 0.08; env.glow_hdr_threshold = 1.0
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.adjustment_enabled = true; env.adjustment_contrast = 1.08; env.adjustment_saturation = 1.12
	we.environment = env; add_child(we)
	sun = DirectionalLight3D.new(); sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.shadow_bias = 0.03; sun.shadow_normal_bias = 1.0
	add_child(sun)

func _star_tex() -> ImageTexture:
	var w := 2048; var h := 1024
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8); img.fill(Color(0, 0, 0, 0))
	for i in 2600:
		var x := rng.randi() % w; var y := rng.randi() % (h / 2)
		var b := pow(rng.randf(), 3.0)
		var c := Color(0.8 + 0.2 * b, 0.85 + 0.15 * b, 1.0, 0.35 + 0.65 * b)
		img.set_pixel(x, y, c)
		if b > 0.7: img.set_pixel((x + 1) % w, y, c * 0.6); img.set_pixel(x, y + 1, c * 0.6)
	return ImageTexture.create_from_image(img)

func _set_time(h: float) -> void:
	tod = fposmod(h, 24.0)
	var day := clampf(sin((tod - 6.0) / 12.0 * PI), -1.0, 1.0)      # 1 at noon, 0 at 6/18, <0 night
	var elev := day * 62.0
	var night := day < 0.0
	var sunset := 1.0 - smoothstep(0.0, 0.35, abs(day))
	if night:
		sun.rotation_degrees = Vector3(-35, -35 + tod * 5, 0)     # moon
		sun.light_color = Color(0.55, 0.65, 1.0); sun.light_energy = 0.22
		sun.light_volumetric_fog_energy = 0.4
	else:
		sun.rotation_degrees = Vector3(-max(elev, 4.0), -100 + (tod - 6.0) * 15.0, 0)
		sun.light_color = Color(1.0, 0.95, 0.86).lerp(Color(1.0, 0.65, 0.4), sunset)
		sun.light_energy = lerp(1.4, 0.9, sunset)
		sun.light_volumetric_fog_energy = lerp(1.0, 3.0, sunset)
	var nf := smoothstep(0.05, -0.25, day)    # 0 day -> 1 night
	sky_mat.sky_top_color = Color(0.22, 0.45, 0.85).lerp(Color(0.3, 0.32, 0.6), sunset).lerp(Color(0.01, 0.02, 0.06), nf)
	sky_mat.sky_horizon_color = Color(0.75, 0.82, 0.9).lerp(Color(1.0, 0.66, 0.45), sunset).lerp(Color(0.05, 0.07, 0.14), nf)
	sky_mat.ground_horizon_color = sky_mat.sky_horizon_color
	sky_mat.ground_bottom_color = Color(0.2, 0.22, 0.2).lerp(Color(0.01, 0.01, 0.02), nf)
	sky_mat.sun_angle_max = 25.0; sky_mat.sun_curve = 0.1
	sky_mat.sky_cover_modulate = Color(1, 1, 1, nf)
	env.ambient_light_energy = lerp(0.9, 0.25, nf)
	env.fog_light_color = sky_mat.sky_horizon_color
	env.volumetric_fog_albedo = Color(0.9, 0.9, 0.95).lerp(Color(1.0, 0.7, 0.5), sunset)
	env.tonemap_exposure = lerp(1.0, 1.5, nf)
	var em: float = lerp(0.0, 3.0, smoothstep(0.25, -0.1, day)) if tier > 0 else 0.0
	for m in emissive_mats: m.emission_energy_multiplier = em
	glow_mat.emission_energy_multiplier = em * 2.0
	for gm in glow_mm: gm.visible = em > 0.05
	var lamp_on := em > 0.3
	for l in lamp_lights:
		l[0].visible = lamp_on and tier >= l[1]
		l[0].shadow_enabled = false
	for f in fx_night: f[0].emitting = night and tier >= f[1]; f[0].visible = f[0].emitting
	for f in fx_day: f[0].emitting = not night and tier >= f[1]; f[0].visible = f[0].emitting

func apply_quality() -> void:
	# Test 3: Mobile renderer for every tier. Cost drivers kept in check: render scale + FSR,
	# one shadowed light (the sun) with short distance, no shadowed lamps, LOD/HLOD everywhere.
	var vp := get_viewport()
	Engine.max_fps = fps_cap
	RenderingServer.directional_shadow_atlas_set_size([1024, 2048, 2048, 4096][tier], true)
	RenderingServer.directional_soft_shadow_filter_set_quality([RenderingServer.SHADOW_QUALITY_HARD, RenderingServer.SHADOW_QUALITY_SOFT_VERY_LOW, RenderingServer.SHADOW_QUALITY_SOFT_LOW, RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM][tier])
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = [30.0, 45.0, 60.0, 100.0][tier]
	sun.directional_shadow_mode = [DirectionalLight3D.SHADOW_ORTHOGONAL, DirectionalLight3D.SHADOW_ORTHOGONAL, DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS, DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS][tier]
	sun.light_angular_distance = 0.0
	sun.shadow_blur = [0.5, 1.0, 1.5, 1.5][tier]
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if tier >= 1 else Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = [0.5, 0.6, 0.7, 0.85][tier]
	vp.fsr_sharpness = 0.3
	vp.msaa_3d = Viewport.MSAA_2X if tier == 3 else Viewport.MSAA_DISABLED
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED if tier == 3 else Viewport.SCREEN_SPACE_AA_FXAA
	env.glow_enabled = tier >= 1
	env.ssao_enabled = false; env.ssil_enabled = false; env.ssr_enabled = false; env.sdfgi_enabled = false
	env.volumetric_fog_enabled = false
	env.fog_enabled = true; env.fog_density = 0.0028
	if probe: probe.visible = tier >= 1
	for c in grass_chunks:
		var cap := int(c.multimesh.instance_count * [0.0, 0.2, 0.35, 0.7][tier])
		c.multimesh.visible_instance_count = cap; c.visible = cap > 0
		c.visibility_range_end = [0.0, 30.0, 40.0, 70.0][tier]
		c.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
	for f in fx_any: f[0].visible = tier >= f[1]; f[0].emitting = tier >= f[1]
	_swap_buildings()
	var tr: Array = [[[-1, -1], [0, 40], [40, 0]], [[-1, -1], [0, 70], [70, 0]], [[0, 30], [30, 120], [120, 0]], [[0, 50], [50, 200], [200, 0]]][tier]
	for t in tree_lods:
		var r: Array = tr[t[1]]; var n2: GeometryInstance3D = t[0]
		n2.visible = r[0] >= 0
		n2.visibility_range_begin = max(r[0], 0); n2.visibility_range_end = max(r[1], 0)
		n2.visibility_range_begin_margin = 4.0; n2.visibility_range_end_margin = 4.0
		var casts: bool = t[1] == 0 or (t[1] == 1 and tier <= 1)
		n2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if casts else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var trr: Array = [[[-1, -1], [-1, -1], [0, 0]], [[-1, -1], [0, 350], [350, 0]], [[-1, -1], [0, 450], [450, 0]], [[0, 300], [300, 650], [650, 0]]][tier]
	for t in hi_terrain:
		var r: Array = trr[t[1]]; var n3: GeometryInstance3D = t[0]
		n3.visible = r[0] >= 0
		n3.visibility_range_begin = max(r[0], 0); n3.visibility_range_end = max(r[1], 0)
		n3.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if (t[1] == 0) else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if q_btn: q_btn.text = "Quality: " + TIERS[tier]
	if f_btn: f_btn.text = "FPS cap: %d" % fps_cap
	_set_time(tod)

func _mat(c: Color, rough := 0.85) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.albedo_color = c; m.roughness = rough; return m

func _water_mat() -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = load("res://scripts/water.gdshader"); return m

func _static_box(pos: Vector3, size: Vector3, rot := 0.0) -> void:
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var bs := BoxShape3D.new()
	bs.size = size; cs.shape = bs; sb.add_child(cs); sb.position = pos; sb.rotation.y = rot; add_child(sb)

func _fountain() -> void:
	var stone := _mat(Color(0.74, 0.72, 0.68))
	var basin := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 6.5; cm.bottom_radius = 6.8; cm.height = 0.9; cm.radial_segments = 48
	cm.material = stone; basin.mesh = cm; basin.position.y = 0.45; add_child(basin)
	var w := MeshInstance3D.new(); var cw := PlaneMesh.new(); cw.size = Vector2(12, 12); cw.subdivide_width = 24; cw.subdivide_depth = 24
	var wm := _water_mat(); wm.set_shader_parameter("wave", 0.015); cw.material = wm; w.mesh = cw; w.position.y = 0.86; add_child(w)
	var mask := MeshInstance3D.new(); var mk := CylinderMesh.new(); mk.top_radius = 9.0; mk.bottom_radius = 9.0; mk.height = 0.01  # hide square corners
	mk.material = stone; mask.visible = false; add_child(mask)
	var col := MeshInstance3D.new(); var c2 := CylinderMesh.new(); c2.top_radius = 0.7; c2.bottom_radius = 1.0; c2.height = 3.2; c2.material = stone
	col.mesh = c2; col.position.y = 1.6; add_child(col)
	var lion := MeshInstance3D.new(); var sp := SphereMesh.new(); sp.radius = 1.0; sp.height = 1.6
	var lm := _mat(Color(0.12, 0.29, 0.6), 0.25); lm.metallic = 0.4; sp.material = lm
	lion.mesh = sp; lion.position.y = 3.8; add_child(lion)
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var cy := CylinderShape3D.new(); cy.radius = 6.8; cy.height = 2.0; cs.shape = cy; sb.add_child(cs); add_child(sb)
	blockers.append([Vector2.ZERO, 9.0])
	probe = ReflectionProbe.new(); probe.size = Vector3(90, 30, 90); probe.position = Vector3(0, 6, 0)
	probe.update_mode = ReflectionProbe.UPDATE_ONCE; probe.box_projection = true; probe.max_distance = 120
	add_child(probe)
	for i in 8:
		var a := i / 8.0 * TAU + PI / 8.0
		var lp := Vector3(cos(a) * 30.0, 0, sin(a) * 30.0)
		var post := _place_glb("res://assets/dressing/lantern_post.glb", lp, -a)
		var top: AABB = _meshes(post, [])[0].get_aabb()
		var l := OmniLight3D.new(); l.position = lp + Vector3(0, top.end.y - 0.4, 0); l.light_color = Color(1.0, 0.72, 0.4)
		l.light_energy = 2.2; l.omni_range = 14.0; l.omni_attenuation = 1.3
		l.set_meta("shadow_ultra", true)
		add_child(l); lamp_lights.append([l, 2])
		plaza_glow.append(l.position)
	# spray
	var p := _particles(400, 1.6, _soft_quad(Color(0.85, 0.93, 1.0, 0.7), 0.18, false), 0)
	var pm: ParticleProcessMaterial = p.process_material
	pm.direction = Vector3(0, 1, 0); pm.spread = 18; pm.initial_velocity_min = 4.0; pm.initial_velocity_max = 5.0; pm.gravity = Vector3(0, -9.8, 0)
	p.position = Vector3(0, 4.4, 0); add_child(p); fx_any.append([p, 1])

func _pond() -> void:
	var w := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(40, 26); pm.subdivide_width = 40; pm.subdivide_depth = 26
	pm.material = _water_mat(); w.mesh = pm; w.position = Vector3(-110, 0.08, 110); add_child(w)
	var edge := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = Vector3(43, 0.3, 29); bm.material = _mat(Color(0.4, 0.36, 0.3))
	edge.mesh = bm; edge.position = Vector3(-110, -0.12, 110); add_child(edge)
	_static_box(Vector3(-110, 0.5, 110), Vector3(40, 1, 26))
	blockers.append([Vector2(-110, 110), 24.0])

func _walls_and_gate() -> void:
	var stone := _mat(Color(0.62, 0.6, 0.56))
	var H := 8.0; var T := 3.0
	var runs := [[Vector3(0, H/2, -CITY_HALF), Vector3(2*CITY_HALF, H, T)],
		[Vector3(-CITY_HALF, H/2, 0), Vector3(T, H, 2*CITY_HALF)], [Vector3(CITY_HALF, H/2, 0), Vector3(T, H, 2*CITY_HALF)],
		[Vector3(-(CITY_HALF+7)/2 - 3.5, H/2, CITY_HALF), Vector3(CITY_HALF - 7, H, T)], [Vector3((CITY_HALF+7)/2 + 3.5, H/2, CITY_HALF), Vector3(CITY_HALF - 7, H, T)]]
	for r in runs:
		var mi := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = r[1]; bm.material = stone; mi.mesh = bm; mi.position = r[0]; add_child(mi)
		_static_box(r[0], r[1])
	for s in [-1, 1]:
		var g := _place_glb("res://assets/buildings/bld_gate_tower.glb", Vector3(s * 8.2 * 1.7, 0, CITY_HALF - 1.2), PI)
		_add_trimesh(g)
		for mi in _meshes(g, []): mi.visible = false
		gate_towers.append(g)
	var arch := MeshInstance3D.new(); var am := BoxMesh.new(); am.size = Vector3(18, 2.0, 4); am.material = stone; arch.mesh = am; arch.position = Vector3(0, 9, CITY_HALF); add_child(arch)

func _place_glb(path: String, pos: Vector3, rot: float) -> Node3D:
	var n: Node3D = load(path).instantiate(); n.position = pos; n.rotation.y = rot; add_child(n); return n

func _meshes(n: Node, out: Array) -> Array:
	if n is MeshInstance3D: out.append(n)
	for c in n.get_children(): _meshes(c, out)
	return out

func _add_trimesh(n: Node3D, skip := "roof") -> void:
	for mi in _meshes(n, []):
		if String(mi.name).to_lower().contains(skip) or String(mi.get_parent().name).to_lower().contains(skip): continue
		mi.create_trimesh_collision()

func _building(d: Array) -> void:
	var id: String = d[0]; var pos := Vector3(float(d[1]) * PK, 0, float(d[2]) * PK); var rot: float = d[3]
	var n := _place_glb("res://assets/buildings/bld_%s.glb" % id, pos, rot)
	_add_trimesh(n)
	var aabb := AABB(); var first := true
	for mi in _meshes(n, []):
		var a: AABB = (n.global_transform.affine_inverse() * mi.global_transform) * mi.get_aabb()
		if first: aabb = a; first = false
		else: aabb = aabb.merge(a)
	for mi in _meshes(n, []): mi.visible = false      # r3 shell = collision proxy; visuals come from Beth r4 hi tiers
	buildings.append({"id": id, "name": d[4], "node": n, "roof": null, "roofs": [], "lods": [], "vis": null, "aabb": aabb})
	blockers.append([Vector2(pos.x, pos.z), max(aabb.size.x, aabb.size.z) * 0.55 + 2.0])
	# warm interior light by the door, night only (Ultra)
	var door_w: Vector3 = n.global_transform * Vector3(0, 2.6, aabb.end.z + 0.8)
	var l := OmniLight3D.new(); l.position = door_w; l.light_color = Color(1.0, 0.7, 0.4); l.light_energy = 2.0; l.omni_range = 9.0
	l.shadow_enabled = false; l.distance_fade_enabled = true; l.distance_fade_begin = 60; l.distance_fade_length = 20
	add_child(l); lamp_lights.append([l, 3])

func _swap_buildings() -> void:
	# HLOD: every building carries all three of Beth's tiers; the tier only changes the distance bands.
	if cur_suffix == "?":
		cur_suffix = "hlod"
		for b in buildings:
			b.lods = []; b.roofs = []
			for suf in ["", "_lod1", "_lod2"]:
				var v: Node3D = load("res://assets/hi/buildings/bld_%s%s.glb" % [b.id, suf]).instantiate()
				b.node.add_child(v); b.lods.append(v)
				var rf = v.find_child("roof", true, false)
				if rf: b.roofs.append(rf)
				if b.id == "windmill": windmill_blades.append(v.find_child("blades", true, false))
			b.vis = b.lods[0]
		for g in gate_towers:
			var gl := []
			for suf in ["", "_lod1", "_lod2"]:
				var v2: Node3D = load("res://assets/hi/buildings/bld_gate_tower%s.glb" % suf).instantiate(); g.add_child(v2); gl.append(v2)
			gate_lods.append(gl)
		_collect_emissive()
	var bands: Array = [[[-1, -1], [-1, -1], [0, 0]], [[-1, -1], [0, 70], [70, 0]], [[0, 55], [55, 140], [140, 0]], [[0, 120], [120, 260], [260, 0]]][tier]
	var sets := []
	for b in buildings: sets.append(b.lods)
	for gl in gate_lods: sets.append(gl)
	for lods in sets:
		for i in 3:
			var r: Array = bands[i]
			for mi in _meshes(lods[i], []):
				mi.visible = r[0] >= 0
				mi.visibility_range_begin = max(r[0], 0); mi.visibility_range_end = max(r[1], 0)
				mi.visibility_range_begin_margin = 3.0; mi.visibility_range_end_margin = 3.0
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if i == 2 else GeometryInstance3D.SHADOW_CASTING_SETTING_ON

func _collect_emissive() -> void:
	var seen := {}
	emissive_mats.clear()
	for b in buildings:
		for lv in b.lods:
			for mi in _meshes(lv, []):
				for i in mi.mesh.get_surface_count():
					var m = mi.get_active_material(i)
					if m is BaseMaterial3D and m.emission_texture and not seen.has(m):
						seen[m] = true; m.emission_enabled = true; m.emission = Color(1.0, 0.72, 0.38); emissive_mats.append(m)

# ---------- Beth dressing / decals ----------
func _mesh_parts(path: String) -> Array:
	var n: Node = load(path).instantiate()
	var out := []
	for mi in _meshes(n, []): out.append([mi.mesh, mi.transform])
	n.free()
	return out

func _multimesh(path: String, xf: Array, shadow := true, vis_end := 0.0) -> Array:
	var made := []
	for part in _mesh_parts(path):
		var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = part[0]; mm.instance_count = xf.size()
		for i in xf.size(): mm.set_instance_transform(i, xf[i] * part[1])
		var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if vis_end > 0: mmi.visibility_range_end = vis_end
		add_child(mmi); made.append(mmi)
	return made

func _load_items(f: String) -> Array:
	var j = JSON.parse_string(FileAccess.get_file_as_string("res://assets/data/" + f))
	return j["items"]

func _dressing() -> void:
	var groups := {}
	var items := _load_items("PLACEMENT_dressing_town.json") + _load_items("PLACEMENT_dressing_roads.json") + _load_items("PLACEMENT_decals.json")
	for it in items:
		var file: String = it["file"]
		if file.contains("wall_cap") or file.contains("puddle"): continue
		var p: Array = it["position"]; var r: Array = it["rotation"]; var s: Array = it["scale"]
		var y: float = height(p[0], p[2]) if p[1] == null else float(p[1])
		if file.contains("decals/") and (file.contains("ground") or file.contains("puddle") or file.contains("leaves")): y += 0.03
		var b := Basis.from_euler(Vector3(r[0], r[1], r[2])).scaled(Vector3(s[0], s[1], s[2]))
		if not groups.has(file): groups[file] = []
		groups[file].append(Transform3D(b, Vector3(p[0], y, p[2])))
	glow_mat = StandardMaterial3D.new(); glow_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	glow_mat.albedo_color = Color(1.0, 0.8, 0.45); glow_mat.emission_enabled = true; glow_mat.emission = Color(1.0, 0.7, 0.35)
	var glow_mesh := SphereMesh.new(); glow_mesh.radius = 0.16; glow_mesh.height = 0.32; glow_mesh.radial_segments = 8; glow_mesh.rings = 4; glow_mesh.material = glow_mat
	var pg := []
	for gp in plaza_glow: pg.append(Transform3D(Basis(), gp))
	if pg.size() > 0:
		var pmm := MultiMesh.new(); pmm.transform_format = MultiMesh.TRANSFORM_3D; pmm.mesh = glow_mesh; pmm.instance_count = pg.size()
		for i in pg.size(): pmm.set_instance_transform(i, pg[i])
		var pmi := MultiMeshInstance3D.new(); pmi.multimesh = pmm; pmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(pmi); glow_mm.append(pmi)
	for file in groups:
		var xf: Array = groups[file]
		var is_decal: bool = file.begins_with("decals/")
		var small: bool = file.contains("curb") or file.contains("cobble") or is_decal or file.contains("rubble")
		_multimesh("res://assets/" + file, xf, not small, 160.0 if small else 300.0)
		if file.contains("lantern"):
			var parts := _mesh_parts("res://assets/" + file)
			var top: AABB = parts[0][0].get_aabb()
			var head := Vector3(top.get_center().x, top.end.y - 0.35, top.get_center().z)
			var gx := []
			for t in xf:
				gx.append(Transform3D(Basis(), t * head))
				if file.contains("lantern_post") or rng.randf() < 0.4:
					var l := OmniLight3D.new(); l.position = t * head; l.light_color = Color(1.0, 0.72, 0.4)
					l.light_energy = 1.6; l.omni_range = 11.0 if file.contains("post") else 7.0; l.omni_attenuation = 1.4
					l.distance_fade_enabled = true; l.distance_fade_begin = 70; l.distance_fade_length = 20
					add_child(l); lamp_lights.append([l, 2 if file.contains("post") else 3])
			var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = glow_mesh; mm.instance_count = gx.size()
			for i in gx.size(): mm.set_instance_transform(i, gx[i])
			var gmi := MultiMeshInstance3D.new(); gmi.multimesh = mm; gmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(gmi); glow_mm.append(gmi)

func _lod_instances(base: String, xf: Transform3D, shadow: bool) -> void:
	for lod in 3:
		var path: String = base + ["", "_lod1", "_lod2"][lod] + ".glb"
		if not ResourceLoader.exists(path): continue
		var n: Node3D = load(path).instantiate(); n.transform = xf; add_child(n)
		for mi in _meshes(n, []):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if (shadow and lod == 0) else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			hi_terrain.append([mi, lod])

const LAKE := Vector2(250, -200)
const SHORE_YAW := PI
func _hi_terrain() -> void:
	var T := "res://assets/hi/terrain/"
	for i in 26:
		var a := i / 26.0 * TAU + rng.randf_range(-0.07, 0.07)
		var r := rng.randf_range(520, 640)
		var p := Vector2(cos(a), sin(a)) * r
		if _road_dist(p) < 70 or p.distance_to(Vector2(405, -402)) < 150: continue
		var k: String = ["peak_snow_hi", "peak_bare_hi", "peak_snow_hi", "peak_bare_hi"][i % 4]
		var sc := rng.randf_range(1.3, 2.0)
		_lod_instances(T + k, Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(sc, sc * rng.randf_range(0.9, 1.2), sc)), Vector3(p.x, height(p.x, p.y) - 6.0, p.y)), true)
	_lod_instances(T + "volcano_flank_hi", Transform3D(Basis().scaled(Vector3(1.6, 1.6, 1.6)), Vector3(405, height(405, -402) - 3.0, -402)), true)
	for i in 18:
		var a2 := rng.randf() * TAU; var r2 := rng.randf_range(250, 460); var p2 := Vector2(cos(a2), sin(a2)) * r2
		if _road_dist(p2) < 30 or p2.distance_to(LAKE) < 70: continue
		var k2: String = "boulder_strata_hi"
		var s2 := rng.randf_range(0.5, 1.0) if k2.begins_with("cliff") else rng.randf_range(0.8, 1.6)
		_lod_instances(T + k2, Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s2, s2, s2)), Vector3(p2.x, height(p2.x, p2.y) - 1.0, p2.y)), true)
	# lake with Beth's shore pieces, waterline at y=0
	var w := MeshInstance3D.new(); var pm := CylinderMesh.new(); pm.top_radius = 66; pm.bottom_radius = 66; pm.height = 0.2; pm.radial_segments = 64; pm.rings = 1
	pm.material = _water_mat(); w.mesh = pm; w.position = Vector3(LAKE.x, -0.1, LAKE.y); add_child(w)
	for i in 12:
		var a3 := i / 12.0 * TAU
		var p3 := LAKE + Vector2(cos(a3), sin(a3)) * 60.0
		var b3 := Basis(Vector3.UP, atan2(p3.x - LAKE.x, p3.y - LAKE.y) + SHORE_YAW)
		_lod_instances(T + "shore_edge_hi", Transform3D(b3, Vector3(p3.x, 0, p3.y)), false)

func _mountains_old() -> void:
	var kinds := ["mountain_peak_snow", "mountain_peak_bare", "mountain_peak_snow", "mountain_peak_bare", "cliff_ridge_60m"]
	var placed := []
	for i in 30:
		var a := i / 30.0 * TAU + rng.randf_range(-0.08, 0.08)
		var r := rng.randf_range(470, 620)
		var p := Vector2(cos(a), sin(a)) * r
		if _road_dist(p) < 45: continue
		placed.append([kinds[i % kinds.size()], p, rng.randf_range(1.6, 3.2)])
	placed.append(["volcano_cone_flank", Vector2(405, -402), 2.6])
	for i in 14:
		var a2 := rng.randf() * TAU; var r2 := rng.randf_range(250, 420); var p2 := Vector2(cos(a2), sin(a2)) * r2
		if _road_dist(p2) < 25: continue
		placed.append([["grass_mound", "scree_slope", "rock_arch", "cliff_ridge_60m"][i % 4], p2, rng.randf_range(0.9, 1.5)])
	var by := {}
	for m in placed:
		var p: Vector2 = m[1]; var s: float = m[2]
		var t := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.9, 1.3), s)), Vector3(p.x, height(p.x, p.y) - 2.0, p.y))
		if not by.has(m[0]): by[m[0]] = []
		by[m[0]].append(t)
	for k in by:
		for lod in 3:
			var path: String = "res://assets/terrain/%s%s.glb" % [k, ["", "_lod1", "_lod2"][lod]]
			if not ResourceLoader.exists(path):
				if lod == 2: path = "res://assets/terrain/%s_lod1.glb" % k
				else: continue
			for mmi in _multimesh(path, by[k], lod == 0):
				terrain_lods.append([mmi, lod])

# ---------- foliage ----------
func _ok_spot(p: Vector2, pad: float) -> bool:
	if abs(p.x) < 7 + pad and p.y > -150 and p.y < 190: return false
	if abs(p.y) < 6 + pad and abs(p.x) < 190: return false
	if p.length() < 40 + pad: return false
	if abs(p.length() - 194.0) < 7 + pad: return false
	if abs(p.y - 38) < 4 + pad or abs(p.y - 71) < 4 + pad: return false
	if (abs(p.x - 67) < 4 + pad or abs(p.x + 67) < 4 + pad) and abs(p.y) < 120: return false
	if abs(p.x) > CITY_HALF - 4 and abs(p.x) < CITY_HALF + 4: return false
	if abs(p.y) > CITY_HALF - 4 and abs(p.y) < CITY_HALF + 4: return false
	for b in blockers:
		if p.distance_to(b[0]) < b[1] + pad: return false
	if p.length() > 200 and _road_dist(p) < 8 + pad: return false
	return true

func _wind_mat_for(mesh: Mesh, sway: float) -> Mesh:
	# duplicate the mesh and give every surface its own wind material (fixes shared-override bug)
	var m2: Mesh = mesh.duplicate()
	for i in m2.get_surface_count():
		var src = m2.surface_get_material(i)
		var m := ShaderMaterial.new(); m.shader = load("res://scripts/wind.gdshader")
		if src is BaseMaterial3D:
			m.set_shader_parameter("albedo_tex", src.albedo_texture)
			m.set_shader_parameter("tint", src.albedo_color)
		m.set_shader_parameter("sway", sway)
		m2.surface_set_material(i, m)
	return m2

func _scatter(path: String, count: int, area: float, minr: float, sway: float, smin: float, smax: float, shadow: bool, collide := false) -> Array:
	var xf := []
	var tries := 0
	while xf.size() < count and tries < count * 40:
		tries += 1
		var p := Vector2(rng.randf_range(-area, area), rng.randf_range(-area, area))
		if p.length() < minr or not _ok_spot(p, 2.0): continue
		var s := rng.randf_range(smin, smax)
		xf.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(p.x, height(p.x, p.y) - 0.05, p.y)))
	for part in _mesh_parts(path):
		var mesh: Mesh = part[0] if sway == 0.0 else _wind_mat_for(part[0], sway)
		var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = mesh; mm.instance_count = xf.size()
		for i in xf.size(): mm.set_instance_transform(i, xf[i] * part[1])
		var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mmi.visibility_range_end = 450.0 if shadow else 120.0
		add_child(mmi)
		if shadow: tree_mmis.append(mmi)
	if collide:
		for t in xf:
			if t.origin.length() < CITY_HALF: _static_box(t.origin + Vector3(0, 1.5, 0), Vector3(0.7, 3, 0.7))
	return xf

var blossom_xf := []
func _pick(count: int, area: float, minr: float, smin: float, smax: float, maxr := 1e9) -> Array:
	var xf := []; var tries := 0
	while xf.size() < count and tries < count * 40:
		tries += 1
		var p := Vector2(rng.randf_range(-area, area), rng.randf_range(-area, area))
		if p.length() < minr or p.length() > maxr or not _ok_spot(p, 2.0) or p.distance_to(LAKE) < 62: continue
		var s := rng.randf_range(smin, smax)
		xf.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(p.x, height(p.x, p.y) - 0.05, p.y)))
	return xf

func _trees_hi(kind: String, xf: Array, sway: float, collide: bool, chunk := 140.0) -> void:
	var chunks := {}
	for t in xf:
		var key := Vector2i(floori(t.origin.x / chunk), floori(t.origin.z / chunk))
		if not chunks.has(key): chunks[key] = []
		chunks[key].append(t)
	for lod in 3:
		var path := "res://assets/hi/trees/%s_hi%s.glb" % [kind, ["", "_lod1", "_lod2"][lod]]
		if not ResourceLoader.exists(path): continue
		for part in _mesh_parts(path):
			var mesh := _wind_mat_for(part[0], sway if lod < 2 else 0.0)
			for key in chunks:
				var arr: Array = chunks[key]
				var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = mesh; mm.instance_count = arr.size()
				for i in arr.size(): mm.set_instance_transform(i, arr[i] * part[1])
				var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm
				mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if lod < 2 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				add_child(mmi); tree_lods.append([mmi, lod])
	if collide:
		for t in xf:
			if t.origin.length() < CITY_HALF: _static_box(t.origin + Vector3(0, 1.5, 0), Vector3(0.7, 3, 0.7))

func _foliage() -> void:
	_trees_hi("oak", _pick(150, 180, 0, 0.9, 1.25), 0.04, true)
	_trees_hi("birch", _pick(60, 180, 0, 0.9, 1.2), 0.06, true)
	blossom_xf = _pick(40, 130, 0, 0.9, 1.1)
	_trees_hi("blossom", blossom_xf, 0.04, true)
	_trees_hi("oak_autumn", _pick(45, 180, 0, 0.9, 1.25), 0.04, true)
	_trees_hi("oak_deep", _pick(30, 180, 0, 0.9, 1.25), 0.04, true)
	_trees_hi("pine", _pick(650, 600, 205, 1.0, 1.6), 0.02, false, 180.0)
	_trees_hi("pine_snow", _pick(120, 650, 480, 1.1, 1.7), 0.02, false, 180.0)
	_trees_hi("oak", _pick(150, 420, 205, 1.0, 1.4, 420), 0.03, false, 180.0)
	_trees_hi("bush", _pick(200, 180, 0, 0.8, 1.3), 0.1, false)
	_trees_hi("bush_autumn", _pick(90, 180, 0, 0.8, 1.3), 0.1, false)
	for f in ["flowers_red", "flowers_yellow", "flowers_white", "flowers_purple"]:
		_scatter("res://assets/veg/%s.glb" % f, 160, 170, 0, 0.25, 0.8, 1.2, false)
	_scatter("res://assets/rocks/rock_mossy.glb", 60, 450, 205, 0.0, 1.0, 2.5, true)
	_scatter("res://assets/rocks/boulder.glb", 40, 450, 205, 0.0, 1.0, 2.0, true)

func _showcase() -> void:
	# one of every tree kind in a row west of the plaza, for close-up checks
	var kinds := ["blossom", "oak", "birch", "oak_autumn", "oak_deep", "pine", "pine_snow", "bush", "bush_autumn"]
	for i in kinds.size():
		var p := Vector3(-150 + i * 9.0, 0, 158)
		_trees_hi(kinds[i], [Transform3D(Basis(), p)], 0.04, false)
		blockers.append([Vector2(p.x, p.z), 3.0])
		_static_box(p + Vector3(0, 1.5, 0), Vector3(0.7, 3, 0.7))

func _grass() -> void:
	# one crossed-quad blade clump; chunked so frustum culling + visibility range keep it cheap
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for k in 3:
		var a := k * PI / 3.0; var dx := cos(a) * 0.09; var dz := sin(a) * 0.09
		var v := [Vector3(-dx, 0, -dz), Vector3(dx, 0, dz), Vector3(dx * 0.15, 0.42, dz * 0.15), Vector3(-dx * 0.15, 0.42, -dz * 0.15)]
		var uv := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)]
		for idx in [0, 1, 2, 0, 2, 3]: st.set_uv(uv[idx]); st.add_vertex(v[idx])
	var blade := st.commit()
	var gm := ShaderMaterial.new(); gm.shader = load("res://scripts/grass.gdshader"); blade.surface_set_material(0, gm)
	var C := 30.0
	for cx in range(-7, 7):
		for cz in range(-7, 7):
			var xf := []
			for i in 1600:
				var p := Vector2((cx + rng.randf()) * C, (cz + rng.randf()) * C)
				if p.length() > 400 or not _ok_spot(p, 0.5): continue
				var s := rng.randf_range(0.7, 1.4)
				xf.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.8, 1.5), s)), Vector3(p.x, height(p.x, p.y), p.y)))
			if xf.is_empty(): continue
			var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = blade; mm.instance_count = xf.size()
			for i in xf.size(): mm.set_instance_transform(i, xf[i])
			var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm; mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mmi.visibility_range_end = 110.0; mmi.visibility_range_end_margin = 10.0
			add_child(mmi); grass_chunks.append(mmi)

# ---------- particles ----------
func _soft_quad(c: Color, size: float, additive: bool) -> QuadMesh:
	var q := QuadMesh.new(); q.size = Vector2(size, size)
	var m := StandardMaterial3D.new()
	if additive: m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES; m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = c; m.vertex_color_use_as_albedo = true
	var g := GradientTexture2D.new(); var gr := Gradient.new(); gr.set_color(0, Color(1, 1, 1, 1)); gr.set_color(1, Color(1, 1, 1, 0))
	g.gradient = gr; g.fill = GradientTexture2D.FILL_RADIAL; g.fill_from = Vector2(0.5, 0.5); g.fill_to = Vector2(1.0, 0.5); g.width = 64; g.height = 64
	m.albedo_texture = g
	if additive: m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD; m.emission_enabled = true; m.emission = c; m.emission_energy_multiplier = 3.0
	q.material = m
	return q

func _particles(amount: int, life: float, mesh: Mesh, _t: int) -> GPUParticles3D:
	var p := GPUParticles3D.new(); p.amount = amount; p.lifetime = life; p.draw_pass_1 = mesh
	p.process_material = ParticleProcessMaterial.new(); p.visibility_aabb = AABB(Vector3(-40, -10, -40), Vector3(80, 40, 80))
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return p

func _fx() -> void:
	# chimney smoke
	for b in buildings:
		if not CHIMNEYS.has(b.id): continue
		var a: AABB = b.aabb
		var p := _particles(40, 6.0, _soft_quad(Color(0.75, 0.75, 0.78, 0.35), 1.6, false), 0)
		var pm: ParticleProcessMaterial = p.process_material
		pm.direction = Vector3(0.3, 1, 0); pm.spread = 12; pm.initial_velocity_min = 0.8; pm.initial_velocity_max = 1.3; pm.gravity = Vector3(0.25, 0.15, 0)
		pm.scale_min = 0.6; pm.scale_max = 1.2
		var sc := Curve.new(); sc.add_point(Vector2(0, 0.4)); sc.add_point(Vector2(1, 2.5)); var sct := CurveTexture.new(); sct.curve = sc; pm.scale_curve = sct
		var cr := Gradient.new(); cr.set_color(0, Color(1, 1, 1, 0.7)); cr.set_color(1, Color(1, 1, 1, 0)); var crt := GradientTexture1D.new(); crt.gradient = cr; pm.color_ramp = crt
		p.position = b.node.global_transform * Vector3(a.position.x * 0.5, a.end.y - 0.5, a.position.z * 0.4)
		add_child(p); fx_any.append([p, 2])
	# falling petals around cherry trees
	var petal := _soft_quad(Color(1.0, 0.72, 0.85, 1.0), 0.09, false)
	for i in blossom_xf.size():
		var t: Transform3D = blossom_xf[i]
		var p := _particles(30, 7.0, petal, 0)
		var pm: ParticleProcessMaterial = p.process_material
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE; pm.emission_sphere_radius = 2.0
		pm.gravity = Vector3(0.3, -0.35, 0.1); pm.initial_velocity_min = 0.1; pm.initial_velocity_max = 0.4
		pm.turbulence_enabled = true; pm.turbulence_noise_strength = 0.6; pm.turbulence_influence_min = 0.05; pm.turbulence_influence_max = 0.15
		p.position = t.origin + Vector3(0, 4.0, 0); p.visibility_range_end = 70.0
		add_child(p); fx_any.append([p, 3])
	# fireflies (night)
	for c in [Vector3(-110, 1.2, 110), Vector3(0, 1.2, 0), Vector3(-60, 1.2, 60), Vector3(60, 1.2, -90), Vector3(-25, 1.2, 40), Vector3(80, 1.2, 80)]:
		var p := _particles(70, 5.0, _soft_quad(Color(0.75, 1.0, 0.35, 1.0), 0.12, true), 0)
		var pm: ParticleProcessMaterial = p.process_material
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX; pm.emission_box_extents = Vector3(22, 1.5, 22)
		pm.gravity = Vector3.ZERO; pm.turbulence_enabled = true; pm.turbulence_noise_strength = 1.5; pm.turbulence_influence_min = 0.2; pm.turbulence_influence_max = 0.4
		var cr := Gradient.new(); cr.offsets = PackedFloat32Array([0, 0.3, 0.7, 1]); cr.colors = PackedColorArray([Color(1,1,1,0), Color(1,1,1,1), Color(1,1,1,1), Color(1,1,1,0)])
		var crt := GradientTexture1D.new(); crt.gradient = cr; pm.color_ramp = crt
		p.position = c; add_child(p); fx_night.append([p, 1])
	# sunlit dust motes around the hero (day)
	var dust := _particles(120, 6.0, _soft_quad(Color(1.0, 0.95, 0.8, 0.5), 0.04, true), 0)
	var dm: ParticleProcessMaterial = dust.process_material
	dm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX; dm.emission_box_extents = Vector3(10, 3, 10)
	dm.gravity = Vector3(0.05, -0.02, 0); dm.turbulence_enabled = true; dm.turbulence_noise_strength = 0.4
	dust.position = Vector3(0, 2, 0); dust.local_coords = false; hero_vis.get_parent().add_child(dust); fx_day.append([dust, 3])

# ---------- hero + Pip ----------
func _limb(parent: Node3D, mesh: Mesh, mat: Material, pos: Vector3) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); mi.mesh = mesh; mi.material_override = mat; mi.position = pos; parent.add_child(mi); return mi

func _hero() -> void:
	hero = CharacterBody3D.new(); hero.position = Vector3(-6, 0.1, 26)
	var cs := CollisionShape3D.new(); var cap := CapsuleShape3D.new(); cap.height = 1.905; cap.radius = 0.32; cs.shape = cap; cs.position.y = 1.905 / 2
	hero.add_child(cs); add_child(hero)
	hero_vis = Node3D.new(); hero.add_child(hero_vis)
	var skin := _mat(Color(0.86, 0.68, 0.55), 0.6); var tunic := _mat(Color(0.45, 0.12, 0.14), 0.7); var dark := _mat(Color(0.15, 0.13, 0.12)); var gold := _mat(Color(0.85, 0.65, 0.2), 0.3)
	gold.metallic = 0.8
	var leg := CapsuleMesh.new(); leg.radius = 0.11; leg.height = 0.95
	var arm := CapsuleMesh.new(); arm.radius = 0.08; arm.height = 0.72
	var torso := CapsuleMesh.new(); torso.radius = 0.24; torso.height = 0.72
	var head := SphereMesh.new(); head.radius = 0.13; head.height = 0.27
	for s in [-1, 1]:
		var hip := Node3D.new(); hip.position = Vector3(s * 0.12, 0.95, 0); hero_vis.add_child(hip)
		_limb(hip, leg, dark, Vector3(0, -0.475, 0)); limbs.append([hip, s])
		var sh := Node3D.new(); sh.position = Vector3(s * 0.31, 1.48, 0); hero_vis.add_child(sh)
		_limb(sh, arm, tunic, Vector3(0, -0.34, 0)); limbs.append([sh, -s])
	_limb(hero_vis, torso, tunic, Vector3(0, 1.27, 0))
	_limb(hero_vis, head, skin, Vector3(0, 1.775, 0))
	var crown := CylinderMesh.new(); crown.top_radius = 0.12; crown.bottom_radius = 0.13; crown.height = 0.05
	_limb(hero_vis, crown, gold, Vector3(0, 1.88, 0))
	var cape := BoxMesh.new(); cape.size = Vector3(0.5, 0.9, 0.04)
	_limb(hero_vis, cape, _mat(Color(0.1, 0.15, 0.35)), Vector3(0, 1.1, 0.26))
	pip = Node3D.new(); pip.position = hero.position + Vector3(1.2, 0, 1.2); add_child(pip)
	var fur := _mat(Color(0.95, 0.78, 0.25), 0.8)
	var pb := SphereMesh.new(); pb.radius = 0.17; pb.height = 0.3; _limb(pip, pb, fur, Vector3(0, 0.2, 0))
	var ph := SphereMesh.new(); ph.radius = 0.12; ph.height = 0.22; _limb(pip, ph, fur, Vector3(0, 0.38, -0.04))
	var ear := PrismMesh.new(); ear.size = Vector3(0.05, 0.13, 0.03)
	_limb(pip, ear, dark, Vector3(-0.07, 0.455, -0.04)); _limb(pip, ear, dark, Vector3(0.07, 0.455, -0.04))
	cam_pivot = Node3D.new(); add_child(cam_pivot)
	cam_arm = SpringArm3D.new(); cam_arm.spring_length = 6.0; cam_arm.margin = 0.3
	var sph := SphereShape3D.new(); sph.radius = 0.25; cam_arm.shape = sph
	cam_arm.add_excluded_object(hero.get_rid())
	cam_pivot.add_child(cam_arm)
	cam = Camera3D.new(); cam.fov = 62; cam.far = 1200; cam_arm.add_child(cam); cam.current = true

func _hud() -> void:
	var cl := CanvasLayer.new(); add_child(cl)
	hud_label = Label.new(); hud_label.position = Vector2(12, 8); hud_label.add_theme_font_size_override("font_size", 20)
	hud_label.add_theme_color_override("font_outline_color", Color.BLACK); hud_label.add_theme_constant_override("outline_size", 6); cl.add_child(hud_label)
	where_label = Label.new(); where_label.position = Vector2(500, 44); where_label.add_theme_font_size_override("font_size", 30)
	where_label.add_theme_color_override("font_outline_color", Color.BLACK); where_label.add_theme_constant_override("outline_size", 8); cl.add_child(where_label)
	q_btn = _btn(cl, Vector2(1040, 12), func(): tier = (tier + 1) % 4; _save_settings(); apply_quality())
	t_btn = _btn(cl, Vector2(1040, 80), func(): time_mode = (time_mode + 1) % 4; _save_settings(); _apply_time_mode())
	s_btn = _btn(cl, Vector2(1040, 148), func(): speed_x = 10.0 if speed_x == 1.0 else 1.0; s_btn.text = "Speed: %dx" % int(speed_x))
	s_btn.text = "Speed: 1x"
	f_btn = _btn(cl, Vector2(1040, 216), func(): fps_cap = 120 if fps_cap == 60 else 60; _save_settings(); apply_quality())
	b_btn = _btn(cl, Vector2(1040, 284), func(): if not bench_running: _flythrough_all())
	b_btn.text = "Benchmark"
	bench_label = Label.new(); bench_label.position = Vector2(330, 120); bench_label.add_theme_font_size_override("font_size", 26)
	bench_label.add_theme_color_override("font_outline_color", Color.BLACK); bench_label.add_theme_constant_override("outline_size", 8); cl.add_child(bench_label)
	_apply_time_mode()
	joy_base = Panel.new(); joy_base.size = Vector2(220, 220); joy_base.position = Vector2(60, 460)
	var sb := StyleBoxFlat.new(); sb.bg_color = Color(1, 1, 1, 0.15); sb.set_corner_radius_all(110); sb.border_color = Color(1, 1, 1, 0.5); sb.set_border_width_all(3)
	joy_base.add_theme_stylebox_override("panel", sb); joy_base.mouse_filter = Control.MOUSE_FILTER_IGNORE; cl.add_child(joy_base)
	joy_knob = Panel.new(); joy_knob.size = Vector2(90, 90)
	var kb := StyleBoxFlat.new(); kb.bg_color = Color(1, 1, 1, 0.55); kb.set_corner_radius_all(45)
	joy_knob.add_theme_stylebox_override("panel", kb); joy_knob.mouse_filter = Control.MOUSE_FILTER_IGNORE; joy_base.add_child(joy_knob)
	joy_knob.position = Vector2(65, 65)
	joy_center = joy_base.position + Vector2(110, 110)

func _btn(cl: CanvasLayer, pos: Vector2, cb: Callable) -> Button:
	var b := Button.new(); b.position = pos; b.size = Vector2(225, 56); b.add_theme_font_size_override("font_size", 22)
	b.focus_mode = Control.FOCUS_NONE; b.pressed.connect(cb); cl.add_child(b); return b

func _apply_time_mode() -> void:
	_set_time(TIME_PRESETS[time_mode][1])
	t_btn.text = "Time: " + TIME_PRESETS[time_mode][0]

func _unhandled_input(e: InputEvent) -> void:
	var vw := get_viewport().get_visible_rect().size
	if e is InputEventScreenTouch:
		if e.pressed:
			if e.position.x < vw.x * 0.45 and joy_touch == -1:
				joy_touch = e.index; joy_center = e.position
				joy_base.position = joy_center - Vector2(110, 110); _joy(e.position)
			elif cam_touch == -1: cam_touch = e.index
		else:
			if e.index == joy_touch: joy_touch = -1; joy_vec = Vector2.ZERO; joy_knob.position = Vector2(65, 65)
			if e.index == cam_touch: cam_touch = -1
	elif e is InputEventScreenDrag:
		if e.index == joy_touch: _joy(e.position)
		elif e.index == cam_touch:
			yaw -= e.relative.x * 0.006; pitch = clamp(pitch - e.relative.y * 0.004, -1.2, 0.35)

func _joy(p: Vector2) -> void:
	var d := (p - joy_center).limit_length(100.0)
	joy_vec = d / 100.0; joy_knob.position = Vector2(65, 65) + d

func _physics_process(dt: float) -> void:
	if hero == null: return
	var inp := joy_vec
	var k := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if k.length() > 0.1: inp = k
	var fwd := Vector3(-sin(yaw), 0, -cos(yaw)); var right := Vector3(cos(yaw), 0, -sin(yaw))
	var dir := right * inp.x + fwd * -inp.y
	var speed: float = 6.0 * clamp(inp.length(), 0.0, 1.0)
	if dir.length() > 0.05: dir = dir.normalized()
	hero.velocity.x = dir.x * speed; hero.velocity.z = dir.z * speed
	hero.velocity.y = -1.0 if hero.is_on_floor() else hero.velocity.y - 20.0 * dt
	hero.floor_snap_length = 0.6
	hero.move_and_slide()
	if speed > 0.1:
		hero_vis.rotation.y = lerp_angle(hero_vis.rotation.y, atan2(-dir.x, -dir.z), 10 * dt)
		walk_t += dt * speed * 1.6
	else: walk_t = lerp(walk_t, round(walk_t / PI) * PI, 8 * dt)
	for l in limbs: l[0].rotation.x = sin(walk_t) * 0.6 * l[1]
	var tgt := hero.position + hero_vis.global_transform.basis.z * 1.3 + hero_vis.global_transform.basis.x * 0.7
	var dp := tgt - pip.position; dp.y = 0
	var gy := height(pip.position.x, pip.position.z)
	if dp.length() > 0.3:
		pip.position += dp * min(1.0, 4.0 * dt)
		pip.rotation.y = lerp_angle(pip.rotation.y, atan2(-dp.x, -dp.z), 8 * dt)
		pip.position.y = gy + abs(sin(Time.get_ticks_msec() * 0.012)) * 0.12
	else: pip.position.y = gy

var _tacc := 0.0
func _process(dt: float) -> void:
	if hero == null: return
	if not bench and not bench_running:
		_tacc += dt
		if _tacc > 0.2: _set_time(tod + _tacc * speed_x * 24.0 / DAY_SECONDS); _tacc = 0.0
	cam_pivot.position = hero.position + Vector3(0, 1.7, 0)
	cam_pivot.rotation = Vector3(pitch, yaw, 0)
	for bl in windmill_blades:
		if bl: bl.rotate_object_local(Vector3(0, 0, 1), dt * 0.8)
	var inside := ""
	for b in buildings:
		var lp: Vector3 = b.node.global_transform.affine_inverse() * hero.global_position
		var a: AABB = b.aabb.grow(-0.6)
		var ins: bool = lp.x > a.position.x and lp.x < a.end.x and lp.z > a.position.z and lp.z < a.end.z
		for rf in b.roofs: rf.visible = not ins
		if ins: inside = b.name
	cam_arm.spring_length = 3.5 if inside != "" else 6.0
	where_label.text = inside
	ft_acc += dt; ft_n += 1; ft_max = max(ft_max, dt)
	if ft_acc >= 0.5:
		ft_txt = "%.1f ms avg / %.1f ms worst" % [ft_acc / ft_n * 1000.0, ft_max * 1000.0]
		ft_acc = 0.0; ft_n = 0; ft_max = 0.0
	hud_label.text = "Varnethryl test %s | %s | FPS %d | %s | dc %d | %dk tris | %02d:%02d" % [VERSION, TIERS[tier], Engine.get_frames_per_second(), ft_txt,
		Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000), int(tod), int(fmod(tod, 1.0) * 60)]

# ---------- in-app benchmark: 10 s fly-through per tier ----------
const FLY := [Vector3(-6, 0, 30), Vector3(0, 0, 44), Vector3(-20, 0, 60), Vector3(0, 0, 120), Vector3(0, 0, 175), Vector3(-30, 0, 90), Vector3(-60, 0, 10), Vector3(-6, 0, 30)]
func _flythrough(seconds := 10.0) -> Array:
	var t := 0.0; var frames := 0; var worst := 0.0; var warm := 0.5
	while t < seconds + warm:
		await get_tree().process_frame
		var dt := get_process_delta_time()
		t += dt
		var u: float = clamp(t / (seconds + warm), 0.0, 0.999) * (FLY.size() - 1)
		var i := int(u); var f := u - i
		var p: Vector3 = FLY[i].lerp(FLY[i + 1], f)
		var d: Vector3 = FLY[i + 1] - FLY[i]
		hero.position = Vector3(p.x, height(p.x, p.z) + 0.1, p.z)
		if d.length() > 0.1: yaw = lerp_angle(yaw, atan2(-d.x, -d.z), 0.08); hero_vis.rotation.y = yaw
		if t > warm: frames += 1; worst = max(worst, dt)
	return [frames / seconds, 1.0 / max(worst, 0.0001)]

func _flythrough_all() -> void:
	bench_running = true
	var saved := tier; var lines := ["Benchmark (10 s fly-through each, cap %d)" % fps_cap]
	var old_cap := fps_cap; Engine.max_fps = 0
	for q in [0, 1, 2, 3]:
		tier = q; apply_quality(); Engine.max_fps = 0
		bench_label.text = "\n".join(lines) + "\nRunning %s..." % TIERS[q]
		var r: Array = await _flythrough()
		lines.append("%s: avg %.0f FPS, min %.0f FPS" % [TIERS[q], r[0], r[1]])
		bench_label.text = "\n".join(lines)
	tier = saved; fps_cap = old_cap; apply_quality()
	var f := FileAccess.open("user://benchmark.txt", FileAccess.WRITE); f.store_string("\n".join(lines)); f.close()
	print("FLY ", " | ".join(lines))
	bench_running = false

# ---------- headless bench / screenshots ----------
func _shot(name: String, pos: Vector3, yw: float, pt: float, hour: float, q: int, frames := 25) -> void:
	tier = q; apply_quality(); _set_time(hour)
	hero.position = pos; hero.position.y = height(pos.x, pos.z) + 0.1; yaw = yw; pitch = pt
	hero_vis.rotation.y = yw
	pip.position = hero.position + Vector3(1, 0, 1)
	for i in frames: await get_tree().process_frame
	var n := 6; var dc := 0.0
	for i in n:
		await get_tree().process_frame
		dc += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	print("BENCH %s tier=%s draw_calls=%d prims=%d objects=%d" % [name, TIERS[q], int(dc / n),
		Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)])
	if not name.begins_with("dc_"):
		get_viewport().get_texture().get_image().save_png("user://shot_%s.png" % name)

func _run_bench() -> void:
	await get_tree().create_timer(0.5).timeout
	var views := [["plaza", Vector3(-6, 0, 30), 0.25, -0.28], ["houses", Vector3(0, 0, 44), PI * 0.82, -0.22],
		["inside", Vector3(-25.2, 0, 52), PI * 0.1, -0.55], ["gate", Vector3(0, 0, 165), 0.0, -0.12],
		["outside", Vector3(30, 0, 240), PI * 0.85, -0.05], ["keep", Vector3(0, 0, -95), 0.0, -0.1]]
	var only := OS.get_environment("BENCH_ONLY")
	if only == "" or only == "dc":
		for q in 4:
			for v in views: await _shot("dc_%s_%s" % [v[0], TIERS[q]], v[1], v[2], v[3], 11.0, q, 8)
		for q in 4: await _shot("dc_night_plaza_%s" % TIERS[q], views[0][1], views[0][2], views[0][3], 22.5, q, 8)
	var ST := int(OS.get_environment("SHOT_TIER")) if OS.get_environment("SHOT_TIER") != "" else 2
	var pre := TIERS[ST].to_lower() + "_"
	if only == "fly":
		await _flythrough_all()
	if only == "" or only == "shots":
		await _shot(pre + "u1_day_plaza", Vector3(-6, 0, 30), 0.25, -0.28, 10.5, ST, 30)
		await _shot(pre + "u2_houses", Vector3(0, 0, 44), PI * 0.82, -0.22, 14.0, ST)
		await _shot(pre + "u3_cherry_closeup", Vector3(-150, 0, 165.5), 0.0, 0.3, 12.0, ST)
		await _shot(pre + "u3b_tree_row", Vector3(-114, 0, 176), 0.0, -0.05, 12.0, ST)
		await _shot(pre + "u4_sunset_gate", Vector3(0, 0, 150), 0.0, -0.05, 18.2, ST)
		await _shot(pre + "u5_sunset_outside", Vector3(30, 0, 240), PI * 0.85, -0.02, 17.6, ST)
		await _shot(pre + "u10_lake", Vector3(250, 0, -120), 0.0, -0.25, 15.0, ST)
		await _shot(pre + "u9_noon_mountains", Vector3(-20, 0, 250), PI * 1.15, 0.05, 12.0, ST)
		await _shot(pre + "u6_night_plaza", Vector3(-6, 0, 30), 0.25, -0.25, 22.5, ST, 40)
		await _shot(pre + "u7_night_street", Vector3(0, 0, -20), PI, -0.15, 22.5, ST, 40)
		await _shot(pre + "u8_inside", Vector3(-25.2, 0, 52), PI * 0.1, -0.55, 12.0, ST)
		await _shot("low_day_plaza", Vector3(-6, 0, 30), 0.25, -0.28, 10.5, 0)
	get_tree().quit()
