extends Node
## VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json xvfb-run -a -s "-screen 0 1600x720x24" godot --rendering-method mobile -s res://tests/wb_shots.gd
var m: Node
var cam: Camera3D
const OUT := "/workspace/shots/worldboss1/"
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
	m.tier = 2; m.apply_quality(); m._set_time(15.5)
	cam = Camera3D.new(); cam.far = 3000; m.add_child(cam)
	var wb: WorldBoss = m.world_boss
	print("WB pos ", wb.global_position, " crystals ", wb.crystals.size())
	var b := wb.global_position
	var dir := Vector3(b.x, 0, b.z).normalized()
	hero_at(dir * 60.0)
	look(-dir * 230.0 + Vector3(0, 95, 0) + dir.cross(Vector3.UP) * 60.0, b + Vector3(0, 50, 0), 55.0)
	await frames(60); await shot("01_wide_city_scale")
	hero_at(b - dir * 120.0)
	var fwd := Vector3(sin(wb.rotation.y), 0, cos(wb.rotation.y))
	look(b + fwd * 95.0 + Vector3(0, 70, 0) + fwd.cross(Vector3.UP) * 30.0, b + Vector3(0, 62, 0), 50.0)
	await frames(40); await shot("02_crystals_veins_front")
	look(b + fwd * 60.0 + Vector3(0, 25, 0) - fwd.cross(Vector3.UP) * 40.0, b + Vector3(0, 35, 0), 55.0)
	await frames(20); await shot("03_crystals_knees_forearm")
	look(b - fwd * 80.0 + Vector3(0, 85, 0), b + Vector3(0, 75, 0), 50.0)
	await frames(20); await shot("04_back_crystal")
	wb.rituals_done = 0; wb._start_ritual(); wb.t_state = 8.5
	hero_at(b + fwd * 70.0)
	await frames(30)
	look(b + fwd * 150.0 + Vector3(0, 110, 0), b + fwd * 20.0, 65.0)
	await shot("05_fissure_slam_telegraph")
	cam.current = false; m.cam.current = true; m.yaw = atan2(fwd.x, fwd.z); m.pitch = -0.1
	await frames(20); await shot("06_fissure_castbar_hud")
	wb.t_state = 11.99; await frames(30); await shot("07_fissure_erupt")
	wb._end_ritual_fx(); wb._set_state("walk")
	Engine.time_scale = 10.0
	var t0 := Time.get_ticks_msec()
	while wb.footprints.size() < 3 and Time.get_ticks_msec() - t0 < 120000: await frames(5)
	Engine.time_scale = 1.0
	b = wb.global_position; fwd = Vector3(sin(wb.rotation.y), 0, cos(wb.rotation.y))
	print("prints ", wb.footprints.size())
	hero_at(b - fwd * 100.0)
	look(b - fwd * 150.0 + Vector3(0, 120, 0) + fwd.cross(Vector3.UP) * 50.0, b - fwd * 30.0, 60.0)
	await frames(30); await shot("08_footprints_dust")
	m.tier = 0; m.apply_quality(); await frames(20)
	look(-dir * 230.0 + Vector3(0, 95, 0), wb.global_position + Vector3(0, 50, 0), 55.0); await shot("09_low_tier")
	get_tree().quit()
