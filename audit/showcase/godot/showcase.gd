extends Node3D
# Beth showcase (Ultra preset, Forward+). Builds town / volcano / frost / port / arena / boss line-up, then renders 8 shots.
# Run: godot --path . --rendering-method forward_plus --resolution 1920x1080 res://sc/showcase.tscn [-- shot_name]
const SC := "res://sc/"
var env: Environment
var sun: DirectionalLight3D
var cam: Camera3D
var camattr: CameraAttributesPractical
var sky_mat: PhysicalSkyMaterial
var night_lights: Array = []
var fx := {}
var rng := RandomNumberGenerator.new()
var only := ""
var fast := false
var rlog := {}

func vc(n: Node) -> void:
	# kit GLBs (round-1..3) carry tints in COLOR_0; Godot leaves vertex colour off. Hi assets need nothing.
	if n is MeshInstance3D and n.mesh:
		for i in n.mesh.get_surface_count():
			var m = n.mesh.surface_get_material(i)
			if m is BaseMaterial3D and n.mesh.surface_get_format(i) & Mesh.ARRAY_FORMAT_COLOR:
				m.vertex_color_use_as_albedo = true
	for c in n.get_children(): vc(c)

func put(path: String, pos: Vector3, yaw := 0.0, s := 1.0, ground := true) -> Node3D:
	var ps = load(path)
	if ps == null:
		push_warning("missing " + path); return null
	var n: Node3D = ps.instantiate(); add_child(n)
	n.position = pos; n.rotation.y = yaw; n.scale = Vector3.ONE * s; vc(n)
	return n

func aabb_of(n: Node) -> AABB:
	var out := AABB(); var first := true
	for m in n.find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = m
		var b: AABB = mi.global_transform * mi.get_aabb()
		if first: out = b; first = false
		else: out = out.merge(b)
	return out

func height_of(n: Node3D) -> Array:
	# skinned meshes: the mesh AABB ignores bone scale (e.g. the 11x titan), so measure the posed skeleton when there is one
	var sk: Skeleton3D = null
	for c in n.find_children("*", "Skeleton3D", true, false): sk = c; break
	if sk and sk.get_bone_count() > 2:
		var lo := INF; var hi := -INF
		for i in sk.get_bone_count():
			var p: Vector3 = (sk.global_transform * sk.get_bone_global_pose(i)).origin
			lo = min(lo, p.y); hi = max(hi, p.y)
		return [(hi - lo) * 1.1, lo]
	var b := aabb_of(n)
	return [b.size.y, b.position.y]

func actor(path: String, pos: Vector3, height: float, yaw := 0.0, anim := "idle") -> Node3D:
	var n := put(path, pos, yaw, 1.0)
	if n == null: return null
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	if ap:
		var pick := ""
		var names := ap.get_animation_list()
		if ap.has_animation(anim): pick = anim
		else:
			for nm in names:
				if "idle" in String(nm).to_lower(): pick = nm; break
			if pick == "" and names.size() > 0: pick = names[0]
		if pick != "":
			ap.get_animation(pick).loop_mode = Animation.LOOP_LINEAR; ap.play(pick); ap.seek(rng.randf() * 0.8, true); ap.advance(0.0)
	for i in 3: await get_tree().process_frame
	var h: Array = height_of(n)
	n.scale = Vector3.ONE * (height / max(h[0], 0.001))
	for i in 2: await get_tree().process_frame
	var b := aabb_of(n)
	var h2: Array = height_of(n)
	n.position.y += pos.y - min(b.position.y, h2[1])   # feet on the ground
	for m in n.find_children("*", "MeshInstance3D", true, false): m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	return n

