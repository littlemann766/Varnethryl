extends SceneTree
## Safety pass. Runs after the presentation fixes. Does not touch gameplay.
## Meant to be run from a fresh project as well as this one.

const OUT_DEFAULT := "/opt/cursor/artifacts/hooded_safety"
const MOBILE := "res://assets/hooded_candidate/hooded_male_mobile.glb"
const FULL := "res://assets/hooded_candidate/hooded_male_full_game.glb"
const ATLAS := "res://assets/hooded_candidate/far_impostor/impostor_atlas_8dir_1024.png"
const Presenter := preload("res://validation/hooded_male/hooded_presenter.gd")

var world: Node3D
var cam: Camera3D
var out_dir := OUT_DEFAULT
var report := {"checks": []}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var from_env := OS.get_environment("HOOD_OUT")
	if from_env != "":
		out_dir = from_env
	DirAccess.make_dir_recursive_absolute(out_dir)
	root.size = Vector2i(1280, 720)
	_stage()
	await process_frame
	await process_frame
	report["renderer"] = str(ProjectSettings.get_setting("rendering/renderer/rendering_method"))
	report["adapter"] = RenderingServer.get_video_adapter_name()
	report["display"] = DisplayServer.get_name()
	report["phone"] = "not tested"
	var hero = _spawn(MOBILE)
	await process_frame
	report["mobile_tris"] = _tris(hero)
	report["albedo_present"] = _has_albedo(hero)
	report["bones"] = hero.skel.get_bone_count() if hero.skel else 0
	report["clips"] = hero.clips
	var face: Vector3 = _face_vector(hero)
	report["face_dot_minus_z"] = face.dot(Vector3(0, 0, -1))
	var mark := _marker(face)
	await _clips(hero, face)
	await _blends(hero, face)
	await _interrupt(hero, face)
	mark.visible = true
	await _crowd(face)
	await _orbit(hero, face)
	await _transition(hero, face)
	var full = _spawn(FULL)
	await process_frame
	report["full_tris"] = _tris(full)
	report["full_albedo"] = _has_albedo(full)
	_pose(full, "idle", 0.4)
	await _shot("full_face", _cam_face(face, 3.5), Vector3(0, 0.95, 0))
	var f := FileAccess.open(out_dir + "/report.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(_jsonify(report), "\t"))
	f.close()
	print("SAFETY_DONE")
	quit(0)

func _stage() -> void:
	_hide_menu()
	world = Node3D.new()
	root.add_child(world)
	var envn := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.62, 0.62, 0.64)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.78, 0.78, 0.8)
	env.ambient_light_energy = 1.05
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.05
	envn.environment = env
	world.add_child(envn)
	_sun(Vector3(1.6, 3.4, -2.8), 2.4, 0.45)
	_sun(Vector3(-2.4, 2.2, -1.6), 1.15, 0.0)
	_sun(Vector3(0.2, 2.6, 3.2), 0.7, 0.0)
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(80, 80)
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.73, 0.72, 0.7)
	gm.roughness = 1.0
	plane.material = gm
	ground.mesh = plane
	world.add_child(ground)
	cam = Camera3D.new()
	cam.current = true
	cam.fov = 36
	world.add_child(cam)

func _sun(from: Vector3, energy: float, shadow: float) -> void:
	var L := DirectionalLight3D.new()
	world.add_child(L)
	L.global_position = from
	L.look_at(Vector3(0, 1.0, 0))
	L.light_energy = energy
	L.shadow_enabled = shadow > 0.0
	if shadow > 0.0:
		L.shadow_opacity = shadow

func _hide_menu() -> void:
	var stack: Array = [root]
	while stack.size() > 0:
		var n: Node = stack.pop_back()
		if n == world or n == cam:
			continue
		if n is CanvasItem and n != root:
			(n as CanvasItem).visible = false
		for c in n.get_children():
			stack.append(c)

func _spawn(path: String):
	var n = Presenter.new()
	world.add_child(n)
	if path != Presenter.MODEL:
		n.use_model(path)
	return n

func _pose(n, clip: String, t: float) -> void:
	n.anim.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	n.anim.play(clip, -1, 1.0)
	var length: float = n.anim.get_animation(clip).length
	n.anim.seek(clampf(t, 0.0, maxf(length - 0.001, 0.0)), true)
	n.anim.advance(0.0)
	if n.skel:
		n.skel.force_update_all_bone_transforms()

