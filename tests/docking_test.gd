extends Node
## test 34: every landing point: sail up -> "Go ashore" -> ship parked level at the moor, hero + Pip + companions ashore ->
## walk 20 m inland on the real colliders (never below the sea, never stuck) -> back to the pier -> "Board ship" -> on deck.
## Also: mainland Tidewrack pier "Go ashore", map markers + fog. Shots with a display. Run: -- --docking
var m: Node
var sea: TidewrackSea
var npass := 0
var nfail := 0
var out := "/workspace/shots/t37/dock/"
func ok(c: bool, t: String) -> void:
	if c: npass += 1; print("DK PASS ", t)
	else: nfail += 1; print("DK FAIL ", t)
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func shot(n: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await frames(25); var img := get_viewport().get_texture().get_image(); img.save_png(out + "dock_%s.png" % n); print("DK SHOT ", n)
	# test 37: camera blackout check -- share of near-black pixels (Vent t36 was ~55%, Gullhaven ~20%)
	var dark := 0; var tot := 0
	for y in range(0, img.get_height(), 8):
		for x in range(0, img.get_width(), 8):
			tot += 1
			if img.get_pixel(x, y).get_luminance() < 0.05: dark += 1
	ok(float(dark) / tot < 0.04, "%s: no camera blackout (%.1f%% near-black pixels)" % [n, 100.0 * dark / tot])
## test 36: every companion's (and Pip's) feet within 0.1 m of the real floor
func feet_check(k: String, when: String) -> void:
	var nodes: Array = [["pip", m.pip]]
	for c in m.party.companions:
		if not m.party.FLYERS.has(c.id): nodes.append([c.id, c.node])
	for e in nodes:
		var n: Node3D = e[1]; var gy: float = sea.floor_y(n.global_position)
		var d: float = absf(n.global_position.y - gy) if not is_nan(gy) else 99.0
		ok(d <= 0.1, "%s: %s feet %.2f m from ground %s" % [k, e[0], d, when])
func hud_check(where: String) -> void:
	var keep: String = sea.ui.msg.text
	sea.ui.msg.text = "Ashore at Some Very Long Landing Name."; await frames(2)
	var o: Array = HudOverlap.overlaps(get_tree().root)
	sea.ui.msg.text = keep
	ok(o.is_empty(), "%s: no HUD texts overlap %s" % [where, str(o)])
## test 36 (Beth stage 5 islands): from the pier head walk to every POI in stage5_manifest.json and back, on foot on the
## real colliders: never below the sea, no safety resets (fall / no floor / stuck), and the floor ray never misses (gaps).
## grid path over the real colliders (1.5 m cells, <= 1.1 m rise per cell ~36 deg), so the walk follows the island's
## paths/switchbacks like a player would instead of beelining into a cliff.
var _grid := {}
func build_grid(win: Array) -> void:
	_grid = {}
	var x0: float = win[0]; var z0: float = win[1]; var x1: float = win[2]; var z1: float = win[3]
	var space: PhysicsDirectSpaceState3D = m.get_world_3d().direct_space_state
	var ix := 0; var x := x0
	while x <= x1:
		var iz := 0; var z := z0
		while z <= z1:
			var w := sea.to_global(Vector3(x, 0, z))
			var q := PhysicsRayQueryParameters3D.create(w + Vector3(0, 200, 0), w - Vector3(0, 5, 0), 1)
			q.exclude = [m.hero.get_rid()]
			var h: Dictionary = space.intersect_ray(q)
			if h and h.normal.y > 0.6 and sea.to_local(h.position).y > 0.3: _grid[Vector2i(ix, iz)] = sea.to_local(h.position)
			z += 1.5; iz += 1
		x += 1.5; ix += 1
func grid_path(from: Vector3, to: Vector3) -> Array:
	var best_a := Vector2i(-1, -1); var best_b := Vector2i(-1, -1); var da := 1e9; var db := 1e9
	for c in _grid:
		var p: Vector3 = _grid[c]
		var a := Vector2(p.x - from.x, p.z - from.z).length(); var b := Vector2(p.x - to.x, p.z - to.z).length() + absf(p.y - to.y) * 0.5
		if a < da: da = a; best_a = c
		if b < db: db = b; best_b = c
	var prev := {best_a: best_a}; var queue: Array = [best_a]; var qi := 0
	while qi < queue.size():
		var c: Vector2i = queue[qi]; qi += 1
		if c == best_b: break
		for o in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1)]:
			var n: Vector2i = c + o
			if prev.has(n) or not _grid.has(n): continue
			if absf(_grid[n].y - _grid[c].y) > 1.1 * (1.41 if o.x != 0 and o.y != 0 else 1.0): continue
			prev[n] = c; queue.append(n)
	if not prev.has(best_b): return []
	var path: Array = []; var c2: Vector2i = best_b
	while c2 != best_a: path.push_front(_grid[c2]); c2 = prev[c2]
	return path
