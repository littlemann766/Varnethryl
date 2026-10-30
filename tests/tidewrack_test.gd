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
	# --- test 33: Owner + CoOwner upgrade their own ship free; normal player stays locked
	var C: Cheats = m.cheats; var rp0: Callable = C.role_provider; var save0: Dictionary = sea.save.duplicate(true); var g0: int = int(VS.gold)
	for who in ["", "owner", "coowner"]:
		C.role_provider = func() -> String: return who
		sea.save.galleon_tier = 0; sea.save.coil_beaten = false; sea.save.glasswyrm_beaten = false; sea.save.items = {}; VS.gold = 0; sea.ship.set_tier(0)
		var tag: String = who if who != "" else "player"
		if who == "":
			ok(not sea.free_upgrade() and sea.upgrade("galleon") != "" and int(sea.save.galleon_tier) == 0, "player: T1 locked without gold/items")
			sea.save.galleon_tier = 1; ok(sea.upgrade("galleon") == "Needs the Brinecrown Coil beaten.", "player: T2 still needs the Coil")
			sea.save.galleon_tier = 2; ok(sea.upgrade("galleon") == "Needs the Glasswyrm beaten.", "player: T3 still needs the Glasswyrm")
			continue
		var errs := []
		for i in 3: errs.append(sea.upgrade("galleon"))
		ok(errs == ["", "", ""] and int(sea.save.galleon_tier) == 3 and sea.ship.tier == 3, "%s: galleon T1-T3 free, no boss wins (%s)" % [tag, errs])
		ok(int(VS.gold) == 0 and sea.save.items.is_empty() and not bool(sea.save.coil_beaten), "%s: no gold/items spent, boss flags untouched" % tag)
		ok(sea.upgrade("galleon") == "Fully upgraded.", "%s: stops at T3" % tag)
		sea.save.skiff_tier = 0; var se := []
		for i in 3: se.append(sea.upgrade("skiff"))
		ok(se == ["", "", ""] and int(sea.save.skiff_tier) == 3, "%s: skiff T1-T3 free" % tag)
		if who == "coowner":
			ok(C.allowed("ship_upgrade", "coowner") and not C.allowed("gold", "coowner") and not C.allowed("spawn_boss", "coowner"), "coowner: ship_upgrade allowed, world/economy cheats still refused")
			ok(not sea.unlock_all and not sea.unlocked("B"), "coowner: free upgrades do not unlock the storm-locked sea")
	await shot("galleon_t3_coowner", an + Vector3(30, 14, 30), an + Vector3(0, 4, 0))
	C.coowner_ok = false
	C.role_provider = func() -> String: return ""
	ok(not sea.free_upgrade(), "unverified coowner (role '') gets no free upgrade")
	C.role_provider = rp0
	for k in save0: sea.save[k] = save0[k]
	VS.gold = g0; sea.ship.set_tier(int(sea.save.galleon_tier))
	ok(sea.ship.gust() and sea.ship.gust_t > 0.0, "gust charm (T1)")
	await shot("galleon_t1", an + Vector3(30, 14, 30), an + Vector3(0, 4, 0))
	# --- test 33: speed cheat scales the ship; fly cheat lifts the whole ship (Owner + CoOwner), players can't
	var C2: Cheats = m.cheats; var rp1: Callable = C2.role_provider; var fa0: float = m.fly_alt
	var open := an + Vector3(0, 0, 0)
	for k in 60:   # find open water near Gullhaven
		var q2 := an + Vector3(cos(k * 0.7), 0, sin(k * 0.7)) * (120.0 + k * 10.0)
		if sea.over_water(Vector2(q2.x, q2.z)) and sea.shore_m(Vector2(q2.x, q2.z)) > 120.0 and sea.unlocked(sea.region_at(Vector2(q2.x, q2.z))): open = q2; break
	var land := Vector3.INF
	for k in 400:
		var q3 := an + Vector3(cos(k * 0.37), 0, sin(k * 0.37)) * (10.0 + k * 2.0)
		if not sea.over_water(Vector2(q3.x, q3.z)) and sea.unlocked(sea.region_at(Vector2(q3.x, q3.z))): land = q3; break
	var sail := func(n: int) -> void:
		for i in n: sea.ship.throttle = 1.0; sea.drive(Vector2.ZERO, 1.0 / 60.0)
	C2.role_provider = func() -> String: return "owner"
	C2.request("fly", false); C2.request("speed", 1.0)
	sea.ship.position = Vector3(open.x, 0, open.z); sea.ship.speed = 0.0; sail.call(600)
	var v1: float = sea.ship.speed
	sea.ship.position = Vector3(open.x, 0, open.z); C2.request("speed", 3.0); sail.call(900)
	print("TW INFO speed x1=%.1f x3=%.1f" % [v1, sea.ship.speed])
	ok(v1 > 1.0 and sea.ship.speed > v1 * 2.5, "speed cheat x3 scales sailing speed (%.1f -> %.1f m/s)" % [v1, sea.ship.speed])
	C2.request("speed", 1.0)
	for who in ["owner", "coowner"]:
		C2.role_provider = func() -> String: return who
		sea.ship.position = Vector3(open.x, 0, open.z); sea.ship.alt = 0.0; sea.ship.speed = 0.0
		ok(C2.request("fly", true), "%s: fly cheat on at sea" % who)
		m.fly_alt = 30.0; sail.call(300)
		ok(absf(sea.ship.alt - 30.0) < 0.5 and absf(sea.ship.global_position.y - sea.to_global(Vector3(0, 30, 0)).y) < 0.6, "%s: whole ship flies at fly_alt (alt %.1f)" % [who, sea.ship.alt])
		ok(absf(sea.ship.rotation.x) < 0.001 and absf(sea.ship.rotation.z) < 0.001, "%s: flying ship stays level" % who)
		ok(sea.ship.speed > 1.0 and Vector2(sea.ship.position.x - open.x, sea.ship.position.z - open.z).length() > 10.0, "%s: flying ship is steerable/moves" % who)
		await frames(10); ok(m.fly_controls.visible, "%s: fly buttons shown at sea with fly on (hud=%s title=%s fly=%s)" % [who, VUI.hud.visible, VUI.title.visible if VUI.title else false, C2.flags.fly])
		C2.request("fly_up"); C2.request("fly_up"); sail.call(200)
		ok(sea.ship.alt > 34.0, "%s: fly up raises the ship (%.1f)" % [who, sea.ship.alt])
		if who == "owner": await shot("galleon_flying", Vector3(sea.ship.position.x + 45, sea.ship.alt + 12, sea.ship.position.z + 45), sea.ship.position)
		# fly off over land: holds above ground, then settles once back over water
		if land != Vector3.INF:
			sea.ship.position = Vector3(land.x, sea.ship.alt, land.z); C2.request("fly", false); sea.ship.throttle = 0.0; sea.ship.speed = 0.0
			for i in 400: sea.drive(Vector2.ZERO, 1.0 / 60.0)
			ok(sea.ship.alt >= sea.SHIP_FLY_MIN - 0.01, "%s: fly off over land -> ship hovers, never drops on land (alt %.1f)" % [who, sea.ship.alt])
		C2.request("fly", false); sea.ship.position = Vector3(open.x, sea.ship.alt, open.z); sea.ship.speed = 0.0
		for i in 600: sea.drive(Vector2.ZERO, 1.0 / 60.0)
		ok(sea.ship.alt == 0.0 and absf(sea.ship.rotation.x) < 0.001 and sea.ship.collision_mask == 1, "%s: fly off over water -> lands back on the sea" % who)
		await frames(10); ok(not m.fly_controls.visible, "%s: fly buttons hidden at sea with fly off (hud=%s fly=%s active=%s)" % [who, VUI.hud.visible, C2.flags.fly, sea.active])
	C2.role_provider = func() -> String: return ""
	ok(not C2.request("fly", true), "player: fly cheat refused")
	sea.ship.position = Vector3(open.x, 0, open.z); m.fly_alt = 30.0; sail.call(200)
	ok(sea.ship.alt == 0.0, "player: ship stays on the water")
	C2.role_provider = rp1; m.fly_alt = fa0; C2.flags.fly = false; C2.flags.speed = 1.0; if m.get("cheat"): m.cheat.fly = false
	sea.ship.position = an; sea.ship.speed = 0.0; sea.ship.throttle = 0.0
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
	# --- test 33: Pip + companions ride ON the deck (every galleon tier + the skiff), even while the ship flies
	m.party._set_companions(["nyx", "selene"]); await frames(5)
	var crew_ok := func(tag: String) -> void:
		var bad := []
		var nodes: Array = [m.pip] + m.party.companions.map(func(c): return c.node)
		for n: Node3D in nodes:
			var lp: Vector3 = sea.ship.global_transform.affine_inverse() * n.global_position
			var half: Vector2 = Vector2(2.3, 7.0) if sea.ship.kind == "galleon" else Vector2(0.8, 3.0)
			var dy: float = n.global_position.y - (sea.ship.global_position.y + sea.deck_y())
			if absf(lp.x) > half.x or absf(lp.z) > half.y or absf(dy) > 0.2 or not n.visible: bad.append("%s lp=%s dy=%.2f vis=%s" % [n.name, lp, dy, n.visible])
		ok(bad.is_empty() and m.party.riding, "%s: Pip + %d companions seated on deck %s" % [tag, m.party.companions.size(), bad])
	for t in 4:
		sea.ship.set_tier(t); sea.ship.speed = 8.0; sea.ship.throttle = 1.0
		for i in 120: sea.drive(Vector2(0.3, 0), 1.0 / 60.0)
		crew_ok.call("galleon T%d sailing" % t)
	var Cc: Cheats = m.cheats; var rpc: Callable = Cc.role_provider
	Cc.role_provider = func() -> String: return "owner"
	Cc.request("fly", true); m.fly_alt = 25.0
	for i in 300: sea.drive(Vector2(0.2, 0), 1.0 / 60.0)
	crew_ok.call("galleon flying (alt %.0f)" % sea.ship.alt)
	Cc.request("fly", false)
	for i in 600: sea.drive(Vector2.ZERO, 1.0 / 60.0)
	Cc.role_provider = rpc
	sea.ship.speed = 0.0; sea.drive(Vector2.ZERO, 1.0 / 60.0)
	await shot("pip_on_deck", sea.ship.position + sea.ship.global_basis * Vector3(9, 7, -9), sea.ship.position + Vector3(0, 3, 0))
	sea._board("skiff", sea.ship.position + Vector3(30, 0, 0), sea.ship.heading)
	for t in 4:
		sea.ship.set_tier(t)
		for i in 60: sea.drive(Vector2(0.3, 0), 1.0 / 60.0)
		crew_ok.call("skiff T%d" % t)
	await shot("skiff_crew", sea.ship.position + sea.ship.global_basis * Vector3(4, 3, -4), sea.ship.position + Vector3(0, 1, 0))
	sea._board("galleon", sea.ship.position + Vector3(-30, 0, 0), sea.ship.heading); sea.ship.set_tier(int(sea.save.galleon_tier))
	# --- charts home
	ok(sea.chart_travel("tidewrack") == "", "Harbour Charts: Tidewrack pier")
	await frames(90)
	ok(not sea.active and m.hero.global_position.distance_to(m._galleon_pier()[0]) < 3.0, "home at the Tidewrack pier (hero %s, pier %s)" % [m.hero.global_position, m._galleon_pier()[0]])
	ok(not m.party.riding and m.party.companions.all(func(c): return c.node.global_position.distance_to(m.hero.global_position) < 6.0), "disembark: companions follow on foot again")
	m.party._set_companions([])
	VS = get_tree().root.get_node("VSave").state; VS.gold = gold0; sea.save.galleon_tier = 0; sea.save.items = {}; sea.save.discovered_ports = ["tidewrack"]; sea.write_save()
	print("TW DONE pass=%d fail=%d" % [npass, nfail]); get_tree().quit(0 if nfail == 0 else 1)
