extends Node
## test 17 (boss: "roof is missing" while flying over town): same-angle shots over the Stables + roof audit in the live game.
## Run: godot --path . -- --roofshots   (env ROOF_TAG=before|after)
var m: Node
const OUT := "/workspace/shots/godot17/"
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var tag := OS.get_environment("ROOF_TAG"); if tag == "": tag = "after"
	await frames(10)
	m.time_mode = 1; m._set_time(12.0)
	m.cheats.role_provider = func() -> String: return "owner"
	m.cheats.request("fly", true); m.set_flight(true); await frames(5)
	var st = null
	for b in m.buildings: if b.id == "stables": st = b
	var c: Vector3 = st.node.global_transform * st.aabb.get_center()
	var hc := Camera3D.new(); hc.fov = 62; hc.far = 4000; m.add_child(hc)
	for alt in [12.0, 40.0]:
		m.fly_alt = alt; m.hero.position = Vector3(c.x + 1.0, m.height(c.x, c.z) + alt, c.z); await frames(40)
		var hp: Vector3 = m.hero.global_position
		hc.look_at_from_position(hp + Vector3(0, 14, 16), hp + Vector3(0, -4, -6), Vector3.UP); hc.current = true
		await frames(4)
		get_viewport().get_texture().get_image().save_png(OUT + "%s_stables_%dm.png" % [tag, int(alt)])
		m.cam.current = true
	# audit: hero hovering over every building (just above the roof, 50 m, 3000 m) -> no roof may be hidden
	var fails := 0
	for b in m.buildings:
		var top: Vector3 = b.node.global_transform * Vector3(b.aabb.get_center().x, b.aabb.end.y, b.aabb.get_center().z)
		for dh in [1.5, 50.0, 3000.0]:
			m.hero.position = top + Vector3(0, dh, 0); m.fly_alt = top.y + dh - m.height(top.x, top.z)
			await get_tree().physics_frame; await frames(1)
			m.hero.position = top + Vector3(0, dh, 0)
			await frames(1)
			for rf in b.roofs:
				if not rf.is_visible_in_tree():
					fails += 1; print("ROOF HIDDEN ", b.id, " hero +", dh, " m over the roof")
	# filler + harbor buildings must stay drawn from any height (last LOD band open-ended)
	for f in m.fillers:
		var last_end := -1.0
		for mi in (f.node as Node).find_children("*", "GeometryInstance3D", true, false):
			if (mi as GeometryInstance3D).visibility_range_begin > 0.0: last_end = (mi as GeometryInstance3D).visibility_range_end
		if last_end != 0.0: fails += 1; print("FILLER LOD ends at ", last_end, " m: ", f.id)
	print("ROOFSHOTS %d failed" % fails)
	get_tree().quit()
