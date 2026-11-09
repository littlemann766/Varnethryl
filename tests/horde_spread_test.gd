extends SceneTree
## Boot placement: small groups on dry land, not a gate horde. Headless. Not a phone result.
## godot --headless --path . -s res://tests/horde_spread_test.gd
var fails := 0
var n := 0

func ok(c: bool, msg: String) -> void:
	n += 1
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1

func _initialize() -> void: _run.call_deferred()

func _run() -> void:
	OS.set_environment("VARN_LITE", "1")
	OS.set_environment("VARN_NO_FLOWERS", "1")
	OS.set_environment("VARN_NO_HORDE_REFILL", "1")
	await process_frame
	var m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for _i in 8: await physics_frame
	var crowd: HordeCrowd = m.horde.crowd
	var pts: Array[Vector2] = []
	var holds: Array[Vector2] = []
	var idxs: Array[int] = []
	var sea := 0
	var inside := 0
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0: continue
		var p := Vector2(crowd.px[i], crowd.pz[i])
		pts.append(p)
		holds.append(Vector2(crowd.hold_x[i], crowd.hold_z[i]))
		idxs.append(i)
		if crowd.on_sea(p.x, p.y): sea += 1
		if TownHaven.body_inside(p, HordeZombie.BODY_R): inside += 1
	ok(pts.size() == HordeCrowd.SIM_DEFAULT, "boot count is the field of %d (%d)" % [HordeCrowd.SIM_DEFAULT, pts.size()])
	ok(sea == 0, "no record starts in the sea (%d)" % sea)
	ok(inside == 0, "no record starts in the haven (%d)" % inside)
	ok(crowd.wedge_count() == 0, "the escape wedge is empty at boot")
	var parent: Array[int] = []
	parent.resize(pts.size())
	for i in pts.size(): parent[i] = i
	for a in pts.size():
		for b in range(a + 1, pts.size()):
			if pts[a].distance_to(pts[b]) > 12.0: continue
			_join(parent, a, b)
	var sizes := {}
	for i in pts.size():
		var r := _find(parent, i)
		sizes[r] = int(sizes.get(r, 0)) + 1
	var max_c := 0
	var over := 0
	var centroids: Array[Vector2] = []
	var counts: Array[int] = []
	for key in sizes:
		var sz: int = int(sizes[key])
		max_c = maxi(max_c, sz)
		if sz > HordeCrowd.GROUP_MAX: over += 1
		var acc := Vector2.ZERO
		var nsum := 0
		for i in pts.size():
			if _find(parent, i) != int(key): continue
			acc += pts[i]
			nsum += 1
		centroids.append(acc / float(nsum))
		counts.append(sz)
	var gap := 100000.0
	for a in centroids.size():
		for b in range(a + 1, centroids.size()):
			gap = minf(gap, centroids[a].distance_to(centroids[b]))
	var nn_sum := 0.0
	var nn_n := 0
	for a in pts.size():
		var best := 100000.0
		for b in pts.size():
			if a == b: continue
			best = minf(best, pts[a].distance_to(pts[b]))
		nn_sum += best
		nn_n += 1
	var nn_mean := nn_sum / float(maxi(nn_n, 1))
	var sectors := [0, 0, 0, 0, 0, 0, 0, 0]
	var far_n := 0
	var mid_n := 0
	for p in pts:
		var ang := atan2(p.x, p.y)
		if ang < 0.0: ang += TAU
		sectors[mini(7, int(ang / TAU * 8.0))] += 1
		if p.length() > 250.0: mid_n += 1
		if p.length() > 450.0: far_n += 1
	var filled := 0
	for s in sectors:
		if s >= 15: filled += 1
	print("SPREAD groups=%d max_cluster=%d over=%d centroid_gap=%.1f nn_mean=%.2f sectors=%s mid=%d far=%d" % [centroids.size(), max_c, over, gap, nn_mean, sectors, mid_n, far_n])
	ok(over == 0 and max_c <= HordeCrowd.GROUP_MAX and max_c >= 1, "clusters are loose groups of 1 to %d (max %d)" % [HordeCrowd.GROUP_MAX, max_c])
	ok(centroids.size() >= 150, "the field is many groups, not one horde (%d)" % centroids.size())
	ok(gap >= HordeCrowd.GROUP_GAP * 0.75, "group centers keep a real gap (%.1f m)" % gap)
	ok(nn_mean < 8.0, "group mates stand near each other (mean nearest %.2f m)" % nn_mean)
	ok(filled >= 5, "groups cover the playable land (%d of 8 sectors have 15 or more)" % filled)
	ok(mid_n >= 200 and far_n >= 40, "groups reach past the town apron (beyond 250 m: %d, beyond 450 m: %d)" % [mid_n, far_n])
	var watch := idxs[0]
	var home := holds[0]
	var start := pts[0]
	var need := TownHaven.outer_limit() + HordeCrowd.FIELD_MIN + HordeCrowd.WANDER_R + 6.0
	for k in idxs.size():
		if holds[k].length() > need and holds[k].length() < 500.0:
			watch = idxs[k]
			home = holds[k]
			start = pts[k]
			break
	m.hero.global_position = Vector3(0, 1, 20)
	for _i in 90: await physics_frame
	var after := Vector2(crowd.px[watch], crowd.pz[watch])
	var wandered := after.distance_to(start)
	var from_home := after.distance_to(home)
	print("WANDER moved %.2f home %.2f" % [wandered, from_home])
	ok(wandered > 0.2 and from_home <= HordeCrowd.WANDER_R + 2.5, "a zombie drifts inside its own area (moved %.2f, home %.2f)" % [wandered, from_home])
	var far_i := watch
	var far_d := 0.0
	for k in idxs.size():
		var d := Vector2(crowd.px[idxs[k]], crowd.pz[idxs[k]]).distance_to(after)
		if d > far_d:
			far_d = d
			far_i = idxs[k]
	var far_home := Vector2(crowd.hold_x[far_i], crowd.hold_z[far_i])
	m.hero.global_position = Vector3(after.x, 1.0, after.y + 2.0)
	var before_close := after.distance_to(Vector2(m.hero.global_position.x, m.hero.global_position.z))
	for _i in 70: await physics_frame
	var closed := Vector2(crowd.px[watch], crowd.pz[watch]).distance_to(Vector2(m.hero.global_position.x, m.hero.global_position.z))
	var far_stay := Vector2(crowd.px[far_i], crowd.pz[far_i]).distance_to(far_home)
	print("NOTICE close %.2f -> %.2f far_home %.2f" % [before_close, closed, far_stay])
	ok(closed < before_close - 0.3, "the nearby zombie comes toward the player (%.2f -> %.2f)" % [before_close, closed])
	ok(far_stay <= HordeCrowd.WANDER_R + 3.0, "a far group does not join that chase (%.2f m from home)" % far_stay)
	ok(crowd.inside_count() == 0 and crowd.wedge_count() == 0, "wandering still stays out of the haven and the wedge")
	print("HORDE_SPREAD %d checks, %d failed" % [n, fails])
	quit(1 if fails else 0)

func _find(parent: Array[int], i: int) -> int:
	var p := i
	while parent[p] != p:
		parent[p] = parent[parent[p]]
		p = parent[p]
	return p

func _join(parent: Array[int], a: int, b: int) -> void:
	var ra := _find(parent, a)
	var rb := _find(parent, b)
	if ra != rb: parent[rb] = ra
