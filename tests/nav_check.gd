extends SceneTree
## Fast navmesh-only reachability check (spawn -> every room), same bake settings as interiors_test.gd.
## godot --headless -s res://tests/nav_check.gd [-- only=inn,smithy]
const B := preload("res://interiors/interior_builder.gd")
const DEF := preload("res://interiors/interior_defs.gd")
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var only: Array = []
	for a in OS.get_cmdline_user_args(): if a.begins_with("only="): only = a.substr(5).split(",")
	for id in DEF.D:
		if only.size() and not id in only: continue
		var info: Dictionary = B.build(id, DEF.D[id], DEF.SIZE.get(id, Vector3(24, 18, 22)))
		root.add_child(info.node)
		for i in 4: await physics_frame
		var nm := NavigationMesh.new(); nm.agent_radius = 0.35; nm.agent_height = 1.95; nm.agent_max_climb = 0.1; nm.agent_max_slope = 42.0
		nm.cell_size = 0.1; nm.cell_height = 0.1; nm.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
		var src := NavigationMeshSourceGeometryData3D.new()
		NavigationServer3D.parse_source_geometry_data(nm, src, info.node)
		NavigationServer3D.bake_from_source_geometry_data(nm, src)
		var map := NavigationServer3D.map_create(); NavigationServer3D.map_set_cell_size(map, 0.1); NavigationServer3D.map_set_cell_height(map, 0.1); NavigationServer3D.map_set_active(map, true)
		var reg := NavigationServer3D.region_create(); NavigationServer3D.region_set_map(reg, map); NavigationServer3D.region_set_navigation_mesh(reg, nm)
		for i in 20: await physics_frame
		NavigationServer3D.map_force_update(map)
		var bad := []
		for r in info.rooms:
			var p := NavigationServer3D.map_get_path(map, info.spawn, r.pos, true)
			if p.size() == 0 or Vector2(p[-1].x - r.pos.x, p[-1].z - r.pos.z).length() > 1.0 or absf(p[-1].y - r.pos.y) > 0.8:
				bad.append("%s %s closest %s end %s" % [r.name, r.pos, NavigationServer3D.map_get_closest_point(map, r.pos), p[-1] if p.size() else null])
		print("NAV ", id, " W%.1f D%.1f " % [info.W, info.D], "OK" if bad.is_empty() else "BAD %s" % [bad])
		info.node.queue_free(); NavigationServer3D.free_rid(reg); NavigationServer3D.free_rid(map); await physics_frame
	quit()
