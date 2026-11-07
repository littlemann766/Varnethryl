extends SceneTree
## Save, resume and quest-progress regressions. No world scene.
## godot --headless --path . -s res://tests/save_reliability_test.gd
var fails := 0
var passes := 0
var VSave
var VPrefs
var VUI
func ok(c: bool, msg: String) -> void:
	if c: passes += 1; print("PASS ", msg)
	else: fails += 1; print("FAIL ", msg)
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	await process_frame
	VSave = root.get_node("VSave")
	VPrefs = root.get_node("VPrefs")
	VUI = root.get_node("VUI")
	var d := "user://save_reliability/"
	DirAccess.make_dir_recursive_absolute(d)
	for f in DirAccess.get_files_at(d): DirAccess.remove_absolute(d + f)
	VSave.dir = d
	if VUI and VUI.has_method("show_title"): VUI.show_title()
	_save_roundtrip()
	_invalid_and_partial()
	_snapshot_keeps_memory()
	_position_and_sea()
	_hero_and_place()
	_quest_progress()
	_corrupt_is_kept()
	_session_and_prefs()
	_fog_and_layout()
	print("SAVE_RELIABILITY %d passed, %d failed" % [passes, fails])
	quit(1 if fails else 0)

func _write_raw(obj) -> void:
	var f := FileAccess.open(VSave.save_path(), FileAccess.WRITE)
	f.store_string(JSON.stringify(obj))
	f.close()

func _save_roundtrip() -> void:
	ok(VSave.read_save().status == "none", "missing save is none and does not invent a file")
	ok(not FileAccess.file_exists(VSave.save_path()), "none does not create a file")
	var s: Dictionary = VSave.fresh_state()
	s.questStep = 4
	s["futureMod"] = {"keep": true}
	ok(VSave.write_state(s), "first write")
	ok(VSave.write_state(VSave.state), "second write replaces the file")
	var st: Dictionary = VSave.read_save().state
	ok(st.questStep == 4 and st.futureMod.keep == true and st.gold == 1250 and st.party == [0, 1, 2], "unknown keys and questStep survive a rewrite")
	ok(not FileAccess.file_exists(VSave.save_path() + ".tmp"), "temp save file is not left behind")

func _invalid_and_partial() -> void:
	_write_raw({"version": 1, "gold": 4242, "questStep": 3, "futureMod": 7})
	var r: Dictionary = VSave.read_save()
	ok(r.status == "ok" and r.state.gold == 4242 and r.state.questStep == 3 and r.state.futureMod == 7, "version-1 save missing gear/party still loads")
	ok(r.state.party == [0, 1, 2] and r.state.gear is Array and r.state.gear.size() == 5, "missing party and gear filled from defaults")
	_write_raw({"version": 1, "gold": "lots", "gear": [null, {"id": "keep"}], "party": [1.0, 1.0, 4.0, 9.0], "unlocked": [0.0, 1.0, 4.0], "active": 9.0, "p3d": {"x": "no", "z": 1}})
	r = VSave.read_save()
	ok(r.status == "ok" and r.state.gold == 1250, "non-numeric gold falls back to the default instead of failing the save")
	ok(r.state.party == [1, 4] and int(r.state.active) == 1, "float party ids are deduped and an active hero outside the party is corrected")
	ok(r.state.gear.size() == 1 and r.state.gear[0].id == "keep", "null gear entries dropped, real items kept")
	ok(VSave.read_pos(r.state) == null, "non-numeric position is not resumed")
	var before := FileAccess.get_file_as_string(VSave.save_path())
	_write_raw({"version": 2, "gold": 9, "gear": [], "party": [0], "unlocked": [0]})
	ok(VSave.read_save().status == "corrupt", "version 2 is not treated as a version 1 save")
	ok(not VSave.write_snapshot({"x": 1, "z": 2, "yaw": 0}), "autosave does not overwrite a future-version file")
	ok(FileAccess.get_file_as_string(VSave.save_path()) == JSON.stringify({"version": 2, "gold": 9, "gear": [], "party": [0], "unlocked": [0]}), "future-version bytes unchanged")
	ok(before.begins_with("{"), "partial save was written before the version check")

