extends SceneTree
## Town layout (test 11, boss: buildings on roads / walkways through walls). In the real main scene:
##  1. no building footprint (Beth's collision AABB U visual AABB, + 1 m) touches a street, the plaza or a gate road
##  2. no two buildings overlap
##  3. walls and the 4 gates stay clear (footprint inside +-175 m, outside the gate corridors)
##  4. every front door has a spur path that starts at the door, ends on a street, and crosses no other building;
##     a path only touches its own building on the door side (the front face)
##  5. both farmstead doors exist (house -> farmhouse interior, barn doors -> barn interior)
## godot --headless -s res://tests/layout_test.gd
func _initialize() -> void: _run.call_deferred()
var fails := 0
func ok(c: bool, m: String) -> void:
	if not c: print("FAIL " + m); fails += 1

func _run() -> void:
	var M = load("res://scripts/main.gd")
	var m = load("res://main.tscn").instantiate(); root.add_child(m)
	for i in 10: await process_frame
	var n := 0
	for b in m.buildings:
		n += 1
		var r: Rect2 = b.rect
		var g := r.grow(1.0)
		if maxf(absf(r.get_center().x), absf(r.get_center().y)) > M.CITY_HALF:   # test 14: the farmstead lives outside the walls now
			ok(r.position.x > M.CITY_HALF + 20 or r.end.x < -M.CITY_HALF - 20 or r.position.y > M.CITY_HALF + 20 or r.end.y < -M.CITY_HALF - 20, "%s outside building hugs the wall" % b.id)
			var lo := INF; var hi := -INF
			for c in [r.position, r.end, Vector2(r.position.x, r.end.y), Vector2(r.end.x, r.position.y)]: var hy: float = m.height(c.x, c.y); lo = minf(lo, hy); hi = maxf(hi, hy)
			ok(hi - lo < 0.3 and absf(b.node.global_position.y - lo) < 0.4, "%s not snapped to a level pad (corners %.2f..%.2f, base %.2f)" % [b.id, lo, hi, b.node.global_position.y])
			for rd in M.ROADS:
				for i in range(1, rd.size()):
					ok(not _seg_hits_rect(Vector2(rd[i-1][0], rd[i-1][1]), Vector2(rd[i][0], rd[i][1]), r.grow(1.0)), "%s on outer road" % b.id)
			continue
		# 1. streets: sample the grown rect's area on a 0.5 m grid against the street edge distance
		var hit := false
		var x := g.position.x
		while x <= g.end.x and not hit:
			var z := g.position.y
			while z <= g.end.y:
				if M.street_edge_dist(Vector2(x, z)) < 0.0: hit = true; break
				z += 0.5
			x += 0.5
		ok(not hit, "%s footprint %s (+1 m) touches a street" % [b.id, r])
		for rd in M.ROADS:
			for i in range(1, rd.size()):
				var a := Vector2(rd[i-1][0], rd[i-1][1]); var c := Vector2(rd[i][0], rd[i][1])
				var cp := Geometry2D.get_closest_point_to_segment(r.get_center(), a, c)
				ok(not g.grow(4.4).has_point(cp) or not _seg_hits_rect(a, c, g.grow(4.4)), "%s on outer road" % b.id)
		# 3. walls/gates
		ok(absf(r.position.x) <= 175 and absf(r.end.x) <= 175 and absf(r.position.y) <= 175 and absf(r.end.y) <= 175, "%s too close to the wall %s" % [b.id, r])
		for gp in [Vector2(0, 185), Vector2(0, -185), Vector2(185, 0), Vector2(-185, 0)]:
			ok(r.get_center().distance_to(gp) > 30.0, "%s blocks a gate" % b.id)
		# 2. overlaps
		for o in m.buildings:
			if o.id < b.id: ok(not r.intersects(o.rect), "%s overlaps %s" % [b.id, o.id])
	ok(n >= 24, "building count %d" % n)
	# 4. spurs
	var doors := 0
	for sp in m.spurs:
		doors += 1
		var b: Dictionary = {}
		for x in m.buildings: if x.id == sp[3]: b = x
		var outside: bool = maxf(absf(b.node.global_position.x), absf(b.node.global_position.z)) > M.CITY_HALF
		if outside: ok(m._road_dist(sp[1]) < 2.0, "%s door path does not reach its dirt road (%s)" % [sp[3], sp[1]])
		else: ok(M.street_edge_dist(sp[1]) < 0.0, "%s door spur does not reach a street (end %s, %.2f)" % [sp[3], sp[1], M.street_edge_dist(sp[1])])
		var lp: Vector3 = b.node.global_transform.affine_inverse() * Vector3(sp[0].x, 0, sp[0].y)
		ok(lp.z > 0.0, "%s spur does not start on the front (door) side" % sp[3])
		for o in m.buildings:
			if o.id == sp[3]: continue
			ok(not _seg_hits_rect(sp[0], sp[1], (o.rect as Rect2).grow(sp[2])), "%s spur crosses %s" % [sp[3], o.id])
		# own building: from the door outward the spur must leave the footprint through the front face only
		var out: Vector2 = sp[1] - sp[0]
		var fwd: Vector3 = b.node.global_transform.basis * Vector3(0, 0, 1)
		ok(out.normalized().dot(Vector2(fwd.x, fwd.z)) > 0.99, "%s spur not leaving through the door side" % sp[3])
	print("doors with spurs: %d" % doors)
	# 5. farmstead
	ok(m.extra_doors.size() == 1 and m.extra_doors[0].id == "barn", "barn doors registered on the farmstead")
	var fh := 0
	for b in m.buildings: if b.id == "farmhouse": fh += 1
	for b in m.buildings: ok(b.id != "barn", "separate barn building still placed")
	for b in m.buildings:
		var has := false
		for sp in m.spurs: if sp[3] == b.id: has = true
		ok(has, "%s has no footpath to its door" % b.id)
	ok(fh == 1, "one farmstead")
	# 6. test 14 fillers: data-driven rows, never on a street, a landmark, another filler, or any landmark door path
	var ids := {}
	for f in m.fillers:
		ok(not ids.has(f.id), "filler id %s unique" % f.id); ids[f.id] = true
		var r: Rect2 = f.rect
		ok(r.position.x >= -175 and r.end.x <= 175 and r.position.y >= -175 and r.end.y <= 175, "%s inside the walls" % f.id)
		var hit := false; var x := r.position.x
		while x <= r.end.x and not hit:
			var z := r.position.y
			while z <= r.end.y:
				if M.street_edge_dist(Vector2(x, z)) < 0.0: hit = true; break
				z += 0.5
			x += 0.5
		ok(not hit, "%s on a street" % f.id)
		for b in m.buildings: ok(not r.intersects(b.rect), "%s overlaps %s" % [f.id, b.id])
		for o in m.fillers: if o.id < f.id: ok(not r.intersects(o.rect), "%s overlaps %s" % [f.id, o.id])
		for sp in m.spurs: ok(not _seg_hits_rect(sp[0], sp[1], r), "%s blocks the %s door path" % [f.id, sp[3]])
		ok(M.street_edge_dist(f.path[1]) < 0.0, "%s path reaches a street" % f.id)
		ok(f.node.get_node("Door") is Marker3D, "%s has a door marker" % f.id)
		for b in m.buildings: ok(not _seg_hits_rect(f.path[0], f.path[1], b.rect), "%s path crosses %s" % [f.id, b.id])
	ok(m.fillers.size() >= 60, "town is crowded: %d filler houses/shops" % m.fillers.size())
	print("fillers: %d" % m.fillers.size())
	print("LAYOUT %d buildings, %d failed" % [n, fails])
	quit(1 if fails else 0)

func _seg_hits_rect(a: Vector2, b: Vector2, r: Rect2) -> bool:
	if r.has_point(a) or r.has_point(b): return true
	var c := [r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]
	for i in 4:
		if Geometry2D.segment_intersects_segment(a, b, c[i], c[(i + 1) % 4]) != null: return true
	return false