func _bone(n, nm: String) -> Vector3:
	var skel: Skeleton3D = n.skel
	var i: int = skel.find_bone(nm)
	return skel.global_transform * skel.get_bone_global_pose(i).origin

func _face_vector(n) -> Vector3:
	_pose(n, "idle", 0.0)
	var skel: Skeleton3D = n.skel
	var hi: int = skel.find_bone("head")
	var head: Vector3 = skel.global_transform * skel.get_bone_global_rest(hi).origin
	var mi := _first_mesh(n)
	var arrays: Array = mi.mesh.surface_get_arrays(0)
	var vs: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var xf: Transform3D = mi.global_transform
	var band: Array[Vector3] = []
	for v in vs:
		var w: Vector3 = xf * v
		if w.y > head.y - 0.04 and w.y < head.y + 0.16 and Vector2(w.x - head.x, w.z - head.z).length() < 0.2:
			band.append(w)
	band.sort_custom(func(a: Vector3, b: Vector3) -> bool: return a.z < b.z)
	var take := mini(40, band.size())
	var acc := Vector3.ZERO
	for i in take:
		acc += band[i]
	var face := (acc / float(take)) - head
	face.y = 0.0
	return face.normalized()

func _marker(face: Vector3) -> MeshInstance3D:
	var s := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.07
	sph.height = 0.14
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(0.95, 0.35, 0.05)
	sph.material = mat
	s.mesh = sph
	s.position = Vector3(0, 1.25, 0) + face * 1.15
	world.add_child(s)
	return s

func _clips(n, face: Vector3) -> void:
	var feet := {}
	for clip in ["idle", "walk", "run", "attack2", "hit", "death"]:
		var length: float = n.anim.get_animation(clip).length
		var times: Array = [0.0, length * 0.5, maxf(length - 0.02, 0.0)]
		if clip == "attack2":
			times = [0.0, 0.3, 0.8, maxf(length - 0.02, 0.0)]
		var i := 0
		for t in times:
			_pose(n, clip, float(t))
			var fl: float = _bone(n, "foot_L").y
			var fr: float = _bone(n, "foot_R").y
			feet["%s_%02d" % [clip, i]] = {"t": t, "foot_L_y": fl, "foot_R_y": fr}
			await _draw()
			await _shot("%s_%02d_face" % [clip, i], _cam_face(face, 3.5), Vector3(0, 0.95, 0))
			if clip in ["walk", "run", "attack2", "death"]:
				await _shot("%s_%02d_side" % [clip, i], _cam_side(face, 3.6), Vector3(0, 0.95, 0))
			i += 1
		if clip in ["idle", "walk", "run"]:
			_pose(n, clip, 0.35 + length * 3.0)
			await _draw()
			await _shot("%s_cycle3_side" % clip, _cam_side(face, 3.6), Vector3(0, 0.95, 0))
	# Death held past the end. LOOP_NONE must not snap back to the bind pose.
	var death_len: float = n.anim.get_animation("death").length
	_pose(n, "death", death_len - 0.02)
	n.anim.advance(1.5)
	if n.skel:
		n.skel.force_update_all_bone_transforms()
	await _draw()
	await _shot("death_hold_side", _cam_side(face, 3.8), Vector3(0, 0.7, 0))
	report["feet"] = feet
	report["checks"].append("six clips, first mid end, loops x3, death held 1.5s past the end")

func _blends(n, face: Vector3) -> void:
	n.anim.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	for pair in [["idle", "attack2"], ["walk", "attack2"], ["run", "attack2"], ["walk", "hit"], ["walk", "death"]]:
		_pose(n, pair[0], 0.4)
		n.anim.play(pair[1], 0.30, 1.0)
		n.anim.advance(0.08)
		await _draw()
		await _shot("blend_%s_%s_008_face" % [pair[0], pair[1]], _cam_face(face, 3.5), Vector3(0, 0.95, 0))
		n.anim.advance(0.22)
		await _draw()
		await _shot("blend_%s_%s_030_side" % [pair[0], pair[1]], _cam_side(face, 3.6), Vector3(0, 0.95, 0))
	report["checks"].append("idle walk run into attack, walk into hit and death, 0.30s blend")

