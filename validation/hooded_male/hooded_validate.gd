extends SceneTree
## Isolated Godot 4.7 mobile-renderer check for the hooded candidate.
## Run with a real window. Does not change gameplay scenes.

const OUT := "/opt/cursor/artifacts/hooded_validate"
const FULL := "res://assets/hooded_candidate/hooded_male_full_game.glb"
const MOBILE := "res://assets/hooded_candidate/hooded_male_mobile.glb"
const FAR := "res://assets/hooded_candidate/far_impostor/hooded_male_far.glb"
const CARD := "res://assets/hooded_candidate/far_impostor/impostor_card.glb"
const Presenter := preload("res://validation/hooded_male/hooded_presenter.gd")

var world: Node3D
var cam: Camera3D
var report := {}
var hide_bin: Node3D

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	root.size = Vector2i(1280, 720)
	root.mode = Window.MODE_WINDOWED
	root.title = "hooded validate"
	report["godot"] = Engine.get_version_info()
	report["renderer"] = str(ProjectSettings.get_setting("rendering/renderer/rendering_method"))
	report["adapter"] = RenderingServer.get_video_adapter_name()
	report["adapter_vendor"] = RenderingServer.get_video_adapter_vendor()
	report["driver"] = OS.get_video_adapter_driver_info()
	report["display"] = DisplayServer.get_name()
	_stage()
	await process_frame
	await process_frame
	var info := {}
	info["full"] = await _inspect(FULL)
	info["mobile"] = await _inspect(MOBILE)
	info["far"] = await _inspect(FAR)
	info["card"] = await _inspect(CARD)
	report["assets"] = info
	_hierarchy(info)
	await _stills()
	await _transitions()
	await _crowd()
	await _lod()
	await _adapter()
	await _clock()
	var f := FileAccess.open(OUT + "/report.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(_jsonify(report), "\t"))
	f.close()
	print("VALIDATE_DONE")
	quit(0)

func _stage() -> void:
	_hide_menu()
	world = Node3D.new()
	world.name = "World"
	root.add_child(world)
	var envn := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.46, 0.46, 0.48)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.42, 0.42, 0.44)
	env.ambient_light_energy = 0.55
	envn.environment = env
	world.add_child(envn)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, 35, 0)
	sun.light_energy = 1.35
	sun.shadow_enabled = true
	world.add_child(sun)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-18, -150, 0)
	fill.light_energy = 0.4
	world.add_child(fill)
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(80, 80)
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.62, 0.61, 0.58)
	plane.material = gm
	ground.mesh = plane
	world.add_child(ground)
	cam = Camera3D.new()
	cam.current = true
	cam.fov = 40
	world.add_child(cam)
	hide_bin = Node3D.new()
	hide_bin.name = "Bin"
	world.add_child(hide_bin)

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

func _spawn(path: String) -> Node3D:
	var n := Presenter.new()
	hide_bin.add_child(n)
	n.use_model(path)
	return n

func _inspect(path: String) -> Dictionary:
	var n := _spawn(path)
	await process_frame
	var d := {
		"path": path,
		"notes": n.notes,
		"clips": [],
		"bones": [],
		"tris": 0,
		"aabb": [],
		"materials": [],
	}
	if n.anim:
		for c in n.anim.get_animation_list():
			var a: Animation = n.anim.get_animation(c)
			var tracks := []
			for t in mini(a.get_track_count(), 3):
				tracks.append(str(a.track_get_path(t)))
			d["clips"].append({
				"name": c,
				"length": a.length,
				"loop": a.loop_mode,
				"tracks": a.get_track_count(),
				"sample_paths": tracks,
			})
	if n.skel:
		for i in n.skel.get_bone_count():
			var p: int = n.skel.get_bone_parent(i)
			d["bones"].append({
				"i": i,
				"name": n.skel.get_bone_name(i),
				"parent": n.skel.get_bone_name(p) if p >= 0 else "",
			})
	d["tris"] = _tris(n)
	var box := _aabb(n)
	d["aabb"] = [box.position, box.position + box.size]
	d["materials"] = _mats(n)
	n.visible = false
	return d

func _hierarchy(info: Dictionary) -> void:
	var bones: Array = info["mobile"]["bones"]
	var parents := {}
	for b in bones:
		parents[b["name"]] = b["parent"]
	report["bone_count"] = bones.size()
	report["shoulders_and_thighs_are_root_siblings"] = (
		parents.get("shoulder_L", "?") == ""
		and parents.get("shoulder_R", "?") == ""
		and parents.get("thigh_L", "?") == ""
		and parents.get("thigh_R", "?") == ""
		and parents.get("hips", "?") == ""
	)
	report["cloak_back_parent"] = parents.get("cloak_back", "MISSING")
	report["bone_names"] = parents.keys()