func _snapshot_keeps_memory() -> void:
	var s: Dictionary = VSave.fresh_state()
	ok(VSave.write_state(s), "baseline save")
	VSave.state.gold = 7777
	VSave.state["story"] = {"volcano": {"state": "fight", "stage": 2, "hp": 0.25}, "extra": 1}
	ok(VSave.write_snapshot({"x": 405.0, "z": -402.0, "yaw": 0.5, "hero": 0}), "snapshot of the volcano crater")
	var st: Dictionary = VSave.read_save().state
	ok(st.gold == 7777, "autosave does not roll in-memory gold back to the older disk copy")
	ok(st.story.extra == 1 and st.story.volcano.state == "fight" and int(st.story.volcano.stage) == 2, "autosave keeps quest progress that was not yet the disk copy")
	ok(is_equal_approx(float(st.p3d.x), 405.0) and is_equal_approx(float(st.p3d.z), -402.0), "crater position stored")

func _position_and_sea() -> void:
	var crater := {"p3d": {"zone": "village", "x": 405.0, "z": -402.0, "yaw": 0.4}}
	var mountain := {"p3d": {"zone": "village", "x": 1000.0, "z": -200.0, "yaw": 0.0}}
	ok(VSave.read_pos(crater, 555.0) != null, "volcano crater is inside the old 555 m box")
	ok(VSave.read_pos(mountain, 555.0) == null, "mountain at 1000 m was rejected by the old box")
	ok(VSave.read_pos(mountain, VSave.MAINLAND_HALF) != null, "mountain resumes inside the 1200 m mainland")
	ok(VSave.read_pos({"p3d": {"x": 999, "z": 0}}) == null, "default 60 m proto box still rejects 999")
	ok(VSave.read_pos({"p3d": {"x": NAN, "z": 0, "zone": "village"}}) == null, "NaN position rejected")
	ok(VSave.read_pos({"p3d": {"x": 1, "z": INF}}) == null, "infinite position rejected")
	var s: Dictionary = VSave.fresh_state()
	s["sea"] = {"galleon_tier": 2, "skiff_tier": 1, "discovered_ports": ["tidewrack", "gullhaven"], "coil_beaten": true, "items": {"Driftwood": 3}}
	s["p3d"] = {"zone": "village", "x": 405.0, "z": -402.0, "yaw": 1.0}
	ok(VSave.write_state(s), "save with sea upgrades and a land position")
	ok(VSave.write_snapshot({"at_sea": true, "x": 1300.0, "z": 300.0, "yaw": -1.57, "ship": "galleon", "hero": 0}), "sailing snapshot")
	var st: Dictionary = VSave.read_save().state
	ok(is_equal_approx(float(st.p3d.x), 405.0) and is_equal_approx(float(st.p3d.z), -402.0), "sailing does not replace the mainland resume point")
	ok(st.sea.aboard == true and int(st.sea.galleon_tier) == 2 and st.sea.coil_beaten == true and st.sea.discovered_ports.has("gullhaven"), "ship position stored beside the existing sea progress")
	var sea = VSave.read_sea_resume(st)
	ok(sea != null and sea.kind == "galleon" and is_equal_approx(float(sea.x), 1300.0), "sea resume reads the ship")
	ok(VSave.read_sea_resume(VSave.fresh_state()) == null, "a save with no voyage stays on land")
	ok(VSave.write_snapshot({"x": 20000.0, "z": 20000.0, "yaw": 0.0}), "out-of-range land coordinate is not a failed save")
	st = VSave.read_save().state
	ok(is_equal_approx(float(st.p3d.x), 405.0) and st.sea.aboard == true, "unreadable world coordinate does not clobber land or the voyage")
	ok(VSave.write_snapshot({"x": 12.0, "z": -6.0, "yaw": 0.2, "hero": 1, "qstate": "active"}), "return to land")
	st = VSave.read_save().state
	ok(st.sea.aboard == false and int(st.sea.galleon_tier) == 2 and is_equal_approx(float(st.p3d.x), 12.0), "docking clears aboard and keeps ship upgrades")
	ok(st.story.volcano.state == "active", "quest step carried in the same autosave")
	ok(not VSave.write_snapshot({"x": "nope", "z": 1}), "non-numeric snapshot rejected")

