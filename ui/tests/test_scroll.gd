extends Node
## Simulated touch drags on scrolling panels. Run: godot --headless res://ui/tests/test_scroll.tscn
var fails := 0; var n := 0
func ok(c: bool, m: String) -> void:
	n += 1
	if c: print("PASS ", m)
	else: fails += 1; print("FAIL ", m)

func _mb(p: Vector2, down: bool) -> void:
	var e := InputEventMouseButton.new(); e.button_index = MOUSE_BUTTON_LEFT; e.pressed = down; e.position = p; e.global_position = p
	e.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
	get_viewport().push_input(e, true)
func _mm(p: Vector2, rel: Vector2) -> void:
	var e := InputEventMouseMotion.new(); e.position = p; e.global_position = p; e.relative = rel; e.button_mask = MOUSE_BUTTON_MASK_LEFT
	get_viewport().push_input(e, true)
func _drag(from: Vector2, delta: Vector2, steps := 10, release := true) -> void:
	_mb(from, true); var p := from
	for i in steps:
		await get_tree().process_frame; p += delta / steps; _mm(p, delta / steps)
	if release: _mb(p, false)
func _c(c: Control) -> Vector2: return c.get_global_rect().get_center()
func _frames(k: int) -> void:
	for i in k: await get_tree().process_frame

func _ready() -> void:
	var d := "user://shots_scroll/"; DirAccess.make_dir_recursive_absolute(d)
	VSave.dir = d; VUI.gate.dir = d; VPrefs.path = d + "p.json"; VSave.state = VSave.fresh_state()
	get_window().size = Vector2i(1170, 540)
	var ui = VUI; ui.settings.selected_tab = "controls"; ui.open_settings()
	for i in 5: ui.settings.tap_about(i * 100)
	ui.settings.is_owner = true; ui.settings.build()
	for t in ["controls", "hidden"]:
		ui.settings.selected_tab = t; ui.settings.build(); await _frames(4)
		var sc: TouchScroll = ui.settings.find_children("*", "TouchScroll", true, false)[0]
		var bar := sc.get_v_scroll_bar()
		ok(bar.max_value > sc.size.y, "%s: list is taller than the panel" % t)
		ok(bar.size.x >= 14 or bar.custom_minimum_size.x >= 14, "%s: wide scroll bar" % t)
		sc.scroll_vertical = 0; await _frames(2)
		# drag up starting on a button
		var btn: Button = null
		for b in sc.find_children("*", "Button", true, false):
			if b.is_visible_in_tree() and sc.get_global_rect().has_point(_c(b)) and _c(b).y > sc.get_global_rect().position.y + 150: btn = b; break
		var hits := [0]; var cb := func(): hits[0] += 1
		btn.pressed.connect(cb)
		await _drag(_c(btn), Vector2(0, -150))
		await _frames(2)
		ok(sc.scroll_vertical >= mini(120, int(bar.max_value - bar.page)) and sc.scroll_vertical > 0, "%s: drag starting on a button scrolls (%d)" % [t, sc.scroll_vertical])
		ok(hits[0] == 0, "%s: the dragged-over button did not fire" % t)
		await _frames(30)
		btn.pressed.disconnect(cb)
		# a tap still presses
		sc.set_process(false)
		var b2: Button = null
		for b in sc.find_children("*", "Button", true, false):
			if b.is_visible_in_tree() and sc.get_global_rect().grow(-10).has_point(_c(b)): b2 = b; break
		var hit2 := [0]; var cb2 := func(): hit2[0] += 1
		b2.pressed.connect(cb2); _mb(_c(b2), true); await _frames(2); _mb(_c(b2), false); await _frames(3)
		ok(hit2[0] == 1, "%s: a tap on a button still presses it" % t)
		if is_instance_valid(b2) and b2.pressed.is_connected(cb2): b2.pressed.disconnect(cb2)
	# slider: vertical drag scrolls without changing value; horizontal drag changes it
	ui.settings.selected_tab = "controls"; ui.settings.build(); await _frames(4)
	var sc2: TouchScroll = ui.settings.find_children("*", "TouchScroll", true, false)[0]
	sc2.scroll_vertical = 0; await _frames(2)
	var sl: HSlider = ui.settings.find_child("set_camSens", true, false)
	if sl and not sc2.get_global_rect().has_point(_c(sl)): sc2.ensure_control_visible(sl); await _frames(2)
	ok(sl != null, "camera sensitivity slider exists")
	var v0 := sl.value; var s0 := sc2.scroll_vertical
	var from := _c(sl) + Vector2(sl.size.x * 0.3, 0)
	await _drag(from, Vector2(0, 120 if s0 > 0 else -120)); await _frames(2)
	ok(sl.value == v0, "vertical drag on a slider leaves its value (%.2f)" % sl.value)
	ok(sc2.scroll_vertical != s0, "vertical drag on a slider scrolls the list (%d → %d)" % [s0, sc2.scroll_vertical])
	sc2.set_process(false); await _frames(2)
	var pos := _c(sl) - Vector2(sl.size.x * 0.3, 0)
	await _drag(pos, Vector2(sl.size.x * 0.5, 0)); await _frames(2)
	ok(sl.value != v0, "horizontal drag still moves the slider (%.2f → %.2f)" % [v0, sl.value])
	# fling
	ui.settings.selected_tab = "hidden"; ui.settings.build(); await _frames(4)
	var sc3: TouchScroll = ui.settings.find_children("*", "TouchScroll", true, false)[0]
	sc3.scroll_vertical = 0; await _frames(2)
	await _drag(sc3.get_global_rect().get_center() + Vector2(0, 100), Vector2(0, -200), 4)
	var after_release := sc3.scroll_vertical
	await _frames(20)
	ok(sc3.scroll_vertical > after_release, "fling keeps scrolling after release (%d → %d)" % [after_release, sc3.scroll_vertical])
	ok(sc3.scroll_deadzone > 0, "built-in touch deadzone set")
	# hero select list
	ui.settings.hide(); ui.open_heroes(true); await _frames(4)
	ok(ui.heroes.find_children("*", "TouchScroll", true, false).size() > 0, "hero select uses TouchScroll")
	print("scroll: %d/%d passed" % [n - fails, n])
	get_tree().quit(1 if fails else 0)

func bar_room(sc: TouchScroll) -> int: return int(sc.get_v_scroll_bar().max_value - sc.size.y) - 130
