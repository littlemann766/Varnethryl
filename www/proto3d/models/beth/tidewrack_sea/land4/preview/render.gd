extends SceneTree
# Compatibility stills. Not a phone Vulkan capture.
# args: shots.json outdir before|after filelist.json
func glb(p: String) -> Node3D:
	var d := GLTFDocument.new()
	var s := GLTFState.new()
	if d.append_from_file(p, s) != OK:
		return null
	return d.generate_scene(s)

func _initialize() -> void:
	_run.call_deferred()

func sh(p: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(p)
	return m

var _maps := {}
func grab(name: String) -> Texture2D:
	if _maps.has(name):
		return _maps[name]
	var p := ProjectSettings.globalize_path("res://").path_join("../textures/%s.jpg" % name)
	var img := Image.load_from_file(p)
	if img == null:
		push_error("missing texture " + p)
		return null
	img.generate_mipmaps()
	var t := ImageTexture.create_from_image(img)
	_maps[name] = t
	return t

func bind_terrain(mat: ShaderMaterial) -> void:
	for key in ["grass", "earth", "sand", "rock", "snow"]:
		mat.set_shader_parameter(key + "_col", grab(key + "_albedo"))
		mat.set_shader_parameter(key + "_nrm", grab(key + "_normal"))
		mat.set_shader_parameter(key + "_rgh", grab(key + "_rough"))

func _run() -> void:
	var a := OS.get_cmdline_user_args()
	var shots: Array = JSON.parse_string(FileAccess.get_file_as_string(a[0]))
	var out: String = a[1]
	var after := a[2] == "after"
	var flist: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(a[3]))
	DirAccess.make_dir_recursive_absolute(out)
	get_root().size = Vector2i(1280, 720)
	var cur := ""
	var top: Node3D = null
	for s in shots:
		if str(s.region) != cur:
			if top:
				top.free()
			top = Node3D.new()
			get_root().add_child(top)
			cur = str(s.region)
			_build(top, cur, flist[cur], after)
			for i in 3:
				await process_frame
		var hero: MeshInstance3D = null
		if s.has("hero"):
			hero = MeshInstance3D.new()
			var cm := CapsuleMesh.new()
			cm.radius = 0.32
			cm.height = 1.7
			hero.mesh = cm
			var hm := StandardMaterial3D.new()
			hm.albedo_color = Color(0.62, 0.12, 0.1)
			hero.material_override = hm
			top.add_child(hero)
			hero.position = Vector3(s.hero[0], s.hero[1] + 0.95, s.hero[2])
		var cam := Camera3D.new()
		top.add_child(cam)
		cam.fov = float(s.fov) if s.has("fov") else 55.0
		cam.far = 2400
		cam.near = 0.15
		cam.current = true
		cam.look_at_from_position(Vector3(s.cam[0], s.cam[1], s.cam[2]), Vector3(s.at[0], s.at[1], s.at[2]), Vector3.UP)
		for i in 6:
			await process_frame
		var img := get_root().get_texture().get_image()
		img.save_png("%s/%s.png" % [out, s.name])
		print("shot ", s.name)
		cam.free()
		if hero:
			hero.free()
	quit()

func _build(top: Node3D, reg: String, files: Array, after: bool) -> void:
	var tint: Array = {
		"A": [Color(0.30, 0.48, 0.72), Color(0.74, 0.80, 0.86)],
		"B": [Color(0.32, 0.46, 0.66), Color(0.78, 0.80, 0.84)],
		"frost": [Color(0.50, 0.60, 0.72), Color(0.86, 0.90, 0.94)],
		"ash": [Color(0.22, 0.22, 0.25), Color(0.36, 0.33, 0.32)]
	}[reg]
	var we := WorldEnvironment.new()
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sky.sky_material = sm
	sm.sky_top_color = tint[0]
	sm.sky_horizon_color = tint[1]
	sm.ground_horizon_color = tint[1]
	sm.ground_bottom_color = tint[1] * 0.7
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.9
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_white = 6.0
	env.ambient_light_sky_contribution = 0.55
	env.ambient_light_color = Color(0.75, 0.68, 0.58)
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.08
	env.adjustment_saturation = 1.12
	env.fog_enabled = true
	env.fog_light_color = tint[1]
	env.fog_density = 0.00042
	env.fog_aerial_perspective = 0.78
	we.environment = env
	top.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-38, 50, 0)
	sun.light_color = Color(1, 0.94, 0.84)
	sun.light_energy = 1.1
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 160
	top.add_child(sun)
	var w := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(9000, 9000)
	w.mesh = pm
	var wm := StandardMaterial3D.new()
	wm.albedo_color = {"A": Color(0.10, 0.38, 0.50), "B": Color(0.10, 0.36, 0.46), "frost": Color(0.20, 0.36, 0.48), "ash": Color(0.04, 0.10, 0.12)}[reg]
	wm.roughness = 0.18
	w.material_override = wm
	top.add_child(w)
	var terrain_shader := "res://shaders/vc_terrain_land4.gdshader" if after else "res://shaders/vc_terrain_land3.gdshader"
	for f in files:
		var p: String = f.path
		var n := glb(p)
		if n == null:
			push_warning("missing " + p)
			continue
		top.add_child(n)
		var mat: Material
		var b: String = p.get_file().get_basename()
		if after and bool(f.terrain):
			mat = sh(terrain_shader)
			mat.set_shader_parameter("region", ["A", "B", "frost", "ash"].find(reg))
			bind_terrain(mat)
			if reg == "ash":
				mat.set_shader_parameter("lift", 0.06)
				mat.set_shader_parameter("ambient", 0.45)
				mat.set_shader_parameter("spec", 0.12)
		elif (not after) and bool(f.terrain):
			mat = sh(terrain_shader)
			mat.set_shader_parameter("region", ["A", "B", "frost", "ash"].find(reg))
			if reg == "ash":
				mat.set_shader_parameter("lift", 0.1)
				mat.set_shader_parameter("ambient", 1.25)
				mat.set_shader_parameter("spec", 0.075)
		elif reg == "ash":
			mat = sh("res://vc_flat.gdshader")
			mat.set_shader_parameter("lift", 0.14)
			mat.set_shader_parameter("ambient", 1.2)
			mat.set_shader_parameter("spec", 0.075)
		else:
			mat = sh("res://vc_flat.gdshader")
			mat.set_shader_parameter("ambient", 0.35)
			mat.set_shader_parameter("lift", 0.03)
		for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false):
			mi.material_override = mat
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