func _stills() -> void:
	var shots := []
	for which in [["full", FULL], ["mobile", MOBILE]]:
		var n = _spawn(which[1])
		n.position = Vector3.ZERO
		await process_frame
		# Rest, before any clip seek. The import pose is the embedded rest.
		n.anim.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		n.anim.stop()
		await _draw()
		shots.append(await _shot("%s_rest_front" % which[0], Vector3(0, 1.05, 3.4), Vector3(0, 0.9, 0)))
		shots.append(await _shot("%s_rest_side" % which[0], Vector3(3.3, 1.05, 0.2), Vector3(0, 0.9, 0)))
		shots.append(await _shot("%s_rest_back" % which[0], Vector3(0, 1.15, -3.2), Vector3(0, 0.95, 0)))
		var poses := {
			"idle": [0.0, 1.2],
			"walk": [0.35, 0.9],
			"run": [0.25, 0.55],
			"attack2": [0.0, 0.45, 0.85],
			"hit": [0.0, 0.2],
			"death": [0.0, 0.8, 1.5],
		}
		var motion := {}
		for clip in poses:
			if not n.anim.has_animation(clip):
				continue
			var series := []
			for t in poses[clip]:
				_pose(n, clip, float(t))
				await _draw()
				var tag := "%s_%s_%03d" % [which[0], clip, int(float(t) * 100)]
				shots.append(await _shot(tag + "_front", Vector3(0.1, 1.05, 3.5), Vector3(0, 0.9, 0)))
				if clip in ["walk", "attack2", "death"] and which[0] == "mobile":
					shots.append(await _shot(tag + "_side", Vector3(3.4, 1.05, 0.15), Vector3(0, 0.9, 0)))
				series.append({"t": t, "hand": _bone(n, "hand_L"), "foot": _bone(n, "foot_L"), "hips": _bone(n, "hips")})
			# Loop ends.
			var length: float = n.anim.get_animation(clip).length
			_pose(n, clip, 0.0)
			var a := _bone(n, "hand_L")
			_pose(n, clip, maxf(length - 0.001, 0.0))
			var b := _bone(n, "hand_L")
			motion[clip] = {"samples": series, "hand_loop_gap_m": a.distance_to(b), "length": length}
		report[which[0] + "_motion"] = motion
		# Arms-out, no blend, first frame of the one-shots. Kept on purpose.
		for clip in ["attack2", "hit", "death"]:
			_pose(n, clip, 0.0)
			await _draw()
			shots.append(await _shot("%s_%s_arms_out" % [which[0], clip], Vector3(0.1, 1.05, 3.5), Vector3(0, 0.9, 0)))
		n.visible = false
	# Two walk times, pixel change.
	var n2 = _spawn(MOBILE)
	_pose(n2, "walk", 0.05)
	await _draw()
	var img_a := await _shot("pixel_a", Vector3(0.1, 1.05, 3.5), Vector3(0, 0.9, 0))
	_pose(n2, "walk", 0.55)
	await _draw()
	var img_b := await _shot("pixel_b", Vector3(0.1, 1.05, 3.5), Vector3(0, 0.9, 0))
	report["walk_frames_differ_px"] = _diff(img_a, img_b)
	n2.visible = false
	report["stills"] = shots.size()

func _transitions() -> void:
	var n = _spawn(MOBILE)
	n.anim.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var rows := []
	for pair in [["idle", "walk"], ["walk", "run"], ["walk", "attack2"], ["walk", "hit"], ["walk", "death"]]:
		_pose(n, pair[0], 0.4)
		n.anim.play(pair[1], 0.30, 1.0)
		for step in [0.05, 0.15, 0.30]:
			n.anim.advance(step if step == 0.05 else (0.10 if step == 0.15 else 0.15))
			await _draw()
			var name := "xfade_%s_to_%s_%02d" % [pair[0], pair[1], int(step * 100)]
			await _shot(name, Vector3(0.15, 1.05, 3.6), Vector3(0, 0.9, 0))
			rows.append({"name": name, "hand": _bone(n, "hand_L"), "from": pair[0], "to": pair[1], "t": step})
	report["transitions"] = rows
	n.visible = false

