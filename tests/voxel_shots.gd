extends SceneTree
## voxel-heroes: shots of the voxel heroes (idle/walk/run), guards in town and the villain, plus a draw-time
## pipeline compile count after warm-up. VK_ICD_FILENAMES=.../lvp_icd.json xvfb-run -a godot --path . -s res://tests/voxel_shots.gd
var m: Node
var OUT := "/workspace/shots/voxel1"
var dc0 := 0.0
func _init() -> void:
	m = load("res://main.tscn").instantiate(); root.add_child(m); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await process_frame
func comp() -> float: return Performance.get_monitor(Performance.PIPELINE_COMPILATIONS_DRAW)
func shot(name: String) -> void:
	await frames(3)
	root.get_viewport().get_texture().get_image().save_png("%s/%s.png" % [OUT, name])
	print("SHOT %s dc=%d prims=%d drawcompiles_since_warm=%d" % [name, Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), comp() - dc0])
func place(p: Vector3, yaw: float, pitch: float) -> void:
	m.hero.position = Vector3(p.x, m.height(p.x, p.z) + 0.1, p.z); m.yaw = yaw; m.pitch = pitch
	m.hero_vis.rotation.y = yaw + PI
	m.party.trail = PackedVector3Array()
	for c in m.party.companions: c.node.global_position = m.hero.position + Vector3(1.2, 0, 0.8)
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var t := 0
	while not m.warmed and t < 6000: await process_frame; t += 1
	await frames(20)
	m._set_time(11.0)
	dc0 = comp(); print("WARMED tier=", m.tier, " frames=", t)
	var party: Party = m.party
	party._set_companions([])
	for id in ["owner", "selene", "darius"]:
		party.set_hero(id)
		place(Vector3(-6, 0, 30), 0.35, -0.12); m.cam_arm.spring_length = 3.6
		await frames(30); await shot("%s_idle" % id)
		# walk: low stick -> real walk speed; run: full stick
		for mode in [["walk", 0.25], ["run", 1.0]]:
			place(Vector3(-6, 0, 30), 0.35, -0.12)
			for i in 45:
				m.joy_vec = Vector2(0, -mode[1]); await process_frame
			print("SPEED %s %s v=%.2f m/s blend=%.2f playback=%.2f" % [id, mode[0], Vector2(m.hero.velocity.x, m.hero.velocity.z).length(), party.rig.tree.get("parameters/loco/blend_position"), party.rig.tree.get("parameters/loco_ts/scale")])
			m.yaw += 0.0
			await shot("%s_%s" % [id, mode[0]])
			m.joy_vec = Vector2.ZERO
		await frames(10)
	party.set_hero("owner")
	# guards: one at the south gate (inside), camera from the plaza side
	if m.guards:
		for i in [0, 1]:
			var g: Node3D = m.guards.guards[i].node
			var gp := g.global_position
			place(gp + Vector3(0, 0, -6), 0.0, -0.1); m.cam_arm.spring_length = 4.5
			await frames(60); await shot("guards_%d" % i)
		print("GUARDS ", m.guards.guards.size())
	# villain outside the east gate
	for e in party.director.living():
		if e.type_id == "holyknight_villain":
			place(e.global_position + Vector3(-9, 0, 0), -PI / 2, -0.08); m.cam_arm.spring_length = 4.0
			await frames(15); await shot("villain_idle")
			await frames(50); await shot("villain_chase")
	print("DRAW_COMPILES_AFTER_WARM ", comp() - dc0)
	quit(0)