func mat(c: Color, rough := 0.9, tex: Texture2D = null, uv := 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.albedo_color = c; m.roughness = rough
	if tex: m.albedo_texture = tex; m.uv1_scale = Vector3(uv, uv, uv); m.uv1_triplanar = true
	return m

func noise_tex(freq := 0.02, seamless := true, normal := false) -> NoiseTexture2D:
	var t := NoiseTexture2D.new(); var n := FastNoiseLite.new(); n.frequency = freq; n.fractal_octaves = 5
	t.noise = n; t.seamless = seamless; t.width = 512; t.height = 512
	if normal: t.as_normal_map = true; t.bump_strength = 6.0
	return t

func ground_patch(pos: Vector3, size: Vector2, c: Color, rough := 0.95) -> MeshInstance3D:
	var g := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = size; pm.subdivide_width = 8; pm.subdivide_depth = 8; g.mesh = pm
	var m := mat(c, rough, noise_tex(0.05), 0.03); m.normal_enabled = true; m.normal_texture = noise_tex(0.08, true, true); m.uv1_scale = Vector3(0.05, 0.05, 0.05)
	g.material_override = m; g.position = pos; add_child(g); return g

func particles(pos: Vector3, amount: int, life: float, box: Vector3, vel: Vector3, spread: float, col: Color, energy: float, size: float, grav := Vector3.ZERO, additive := true) -> GPUParticles3D:
	var p := GPUParticles3D.new(); p.amount = amount; p.lifetime = life; p.preprocess = life
	var pm := ParticleProcessMaterial.new(); pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX; pm.emission_box_extents = box
	pm.direction = vel.normalized() if vel.length() > 0 else Vector3.UP; pm.initial_velocity_min = vel.length() * 0.5; pm.initial_velocity_max = vel.length() * 1.2; pm.spread = spread
	pm.gravity = grav; pm.scale_min = 0.5; pm.scale_max = 1.3; pm.turbulence_enabled = true; pm.turbulence_noise_strength = 0.6
	var grad := Gradient.new(); grad.set_color(0, Color(col, 0.0)); grad.add_point(0.15, col); grad.set_color(grad.get_point_count() - 1, Color(col, 0.0))
	var gt := GradientTexture1D.new(); gt.gradient = grad; pm.color_ramp = gt
	p.process_material = pm
	var q := QuadMesh.new(); q.size = Vector2(size, size)
	var m := StandardMaterial3D.new(); m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES; m.vertex_color_use_as_albedo = true
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if additive: m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.albedo_texture = soft_dot(); m.emission_enabled = energy > 0; m.emission = col; m.emission_energy_multiplier = energy
	q.material = m; p.draw_pass_1 = q; p.position = pos; p.visibility_aabb = AABB(-box - Vector3(40, 40, 40), box * 2 + Vector3(80, 120, 80)); add_child(p); return p

var _dot: Texture2D
func soft_dot() -> Texture2D:
	if _dot: return _dot
	var g := Gradient.new(); g.set_color(0, Color(1, 1, 1, 1)); g.set_color(1, Color(1, 1, 1, 0))
	var t := GradientTexture2D.new(); t.gradient = g; t.fill = GradientTexture2D.FILL_RADIAL; t.fill_from = Vector2(0.5, 0.5); t.fill_to = Vector2(1.0, 0.5); t.width = 64; t.height = 64
	_dot = t; return t

func omni(pos: Vector3, col: Color, energy: float, rng_m: float, shadow := false) -> OmniLight3D:
	var l := OmniLight3D.new(); l.position = pos; l.light_color = col; l.light_energy = energy; l.omni_range = rng_m; l.shadow_enabled = shadow
	l.light_volumetric_fog_energy = 1.5; add_child(l); night_lights.append(l); return l

# ------------------------------------------------------------------ world
func build_env() -> void:
	var we := WorldEnvironment.new(); env = Environment.new()
	env.background_mode = Environment.BG_SKY; var sky := Sky.new(); sky_mat = PhysicalSkyMaterial.new()
	sky_mat.rayleigh_coefficient = 2.2; sky_mat.mie_coefficient = 0.006; sky_mat.mie_eccentricity = 0.82; sky_mat.turbidity = 8.0; sky_mat.sun_disk_scale = 1.4; sky_mat.ground_color = Color(0.18, 0.2, 0.17); sky_mat.energy_multiplier = 1.0
	sky.sky_material = sky_mat; sky.radiance_size = Sky.RADIANCE_SIZE_256; env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES; env.tonemap_exposure = 1.0; env.tonemap_white = 6.0
	env.ssr_enabled = true; env.ssr_max_steps = 96; env.ssr_fade_in = 0.1; env.ssr_fade_out = 2.0
	env.ssao_enabled = true; env.ssao_radius = 1.6; env.ssao_intensity = 2.2; env.ssao_detail = 0.6
	env.ssil_enabled = true; env.ssil_radius = 6.0; env.ssil_intensity = 1.0
	env.sdfgi_enabled = true; env.sdfgi_use_occlusion = true; env.sdfgi_cascades = 6; env.sdfgi_min_cell_size = 0.4; env.sdfgi_energy = 1.0; env.sdfgi_bounce_feedback = 0.6
	env.glow_enabled = true; env.glow_intensity = 0.7; env.glow_strength = 1.0; env.glow_bloom = 0.06; env.glow_hdr_threshold = 1.1; env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.set_glow_level(1, 1.0); env.set_glow_level(3, 1.0); env.set_glow_level(5, 0.7)
	env.volumetric_fog_enabled = true; env.volumetric_fog_density = 0.006; env.volumetric_fog_albedo = Color(0.92, 0.9, 0.86); env.volumetric_fog_anisotropy = 0.7; env.volumetric_fog_length = 260.0; env.volumetric_fog_detail_spread = 2.0; env.volumetric_fog_sky_affect = 0.35; env.volumetric_fog_temporal_reprojection_enabled = true
	env.adjustment_enabled = true; env.adjustment_saturation = 1.08; env.adjustment_contrast = 1.05
	we.environment = env
	camattr = CameraAttributesPractical.new(); camattr.dof_blur_far_enabled = false; camattr.dof_blur_amount = 0.08
	we.camera_attributes = camattr; add_child(we)
	sun = DirectionalLight3D.new(); sun.shadow_enabled = true; sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS; sun.directional_shadow_max_distance = 420.0
	sun.shadow_blur = 1.5; sun.light_angular_distance = 0.8; sun.light_volumetric_fog_energy = 2.0; sun.shadow_bias = 0.04; sun.shadow_normal_bias = 1.2; add_child(sun)
	cam = Camera3D.new(); cam.far = 6000; cam.near = 0.1; add_child(cam); cam.make_current()

func time_of_day(kind: String) -> void:
	var on := kind == "night"
	for l in night_lights: l.visible = on
	sky_mat.sun_disk_scale = 1.4
	match kind:
		"golden":
			sun.rotation_degrees = Vector3(-17, 75, 0); sun.light_color = Color(1.0, 0.74, 0.48); sun.light_energy = 3.0; sky_mat.energy_multiplier = 1.0; env.ambient_light_energy = 1.0; env.volumetric_fog_density = 0.003; env.volumetric_fog_albedo = Color(1.0, 0.86, 0.7); env.tonemap_exposure = 1.3
		"sunset":
			sun.rotation_degrees = Vector3(-8, -135, 0); sun.light_color = Color(1.0, 0.6, 0.36); sun.light_energy = 2.6; sky_mat.energy_multiplier = 1.2; env.ambient_light_energy = 1.0; env.volumetric_fog_density = 0.003; env.volumetric_fog_albedo = Color(1.0, 0.78, 0.62); env.tonemap_exposure = 1.35
		"day":
			sun.rotation_degrees = Vector3(-42, -35, 0); sun.light_color = Color(1.0, 0.96, 0.9); sun.light_energy = 2.0; sky_mat.energy_multiplier = 1.0; env.ambient_light_energy = 0.8; env.volumetric_fog_density = 0.004; env.volumetric_fog_albedo = Color(0.9, 0.92, 0.95); env.tonemap_exposure = 0.95
		"snow":
			sun.rotation_degrees = Vector3(-24, 40, 0); sun.light_color = Color(0.92, 0.95, 1.0); sun.light_energy = 2.0; sky_mat.energy_multiplier = 0.8; env.ambient_light_energy = 0.9; env.volumetric_fog_density = 0.012; env.volumetric_fog_albedo = Color(0.88, 0.92, 1.0); env.tonemap_exposure = 0.85
		"volcano":
			sun.rotation_degrees = Vector3(-22, 25, 0); sun.light_color = Color(1.0, 0.55, 0.35); sun.light_energy = 1.8; sky_mat.energy_multiplier = 0.5; env.ambient_light_energy = 0.6; env.volumetric_fog_density = 0.01; env.volumetric_fog_albedo = Color(0.55, 0.45, 0.4); env.tonemap_exposure = 1.4
		"night":
			sun.rotation_degrees = Vector3(-40, -20, 0); sun.light_color = Color(0.55, 0.65, 1.0); sun.light_energy = 0.12; sky_mat.energy_multiplier = 0.02; sky_mat.sun_disk_scale = 0.0; env.ambient_light_energy = 0.15; env.volumetric_fog_density = 0.01; env.volumetric_fog_albedo = Color(0.5, 0.55, 0.7); env.tonemap_exposure = 1.6

func build_town() -> void:
	var H := SC + "hi/buildings/bld_"
	ground_patch(Vector3(0, 0, 0), Vector2(900, 900), Color(0.30, 0.42, 0.22))
	var plaza := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 40; cm.bottom_radius = 40.3; cm.height = 0.3; cm.radial_segments = 96; plaza.mesh = cm
	var pmat := mat(Color(0.55, 0.52, 0.48), 0.85, noise_tex(0.4), 0.4); pmat.normal_enabled = true; pmat.normal_texture = noise_tex(0.6, true, true); plaza.material_override = pmat; plaza.position = Vector3(0, 0.05, 0); add_child(plaza)
	# ring of buildings facing the square (door +z faces the centre)
	var ring := [["guildhall", 0.0, 66.0], ["inn", 0.62, 60.0], ["apothecary", 1.15, 56.0], ["bakery", 1.6, 54.0], ["market", 2.15, 60.0], ["house1", 2.65, 54.0], ["house2", 3.12, 54.0], ["house3", 3.6, 54.0], ["house4", 4.1, 54.0], ["smithy", 4.65, 56.0], ["townhall", 5.2, 60.0], ["library", 5.72, 66.0]]
	for r in ring:
		var a: float = r[1]; var d: float = r[2]
		put(H + r[0] + ".glb", Vector3(sin(a) * d, 0, -cos(a) * d), -a + PI)
		omni(Vector3(sin(a) * (d - 9.5), 3.2, -cos(a) * (d - 9.5)), Color(1.0, 0.68, 0.38), 3.0, 14.0, false)
	put(H + "mage.glb", Vector3(-150, 0, -120), 0.6); put(H + "keep.glb", Vector3(0, 0, -190), 0.0); put(H + "windmill.glb", Vector3(140, 0, 90), -0.8)
	put(H + "farmhouse.glb", Vector3(120, 0, 150), -0.5); put(H + "barn.glb", Vector3(165, 0, 135), -1.2); put(H + "stables.glb", Vector3(-120, 0, 120), 0.7)
	# fountain / statue focal point (simple stone)
	var f := MeshInstance3D.new(); var fc := CylinderMesh.new(); fc.top_radius = 5.5; fc.bottom_radius = 6.0; fc.height = 1.0; f.mesh = fc; f.material_override = mat(Color(0.7, 0.68, 0.64), 0.7); f.position = Vector3(0, 0.5, 0); add_child(f)
	var fw := MeshInstance3D.new(); var wc := CylinderMesh.new(); wc.top_radius = 5.0; wc.bottom_radius = 5.0; wc.height = 0.1; fw.mesh = wc; fw.material_override = water_mat(); fw.position = Vector3(0, 0.95, 0); add_child(fw)
	var pil := MeshInstance3D.new(); var pc := CylinderMesh.new(); pc.top_radius = 0.6; pc.bottom_radius = 0.9; pc.height = 4.5; pil.mesh = pc; pil.material_override = mat(Color(0.72, 0.7, 0.66), 0.6); pil.position = Vector3(0, 2.6, 0); add_child(pil)
	# lamp posts + market stalls + benches (round-3 dressing, vertex colours fixed)
	for i in 10:
		var a := i * TAU / 10 + 0.3
		put(SC + "kit/dressing/lantern_post.glb", Vector3(sin(a) * 37, 0.2, cos(a) * 37), a)
		omni(Vector3(sin(a) * 37 + 0.55 * cos(a), 3.0, cos(a) * 37), Color(1.0, 0.75, 0.42), 2.2, 11.0, i % 3 == 0)
	for i in 6:
		var a := i * TAU / 6 + 0.55
		put(SC + "kit/dressing/market_stall_%s.glb" % ["red", "blue", "green"][i % 3], Vector3(sin(a) * 24, 0.2, cos(a) * 24), a + PI, 1.6)
	# trees around the outskirts
	var tr := ["oak_hi", "oak_autumn_hi", "oak_deep_hi", "birch_hi", "blossom_hi", "pine_hi"]
	for k in 90:
		var a := rng.randf() * TAU; var d := rng.randf_range(95, 260)
		var p := Vector3(sin(a) * d, 0, cos(a) * d)
		if p.distance_to(Vector3(-150, 0, -120)) < 30 or p.distance_to(Vector3(0, 0, -190)) < 35 or p.distance_to(Vector3(140, 0, 90)) < 20 or p.distance_to(Vector3(140, 0, 145)) < 40 or p.distance_to(Vector3(-120, 0, 120)) < 28: continue
		put(SC + "hi/trees/" + tr[k % tr.size()] + ".glb", p, rng.randf() * TAU, rng.randf_range(1.3, 2.0))
	for k in 70:
		var a := rng.randf() * TAU; var d := rng.randf_range(72, 140)
		put(SC + "hi/trees/" + ["bush_hi", "bush_autumn_hi", "grass_clump_hi"][k % 3] + ".glb", Vector3(sin(a) * d, 0, cos(a) * d), rng.randf() * TAU, 1.5)
	fx["fireflies"] = particles(Vector3(0, 3, 70), 160, 6.0, Vector3(70, 2.5, 30), Vector3(0, 0.3, 0), 180, Color(0.85, 1.0, 0.4), 6.0, 0.14)
	fx["smoke"] = particles(Vector3(-28, 16, -58), 60, 9.0, Vector3(1, 0.5, 1), Vector3(0.6, 2.2, 0), 15, Color(0.6, 0.6, 0.62, 0.35), 0.0, 3.5, Vector3(0.3, 0.2, 0), false)

func water_mat() -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = load(SC + "showcase_water.gdshader")
	m.set_shader_parameter("noise1", noise_tex(0.03, true, true)); m.set_shader_parameter("noise2", noise_tex(0.07, true, true)); return m

func build_volcano() -> void:
	var o := Vector3(1600, 0, 0)
	ground_patch(o, Vector2(700, 700), Color(0.12, 0.11, 0.11), 0.95)
	var v := put(SC + "hi/terrain/volcano_flank_hi.glb", o + Vector3(0, -1, -60), 0.0, 3.2)
	for i in 6:
		var a := i * TAU / 6 + 0.6
		put(SC + "hi/terrain/boulder_strata_hi.glb", o + Vector3(sin(a) * 120, -0.8, cos(a) * 90 + 60), a, rng.randf_range(0.8, 1.8))
	omni(o + Vector3(0, 150, -60), Color(1.0, 0.4, 0.12), 0.0, 1.0)  # placeholder (night list)
	var lava_l := OmniLight3D.new(); lava_l.position = o + Vector3(0, 30, 40); lava_l.light_color = Color(1.0, 0.42, 0.15); lava_l.light_energy = 6.0; lava_l.omni_range = 160.0; lava_l.light_volumetric_fog_energy = 3.0; add_child(lava_l)
	var crater := OmniLight3D.new(); crater.position = o + Vector3(0, 175, -60); crater.light_color = Color(1.0, 0.4, 0.1); crater.light_energy = 16.0; crater.omni_range = 120.0; crater.light_volumetric_fog_energy = 4.0; add_child(crater)
	fx["embers"] = particles(o + Vector3(0, 40, 60), 700, 7.0, Vector3(90, 30, 60), Vector3(0.4, 2.5, 0), 40, Color(1.0, 0.45, 0.12), 14.0, 0.35, Vector3(0, -0.15, 0))
	fx["sparks"] = particles(o + Vector3(0, 172, -60), 400, 3.0, Vector3(10, 3, 10), Vector3(0, 22, 0), 25, Color(1.0, 0.62, 0.2), 20.0, 0.6, Vector3(0, -9.8, 0))
	fx["ash"] = particles(o + Vector3(0, 220, -60), 120, 14.0, Vector3(14, 6, 14), Vector3(4, 10, 2), 25, Color(0.18, 0.16, 0.16, 0.5), 0.0, 22.0, Vector3(0.6, 0.4, 0), false)

func build_frost() -> void:
	var o := Vector3(-1600, 0, 0)
	ground_patch(o, Vector2(1200, 1200), Color(0.86, 0.9, 0.96), 0.55)
	put(SC + "hi/terrain/peak_snow_hi.glb", o + Vector3(0, -2, -260), 0.3, 3.6)
	put(SC + "hi/terrain/peak_snow_hi.glb", o + Vector3(-300, -2, -420), 2.2, 4.2)
	put(SC + "hi/terrain/peak_bare_hi.glb", o + Vector3(280, -2, -380), 1.0, 3.8)
	put(SC + "hi/terrain/cliff_strata_hi.glb", o + Vector3(-110, -1, -70), 0.4, 1.3)
	for k in 70:
		var p := o + Vector3(rng.randf_range(-260, 260), 0, rng.randf_range(-160, 0))
		if abs(p.x - o.x) < 40: continue
		put(SC + "hi/trees/pine_snow_hi.glb", p, rng.randf() * TAU, rng.randf_range(1.2, 2.2))
	var pond := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(80, 50); pond.mesh = pm
	var im := mat(Color(0.75, 0.88, 0.98), 0.08); im.metallic_specular = 0.8; pond.material_override = im; pond.position = o + Vector3(30, 0.06, 30); add_child(pond)
	fx["snow"] = particles(o + Vector3(0, 40, 40), 2500, 10.0, Vector3(120, 20, 90), Vector3(1.0, -2.2, 0.3), 20, Color(1, 1, 1, 0.9), 0.8, 0.22, Vector3(0, -0.4, 0), false)

func build_port() -> void:
	var o := Vector3(0, 0, 1600)
	ground_patch(o + Vector3(0, 0.0, -240), Vector2(800, 300), Color(0.32, 0.42, 0.24))
	for i in 5: put(SC + "hi/terrain/shore_edge_hi.glb", o + Vector3(-80 + i * 40, 0.2, -82), 0.0, 1.0)
	var w := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(1600, 1100); pm.subdivide_width = 160; pm.subdivide_depth = 110; w.mesh = pm; w.material_override = water_mat(); w.position = o + Vector3(0, 0.0, 380); add_child(w)
	var sea := MeshInstance3D.new(); var sp := PlaneMesh.new(); sp.size = Vector2(1600, 1100); sea.mesh = sp; sea.material_override = mat(Color(0.25, 0.22, 0.18), 1.0); sea.position = o + Vector3(0, -9, 380); add_child(sea)
	put(SC + "hi/buildings/bld_lighthouse.glb", o + Vector3(70, 0.2, -105), 2.6)
	for i in 4: put(SC + "kit/port/dock_10m.glb", o + Vector3(-20, 0.6, -70 + i * 10), PI / 2, 1.0)
	for i in 8: put(SC + "kit/port/pier_post.glb", o + Vector3(-23 + (i % 2) * 6, 0, -68 + (i / 2) * 10), 0.0, 1.0)
	var ship := put(SC + "kit/port/ship_galleon.glb", o + Vector3(-2, 0.35, -15), -1.25, 2.2)
	put(SC + "kit/port/ship_sloop.glb", o + Vector3(-70, 0.3, 10), 0.6, 2.0)
	put(SC + "kit/port/crate_stack.glb", o + Vector3(-16, 0.6, -84), 0.3, 1.2); put(SC + "kit/port/net_rack.glb", o + Vector3(-34, 0.2, -92), 0.2, 1.2)
	for k in 25: put(SC + "hi/trees/" + ["pine_hi", "oak_hi", "birch_hi"][k % 3] + ".glb", o + Vector3(rng.randf_range(-300, 300), 0, rng.randf_range(-260, -120)), rng.randf() * TAU, rng.randf_range(1.4, 2.0))

func build_arena() -> void:
	var o := Vector3(0, 0, -1600)
	ground_patch(o, Vector2(700, 700), Color(0.34, 0.44, 0.24))
	put(SC + "hi/buildings/bld_colosseum.glb", o + Vector3(-60, 0, 0), 0.0, 1.0)
	put(SC + "hi/buildings/bld_temple.glb", o + Vector3(70, 0, -10), -0.35, 1.0)
	var ap := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = Vector3(70, 0.25, 110); ap.mesh = bm; ap.material_override = mat(Color(0.78, 0.76, 0.72), 0.7, noise_tex(0.3), 0.3); ap.position = o + Vector3(70, 0.1, 30); add_child(ap)
	for k in 40: put(SC + "hi/trees/" + ["pine_hi", "oak_deep_hi", "birch_hi"][k % 3] + ".glb", o + Vector3(rng.randf_range(-250, 250), 0, rng.randf_range(-260, -60)), rng.randf() * TAU, rng.randf_range(1.4, 2.2))

func build_lineup() -> void:
	var o := Vector3(1600, 0, 1600)
	ground_patch(o, Vector2(800, 800), Color(0.36, 0.4, 0.26))
	for k in 30: put(SC + "hi/terrain/boulder_strata_hi.glb", o + Vector3(rng.randf_range(-200, 200), -0.6, rng.randf_range(-260, -90)), rng.randf() * TAU, rng.randf_range(0.6, 2.5))
	put(SC + "hi/terrain/peak_bare_hi.glb", o + Vector3(-60, -2, -360), 0.5, 3.0); put(SC + "hi/terrain/peak_snow_hi.glb", o + Vector3(160, -2, -420), 1.2, 3.0)

func build_actors() -> void:
	var C := SC + "chars/"
	# town hero shot: group stands in the plaza, everyone turned to face the camera (glTF forward = +Z)
	var hc := Vector3(1.4, 1.7, 9.0)
	var hero := [["owner_new5_fight.glb", Vector3(0, 0.25, 14), 1.85, "idle_saber"], ["kael_armor2.glb", Vector3(-2.3, 0.25, 15.6), 1.82, "idle"], ["selene_armor2.glb", Vector3(2.4, 0.25, 15.4), 1.74, "idle"],
		["rook_armor2.glb", Vector3(-4.4, 0.25, 17.6), 1.8, "idle"], ["asha_armor2.glb", Vector3(4.6, 0.25, 17.8), 1.7, "idle"], ["owner_pika1.glb", Vector3(1.3, 0.25, 12.6), 0.7, "idle"]]
	for h in hero:
		var p: Vector3 = h[1]
		await actor(C + h[0], p, h[2], atan2(hc.x - p.x, hc.z - p.z), h[3])
	var key := OmniLight3D.new(); key.position = Vector3(3.0, 3.2, 10.5); key.light_color = Color(1.0, 0.86, 0.7); key.light_energy = 1.6; key.omni_range = 9.0; add_child(key)
	# volcano titan
	await actor(C + "ashentitan_volcano_11x.glb", Vector3(1600, 0, 40), 32.0, atan2(60.0, 190.0), "idle")
	var rim := OmniLight3D.new(); rim.position = Vector3(1612, 6, 70); rim.light_color = Color(1.0, 0.45, 0.15); rim.light_energy = 10.0; rim.omni_range = 60.0; add_child(rim)
	await actor(C + "owner_new5_fight.glb", Vector3(1606, 0, 110), 1.85, PI + 0.2, "idle_saber")
	# frost trolls
	await actor(C + "frosttroll_a4.glb", Vector3(-1612, 0, 40), 5.5, 0.6)
	await actor(C + "frosttrollB_1.glb", Vector3(-1590, 0, 32), 6.2, 0.2)
	# boss lineup at scale (left -> right), heroes for scale
	var o := Vector3(1600, 0, 1600)
	await actor(C + "frosttroll_a4.glb", o + Vector3(-52, 0, 0), 5.5, 0.15)
	await actor(C + "frosttrollB_1.glb", o + Vector3(-40, 0, 0), 6.2, 0.1)
	await actor(C + "phoenix_new3.glb", o + Vector3(-18, 6, 0), 7.0, 0.2, "hover")
	await actor(C + "ashentitan_volcano_11x.glb", o + Vector3(10, 0, -6), 32.0, 0.0)
	await actor(C + "vaelthryx_new7.glb", o + Vector3(48, 0, -4), 9.0, -0.9, "coil_idle")
	await actor(C + "owner_new5_fight.glb", o + Vector3(-4, 0, 22), 1.85, 0.0, "idle_saber")
	await actor(C + "kael_armor2.glb", o + Vector3(-7, 0, 23), 1.82, 0.2)

func _ready() -> void:
	rng.seed = 42
	var args := OS.get_cmdline_user_args(); if args.size() > 0: only = args[0]
	if args.size() > 1: fast = args[1] == "fast"
	if only == "all": only = ""
	build_env(); build_town(); build_volcano(); build_frost(); build_port(); build_arena(); build_lineup()
	await build_actors()
	await shots()
	var fa := FileAccess.open("res://sc/out/render_log.json", FileAccess.WRITE); fa.store_string(JSON.stringify(rlog, "  ")); fa.close()
	get_tree().quit()

func shot(name: String, tod: String, p: Vector3, t: Vector3, fov := 50.0, dof := 0.0, frames := 48) -> void:
	if only != "" and only != name: return
	time_of_day(tod)
	for k in fx: fx[k].emitting = true
	cam.position = p; cam.look_at(t); cam.fov = fov
	camattr.dof_blur_far_enabled = dof > 0.0; camattr.dof_blur_near_enabled = dof > 0.0
	if dof > 0.0:
		camattr.dof_blur_far_distance = dof * 1.6; camattr.dof_blur_far_transition = dof * 2.5; camattr.dof_blur_near_distance = dof * 0.45; camattr.dof_blur_near_transition = dof * 0.3; camattr.dof_blur_amount = 0.11
	if fast: frames = 8
	var t0 := Time.get_ticks_msec()
	for i in frames: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://sc/out/%s.png" % name)
	rlog[name] = {"ms_total": Time.get_ticks_msec() - t0, "frames": frames, "draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), "primitives": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)}
	print("SHOT ", name, " ", rlog[name])

func shots() -> void:
	await shot("1_town_square_golden", "golden", Vector3(14, 4.5, 37), Vector3(-6, 9, -60), 62.0)
	await shot("2_town_night", "night", Vector3(0, 24, 38), Vector3(0, 4, -42), 62.0)
	await shot("3_owner_hero_closeup", "golden", Vector3(1.4, 1.7, 9.0), Vector3(0, 1.35, 14), 34.0, 5.0)
	await shot("4_volcano_titan", "volcano", Vector3(1660, 9, 250), Vector3(1600, 42, 10), 50.0, 0.0)
	await shot("5_frostreach_peaks", "snow", Vector3(-1585, 5, 110), Vector3(-1600, 40, -250), 55.0)
	await shot("6_port_sunset", "sunset", Vector3(48, 7, 1500), Vector3(-20, 8, 1600), 50.0)
	await shot("7_colosseum_temple", "day", Vector3(38, 8, -1535), Vector3(-45, 9, -1600), 55.0)
	await shot("8_boss_lineup", "day", Vector3(1598, 12, 1735), Vector3(1600, 15, 1594), 55.0, 0.0)