func walk_path(tgt: Vector3, reach: float, limit_s: float) -> Dictionary:
	var path := grid_path(sea.to_local(m.hero.global_position), tgt)
	if path.is_empty(): return {"ok": false, "resets": 0, "gaps": 0, "minh": 0.0, "t": 0.0, "nopath": true}
	var tot := {"ok": true, "resets": 0, "gaps": 0, "minh": 1e9, "t": 0.0}
	for i in range(0, path.size(), 4):
		var wp: Vector3 = path[mini(i + 3, path.size() - 1)]
		var r := await walk_to(wp, 2.0, 25.0)
		tot.resets += r.resets; tot.gaps += r.gaps; tot.minh = minf(tot.minh, r.minh); tot.t += r.t
		if not r.ok: tot.ok = false; break
	if tot.ok: var f := await walk_to(tgt, reach, 20.0); tot.ok = f.ok; tot.resets += f.resets; tot.gaps += f.gaps; tot.t += f.t
	return tot
func walk_to(tgt: Vector3, reach: float, limit_s: float) -> Dictionary:
	var resets := 0; var gaps := 0; var minh := 1e9; var t := 0.0; var last: Vector3 = m.hero.global_position; var still := 0.0; var detour := 0.0; var dsign := 1.0
	while t < limit_s:
		var lp := sea.to_local(m.hero.global_position)
		var to := Vector2(tgt.x - lp.x, tgt.z - lp.z)
		if to.length() <= reach: return {"ok": true, "resets": resets, "gaps": gaps, "minh": minh, "t": t}
		var yaw := atan2(-to.x, -to.y)
		if detour > 0.0: yaw += dsign * 1.1; detour -= 1.0 / 60.0
		m.yaw = yaw
		sea.drive(Vector2(0, -1), 1.0 / 60.0); t += 1.0 / 60.0
		lp = sea.to_local(m.hero.global_position); minh = minf(minh, lp.y)
		if sea.ui.msg.text.begins_with("Careful"): resets += 1; sea.ui.msg.text = ""
		if m.hero.is_on_floor() and sea._ray_floor(lp, 0.5, 3.0).is_empty(): gaps += 1
		if fmod(t, 1.0) < 1.0 / 60.0:
			if m.hero.global_position.distance_to(last) < 1.0: still += 1.0
			else: still = 0.0
			last = m.hero.global_position
			if still >= 2.0: detour = 1.2; dsign = -dsign; still = 0.0
		await get_tree().physics_frame
	return {"ok": false, "resets": resets, "gaps": gaps, "minh": minh, "t": t}
