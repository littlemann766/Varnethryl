extends Node
## voxel-heroes test 25: palette close-ups (Owner, Selene, Darius, guard) near + mid distance. -- --voxclose (VOX_TAG=before/after)
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	var out := "/workspace/shots/voxel25/"; DirAccess.make_dir_recursive_absolute(out)
	var tag := OS.get_environment("VOX_TAG")
	var t := 0
	while not m.warmed and t < 6000: await get_tree().process_frame; t += 1
	m._set_time(11.0)
	var base := Vector3(-6, 0, 30); base.y = m.height(base.x, base.z)
	m.hero.position = base + Vector3(0, 0, 40)
	var root := Node3D.new(); m.add_child(root); root.global_position = base
	var paths := [HeroRoster.VOXEL.owner, HeroRoster.VOXEL.selene, HeroRoster.VOXEL.darius, TownGuards.MODEL]
	var names := ["owner", "selene", "darius", "guard"]
	var cam := Camera3D.new(); cam.fov = 40; m.add_child(cam); cam.current = true
	for i in 4:
		var r := CharacterRig.new().setup(paths[i], 1.905); root.add_child(r); r.position = Vector3(i * 1.6, 0, 0)
	await frames(10)
	for i in 4:
		for d in [["near", 2.6], ["mid", 9.0]]:
			var p: Vector3 = root.global_position + Vector3(i * 1.6, 1.1, 0)
			cam.look_at_from_position(p + Vector3(0.0, 0.25, -d[1]), p, Vector3.UP); cam.current = true
			await frames(8)
			get_viewport().get_texture().get_image().save_png(out + "%s_%s_%s.png" % [names[i], d[0], tag]); print("CLOSE ", names[i], d[0], tag)
	get_tree().quit(0)
