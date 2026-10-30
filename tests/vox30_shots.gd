extends Node
## test 30: Owner slippers, Nyx boots (idle + walk), Asha cape (back). -- --vox30 (VOX_TAG=before/after)
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	var out := "/workspace/shots/voxel30/"; DirAccess.make_dir_recursive_absolute(out); var tag := OS.get_environment("VOX_TAG")
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0)
	var base := Vector3(-6, 0, 30); base.y = m.height(base.x, base.z); m.hero.position = base + Vector3(0, 0, 40)
	var cam := Camera3D.new(); cam.fov = 35; m.add_child(cam)
	# [id, name, look-at height, cam offset (front = -z), walk?]
	var jobs := [["owner", "owner_slippers", 0.15, Vector3(0.6, 0.5, -1.6), false],
		["nyx", "nyx_boots_idle", 0.3, Vector3(0.5, 0.5, -1.8), false], ["nyx", "nyx_boots_walk", 0.3, Vector3(0.5, 0.5, -1.8), true],
		["asha", "asha_cape_back", 1.0, Vector3(0.8, 0.6, 3.2), false], ["asha", "asha_cape_walk", 1.0, Vector3(1.6, 0.6, 2.8), true]]
	for j in jobs:
		var r := CharacterRig.new().setup(HeroRoster.model(j[0]), HeroRoster.height(j[0])); m.add_child(r); r.global_position = base
		if HeroRoster.ROOT_SPEED.has(j[0]): r.set_root_speeds(HeroRoster.ROOT_SPEED[j[0]][0], HeroRoster.ROOT_SPEED[j[0]][1], 6.0)
		await frames(10)
		if j[4]: r.set_move_mps(HeroRoster.ROOT_SPEED.get(j[0], [1.0])[0])
		await frames(40)
		var t: Vector3 = base + Vector3(0, j[2], 0)
		cam.look_at_from_position(base + j[3], t, Vector3.UP); cam.current = true
		await frames(4); get_viewport().get_texture().get_image().save_png(out + "%s_%s.png" % [j[1], tag]); print("V30 ", j[1])
		r.queue_free(); await frames(2)
	get_tree().quit(0)
