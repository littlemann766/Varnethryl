extends Node
## test 19 (boss: kneel looked like a pretzel). Breaks his leg crystals from the ground, waits for the kneel to settle,
## shoots side + ground views at ~50 m, prints crystal heights/reach and the lowest point vs terrain.
var m: Node
const OUT := "/workspace/shots/godot19/"
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var tag := OS.get_environment("WB_TAG"); if tag == "": tag = "after"
	var hero := Node3D.new(); m.add_child(hero); m.hero = hero
	m.spawn_world_boss(false); await frames(5)
	var wb = m.world_boss
	wb.place_at(5); await frames(30)
	for c in wb.crystals:
		if c.name in wb.LEGS: c.hp = 1.0; wb._hit_crystal(c, 5.0)
	var t0 := Time.get_ticks_msec()
	while not (wb.state == "kneel" and wb.t_state > 5.0) and Time.get_ticks_msec() - t0 < 120000: await frames(1)
	print("KNEEL state=%s t=%.1f anim=%s banner=%s" % [wb.state, wb.t_state, wb.ap.current_animation, wb.get("last_warn")])
	var bp: Vector3 = wb.global_position; var f: Vector3 = wb._fwd(); var side: Vector3 = f.cross(Vector3.UP).normalized()
	var lo := INF
	for b in range(1, wb.skel.get_bone_count()):
		var q: Vector3 = wb.skel.global_transform * wb.skel.get_bone_global_pose(b).origin
		lo = minf(lo, q.y - wb._gy(q.x, q.z))
	print("KNEEL lowest_bone_above_ground=%.2f" % lo)
	for c in wb.crystals:
		var p: Vector3 = c.node.global_position
		print("KNEEL crystal %s h=%.1f" % [c.name, p.y - wb._gy(p.x, p.z)])
	var cam: Camera3D = m.cam; cam.fov = 85
	var c1: Vector3 = bp + side * 60.0 + f * 10.0; c1.y = m.height(c1.x, c1.z) + 8.0
	cam.look_at_from_position(c1, Vector3(bp.x, m.height(bp.x, bp.z) + 25.0, bp.z), Vector3.UP); await frames(4)
	get_viewport().get_texture().get_image().save_png(OUT + tag + "_kneel_side_55m.png")
	var c2: Vector3 = bp + f * 45.0 + side * 15.0; c2.y = m.height(c2.x, c2.z) + 1.7
	cam.look_at_from_position(c2, Vector3(bp.x, m.height(bp.x, bp.z) + 28.0, bp.z), Vector3.UP); await frames(4)
	get_viewport().get_texture().get_image().save_png(OUT + tag + "_kneel_ground_45m.png")
	var c3: Vector3 = bp + side * 170.0 + f * 40.0; c3.y = m.height(c3.x, c3.z) + 20.0
	cam.fov = 60; cam.look_at_from_position(c3, Vector3(bp.x, m.height(bp.x, bp.z) + 40.0, bp.z), Vector3.UP); await frames(4)
	get_viewport().get_texture().get_image().save_png(OUT + tag + "_kneel_wide_170m.png")
	var c4: Vector3 = bp + f * 170.0 + side * 30.0; c4.y = m.height(c4.x, c4.z) + 20.0
	cam.look_at_from_position(c4, Vector3(bp.x, m.height(bp.x, bp.z) + 40.0, bp.z), Vector3.UP); await frames(4)
	get_viewport().get_texture().get_image().save_png(OUT + tag + "_kneel_front_170m.png")
	get_tree().quit()
