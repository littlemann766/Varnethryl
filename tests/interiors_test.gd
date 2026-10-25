extends SceneTree
## Headless walk-through of every interior: for Pip (0.52 m) and Owner (1.905 m) capsules, walk from the door to
## every room on every floor (stairs via navmesh, ladders by pushing into them), back out the door, plus
## "no auto-climb" checks at each stair foot and ladder, and door enter/exit triggers through InteriorManager.
## Run: godot --headless --fixed-fps 60 -s res://tests/interiors_test.gd   [-- only=inn,bakery]
const B := preload("res://interiors/interior_builder.gd")
const DEF := preload("res://interiors/interior_defs.gd")
const HEROES := {"pip": 0.52, "owner": 1.905}
var fails := 0
var passes := 0
var log_lines := []

func ok(c: bool, msg: String) -> void:
	if c: passes += 1; log_lines.append("PASS " + msg)
	else: fails += 1; log_lines.append("FAIL " + msg); print("FAIL: ", msg)

func _initialize() -> void: _run.call_deferred()

func phys(n := 1) -> void:
	for i in n: await physics_frame

func size_of(id: String) -> Vector3:
	var M := {"inn": Vector3(38.8, 21.8, 28.3), "guildhall": Vector3(40.8, 24.1, 32.1), "townhall": Vector3(30.1, 22.7, 26.1),
		"smithy": Vector3(25.5, 18.1, 24.4), "bakery": Vector3(25.6, 17.5, 22.0), "temple": Vector3(26.5, 24.1, 44.5)}
	return M.get(id, Vector3(24, 18, 22))

func make_hero(h: float) -> CharacterBody3D:
	var cb := CharacterBody3D.new(); var cs := CollisionShape3D.new(); var cap := CapsuleShape3D.new()
	cap.radius = clamp(h * 0.17, 0.12, 0.53); cap.height = max(h, cap.radius * 2.0 + 0.01)   # same as heroes/party.gd
	cs.shape = cap; cs.position.y = cap.height / 2; cb.add_child(cs); cb.floor_snap_length = 0.6
	return cb

func step(hero: CharacterBody3D, dir: Vector3, mgr: InteriorManager) -> void:
	# mirrors main.gd _physics_process movement
	dir.y = 0
	if dir.length() > 0.05: dir = dir.normalized()
	hero.velocity.x = dir.x * 4.0; hero.velocity.z = dir.z * 4.0
	hero.velocity.y = -1.0 if hero.is_on_floor() else hero.velocity.y - 20.0 / 60.0
	if mgr and mgr.climb(hero, dir, 1.0 / 60.0): pass
	hero.move_and_slide()
	await physics_frame

func _run() -> void:
	var only: Array = []
	for a in OS.get_cmdline_user_args(): if a.begins_with("only="): only = a.substr(5).split(",")
	for id in DEF.D:
		if only.size() and not only.has(id): continue
		await test_building(id)
	await test_doors()
	print("\n".join(log_lines))
	print("RESULT %d passed, %d failed" % [passes, fails])
	quit(1 if fails else 0)

func test_building(id: String) -> void:
	var info := B.build(id, DEF.D[id], size_of(id))
	root.add_child(info.node)
	var mgr := InteriorManager.new(); root.add_child(mgr); mgr.cur = info
	# navmesh over static colliders
	var nm := NavigationMesh.new(); nm.agent_radius = 0.35; nm.agent_height = 1.95; nm.agent_max_climb = 0.1; nm.agent_max_slope = 42.0
	nm.cell_size = 0.1; nm.cell_height = 0.1; nm.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
	var src := NavigationMeshSourceGeometryData3D.new()
	await phys(2)
	NavigationServer3D.parse_source_geometry_data(nm, src, info.node)
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	var map := NavigationServer3D.map_create(); NavigationServer3D.map_set_cell_size(map, 0.1); NavigationServer3D.map_set_cell_height(map, 0.1)
	NavigationServer3D.map_set_active(map, true)
	var reg := NavigationServer3D.region_create(); NavigationServer3D.region_set_map(reg, map); NavigationServer3D.region_set_navigation_mesh(reg, nm)
	await phys(3); NavigationServer3D.map_force_update(map)
	ok(nm.get_polygon_count() > 0, "%s navmesh baked (%d polys)" % [id, nm.get_polygon_count()])
	for hn in HEROES:
		var hero := make_hero(HEROES[hn]); root.add_child(hero)
		hero.global_position = info.spawn + Vector3(0, 0.1, 0)
		for i in 20: await step(hero, Vector3.ZERO, mgr)
		ok(hero.is_on_floor(), "%s/%s spawns on floor at the door" % [id, hn])
		for r in info.rooms:
			var got: bool = await walk_to(hero, r.pos, map, info, mgr)
			ok(got, "%s/%s reaches %s (floor %d)" % [id, hn, r.name, r.floor])
		var out: bool = await walk_to(hero, Vector3(0, 0, info.exit_z + 0.6), map, info, mgr)
		ok(out, "%s/%s walks back out the door" % [id, hn])
		# stairs never pull: stand at each stair foot idle for 2 s
		for s in info.stairs:
			hero.global_position = s.base - s.dir * 0.6 + Vector3(0, 0.1, 0); hero.velocity = Vector3.ZERO
			for i in 30: await step(hero, Vector3.ZERO, mgr)
			var y0 := hero.global_position.y
			for i in 120: await step(hero, Vector3.ZERO, mgr)
			ok(absf(hero.global_position.y - y0) < 0.05, "%s/%s idle at stair foot stays put (dy %.3f)" % [id, hn, hero.global_position.y - y0])
		for l in info.ladders:
			hero.global_position = l.pos - l.dir * 0.5 + Vector3(0, 0.1, 0); hero.velocity = Vector3.ZERO
			for i in 30: await step(hero, Vector3.ZERO, mgr)
			var y1 := hero.global_position.y
			for i in 120: await step(hero, Vector3.ZERO, mgr)
			ok(absf(hero.global_position.y - y1) < 0.05, "%s/%s idle at ladder foot stays put" % [id, hn])
		hero.queue_free(); await phys(2)
	NavigationServer3D.free_rid(reg); NavigationServer3D.free_rid(map)
	mgr.queue_free(); info.node.queue_free(); await phys(2)

