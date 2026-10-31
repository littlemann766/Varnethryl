extends Node
## test 34: minions chasing + attacking the hero near the world boss. -- --minionshots
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	var out := "/workspace/shots/t34/minions/"; DirAccess.make_dir_recursive_absolute(out)
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0); m.party._set_companions([]); m.party.set_hero("aldric")
	m.cheat["god"] = true
	m.spawn_world_boss(true); await frames(10)
	var wb = m.world_boss; var h: Node3D = m.hero
	var spot: Vector3 = wb.global_position + Vector3(70, 0, 0); h.global_position = Vector3(spot.x, m.height(spot.x, spot.z) + 0.2, spot.z)
	wb._spawn_adds(spot + Vector3(0, 0, 14)); await frames(4)
	var cam := Camera3D.new(); cam.fov = 50; m.add_child(cam); cam.current = true
	for i in 16:
		await frames(15)
		var c: Vector3 = h.global_position + Vector3(0, 1.2, 0)
		cam.look_at_from_position(c + Vector3(7, 3.5, 7), c + Vector3(0, 0, 3), Vector3.UP)
		get_viewport().get_texture().get_image().save_png(out + "minions_%02d.png" % i)
	print("MS DONE"); get_tree().quit(0)
