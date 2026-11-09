extends SceneTree
## Lit presentation pass for the hooded candidate. Does not touch gameplay.

const OUT := "/opt/cursor/artifacts/hooded_delivery"
const MOBILE := "res://assets/hooded_candidate/hooded_male_mobile.glb"
const FULL := "res://assets/hooded_candidate/hooded_male_full_game.glb"
const ATLAS := "res://assets/hooded_candidate/far_impostor/impostor_atlas_8dir_1024.png"
const Presenter := preload("res://validation/hooded_male/hooded_presenter.gd")

var world: Node3D
var cam: Camera3D
var report := {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	root.size = Vector2i(1280, 720)
	_stage()
	await process_frame
	await process_frame
	var hero = _spawn(MOBILE)
	await process_frame
	var face := _face_vector(hero)
	report["face_world"] = face
	report["face_dot_game_forward"] = face.dot(Vector3(0, 0, -1))
	report["game_forward"] = "yaw 0 looks down -Z. Presenter yaw is PI so the glTF +Z face lands on -Z."
	var attack := _attack_series(hero, face)
	report["attack2"] = attack
	await _attack_stills(hero, face, attack)
	await _blends(hero, face)
	await _rest_pair(face)
	await _impostors(hero, face)
	var f := FileAccess.open(OUT + "/report.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(_jsonify(report), "\t"))
	f.close()
	print("DELIVERY_DONE")
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
	plane.size = Vector2(60, 60)
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
	if path != MOBILE:
		n.use_model(path)
	return n

func _pose(n, clip: String, t: float) -> void:
	n.anim.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	n.anim.play(clip, -1, 1.0)
	n.anim.seek(t, true)
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
	var nose: Vector3 = acc / float(take)
	var face := nose - head
	face.y = 0.0
	if face.length() < 0.001:
		face = Vector3(0, 0, -1)
	return face.normalized()

func _attack_series(n, face: Vector3) -> Dictionary:
	var length: float = n.anim.get_animation("attack2").length
	var rows: Array = []
	var best_t := 0.0
	var best_fwd := -999.0
	var t := 0.0
	while t <= length + 0.001:
		_pose(n, "attack2", t)
		var chest := _bone(n, "chest")
		var hl := _bone(n, "hand_L")
		var hr := _bone(n, "hand_R")
		var fl: float = (hl - chest).dot(face)
		var fr: float = (hr - chest).dot(face)
		var fwd: float = maxf(fl, fr)
		if fwd > best_fwd:
			best_fwd = fwd
			best_t = t
		rows.append({
			"t": snappedf(t, 0.001),
			"hand_L": hl, "hand_R": hr,
			"fwd_L": snappedf(fl, 0.001), "fwd_R": snappedf(fr, 0.001),
		})
		t += 0.1
	return {"length": length, "samples": rows, "peak_t": best_t, "peak_forward_m": snappedf(best_fwd, 0.001)}

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
	s.name = "BiteTarget"
	world.add_child(s)
	return s

func _attack_stills(n, face: Vector3, attack: Dictionary) -> void:
	var mark := _marker(face)
	var times: Array = []
	for row in attack["samples"]:
		times.append(float(row["t"]))
	var i := 0
	for t in times:
		_pose(n, "attack2", float(t))
		await _draw()
		await _shot("attack_face_%02d" % i, _cam_face(face, 3.5), Vector3(0, 0.95, 0))
		await _shot("attack_side_%02d" % i, _cam_side(face, 3.6), Vector3(0, 0.95, 0))
		i += 1
	mark.visible = false

func _blends(n, face: Vector3) -> void:
	n.anim.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	for pair in [["idle", "attack2"], ["walk", "attack2"], ["run", "attack2"], ["walk", "hit"], ["walk", "death"]]:
		_pose(n, pair[0], 0.4)
		n.anim.play(pair[1], 0.30, 1.0)
		n.anim.advance(0.05)
		await _draw()
		await _shot("blend_%s_to_%s_005_face" % [pair[0], pair[1]], _cam_face(face, 3.5), Vector3(0, 0.95, 0))
		n.anim.advance(0.25)
		await _draw()
		await _shot("blend_%s_to_%s_030_face" % [pair[0], pair[1]], _cam_face(face, 3.5), Vector3(0, 0.95, 0))
		if pair[1] == "attack2" or pair[1] == "death":
			await _shot("blend_%s_to_%s_030_side" % [pair[0], pair[1]], _cam_side(face, 3.6), Vector3(0, 0.95, 0))

func _rest_pair(face: Vector3) -> void:
	for which in [["mobile", MOBILE], ["full", FULL]]:
		var n = _spawn(which[1])
		n.position = Vector3.ZERO
		_pose(n, "idle", 0.2)
		await _draw()
		await _shot("%s_face" % which[0], _cam_face(face, 3.5), Vector3(0, 0.95, 0))
		await _shot("%s_side" % which[0], _cam_side(face, 3.6), Vector3(0, 0.95, 0))
		n.visible = false

func _impostors(hero, face: Vector3) -> void:
	var shader := load("res://validation/hooded_male/impostor_billboard.gdshader") as Shader
	var mat := ShaderMaterial.new()
	mat.shader = shader
	mat.set_shader_parameter("atlas", load(ATLAS))
	mat.set_shader_parameter("fade", 1.0)
	mat.set_shader_parameter("view_bias", 4.0)
	var quad := _card_mesh()
	# One card beside the body, both facing -Z. Orbit the camera.
	var single := MeshInstance3D.new()
	single.mesh = quad
	single.material_override = mat
	single.position = Vector3(1.6, 0, 0)
	world.add_child(single)
	hero.position = Vector3(-0.2, 0, 0)
	_pose(hero, "idle", 0.0)
	hero.visible = true
	var angles := [0.0, 45.0, 90.0, 180.0, 270.0]
	for deg in angles:
		var rad := deg_to_rad(deg)
		var dir := Vector3(sin(rad), 0, -cos(rad))
		await _draw()
		await _shot("orbit_%03d" % int(deg), dir * 4.2 + Vector3(0.7, 1.15, 0), Vector3(0.7, 0.9, 0))
	single.visible = false
	hero.visible = false
	# 72 cards, mixed yaws, no skeletons. Camera from the front, the side, and behind.
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = quad
	mm.instance_count = 72
	for i in 72:
		var c := i % 12
		var r := int(i / 12)
		var yaw := float(i % 8) * TAU / 8.0
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(c * 1.35 - 7.4, 0, r * 1.5 - 1.0)))
		mm.set_instance_custom_data(i, Color(yaw, 0, 0, 1))
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = mat
	world.add_child(mmi)
	for deg2 in [0.0, 90.0, 180.0]:
		var rad2 := deg_to_rad(deg2)
		var dir2 := Vector3(sin(rad2), 0, -cos(rad2))
		await _draw()
		await _shot("crowd_%03d" % int(deg2), dir2 * 14.0 + Vector3(0, 5.5, 2.5), Vector3(0, 0.8, 2.5))
	mmi.visible = false
	# Near body fades into one card over 8–14 m. Same anchor, no second skeleton.
	hero.position = Vector3.ZERO
	hero.visible = true
	_pose(hero, "idle", 0.0)
	var card := MeshInstance3D.new()
	card.mesh = quad
	card.material_override = mat.duplicate()
	card.position = Vector3.ZERO
	world.add_child(card)
	_set_mesh_fade(hero, 1.0)
	for dist in [4.0, 8.0, 10.0, 11.5, 13.0, 16.0, 22.0]:
		var fade_card := clampf((dist - 8.0) / 6.0, 0.0, 1.0)
		var fade_mesh := 1.0 - fade_card
		(card.material_override as ShaderMaterial).set_shader_parameter("fade", fade_card)
		card.visible = fade_card > 0.02
		_set_mesh_fade(hero, fade_mesh)
		hero.visible = fade_mesh > 0.02
		await _draw()
		await _shot("transition_%04d" % int(dist * 10.0), face * dist + Vector3(0, 1.3, 0), Vector3(0, 0.9, 0))
	report["impostor"] = {
		"primary": "8-view atlas, Y-billboard, no skeleton",
		"cell": "4 columns x 2 rows, view 0 is the baked front",
		"transition_m": [8.0, 14.0],
		"far_mesh": "optional, not used for the crowd",
	}