func _interrupt(n, face: Vector3) -> void:
	_pose(n, "attack2", 0.55)
	n.anim.play("hit", 0.25, 1.0)
	n.anim.advance(0.12)
	await _draw()
	await _shot("interrupt_attack_hit_face", _cam_face(face, 3.5), Vector3(0, 0.95, 0))
	await _shot("interrupt_attack_hit_side", _cam_side(face, 3.6), Vector3(0, 0.95, 0))
	n.anim.play("death", 0.30, 1.0)
	n.anim.advance(0.35)
	await _draw()
	await _shot("interrupt_attack_death_side", _cam_side(face, 3.8), Vector3(0, 0.8, 0))
	report["checks"].append("attack interrupted into hit, then into death")

func _crowd(face: Vector3) -> void:
	var bodies: Array = []
	var clips := ["idle", "walk", "run", "attack2", "hit", "death"]
	for i in 16:
		var n = _spawn(MOBILE)
		var col := i % 4
		var row := int(i / 4)
		n.position = Vector3(col * 1.7 - 2.55, 0, row * 1.6)
		bodies.append(n)
	var mm := _crowd_mesh()
	for phase in [0.0, 0.45, 1.05]:
		for i in bodies.size():
			var clip: String = clips[i % clips.size()]
			_pose(bodies[i], clip, phase + float(i) * 0.07)
		await _draw()
		await _shot("crowd_phase_%02d" % int(phase * 10.0), Vector3(0, 5.2, 12.0), Vector3(0, 0.7, 1.0))
	for b in bodies:
		(b as Node3D).visible = false
	mm.visible = false
	report["checks"].append("16 skinned bodies plus 72 impostors, three phases")

func _crowd_mesh() -> MultiMeshInstance3D:
	var shader := load("res://validation/hooded_male/impostor_billboard.gdshader") as Shader
	var mat := ShaderMaterial.new()
	mat.shader = shader
	mat.set_shader_parameter("atlas", load(ATLAS))
	mat.set_shader_parameter("fade", 1.0)
	mat.set_shader_parameter("view_bias", 4.0)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = _card_mesh()
	mm.instance_count = 72
	for i in 72:
		var c := i % 12
		var r := int(i / 12)
		var yaw := float(i % 8) * TAU / 8.0
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(c * 1.35 - 7.4, 0, -4.5 - r * 1.45)))
		mm.set_instance_custom_data(i, Color(yaw, 0, 0, 1))
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = mat
	world.add_child(mmi)
	return mmi

func _orbit(hero, face: Vector3) -> void:
	var shader := load("res://validation/hooded_male/impostor_billboard.gdshader") as Shader
	var mat := ShaderMaterial.new()
	mat.shader = shader
	mat.set_shader_parameter("atlas", load(ATLAS))
	mat.set_shader_parameter("fade", 1.0)
	mat.set_shader_parameter("view_bias", 4.0)
	var card := MeshInstance3D.new()
	card.mesh = _card_mesh()
	card.material_override = mat
	card.position = Vector3(1.5, 0, 0)
	world.add_child(card)
	hero.position = Vector3(-0.9, 0, 0)
	hero.visible = true
	_pose(hero, "idle", 0.5)
	for deg in [0, 45, 90, 135, 180, 225, 270, 315]:
		var rad := deg_to_rad(float(deg))
		var dir := Vector3(sin(rad), 0, -cos(rad))
		await _draw()
		await _shot("orbit_%03d" % deg, dir * 4.4 + Vector3(0.3, 1.2, 0), Vector3(0.3, 0.9, 0))
	card.visible = false
	hero.position = Vector3.ZERO
	report["checks"].append("orbit 360, mesh beside billboard")

func _transition(hero, face: Vector3) -> void:
	var shader := load("res://validation/hooded_male/impostor_billboard.gdshader") as Shader
	var mat := ShaderMaterial.new()
	mat.shader = shader
	mat.set_shader_parameter("atlas", load(ATLAS))
	mat.set_shader_parameter("view_bias", 4.0)
	var card := MeshInstance3D.new()
	card.mesh = _card_mesh()
	card.material_override = mat
	card.position = Vector3.ZERO
	world.add_child(card)
	hero.position = Vector3.ZERO
	_pose(hero, "idle", 0.4)
	var seq: Array = [
		["go", 4.0], ["go", 8.0], ["go", 11.0], ["go", 14.0], ["go", 18.0],
		["back", 14.0], ["back", 11.0], ["back", 8.0], ["back", 4.0],
	]
	for step in seq:
		var dist: float = float(step[1])
		var fade_card := clampf((dist - 8.0) / 6.0, 0.0, 1.0)
		var fade_mesh := 1.0 - fade_card
		(card.material_override as ShaderMaterial).set_shader_parameter("fade", fade_card)
		card.visible = fade_card > 0.02
		_set_mesh_fade(hero, fade_mesh)
		hero.visible = fade_mesh > 0.02
		await _draw()
		await _shot("transition_%s_%04d" % [step[0], int(dist * 10.0)], face * dist + Vector3(0, 1.35, 0), Vector3(0, 0.9, 0))
	report["checks"].append("near to far and back, 8m to 14m dither")

