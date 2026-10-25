extends Node
## VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json xvfb-run -a godot -s res://tests/road_shots.gd
var m: Node
var root: Window
func _ready() -> void:
	root = get_tree().root
	await get_tree().process_frame; await get_tree().process_frame
	m = get_tree().current_scene; _run()
func quit() -> void: get_tree().quit()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func shot(name: String) -> void:
	m.speed_x = 0.0; m._set_time(11.0)
	await frames(4)
	root.get_viewport().get_texture().get_image().save_png("res://tests/shots/road_%s.png" % name); print("SHOT ", name)
func place(p: Vector2, yaw: float, pitch: float, arm: float) -> void:
	m.hero.position = Vector3(p.x, m.height(p.x, p.y) + 0.1, p.y); m.yaw = yaw; m.pitch = pitch; m.cam_arm.spring_length = arm
	m.hero_vis.rotation.y = yaw + PI; m.party.trail = PackedVector3Array()
	for c in m.party.companions: c.node.global_position = m.hero.position + Vector3(1.2, 0, 0.8)
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://tests/shots"))
	await frames(10)
	m.tier = 2; m.apply_quality(); m._set_time(11.0)
	var t0 := Time.get_ticks_msec()
	var rb = load("res://assets/roads/road_builder.gd").new(); rb._grid(m)
	var res := []
	for r in m.ROADS:
		for i in range(1, r.size()):
			var a := Vector2(r[i-1][0], r[i-1][1]); var b := Vector2(r[i][0], r[i][1])
			var n := int(ceil(a.distance_to(b) / 4.0))
			for k in n:
				var p0 := a.lerp(b, float(k) / n); var p1 := a.lerp(b, float(k + 1) / n)
				var dir := (p1 - p0).normalized(); var side := Vector2(-dir.y, dir.x)
				for o in [-1.0, 0.0, 1.0]:
					var q0: Vector2 = p0 + side * 4.4 * o; var q1: Vector2 = p1 + side * 4.4 * o
					var h0: float = m.height(q0.x, q0.y); var h1: float = m.height(q1.x, q1.y)
					for f in [0.25, 0.5, 0.75]:
						var q: Vector2 = q0.lerp(q1, f)
						res.append([lerpf(h0, h1, f) + 0.12 - rb.th(q.x, q.y), q, atan2(dir.x, dir.y)])
	res.sort_custom(func(x, y): return x[0] < y[0])
	print("PROBE ms ", Time.get_ticks_msec() - t0, " samples ", res.size(), " buried(<0) ", res.filter(func(x): return x[0] < 0.0).size())
	var spots := []
	for x in res:
		if spots.size() >= 3: break
		var ok := true
		for s in spots: if s[1].distance_to(x[1]) < 60: ok = false
		if ok: spots.append(x); print("WORST ", x[0], " ", x[1])
	# old road mesh
	var old: MeshInstance3D
	for c in m.get_children():
		if c is MeshInstance3D and c.material_override is StandardMaterial3D and c.material_override.albedo_color.is_equal_approx(Color(0.55, 0.49, 0.40)): old = c
	print("OLD ", old)
	var views := []
	for s in spots: views.append([s[1] - Vector2(sin(s[2]), cos(s[2])) * 3.0, s[2] + PI, -0.25, 9.0])
	views.append([Vector2(-140, 222), -1.75, -0.3, 10.0])   # SW road, a bend
	views.append([Vector2(330, 0), 1.2, -0.35, 14.0])
	for k in views.size():
		var v = views[k]; place(v[0], v[1], v[2], v[3]); await frames(25); await shot("%d_before" % k)
	old.visible = false
	var t1 := Time.get_ticks_msec(); var roads: Node3D = rb.build(m, m.ROADS); m.add_child(roads)
	var tri := 0
	for c in roads.get_children(): tri += c.mesh.get_faces().size() / 3
	print("BUILD ms ", Time.get_ticks_msec() - t1, " chunks ", roads.get_child_count(), " tris(all lods) ", tri)
	for k in views.size():
		var v = views[k]; place(v[0], v[1], v[2], v[3]); await frames(25); await shot("%d_after" % k)
	quit()
