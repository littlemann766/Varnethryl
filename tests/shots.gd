extends SceneTree
## Screenshots: VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json xvfb-run -a godot -s res://tests/shots.gd
var m: Node
func _init() -> void:
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	_run.call_deferred()

func frames(n: int) -> void:
	for i in n: await process_frame

func shot(name: String) -> void:
	await frames(3)
	root.get_viewport().get_texture().get_image().save_png("res://tests/shots/%s.png" % name)
	print("SHOT ", name, " dc=", Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))

func place(p: Vector3, yaw: float, pitch: float) -> void:
	m.hero.position = Vector3(p.x, m.height(p.x, p.z) + 0.1, p.z); m.yaw = yaw; m.pitch = pitch
	m.hero_vis.rotation.y = yaw + PI
	m.party.trail = PackedVector3Array()
	for c in m.party.companions: c.node.global_position = m.hero.position + Vector3(1.2, 0, 0.8)

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://tests/shots"))
	await frames(10)
	m.tier = 2; m.apply_quality(); m._set_time(11.0)
	var party: Party = m.party
	# 1. Owner + Pip in the plaza, close camera
	place(Vector3(-6, 0, 30), 0.6, -0.15); m.cam_arm.spring_length = 4.0
	await frames(30); await shot("01_owner_pip_plaza")
	# 2. walking (companion follows on trail)
	for i in 60:
		m.joy_vec = Vector2(0, -1); await process_frame
	await shot("02_walking_follow"); m.joy_vec = Vector2.ZERO
	# 3. roster lineup
	var line := Node3D.new(); m.add_child(line)
	place(Vector3(-6, 0, 30), 0.0, -0.02); m.cam_arm.spring_length = 7.5
	party.rig.visible = false
	for c in party.companions: c.node.visible = false
	var base := Vector3(-6, 0, 24)
	var x := -6.9
	for id in HeroRoster.ORDER:
		var r := CharacterRig.new().setup(HeroRoster.model(id), HeroRoster.height(id))
		line.add_child(r); r.position = Vector3(base.x + x, m.height(base.x + x, base.z), base.z); r.rotation.y = PI; x += 0.6
	await frames(20); await shot("03_roster_lineup")
	line.queue_free(); m.cam_arm.spring_length = 6.0; party.rig.visible = true
	for c in party.companions: c.node.visible = true
	# 4. switch to Wren, Pip + Owner follow
	party.set_hero("wren"); party._set_companions(["owner", "pip"])
	place(Vector3(-6, 0, 30), 0.3, -0.2)
	await frames(20); await shot("04_wren_with_owner_pip")
	party.set_hero("owner"); party._set_companions(["pip"])
	# 5. frost trolls (3x) vs Owner
	place(Vector3(44, 0, 222), PI - 0.1, -0.08); m.cam_arm.spring_length = 9.0
	await frames(40)
	party.combat.use(0); await frames(6); await shot("05_frost_trolls_3x")
	# 6. Ashen Titan 6x
	place(Vector3(-66, 0, 238), PI - 0.1, 0.1); m.cam_arm.spring_length = 10.0
	await frames(40); await shot("06_ashen_titan_6x")
	# 7. Volcano Titan 11x
	place(Vector3(405, 0, -365), 0.0, 0.12); m.cam_arm.spring_length = 14.0
	await frames(90); await shot("07_volcano_titan_11x")
	for e in party.director.enemies: print("ENEMY ", e.type_id, " state=", e.state, " hp=", e.hp, "/", e.max_hp)
	quit()
