extends SceneTree
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var a := OS.get_cmdline_user_args()
	var z = load("res://tp/ice_cave_zone.gd").new(); await z.build(get_root())
	print("CAVE dressed=%d dropped=%d" % [z.dressed, z.dropped])
	if a.size() > 0 and a[0] == "shot":
		var cam := Camera3D.new(); cam.fov = 70; get_root().add_child(cam); cam.current = true
		var views := [[Vector3(-10, 2.2, -50), Vector3(-16, 3, 0)], [Vector3(-14, 6, 70), Vector3(-14, 4, 150)], [Vector3(-30, 9, 182), Vector3(0, 2, 120)]]
		for i in views.size():
			cam.look_at_from_position(z.to_global(views[i][0]), z.to_global(views[i][1]), Vector3.UP)
			for k in 8: await process_frame
			get_root().get_texture().get_image().save_jpg("/tmp/rp/s7/cave3_%d.jpg" % i, 0.88)
		quit(); return
	var route := [z.info.spawn, [-14, 0.5, 0], [-20, 0.5, 40], [-16, 0.5, 90], z.info.arena_center, z.info.troll_spawns.frosttroll_a, z.info.troll_spawns.frosttroll_b]
	for dir in [1]:
		var r: Array = route.duplicate(); if dir < 0: r.reverse()
		var b := CharacterBody3D.new(); var cs := CollisionShape3D.new(); var cap := CapsuleShape3D.new(); cap.radius = 0.35; cap.height = 1.8; cs.shape = cap; cs.position.y = 0.9; b.add_child(cs)
		b.floor_max_angle = deg_to_rad(40); b.floor_snap_length = 0.5; get_root().add_child(b)
		b.global_position = z.to_global(Vector3(r[0][0], z.floor_y(r[0][0], r[0][2]) + 0.5, r[0][2]))
		for i in 3: await physics_frame
		var wi := 1; var t := 0.0
		while t < 120.0 and wi < r.size():
			var tg: Vector3 = z.to_global(Vector3(r[wi][0], 0, r[wi][2])); var dv := tg - b.global_position; dv.y = 0
			if dv.length() < 1.0: wi += 1; continue
			var v := dv.normalized() * 5.0; b.velocity.x = v.x; b.velocity.z = v.z
			b.velocity.y = 0.0 if b.is_on_floor() else b.velocity.y - 9.8 / 60.0
			b.move_and_slide(); await physics_frame; t += 1.0 / 60.0
			if int(t * 60) % 120 == 0: print("  t=%.0f wi=%d p=%s" % [t, wi, z.to_local(b.global_position)])
		print("WALK cave %s ok=%s t=%.1f end_local=%s" % ["in" if dir > 0 else "out", wi >= r.size(), t, z.to_local(b.global_position)])
		b.queue_free()
	quit()
