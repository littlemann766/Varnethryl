extends SceneTree
## Interior screenshots per building: one 3/4 overview per floor (floors above shown as outline) + one eye-level
## view per room. VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json xvfb-run -a godot -s res://tests/interior_shots.gd [-- only=inn]
const B := preload("res://interiors/interior_builder.gd")
const DEF := preload("res://interiors/interior_defs.gd")
const T := preload("res://tests/interiors_test.gd")
var cam: Camera3D
var mgr: InteriorManager

func _initialize() -> void: _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await process_frame

func shot(path: String) -> void:
	await frames(4)
	root.get_viewport().get_texture().get_image().save_png(path)

func _run() -> void:
	root.size = Vector2i(960, 640)
	var only: Array = []
	for a in OS.get_cmdline_user_args(): if a.begins_with("only="): only = a.substr(5).split(",")
	var we := WorldEnvironment.new(); var env := Environment.new()
	env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.03, 0.025, 0.02)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.56, 0.54, 0.5); env.ambient_light_energy = 0.9
	env.tonemap_mode = Environment.TONE_MAPPER_ACES; env.tonemap_white = 6.0
	env.glow_enabled = true; env.glow_intensity = 0.6; env.glow_bloom = 0.08; env.glow_hdr_threshold = 1.0; env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.adjustment_enabled = true; env.adjustment_contrast = 1.08; env.adjustment_saturation = 1.12
	we.environment = env; root.add_child(we)
	cam = Camera3D.new(); cam.fov = 60; cam.cull_mask = 0xFFFFF; root.add_child(cam); cam.current = true
	var tst = T.new()
	for c in root.get_children(): if c is CanvasLayer: c.visible = false
	for c in root.get_children():
		for cc in c.get_children(): if cc is CanvasLayer: cc.visible = false
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://tests/shots/interiors"))
	for id in DEF.D:
		if only.size() and not only.has(id): continue
		var only_plans := OS.get_cmdline_user_args().has("plans")
		var info := B.build(id, DEF.D[id], tst.size_of(id)); root.add_child(info.node)
		mgr = InteriorManager.new(); root.add_child(mgr); mgr.cur = info
		var hero := MeshInstance3D.new(); var cap := CapsuleMesh.new(); cap.radius = 0.32; cap.height = 1.905; hero.mesh = cap
		var hm := StandardMaterial3D.new(); hm.albedo_color = Color(0.2, 0.35, 0.7); hero.material_override = hm; hero.layers = InteriorKit.LAYER; root.add_child(hero)
		var W: float = info.W; var D: float = info.D
		for i in info.floors.size():
			var F: Dictionary = info.floors[i]
			mgr._update_floors(F.y + 0.1)
			hero.position = Vector3(0, F.y + 0.95, D * 0.3 if i == 0 else 0.0)
			var r: float = max(W, D)
			cam.position = Vector3(0, F.y + r * 0.62, D * 0.5 + r * 0.3); cam.look_at(Vector3(0, F.y, -D * 0.05))
			await shot("res://tests/shots/interiors/%s_f%d.png" % [id, i])
		# orthographic floor plans (compare with the card's plan)
		for i in info.floors.size():
			var F2: Dictionary = info.floors[i]
			mgr._update_floors(F2.y + 0.1); cam.projection = Camera3D.PROJECTION_ORTHOGONAL; cam.size = maxf(W * 0.667, D) + 2.0
			cam.position = Vector3(0, F2.y + F2.h + 20.0, 0); cam.rotation = Vector3(-PI / 2, 0, 0)
			hero.position = Vector3(0, -50, 0)
			await shot("res://tests/shots/interiors/%s_p%d.png" % [id, i])
		cam.projection = Camera3D.PROJECTION_PERSPECTIVE
		var k := 0
		for rm in info.rooms:
			mgr._update_floors(rm.pos.y + 0.1)
			var p: Vector3 = rm.pos
			# stand back toward the room's nearest open side, look across the room at eye height
			var fh: float = info.floors[rm.floor].h
			cam.position = p + Vector3(0, fh + 2.5, 5.0)     # game-style cutaway camera over the walls
			cam.position.z = minf(cam.position.z, D / 2 + 1.0)
			cam.look_at(p + Vector3(0, 0.6, -1.0))
			hero.position = p + Vector3(0, 0.95, 0)
			await shot("res://tests/shots/interiors/%s_r%d.png" % [id, k]); k += 1
		hero.queue_free(); mgr.queue_free(); info.node.queue_free(); await frames(2)
		print("SHOTS ", id)
	quit()