func _crowd() -> void:
	var holders: Array[Node] = []
	var clips := ["idle", "walk", "run", "attack2", "hit", "death"]
	for i in 16:
		var n = _spawn(MOBILE)
		var col := i % 4
		var row := i / 4
		n.position = Vector3(col * 1.7 - 2.55, 0, row * 1.7)
		var clip: String = clips[i % clips.size()]
		_pose(n, clip, float(i) * 0.07)
		holders.append(n)
	var far_root := _spawn(FAR)
	var far_mesh := _first_mesh(far_root)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = far_mesh.mesh
	mm.instance_count = 72
	for i in 72:
		var c := i % 12
		var r := i / 12
		var xf := Transform3D(Basis.IDENTITY, Vector3(c * 1.15 - 6.3, 0, -6.0 - r * 1.15))
		mm.set_instance_transform(i, xf)
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	world.add_child(mmi)
	far_root.visible = false
	await _draw()
	var crowd_draws: Array = []
	for _i in 3:
		var t_draw := Time.get_ticks_usec()
		RenderingServer.force_draw(true, 0.0)
		crowd_draws.append((Time.get_ticks_usec() - t_draw) / 1000.0)
	report["crowd_force_draw_ms"] = crowd_draws
	var wide_a := await _shot("crowd16_far72_a", Vector3(0, 6.5, 14.5), Vector3(0, 0.6, -1.5))
	for n in holders:
		if n.anim:
			n.anim.advance(0.35)
	await _draw()
	var wide_b := await _shot("crowd16_far72_b", Vector3(0, 6.5, 14.5), Vector3(0, 0.6, -1.5))
	report["crowd_frames_differ_px"] = _diff(wide_a, wide_b)
	report["crowd"] = {"skinned": 16, "far_multimesh": 72, "mobile_tris_each": _tris(holders[0]), "far_tris": _tris(far_root)}
	for n in holders:
		n.visible = false
	mmi.visible = false

func _lod() -> void:
	var near := _spawn(MOBILE)
	_pose(near, "idle", 0.0)
	var far := _spawn(FAR)
	far.position = Vector3(2.2, 0, 0)
	var card := _spawn(CARD)
	card.position = Vector3(-2.2, 0, 0)
	await _draw()
	await _shot("lod_near_mobile_far_card", Vector3(0, 1.2, 5.5), Vector3(0, 0.9, 0))
	# Pull back until the body is small. Same camera for a switch comparison.
	await _shot("lod_mid", Vector3(0, 2.2, 12.0), Vector3(0, 0.8, 0))
	near.visible = false
	await _draw()
	await _shot("lod_swapped_far_only", Vector3(0, 2.2, 12.0), Vector3(0, 0.8, 0))
	# Close on the far mesh and the card so the defects are visible.
	far.position = Vector3.ZERO
	card.visible = false
	await _draw()
	await _shot("far_close_front", Vector3(0, 1.05, 3.4), Vector3(0, 0.9, 0))
	card.visible = true
	card.position = Vector3.ZERO
	far.visible = false
	await _draw()
	await _shot("impostor_close", Vector3(0, 1.05, 3.4), Vector3(0, 0.9, 0))
	# Foot height: lowest vertex of mobile rest vs far.
	far.visible = true
	near.visible = true
	near.position = Vector3.ZERO
	far.position = Vector3.ZERO
	_pose(near, "idle", 0.0)
	report["lod"] = {
		"mobile_lowest_y": _lowest(near),
		"far_lowest_y": _lowest(far),
		"card_aabb": _aabb(card),
		"note": "Supplied far and impostor were baked before the foot lock. A few centimetres of foot difference is expected.",
	}
	near.visible = false
	far.visible = false
	card.visible = false

func _adapter() -> void:
	var z := HordeZombie.new()
	z.setup_horde("shambler", Vector3(0, 0, 0), func(_x, _z): return 0.0)
	z.set_physics_process(false)
	z.set_process(false)
	# The placeholder capsule stays in the tree but off camera.
	world.add_child(z)
	var p = Presenter.new()
	z.add_child(p)
	await process_frame
	var seen := {}
	seen["after_ready"] = p.clip
	z.global_position = Vector3(0, 0, -0.2)
	p._process(0.05)
	seen["after_step"] = p.clip
	z.state = "windup"
	z.pending_kind = "bite"
	p._process(0.05)
	seen["windup"] = p.clip
	z.state = "recover"
	p._process(0.05)
	seen["recover"] = p.clip
	z.state = "approach"
	z.hp = z.hp - 20.0
	p._process(0.05)
	seen["hp_drop"] = p.clip
	z.state = "defeated"
	z.hp = 0.0
	p._process(0.05)
	seen["defeated"] = p.clip
	# Runner speed scale, off to the side so it is not in the stills.
	var r := HordeZombie.new()
	r.setup_horde("runner", Vector3(40, 0, 40), func(_x, _z): return 0.0)
	r.set_physics_process(false)
	world.add_child(r)
	var pr = Presenter.new()
	r.add_child(pr)
	await process_frame
	r.global_position = Vector3(40, 0, 39.5)
	pr._process(0.05)
	seen["runner_clip"] = pr.clip
	seen["runner_speed_scale"] = pr.anim.speed_scale if pr.anim else -1
	seen["shambler_walk_scale_expected"] = 1.25 / 0.91
	report["adapter"] = seen
	z.visible = false
	r.visible = false

