extends SceneTree
func glb(p: String) -> Node3D:
	var d := GLTFDocument.new(); var s := GLTFState.new()
	if d.append_from_file(p, s) != OK: return null
	return d.generate_scene(s)
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var root := Node3D.new(); get_root().add_child(root)
	for f in DirAccess.get_files_at("res://tidewrack/stage2/meshes"):
		if f.begins_with("coast_") and f.ends_with("_col.glb") and not f.contains("storm"):
			var n := glb(ProjectSettings.globalize_path("res://tidewrack/stage2/meshes/" + f)); root.add_child(n)
			for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false):
				var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); cs.shape = mi.mesh.create_trimesh_shape(); sb.add_child(cs); root.add_child(sb); sb.global_transform = mi.global_transform
	for i in 3: await physics_frame
	var sp := get_root().get_world_3d().direct_space_state
	var gy := func(x: float, z: float, top: float) -> float:
		var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, top, z), Vector3(x, -60, z))); return h.position.y if h else NAN
	var M: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tidewrack/stage5_manifest.json"))
	var pois := {}
	var stack := [M]
	while stack.size() > 0:
		var o = stack.pop_back()
		if o is Dictionary:
			if o.has("pois") and o.get("id", "") in ["saltglass", "beached_wreck"]: pois[o.id] = o.pois
			for v in o.values(): stack.append(v)
		elif o is Array:
			for v in o: stack.append(v)
	var stones := {"saltglass": [[-2338.0, 108.0], [-2190.0, 14.0]], "beached_wreck": [[-2446.0, 960.0], [-2600.0, 975.0]]}
	var out := {}
	for id in stones:
		var s2: Array = stones[id][1]; var s1: Array = stones[id][0]
		var w1 := Vector3(s1[0], gy.call(s1[0], s1[1], 200.0), s1[1]); var w2 := Vector3(s2[0], gy.call(s2[0], s2[1], 200.0), s2[1])
		if id == "beached_wreck":   # far stone on the Salvage Chest route, nearest the 3 POIs' centroid
			var cen := Vector3.ZERO
			for p in pois[id]: cen += Vector3(p.pos[0], 0, p.pos[2]) / 3.0
			var best := 1e9
			for p in pois[id]:
				if p.name != "Salvage Chest": continue
				for q in p.route:
					var d := Vector2(q[0] - cen.x, q[2] - cen.z).length()
					if d < best: best = d; w2 = Vector3(q[0], q[1], q[2])
		out[id] = {"dock_stone": [w1.x, w1.y, w1.z], "far_stone": [w2.x, w2.y, w2.z], "legs": {}}
		for p in pois[id]:
			# best of: original route time is known; new = walk from far stone straight to POI (raycast-seated capsule)
			var tgt := Vector3(p.pos[0], p.pos[1], p.pos[2])
			var b := CharacterBody3D.new(); var cs := CollisionShape3D.new(); var cap := CapsuleShape3D.new(); cap.radius = 0.35; cap.height = 1.8; cs.shape = cap; cs.position.y = 0.9; b.add_child(cs)
			b.floor_max_angle = deg_to_rad(46); b.floor_snap_length = 0.6; root.add_child(b); b.global_position = w2 + Vector3(1.5, 0.4, 1.5)
			for i in 2: await physics_frame
			var t := 0.0; var ok := false
			var rt: Array = p.route; var k0 := 0; var bd := 1e9
			for k in rt.size():
				var d := Vector2(rt[k][0] - w2.x, rt[k][2] - w2.z).length()
				if d < bd: bd = d; k0 = k
			var wps := []
			for k in range(k0, rt.size()): wps.append(Vector3(rt[k][0], rt[k][1], rt[k][2]))
			wps.append(tgt); var wi := 0
			while t < 90.0:
				while wi < wps.size() - 1 and Vector2(wps[wi].x - b.global_position.x, wps[wi].z - b.global_position.z).length() < 1.2: wi += 1
				var dv: Vector3 = wps[wi] - b.global_position; dv.y = 0
				var dt := tgt - b.global_position; dt.y = 0
				if dt.length() < float(p.get("radius", 3)) * 0.5 + 1.0: ok = true; break
				var v := dv.normalized() * 6.0; b.velocity.x = v.x; b.velocity.z = v.z
				b.velocity.y = 0.0 if b.is_on_floor() else b.velocity.y - 9.8 / 60.0
				b.move_and_slide(); await physics_frame; t += 1.0 / 60.0
			out[id].legs[p.name] = {"ok": ok, "t": snappedf(t, 0.1), "end": [b.global_position.x, b.global_position.y, b.global_position.z]}
			print("WAY ", id, " ", p.name, " ok=", ok, " t=%.1f" % t)
			b.queue_free()
	FileAccess.open("/tmp/rp/s8/waywalk.json", FileAccess.WRITE).store_string(JSON.stringify(out, " ")); quit()
