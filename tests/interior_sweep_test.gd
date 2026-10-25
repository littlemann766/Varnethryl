extends SceneTree
## Test 13 (boss stuck beside a pillar in the Treasury): walkability sweep of EVERY interior.
## For each floor, a 0.5 m grid of spots where the Owner capsule fits (no overlap, floor below) is sampled; every
## such spot must (a) lie on the navmesh baked for the same capsule radius and (b) have a path back to the exit door.
## Spots the hero can stand in but cannot leave = traps -> FAIL (printed with coordinates).
## Run: godot --headless --fixed-fps 60 --path . -s res://tests/interior_sweep_test.gd [-- only=treasury]
const B := preload("res://interiors/interior_builder.gd")
const DEF := preload("res://interiors/interior_defs.gd")
const R := 0.33        # Owner capsule radius (party.gd: clamp(1.905*0.17, .12, .53))
const H := 1.905
var fails := 0; var passes := 0
func ok(c: bool, msg: String) -> void:
	if c: passes += 1
	else: fails += 1
	print(("PASS " if c else "FAIL ") + msg)
func _initialize() -> void: _run.call_deferred()
func phys(n := 1) -> void:
	for i in n: await physics_frame

func _run() -> void:
	var only: Array = []
	for a in OS.get_cmdline_user_args(): if a.begins_with("only="): only = a.substr(5).split(",")
	for id in DEF.D:
		if only.size() and not only.has(id): continue
		await sweep(id)
	print("SWEEP %d passed, %d failed" % [passes, fails])
	quit(1 if fails else 0)