var _s5 := {}
func poi_walk(k: String, d: Dictionary) -> void:
	if _s5.is_empty(): _s5 = JSON.parse_string(FileAccess.get_file_as_string("res://tidewrack/stage5_manifest.json")).islands
	var isl: Dictionary = _s5.get(k, {})
	ok(not isl.is_empty(), "%s: stage 5 island in the manifest" % k)
	if isl.is_empty(): return
	build_grid(isl.window)
	for poi in isl.get("pois", []):
		var tgt := Vector3(poi.pos[0], poi.pos[1], poi.pos[2])
		var r := await walk_path(tgt, float(poi.radius) + 4.0, 150.0)
		print("DK POI %s / %s: nopath=%s reached=%s t=%.0fs resets=%d gaps=%d miny=%.1f" % [k, poi.name, r.get("nopath", false), r.ok, r.t, r.resets, r.gaps, r.minh])
		ok(r.ok and r.resets == 0 and r.gaps == 0 and r.minh > 0.0, "%s: walked to %s (%.0f s, resets %d, gaps %d)" % [k, poi.name, r.t, r.resets, r.gaps])
		var back := await walk_path(sea.pier_head(d), 6.0, 150.0)
		ok(back.ok and back.resets == 0 and back.gaps == 0, "%s: walked back from %s to the pier (%.0f s, resets %d, gaps %d)" % [k, poi.name, back.t, back.resets, back.gaps])
		if not back.ok: m.hero.global_position = sea.to_global(sea.pier_head(d) + Vector3(0, 0.6, 0)); await frames(3)
	m.hero.global_position = sea.to_global(sea.pier_head(d) + Vector3(0, 0.6, 0)); m.hero.velocity = Vector3.ZERO; await frames(10)
	sea.unseat_crew()
func cam_probe(t: String) -> void:
	await frames(25)
	var c: Vector3 = m.cam.global_position; var h: Vector3 = m.hero.global_position + Vector3(0, 1.2, 0)
	print("CP %s cam=%s hero=%s arm=%.2f floor_under_cam=%s" % [t, c, h, m.cam_arm.get_hit_length(), sea.floor_y(c)])
	for id in RenderingServer.instances_cull_ray(h, c + (c - h).normalized() * 0.5, m.get_world_3d().scenario):
		var o = instance_from_id(id)
		if o is GeometryInstance3D: print("CP   ", o.get_path(), " aabb=", o.get_aabb().size)
	for id in RenderingServer.instances_cull_ray(h + Vector3(2, 0, 2), h + Vector3(2, -6, 2), m.get_world_3d().scenario):
		var o = instance_from_id(id)
		if o is MeshInstance3D and o.mesh:
			var mats := []
			for si in o.mesh.get_surface_count():
				var mm = o.get_active_material(si)
				mats.append(str(mm.shader.resource_path if mm is ShaderMaterial else (mm.resource_path if mm else "none")) + ("/" + str(mm.get("transparency")) if mm else ""))
			print("CPdown ", o.get_path(), " ovr=", o.material_override, " ", mats)
	for id in RenderingServer.instances_cull_aabb(AABB(c - Vector3.ONE * 0.5, Vector3.ONE), m.get_world_3d().scenario):
		var o = instance_from_id(id)
		if o is GeometryInstance3D: print("CPin ", o.get_path(), " aabb=", o.get_aabb().size)
func pix_probe(t: String) -> void:
	var vs: Vector2 = get_viewport().get_visible_rect().size
	for px in [Vector2(960, 300), Vector2(990, 420), Vector2(300, 520), Vector2(700, 500)]:
		var p: Vector2 = px * vs / Vector2(1024, 576)
		var o: Vector3 = m.cam.project_ray_origin(p); var dv: Vector3 = m.cam.project_ray_normal(p)
		var best := ""
		for id in RenderingServer.instances_cull_ray(o, o + dv * 30.0, m.get_world_3d().scenario):
			var g = instance_from_id(id)
			if g is GeometryInstance3D: best += " " + str(g.get_path()).get_slice("/", 4) + "/" + g.name + str(g.get_aabb().size.round())
		print("PX %s %s:%s" % [t, px, best])
func dark_pct() -> float:
	await frames(3); var img := get_viewport().get_texture().get_image(); var dark := 0; var tot := 0
	for y in range(0, img.get_height(), 8):
		for x in range(0, img.get_width(), 8):
			tot += 1
			if img.get_pixel(x, y).get_luminance() < 0.05: dark += 1
	return 100.0 * dark / tot
