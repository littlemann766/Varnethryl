extends SceneTree
## Stage 5 before/after: region base terrain + props near the landing, with / without the island patch. args: outdir id tier(High|Low) mode(before|after)
var top: Node3D
func glb(p: String) -> Node3D:
	var d := GLTFDocument.new(); var s := GLTFState.new()
	if d.append_from_file(ProjectSettings.globalize_path(p), s) != OK: return null
	return d.generate_scene(s)
func vcmat(ash: bool) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.vertex_color_use_as_albedo = true; m.roughness = 0.9
	if ash: m.metallic_specular = 0.15
	return m
func add(p: String, mat: Material, shadow: bool) -> void:
	var n := glb(p)
	if n == null: return
	top.add_child(n)
	for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = mat; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var a := OS.get_cmdline_user_args(); var out := a[0]; var id := a[1]; var low := a[2] == "Low"; var after := a[3] == "after"
	top = Node3D.new(); get_root().add_child(top); get_root().size = Vector2i(1280, 720)
	var man: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://stage5_manifest.json")); var I: Dictionary = man.islands[id]
	var reg: String = I.region; var ash := reg == "ash"
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://files.json"))
	var vc := vcmat(ash); var glow := ShaderMaterial.new(); glow.shader = load("res://shaders/glow_vc.gdshader")
	for f in cfg[reg]:
		var b: String = f.get_file().get_basename()
		var lo := "res://base/" + b + "_lod1.glb"
		var p := lo if low and FileAccess.file_exists(lo) else "res://base/" + b + ".glb"
		add(p, glow if b.ends_with("_glow") else vc, not low and not b.ends_with("_glow"))
	if after:
		var nm: String = I.files.mesh
		add("res://isl/%s%s.glb" % [nm, "_lod1" if low else ""], vc, not low)
		if I.files.glow != null: add("res://isl/%s.glb" % I.files.glow, glow, false)
		for po in I.pois:
			var ol := OmniLight3D.new(); ol.light_color = Color(1, 0.75, 0.45); ol.light_energy = 1.5; ol.omni_range = 12; top.add_child(ol); ol.position = Vector3(po.pos[0], po.pos[1] + 2.5, po.pos[2])
	var we := WorldEnvironment.new(); var env := Environment.new(); var sky := Sky.new(); var sm := ProceduralSkyMaterial.new(); sky.sky_material = sm
	var tint: Array = {"A": [Color(0.3, 0.48, 0.72), Color(0.74, 0.8, 0.86)], "B": [Color(0.32, 0.46, 0.66), Color(0.78, 0.8, 0.84)], "frost": [Color(0.5, 0.6, 0.72), Color(0.86, 0.9, 0.94)], "ash": [Color(0.22, 0.22, 0.25), Color(0.36, 0.33, 0.32)]}[reg]
	sm.sky_top_color = tint[0]; sm.sky_horizon_color = tint[1]; sm.ground_horizon_color = tint[1]; sm.ground_bottom_color = tint[1] * 0.7
	env.background_mode = Environment.BG_SKY; env.sky = sky; env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.ambient_light_energy = 1.7 if ash else 1.0; env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.fog_enabled = true; env.fog_light_color = tint[1]; env.fog_density = 0.0006 if ash else 0.00025; env.glow_enabled = not low; we.environment = env; top.add_child(we)
	var sun := DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-38, 50, 0); sun.light_color = Color(1, 0.93, 0.82); sun.light_energy = 1.5 if ash else 1.0; sun.shadow_enabled = false;   # render-only: the Mobile PSSM acne-stripes on these big gentle slopes; the game lights it its own way
	sun.directional_shadow_max_distance = 120; sun.shadow_bias = 0.1; sun.shadow_normal_bias = 8.0; sun.directional_shadow_split_1 = 0.15; sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL; top.add_child(sun)
	var w := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(3000, 3000); w.mesh = pm; var wm := StandardMaterial3D.new()
	wm.albedo_color = Color(0,0,0) if false else ({"A": Color(0.1, 0.38, 0.5), "B": Color(0.1, 0.36, 0.46), "frost": Color(0.2, 0.36, 0.48), "ash": Color(0.04, 0.1, 0.12)}[reg] as Color); wm.roughness = 0.3; w.material_override = wm; top.add_child(w)
	w.position = Vector3(I.pier_head[0], 0, I.pier_head[2])
	var cam := Camera3D.new(); top.add_child(cam); cam.current = true; cam.far = 3000
	for sh in [["inland", "inland_look", 62.0], ["over", "over_look", 55.0]]:
		var c: Array = I.cams[sh[0]]; var l: Array = I.cams[sh[1]]
		cam.fov = sh[2]; cam.look_at_from_position(Vector3(c[0], c[1], c[2]), Vector3(l[0], l[1], l[2]), Vector3.UP)
		for i in 4: await process_frame
		get_root().get_texture().get_image().save_jpg("%s/%s_%s_%s_%s.jpg" % [out, id, sh[0], a[2], a[3]], 0.85)
	if after:
		var n := 0
		for po in I.pois:
			var p := Vector3(po.pos[0], po.pos[1], po.pos[2]); var ph := Vector3(I.pier_head[0], p.y, I.pier_head[2]); var d := (ph - p).normalized()
			var rr := float(po.radius) * 2.2 + 8.0
			cam.fov = 60; cam.look_at_from_position(p + d * rr * 0.55 + Vector3(0, rr * 0.95 + 4, 0), p + Vector3(0, 1.0, 0), Vector3.UP)   # steep look-down: never inside the hill between POI and pier
			for i in 4: await process_frame
			get_root().get_texture().get_image().save_jpg("%s/%s_poi%d_%s.jpg" % [out, id, n, a[2]], 0.85); n += 1
	print("SHOTS ", id); quit()