func _hero_and_place() -> void:
	ok(VSave.skin_for_index(0) == "aldric" and VSave.data_index_for_skin("rowan") == 4 and VSave.data_index_for_skin("owner") == -1, "hero index map matches the roster")
	var s: Dictionary = VSave.fresh_state()
	s["p3d"] = {"zone": "village", "x": 12.0, "z": 4.0, "yaw": 0.2}
	VSave.remember_hero(s, "rowan")
	ok(VSave.write_state(s), "save switched character")
	ok(VSave.write_snapshot({"x": 1000.0, "z": -200.0, "yaw": 1.1, "heroId": "darius"}), "switch to Darius outside town and save")
	var st: Dictionary = VSave.read_save().state
	var in_party := false
	for member in st.party:
		if int(member) == VSave.data_index_for_skin("darius"): in_party = true
	ok(st.heroId == "darius" and int(st.active) == VSave.data_index_for_skin("darius") and in_party, "character switch survives sanitize and relaunch data")
	var place: Dictionary = VSave.resume_place(st)
	ok(place.kind == "land" and is_equal_approx(float(place.x), 1000.0) and is_equal_approx(float(place.z), -200.0), "outside-town position resumes on the mainland, not in town")
	ok(VSave.resume_skin(st, true) == "darius", "owner gate does not replace a saved character")
	var legacy_owner: Dictionary = VSave.fresh_state()
	ok(VSave.resume_skin(legacy_owner, true) == "owner", "old owner-gate save with no heroId still starts as Owner")
	ok(VSave.resume_skin(legacy_owner, false) == "", "no saved character and no owner gate uses the numeric active index")
	VSave.remember_hero(VSave.state, "pip")
	ok(str(VSave.state.heroId) == "pip" and VSave.resume_skin(VSave.state, true) == "pip", "pip has no JS index but the model id is what reloads")
	var inn: Dictionary = VSave.state.duplicate(true)
	inn["interior"] = {"inside": true, "id": "inn", "x": 1.5, "z": -2.0, "y": 0.2, "yaw": 0.3}
	var ip: Dictionary = VSave.resume_place(inn)
	ok(ip.kind == "interior" and ip.id == "inn" and is_equal_approx(float(ip.x), 1.5), "interior relaunch returns to that building, not town")
	ok(VSave.write_snapshot({"at_interior": true, "interior": "library", "x": 2.0, "z": 3.0, "iy": 1.0, "yaw": 0.4, "heroId": "pip"}), "interior snapshot")
	st = VSave.read_save().state
	ok(st.interior.inside == true and st.interior.id == "library" and is_equal_approx(float(st.p3d.x), 1000.0), "entering a building does not replace the outside resume point")
	var old_sea: Dictionary = {"p3d": {"zone": "village", "x": 1300.0, "z": 20300.0, "yaw": -1.2}, "version": 1}
	var sp: Dictionary = VSave.resume_place(VSave.adopt(old_sea))
	ok(sp.kind == "sea" and is_equal_approx(float(sp.x), 1300.0) and is_equal_approx(float(sp.z), 300.0), "old ship world coordinate resumes on the sea, not in town")
	var old_inn: Dictionary = {"p3d": {"zone": "village", "x": 4000.0 + 160.0, "z": 4000.0, "yaw": 0.0}, "version": 1}
	var op: Dictionary = VSave.resume_place(VSave.adopt(old_inn))
	ok(op.kind == "interior_legacy" and int(op.index) == 1, "old interior world coordinate maps back to that interior slot")
	ok(VSave.resume_place({"version": 1, "p3d": {"x": NAN, "z": 1}}).kind == "town", "town fallback is only for an unusable position")

func _quest_progress() -> void:
	ok(VSave.volcano_resume({}, false).state == "none", "no story key means the quest has not started")
	var fight: Dictionary = VSave.volcano_resume({"story": {"volcano": {"state": "fight", "stage": 2, "hp": 0.4}}}, false)
	ok(fight.state == "fight" and fight.stage == 2 and is_equal_approx(float(fight.hp), 0.4), "fight stage and health round-trip")
	var junk: Dictionary = VSave.volcano_resume({"story": {"volcano": {"state": "fight", "stage": 9, "hp": 5}}}, false)
	ok(junk.stage == 3 and is_equal_approx(float(junk.hp), 1.0), "out-of-range stage and health are clamped")
	ok(VSave.volcano_resume({"story": {"volcano": {"state": "banana"}}}, false).state == "none", "unknown quest state does not resume a fight")
	ok(VSave.volcano_resume({}, true).state == "won", "legacy story.cfg completion still completes the quest")
	ok(VSave.volcano_resume({"story": {"volcano": {"state": "active"}}}, true).state == "won", "completion wins over a stale active step")
	ok(VSave.volcano_resume({"story": {"volcano": {"state": "won"}}}, false).state == "won", "save-file completion stands without the cfg")
	ok(VSave.volcano_done_in_cfg_text("[story]\nvolcano_done=true\n[broken"), "truncated cfg text still reports the quest done")
	ok(not VSave.volcano_done_in_cfg_text("volcano_done=false"), "cfg text false is not done")
	VSave.state = VSave.adopt({"version": 1})
	VSave.set_volcano_progress("intro", 1, 1.0)
	ok(VSave.volcano_progress(VSave.state).state == "fight", "an intro in progress is stored as the fight it already started")

