extends Node
## test 26: Owner close-up (front/back, slippers), at the sea (swim/tread) and flying. -- --ownershots (VOX_TAG=before/after)
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func shot(n: String) -> void:
	await frames(3)
	var r = m.party.rig
	get_viewport().get_texture().get_image().save_png("/workspace/shots/voxel27/owner_%s_%s.png" % [n, OS.get_environment("VOX_TAG")])
	print("OSHOT %s fly_on=%s swim=%s y=%.2f rig_y=%.2f" % [n, r.fly_on, r.get("swim_on"), m.hero.position.y, r.position.y])
func place(p: Vector3, yaw: float, pitch: float, arm: float) -> void:
	m.hero.position = Vector3(p.x, m.height(p.x, p.z) + 0.1, p.z); m.yaw = yaw; m.pitch = pitch; m.cam_arm.spring_length = arm
	m.hero_vis.rotation.y = yaw + PI
func _run() -> void:
	DirAccess.make_dir_recursive_absolute("/workspace/shots/voxel27")
	var t := 0
	while not m.warmed and t < 6000: await get_tree().process_frame; t += 1
	m._set_time(11.0); m.party._set_companions([]); m.party.set_hero("owner")
	place(Vector3(-6, 0, 30), PI, -0.1, 2.4); await frames(30); await shot("front")
	place(Vector3(-6, 0, 30), 0.0, -0.25, 2.4); await frames(20); await shot("back")
	place(Vector3(-470, 0, 380), 0.0, -0.2, 4.0); await frames(40); await shot("sea_idle")
	for i in 40: m.joy_vec = Vector2(0, -1); await get_tree().process_frame
	await shot("sea_swim"); m.joy_vec = Vector2.ZERO
	if m.fly_controls: m.fly_controls.process_mode = Node.PROCESS_MODE_DISABLED
	place(Vector3(-470, 0, 380), 0.0, -0.2, 4.0); m.fly_alt = 6.0
	for i in 60:
		m.cheat["fly"] = true; m.flight = true; m.joy_vec = Vector2(0, -1); await get_tree().process_frame
	await shot("flying"); m.joy_vec = Vector2.ZERO
	for i in 40:
		m.cheat["fly"] = true; m.flight = true; await get_tree().process_frame
	await shot("hover")
	m.set_flight(false); m.cheat["fly"] = false
	# test 27: harbour, phone aspect (2340x1080 ~ 2.17:1): galleon at the pier + the Owner's HUD
	m.joy_vec = Vector2.ZERO
	for hv in [[Vector3(-434, 0, 371), PI / 2], [Vector3(-440, 0, 392), PI / 2 + 0.5]]:
		place(hv[0], hv[1], -0.05, 5.0); await frames(60)
		await shot("harbour_hud_%d" % (1 if hv[0].z < 380 else 2))
	# ships: same camera for before/after, from the quay looking at the pier galleon (Ship0) and the district one (Ship6)
	for nm in ["Ship0_tidewrack_sailing_ship", "Ship6_tidewrack_sailing_ship"]:
		var sh: Node3D = m.get_node_or_null(nm)
		if sh == null: continue
		var cam := Camera3D.new(); cam.fov = 55; m.add_child(cam)
		var c := Vector3(sh.global_position.x, 0, sh.global_position.z)
		for v in [["side", Vector3(40, 5, 0)], ["quarter", Vector3(28, 7, 26)]]:
			cam.look_at_from_position(c + sh.global_basis * v[1], c + Vector3(0, 3, 0), Vector3.UP); cam.current = true
			await frames(20)
			get_viewport().get_texture().get_image().save_png("/workspace/shots/voxel27/%s_%s_%s.png" % [nm.substr(0, 5), v[0], OS.get_environment("VOX_TAG")]); print("SSHOT ", nm, v[0])
		cam.queue_free()
	get_tree().quit(0)