func _set_mesh_fade(n, fade: float) -> void:
	var stack: Array = [n]
	while stack.size() > 0:
		var node: Node = stack.pop_back()
		if node is MeshInstance3D:
			var mi := node as MeshInstance3D
			if mi.mesh:
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
	var pts := PackedVector3Array([
		Vector3(-w, 0, 0), Vector3(w, 0, 0), Vector3(w, h, 0), Vector3(-w, h, 0),
	])
	var uvs := PackedVector2Array([
		Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1),
	])
	var idx := PackedInt32Array([0, 1, 2, 0, 2, 3])
	for k in idx:
		st.set_uv(uvs[k])
		st.add_vertex(pts[k])
	return st.commit()

func _cam_face(face: Vector3, dist: float) -> Vector3:
	return face * dist + Vector3(0, 1.15, 0)

func _cam_side(face: Vector3, dist: float) -> Vector3:
	var side := face.cross(Vector3.UP).normalized()
	return side * dist + Vector3(0, 1.1, 0)

func _first_mesh(n: Node) -> MeshInstance3D:
	if n is MeshInstance3D and (n as MeshInstance3D).mesh:
		return n
	for c in n.get_children():
		var m := _first_mesh(c)
		if m:
			return m
	return null

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
	img.save_png(OUT + "/" + name + ".png")

func _jsonify(v):
	if v is Vector3:
		return [snappedf(v.x, 0.001), snappedf(v.y, 0.001), snappedf(v.z, 0.001)]
	if v is Dictionary:
		var d := {}
		for k in v:
			d[str(k)] = _jsonify(v[k])
		return d
	if v is Array:
		var a: Array = []
		for i in v:
			a.append(_jsonify(i))
		return a
	return v