func _corrupt_is_kept() -> void:
	for f in DirAccess.get_files_at(VSave.dir):
		if str(f).find(".corrupt") >= 0: DirAccess.remove_absolute(VSave.dir + str(f))
	ok(VSave.write_state(VSave.fresh_state()), "clean save before corruption")
	var f := FileAccess.open(VSave.save_path(), FileAccess.WRITE)
	f.store_string("{bad")
	f.close()
	var bytes := FileAccess.get_file_as_bytes(VSave.save_path())
	ok(VSave.read_save().status == "corrupt" and not VSave.write_snapshot({"x": 1, "z": 1}), "corrupt save is not overwritten by autosave")
	ok(FileAccess.get_file_as_bytes(VSave.save_path()) == bytes, "corrupt bytes unchanged after the refused autosave")
	VSave.state = VSave.fresh_state()
	VSave.state.gold = 50
	ok(VSave.write_state(VSave.state), "explicit save after a corrupt file")
	ok(VSave.read_save().status == "ok" and VSave.read_save().state.gold == 50, "new save is readable")
	var side: String = VSave.save_path() + ".corrupt"
	ok(FileAccess.file_exists(side) and FileAccess.get_file_as_bytes(side) == bytes, "corrupt bytes were copied aside before the replace")
	ok(not VSave.import_json("{nope"), "bad import is refused")
	ok(VSave.read_save().state.gold == 50, "refused import leaves the current save in place")

func _session_and_prefs() -> void:
	ok(VSave.save_session("solo", "Liongate-1", "Hero", {"x": 3}), "session write")
	ok(VSave.read_session() != null, "fresh session resumes")
	var raw: Dictionary = VSave._read_json(VSave.active_path())
	raw.time = 0
	var f := FileAccess.open(VSave.active_path(), FileAccess.WRITE)
	f.store_string(JSON.stringify(raw))
	f.close()
	ok(VSave.read_session() == null, "ancient session does not auto-resume")
	f = FileAccess.open(VSave.active_path(), FileAccess.WRITE)
	f.store_string("{bad")
	f.close()
	ok(VSave.read_session() == null, "corrupt session does not auto-resume")
	VSave.clear_session()
	VPrefs.path = VSave.dir + "prefs.json"
	VPrefs.prefs = VPrefs.sanitize(null)
	VPrefs.set_pref("quality", "low")
	VPrefs.set_pref("quality", "ultra")
	ok(VPrefs.load_prefs().quality == "ultra", "prefs rewrite keeps the latest value")
	ok(not FileAccess.file_exists(VPrefs.path + ".tmp"), "prefs temp file is not left behind")
	var bad := FileAccess.open(VPrefs.path, FileAccess.WRITE)
	bad.store_string("{bad")
	bad.close()
	ok(VPrefs.load_prefs().quality == "auto" and VPrefs.load_prefs().view == "third", "corrupt prefs fall back to defaults")

func _fog_and_layout() -> void:
	var Hud = load("res://ui/hud.gd")
	ok(Hud.layout_point([12, 34]) == Vector2(12, 34), "hud layout point")
	ok(Hud.layout_point([]) == null and Hud.layout_point(["x", 1]) == null and Hud.layout_point([NAN, 1]) == null, "bad hud layout entries are ignored")
	var n := 32
	var buf := PackedByteArray(); buf.resize(n); buf[0] = 255; buf[n - 1] = 7
	var encoded := Marshalls.raw_to_base64(buf.compress(FileAccess.COMPRESSION_DEFLATE))
	var WM = load("res://ui/world_map.gd")
	var back: PackedByteArray = WM.decode_fog(encoded, n)
	ok(back.size() == n and back[0] == 255 and back[n - 1] == 7, "fog blob round-trips")
	ok(WM.decode_fog("@@@", n).is_empty() and WM.decode_fog("", n).is_empty(), "undecodable fog is empty")
	ok(WM.decode_fog(encoded, n + 5).is_empty(), "fog of the wrong length is rejected")
	VSave.state = VSave.fresh_state()
	VSave.state["fog"] = "@@@"
	var map: Node = WM.new()
	map.visible = false
	root.add_child(map)
	map.load_fog()
	map.fog[0] = 255
	map.save_fog()
	ok(str(VSave.state.get("fog", "")) == "@@@", "failed fog decode is not overwritten with an empty map")
	map.free()
