extends Node
## test 34: test 33 vs test 34 shots. Run + attack (front, side) for Owner, Garruk, Selene, villain, Titan; capes from the back.
## VOX_SRC=t33|t34. -- --vox34
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func path(f: String, t34: String) -> String:
	return ("res://t33ref/" + f) if OS.get_environment("VOX_SRC") == "t33" else t34
func _run() -> void:
	var out := OS.get_environment("SHOT_OUT") if OS.get_environment("SHOT_OUT") != "" else "/workspace/shots/t34/compare/"; DirAccess.make_dir_recursive_absolute(out); var tag := OS.get_environment("VOX_SRC")
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0); m.party._set_companions([])
	var base := Vector3(-6, 0, 30); base.y = m.height(base.x, base.z); m.hero.position = base + Vector3(0, 0, 40)
	var cam := Camera3D.new(); cam.fov = 40; m.add_child(cam); cam.current = true
	var L := [["owner", "owner_voxel.glb", "res://voxel/owner_voxel.glb", 1.905], ["garruk", "garruk_voxel.glb", "res://voxel/garruk_voxel.glb", 1.905],
		["selene", "selene_voxel.glb", "res://voxel/selene_voxel.glb", 1.905], ["villain", "holyknight_villain_voxel.glb", "res://voxel/holyknight_villain_voxel.glb", 1.905],
		["titan", "ashentitan_lod1.glb", "res://characters/ashentitan_lod1.glb", 6.0 * 1.905],
		["titan_wb", "ashentitan_lod1.glb", "res://assets/volcano/worldboss/titan/ashentitan_wb_voxel_lod1.glb", 6.0 * 1.905]]   # test 36: world-boss voxel Titan
	var only := OS.get_environment("VOX_ONLY").split(",", false)
	for e in L:
		if not only.is_empty() and not (e[0] in only): continue
		var r := CharacterRig.new().setup(path(e[1], e[2]), e[3]); m.add_child(r); r.global_position = base
		var s: float = e[3] / 1.905; var c := base + Vector3(0, 0.95 * s, 0)
		var rs = HeroRoster.ROOT_SPEED.get(e[0], [1.6, 4.5]); r.set_root_speeds(rs[0], rs[1], 6.0)
		r.set_move_mps(0.0); await frames(20); r.set_move_mps(rs[1]); await frames(47)
		for v in [["front", Vector3(0.4, 0.3, -4.2)], ["side", Vector3(4.2, 0.3, 0)]]:
			cam.look_at_from_position(c + v[1] * s, c, Vector3.UP); await frames(1)
			get_viewport().get_texture().get_image().save_png(out + "%s_run_%s_%s.png" % [e[0], v[0], tag])
		r.set_move_mps(0.0); await frames(20)
		for v in [["front", Vector3(0.4, 0.3, -4.2)], ["side", Vector3(4.2, 0.3, 0)]]:
			cam.look_at_from_position(c + v[1] * s, c, Vector3.UP); r.play_attack("", 1.0); await frames(14)
			get_viewport().get_texture().get_image().save_png(out + "%s_attack_%s_%s.png" % [e[0], v[0], tag])
			await frames(40)
		r.queue_free(); await frames(2)
	for id in ["owner", "aldric", "asha", "morwen", "wren", "holyknight_villain", "garruk", "rook"]:
		if not only.is_empty() and not (id in only): continue
		var r := CharacterRig.new().setup(path(id + "_voxel.glb", "res://voxel/%s_voxel.glb" % id), 1.905); m.add_child(r); r.global_position = base
		r.set_locomotion(0.5); await frames(40)
		cam.look_at_from_position(base + Vector3(0, 1.3, 3.6), base + Vector3(0, 1.0, 0), Vector3.UP); await frames(4)
		get_viewport().get_texture().get_image().save_png(out + "cape_%s_back_%s.png" % [id, tag]); r.queue_free(); await frames(2)
	print("V34 DONE"); get_tree().quit(0)