func hide_probe(t: String) -> void:
	await frames(20); var base := await dark_pct(); print("HP %s base %.1f" % [t, base])
	var cands: Array = []
	for mi in sea.find_children("*", "GeometryInstance3D", true, false): cands.append(mi)
	for mi in m.find_children("*", "GeometryInstance3D", true, false):
		if not sea.is_ancestor_of(mi) and (mi as Node3D).is_visible_in_tree() and (mi as Node3D).global_position.distance_to(m.hero.global_position) < 60: cands.append(mi)
	var groups := {}
	for mi in cands:
		if not mi.is_visible_in_tree(): continue
		var key = mi.mesh if mi is MeshInstance3D and mi.mesh else mi
		if not groups.has(key): groups[key] = []
		groups[key].append(mi)
	for key in groups:
		for mi in groups[key]: mi.visible = false
		var d := await dark_pct()
		for mi in groups[key]: mi.visible = true
		if absf(d - base) > 2.0: print("HP   ", groups[key][0].get_path(), " x", groups[key].size(), " -> %.1f" % d)
	m.sun.visible = false; print("HP no sun %.1f" % await dark_pct()); m.sun.visible = true
	m.sun.shadow_enabled = false; print("HP no shadow %.1f" % await dark_pct()); m.sun.shadow_enabled = true
