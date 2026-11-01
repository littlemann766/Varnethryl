extends SceneTree
const DIRS := {"A": "stage1", "B": "stage2", "frost": "stage4", "ash": "stage4"}
const PRE := {"A": "arch_", "B": "coast_", "frost": "frost_", "ash": "ash_"}
func glb(p: String) -> Node3D:
	var d := GLTFDocument.new(); var s := GLTFState.new()
	if d.append_from_file(p, s) != OK: return null
	return d.generate_scene(s)
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var root := Node3D.new(); get_root().add_child(root)
	for reg in DIRS:
		for f in DirAccess.get_files_at("res://tidewrack/%s/meshes" % DIRS[reg]):
			if f.begins_with(PRE[reg]) and f.ends_with("_col.glb") and not f.contains("storm") and not f.contains("landing"):
				var n := glb(ProjectSettings.globalize_path("res://tidewrack/%s/meshes/%s" % [DIRS[reg], f])); root.add_child(n)
				for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false):
					var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); cs.shape = mi.mesh.create_trimesh_shape(); sb.add_child(cs); root.add_child(sb); sb.global_transform = mi.global_transform; sb.set_meta("f", f)
	for i in 3: await physics_frame
	var sp := get_root().get_world_3d().direct_space_state
	# height grid over the whole sea world, 10 m, -3200..3200 x, -3200..3200 z
	var W := 640; var img := Image.create(W, W, false, Image.FORMAT_RF)
	for j in W:
		for i in W:
			var x := -3200.0 + i * 10.0 + 5.0; var z := -3200.0 + j * 10.0 + 5.0
			var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, 400, z), Vector3(x, -80, z)))
			img.set_pixel(i, j, Color(h.position.y if h else -80.0, 0, 0))
	img.save_exr("/tmp/rp/s10/world_h.exr"); print("EDGE done"); quit()
