extends SceneTree
## Lightweight stills of the real placeholder horde and the real wall line.
## The full town's shader compile did not finish under software OpenGL here.
## godot --rendering-method gl_compatibility --path . -s res://tests/horde_shots.gd
var cam: Camera3D

func _initialize() -> void: _run.call_deferred()

func _run() -> void:
	DisplayServer.window_set_size(Vector2i(1280, 720))
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.62, 0.74, 0.84)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.75, 0.75, 0.7)
	env.ambient_light_energy = 0.8
	var we := WorldEnvironment.new()
	we.environment = env
	root.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, 30, 0)
	sun.shadow_enabled = false
	root.add_child(sun)
	_ground()
	_walls()
	_crowd()
	cam = Camera3D.new()
	cam.fov = 55
	cam.current = true
	root.add_child(cam)
	var ui := root.get_node_or_null("VUI")
	if ui and ui.get("title"): ui.title.hide()
	if ui and ui.get("hud"): ui.hud.visible = false
	for _i in 8: await process_frame
	_aim(Vector3(0, 6.0, 230), Vector3(0, 1.2, 204))
	await _save("horde_south_gate_crowd")
	_aim(Vector3(0, 3.4, 168), Vector3(0, 1.4, 210))
	await _save("horde_inside_looking_out")
	_aim(Vector3(0, 2.4, -214), Vector3(0, 1.4, -204))
	await _save("horde_placeholder_knight")
	_aim(Vector3(214, 2.4, 0), Vector3(204, 1.4, 0))
	await _save("horde_placeholder_sailor")
	var w := _wedge()
	_aim(Vector3(w.x, 8, w.y), Vector3(0, 2, 0))
	await _save("horde_escape_wedge")
	print("HORDE_SHOTS done")
	quit()

func _ground() -> void:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(520, 520)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.34, 0.42, 0.26)
	pm.material = mat
	mi.mesh = pm
	root.add_child(mi)

func _walls() -> void:
	var stone := StandardMaterial3D.new()
	stone.albedo_color = Color(0.55, 0.53, 0.48)
	var half := TownHaven.city_half()
	var t := TownHaven.wall_t()
	var h := TownHaven.wall_h()
	var g := TownHaven.gate_half()
	var span := half - g
	var cpos := (half + g) / 2.0
	for sd in [-1.0, 1.0]:
		_box(Vector3(sd * cpos, h * 0.5, half), Vector3(span, h, t), stone)
		_box(Vector3(sd * cpos, h * 0.5, -half), Vector3(span, h, t), stone)
		_box(Vector3(half, h * 0.5, sd * cpos), Vector3(t, h, span), stone)
		_box(Vector3(-half, h * 0.5, sd * cpos), Vector3(t, h, span), stone)

func _box(pos: Vector3, size: Vector3, mat: Material) -> void:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	bm.material = mat
	mi.mesh = bm
	mi.position = pos
	root.add_child(mi)

func _crowd() -> void:
	for slot in 48:
		var at := HordeCrowd.formation_xz(0, slot)
		var role_name: String = HordeCrowd.ROLE_NAME[0 if slot % 7 != 3 else 1]
		var z := HordeZombie.new()
		root.add_child(z)
		z.setup_horde(role_name, Vector3(at.x, 0.0, at.y), func(_x, _z): return 0.0)
		z.rotation.y = PI

func _wedge() -> Vector2:
	var a := deg_to_rad(135.0)
	return Vector2(sin(a), cos(a)) * (TownHaven.outer_limit() + 26.0)

func _aim(from: Vector3, at: Vector3) -> void:
	cam.global_position = from
	cam.look_at(at, Vector3.UP)

func _save(name: String) -> void:
	for _i in 4: await process_frame
	var img: Image = root.get_viewport().get_texture().get_image()
	var path := "/cursor/stores/self/transfer/test59-crowd/%s.png" % name
	DirAccess.make_dir_recursive_absolute("/cursor/stores/self/transfer/test59-crowd")
	img.save_png(path)
	print("SHOT %s %dx%d" % [path, img.get_width(), img.get_height()])
