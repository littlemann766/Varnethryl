extends Node
## test 24 (boss: "the crystals are hard to get to"). The only crystals in the world are the Ashen Titan's weak points
## (6 body + 2 ankle; no harvestable crystal nodes exist on master). Players fight them where he stops: his stations.
## Bakes an outskirts navmesh (terrain heightfield, 42 deg slope / 0.5 m climb, hero capsule r 0.45; boulder colliders,
## tree/rock blockers, sea and lake carved out as obstructions) and asserts every station is reachable on foot from the
## South Gate, lands on the navmesh within MELEE reach of his feet, is within 25 m of a road, and not on a cliff.
## Run: VARN_LITE=1 godot --headless --path . -- --crystalcheck    (writes /workspace/shots/godot24/crystals_map.png)
var m: Node
const EXT := 760.0
const STEP := 4.0
const NEAR_ROAD := 25.0
const REACH := 10.0   # hero must get within 10 m of the station (ankle crystals melee 12 m)
func _ready() -> void:
	m = get_parent(); _run.call_deferred()
	get_tree().create_timer(600.0).timeout.connect(func(): print("CRYSTALCHECK timeout"); get_tree().quit(2))
func _run() -> void:
	for i in 5: await get_tree().physics_frame
	var wb: WorldBoss = m.world_boss
	if wb == null: m.spawn_world_boss(false); wb = m.world_boss
	var nm := NavigationMesh.new(); nm.agent_radius = 0.45; nm.agent_height = 1.9; nm.agent_max_climb = 0.5; nm.agent_max_slope = 42.0
	nm.cell_size = 1.0; nm.cell_height = 0.25; nm.region_min_size = 4.0
	nm.filter_baking_aabb = AABB(Vector3(-EXT, -60, -EXT), Vector3(EXT * 2, 400, EXT * 2))
	var src := NavigationMeshSourceGeometryData3D.new()
	var N := int(EXT * 2 / STEP); var verts := PackedVector3Array()
	var hgt := func(x: float, z: float) -> float: return float(m.height(x, z))
	for iz in N:
		for ix in N:
			var x0 := -EXT + ix * STEP; var z0 := -EXT + iz * STEP; var x1 := x0 + STEP; var z1 := z0 + STEP
			var a := Vector3(x0, hgt.call(x0, z0), z0); var b := Vector3(x1, hgt.call(x1, z0), z0)
			var c := Vector3(x1, hgt.call(x1, z1), z1); var d := Vector3(x0, hgt.call(x0, z1), z1)
			verts.append_array([a, b, c, a, c, d])
	src.add_faces(verts, Transform3D())
	var obs := [0]
	var circle := func(c2: Vector2, r: float) -> void:
		var pts := PackedVector3Array()
		for k in 10: pts.append(Vector3(c2.x + cos(k * TAU / 10) * r, 0, c2.y + sin(k * TAU / 10) * r))
		src.add_projected_obstruction(pts, -100.0, 400.0, true); obs[0] += 1
	var bc: Node = TerrainScatter.root.get_node_or_null("BoulderCollision") if TerrainScatter.root else null
	if bc: for cs in bc.get_children():
		if cs.is_queued_for_deletion(): continue
		var p: Vector3 = (cs as Node3D).global_position; circle.call(Vector2(p.x, p.z), (cs.shape as CylinderShape3D).radius if cs.shape is CylinderShape3D else 1.0)
	for b in m.blockers: if (b[0] as Vector2).length() > 200.0: circle.call(b[0], b[1])
	circle.call(m.LAKE, 95.0)
	src.add_projected_obstruction(PackedVector3Array([Vector3(-2000, 0, -2000), Vector3(m.SEA_COAST_X, 0, -2000), Vector3(m.SEA_COAST_X, 0, 2000), Vector3(-2000, 0, 2000)]), -100, 400, true)
	var t0 := Time.get_ticks_msec()
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	print("CRYSTALCHECK navmesh polys=%d obstructions=%d bake=%d ms" % [nm.get_polygon_count(), obs[0], Time.get_ticks_msec() - t0])
	var map := NavigationServer3D.map_create(); NavigationServer3D.map_set_cell_size(map, 1.0); NavigationServer3D.map_set_cell_height(map, 0.25); NavigationServer3D.map_set_active(map, true)
	var reg := NavigationServer3D.region_create(); NavigationServer3D.region_set_map(reg, map); NavigationServer3D.region_set_navigation_mesh(reg, nm)
	for i in 300:
		await get_tree().physics_frame
		NavigationServer3D.map_force_update(map)
		if NavigationServer3D.map_get_iteration_id(map) > 0 and NavigationServer3D.map_get_closest_point(map, Vector3(0, 0, 205)).distance_to(Vector3(0, 0, 205)) < 3.0: break
	var gate := NavigationServer3D.map_get_closest_point(map, Vector3(0, 0, 205))
	var lines := []; var fails := 0
	var res_new := _eval(wb.waypoints, wb.stations, map, gate, lines, "new"); var res_old := _eval(wb.waypoints_old, wb.stations_old, map, gate, [], "old")
	for r in res_new: if not r[1]: fails += 1
	var n_old_ok := res_old.filter(func(r): return r[1]).size()
	lines.append("CRYSTALCHECK stations old=%d (reachable+near road %d) new=%d (ok %d) -> %s" % [res_old.size(), n_old_ok, res_new.size(), res_new.size() - fails, "PASS" if fails == 0 else "FAIL"])
	print("\n".join(lines))
	_map_png(wb, res_old, res_new)
	DirAccess.make_dir_recursive_absolute("/workspace/shots/godot24")
	FileAccess.open("/workspace/shots/godot24/crystal_check.txt", FileAccess.WRITE).store_string("\n".join(lines) + "\n")
	get_tree().quit(0 if fails == 0 else 1)
