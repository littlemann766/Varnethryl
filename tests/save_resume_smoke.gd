extends SceneTree
## Full main-scene relaunch: hero model, outside-town position, interior, and sea.
## Each case is written to disk, read back with VSave.load_state (the autoload path), then a new
## main.tscn is initialized. The hero is whatever _hook_ui restored. Movement happens only when
## VUI.play_solo fires, which is the Play path connected in _hook_ui.
## Run: VARN_LITE=1 godot --headless --path . -s res://tests/save_resume_smoke.gd -- --nosave
const SAVE := "user://guildbound_rpg_save_v1.json"
const CFG := "user://story.cfg"
const TOWN := Vector2(-6.0, 26.0)
var fails := 0
var VSave
func ok(c: bool, msg: String) -> void:
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1
func _initialize() -> void: _run.call_deferred()
func _frames(n: int) -> void:
	for i in n: await process_frame
func _run() -> void:
	await process_frame
	VSave = root.get_node("VSave")
	var had_save := FileAccess.file_exists(SAVE)
	var had_cfg := FileAccess.file_exists(CFG)
	var save0 := FileAccess.get_file_as_bytes(SAVE) if had_save else PackedByteArray()
	var cfg0 := FileAccess.get_file_as_bytes(CFG) if had_cfg else PackedByteArray()
	VSave.clear_session()
	var cf := ConfigFile.new()
	cf.set_value("story", "volcano_done", false)
	cf.save(CFG)
	await _case_outside()
	await _case_interior()
	await _case_sea()
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

func _base() -> Dictionary:
	var s: Dictionary = VSave.fresh_state()
	s["sea"] = {"galleon_tier": 1, "skiff_tier": 0, "discovered_ports": ["tidewrack"], "coil_beaten": false, "items": {}}
	return s

func _boot(s: Dictionary) -> Node:
	VSave.write_state(s)
	VSave.clear_session()
	# Same read the autoload uses on the next process: discard the dict we just built.
	VSave.state = VSave.load_state()
	var ps: PackedScene = load("res://main.tscn")
	var m := ps.instantiate()
	root.add_child(m)
	await _frames(2)
	return m

func _play(m: Node) -> void:
	var ui = root.get_node("VUI")
	var connected: bool = ui.play_solo.is_connected(Callable(m, "_on_play_solo"))
	ok(connected, "Play Solo is wired to the world resume")
	# Before Play, the body is still the town start. Play is what moves it.
	var before := Vector2(m.hero.position.x, m.hero.position.z)
	ok(before.distance_to(TOWN) < 3.0, "before Play the body is still at the town start (%.1f, %.1f)" % [before.x, before.y])
	ui.play_solo.emit()
	await _frames(8)

func _hero_model(m: Node, id: String) -> void:
	ok(m.party != null and str(m.party.hero_id) == id, "world init restored hero %s (got %s)" % [id, m.party.hero_id if m.party else "?"])
	var path := ""
	if m.party and m.party.rig and m.party.rig.model:
		path = str(m.party.rig.model.scene_file_path)
	ok(path.find(id) >= 0, "hero appearance loaded %s (scene %s)" % [id, path])

func _shutdown(m: Node) -> void:
	m.queue_free()
	await _frames(6)

func _case_outside() -> void:
	print("SMOKE CASE outside-town")
	var s := _base()
	VSave.remember_hero(s, "darius")
	s["p3d"] = {"zone": "village", "x": 1000.0, "z": -200.0, "yaw": 0.7}
	var m := await _boot(s)
	_hero_model(m, "darius")
	await _play(m)
	var at := Vector2(m.hero.position.x, m.hero.position.z)
	ok(at.distance_to(Vector2(1000.0, -200.0)) < 2.0, "Play resumed outside town at (%.1f, %.1f)" % [at.x, at.y])
	ok(at.distance_to(TOWN) > 100.0, "outside-town resume did not stay in town")
	await _shutdown(m)

func _case_interior() -> void:
	print("SMOKE CASE interior")
	var s := _base()
	VSave.remember_hero(s, "elira")
	s["p3d"] = {"zone": "village", "x": -6.0, "z": 26.0, "yaw": 0.0}
	s["interior"] = {"inside": true, "id": "inn", "x": 1.25, "z": -1.5, "y": 0.2, "yaw": 0.4}
	var m := await _boot(s)
	_hero_model(m, "elira")
	await _play(m)
	var inn_on: bool = m.interiors != null and m.interiors.active() and str(m.interiors.cur_bld.get("id", "")) == "inn"
	ok(inn_on, "Play re-entered the inn (active=%s id=%s)" % [m.interiors.active() if m.interiors else false, m.interiors.cur_bld.get("id", "") if m.interiors else ""])
	if inn_on:
		var local: Vector3 = (m.interiors.cur.node as Node3D).to_local(m.hero.global_position)
		ok(Vector2(local.x - 1.25, local.z + 1.5).length() < 1.0, "inn local position restored (%.2f, %.2f)" % [local.x, local.z])
	ok(str(m.party.hero_id) == "elira", "interior relaunch kept Elira")
	await _shutdown(m)

func _case_sea() -> void:
	print("SMOKE CASE sea")
	var s := _base()
	VSave.remember_hero(s, "pip")
	s["p3d"] = {"zone": "village", "x": 405.0, "z": -402.0, "yaw": 0.2}
	s["sea"]["aboard"] = true
	s["sea"]["ship"] = "galleon"
	s["sea"]["x"] = 1300.0
	s["sea"]["z"] = 300.0
	s["sea"]["yaw"] = -PI / 2.0
	var m := await _boot(s)
	_hero_model(m, "pip")
	await _play(m)
	var sailing: bool = m.sea != null and m.sea.active and m.sea.ship != null
	ok(sailing, "Play boarded the saved ship")
	if sailing:
		var ship_at := Vector2(m.sea.ship.position.x, m.sea.ship.position.z)
		ok(ship_at.distance_to(Vector2(1300.0, 300.0)) < 1.0, "ship resumed at (%.1f, %.1f)" % [ship_at.x, ship_at.y])
		ok(int(m.sea.save.get("galleon_tier", -1)) == 1, "sea resume kept the galleon tier")
		var hero_at := Vector2(m.hero.global_position.x, m.hero.global_position.z)
		ok(hero_at.distance_to(TOWN) > 100.0, "sea resume did not leave the hero in town")
	ok(str(m.party.hero_id) == "pip", "sea relaunch kept Pip")
	await _shutdown(m)
