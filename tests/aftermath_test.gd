extends SceneTree
## test 24: the volcano quest aftermath is tied to the saved story flag (user://story.cfg volcano_done) and survives
## reload, quality changes and day/night; without the flag the volcano is live and no world boss is out.
## Run: VARN_LITE=1 godot --headless --path . -s res://tests/aftermath_test.gd
const CFG := "user://story.cfg"
var fails := 0; var passes := 0
func ok(c: bool, what: String) -> void:
	if c: passes += 1; print("PASS ", what)
	else: fails += 1; print("FAIL ", what)
func frames(n: int) -> void:
	for i in n: await process_frame
func _init() -> void: _run.call_deferred()
func _load_main() -> Node:
	var ps: PackedScene = load(ProjectSettings.get_setting("application/run/main_scene"))
	if current_scene: current_scene.queue_free(); await frames(3)
	var m := ps.instantiate(); root.add_child(m); current_scene = m
	for i in 600:
		await process_frame
		if m.titan_quest != null: break
	await frames(5); return m
func _check(m: Node, tag: String) -> void:
	var q = m.titan_quest
	ok(m.world_boss != null, tag + ": world boss out")
	ok(q != null and q.state == "won" and q.stage == 3, tag + ": quest won, destroyed arena stage 3")
	ok(q != null and not q.titan.visible and not q.titan.active, tag + ": quest Titan gone")
	ok(m.lava_mat() == null or is_equal_approx(float(m.lava_mat().get_shader_parameter("glow")), 0.12), tag + ": lava calm")
	ok(q != null and (q.giver == null or not q.giver.visible), tag + ": quest giver retired")
	ok(m.pool_lights.all(func(l): return is_equal_approx(l.light_energy, 0.5)), tag + ": pool lights dimmed")
func _run() -> void:
	var had := FileAccess.file_exists(CFG); var orig := FileAccess.get_file_as_string(CFG) if had else ""
	var cf := ConfigFile.new(); cf.load(CFG); cf.set_value("story", "volcano_done", false); cf.save(CFG)
	var m := await _load_main()
	ok(m.world_boss == null and m.titan_quest.state == "none" and m.titan_quest.stage == 1, "no flag: volcano live, no world boss")
	cf.set_value("story", "volcano_done", true); cf.save(CFG)
	m = await _load_main(); _check(m, "reload")
	for t in [0, 3, 1, 2]: m.tier = t; m.apply_quality(); await frames(2)
	_check(m, "after tier swaps")
	m._set_time(22.0); await frames(2); _check(m, "night")
	m._set_time(12.0); await frames(2); _check(m, "noon")
	m = await _load_main(); _check(m, "second reload")
	if had: var f := FileAccess.open(CFG, FileAccess.WRITE); f.store_string(orig)
	else: DirAccess.remove_absolute(ProjectSettings.globalize_path(CFG))
	print("AFTERMATH %d passed, %d failed" % [passes, fails]); quit(1 if fails else 0)
