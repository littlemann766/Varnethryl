extends SceneTree
## CPU upload and software-GL draw of placeholder capsules.
## Desktop only. Not a phone and not a GPU result.
## godot --headless --path . -s res://tests/horde_render_bench.gd
## and, for pixels: LIBGL_ALWAYS_SOFTWARE=1 godot --rendering-method gl_compatibility --rendering-driver opengl3 --display-driver x11 --path . -s res://tests/horde_render_bench.gd
func _initialize() -> void: _run.call_deferred()

func _run() -> void:
	var counts := [256, 1024, 2048, 4096]
	print("RENDER_BENCH headless_upload godot=%s" % Engine.get_version_info().string)
	for n in counts:
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		var cap := CapsuleMesh.new()
		cap.radius = 0.28
		cap.height = 1.35
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color(0.4, 0.55, 0.32)
		cap.material = mat
		mm.mesh = cap
		mm.instance_count = n
		var t0 := Time.get_ticks_usec()
		for rep in 30:
			for i in n:
				var x := float(i % 40) * 1.7 - 34.0
				var z := 204.0 + float(i / 40) * 1.85
				var scale := 1.0 if i < n / 2 else 0.62
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3(scale, scale, scale)), Vector3(x, 0.7, z)))
			mm.visible_instance_count = n
		var ms := float(Time.get_ticks_usec() - t0) / 1000.0 / 30.0
		print("RENDER_UPLOAD n=%d ms_per_update=%.3f" % [n, ms])
	if DisplayServer.get_name() == "headless":
		print("RENDER_DRAW skipped_headless")
		print("RENDER_BENCH_DONE")
		quit(0)
		return
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.62, 0.74, 0.84)
	var we := WorldEnvironment.new()
	we.environment = env
	root.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.shadow_enabled = false
	root.add_child(sun)
	var cam := Camera3D.new()
	cam.current = true
	cam.position = Vector3(0, 8, 160)
	cam.look_at(Vector3(0, 1, 220), Vector3.UP)
	root.add_child(cam)
	for n in counts:
		var mi := MultiMeshInstance3D.new()
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		var cap := CapsuleMesh.new()
		cap.radius = 0.28
		cap.height = 1.35
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color(0.4, 0.55, 0.32)
		cap.material = mat
		mm.mesh = cap
		mm.instance_count = n
		mm.visible_instance_count = n
		for i in n:
			var x := float(i % 40) * 1.7 - 34.0
			var z := 204.0 + float(i / 40) * 1.85
			mm.set_instance_transform(i, Transform3D(Basis(), Vector3(x, 0.7, z)))
		mi.multimesh = mm
		root.add_child(mi)
		for _i in 5: await process_frame
		var t0 := Time.get_ticks_usec()
		var frames := 20
		for _i in frames: await process_frame
		var ms := float(Time.get_ticks_usec() - t0) / 1000.0 / float(frames)
		print("RENDER_DRAW n=%d ms_per_frame=%.2f driver=%s" % [n, ms, RenderingServer.get_current_rendering_method()])
		mi.queue_free()
		await process_frame
	print("RENDER_BENCH_DONE")
	quit(0)
