extends Node
## test 22 (Beth's exterior weathering pass): street shots of card2 exteriors at noon and 22:30 + compile count.
## Run: godot --path . -- --extshots   (env EXT_OUT=dir; VARN_NO_EXT=1 = without the pass, for "before")
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	while not m.warmed: await get_tree().process_frame
	var out := OS.get_environment("EXT_OUT") if OS.get_environment("EXT_OUT") != "" else "/workspace/shots/godot22/exterior/x"
	DirAccess.make_dir_recursive_absolute(out)
	var c := Camera3D.new(); c.fov = 60; c.far = 2000; m.add_child(c); c.current = true
	var picks := ["inn", "townhall", "bakery", "smithy", "guildhall", "temple"]
	var pc0: Array = m._pc(); var lines := []
	for h in [12.0, 22.5]:
		m.time_mode = 1; m._set_time(h); await frames(3)
		for b in m.buildings:
			if not picks.has(b.id): continue
			var n: Node3D = b.node; var dl: Vector3 = m.interiors.door_local(b)
			var eye: Vector3 = n.global_transform * (dl + Vector3(6.0, 2.0, 16.0)); eye.y = m.height(eye.x, eye.z) + 2.0
			c.look_at_from_position(eye, n.global_transform * Vector3(0, 5.0, dl.z * 0.3), Vector3.UP)
			await frames(6)
			get_viewport().get_texture().get_image().save_jpg("%s/%s_%s.jpg" % [out, b.id, "day" if h < 18 else "night"], 0.85)
		# a filler street
		if m.fillers.size() > 20:
			var f = m.fillers[12]; var fp: Vector3 = f.node.global_position
			c.look_at_from_position(fp + f.node.global_transform.basis * Vector3(14, 0, 22) + Vector3(0, 2.2, 0), fp + Vector3(0, 4, 0), Vector3.UP)
			await frames(6); get_viewport().get_texture().get_image().save_jpg("%s/fillers_%s.jpg" % [out, "day" if h < 18 else "night"], 0.85)
	var pc1: Array = m._pc()
	var em := 0.0
	for e in m.emissive_mats: em = maxf(em, float(e.emission_energy_multiplier))
	lines.append("EXTSHOTS ext_tier=%s emissive_entries=%d night_emission=%.2f draw_compiles=%d spec=%d" % [m._ext_tier, m.emissive_mats.size(), em, int(pc1[0] - pc0[0]), int(pc1[1] - pc0[1])])
	print("\n".join(lines)); FileAccess.open(out + "/report.txt", FileAccess.WRITE).store_string("\n".join(lines) + "\n")
	get_tree().quit()
