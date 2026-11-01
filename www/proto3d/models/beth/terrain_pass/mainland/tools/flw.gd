extends SceneTree
## close-up: terrain + baked wildflowers. args: main_script bake.bin out.jpg
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var a := OS.get_cmdline_user_args(); get_root().size = Vector2i(1280, 720)
	var M: Node3D = load(a[0]).new(); M.noise.seed = 7; M.noise.frequency = 0.0035; M.noise.fractal_octaves = 4
	M._terrain(); var top := Node3D.new(); get_root().add_child(top)
	for c in M.get_children(): M.remove_child(c); top.add_child(c)
	var f := FileAccess.open(a[1], FileAccess.READ); var data: Dictionary = f.get_var(); f.close()
	TerrainFlowers._make_nodes(top, data.chunks, data.stats)
	var we := WorldEnvironment.new(); var env := Environment.new(); var sky := Sky.new(); sky.sky_material = ProceduralSkyMaterial.new(); env.background_mode = Environment.BG_SKY; env.sky = sky; env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.tonemap_mode = Environment.TONE_MAPPER_ACES; we.environment = env; top.add_child(we)
	var sun := DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-40, 40, 0); top.add_child(sun)
	var cam := Camera3D.new(); top.add_child(cam); cam.current = true; cam.fov = 50
	var shots := [[Vector3(-311, 0, -230), Vector3(-300, 0, -238)], [Vector3(-380, 0, -45), Vector3(-370, 0, -38)]]
	var k := 0
	for s in shots:
		var f0: Vector3 = s[0]; f0.y = M.height(f0.x, f0.z) + 1.3; var t: Vector3 = s[1]; t.y = M.height(t.x, t.z)
		cam.look_at_from_position(f0, t, Vector3.UP)
		for i in 6: await process_frame
		get_root().get_texture().get_image().save_jpg(a[2].replace(".jpg", "_%d.jpg" % k), 0.88); k += 1
	quit()
