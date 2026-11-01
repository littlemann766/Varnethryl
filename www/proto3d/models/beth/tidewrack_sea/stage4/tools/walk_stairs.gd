extends SceneTree
const DIRS := {"frost": "stage4", "ash": "stage4"}
const PRE := {"frost": "frost_", "ash": "ash_"}
func glb(p: String) -> Node3D:
	var d := GLTFDocument.new(); var s := GLTFState.new()
	if d.append_from_file(p, s) != OK: return null
	return d.generate_scene(s)
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var J: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tp/landing_stairs.json"))
	var root := Node3D.new(); get_root().add_child(root)
	for f in DirAccess.get_files_at("res://tidewrack/stage4/meshes"):
		if (f.begins_with("ash_") or f.begins_with("frost_")) and f.ends_with("_col.glb") and not f.contains("storm"):
			var n := glb(ProjectSettings.globalize_path("res://tidewrack/stage4/meshes/" + f)); root.add_child(n)
			for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false):
				var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); cs.shape = mi.mesh.create_trimesh_shape(); sb.add_child(cs); root.add_child(sb); sb.global_transform = mi.global_transform
	for id in J:
		for dir in [1, -1]:
			var r: Array = J[id].inland_route.duplicate(); if dir < 0: r.reverse()
			var b := CharacterBody3D.new(); var cs := CollisionShape3D.new(); var cap := CapsuleShape3D.new(); cap.radius = 0.35; cap.height = 1.8; cs.shape = cap; cs.position.y = 0.9; b.add_child(cs)
			b.floor_max_angle = deg_to_rad(40); b.floor_snap_length = 0.5; root.add_child(b)
			b.global_position = Vector3(r[0][0], r[0][1] + 0.6, r[0][2])
			for i in 3: await physics_frame
			var wi := 1; var t := 0.0; var miny := 999.0
			while t < 60.0 and wi < r.size():
				var tg := Vector3(r[wi][0], r[wi][1], r[wi][2]); var dv := tg - b.global_position; dv.y = 0
				if dv.length() < 0.8: wi += 1; continue
				var v := dv.normalized() * 4.0; b.velocity.x = v.x; b.velocity.z = v.z
				b.velocity.y = 0.0 if b.is_on_floor() else b.velocity.y - 9.8 / 60.0
				b.move_and_slide(); await physics_frame; t += 1.0 / 60.0; miny = min(miny, b.global_position.y - lerpf(r[wi - 1][1], r[wi][1], 0.5))
			var e: Array = r[-1]
			print("WALK ", id, " ", "up" if dir > 0 else "down", " ok=", wi >= r.size(), " t=%.1f end=%s target_y=%.1f" % [t, b.global_position, e[1]])
			b.queue_free()
	quit()
