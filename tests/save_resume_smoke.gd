extends SceneTree
## Headless load: a saved in-progress volcano fight and a mainland position survive a real scene load.
## VARN_LITE=1 godot --headless --path . -s res://tests/save_resume_smoke.gd -- --nosave
const SAVE := "user://guildbound_rpg_save_v1.json"
const CFG := "user://story.cfg"
var fails := 0
var VSave
func ok(c: bool, msg: String) -> void:
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	await process_frame
	VSave = root.get_node("VSave")
	var had_save := FileAccess.file_exists(SAVE)
	var had_cfg := FileAccess.file_exists(CFG)
	var save0 := FileAccess.get_file_as_bytes(SAVE) if had_save else PackedByteArray()
	var cfg0 := FileAccess.get_file_as_bytes(CFG) if had_cfg else PackedByteArray()
	var s: Dictionary = VSave.fresh_state()
	s["p3d"] = {"zone": "village", "x": 405.0, "z": -402.0, "yaw": 0.4}
	s["story"] = {"volcano": {"state": "fight", "stage": 2, "hp": 0.5}}
	s["sea"] = {"galleon_tier": 1, "skiff_tier": 0, "discovered_ports": ["tidewrack"], "coil_beaten": false, "items": {}}
	VSave.write_state(s)
	var cf := ConfigFile.new()
	cf.set_value("story", "volcano_done", false)
	cf.save(CFG)
	var ps: PackedScene = load("res://main.tscn")
	var m := ps.instantiate()
	root.add_child(m)
	for i in 800:
		await process_frame
		if m.titan_quest != null: break
	var q = m.titan_quest
	ok(q != null, "titan quest exists after load")
	if q != null:
		ok(q.state == "fight" and q.stage == 2, "in-progress fight resumes at stage %s/%s" % [q.state, q.stage])
		ok(q.titan != null and q.titan.active and is_equal_approx(q.titan.hp / q.titan.max_hp, 0.5), "titan health fraction restored")
		m._on_play_solo()
		await process_frame
		ok(m.hero != null and Vector2(m.hero.position.x - 405.0, m.hero.position.z + 402.0).length() < 2.0, "play resumes at the volcano (%.1f, %.1f)" % [m.hero.position.x, m.hero.position.z])
		VSave.state["sea"]["aboard"] = true
		VSave.state["sea"]["ship"] = "galleon"
		VSave.state["sea"]["x"] = 1300.0
		VSave.state["sea"]["z"] = 300.0
		VSave.state["sea"]["yaw"] = -PI / 2.0
		m._on_play_solo()
		await process_frame
		ok(m.sea != null and m.sea.active and m.sea.ship != null, "sailing resume boards the ship")
		if m.sea and m.sea.ship:
			ok(Vector2(m.sea.ship.position.x - 1300.0, m.sea.ship.position.z - 300.0).length() < 1.0, "ship resumes at the saved sea position")
			ok(int(m.sea.save.galleon_tier) == 1, "sea resume keeps the ship tier")
	m.queue_free()
	for i in 5: await process_frame
	if had_save:
		var out := FileAccess.open(SAVE, FileAccess.WRITE)
		if out: out.store_buffer(save0); out.close()
	else: DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE))
	if had_cfg:
		var out2 := FileAccess.open(CFG, FileAccess.WRITE)
		if out2: out2.store_buffer(cfg0); out2.close()
	else: DirAccess.remove_absolute(ProjectSettings.globalize_path(CFG))
	print("SAVE_SMOKE %d failed" % fails)
	quit(1 if fails else 0)
