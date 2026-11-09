extends SceneTree
## Still renders of the original zombie meshes on the game's humanoid clips.
## Software Vulkan via lavapipe is not a phone test.
## VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json xvfb-run -a godot --path . -s res://assets/zombie/preview_render.gd

var cam: Camera3D
var out_dir := "/tmp/zombie_godot"

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var env_out := OS.get_environment("ZOMBIE_OUT")
	if env_out != "":
		out_dir = env_out
	DirAccess.make_dir_recursive_absolute(out_dir)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	_stage()
	await _frames(2)
	var ui := root.get_node_or_null("VUI")
	if ui:
		ui.hide()
	var stats = _stats()
	var times: Dictionary = stats.get("pose_times", {})
	var female := _spawn("res://assets/zombie/zombie_female_villager.glb", Vector3.ZERO)
	if female == null:
		push_error("combat mesh did not import")
		quit(1)
		return
	_report_mesh(female, "female_villager")
	await _frames(8)
	_pose(female, "idle", float(times.get("idle", 1.25)))
	await _frames(6)
	_aim(Vector3(0.35, 1.15, 3.05), Vector3(0, 0.95, 0.05))
	await _shot("01_front")
	_aim(Vector3(3.05, 1.1, 0.45), Vector3(0, 0.95, 0.05))
	await _shot("02_side")
	_aim(Vector3(-0.2, 1.15, -3.05), Vector3(0, 0.95, 0.0))
	await _shot("03_back")
	_aim(Vector3(0.28, 1.62, 0.72), Vector3(0.0, 1.55, 0.08))
	await _shot("04_face")
	for clip in ["idle", "walk", "run", "attack1", "attack2", "attack3", "hit", "death"]:
		_pose(female, clip, float(times.get(clip, 0.4)))
		await _frames(3)
		_log_pose(female, clip)
	_pose(female, "walk", float(times.get("walk", 0.4)))
	await _frames(4)
	_aim(Vector3(0.55, 1.05, 3.1), Vector3(0, 0.9, 0.1))
	await _shot("05_walk")
	_pose(female, "attack2", float(times.get("attack2", 0.47)))
	await _frames(3)
	_aim(Vector3(0.8, 1.15, 2.6), Vector3(0, 1.0, 0.05))
	await _shot("06_attack")
	_pose(female, "hit", float(times.get("hit", 0.17)))
	await _frames(3)
	_aim(Vector3(0.4, 1.1, 2.8), Vector3(0, 1.0, 0.0))
	await _shot("07_hit")
	_pose(female, "death", float(times.get("death", 1.5)))
	await _frames(4)
	_aim(Vector3(2.4, 1.35, 0.4), Vector3(0.1, 0.45, -0.35))
	await _shot("08_death")
	female.queue_free()
	await _frames(2)
	await _lineup(times)
	await _shot("09_variants")
	_clear_cast()
	await _frames(2)
	await _horde(times)
	await _shot("10_group16")
	_clear_cast()
	await _frames(2)
	await _far_compare(times)
	await _shot("11_far_crowd")
	print("ZOMBIE_SHOTS_DONE")
	quit(0)

func _stage() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.145, 0.145, 0.155)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.62, 0.64, 0.68)
	env.ambient_light_energy = 0.55
	var we := WorldEnvironment.new()
	we.environment = env
	root.add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-42, 28, 0)
	key.light_energy = 1.25
	key.shadow_enabled = false
	root.add_child(key)
	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-18, 200, 0)
	rim.light_energy = 0.45
	rim.light_color = Color(0.75, 0.8, 0.9)
	root.add_child(rim)
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(40, 40)
	var gmat := StandardMaterial3D.new()
	gmat.albedo_color = Color(0.11, 0.11, 0.12)
	gmat.roughness = 1.0
	plane.material = gmat
	ground.mesh = plane
	root.add_child(ground)
	cam = Camera3D.new()
	cam.fov = 32
	cam.current = true
	root.add_child(cam)

func _stats() -> Dictionary:
	var f := FileAccess.open("res://assets/zombie/STATS.json", FileAccess.READ)
	if f == null:
		return {}
	var parsed = JSON.parse_string(f.get_as_text())
	return parsed if parsed is Dictionary else {}

func _spawn(path: String, at: Vector3) -> Node3D:
	if not ResourceLoader.exists(path):
		push_error("missing %s" % path)
		return null
	var packed: PackedScene = load(path)
	if packed == null:
		push_error("failed to load %s" % path)
		return null
	var inst := packed.instantiate() as Node3D
	if inst == null:
		push_error("failed to instance %s" % path)
		return null
	inst.position = at
	root.add_child(inst)
	return inst

func _find(n: Node, klass: String) -> Node:
	if n.is_class(klass):
		return n
	for c in n.get_children():
		var f := _find(c, klass)
		if f:
			return f
	return null

func _pose(inst: Node, clip: String, t: float) -> void:
	if inst == null:
		return
	var ap := _find(inst, "AnimationPlayer") as AnimationPlayer
	if ap == null:
		push_error("no AnimationPlayer on %s" % inst.name)
		return
	if not ap.has_animation(clip):
		push_error("missing clip %s" % clip)
		return
	ap.play(clip)
	ap.seek(t, true)
	ap.advance(0.0)

