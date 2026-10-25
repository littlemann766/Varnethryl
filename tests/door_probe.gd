extends SceneTree
## Finds each building's real front door in local coords (ray-cast the collision mesh the game uses) -> prints DOOR table.
## godot --headless -s res://tests/door_probe.gd
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var M = load("res://scripts/main.gd")
	var defs: Array = M.DEFS; var card2: Array = M.CARD2
	var out := []
	var i := 0
	for d in defs:
		var id: String = d[0]
		var path := "res://assets/card2/bld_%s_card2_lod1.glb" % id if card2.has(id) else "res://assets/buildings/bld_%s.glb" % id
		var n: Node3D = load(path).instantiate(); n.position = Vector3(i * 300, 0, 0); root.add_child(n); i += 1
		var aabb := AABB(); var first := true
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			if not card2.has(id) and (String(mi.name).to_lower().contains("roof") or String(mi.get_parent().name).to_lower().contains("roof")): continue
			mi.create_trimesh_collision()
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var a: AABB = (n.global_transform.affine_inverse() * mi.global_transform) * mi.get_aabb()
			if first: aabb = a; first = false
			else: aabb = aabb.merge(a)
		await physics_frame; await physics_frame
		var space := n.get_world_3d().direct_space_state
		# ground under the door + deepest recess between |x|<4 at 1.0..1.6 m above the local ground
		var best := Vector3(0, 0, aabb.end.z); var bestz := 1e9
		var prof := []
		for xi in range(-30, 31):
			var x := xi * 0.1
			var gq := PhysicsRayQueryParameters3D.create(n.to_global(Vector3(x, 30, aabb.end.z - 1.0)), n.to_global(Vector3(x, -5, aabb.end.z - 1.0)))
			var zs := []
			for hy in [1.2, 1.8]:
				var q := PhysicsRayQueryParameters3D.create(n.to_global(Vector3(x, hy, aabb.end.z + 3)), n.to_global(Vector3(x, hy, aabb.position.z)))
				var r := space.intersect_ray(q)
				zs.append(n.to_local(r.position).z if r else -1e9)
			var z: float = max(zs[0], zs[1])
			prof.append([x, z])
		# door = the recessed run (z well behind the facade) nearest the centre; facade = median z
		var zs2 := []
		for pz in prof: if pz[1] > -1e8: zs2.append(pz[1])
		zs2.sort(); var facade: float = zs2[zs2.size() / 2] if zs2.size() else aabb.end.z
		var runs := []; var cur := []
		for pz in prof:
			if pz[1] < facade - 0.12 and pz[1] > facade - 3.0: cur.append(pz)
			elif cur.size(): runs.append(cur); cur = []
		if cur.size(): runs.append(cur)
		var pick = null
		for r in runs:
			if r.size() < 6: continue
			var cx: float = (r[0][0] + r[-1][0]) / 2.0
			if pick == null or absf(cx) < absf(pick[0]): pick = [cx, r.reduce(func(a, q): return minf(a, q[1]), 1e9), r.size() * 0.1]
		if pick: best = Vector3(pick[0], 0, pick[1])
		else: best = Vector3(0, 0, facade)
		bestz = best.z
		print("  %s facade %.2f runs %s" % [id, facade, str(runs.map(func(r): return [r[0][0], r[-1][0], snappedf(r[0][1], 0.01)]))])
		print("DOOR %s x=%.1f z=%.2f aabb_end=%.2f size=%s" % [id, best.x, best.z, aabb.end.z, aabb.size.snapped(Vector3.ONE * 0.1)])
		out.append('"%s": Vector3(%.2f, 0, %.2f)' % [id, best.x, best.z])
	print("DOORS := {" + ", ".join(out) + "}")
	quit()