func _set_mesh_fade(n, fade: float) -> void:
	var stack: Array = [n]
	while stack.size() > 0:
		var node: Node = stack.pop_back()
		if node is MeshInstance3D:
			var mi := node as MeshInstance3D
			if mi.mesh and mi.name != "BiteTarget":
				for s in mi.mesh.get_surface_count():
					var base: Material = mi.get_surface_override_material(s)
					if base == null:
						base = mi.mesh.surface_get_material(s)
					if base is StandardMaterial3D:
						var sm := (base as StandardMaterial3D).duplicate() as StandardMaterial3D
						sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if fade < 0.98 else BaseMaterial3D.TRANSPARENCY_DISABLED
						sm.albedo_color.a = fade
						sm.cull_mode = BaseMaterial3D.CULL_DISABLED
						mi.set_surface_override_material(s, sm)
		for c in node.get_children():
			stack.append(c)

func _card_mesh() -> ArrayMesh:
	var w := 1.0687 * 0.5
	var h := 2.1374
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pts := PackedVector3Array([Vector3(-w, 0, 0), Vector3(w, 0, 0), Vector3(w, h, 0), Vector3(-w, h, 0)])
	var uvs := PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])
	var idx := PackedInt32Array([0, 1, 2, 0, 2, 3])
	for k in idx:
		st.set_uv(uvs[k])
		st.add_vertex(pts[k])
	return st.commit()

func _cam_face(face: Vector3, dist: float) -> Vector3:
	return face * dist + Vector3(0, 1.15, 0)

func _cam_side(face: Vector3, dist: float) -> Vector3:
	return face.cross(Vector3.UP).normalized() * dist + Vector3(0, 1.1, 0)

func _first_mesh(n: Node) -> MeshInstance3D:
	if n is MeshInstance3D and (n as MeshInstance3D).mesh:
		return n
	for c in n.get_children():
		var m := _first_mesh(c)
		if m:
			return m
	return null

func _tris(n: Node) -> int:
	var count := 0
	if n is MeshInstance3D and (n as MeshInstance3D).mesh:
		var mi := n as MeshInstance3D
		for s in mi.mesh.get_surface_count():
			var arrays: Array = mi.mesh.surface_get_arrays(s)
			var idx: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
			count += idx.size() / 3
	for c in n.get_children():
		count += _tris(c)
	return count

func _has_albedo(n: Node) -> bool:
	if n is MeshInstance3D and (n as MeshInstance3D).mesh:
		var mi := n as MeshInstance3D
		var m: Material = mi.get_active_material(0)
		if m == null:
			m = mi.mesh.surface_get_material(0)
		if m is StandardMaterial3D:
			return (m as StandardMaterial3D).albedo_texture != null
	for c in n.get_children():
		if _has_albedo(c):
			return true
	return false

func _draw() -> void:
	await process_frame

func _shot(name: String, from: Vector3, at: Vector3) -> void:
	_hide_menu()
	cam.current = true
	cam.global_position = from
	cam.look_at(at, Vector3.UP)
	await process_frame
	await process_frame
	var img := root.get_texture().get_image()
	if img == null:
		push_error("no image " + name)
		return
	img.save_png(out_dir + "/" + name + ".png")

func _jsonify(v):
	if v is Vector3:
		return [snappedf(v.x, 0.001), snappedf(v.y, 0.001), snappedf(v.z, 0.001)]
	if v is Dictionary:
		var d := {}
		for k in v:
			d[str(k)] = _jsonify(v[k])
		return d
	if v is Array or v is PackedStringArray:
		var a: Array = []
		for i in v:
			a.append(_jsonify(i))
		return a
	return v