func fade_wait() -> void:
	await get_tree().create_timer(1.4).timeout; await frames(3)
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(out)
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0); m.party.set_hero("aldric"); m.party._set_companions(["garruk", "wren"])
	sea = m.sea; sea.save.discovered_ports = ["tidewrack"]
	sea.enter("galleon"); sea.unlock_all = true; await frames(5)
	var L: Dictionary = sea._landings()
	ok(L.size() >= 13, "landings.json has %d landing points" % L.size())
	var shots := ["gullhaven", "lantern_rock", "saltglass", "frostreach", "vent", "aurora_arch", "hot_spring"]
	var only := OS.get_environment("DK_ONLY")
	for k in L:
		if only != "" and not (k in only.split(",")): continue
		var d: Dictionary = L[k]; var moor := sea._v3(d.moor)
		sea.cur_region = d.region; sea.ship.position = moor - sea._inland(d) * 20.0; sea.ship.speed = 0.0; sea.ship.alt = 0.0
		for i in 3000:
			if sea._region_ready(d.region): break
			await get_tree().process_frame
		await frames(10)
		sea.ship.position = moor - sea._inland(d) * 15.0; sea.ship.speed = 0.0; await frames(3)
		ok(sea.ui.prompt.visible and sea.ui.prompt.text == "Go ashore", "%s: Go ashore prompt near the moor (got '%s')" % [k, sea.ui.prompt.text])
		sea.go_ashore(k); await fade_wait()
		ok(sea.ashore == k, "%s: ashore" % k)
		ok(sea.ship.position.distance_to(Vector3(moor.x, 0, moor.z)) < 0.5 and absf(sea.ship.rotation.x) < 0.001 and absf(sea.ship.rotation.z) < 0.001 and sea.ship.position.y == 0.0, "%s: ship parked level at the moor" % k)
		var hp := sea.to_local(m.hero.global_position)
		ok(hp.distance_to(sea.pier_head(d)) < 2.5, "%s: hero on the pier head (%.1f m)" % [k, hp.distance_to(sea.pier_head(d))])
		ok(m.pip.global_position.distance_to(m.hero.global_position) < 4.0 and not m.party.riding, "%s: Pip + companions ashore with the hero" % k)
		feet_check(k, "after disembark")
		await hud_check(k + " ashore")
		ok(sea.ui.charts_b.visible, "%s: Charts shown at the pier beside the ship" % k)
		if OS.get_environment("DK_POI") != "": await poi_walk(k, d)
		var inl := sea._inland(d)
		m.yaw = atan2(inl.x, inl.z)   # camera looks inland: fwd = (-sin, -cos) = -inl, so the shot frames hero + pier + ship behind
		if OS.get_environment("DK_CAMPROBE") != "": await cam_probe(k + " ashore")
		if OS.get_environment("DK_HIDEPROBE") != "": m.yaw = atan2(inl.x, inl.z); await hide_probe(k)
		if k in shots: await shot(k + "_ashore")
		if OS.get_environment("DK_CAMPROBE") != "": pix_probe(k)
		var start := sea.to_local(m.hero.global_position); var minh := 1e9; var resets := 0
		var fw := Vector3(-sin(m.yaw), 0, -cos(m.yaw))
		var iy := -1.0 if fw.dot(inl) > 0 else 1.0
		for i in 900:
			sea.drive(Vector2(0, iy), 1.0 / 60.0)
			var lp := sea.to_local(m.hero.global_position); minh = minf(minh, lp.y)
			if sea.ui.msg.text.begins_with("Careful"): resets += 1; sea.ui.msg.text = ""
			if Vector2(lp.x - start.x, lp.z - start.z).length() >= 20.0: break
			await get_tree().physics_frame
		var endp := sea.to_local(m.hero.global_position)
		var dist := Vector2(endp.x - start.x, endp.z - start.z).length()
		if dist < 20.0:
			var w: Vector3 = m.hero.global_position + Vector3(0, 0.5, 0); var q := PhysicsRayQueryParameters3D.create(w, w + fw * 3.0, 1); q.exclude = [m.hero.get_rid()]
			var hh: Dictionary = m.get_world_3d().direct_space_state.intersect_ray(q)
			print("DK BLOCK %s at %s by %s n=%s" % [k, str(endp), str(hh.get("collider", null).get_parent().name if hh else "none"), str(hh.get("normal", ""))])
		ok(dist >= 20.0 and minh > 0.0 and resets == 0, "%s: walked %.1f m inland on foot (min y %.2f, resets %d)" % [k, dist, minh, resets])
		await frames(30)
		var c0: Vector3 = m.party.companions[0].node.global_position if m.party.companions.size() > 0 else m.pip.global_position
		ok(c0.distance_to(m.hero.global_position) < 8.0, "%s: companion followed ashore (%.1f m)" % [k, c0.distance_to(m.hero.global_position)])
		feet_check(k, "20 m inland")
		ok(not sea.ui.charts_b.visible, "%s: Charts hidden 20 m inland, away from the ship" % k)
		await hud_check(k + " inland")
		if k in shots:
			m.yaw = atan2(-inl.x, -inl.z); await shot(k + "_inland")
		m.hero.global_position = sea.to_global(sea.pier_head(d) + Vector3(0, 0.6, 0)); await frames(4); sea.drive(Vector2.ZERO, 1.0 / 60.0)
		ok(sea.ui.prompt.text == "Board ship", "%s: Board ship prompt at the pier" % k)
		sea.board_ship(); await fade_wait()
		for i in 3: sea.drive(Vector2.ZERO, 1.0 / 60.0)
		var deck: Vector3 = m.hero.global_position - sea.ship.global_position
		ok(sea.ashore == "" and deck.length() < 6.0 and deck.y > 1.0 and m.party.riding, "%s: re-boarded at the same spot, crew on deck" % k)
	var wm = m.world_map
	var lw := Vector2(L.coil_isle.shore[0], L.coil_isle.shore[2])
	ok(wm.revealed(lw), "map: visited landing (Coil Isle) revealed on the fogged map")
	ok(not wm.revealed(Vector2(-2900, -2900)), "map: unvisited corner stays fogged")
	sea.cur_region = "A"; sea.ship.position = Vector3(1300, 0, 300); sea.ship.speed = 0.0; await frames(3); sea._contexts()
	ok(sea.ui.prompt.text == "Go ashore", "mainland Tidewrack pier: Go ashore prompt at the bay mouth")
	sea.ui._cb.call(); await fade_wait()
	ok(not sea.active and m.hero.global_position.distance_to(m._galleon_pier()[0]) < 3.0, "mainland: ashore on the Tidewrack pier beside the galleon")
	await frames(5)
	ok(sea.ui.prompt.text == "Set sail", "mainland: Set sail again from the same pier")
	await shot("mainland_pier")
	print("DK DONE pass=%d fail=%d" % [npass, nfail]); get_tree().quit(0 if nfail == 0 else 1)