func walk_to(hero: CharacterBody3D, target: Vector3, map: RID, info: Dictionary, mgr: InteriorManager) -> bool:
	for attempt in 3:
		var path := NavigationServer3D.map_get_path(map, hero.global_position, target, true)
		var reach := path.size() > 0 and Vector2(path[-1].x - target.x, path[-1].z - target.z).length() < 1.0 and absf(path[-1].y - target.y) < 0.8
		if not reach and info.ladders.size() > 0:
			# take the nearest ladder in the needed direction
			var l: Dictionary = info.ladders[0]
			var up: bool = target.y > hero.global_position.y + 1.0
			var foot: Vector3 = (l.pos - l.dir * 0.5) if up else (l.pos + l.dir * 0.5 + Vector3(0, l.top - l.pos.y, 0))
			if not await follow(hero, NavigationServer3D.map_get_path(map, hero.global_position, foot, true), mgr): return false
			for i in 300:
				await step(hero, l.dir if up else -l.dir, mgr)
				if up and hero.global_position.y > l.top - 0.1 and Vector2(hero.global_position.x - l.pos.x, hero.global_position.z - l.pos.z).dot(Vector2(l.dir.x, l.dir.z)) > 0.6: break
				if not up and hero.is_on_floor() and hero.global_position.y < l.pos.y + 0.2: break
			continue
		if await follow(hero, path, mgr):
			var hp := hero.global_position
			if Vector2(hp.x - target.x, hp.z - target.z).length() < 1.0 and absf(hp.y - target.y) < 0.8: return true
	return false

func follow(hero: CharacterBody3D, path: PackedVector3Array, mgr: InteriorManager) -> bool:
	for p in path:
		var t := 0
		while Vector2(hero.global_position.x - p.x, hero.global_position.z - p.z).length() > 0.25:
			var d := p - hero.global_position
			await step(hero, d, mgr)
			t += 1
			if t > 60 * 12:
				print("STUCK at ", hero.global_position, " wp ", p, " floor ", hero.is_on_floor(), " wall ", hero.is_on_wall())
				return false
	return true

func test_doors() -> void:
	# door triggers through InteriorManager with a stub main (one building per def)
	var stub_src := GDScript.new()
	stub_src.source_code = "extends Node3D\nvar hero\nvar buildings := []\nvar sun\nvar yaw := 0.0\nvar party = null\nfunc height(_x, _z): return 0.0\n"
	stub_src.reload()
	var m: Node3D = stub_src.new(); root.add_child(m)
	m.sun = DirectionalLight3D.new(); m.add_child(m.sun)
	var hero := make_hero(1.905); m.add_child(hero); m.hero = hero
	var mgr := InteriorManager.new(); m.add_child(mgr); mgr.setup(m)
	var i := 0
	for id in DEF.D:
		var n := Node3D.new(); n.position = Vector3(i * 60, 0, 0); n.rotation.y = [0.0, PI / 2, -PI / 2, PI][i % 4]; m.add_child(n)
		var sz := size_of(id)
		m.buildings.append({"id": id, "node": n, "aabb": AABB(Vector3(-sz.x / 2, 0, -sz.z / 2), sz), "name": id})
		i += 1
	var gfloor := StaticBody3D.new(); var gcs := CollisionShape3D.new(); var gb := BoxShape3D.new(); gb.size = Vector3(2000, 1, 2000); gcs.shape = gb; gcs.position.y = -0.5; gfloor.add_child(gcs); m.add_child(gfloor)
	await phys(2)
	for b in m.buildings:
		var into: Vector3 = b.node.global_transform.basis * Vector3(0, 0, -1)
		hero.global_position = b.node.global_transform * Vector3(0, 0.1, b.aabb.end.z + 3.0)
		mgr.cooldown = 0.0
		for k in 90:
			await step(hero, into, mgr)
			if mgr.active(): break
		ok(mgr.active() and mgr.cur_bld.id == b.id, "%s door enters interior" % b.id)
		ok(not m.sun.visible, "%s sun hidden inside" % b.id)
		var back: Vector3 = mgr.cur.node.global_transform.basis * Vector3(0, 0, 1)
		await phys(50)
		for k in 240:
			await step(hero, back, mgr)
			if not mgr.active(): break
		ok(not mgr.active() and m.sun.visible, "%s walks back out to the street" % b.id)
		var lp: Vector3 = b.node.global_transform.affine_inverse() * hero.global_position
		ok(lp.z > b.aabb.end.z, "%s exit lands outside the door (z %.1f)" % [b.id, lp.z])
	m.queue_free(); await phys(2)
