extends Node
## test 22 (boss: Titan "walks funny, like he's slow" + "his knees are bent too much"). Run in the lean host:
##   WB_SCRIPT=res://tests/wb_walk_check.gd godot --path . --fixed-fps 30 res://tests/wb_lite.tscn   [WB_VIDEO=dir WB_FRAMES=n]
## Measures: knee bend (deg) while the foot is planted vs in swing, planted-foot slip per metre walked, steps/s,
## travel speed, sole gap. WB_VIDEO: side-view frames (follow cam) for the before/after video.
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func bend(wb, a: String, b: String, c: String) -> float:
	var s: Skeleton3D = wb.skel
	var pa := s.get_bone_global_pose(s.find_bone(a)).origin; var pb := s.get_bone_global_pose(s.find_bone(b)).origin; var pc := s.get_bone_global_pose(s.find_bone(c)).origin
	return rad_to_deg((pb - pa).angle_to(pc - pb))
func _run() -> void:
	await frames(10)
	m.spawn_world_boss(false); await frames(5)
	var wb = m.world_boss
	wb.place_at(5); await frames(30)
	var vid := OS.get_environment("WB_VIDEO")
	if vid != "": DirAccess.make_dir_recursive_absolute(vid)
	var NF := int(OS.get_environment("WB_FRAMES")) if OS.get_environment("WB_FRAMES") != "" else 600
	var st_b := []; var sw_b := []; var slide := 0.0; var walked := 0.0; var gapmax := 0.0
	var lastfoot := {}; var lastloc := {}; var footmin := {}; var last: Vector3 = wb.global_position
	var p0: int = wb.prints_made; var t := 0.0
	var c := Camera3D.new(); c.fov = 50; c.far = 3000; m.add_child(c)
	for i in NF:
		await get_tree().process_frame
		if wb.state != "walk": wb._set_state("walk")
		var dt := get_process_delta_time(); t += dt
		var p: Vector3 = wb.global_position; var v := Vector3(p.x - last.x, 0, p.z - last.z); last = p
		var f: Vector3 = wb._fwd(); var inv: Transform3D = wb.global_transform.affine_inverse()
		if OS.get_environment("WB_DBG") != "" and i % 15 == 0 or (OS.get_environment("WB_DBG") != "" and i > 425 and i < 450): var sk = wb.skel; print("DBGP hips=%s root=%s shinL=%s footL=%s toeL=%s" % [sk.get_bone_pose_position(sk.find_bone("hips")), sk.get_bone_pose_position(0), sk.get_bone_pose_position(sk.find_bone("shin_L")), sk.get_bone_pose_position(sk.find_bone("foot_L")), sk.get_bone_pose_position(sk.find_bone("toe_L"))]); print("DBG tyL=%.2f tyR=%.2f fyL=%.2f fyR=%.2f " % [sk.get_bone_global_pose(sk.find_bone("toe_L")).origin.y, sk.get_bone_global_pose(sk.find_bone("toe_R")).origin.y, sk.get_bone_global_pose(sk.find_bone("foot_L")).origin.y, sk.get_bone_global_pose(sk.find_bone("foot_R")).origin.y]); print("DBG i=%d lift=%.2f gap=%.2f off=%.2f kL=%.1f kR=%.1f" % [i, wb._hip_lift, wb.foot_gap, wb.ground_off, bend(wb, "thigh_L", "shin_L", "foot_L"), bend(wb, "thigh_R", "shin_R", "foot_R")])
		if i > 30: walked += v.length(); gapmax = maxf(gapmax, absf(wb.foot_gap))
		var tys := {}
		for sd2 in ["L", "R"]: tys[sd2] = (inv * (wb.skel.global_transform * wb.skel.get_bone_global_pose(wb.skel.find_bone("toe_" + sd2)).origin)).y
		for side in ["L", "R"]:
			var tp: Vector3 = wb.skel.global_transform * wb.skel.get_bone_global_pose(wb.skel.find_bone("toe_" + side)).origin
			var lp: Vector3 = inv * tp
			footmin[side] = minf(footmin.get(side, INF), lp.y)
			var planted: bool = lp.y < footmin[side] + 2.0
			var weight_on: bool = planted and tys[side] <= tys["L" if side == "R" else "R"] + 0.3   # carrying the body (lowest foot)
			if i > 60: (st_b if weight_on else sw_b).append(bend(wb, "thigh_" + side, "shin_" + side, "foot_" + side))
			if lastfoot.has(side) and i > 60 and planted and lp.z > lastloc[side].z: slide += (tp - lastfoot[side]).dot(f)
			lastfoot[side] = tp; lastloc[side] = lp
		if vid != "":
			var sd: Vector3 = f.cross(Vector3.UP).normalized()
			c.look_at_from_position(p + sd * 210.0 + Vector3(0, 40, 0) + f * 20.0, p + Vector3(0, 50, 0), Vector3.UP); c.current = true
			get_viewport().get_texture().get_image().save_jpg("%s/f%04d.jpg" % [vid, i], 0.85)
	var avg := func(a: Array) -> float: return a.reduce(func(s, x): return s + x, 0.0) / maxf(a.size(), 1)
	st_b.sort(); sw_b.sort()
	var steps: int = wb.prints_made - p0
	print("WBWALK speed=%.2f m/s rate=%.2f steps_per_s=%.2f knee_stance avg=%.1f p90=%.1f knee_swing avg=%.1f max=%.1f slip=%+.3f m/m sole_gap_max=%.2f" % [walked / maxf(t - 1.0, 0.1), wb.walk_rate, steps / maxf(t, 0.1), avg.call(st_b), st_b[int(st_b.size() * 0.9)] if st_b.size() else 0.0, avg.call(sw_b), sw_b[-1] if sw_b.size() else 0.0, slide / maxf(walked, 0.01), gapmax])
	get_tree().quit()