func _log_pose(inst: Node, clip: String) -> void:
	var sk := _find(inst, "Skeleton3D") as Skeleton3D
	if sk == null:
		print("POSE", clip, "no skeleton")
		return
	var pairs := [["shoulder_L", "upperArm_L"], ["upperArm_L", "foreArm_L"], ["foreArm_L", "hand_L"], ["thigh_L", "shin_L"], ["shin_L", "foot_L"], ["chest", "neck"], ["neck", "head"]]
	var bits := []
	for p in pairs:
		var a := sk.find_bone(p[0])
		var b := sk.find_bone(p[1])
		if a < 0 or b < 0:
			bits.append("%s missing" % p[0])
			continue
		var d := sk.get_bone_global_pose(a).origin.distance_to(sk.get_bone_global_pose(b).origin)
		bits.append("%s=%.3f" % [p[0], d])
	print("POSE %s %s" % [clip, " ".join(bits)])

func _report_mesh(inst: Node, label: String) -> void:
	var ap := _find(inst, "AnimationPlayer") as AnimationPlayer
	var sk := _find(inst, "Skeleton3D") as Skeleton3D
	var mi := _find(inst, "MeshInstance3D") as MeshInstance3D
	var names: PackedStringArray = ap.get_animation_list() if ap else PackedStringArray()
	print("IMPORT %s bones=%d clips=%s" % [label, sk.get_bone_count() if sk else -1, ",".join(names)])
	if mi and mi.mesh:
		var tris := 0
		for s in mi.mesh.get_surface_count():
			var arrays: Array = mi.mesh.surface_get_arrays(s)
			var idx = arrays[Mesh.ARRAY_INDEX]
			tris += int(idx.size() / 3) if idx != null else 0
			var mat := mi.get_active_material(s)
			var info := ""
			if mat is StandardMaterial3D:
				var sm := mat as StandardMaterial3D
				info = "transparency=%s albedo=%s normal=%s orm=%s" % [sm.transparency, sm.albedo_texture != null, sm.normal_texture != null, sm.orm_texture != null]
			print(" SURFACE %d %s" % [s, info])
		print("GODOT_TRIS %s %d" % [label, tris])

func _lineup(times: Dictionary) -> void:
	var files := [
		"res://assets/zombie/zombie_female_villager.glb",
		"res://assets/zombie/zombie_male_villager.glb",
		"res://assets/zombie/zombie_male_sailor.glb",
		"res://assets/zombie/zombie_male_knight.glb",
	]
	for i in files.size():
		var n := _spawn(files[i], Vector3((i - 1.5) * 1.55, 0, 0))
		if n:
			_pose(n, "idle", float(times.get("idle", 1.25)))
	await _frames(4)
	_aim(Vector3(0.2, 1.35, 7.4), Vector3(0, 0.9, 0))
	cam.fov = 34

func _horde(times: Dictionary) -> void:
	var files := [
		"res://assets/zombie/zombie_female_villager.glb",
		"res://assets/zombie/zombie_male_villager.glb",
		"res://assets/zombie/zombie_male_sailor.glb",
		"res://assets/zombie/zombie_male_knight.glb",
	]
	var n := 0
	for row in 4:
		for col in 4:
			var inst := _spawn(files[n % 4], Vector3((col - 1.5) * 0.95, 0, (row - 1.5) * 0.95))
			if inst:
				inst.rotation.y = (n - 8) * 0.18
				_pose(inst, "idle", float(times.get("idle", 1.25)) + (n % 5) * 0.07)
			n += 1
	await _frames(5)
	cam.fov = 38
	_aim(Vector3(1.2, 2.4, 7.2), Vector3(0, 0.8, 0))

func _far_compare(times: Dictionary) -> void:
	var hero := _spawn("res://assets/zombie/zombie_female_villager.glb", Vector3(-1.4, 0, 0))
	_pose(hero, "idle", float(times.get("idle", 1.25)))
	for i in 6:
		var lod := _spawn("res://assets/zombie/zombie_far_lod.glb", Vector3(0.4 + (i % 3) * 0.7, 0, -0.2 + int(i / 3) * 0.7))
		if lod:
			lod.rotation.y = i * 0.4
	for i in 4:
		_spawn("res://assets/zombie/zombie_far_impostor.glb", Vector3(2.8 + (i % 2) * 0.55, 0, -0.15 + int(i / 2) * 0.6))
	await _frames(4)
	cam.fov = 36
	_aim(Vector3(1.2, 1.6, 8.5), Vector3(1.0, 0.85, 0))

func _clear_cast() -> void:
	for c in root.get_children():
		if c == cam:
			continue
		if c is DirectionalLight3D or c is WorldEnvironment or c is Camera3D:
			continue
		if c is MeshInstance3D and c.name == "Ground":
			continue
		# ground plane was unnamed; keep the first PlaneMesh
		if c is MeshInstance3D and (c as MeshInstance3D).mesh is PlaneMesh:
			continue
		c.queue_free()

func _aim(from: Vector3, at: Vector3) -> void:
	cam.global_position = from
	cam.look_at(at, Vector3.UP)

func _frames(n: int) -> void:
	for i in n:
		await process_frame

func _shot(name: String) -> void:
	await _frames(4)
	var img := root.get_viewport().get_texture().get_image()
	var path := "%s/%s.png" % [out_dir, name]
	img.save_png(path)
	print("SHOT ", path, " ", img.get_width(), "x", img.get_height())
