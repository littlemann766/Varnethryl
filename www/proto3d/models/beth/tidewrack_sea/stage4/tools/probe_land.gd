extends SceneTree
const DIRS := {"A": "stage1", "B": "stage2", "frost": "stage4", "ash": "stage4"}
const PRE := {"A": "arch_", "B": "coast_", "frost": "frost_", "ash": "ash_"}
func glb(p: String) -> Node3D:
	var d := GLTFDocument.new(); var s := GLTFState.new()
	if d.append_from_file(p, s) != OK: return null
	return d.generate_scene(s)
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var L: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tidewrack/landings.json"))
	var root := Node3D.new(); get_root().add_child(root); var done := {}
	var res := {}
	for id in ["vent", "aurora_arch", "hot_spring", "obsidian_arch"]:
		var reg: String = L[id].region
		if not done.has(reg):
			done[reg] = true
			for f in DirAccess.get_files_at("res://tidewrack/%s/meshes" % DIRS[reg]):
				if f.begins_with(PRE[reg]) and f.ends_with("_col.glb") and not f.contains("storm"):
					var n := glb(ProjectSettings.globalize_path("res://tidewrack/%s/meshes/%s" % [DIRS[reg], f])); root.add_child(n)
					for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false):
						var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); cs.shape = mi.mesh.create_trimesh_shape(); sb.add_child(cs); root.add_child(sb); sb.global_transform = mi.global_transform
		pass
		for i in 3: await physics_frame
		var sp := get_root().get_world_3d().direct_space_state
		var S := Vector3(L[id].shore[0], L[id].shore[1], L[id].shore[2]); var inl := Vector3(L[id].inland[0], 0, L[id].inland[1]).normalized()
		var dirs := {}
		for deg in [0]:
			var d := (-inl).rotated(Vector3.UP, deg_to_rad(deg)); var prof := []
			for t2 in range(-24, 17):
				var t := t2 * 0.5
				var p := S + d * t; var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, 200, p.z), Vector3(p.x, -60, p.z)); var h := sp.intersect_ray(q)
				prof.append(snappedf(h.position.y, 0.1) if h else -60.0)
			dirs[str(deg)] = prof
		res[id] = {"S": [S.x, S.y, S.z], "inl": [inl.x, inl.z], "dirs": dirs}
	FileAccess.open("/tmp/rp/land_rim.json", FileAccess.WRITE).store_string(JSON.stringify(res)); quit()
