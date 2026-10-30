extends Node
## test 32: Tidewrack Sea wiring test + shots (-- --tidewrack). Prints TW PASS/FAIL lines and "TW DONE pass=N fail=M".
var m: Node
var sea: TidewrackSea
var npass := 0
var nfail := 0
var out := "/workspace/shots/voxel32/"
func ok(c: bool, t: String) -> void:
	if c: npass += 1; print("TW PASS ", t)
	else: nfail += 1; print("TW FAIL ", t)
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func until(f: Callable, n := 900) -> bool:
	for i in n:
		if f.call(): return true
		await get_tree().physics_frame
	return false
func shot(n: String, cam_from := Vector3.INF, at := Vector3.INF) -> void:
	if DisplayServer.get_name() == "headless": return
	var c: Camera3D = null
	if cam_from != Vector3.INF:
		c = Camera3D.new(); c.far = 3000; c.fov = 60; m.add_child(c); c.environment = m.cam.environment
		c.look_at_from_position(sea.to_global(cam_from), sea.to_global(at), Vector3.UP); c.current = true
	await frames(20)
	get_viewport().get_texture().get_image().save_png(out + "tw_%s.png" % n); print("TW SHOT ", n)
	if c: c.queue_free(); m.cam.current = true
func ray_y(p: Vector3) -> float:
	var w := sea.to_global(Vector3(p.x, 120, p.z)); var q := PhysicsRayQueryParameters3D.create(w, w - Vector3(0, 200, 0), 1)
	var h: Dictionary = m.get_world_3d().direct_space_state.intersect_ray(q)
	return sea.to_local(h.position).y if h else -999.0
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(out)
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0); m.party._set_companions([]); m.party.set_hero("aldric")
	sea = m.sea; var VS: Dictionary = get_tree().root.get_node("VSave").state; var gold0: int = int(VS.get("gold", 0))
	sea.save.galleon_tier = 0; sea.save.skiff_tier = 0; sea.save.discovered_ports = ["tidewrack"]; sea.save.coil_beaten = false
	# --- set sail from the pier prompt path
	var g: Array = m._galleon_pier(); m._teleport(g[0], g[1]); await frames(5)
	ok(sea.ui.prompt.visible and sea.ui.prompt.text == "Set sail", "Set sail prompt beside the moored galleon")
	sea.ui._cb.call(); await frames(60)
	ok(sea.active and sea.ship != null and sea.ship.kind == "galleon", "boarded the galleon in the Tidewrack Sea")
	ok(await until(func(): return sea.regions.get("A", {}).get("state", 0) == 2), "region A streamed in (threaded load)")
	await frames(3)
	ok(not m.party.hud.visible and not m.fly_controls.visible, "combat + jump/fly buttons hidden while sailing")
	if m.world_boss: m.world_boss._warn("3 SECONDS! Break his crystals!"); await frames(2); ok(not m.world_boss.ui.visible and not m.world_boss.warn.visible, "mainland world-boss popups suppressed at sea")
	await shot("A_start")
	# --- water: per-region shader + shore rect shifted to world coords
	var wm: ShaderMaterial = sea.water.material_override
	ok(wm != null and wm.get_shader_parameter("shore_rect").y == -1300.0 + TidewrackSea.OFF.z, "water shore_rect in world coords")
	var t0: int = m.tier; m.tier = 0
	ok(sea._water_mat("ash").shader.resource_path.ends_with("stage4/shaders/ocean_water_low_straits.gdshader"), "Low ash water = ocean_water_low_straits")
	ok(sea._water_mat("frost").shader.resource_path.ends_with("stage1/shaders/ocean_water_low.gdshader"), "Low frost water = stage1 ocean_water_low")
	m.tier = 2
	ok(sea._water_mat("ash").shader.resource_path.ends_with("stage1/shaders/ocean_water.gdshader"), "High ash water = stage1 ocean_water")
	m.tier = t0
	# --- sailing
	var p0: Vector3 = sea.ship.position
	for i in 360: sea.drive(Vector2(0, -1), 1.0 / 60.0)
	ok(sea.ship.position.distance_to(p0) > 15.0 and sea.ship.speed > 4.0 and sea.ship.speed <= 13.0 * 1.15 + 0.01, "galleon sails (moved %.0f m, %.1f m/s)" % [sea.ship.position.distance_to(p0), sea.ship.speed])
	var h0: float = sea.ship.heading
	for i in 120: sea.drive(Vector2(1, 0), 1.0 / 60.0)
	ok(absf(sea.ship.heading - h0) > 0.3, "rudder turns the ship")
	var sp := sea.ship.speed
	for i in 60: sea.drive(Vector2.ZERO, 1.0 / 60.0)
	ok(sea.ship.speed > sp * 0.6, "coasting: the sail setting holds with no input")
	ok(absf(sea.ship.rotation.x) < 0.001 and absf(sea.ship.rotation.z) < 0.001, "ship stays level (no pitch/roll)")
	# --- borders: A's west box (towards locked B) blocks, its north box (towards frost) is open
	var west := 0; var north := 0
	for c in sea.regions.A.cols:
		if c[1].x < -1100.0 and c[0].collision_layer == 1: west += 1
		if c[1].z < -1200.0 and c[0].collision_layer == 0: north += 1
	ok(sea.regions.A.cols.size() >= 4 and west >= 1, "invisible storm collider stands towards locked B (%d boxes)" % sea.regions.A.cols.size())
	ok(north >= 1, "border box between two unlocked regions dropped")
	sea.ship.position = Vector3(-1120, 0, 0); sea.ship.heading = -PI / 2; sea.ship.speed = 13.0; sea.ship.throttle = 1.0
	for i in 400: sea.drive(Vector2(0, -1), 1.0 / 60.0)
	ok(sea.ship.position.x > -1205.0, "locked region B: ship held back (x=%.0f)" % sea.ship.position.x)
	# --- Wreck Reef ring
	var reef := sea._v3(sea.M.s1.props.wreck_reef.pos)
	sea.ship.position = reef + Vector3(20, 0, 0); sea.drive(Vector2.ZERO, 1.0 / 60.0)
	ok(Vector2(sea.ship.position.x - reef.x, sea.ship.position.z - reef.z).length() >= 94.9, "galleon kept out of the Wreck Reef ring")
	# --- Gullhaven: dock, chart, shipwright
	var an := sea._v3(sea.M.s1.props.gullhaven.anchor); sea.ship.position = an; sea.ship.speed = 0.0; sea.ship.throttle = 0.0; sea.drive(Vector2.ZERO, 1.0 / 60.0)
	ok(sea.save.discovered_ports.has("gullhaven") and sea.ui.prompt.text == "Shipwright", "docking at Gullhaven charts it + Shipwright prompt")
	VS = get_tree().root.get_node("VSave").state; sea.save.galleon_tier = 0; sea.ship.set_tier(0); VS.gold = 100; ok(sea.upgrade("galleon") != "", "upgrade refused without gold/Driftwood")
	VS.gold = 5000; sea.save.items = {"Driftwood": 10}
	var ue := sea.upgrade("galleon"); print("TW INFO upgrade: '%s' tier=%d" % [ue, sea.ship.tier])
	ok(ue == "" and sea.ship.tier == 1 and sea.ship.addon != null, "Patched Canvas (T1) add-on fitted")
	ok(sea.upgrade("galleon") != "", "T2 needs the Coil beaten")
	ok(sea.ship.gust() and sea.ship.gust_t > 0.0, "gust charm (T1)")
	await shot("galleon_t1", an + Vector3(30, 14, 30), an + Vector3(0, 4, 0))
	# --- Echo Grotto: clear exit (never inside the north cliff), skiff, cave cell in/out
	var q: Dictionary = sea.M.s2.props.coast_echo_grotto; var mouth := sea._v3(q.pos)
	sea.unlock_all = true; sea._border_update()   # Owner-style unlock for the B checks
	sea.ship.position = mouth + Vector3(300, 0, 0); sea.cur_region = "B"; sea._stream(Vector2(mouth.x, mouth.z))
	ok(await until(func(): sea._stream(Vector2(mouth.x, mouth.z)); return sea.regions.get("B", {}).get("state", 0) == 2, 1800), "region B streamed in")
	var ex: Array = sea.clear_exit(mouth, float(q.yaw))
	ok(sea.shore_m(Vector2(ex[0].x, ex[0].z)) >= 6.0 and ray_y(ex[0]) < 0.5, "Echo Grotto exit is open water (shore %.0f m, ground %.1f m)" % [sea.shore_m(Vector2(ex[0].x, ex[0].z)), ray_y(ex[0])])
	var fixed: Vector3 = mouth + Vector3(sin(float(q.yaw)), 0, cos(float(q.yaw))) * 60.0
	print("TW INFO old fixed-60m point ground=%.1f shore=%.0f; clear exit %.0f m from mouth" % [ray_y(fixed), sea.shore_m(Vector2(fixed.x, fixed.z)), ex[0].distance_to(mouth)])
	sea._board("skiff", ex[0], ex[1] + PI); sea.drive(Vector2.ZERO, 1.0 / 60.0)
	await shot("echo_grotto_mouth_from_exit", ex[0] + Vector3(0, 9, 0) - Vector3(sin(ex[1] + PI), 0, cos(ex[1] + PI)) * 12.0, mouth + Vector3(0, 4, 0))
	sea._cave_enter("echo_grotto"); await frames(90)
	ok(sea.in_cave == "echo_grotto" and sea.cells.echo_grotto.visible and m.cam.environment == sea.cave_env, "fade into the Echo Grotto cell")
	for i in 200: sea.drive(Vector2(0, -0.3), 1.0 / 60.0)
	await shot("echo_grotto_inside")
	sea.ship.position = sea.cells.echo_grotto.position + Vector3(0, 0, 9); sea.drive(Vector2.ZERO, 1.0 / 60.0); await frames(90)
	ok(sea.in_cave == "" and sea.ship.position.distance_to(ex[0]) < 15.0 and sea.shore_m(Vector2(sea.ship.position.x, sea.ship.position.z)) >= 3.0, "back out of the cell to the clear exit (%.1f m)" % sea.ship.position.distance_to(ex[0]))
	for cave in ["glasswyrm_cavern", "smugglers_throat"]:
		sea._cave_enter(cave); await frames(90); var c_ok: bool = sea.in_cave == cave
		await shot(cave + "_inside")
		sea.ship.position = sea.cells[cave].position + Vector3(0, 0, 9); sea.drive(Vector2.ZERO, 1.0 / 60.0); await frames(90)
		ok(c_ok and sea.in_cave == "", "%s cell in/out" % cave)
	# --- Sunken Ward dive
	var dv := sea._v3(sea.M.s2.props.sunken_ward.dive_buoy); sea.ship.position = dv + Vector3(10, 0, 0); sea.ship.speed = 0.0; sea.drive(Vector2.ZERO, 1.0 / 60.0)
	ok(sea.ui.prompt.text == "Dive", "dive prompt inside the Sunken Ward ring")
	sea.dive(); await frames(90)
	ok(sea.diving and sea.to_local(m.hero.global_position).y < -2.0, "dived into the Sunken Ward")
	for i in 240: sea.drive(Vector2(0, -1), 1.0 / 60.0)
	ok(ray_y(sea.to_local(m.hero.global_position)) > -40.0, "Ward seabed collider under the diver")
	await shot("sunken_ward")
	sea.surface(); await frames(90)
	ok(not sea.diving and m.cam.environment == null, "surfaced")
	# --- frost: icebergs drift
	var fp := Vector3(600, 0, -1800); sea._board("galleon", fp, 0.0); sea.cur_region = "frost"
	ok(await until(func(): sea._stream(Vector2(fp.x, fp.z)); return sea.regions.get("frost", {}).get("state", 0) == 2, 1800), "frost region streamed in")
	ok(sea.bergs.size() == 12, "12 drifting icebergs (%d)" % sea.bergs.size())
	if sea.bergs.size() > 0:
		var b0: Node3D = sea.bergs[0].node; var s0 := b0.position
		for i in 600: sea._tick_bergs(0.1)   # 60 s
		ok(b0.position.distance_to(s0) > 5.0, "iceberg drifted %.1f m in 60 s" % b0.position.distance_to(s0))
		await shot("frost_icebergs", b0.position + Vector3(90, 30, 90), b0.position)
	# --- ash
	var ap := sea._v3(sea.M.s4.props.vent_harbour.anchor); sea._board("galleon", ap, 0.0); sea.cur_region = "ash"
	ok(await until(func(): sea._stream(Vector2(ap.x, ap.z)); return sea.regions.get("ash", {}).get("state", 0) == 2, 1800), "ash region streamed in")
	var basalt := false; var lava := false
	for mi: MeshInstance3D in sea.regions.ash.node.find_children("*", "MeshInstance3D", true, false):
		if mi.material_override is StandardMaterial3D and is_equal_approx(mi.material_override.metallic_specular, 0.15): basalt = true
		if mi.material_override is ShaderMaterial and mi.material_override.shader.resource_path.ends_with("lava_seam.gdshader"): lava = true
	ok(basalt and lava, "ash basalt (metallic_specular 0.15) + lava seam materials")
	sea.drive(Vector2.ZERO, 1.0 / 60.0); await shot("ash_vent_harbour_" + m.TIERS[m.tier])
	m.tier = 0; sea.water_mats.clear(); sea.drive(Vector2.ZERO, 1.0 / 60.0); await shot("ash_vent_harbour_Low_water"); m.tier = t0; sea.water_mats.clear()
	# --- charts home
	ok(sea.chart_travel("tidewrack") == "", "Harbour Charts: Tidewrack pier")
	await frames(90)
	ok(not sea.active and m.hero.global_position.distance_to(m._galleon_pier()[0]) < 3.0, "home at the Tidewrack pier (hero %s, pier %s)" % [m.hero.global_position, m._galleon_pier()[0]])
	VS = get_tree().root.get_node("VSave").state; VS.gold = gold0; sea.save.galleon_tier = 0; sea.save.items = {}; sea.save.discovered_ports = ["tidewrack"]; sea.write_save()
	print("TW DONE pass=%d fail=%d" % [npass, nfail]); get_tree().quit(0 if nfail == 0 else 1)
