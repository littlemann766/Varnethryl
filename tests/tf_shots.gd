extends Node
## test 23 (from Beth's tools/tf_shots.gd): terrain/flower views at High + Low. Run: godot --path . -- --tfshots (env TF_OUT, TF_TAG, TF_ONLY)
var m: Node
const VIEWS := [
	# name, hero pos, yaw, pitch
	["meadow_s", Vector3(40, 0, 262), PI * 0.9, -0.12],
	["meadow_e", Vector3(255, 0, 60), -PI * 0.4, -0.15],
	["road_w", Vector3(-262, 0, 14), PI * 0.55, -0.12],
	["road_n", Vector3(-30, 0, -268), 0.6, -0.12],
	["farm", Vector3(-245, 0, -245), 0.8, -0.15],
	["lake", Vector3(198, 0, -160), -PI * 0.25, -0.18],
	["pond", Vector3(-110, 0, 136), 0.0, -0.3],
	["garden", Vector3(-48, 0, 76), PI * 0.6, -0.2],
	["volcano_edge", Vector3(230, 0, -262), -0.89, -0.02],
	["hills_far", Vector3(-60, 0, -440), 2.5, -0.05],
	["grass_edge", Vector3(198, 0, 60), -PI / 2, -0.15],
	["map_edge", Vector3(150, 0, 950), PI * 0.9, -0.05],
	["town", Vector3(-6, 0, 30), PI, -0.15]]
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	var out := OS.get_environment("TF_OUT"); var tag := OS.get_environment("TF_TAG")
	DirAccess.make_dir_recursive_absolute(out)
	var only := OS.get_environment("TF_ONLY")
	while not m.warmed: await get_tree().process_frame
	await frames(10)
	if OS.get_environment("TF_BAKE") != "": TerrainFlowers.bake_to(OS.get_environment("TF_BAKE"))
	var rep := []
	for q in [2, 0]:
		for v in VIEWS:
			if only != "" and not (only.split(",") as Array).has(v[0]): continue
			if FileAccess.file_exists("%s/%s_%s_%s.jpg" % [out, v[0], ["Low", "Med", "High", "Ultra"][q], tag]): continue   # resumable (shared box OOM kills)
			m.tier = q; m.apply_quality(); m._set_time(10.5)
			if OS.get_environment("TF_GROUND") != "": m.terrain_mat.set_shader_parameter("beth_detail", q >= 2)
			var pos: Vector3 = v[1]; m.hero.position = pos; m.hero.position.y = m.ground_y(pos.x, pos.z) + 0.1
			m.yaw = v[2]; m.pitch = v[3]; m.hero_vis.rotation.y = v[2]
			await frames(25)
			var dc := 0.0; var pr := 0.0
			for i in 6:
				await get_tree().process_frame
				dc += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME); pr += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
			var tn: String = ["Low", "Med", "High", "Ultra"][q]
			get_viewport().get_texture().get_image().save_jpg("%s/%s_%s_%s.jpg" % [out, v[0], tn, tag], 0.85)
			var fl := 0; var flt := 0
			var cp: Vector3 = get_viewport().get_camera_3d().global_position
			if _has_flowers():
				for arr in [TerrainFlowers.lod0, TerrainFlowers.lod1]:
					for mmi in arr:
						if not mmi.visible: continue
						var c: Vector3 = mmi.multimesh.get_aabb().get_center()
						var d := Vector2(c.x - cp.x, c.z - cp.z).length()
						if d < mmi.visibility_range_end + 34.0 and d >= mmi.visibility_range_begin - 34.0: fl += 1; flt += mmi.multimesh.visible_instance_count * (8 if arr == TerrainFlowers.lod0 else 4)
			rep.append("%s %s %s draw_calls=%d prims=%d flower_chunks_in_range=%d flower_tris_upper_bound=%d" % [tag, tn, v[0], int(dc / 6), int(pr / 6), fl, flt])
			print(rep[-1])
	var f := FileAccess.open("%s/report_%s.txt" % [out, tag], FileAccess.READ_WRITE if FileAccess.file_exists("%s/report_%s.txt" % [out, tag]) else FileAccess.WRITE); f.seek_end(); f.store_string("\n".join(rep) + "\n")
	get_tree().quit()

func _has_flowers() -> bool:
	return ProjectSettings.get_global_class_list().any(func(c): return c["class"] == "TerrainFlowers") and TerrainFlowers.root != null
