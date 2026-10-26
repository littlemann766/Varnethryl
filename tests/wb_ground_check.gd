extends Node
## test 17 (boss: world boss floats + moon-walks; wants fading footprints). Run: godot --path . -- --wbcheck
## Walks the world boss along his patrol and measures: lowest-sole gap to terrain, facing vs velocity angle,
## planted-foot slide; footprints appear at plants and are removed after hold+fade. Shots to /workspace/shots/godot17/.
var m: Node
const OUT := "/workspace/shots/godot17/"
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	await frames(10)
	m.time_mode = 1; m._set_time(12.0)
	m.spawn_world_boss(false); await frames(5)
	var wb = m.world_boss
	wb.place_at(5); await frames(30)
	print("WB walk_rate=%.3f sole_clear=%.2f body_yaw=%.2f" % [wb.walk_rate, wb.sole_clear, wb.body.rotation.y])
	var fails := 0; var max_gap := 0.0; var max_ang := 0.0; var n := 0; var slide := 0.0; var slide_n := 0
	var last: Vector3 = wb.global_position
	var lastfoot := {}
	var p0: int = wb.prints_made
	for i in 900:   # ~ 900 frames of patrol walking
		await get_tree().process_frame
		if wb.state != "walk": wb._set_state("walk")
		var p: Vector3 = wb.global_position; var v := Vector3(p.x - last.x, 0, p.z - last.z); last = p
		if i < 30 or v.length() < 0.001: continue
		var f: Vector3 = wb._fwd()
		var face: Vector3 = (wb.body.global_basis * Vector3.BACK)   # glTF front (+Z) of the turned body, in world
		face.y = 0
		var ang := rad_to_deg(face.normalized().angle_to(v.normalized()))
		max_ang = maxf(max_ang, ang); max_gap = maxf(max_gap, absf(wb.foot_gap)); n += 1
		# planted-foot slide: lowest toe's world xz motion per second while it is within 0.5 m of the ground
		for bn in ["toe_L", "toe_R"]:
			var b: int = wb.skel.find_bone(bn)
			var tp: Vector3 = wb.skel.global_transform * wb.skel.get_bone_global_pose(b).origin
			var g: float = tp.y - wb.sole_clear - wb._gy(tp.x, tp.z)
			if lastfoot.has(bn) and g < 0.5:
				var dt := get_process_delta_time() * Engine.time_scale
				if dt > 0.0: slide += Vector2(tp.x - lastfoot[bn].x, tp.z - lastfoot[bn].z).length() / dt; slide_n += 1
			lastfoot[bn] = tp
		if i == 400:
			var hp: Vector3 = wb.global_position; var side: Vector3 = f.cross(Vector3.UP).normalized()
			var c := Camera3D.new(); c.fov = 50; c.far = 3000; m.add_child(c)
			c.look_at_from_position(hp + side * 170.0 + Vector3(0, 30, 0), hp + Vector3(0, 45, 0), Vector3.UP); c.current = true
			await frames(2); get_viewport().get_texture().get_image().save_png(OUT + "wb_walk_side.png")
			c.look_at_from_position(hp + f * 190.0 + Vector3(0, 35, 0), hp + Vector3(0, 45, 0), Vector3.UP)
			await frames(2); get_viewport().get_texture().get_image().save_png(OUT + "wb_walk_front.png")
			c.look_at_from_position(hp + side * 40.0 + Vector3(0, 6, 0), hp + Vector3(0, 2, 0) + side * 0.0, Vector3.UP)
			await frames(2); get_viewport().get_texture().get_image().save_png(OUT + "wb_feet_ground_close.png")
			m.cam.current = true; c.queue_free()
	var avg_slide := slide / maxf(slide_n, 1)
	print("WBCHECK samples=%d max_foot_gap=%.2f m max_facing_vs_velocity=%.1f deg planted_slide=%.2f m/s prints=%d" % [n, max_gap, max_ang, avg_slide, wb.prints_made - p0])
	if max_gap > 0.6: fails += 1; print("FAIL foot gap")
	if max_ang > 20.0: fails += 1; print("FAIL facing")
	if avg_slide > 1.0: fails += 1; print("FAIL foot slide")
	if wb.prints_made - p0 < 4: fails += 1; print("FAIL no footprints at plants")
	# fresh prints shot (behind him, from above)
	var hp2: Vector3 = wb.global_position; var bk: Vector3 = -wb._fwd()
	var c2 := Camera3D.new(); c2.fov = 55; c2.far = 3000; m.add_child(c2)
	c2.look_at_from_position(hp2 + bk * 110.0 + Vector3(0, 70, 0) + bk.cross(Vector3.UP) * 30.0, hp2 + bk * 40.0, Vector3.UP); c2.current = true
	wb.visible = true; var save_state = wb.state; wb.set_process(false)
	await frames(3); get_viewport().get_texture().get_image().save_png(OUT + "wb_prints_fresh.png")
	# age every print into the fade window, shot, then past the end: all must be removed
	for fp in wb.footprints: fp[2] = wb.PRINT_HOLD + wb.PRINT_FADE * 0.6
	wb._update_prints(0.0); await frames(3); get_viewport().get_texture().get_image().save_png(OUT + "wb_prints_fading.png")
	var before: int = wb.footprints.size()
	wb._update_prints(wb.PRINT_FADE); await frames(2)
	var left := 0
	for c in wb.get_children(): pass
	left = wb.footprints.size()
	print("PRINTS before_fade_end=%d after=%d cap=%d" % [before, left, wb.PRINT_CAP])
	if before == 0 or left != 0: fails += 1; print("FAIL prints not removed after fade")
	if before > wb.PRINT_CAP: fails += 1; print("FAIL print cap")
	print("WBGROUND %d failed" % fails)
	get_tree().quit()
