extends SceneTree
## Stage 5 walk test: Lucky's ashore physics (CharacterBody3D capsule h1.905 r0.32, speed 6, g 20, floor snap 0.6, max floor 50 deg,
## same reset rules as tw_sea._walk) along every exported route pier head -> POI, the pier boards, the causeways and the Saltglass stair.
var space_root: Node3D
var hero: CharacterBody3D
var res := {}
const DIRS := {"A": "stage1", "B": "stage2", "frost": "stage4", "ash": "stage4"}
const PRE := {"A": "arch_", "B": "coast_", "frost": "frost_", "ash": "ash_"}
func glb(p: String) -> Node3D:
	var d := GLTFDocument.new(); var s := GLTFState.new()
	if d.append_from_file(p, s) != OK: return null
	return d.generate_scene(s)
func add_col(p: String) -> void:
	var n := glb(p)
	if n == null:
		print("MISSING ", p); return
	space_root.add_child(n)
	for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false):
		var sb := StaticBody3D.new(); sb.name = p.get_file().get_basename() + "_" + mi.name; var cs := CollisionShape3D.new(); cs.shape = mi.mesh.create_trimesh_shape(); sb.add_child(cs); space_root.add_child(sb); sb.global_transform = mi.global_transform
	n.visible = false
func v3(a: Array) -> Vector3: return Vector3(a[0], a[1], a[2])
func pier(L: Dictionary) -> void:
	var inl := Vector3(L.inland[0], 0, L.inland[1]).normalized()
	var a := v3(L.moor) + inl * 3.0 + Vector3(0, 1.0, 0); var b := v3(L.shore) + inl * 1.5
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var bs := BoxShape3D.new(); bs.size = Vector3(3.2, 0.3, a.distance_to(b)); cs.shape = bs; sb.add_child(cs); space_root.add_child(sb)
	sb.look_at_from_position((a + b) * 0.5, b, Vector3.UP)
