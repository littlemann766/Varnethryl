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
	var hz := Vector2(b.x - a.x, b.z - a.z).length(); a.y = maxf(a.y, b.y - hz * tan(deg_to_rad(18.0)))   # Lucky test 36 (godot-voxel 74526d1): sea end raised so the boards are <= 18 deg
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
func pv3(a: Array) -> Array:
	var o := []
	for q in a: o.append(v3(q))
	return o
func ride(body: AnimatableBody3D, to: Vector3, speed: float) -> Dictionary:   # player stands still on the moving platform (Lucky's ashore physics, no input)
	var from := body.global_position; var dur := from.distance_to(to) / speed; var t := 0.0
	while t < dur + 1.0:
		await physics_frame
		t += 1.0 / 60.0; body.global_position = from.lerp(to, clampf(t / dur, 0.0, 1.0))
		hero.velocity.x = 0.0; hero.velocity.z = 0.0
		hero.velocity.y = -1.0 if hero.is_on_floor() else hero.velocity.y - 20.0 / 60.0
		hero.move_and_slide()
		if absf(hero.global_position.y - body.global_position.y) > 2.5: return {"ok": false, "why": "left_platform", "t": snappedf(t, 0.1), "at": pos3(hero.global_position)}
	var ok := hero.is_on_floor() and absf(hero.global_position.y - to.y) < 0.4 and Vector2(hero.global_position.x - to.x, hero.global_position.z - to.z).length() < 1.6
	return {"ok": ok, "t": snappedf(t, 0.1), "at": pos3(hero.global_position), "why": "" if ok else "off_target"}
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
		var gate: StaticBody3D = null; var lift: AnimatableBody3D = null
		if I.has("stage9"):   # stage 9 (Saltglass): lift + shortcut statics; the gate starts LOCKED, the lift platform parks at the bottom
			add_col("%s/meshes/%s/%s.glb" % [S5, reg, I.stage9.files.col])
			gate = StaticBody3D.new(); var gcs := CollisionShape3D.new(); var gbs := BoxShape3D.new(); gbs.size = v3(I.stage9.gate.size); gcs.shape = gbs; gate.add_child(gcs); space_root.add_child(gate)
			gate.global_position = v3(I.stage9.gate.pos) + Vector3(0, gbs.size.y / 2, 0)
			lift = AnimatableBody3D.new(); lift.sync_to_physics = true
			for bx in [[Vector3(3.6, 0.3, 3.6), Vector3(0, -0.15, 0)], [Vector3(3.6, 1.1, 0.12), Vector3(0, 0.55, -1.74)], [Vector3(0.12, 1.1, 3.6), Vector3(-1.74, 0.55, 0)], [Vector3(0.12, 1.1, 3.6), Vector3(1.74, 0.55, 0)]]:
				var lc := CollisionShape3D.new(); var lb := BoxShape3D.new(); lb.size = bx[0]; lc.shape = lb; lc.position = bx[1]; lift.add_child(lc)
			space_root.add_child(lift); lift.global_position = v3(I.stage9.lift.bottom)
		var L: Dictionary = man.landings[k]; pier(L)
		for i in 3: await physics_frame
		var ph := v3(L.shore) + Vector3(0, 0.8, 0); var inl := Vector3(L.inland[0], 0, L.inland[1]).normalized()
		var out := {}
		var pa := v3(L.moor) + inl * 3.0 + Vector3(0, 1.0, 0); var pb := v3(L.shore) + inl * 1.5; pa.y = maxf(pa.y, pb.y - Vector2(pb.x - pa.x, pb.z - pa.z).length() * tan(deg_to_rad(18.0))); var pf := pa.lerp(pb, 0.08) + Vector3(0, 1.0, 0)
		out["pier_boards"] = await walk(pf, [ph], ph, 1.2)
		for po in I.pois:
			var pts := []
			for q in po.route: pts.append(v3(q))
			if pts.size() == 0:
				out[po.name] = {"ok": false, "why": "no_route"}; continue
			out[po.name] = await walk(ph, pts, v3(po.pos), float(po.radius) + 2.0)
		for b in I.bridges:
			var dv := (v3(b.b) - v3(b.a)).normalized(); var A := v3(b.a) - dv * 3.0 + Vector3(0, 0.8, 0); var B := v3(b.b) + dv * 3.0 + Vector3(0, 0.8, 0)
			var da := v3(b.a) + Vector3(0, 0.3, 0); var db := v3(b.b) + Vector3(0, 0.3, 0)
			if b.has("ends"):
				A = v3(b.ends[0]) + Vector3(0, 0.8, 0); B = v3(b.ends[1]) + Vector3(0, 0.8, 0)
			if b.has("path"):   # causeway with built bank stairs: walk the whole deck chain end to end
				var cp := []
				for q in b.path: cp.append(v3(q) + Vector3(0, 0.3, 0))
				var rv := cp.duplicate(); rv.reverse()
				out["causeway a->b"] = await walk(cp[0] + Vector3(0, 0.5, 0), cp.slice(1), cp[-1], 1.5)
				out["causeway b->a"] = await walk(rv[0] + Vector3(0, 0.5, 0), rv.slice(1), rv[-1], 1.5)
			else:
				out["causeway a->b"] = await walk(A, [da, db, B], B, 1.5)
				out["causeway b->a"] = await walk(B, [db, da, A], A, 1.5)
		if I.get("ramp") != null and I.ramp.has("pier_stair"):
			var pp := []
			for d in I.ramp.pier_stair.decks:
				pp.append(v3(d.a)); pp.append(v3(d.b))
			var s0: Vector3 = pp[0].lerp(pp[1], 0.2) + Vector3(0, 1.0, 0)
			out["pier stair up"] = await walk(s0, pp, pp[-1], 1.5)
			var rp := pp.duplicate(); rp.reverse()
			out["pier stair down"] = await walk(rp[0] + Vector3(0, 0.8, 0), rp, rp[-1], 1.5)
		if I.get("ramp") != null:
			var pts := []
			for d in I.ramp.decks:
				pts.append(v3(d.a)); pts.append(v3(d.b))
			var st: Vector3 = pts[0] - (pts[1] - pts[0]).normalized() * 3.0 + Vector3(0, 1.0, 0)
			out["stair up"] = await walk(st, pts, pts[-1], 1.5)
			var rv := pts.duplicate(); rv.reverse()
			out["stair down"] = await walk(rv[0] + Vector3(0, 0.8, 0), rv, rv[-1], 1.5)
		if I.has("stage9"):
			var R9: Dictionary = I.stage9.routes
			var gr := await walk(ph, pv3(R9.dock_to_gate), pv3(R9.dock_to_gate)[-1], 1.0)   # must NOT get through while locked
			out["shortcut gate locked (dock side blocked)"] = {"ok": not gr.ok, "walk": gr}
			var dn := pv3(R9.shortcut_down_to_lever)
			out["shortcut down to lever (gate locked)"] = await walk(dn[0] + Vector3(0, 0.8, 0), dn.slice(1), dn[-1], 1.0)
			gate.queue_free(); for i in 3: await physics_frame   # lever pulled: gate open (persistent flag)
			var upr := pv3(R9.shortcut_up)
			out["shortcut up (unlocked)"] = await walk(ph, upr, upr[-1], 1.5)
			var rv9 := upr.duplicate(); rv9.reverse(); rv9.append(ph)
			out["shortcut down (unlocked)"] = await walk(rv9[0] + Vector3(0, 0.8, 0), rv9.slice(1), ph, 1.5)
			var dl := pv3(R9.dock_to_lift)
			out["lift: dock to platform"] = await walk(ph, dl, dl[-1], 0.6)
			out["lift: ride up"] = await ride(lift, v3(I.stage9.lift.top), float(I.stage9.lift.speed))
			var lp := pv3(R9.lift_to_plateau)
			out["lift: top to plateau"] = await walk(hero.global_position, lp, lp[-1], 1.5)
			var lr := lp.duplicate(); lr.reverse(); lr.append(v3(I.stage9.lift.top) + Vector3(0, 0.08, 0))
			out["lift: plateau back to platform"] = await walk(lr[0] + Vector3(0, 0.8, 0), lr.slice(1), lr[-1], 0.6)
			out["lift: ride down"] = await ride(lift, v3(I.stage9.lift.bottom), float(I.stage9.lift.speed))
		res[k] = out; var nok := 0
		for r in out.values(): nok += 1 if r.ok else 0
		print("ISLAND %s %d/%d" % [k, nok, out.size()])
		space_root.queue_free()
		await physics_frame
	var f := FileAccess.open(a[1], FileAccess.WRITE); f.store_string(JSON.stringify(res, " ")); f.close(); quit()