func _clock() -> void:
	# process_frame deltas are the frame slot. Record them and say so.
	var slots: Array[float] = []
	for i in 8:
		var t := Time.get_ticks_usec()
		await process_frame
		slots.append((Time.get_ticks_usec() - t) / 1000.0)
	var draws: Array[float] = []
	for i in 5:
		var t2 := Time.get_ticks_usec()
		RenderingServer.force_draw(true, 0.0)
		draws.append((Time.get_ticks_usec() - t2) / 1000.0)
	report["clock"] = {
		"process_frame_ms": slots,
		"force_draw_ms": draws,
		"process_frame_is_frame_slot_not_gpu": true,
		"display": DisplayServer.get_name(),
	}

func _jsonify(v):
	if v is Vector3:
		return [v.x, v.y, v.z]
	if v is AABB:
		return {"pos": _jsonify(v.position), "size": _jsonify(v.size)}
	if v is PackedStringArray or v is PackedStringArray:
		var ps: Array = []
		for s in v:
			ps.append(s)
		return ps
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

func _pose(n, clip: String, t: float) -> void:
	n.anim.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	n.anim.play(clip, -1, 1.0)
	n.anim.seek(t, true)
	n.anim.advance(0.0)
	if n.skel:
		n.skel.force_update_all_bone_transforms()

func _bone(n, nm: String) -> Vector3:
	if n.skel == null:
		return Vector3.ZERO
	var i: int = n.skel.find_bone(nm)
	if i < 0:
		return Vector3.INF
	return n.skel.get_bone_global_pose(i).origin

func _draw() -> void:
	await process_frame

func _shot(name: String, from: Vector3, at: Vector3) -> Image:
	_hide_menu()
	cam.current = true
	cam.global_position = from
	cam.look_at(at, Vector3.UP)
	await process_frame
	await process_frame
	var img := root.get_texture().get_image()
	img.save_png(OUT + "/" + name + ".png")
	return img

func _diff(a: Image, b: Image) -> int:
	if a == null or b == null:
		return -1
	var n := 0
	var w := mini(a.get_width(), b.get_width())
	var h := mini(a.get_height(), b.get_height())
	for y in range(0, h, 2):
		for x in range(0, w, 2):
			var ca := a.get_pixel(x, y)
			var cb := b.get_pixel(x, y)
			if absf(ca.r - cb.r) + absf(ca.g - cb.g) + absf(ca.b - cb.b) > 0.08:
				n += 1
	return n

func _tris(n: Node) -> int:
	var count := 0
	if n is MeshInstance3D and n.mesh:
		for s in n.mesh.get_surface_count():
			var prim: int = n.mesh.surface_get_primitive_type(s)
			var arrays: Array = n.mesh.surface_get_arrays(s)
			var idx: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
			if idx.is_empty():
				continue
			if prim == Mesh.PRIMITIVE_TRIANGLES:
				count += idx.size() / 3
	for c in n.get_children():
		count += _tris(c)
	return count

func _aabb(n: Node) -> AABB:
	var box := AABB()
	var first := true
	if n is MeshInstance3D and n.mesh and n.visible:
		var b: AABB = n.global_transform * n.mesh.get_aabb()
		box = b
		first = false
	for c in n.get_children():
		if c is Node3D and not (c as Node3D).visible:
			continue
		var cb := _aabb(c)
		if cb.size == Vector3.ZERO:
			continue
		if first:
			box = cb
			first = false
		else:
			box = box.merge(cb)
	return box

func _lowest(n: Node) -> float:
	var y := 99.0
	if n is MeshInstance3D and n.mesh:
		var arrays: Array = n.mesh.surface_get_arrays(0)
		var vs: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var xf: Transform3D = n.global_transform
		for v in vs:
			y = minf(y, (xf * v).y)
	for c in n.get_children():
		y = minf(y, _lowest(c))
	return y

func _first_mesh(n: Node) -> MeshInstance3D:
	if n is MeshInstance3D and n.mesh:
		return n
	for c in n.get_children():
		var m := _first_mesh(c)
		if m:
			return m
	return null

func _mats(n: Node) -> Array:
	var out: Array = []
	if n is MeshInstance3D and n.mesh:
		for i in n.mesh.get_surface_count():
			var m: Material = n.get_active_material(i)
			if m == null:
				m = n.mesh.surface_get_material(i)
			var row := {"class": m.get_class() if m else "none"}
			if m is StandardMaterial3D:
				var sm := m as StandardMaterial3D
				row["metallic"] = sm.metallic
				row["roughness"] = sm.roughness
				row["cull"] = sm.cull_mode
				row["albedo"] = sm.albedo_texture.resource_path if sm.albedo_texture else ""
				row["normal"] = sm.normal_texture != null
				row["transparency"] = sm.transparency
			out.append(row)
	for c in n.get_children():
		out.append_array(_mats(c))
	return out