func _eval(wps: Array[Vector3], idx: Array, map: RID, gate: Vector3, lines: Array, tag: String) -> Array:
	var out := []
	for i in idx:
		var w: Vector3 = wps[i]; var p2 := Vector2(w.x, w.z)
		var y := float(m.height(w.x, w.z)); var tgt := Vector3(w.x, y, w.z)
		var c := NavigationServer3D.map_get_closest_point(map, tgt)
		var path := NavigationServer3D.map_get_path(map, gate, c, true)
		var reach := path.size() > 0 and path[path.size() - 1].distance_to(c) < 1.0 and Vector2(c.x, c.z).distance_to(p2) < REACH
		var rd := float(m._road_dist(p2))
		var slope := 0.0
		for o in [Vector2(3, 0), Vector2(0, 3)]: slope = maxf(slope, rad_to_deg(atan(absf(float(m.height(w.x + o.x, w.z + o.y)) - y) / 3.0)))
		var ok := reach and rd <= NEAR_ROAD and slope < 35.0
		var plen := 0.0
		for k in range(1, path.size()): plen += path[k].distance_to(path[k - 1])
		lines.append("%s station wp %2d at (%.0f, %.0f): road %.0f m, slope %.0f deg, nav gap %.1f m, walk %.0f m -> %s" % [tag, i, w.x, w.z, rd, slope, Vector2(c.x, c.z).distance_to(p2), plen, "ok" if ok else "FAIL"])
		out.append([p2, ok])
	return out
func _map_png(wb: WorldBoss, old: Array, nw: Array) -> void:
	var S := 900; var img := Image.create(S * 2, S, false, Image.FORMAT_RGB8)
	var f := func(v: Vector2, ox: int) -> Vector2i: return Vector2i(ox + int((v.x + EXT) / (2 * EXT) * S), int((v.y + EXT) / (2 * EXT) * S))
	for panel in 2:
		var ox := panel * S
		for y in S: for x in S:
			var wx := -EXT + (x + 0.5) / S * 2 * EXT; var wz := -EXT + (y + 0.5) / S * 2 * EXT
			var h := float(m.height(wx, wz)); var g := clampf(0.25 + h / 160.0, 0.1, 0.9)
			var col := Color(g * 0.8, g, g * 0.7)
			if wx < m.SEA_COAST_X or Vector2(wx, wz).distance_to(m.LAKE) < 95.0: col = Color(0.15, 0.3, 0.55)
			if maxf(absf(wx), absf(wz)) < 185.0: col = Color(0.45, 0.35, 0.3)
			img.set_pixel(ox + x, y, col)
		for r in m.ROADS:
			for i in range(1, r.size()):
				var a := Vector2(r[i-1][0], r[i-1][1]); var b := Vector2(r[i][0], r[i][1])
				for k in 200: var q: Vector2i = f.call(a.lerp(b, k / 200.0), ox); if q.x >= ox and q.x < ox + S and q.y >= 0 and q.y < S: img.set_pixelv(q, Color(0.85, 0.75, 0.5))
		var wps: Array[Vector3] = wb.waypoints_old if panel == 0 else wb.waypoints
		for i in wps.size():
			var a := Vector2(wps[i].x, wps[i].z); var b := Vector2(wps[(i + 1) % wps.size()].x, wps[(i + 1) % wps.size()].z)
			for k in 60: var q: Vector2i = f.call(a.lerp(b, k / 60.0), ox); img.set_pixelv(q, Color(1, 0.5, 0.1))
		for r in (old if panel == 0 else nw):
			var q: Vector2i = f.call(r[0], ox); var c := Color(0.2, 1, 0.3) if r[1] else Color(1, 0, 0.1)
			for dx in range(-6, 7): for dy in range(-6, 7):
				if dx * dx + dy * dy <= 36: img.set_pixel(clampi(q.x + dx, ox, ox + S - 1), clampi(q.y + dy, 0, S - 1), c)
	for y in S: img.set_pixel(S, y, Color.WHITE)
	DirAccess.make_dir_recursive_absolute("/workspace/shots/godot24"); img.save_png("/workspace/shots/godot24/crystals_map.png")
