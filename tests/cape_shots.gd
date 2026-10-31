extends Node
## test 33: Beth's cape_fix32 before/after. Owner, villain, Asha, guard front/side/back, walking. -- --capeshots (CAPE_TAG=before/after)
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	var out := "/workspace/shots/voxel33/capes/"; DirAccess.make_dir_recursive_absolute(out)
	var tag := OS.get_environment("CAPE_TAG")
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0)
	var base := Vector3(-6, 0, 30); base.y = m.height(base.x, base.z); m.hero.position = base + Vector3(0, 0, 40)
	var ids := ["owner", "holyknight_villain", "asha", "town_guard", "morwen", "wren"]
	var cam := Camera3D.new(); cam.fov = 40; m.add_child(cam); cam.current = true
	for id in ids:
		var r := CharacterRig.new().setup("res://voxel/%s_voxel.glb" % id, 1.905); m.add_child(r); r.global_position = base
		r.set_locomotion(0.5); await frames(40)
		var p := base + Vector3(0, 1.0, 0)
		for v in [["back", Vector3(0, 0.3, 3.6)], ["side", Vector3(3.6, 0.3, 0)], ["front", Vector3(0, 0.3, -3.6)]]:
			cam.look_at_from_position(p + v[1], p, Vector3.UP); await frames(4)
			get_viewport().get_texture().get_image().save_png(out + "%s_%s_%s.png" % [id, v[0], tag])
		r.queue_free(); await frames(2)
	print("CAPE DONE"); get_tree().quit()
