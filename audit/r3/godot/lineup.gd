extends Node3D
# Beth r3 import check: lays out GLBs in rows and saves screenshots (day + night with emissive windows).
var cam: Camera3D
var sun: DirectionalLight3D
var env: WorldEnvironment
func _place(path: String, pos: Vector3, yaw := 0.0) -> Node3D:
	var ps = load(path)
	if ps == null:
		print("FAIL ", path); return null
	var n: Node3D = ps.instantiate(); n.position = pos; n.rotation.y = yaw; add_child(n); _vc(n); return n
func _vc(n: Node) -> void:
	# Beth GLBs carry tints in COLOR_0; Godot's glTF importer leaves vertex_color_use_as_albedo off.
	if n is MeshInstance3D:
		for i in n.mesh.get_surface_count():
			var m = n.mesh.surface_get_material(i)
			if m is BaseMaterial3D: m.vertex_color_use_as_albedo = true; m.vertex_color_is_srgb = false
	for c in n.get_children(): _vc(c)
func _ready() -> void:
	env = WorldEnvironment.new(); var e := Environment.new(); e.background_mode = Environment.BG_SKY
	var sky := Sky.new(); sky.sky_material = ProceduralSkyMaterial.new(); e.sky = sky; e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = e; add_child(env)
	sun = DirectionalLight3D.new(); sun.rotation = Vector3(-0.9, 0.7, 0); sun.shadow_enabled = true; add_child(sun)
	var g := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(900, 900); g.mesh = pm
	var gm := StandardMaterial3D.new(); gm.albedo_color = Color(0.36, 0.5, 0.3); g.material_override = gm; add_child(g)
	cam = Camera3D.new(); cam.far = 2000; add_child(cam)
	var ids := ["guildhall","library","townhall","mage","treasury","keep","observatory","crypt","market","apothecary","bakery","inn","smithy","temple","training","colosseum"]
	var ok := 0
	for i in ids.size():
		if _place("res://r3/buildings/bld_%s.glb" % ids[i], Vector3((i % 4) * 55 - 82, 0, -(i / 4) * 55)) != null: ok += 1
	var dz := ["well","market_stall_red","market_stall_blue","market_stall_green","lantern_post","signpost","bench","flower_planter","banner_pole_blue","banner_pole_red","curb_2m","cobble_edge_2m","milestone","rubble","wall_cap_4m"]
	for i in dz.size():
		if _place("res://r3/dressing/%s.glb" % dz[i], Vector3(i * 4.0 - 28, 0, 40)) != null: ok += 1
	var tr := ["mountain_peak_snow","mountain_peak_bare","volcano_cone_flank","cliff_ridge_60m","scree_slope","grass_mound","rock_arch"]
	for i in tr.size():
		if _place("res://r3/terrain/%s.glb" % tr[i], Vector3(i * 70 - 210, 0, -330)) != null: ok += 1
	var w := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = Vector3(20, 6, 1); w.mesh = bm; w.position = Vector3(0, 3, 55); add_child(w)
	var dc := ["decal_moss_wall","decal_grime_wall","decal_crack_wall","decal_soot_wall","decal_dirt_wall"]
	for i in dc.size(): _place("res://r3/decals/%s.glb" % dc[i], Vector3(i * 3.6 - 7.2, 0, 54.5), PI)
	var dg := ["decal_moss_ground","decal_dirt_ground","decal_puddle","decal_leaves","decal_crack_ground"]
	for i in dg.size(): _place("res://r3/decals/%s.glb" % dg[i], Vector3(i * 3.0 - 6, 0.0, 48))
	print("LOADED ", ok)
	await _shots()
	get_tree().quit()
func _shot(name: String, p: Vector3, t: Vector3) -> void:
	cam.position = p; cam.look_at(t)
	for i in 30: await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png("res://r3/shot_%s.png" % name)
func _shots() -> void:
	await _shot("buildings_row1", Vector3(-10, 30, 60), Vector3(-10, 4, 0))
	await _shot("buildings_row3", Vector3(-10, 34, -40), Vector3(-10, 4, -130))
	await _shot("dressing", Vector3(0, 5, 28), Vector3(-2, 1, 40))
	await _shot("decals", Vector3(0, 4, 40), Vector3(0, 1.5, 55))
	await _shot("terrain", Vector3(0, 45, -230), Vector3(0, 12, -330))
	sun.light_energy = 0.03; env.environment.background_energy_multiplier = 0.05; env.environment.ambient_light_energy = 0.15
	await _shot("night_row1", Vector3(-10, 30, 60), Vector3(-10, 4, 0))
	await _shot("night_inn", Vector3(-10, 10, -32), Vector3(-27, 4, -110))
