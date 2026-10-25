extends SceneTree
## Real-game climb: in the full main scene, enter the Arcane Academy (id "mage") through InteriorManager and drive the
## Owner with the same joystick input players use (main.joy_vec + camera yaw) along a navmesh path, floor by floor,
## to the top floor (Observatory). Fails if the hero is stuck or never gets above floor 3's height.
## godot --headless -s res://tests/mage_climb_test.gd
func _initialize() -> void: _run.call_deferred()
var fails := 0
func ok(c: bool, m: String) -> void:
	print(("PASS " if c else "FAIL ") + m)
	if not c: fails += 1

func _run() -> void:
	var m = load("res://main.tscn").instantiate(); root.add_child(m)
	for i in 30: await process_frame
	var b: Dictionary = {}
	for x in m.buildings: if x.id == "mage": b = x
	ok(not b.is_empty(), "mage building present")
	m.interiors.enter(b)
	var info: Dictionary = m.interiors.cur
	for i in 20: await physics_frame
	ok(String(info.get("name", "")).begins_with("Arcane Academy"), "interior title is '%s'" % info.get("name", ""))
	var nm := NavigationMesh.new(); nm.agent_radius = 0.35; nm.agent_height = 1.95; nm.agent_max_climb = 0.1; nm.agent_max_slope = 42.0
	nm.cell_size = 0.1; nm.cell_height = 0.1; nm.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
	var src := NavigationMeshSourceGeometryData3D.new()
	NavigationServer3D.parse_source_geometry_data(nm, src, info.node)
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	var map := NavigationServer3D.map_create(); NavigationServer3D.map_set_cell_size(map, 0.1); NavigationServer3D.map_set_cell_height(map, 0.1)
	NavigationServer3D.map_set_active(map, true)
	var reg := NavigationServer3D.region_create(); NavigationServer3D.region_set_map(reg, map); NavigationServer3D.region_set_navigation_mesh(reg, nm)
	NavigationServer3D.region_set_transform(reg, (info.node as Node3D).global_transform)
	for i in 10: await physics_frame
	NavigationServer3D.map_force_update(map)
	var hero: CharacterBody3D = m.hero
	var y0 := hero.global_position.y
	var top := -1
	for r in info.rooms: top = maxi(top, r.floor)
	for r in info.rooms:
		var tgt: Vector3 = (info.node as Node3D).to_global(r.pos)
		var path := NavigationServer3D.map_get_path(map, hero.global_position, tgt, true)
		for w in 60:
			if path.size() > 0: break
			await physics_frame; NavigationServer3D.map_force_update(map); path = NavigationServer3D.map_get_path(map, hero.global_position, tgt, true)
		var stuck := false
		for p in path:
			var t := 0
			while Vector2(hero.global_position.x - p.x, hero.global_position.z - p.z).length() > 0.3:
				var d: Vector3 = p - hero.global_position
				m.yaw = atan2(-d.x, -d.z); m.joy_vec = Vector2(0, -0.6)
				await physics_frame
				t += 1
				if t > 600: stuck = true; break
			if stuck: break
		m.joy_vec = Vector2.ZERO
		for i in 10: await physics_frame
		var hp := hero.global_position
		ok(not stuck and absf(hp.y - tgt.y) < 0.8 and Vector2(hp.x - tgt.x, hp.z - tgt.z).length() < 1.2,
			"walks to %s (floor %d): hero y %.2f (target %.2f)" % [r.name, r.floor, hp.y - y0, tgt.y - y0])
	ok(hero.global_position.y - y0 > 8.0, "top floor %d reached by walking (climbed %.1f m)" % [top, hero.global_position.y - y0])
	print("MAGE_CLIMB %d failed" % fails)
	quit(1 if fails else 0)
