extends Node
## Headless tests: godot --headless res://ui/tests/test_ui.tscn  (exit code = failures)
var fails := 0
var n := 0
func ok(c: bool, m: String) -> void:
	n += 1
	if not c: fails += 1; print("FAIL: ", m)
	else: print("ok   ", m)

func _ready() -> void:
	await get_tree().process_frame
	var d := "user://test_ui/"
	DirAccess.make_dir_recursive_absolute(d)
	for f in DirAccess.get_files_at(d): DirAccess.remove_absolute(d + f)
	# --- PBKDF2 (RFC 7914 §11 / known vectors) ---
	ok(VOwnerGate.derive("password", "salt".to_utf8_buffer().hex_encode(), 1) == "120fb6cffcf8b32c43e7225256c4f837a86548c92ccc35480805987cb70be17b", "pbkdf2 c=1")
	ok(VOwnerGate.derive("password", "salt".to_utf8_buffer().hex_encode(), 4096) == "c5e478d59288c841aa530db6845c4c8d962893a001ce4e11a4963873aa98134a", "pbkdf2 c=4096")
	ok(VOwnerGate.unlock_token({"hash": "abc", "v": 2}) == ("abc:unlock:v2").sha256_text(), "unlock token formula")
	ok(VOwnerGate.GATE.salt == "150a1c54ab232044870dcb521f1468ba" and VOwnerGate.GATE.iter == 210000, "gate params match ownergate.js")
	ok(VOwnerGate.owner_from_claims({"owner": true}) and not VOwnerGate.owner_from_claims({"uid": "x"}) and VOwnerGate.owner_from_claims(true), "ownerFromClaims")
	# --- gate flow with a test-only key (never the real one) ---
	var g := VOwnerGate.new(); g.dir = d
	var t := [1000000]
	g.now_ms = func(): return t[0]
	g.params = {"v": 2, "salt": "00ff", "hash": VOwnerGate.derive("testpw", "00ff", 10), "iter": 10}
	ok(not g.is_owner(), "not owner initially")
	var r := g.unlock("nope"); ok(not r.ok and r.reason == "wrong" and r.triesLeft == 2, "wrong 1")
	g.unlock("nope"); r = g.unlock("nope"); ok(r.reason == "throttled" and r.retryMs == 30000, "3rd wrong -> 30s lock")
	r = g.unlock("testpw"); ok(not r.ok and r.reason == "throttled", "correct while throttled is refused")
	t[0] += 30001; r = g.unlock("nope"); ok(r.retryMs == 60000, "doubling 60s")
	t[0] += 60001; r = g.unlock("  testpw "); ok(r.ok and g.is_owner(), "correct (trimmed) unlocks")
	ok(g.status().fails == 0, "throttle cleared")
	g.lock(); ok(not g.is_owner(), "lock")
	ok(g.unlock("x".repeat(129)).ok == false, "max len")
	g.set_server_owner_provider(func(): return {"owner": true}); ok(g.is_owner() and g.unlock("testpw").reason == "server-mode", "server mode")
	var real := VOwnerGate.new(); real.dir = d
	var t0 := Time.get_ticks_msec(); var rr := real.unlock("definitely-not-it"); var ms := Time.get_ticks_msec() - t0
	ok(not rr.ok, "real gate rejects wrong pass (%d ms for 210k iters)" % ms)
	# --- tap counter ---
	var tc := VTapCounter.new()
	var res := []
	for i in 5: res.append(tc.tap(i * 100))
	ok(res == [false, false, false, false, true], "5 taps fire")
	ok(not tc.tap(10000) and not tc.tap(13000), "window resets")
	# --- prefs ---
	var sp := VPrefs.sanitize({"view": "first", "zoom": 9, "lookSens": 0.1, "quality": "bogus", "showFps": true, "combat": false})
	ok(sp.view == "first" and sp.zoom == VPrefs.ZOOM_MAX and sp.lookSens == VPrefs.SENS_MIN and sp.quality == "auto" and sp.showFps == false and sp.combat == true, "sanitizePrefs matches camprefs.js")
	VPrefs.path = d + "prefs.json"; VPrefs.prefs = VPrefs.sanitize(null); VPrefs.set_pref("quality", "ultra")
	ok(VPrefs.load_prefs().quality == "ultra" and VPrefs.tier() == 3, "prefs round-trip + tier")
	# --- save ---
	VSave.dir = d
	ok(VSave.read_save().status == "none", "no save")
	var s := VSave.fresh_state(); ok(VSave.is_valid_save(s) and s.gold == 1250 and s.party == [0, 1, 2], "fresh state mirrors core/save.js")
	ok(VSave.write_state(s) and VSave.read_save().status == "ok", "write/read")
	ok(VSave.write_snapshot({"x": 3.14159, "z": -2.0, "yaw": 1.23456, "hero": 1}), "snapshot")
	var st: Dictionary = VSave.read_save().state
	ok(st.p3d.x == 3.14 and st.p3d.zone == "village" and int(st.active) == 1, "snapshot fields")
	ok(VSave.read_pos(st) != null and VSave.read_pos({"p3d": {"x": 999, "z": 0}}) == null, "readPos bounds")
	var f := FileAccess.open(VSave.save_path(), FileAccess.WRITE); f.store_string("{bad"); f.close()
	ok(VSave.read_save().status == "corrupt" and not VSave.write_snapshot({"x": 1, "z": 1}), "corrupt save never overwritten")
	ok(VSave.import_json(JSON.stringify(VSave.fresh_state())) and VSave.read_save().status == "ok", "import JSON")
	ok(VSave.save_session("solo", "", "", {"x": 1}) and VSave.read_session() != null, "session")
	VSave.clear_session(); ok(VSave.read_session() == null, "session cleared")
	# --- UI flow ---
	var ui = VUI
	ui.gate.dir = d; ui._set_owner(false)
	ui.show_title(); ok(ui.title.visible and not ui.hud.visible, "title shown")
	var fired := [false]; ui.play_solo.connect(func(): fired[0] = true)
	ui.title.buttons.play.pressed.emit(); ok(fired[0] and ui.hud.visible and not ui.title.visible, "Play Solo")
	ui.toggle_menu(true); ok(ui.quick.visible and ui.quick.buttons.size() == 6, "☰ menu has 6 buttons")
	var dest := [""]; ui.travel_requested.connect(func(x): dest[0] = x)
	ui.quick.buttons.travel.pressed.emit(); ok(ui.quick.travel_box.visible, "travel expands")
	ui.quick.travel_box.get_node("T_sail").pressed.emit(); ok(dest[0] == "sail" and not ui.quick.visible, "travel emits")
	ui.open_settings(); ok(ui.settings.visible and ui.settings.find_child("tab_hidden", true, false) == null, "settings 3 tabs, hidden hidden")
	ok(ui.settings.find_child("tab_graphics", true, false) and ui.settings.find_child("tab_controls", true, false) and ui.settings.find_child("tab_gameplay", true, false), "tabs present")
	ui.settings.selected_tab = "gameplay"; ui.settings.build()
	for i in 4: ui.settings.tap_about(i * 200)
	ok(ui.settings.find_child("tab_hidden", true, false) == null, "4 taps not enough")
	ui.settings.tap_about(900); ok(ui.settings.find_child("tab_hidden", true, false) != null and ui.settings.selected_tab == "hidden", "5 taps reveal Owner & Dev")
	ok(ui.settings.find_child("set_owner-god", true, false) == null, "owner cards hidden for non-owner")
	var got := [false]; ui.owner_cheat.connect(func(k, v): got[0] = true)
	ui._on_owner_cheat("god", true); ok(not got[0], "cheat blocked without gate")
	ui._owner_entry(); ok(ui.owner_dlg.visible, "gate prompt shown")
	ui._pick_hero(7); ok(int(VSave.state.active) == 7 and VSave.state.party.has(7), "hero pick updates save")
	ui.return_to_title(); ok(ui.title.visible, "return to title")
	print("RESULT %d/%d passed" % [n - fails, n])
	get_tree().quit(fails)
