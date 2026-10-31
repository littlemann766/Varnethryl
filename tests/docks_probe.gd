extends Node
var m: Node
func frames(n): 
	for i in n: await get_tree().process_frame
func _ready(): m = get_parent(); _run.call_deferred()
func ray(x, z):
	var q := PhysicsRayQueryParameters3D.create(Vector3(x, 60, z), Vector3(x, -10, z)); var h = m.get_world_3d().direct_space_state.intersect_ray(q)
	return h.position.y if h else -99.0
func _run():
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0)
	var out := "/workspace/shots/voxel32/"
	var log := ""
	for x in [-560.0, -535.0, -510.0, -484.0, -460.0]:
		var row := "x=%d:" % x
		for z in [299.7, 300.0, 300.3, 309.7, 310.0, 310.3, 312.0, 316.0, 318.0, 319.7, 320.0, 320.3]: row += " z%d terr=%.2f col=%.2f |" % [z, m.height(x, z), ray(x, z)]
		log += row + "\n"
	FileAccess.open(out + "profile.txt", FileAccess.WRITE).store_string(log); print(log)
	m.party._set_companions([]); m.party.set_hero("owner")
	for spot in [Vector3(-510, 0, 318), Vector3(-484, 0, 316)]:
		var y = ray(spot.x, spot.z); m.hero.position = Vector3(spot.x, y + 0.1, spot.z)
		m.yaw = PI * 0.5; m.pitch = -0.12; m.cam_arm.spring_length = 6.0; m.hero_vis.rotation.y = m.yaw + PI
		await frames(40)
		get_viewport().get_texture().get_image().save_png(out + "owner_docks_%d.png" % int(spot.x)); print("DOCK ", spot, " y=", y, " hero=", m.hero.global_position)
	get_tree().quit(0)
