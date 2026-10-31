extends SceneTree
const B := preload("res://interiors/interior_builder.gd")
const DEF := preload("res://interiors/interior_defs.gd")
func _initialize() -> void: _run.call_deferred()
func test(id: String, def: Dictionary, tgt: Vector3) -> String:
	var info: Dictionary = B.build(id, def, DEF.SIZE[id])
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
	var pth := NavigationServer3D.map_get_path(map, info.spawn, tgt, true)
	info.node.queue_free(); NavigationServer3D.free_rid(reg); NavigationServer3D.free_rid(map)
	await physics_frame
	return ("%.2f" % pth[-1].y) if pth.size() else "none"
func _run() -> void:
	var base: Dictionary = DEF.D["guildhall"]
	for v in [[5.55, 2.2], [5.3, 2.2], [5.0, 2.2], [4.7, 2.2], [5.55, 1.6], [5.0, 1.6]]:
		var d := base.duplicate(true); d.stairs = [[0, v[0], v[1], 0, 1.4]]
		print(v, " -> ", await test("guildhall", d, Vector3(0, 4.2, 4.8)))
	quit()
