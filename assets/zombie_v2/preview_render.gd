extends SceneTree
## Godot 4.7 Forward Mobile stills of the v2 villager.
## Software Vulkan (lavapipe), not a phone GPU.
## VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json xvfb-run -a godot --path . -s res://assets/zombie_v2/preview_render.gd

var cam: Camera3D
var out_dir := "/tmp/zombie_v2_godot"
const VILLAGER := "res://assets/zombie_v2/zombie_villager.glb"
const FAR := "res://assets/zombie_v2/zombie_far.glb"

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var env_out := OS.get_environment("ZOMBIE_OUT")
	if env_out != "":
		out_dir = env_out
	DirAccess.make_dir_recursive_absolute(out_dir)
	DisplayServer.window_set_size(Vector2i(960, 1200))
	_stage()
	await _frames(2)
	var ui := root.get_node_or_null("VUI")
	if ui:
		ui.hide()
	var z := _spawn(VILLAGER, Vector3.ZERO)
	if z == null:
		quit(1)
		return
	_report(z)
	await _frames(6)
	_pose(z, "idle", 0.8)
	await _frames(4)
	_aim(Vector3(0.22, 1.58, 0.85), Vector3(0.0, 1.52, 0.02))
	await _shot("01_face")
	_aim(Vector3(0.35, 1.15, 3.15), Vector3(0, 0.95, 0.0))
	await _shot("02_front")
	_aim(Vector3(3.15, 1.1, 0.35), Vector3(0, 0.95, 0.0))
	await _shot("03_side")
	_aim(Vector3(-0.15, 1.15, -3.15), Vector3(0, 0.95, 0.0))
	await _shot("04_back")
	for item in [["attack2", 0.45, "05_attack"], ["hit", 0.16, "06_hit"], ["death", 1.2, "07_death"], ["walk", 0.45, "08_walk"]]:
		_pose(z, item[0], item[1])
		await _frames(3)
		_log_pose(z, item[0])
		_aim(Vector3(0.7, 1.15, 2.7), Vector3(0, 0.95, 0.0))
		await _shot(item[2])
	z.queue_free()
	await _frames(2)
	_horde()
	await _frames(4)
	_aim(Vector3(2.2, 2.4, 7.5), Vector3(0, 0.7, 0))
	await _shot("09_group16")
	_clear()
	await _frames(2)
	_far()
	await _frames(3)
	_aim(Vector3(0, 6.5, 18.0), Vector3(0, 0.4, 0))
	await _shot("10_far_crowd")
	print("ZOMBIE_V2_SHOTS_DONE")
	quit(0)

func _stage() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.16, 0.16, 0.17)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.7, 0.72, 0.75)
	env.ambient_light_energy = 0.7
	var we := WorldEnvironment.new()
	we.environment = env
	root.add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-48, 32, 0)
	key.light_energy = 1.6
	key.shadow_enabled = false
	root.add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-20, -140, 0)
	fill.light_energy = 0.45
	root.add_child(fill)
	cam = Camera3D.new()
	cam.fov = 34
	cam.current = true
	root.add_child(cam)

func _spawn(path: String, at: Vector3) -> Node3D:
	var packed: PackedScene = load(path)
	if packed == null:
		push_error("load failed " + path)
		return null
	var inst := packed.instantiate() as Node3D
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
	var ap := _find(inst, "AnimationPlayer") as AnimationPlayer
	if ap == null or not ap.has_animation(clip):
		push_error("missing " + clip)
		return
	ap.play(clip)
	ap.seek(t, true)
	ap.advance(0.0)

func _log_pose(inst: Node, clip: String) -> void:
	var sk := _find(inst, "Skeleton3D") as Skeleton3D
	if sk == null:
		return
	var pairs := [["upperArm_L", "foreArm_L"], ["foreArm_L", "hand_L"], ["thigh_L", "shin_L"], ["shin_L", "foot_L"], ["neck", "head"]]
	var bits: PackedStringArray = []
	for p in pairs:
		var a := sk.find_bone(p[0])
		var b := sk.find_bone(p[1])
		if a < 0 or b < 0:
			continue
		var d := sk.get_bone_global_pose(a).origin.distance_to(sk.get_bone_global_pose(b).origin)
		bits.append("%s=%.3f" % [p[0], d])
	print("POSE %s %s" % [clip, " ".join(bits)])

func _report(inst: Node) -> void:
	var ap := _find(inst, "AnimationPlayer") as AnimationPlayer
	var sk := _find(inst, "Skeleton3D") as Skeleton3D
	var names: PackedStringArray = ap.get_animation_list() if ap else PackedStringArray()
	print("IMPORT bones=%d clips=%s" % [sk.get_bone_count() if sk else -1, ",".join(names)])
	var tris := 0
	var stack: Array = [inst]
	while stack.size():
		var n: Node = stack.pop_back()
		stack.append_array(n.get_children())
		if n is MeshInstance3D and (n as MeshInstance3D).mesh:
			var mi := n as MeshInstance3D
			for s in mi.mesh.get_surface_count():
				var arrays: Array = mi.mesh.surface_get_arrays(s)
				var idx = arrays[Mesh.ARRAY_INDEX]
				tris += int(idx.size() / 3) if idx != null else 0
	print("GODOT_TRIS", tris)

func _horde() -> void:
	for i in 16:
		var col := i % 4
		var row := i / 4
		var z := _spawn(VILLAGER, Vector3(col * 1.15 - 1.7, 0, row * 1.2 - 1.8))
		_pose(z, "idle" if i % 2 == 0 else "walk", 0.3 + 0.15 * (i % 5))

func _far() -> void:
	for i in 24:
		var col := i % 6
		var row := i / 6
		_spawn(FAR, Vector3(col * 1.3 - 3.2, 0, row * 1.3 - 2.0))

func _clear() -> void:
	for c in root.get_children():
		if c is Camera3D or c is DirectionalLight3D or c is WorldEnvironment:
			continue
		c.queue_free()

func _aim(eye: Vector3, at: Vector3) -> void:
	cam.global_position = eye
	cam.look_at(at, Vector3.UP)

func _shot(name: String) -> void:
	await _frames(2)
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out_dir + "/" + name + ".png")
	print("SHOT", name)

func _frames(n: int) -> void:
	for _i in n:
		await process_frame
