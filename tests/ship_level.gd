extends Node
## test 28: every ship sits level. Measures, over 20 s of bobbing, each ship's world tilt (root + every LOD mesh node, i.e.
## node rotation AND the mesh instances' own transforms) and writes phone-aspect shots (side, bow, Owner flying near the
## sea galleon). -- --shiplevel   (2340x1080)
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func tilt_deg(b: Basis) -> Vector2:   # (pitch about local X, roll about local Z) of the up axis
	var u := b.orthonormalized().y
	var f := b.orthonormalized().z; var r := b.orthonormalized().x
	return Vector2(rad_to_deg(asin(clampf(f.y, -1, 1))), rad_to_deg(asin(clampf(r.y, -1, 1))))
func _run() -> void:
	var out := "/workspace/shots/voxel31/ship_level/"; DirAccess.make_dir_recursive_absolute(out)
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0); m.party._set_companions([]); m.party.set_hero("owner")
	var mx := {}
	for k in 1200:   # 20 s
		for s in m.ships:
			var r: Node3D = s[0]
			var worst := 0.0
			for mi in r.find_children("*", "MeshInstance3D", true, false):
				var t := tilt_deg((mi as Node3D).global_basis); worst = maxf(worst, maxf(absf(t.x), absf(t.y)))
			mx[r.name] = maxf(mx.get(r.name, 0.0), worst)
		await get_tree().physics_frame
	for n in mx: print("SHIPTILT %s max %.4f deg" % [n, mx[n]])
	var cam := Camera3D.new(); cam.fov = 60; m.add_child(cam)
	for nm in ["Ship0_tidewrack_sailing_ship", "Ship7_tidewrack_sailing_ship"]:
		var sh: Node3D = m.get_node_or_null(nm)
		if sh == null: continue
		var c := sh.global_position; c.y = 0.0
		var side: Vector3 = sh.global_basis.x.normalized(); var fwd: Vector3 = sh.global_basis.z.normalized()
		for v in [["side", side * 42.0 + Vector3(0, 3.0, 0)], ["bow", fwd * 45.0 + side * 6.0 + Vector3(0, 3.0, 0)]]:
			cam.look_at_from_position(c + v[1], c + Vector3(0, 4, 0), Vector3.UP); cam.current = true
			await frames(20); get_viewport().get_texture().get_image().save_png(out + "%s_%s.png" % [nm.substr(0, 5), v[0]]); print("SHOT ", nm, v[0])
	cam.current = false; m.get_viewport().get_camera_3d()
	# Owner flying near the sea galleon, like the boss's screenshot
	var s7: Node3D = m.get_node_or_null("Ship7_tidewrack_sailing_ship")
	if s7:
		if m.fly_controls: m.fly_controls.process_mode = Node.PROCESS_MODE_DISABLED
		cam.queue_free(); await frames(2)
		var p: Vector3 = s7.global_position + s7.global_basis.x.normalized() * 28.0 + s7.global_basis.z.normalized() * 8.0
		m.hero.position = Vector3(p.x, 6.0, p.z); m.fly_alt = 10.0
		var to := s7.global_position - p; m.yaw = atan2(-to.x, -to.z) - 0.45; m.pitch = -0.15; m.cam_arm.spring_length = 5.0
		for i in 60:
			m.cheat["fly"] = true; m.flight = true; await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(out + "owner_flying_near_ship.png"); print("SHOT flying")
	get_tree().quit(0)
