extends SceneTree
## Truthful save/resume copy. Does not change the save schema.
## godot --headless --path . -s res://tests/save_status_test.gd
var fails := 0
func ok(c: bool, msg: String) -> void:
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	await process_frame
	var VSave = root.get_node("VSave")
	var ui = root.get_node("VUI")
	var d := "user://save_status/"
	DirAccess.make_dir_recursive_absolute(d)
	for f in DirAccess.get_files_at(d): DirAccess.remove_absolute(d + f)
	VSave.dir = d
	VSave.clear_session()
	ok(SaveStatus.title_line(false) == "No save yet. Play Solo starts in town.", "no file")
	var s: Dictionary = VSave.fresh_state()
	VSave.remember_hero(s, "darius")
	s["p3d"] = {"zone": "village", "x": 1000.0, "z": -200.0, "yaw": 0.7}
	ok(VSave.write_state(s), "darius mainland write")
	ok(SaveStatus.title_line(true) == "Saved: Darius, on the mainland. You stay in town until Play Solo.", "darius line")
	s = VSave.fresh_state()
	VSave.remember_hero(s, "pip")
	s["sea"] = {"galleon_tier": 1, "aboard": true, "ship": "galleon", "x": 1300.0, "z": 300.0, "yaw": -1.57}
	s["p3d"] = {"zone": "village", "x": 12.0, "z": 4.0, "yaw": 0.0}
	ok(VSave.write_state(s), "pip sea write")
	ok(SaveStatus.title_line(false).find("Pip") >= 0 and SaveStatus.title_line(false).find("galleon") >= 0 and SaveStatus.title_line(false).find("until Play Solo") >= 0, "pip aboard line")
	s = VSave.fresh_state()
	VSave.remember_hero(s, "elira")
	s["interior"] = {"inside": true, "id": "inn", "x": 1.25, "z": -1.5, "y": 0.2, "yaw": 0.4}
	s["p3d"] = {"zone": "village", "x": -6.0, "z": 26.0, "yaw": 0.0}
	ok(VSave.write_state(s), "elira inn write")
	ok(SaveStatus.title_line(false) == "Saved: Elira, inside the Inn. You stay in town until Play Solo.", "elira line")
	var bad := FileAccess.open(VSave.save_path(), FileAccess.WRITE)
	bad.store_string("{bad")
	bad.close()
	ok(VSave.read_save().status == "corrupt", "corrupt status")
	ok(SaveStatus.title_line(false) == "Save could not be read. It was not replaced. Play Solo starts in town.", "corrupt line")
	ok(not VSave.write_snapshot({"x": 1, "z": 2, "yaw": 0}), "corrupt file is not overwritten")
	var fut := FileAccess.open(VSave.save_path(), FileAccess.WRITE)
	fut.store_string(JSON.stringify({"version": 2, "gold": 9, "gear": [], "party": [0], "unlocked": [0]}))
	fut.close()
	ok(VSave.read_save().status == "corrupt", "future version is not a current save")
	ok(SaveStatus.title_line(false).find("could not be read") >= 0 and SaveStatus.title_line(false).find("not replaced") >= 0, "future version line")
	ok(not VSave.write_snapshot({"x": 4, "z": 5, "yaw": 0}), "future version is not overwritten")
	var blocker := d + "not_a_dir"
	var bf := FileAccess.open(blocker, FileAccess.WRITE)
	bf.store_string("x"); bf.close()
	VSave.dir = blocker + "/"
	ok(not VSave.write_state(VSave.fresh_state()), "storage failure returns false")
	ok(SaveStatus.fail_line() == "Save failed. Nothing new was written.", "failure copy does not say saved")
	ok(SaveStatus.resume_done("land", "darius", "", true) == "Resumed Darius on the mainland.", "resume land")
	ok(SaveStatus.resume_done("sea", "pip", "galleon", true) == "Resumed Pip aboard the galleon.", "resume sea")
	ok(SaveStatus.resume_done("interior", "elira", "Inn", true) == "Resumed Elira inside the Inn.", "resume inn")
	ok(SaveStatus.resume_done("town", "aldric", "", false) == "No saved place restored. You are in town.", "resume town")
	VSave.dir = d
	var none := FileAccess.open(VSave.save_path(), FileAccess.WRITE)
	none.store_string("{bad"); none.close()
	ui._save_failed = false
	ui.get_snapshot = func(): return {"x": 3.0, "z": 4.0, "yaw": 0.0}
	var notes: Array = []
	if not ui.notice.is_connected(func(_t): pass):
		pass
	ui.notice.connect(func(t): notes.append(t))
	ok(not ui._save_now(true), "explicit save against a corrupt file fails")
	ok(notes.size() == 1 and notes[0] == SaveStatus.fail_line(), "failed explicit save says so once (%s)" % str(notes))
	ok(ui._save_now(true) == false and notes.size() == 1, "repeated failure does not claim a new save")
	var good: Dictionary = VSave.fresh_state()
	VSave.remember_hero(good, "darius")
	good["p3d"] = {"zone": "village", "x": 1000.0, "z": -200.0, "yaw": 0.2}
	# Replace the corrupt bytes so a real write can succeed, then confirm the success line.
	DirAccess.remove_absolute(VSave.save_path())
	ok(VSave.write_state(good), "replace corrupt file with a real save")
	notes.clear()
	ui._save_failed = true
	ok(ui._save_now(true), "explicit save succeeds")
	ok(notes.size() == 1 and notes[0] == "Save written.", "success is only reported after the write (%s)" % str(notes))
	ui.show_title()
	var lab: Label = ui.title.find_child("SaveStatus", true, false)
	ok(lab != null and lab.text.find("Darius") >= 0 and lab.text.find("until Play Solo") >= 0, "title shows the saved resume (%s)" % (lab.text if lab else ""))
	ok(lab != null and int(lab.get_theme_font_size("font_size")) >= 18, "status text is at least 18 px")
	ok(lab != null and lab.text.find("Nothing is reset") < 0, "the old unconditional save sentence is gone")
	print("SAVE_STATUS %d failed" % fails)
	quit(1 if fails else 0)
