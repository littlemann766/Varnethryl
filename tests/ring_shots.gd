extends Node
var m: Node
func _ready(): m = get_parent(); _run.call_deferred()
func _run():
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0); var tag := OS.get_environment("VOX_TAG")
	var cam := Camera3D.new(); cam.fov = 60; cam.far = 3000; m.add_child(cam)
	for v in [["overhead", Vector3(0, 230, 230), Vector3(0, 0, 40)], ["wall_sw", Vector3(-120, 70, 260), Vector3(-150, 0, 160)]]:
		cam.look_at_from_position(v[1], v[2], Vector3.UP); cam.current = true
		for i in 40: await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png("/workspace/shots/voxel32/ring_%s_%s.png" % [v[0], tag]); print("RING ", v[0])
	get_tree().quit(0)
