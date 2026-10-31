extends Node
## test 18 (boss: destroy the crystals without letting others fly). A ground-only player (feet always on the
## terrain, no fly cheat) walks up to the Titan and uses only melee (slot 0) and ranged skills (slot 1) from
## ground height. Must break every crystal: legs first -> kneel -> upper crystals, repeating cycles as needed.
## Shots: standing leg crystals + kneeling. Run: WB_SCRIPT=res://tests/wb_ground_crystals_test.gd godot res://tests/wb_lite.tscn
var m: Node
const OUT := "/workspace/shots/godot18/"
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	m.cheat = {"fly": false, "god": true}
	var hero := Node3D.new(); m.add_child(hero); m.hero = hero
	m.spawn_world_boss(false); await frames(5)
	var wb = m.world_boss
	wb.place_at(5); await frames(30)
	var fails := 0; var max_hero_air := 0.0
	var broken_ever := {}
	var shots := {}
	var cam: Camera3D = m.cam
	var t0 := Time.get_ticks_msec()
	while broken_ever.size() < wb.crystals.size() and Time.get_ticks_msec() - t0 < 600000:
		await frames(1)
		if wb.state in ["idle", "windup", "arrive", "release", "stagger"]: pass
		# nearest available crystal
		var tgt = null; var td := 1e9
		for c in wb.crystals:
			if not wb.crystal_available(c): continue
			var cp: Vector3 = c.node.global_position
			var d := Vector2(cp.x - hero.position.x, cp.z - hero.position.z).length()
			if d < td: td = d; tgt = c
		if tgt == null: continue
		var cp: Vector3 = tgt.node.global_position
		# walk on the ground to a spot under/next to it (teleport-walk: always at terrain height)
		var off := Vector3(cp.x - wb.position.x, 0, cp.z - wb.position.z).normalized() * 4.0
		var gp := Vector3(cp.x + off.x, 0, cp.z + off.z); gp.y = m.height(gp.x, gp.z)
		hero.position = gp
		max_hero_air = maxf(max_hero_air, hero.position.y - m.height(gp.x, gp.z))
		var eye := hero.position + Vector3(0, 1.5, 0)
		var slot := 0 if eye.distance_to(cp) < wb.MELEE_R else 1
		if wb.state != "kneel" and tgt.name.begins_with("ankle") and not shots.has("stand"):
			shots["stand"] = true
			var bp: Vector3 = wb.global_position; var side: Vector3 = wb._fwd().cross(Vector3.UP).normalized()
			var cp1: Vector3 = bp + side * 70.0 + wb._fwd() * 35.0; cp1.y = m.height(cp1.x, cp1.z) + 4.0
			cam.look_at_from_position(cp1, Vector3(bp.x, m.height(bp.x, bp.z) + 22.0, bp.z), Vector3.UP); await frames(4)
			get_viewport().get_texture().get_image().save_png(OUT + "crystals_standing_legs.png")
		if wb.state == "kneel" and wb.t_state <= 6.0 and not shots.has("kneel"): continue   # let him settle for the shot
		var c = wb.hit_from(eye, slot)
		if c != null and c.broken: broken_ever[c.name] = slot
		if wb.state == "kneel" and wb.t_state > 6.0 and not shots.has("kneel"):
			shots["kneel"] = true
			var bp: Vector3 = wb.global_position; var side: Vector3 = wb._fwd().cross(Vector3.UP).normalized()
			var cp2: Vector3 = bp + side * 85.0 + wb._fwd() * 60.0; cp2.y = m.height(cp2.x, cp2.z) + 4.0
			cam.look_at_from_position(cp2, Vector3(bp.x, m.height(bp.x, bp.z) + 15.0, bp.z), Vector3.UP); await frames(4)
			get_viewport().get_texture().get_image().save_png(OUT + "crystals_kneeling.png")
			var away: Vector3 = Vector3(hero.position.x - bp.x, 0, hero.position.z - bp.z).normalized()
			var cp3: Vector3 = hero.position + away * 30.0; cp3.y = m.height(cp3.x, cp3.z) + 1.7
			cam.look_at_from_position(cp3, cp, Vector3.UP); await frames(4)
			get_viewport().get_texture().get_image().save_png(OUT + "crystals_kneeling_ground_view.png")
	print("GROUNDCRYSTALS broken=%d/%d kneels=%d hero_max_height_above_ground=%.2f fly_cheat=%s state=%s" % [broken_ever.size(), wb.crystals.size(), wb.kneels, max_hero_air, m.cheat.get("fly"), wb.state])
	print("  how: ", broken_ever)
	if broken_ever.size() < wb.crystals.size(): fails += 1; print("FAIL not every crystal broken from the ground")
	if max_hero_air > 0.01: fails += 1; print("FAIL hero left the ground")
	if wb.kneels < 1: fails += 1; print("FAIL no kneel")
	print("WBGROUNDCRYSTALS %d failed" % fails)
	get_tree().quit(fails)
