extends Node
## test 31: run / walk mid-stride + attack (front 3/4) for the hands-fix heroes; guards vs troll at the South Gate. -- --vox31
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	var out := "/workspace/shots/voxel31/"; DirAccess.make_dir_recursive_absolute(out); var tag := OS.get_environment("VOX_TAG")
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0); m.party._set_companions([])
	var base := Vector3(-6, 0, 30); base.y = m.height(base.x, base.z); m.hero.position = base + Vector3(0, 0, 40)
	var cam := Camera3D.new(); cam.fov = 40; m.add_child(cam)
	for id in ([] if tag == "guards" else ["aldric", "rowan", "seraphine", "garruk", "darius", "selene"]):
		var r := CharacterRig.new().setup(HeroRoster.model(id), HeroRoster.height(id)); m.add_child(r); r.global_position = base
		var rs: Array = HeroRoster.ROOT_SPEED[id]; r.set_root_speeds(rs[0], rs[1], 6.0)
		cam.look_at_from_position(base + Vector3(2.2, 1.3, -3.6), base + Vector3(0, 0.95, 0), Vector3.UP); cam.current = true
		for mode in [["walk", rs[0]], ["run", rs[1]]]:
			r.set_move_mps(0.0); await frames(20)
			r.set_move_mps(mode[1]); await frames(47)   # same frame count before/after -> comparable stride phase
			get_viewport().get_texture().get_image().save_png(out + "%s_%s_%s.png" % [id, mode[0], tag]); print("V31 ", id, mode[0])
		r.set_move_mps(0.0); await frames(20); r.play_attack("attack", 1.0); await frames(14)
		get_viewport().get_texture().get_image().save_png(out + "%s_attack_%s.png" % [id, tag]); print("V31 ", id, " attack")
		r.queue_free(); await frames(2)
	# guards vs a stone troll at the South Gate
	if tag in ["after", "guards"] and m.guards:
		cam.current = false
		var d: EnemyDirector = m.party.director
		for e in d.living(): e.kill_now(Vector3.ZERO)
		var e: Enemy = d.spawn("stonetroll", Vector3(3, 0, 210), m.hero); e.target = m.hero; e.set_state("chase")
		m.hero.position = Vector3(-10, m.height(-10, 160), 160); m.yaw = 0.25 + PI; m.pitch = -0.18; m.cam_arm.spring_length = 7.0
		m.hero_vis.rotation.y = m.yaw + PI
		var t := 0
		while e.alive() and t < 1800:
			await get_tree().process_frame; t += 1; m.party.combat.hp = m.party.combat.max_hp
			if t > 30 and m.guards.guards.any(func(g): return g.tgt == e and g.atk_t > 0.6):
				cam.look_at_from_position(e.global_position + Vector3(9, 5, 11), e.global_position + Vector3(0, 1.2, 0), Vector3.UP); cam.current = true
				await frames(6); get_viewport().get_texture().get_image().save_png(out + "guards_vs_troll_gate.png"); print("V31 guards"); break
	get_tree().quit(0)