func sweep(id: String) -> void:
	var info := B.build(id, DEF.D[id], DEF.SIZE.get(id, Vector3(24, 18, 22)))
	root.add_child(info.node); await phys(3)
	var nm := NavigationMesh.new(); nm.agent_radius = R; nm.agent_height = H; nm.agent_max_climb = 0.25; nm.agent_max_slope = 42.0
	nm.cell_size = 0.1; nm.cell_height = 0.1; nm.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
	var src := NavigationMeshSourceGeometryData3D.new()
	NavigationServer3D.parse_source_geometry_data(nm, src, info.node); NavigationServer3D.bake_from_source_geometry_data(nm, src)
	var map := NavigationServer3D.map_create(); NavigationServer3D.map_set_cell_size(map, 0.1); NavigationServer3D.map_set_cell_height(map, 0.1)
	NavigationServer3D.map_set_active(map, true)
	var reg := NavigationServer3D.region_create(); NavigationServer3D.region_set_map(reg, map); NavigationServer3D.region_set_navigation_mesh(reg, nm)
	await phys(3); NavigationServer3D.map_force_update(map)
	for i in 600:
		if NavigationServer3D.map_get_iteration_id(map) > 0 and NavigationServer3D.map_get_path(map, info.spawn, info.spawn + Vector3(0, 0, -2), true).size() > 0: break
		await phys(1)
	print("  %s navmesh polys %d, spawn %s exit_z %.2f" % [id, nm.get_polygon_count(), info.spawn, info.exit_z])
	var door: Vector3 = info.spawn
	var door_nav := NavigationServer3D.map_get_closest_point(map, door)
	ok(door_nav.distance_to(door) < 1.2, "%s door on the navmesh" % id)
	var space: PhysicsDirectSpaceState3D = (info.node as Node3D).get_world_3d().direct_space_state
	var cap := CapsuleShape3D.new(); cap.radius = R; cap.height = H
	var W: float = info.W; var D: float = info.D
	var traps := []; var n := 0; var good := []
	for fi in info.floors.size():
		var fy: float = info.floors[fi].y
		var x := -W / 2 + 0.4
		while x < W / 2 - 0.4:
			var z := -D / 2 + 0.4
			while z < D / 2 - 0.4:
				# floor under the spot (slab/stairs), within this storey
				var q := PhysicsRayQueryParameters3D.create(Vector3(x, fy + 1.0, z), Vector3(x, fy - 0.3, z))
				var hit: Dictionary = space.intersect_ray(q)
				if not hit.is_empty() and absf(hit.position.y - fy) < 0.15:
					var sp := PhysicsShapeQueryParameters3D.new(); sp.shape = cap
					sp.transform = Transform3D(Basis(), hit.position + Vector3(0, H / 2 + 0.05, 0))
					if space.intersect_shape(sp, 1).is_empty():
						n += 1
						var p: Vector3 = hit.position
						var c := NavigationServer3D.map_get_closest_point(map, p)
						var path := NavigationServer3D.map_get_path(map, c, door_nav, true)
						var on_nav := Vector2(c.x - p.x, c.z - p.z).length() < 0.45 and absf(c.y - p.y) < 0.5
						var out := path.size() > 0 and path[-1].distance_to(door_nav) < 0.6
						if not (on_nav and out): traps.append([fi, snappedf(x, 0.1), snappedf(z, 0.1), on_nav, out])
						else: good.append(p)
				z += 0.5
			x += 0.5
	# a nav-isolated spot is only a TRAP if the real hero standing there cannot walk back onto the door-connected navmesh
	var real := []
	var hero := CharacterBody3D.new(); var cs := CollisionShape3D.new(); cs.shape = cap; cs.position.y = H / 2; hero.add_child(cs); hero.floor_snap_length = 0.6
	info.node.add_child(hero)
	var mgr := InteriorManager.new(); root.add_child(mgr); mgr.cur = info
	for t in traps:
		var fy: float = info.floors[t[0]].y
		var spot := Vector3(t[1], fy + 0.05, t[2])
		# 1) can the hero even get in? start at the nearest door-connected spot on this floor and push toward it
		var st := Vector3.INF; var bd := INF
		for g in good:
			if absf(g.y - spot.y) < 0.6 and g.distance_to(spot) < bd: bd = g.distance_to(spot); st = g
		if st == Vector3.INF or bd > 4.0: continue    # sealed pocket (props against walls / ladder lofts): unreachable, not a trap
		hero.global_position = st + Vector3(0, 0.05, 0); hero.velocity = Vector3.ZERO
		var entered := false
		for i in 180:
			var d0 := spot - hero.global_position; d0.y = 0
			if d0.length() < 0.35: entered = true; break
			d0 = d0.normalized(); hero.velocity.x = d0.x * 4.0; hero.velocity.z = d0.z * 4.0
			hero.velocity.y = -1.0 if hero.is_on_floor() else hero.velocity.y - 20.0 / 60.0
			hero.move_and_slide(); await physics_frame
		if not entered: continue
		# 2) inside: can he get back to the door-connected area?
		var escaped := false
		for i in 240:
			var tgt := NavigationServer3D.map_get_closest_point(map, hero.global_position)
			var conn := NavigationServer3D.map_get_path(map, tgt, door_nav, true)
			if Vector2(tgt.x - hero.global_position.x, tgt.z - hero.global_position.z).length() < 0.3 and absf(tgt.y - hero.global_position.y) < 0.5 and conn.size() > 0 and conn[-1].distance_to(door_nav) < 0.6: escaped = true; break
			var goal := st if i > 120 else tgt
			var d := goal - hero.global_position; d.y = 0
			if d.length() > 0.05: d = d.normalized()
			hero.velocity.x = d.x * 4.0; hero.velocity.z = d.z * 4.0
			hero.velocity.y = -1.0 if hero.is_on_floor() else hero.velocity.y - 20.0 / 60.0
			mgr.climb(hero, d, 1.0 / 60.0); hero.move_and_slide(); await physics_frame
		if not escaped: real.append(t)
	hero.queue_free(); mgr.queue_free()
	for t in real.slice(0, 10): print("  TRAP %s f%d (%.1f, %.1f) on_nav=%s path_out=%s" % [id, t[0], t[1], t[2], t[3], t[4]])
	ok(real.is_empty(), "%s: %d standable spots, %d nav-isolated, %d real traps" % [id, n, traps.size(), real.size()])
	NavigationServer3D.free_rid(reg); NavigationServer3D.free_rid(map)
	info.node.queue_free(); await phys(2)