func pos3(v: Vector3) -> Array: return [snappedf(v.x, 0.1), snappedf(v.y, 0.1), snappedf(v.z, 0.1)]
func walk(start: Vector3, pts: Array, goal: Vector3, goal_r: float) -> Dictionary:
	hero.global_position = start; hero.velocity = Vector3.ZERO
	var wi := 0; var t := 0.0; var air := 0.0; var stuck := 0.0
	var tmax := 40.0 + float(pts.size()) * 2.0
	while t < tmax:
		await physics_frame
		var dt := 1.0 / 60.0; t += dt
		var hp := hero.global_position
		if Vector2(hp.x - goal.x, hp.z - goal.z).length() < goal_r: return {"ok": true, "t": snappedf(t, 0.1)}
		while wi < pts.size() - 1 and Vector2(hp.x - pts[wi].x, hp.z - pts[wi].z).length() < 1.6: wi += 1
		var tgt: Vector3 = pts[wi]
		var dir := Vector3(tgt.x - hp.x, 0, tgt.z - hp.z)
		if dir.length() > 0.05: dir = dir.normalized()
		hero.velocity.x = dir.x * 6.0; hero.velocity.z = dir.z * 6.0
		hero.velocity.y = -1.0 if hero.is_on_floor() else hero.velocity.y - 20.0 * dt
		var before := hero.global_position
		hero.move_and_slide()
		var moved := hero.global_position.distance_to(before)
		if hero.is_on_floor(): air = 0.0
		else: air += dt
		stuck = stuck + dt if moved < 6.0 * dt * 0.05 else 0.0
		var why := ""
		if hero.global_position.y < -0.2: why = "fell_in_sea"
		elif air > 1.5: why = "airborne"
		elif stuck > 2.0: why = "stuck"
		elif hero.global_position.y < tgt.y - 3.0 and Vector2(hp.x - tgt.x, hp.z - tgt.z).length() < 3.0: why = "dropped_through"
		var hits := []
		for ci in hero.get_slide_collision_count():
			var c := hero.get_slide_collision(ci); var co: Object = c.get_collider()
			hits.append("%s n%s p%s" % [(co as Node).name if co is Node else "?", str(c.get_normal().snapped(Vector3(0.01, 0.01, 0.01))), str(c.get_position().snapped(Vector3(0.1, 0.1, 0.1)))])
		if why != "": return {"hits": hits, "ok": false, "t": snappedf(t, 0.1), "why": why, "at": pos3(hero.global_position), "wp": wi, "of": pts.size()}
	return {"ok": false, "t": snappedf(t, 0.1), "why": "timeout", "at": pos3(hero.global_position), "wp": wi, "of": pts.size()}
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var a := OS.get_cmdline_user_args(); var man: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(a[0])); var only: Array = a.slice(2)
	var S5 := a[0].get_base_dir()
	hero = CharacterBody3D.new(); var cs := CollisionShape3D.new(); var cap := CapsuleShape3D.new(); cap.height = 1.905; cap.radius = 0.32; cs.shape = cap; cs.position.y = 1.905 / 2; hero.add_child(cs)
	hero.floor_snap_length = 0.6; hero.floor_max_angle = deg_to_rad(50.0); get_root().add_child(hero)
	for k in man.islands:
		if only.size() > 0 and not only.has(k): continue
		var I: Dictionary = man.islands[k]; var reg: String = I.region
		space_root = Node3D.new(); get_root().add_child(space_root)
		for f in DirAccess.get_files_at("res://tw/" + DIRS[reg]):
			if f.begins_with(PRE[reg]) and f.ends_with("_col.glb") and not f.contains("storm"): add_col(ProjectSettings.globalize_path("res://tw/%s/%s" % [DIRS[reg], f]))
		add_col("%s/meshes/%s/%s.glb" % [S5, reg, I.files.col])
		var L: Dictionary = man.landings[k]; pier(L)
		for i in 3: await physics_frame
		var ph := v3(L.shore) + Vector3(0, 0.8, 0); var inl := Vector3(L.inland[0], 0, L.inland[1]).normalized()
		var out := {}
		var pa := v3(L.moor) + inl * 3.0 + Vector3(0, 1.0, 0); var pb := v3(L.shore) + inl * 1.5; var pf := pa.lerp(pb, 0.08) + Vector3(0, 1.0, 0)
		out["pier_boards"] = await walk(pf, [ph], ph, 1.2)
		for po in I.pois:
			var pts := []
			for q in po.route: pts.append(v3(q))
			if pts.size() == 0:
				out[po.name] = {"ok": false, "why": "no_route"}; continue
			out[po.name] = await walk(ph, pts, v3(po.pos), float(po.radius) + 2.0)
		for b in I.bridges:
			var dv := (v3(b.b) - v3(b.a)).normalized(); var A := v3(b.a) - dv * 3.0 + Vector3(0, 0.8, 0); var B := v3(b.b) + dv * 3.0 + Vector3(0, 0.8, 0)
			out["causeway a->b"] = await walk(A, [B], B, 1.5)
			out["causeway b->a"] = await walk(B, [A], A, 1.5)
		if I.get("ramp") != null:
			var pts := []
			for d in I.ramp.decks:
				pts.append(v3(d.a)); pts.append(v3(d.b))
			var st: Vector3 = pts[0] - (pts[1] - pts[0]).normalized() * 3.0 + Vector3(0, 1.0, 0)
			out["stair up"] = await walk(st, pts, pts[-1], 1.5)
			var rv := pts.duplicate(); rv.reverse()
			out["stair down"] = await walk(rv[0] + Vector3(0, 0.8, 0), rv, rv[-1], 1.5)
		res[k] = out; var nok := 0
		for r in out.values(): nok += 1 if r.ok else 0
		print("ISLAND %s %d/%d" % [k, nok, out.size()])
		space_root.queue_free()
		await physics_frame
	var f := FileAccess.open(a[1], FileAccess.WRITE); f.store_string(JSON.stringify(res, " ")); f.close(); quit()
