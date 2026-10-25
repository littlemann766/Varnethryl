extends Node
## VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json xvfb-run -a -s "-screen 0 1600x720x24" godot --rendering-method mobile -s res://tests/wb_shots.gd
var m: Node
var cam: Camera3D
const OUT := "/workspace/shots/godot15/"
func _ready() -> void:
	m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func shot(n: String) -> void:
	await frames(3)
	get_viewport().get_texture().get_image().save_png(OUT + n + ".png")
	print("SHOT ", n, " dc=", Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), " fps=", Engine.get_frames_per_second())
func hero_at(p: Vector3) -> void:
	m.hero.position = Vector3(p.x, m.height(p.x, p.z) + 0.1, p.z)
func look(from: Vector3, at: Vector3, fov := 60.0) -> void:
	cam.global_position = from; cam.look_at(at, Vector3.UP); cam.fov = fov; cam.current = true
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	await frames(10)
	m.tier = 2; m.apply_quality(); await frames(5); m.time_mode = 1; m._set_time(12.0); await frames(5)
	cam = Camera3D.new(); cam.far = 3000; m.add_child(cam)
	if m.world_boss == null: m.spawn_world_boss(false)   # test 15: gated on the volcano quest; shots force it
	var wb: WorldBoss = m.world_boss
	for t in m.tree_lods: (t[0] as Node3D).visible = false      # keep trees out of the shot camera
	for t in m.tree_mmis: if t is Node3D: (t as Node3D).visible = false
	print("WB pos ", wb.global_position, " crystals ", wb.crystals.size())
	var b := wb.global_position
	var dir := Vector3(b.x, 0, b.z).normalized()
	hero_at(dir * 60.0)
	look(-dir * 230.0 + Vector3(0, 95, 0) + dir.cross(Vector3.UP) * 60.0, b + Vector3(0, 50, 0), 55.0)
	await frames(60); await shot("01_wide_city_scale")
	hero_at(b - dir * 120.0)
	var fwd := wb._fwd()
	look(b + fwd * 210.0 + Vector3(0, 75, 0) + fwd.cross(Vector3.UP) * 70.0, b + Vector3(0, 60, 0), 45.0)
	await frames(40); await shot("02_crystals_veins_front")
	look(b + fwd * 130.0 + Vector3(0, 30, 0) - fwd.cross(Vector3.UP) * 60.0, b + Vector3(0, 35, 0), 50.0)
	await frames(20); await shot("03_crystals_knees_forearm")
	look(b - fwd * 190.0 + Vector3(0, 95, 0) + fwd.cross(Vector3.UP) * 40.0, b + Vector3(0, 70, 0), 45.0)
	await frames(20); await shot("04_back_crystal")
	wb.rituals_done = 0; wb._start_ritual(); wb.t_state = 6.0
	hero_at(b + fwd * 70.0)
	look(b + fwd * 220.0 + Vector3(0, 160, 0) + fwd.cross(Vector3.UP) * 60.0, b + fwd * 20.0, 60.0)
	await frames(4)
	await shot("05_fissure_slam_telegraph")
	cam.current = false; m.cam.current = true; m.yaw = atan2(fwd.x, fwd.z); m.pitch = -0.1
	await frames(3); await shot("06_fissure_castbar_hud")
	wb.t_state = 11.99; await frames(30); await shot("07_fissure_erupt")
	var side0 := fwd.cross(Vector3.UP).normalized()
	look(b + fwd * 140.0 + side0 * 40.0 + Vector3(0, 1.7 + m.height(b.x + fwd.x * 140.0, b.z + fwd.z * 140.0) - b.y, 0), b + Vector3(0, 55, 0), 65.0)
	await frames(10); await shot("13_eye_level_fissure_erupt")
	wb._end_ritual_fx(); wb.rituals_done = 1; wb._start_ritual(); wb.t_state = 7.0
	look(b + fwd * 230.0 + Vector3(0, 120, 0) + side0 * 80.0, b, 55.0); await frames(6); await shot("14_lavawave_telegraph")
	wb.t_state = 9.5; await frames(6)
	look(b + Vector3(0, 330, 1.0), b, 55.0); await frames(6); await shot("14b_lavawave_gaps_top")
	var ga: float = deg_to_rad(wb.wave.gap_angles()[0]); var gd := Vector3(cos(ga), 0, sin(ga))
	look(b + gd * 125.0 + Vector3(0, 1.7 + m.height(b.x + gd.x * 125.0, b.z + gd.z * 125.0) - b.y, 0), b + Vector3(0, 20, 0), 70.0); await frames(6); await shot("14c_lavawave_gap_eye_level")
	print("WAVE gaps ", wb.wave.gap_count, " ", wb.wave.gap_angles(), " in_gap(centre dir)=", wb.wave.is_in_gap(b + gd * 100.0), " in_gap(off)=", wb.wave.is_in_gap(b + gd.rotated(Vector3.UP, 0.4) * 100.0))
	wb.t_state = 9.99; await frames(12); await shot("15_lavawave_release")
	look(b + fwd * 120.0 + Vector3(0, 1.7 + m.height(b.x + fwd.x * 120.0, b.z + fwd.z * 120.0) - b.y, 0), b + Vector3(0, 55, 0), 65.0)
	await frames(5); await shot("16_eye_level_lavawave")
	wb._end_ritual_fx(); wb.rituals_done = 0; wb._start_ritual(); wb.t_state = 5.0; wb.dmg_window = 1e9
	await frames(10); look(b + fwd * 200.0 + Vector3(0, 60, 0), b + Vector3(0, 60, 0), 50.0); await frames(20); await shot("17_interrupted_stagger_dim")
	m.cam.current = true; cam.current = false; m.yaw = atan2(fwd.x, fwd.z); m.pitch = 0.15; hero_at(b + fwd * 200.0)
	await frames(10); await shot("18_eye_level_weakpoint_markers"); cam.current = true
	wb._end_ritual_fx(); wb._set_state("walk")
	Engine.time_scale = 10.0
	var t0 := Time.get_ticks_msec()
	while wb.footprints.size() < 3 and Time.get_ticks_msec() - t0 < 120000: await frames(5)
	Engine.time_scale = 1.0
	b = wb.global_position; fwd = wb._fwd()
	print("prints ", wb.footprints.size())
	hero_at(b - fwd * 100.0)
	look(b - fwd * 170.0 + Vector3(0, 150, 0) + fwd.cross(Vector3.UP) * 60.0, b - fwd * 40.0, 55.0)
	await frames(30); await shot("08_footprints_dust")
	print("prints_now ", wb.footprints.size(), " fp0_vis ", (wb.footprints[0][0] as Node3D).visible if wb.footprints.size() > 0 else false)
	look(b - fwd * 40.0 + Vector3(0, 220, 0), b - fwd * 40.0, 50.0); await frames(5); await shot("10_footprints_topdown")
	var side := fwd.cross(Vector3.UP).normalized()
	ap_walk_pos(wb, 2.5); look(b + side * 150.0 + Vector3(0, 30, 0), b + Vector3(0, 28, 0), 40.0); await frames(4); await shot("11_knees_side_midwalk_L")
	ap_walk_pos(wb, 7.5); await frames(4); await shot("12_knees_side_midwalk_R"); wb.ap.play()
	m.tier = 0; m.apply_quality(); await frames(20)
	look(-dir * 230.0 + Vector3(0, 95, 0), wb.global_position + Vector3(0, 50, 0), 55.0); await shot("09_low_tier")
	get_tree().quit()

func ap_walk_pos(wb, t: float) -> void:
	wb.ap.play("wb_walk"); wb.ap.seek(t, true); wb.ap.pause()
