extends SceneTree
## Headless: Fly HUD visibility by role, toggle <-> cheat flag sync both ways, hold ▲/▼ changes altitude, layout clear
## of the joystick and the skill cluster. Run: godot --headless -s res://tests/test_fly_hud.gd
class FakeMain extends Node:
	var fly_alt := 6.0
	var cheat := {"fly": false, "speed": 1.0}
	var flight := false
	var landing := false
	var jumps := 0
	func set_flight(on: bool) -> void:
		if flight and not on: landing = true
		flight = on
	func request_jump() -> void: jumps += 1
var passed := 0; var failed := 0
func ok(c: bool, m: String) -> void:
	if c: passed += 1; print("PASS ", m)
	else: failed += 1; print("FAIL ", m)

func BTN_W(b: Button) -> float: return b.offset_right - b.offset_left

func _init() -> void:
	var fm := FakeMain.new(); root.add_child(fm)
	var ch := Cheats.new(); ch.main = fm; root.add_child(ch)
	var role := [""]
	ch.role_provider = func() -> String: return role[0]
	var ui := Control.new(); ui.size = Vector2(1440, 720); root.add_child(ui)
	var fc := FlyControls.new(); fc.cheats = ch; fc.main = fm; ui.add_child(fc); fc.build()
	fc.step(0.016)
	ok(not fc.fly_btn.visible, "hidden for a normal player")
	ok(fc.jump_btn.visible, "Jump shown for every hero")
	fc.jump_btn.button_down.emit(); fc.jump_btn.button_up.emit()
	ok(fm.jumps == 1, "Jump requests a jump on the ground")
	role[0] = "owner"; fc.step(0.016)
	ok(not fc.fly_btn.visible and not fc.up_btn.visible, "owner, Fly cheat off -> no Fly/Up/Down")
	ch.request("fly", true); fc.step(0.016)
	ok(fc.fly_btn.visible and not fc.up_btn.visible and not fm.flight, "Fly cheat on in the menu -> Fly button shown, still grounded")
	fc.fly_btn.button_pressed = true; fc.step(0.016)
	ok(fm.flight and fc.up_btn.visible and fc.down_btn.visible, "HUD Fly starts flight, Up/Down shown")
	var a0 := fm.fly_alt
	fc.up_btn.button_down.emit()
	for i in 60: fc.step(1.0 / 60.0)
	fc.up_btn.button_up.emit()
	ok(absf(fm.fly_alt - (a0 + 8.0)) < 0.2, "hold Up 1 s climbs 8 m (%.2f -> %.2f)" % [a0, fm.fly_alt])
	fc.down_btn.button_down.emit()
	for i in 30: fc.step(1.0 / 60.0)
	fc.down_btn.button_up.emit()
	ok(absf(fm.fly_alt - (a0 + 4.0)) < 0.2, "hold Down 0.5 s descends 4 m")
	ok(not fc.jump_btn.visible and fc.up_btn.visible, "no duplicate Up: Jump hides while flying, HUD ▲ climbs")
	fc.fly_btn.button_pressed = false; fc.step(0.016)
	ok(not fm.flight and fc.fly_btn.visible and not fc.up_btn.visible and fc.jump_btn.visible, "HUD Fly off -> grounded, button stays, Jump back")
	fc.fly_btn.button_pressed = true; fc.step(0.016)
	ch.request("fly", false); fc.step(0.016)
	ok(not fc.fly_btn.visible and not fc.up_btn.visible and not fc.down_btn.visible, "menu cheat off -> Fly, Up, Down hidden")
	ok(not fm.flight and fm.landing, "cheat off mid-flight -> flight stops with a soft landing")
	ch.request("fly", true); fc.step(0.016)
	ok(fc.fly_btn.visible and not fm.flight, "cheat back on -> button back, not auto-flying")
	role[0] = ""; fc.step(0.016)
	ok(not fc.fly_btn.visible and not fc.up_btn.visible, "role lost -> hidden")
	# layout: no overlap with the joystick (bottom-left 260x260) or the skill cluster (combat_hud lay)
	var W := 1440.0; var H := 720.0
	var skills := [[Vector2(-180, -180), 150], [Vector2(-300, -116), 96], [Vector2(-282, -236), 96], [Vector2(-176, -300), 96], [Vector2(-80, -280), 70]]
	var joy := Rect2(0, H - 260, 260, 260)
	var clear := true
	for b in [fc.fly_btn, fc.up_btn, fc.down_btn, fc.jump_btn]:
		var r := Rect2(W + b.offset_left, H + b.offset_top, b.offset_right - b.offset_left, b.offset_bottom - b.offset_top)
		if r.size.x < 48 or r.size.y < 48: clear = false
		if r.intersects(joy): clear = false
		for s in skills: if r.intersects(Rect2(W + s[0].x, H + s[0].y, s[1], s[1])): clear = false
	ok(clear, "buttons >= 48 px, clear of joystick and skills")
	var rs := []
	for b in [fc.fly_btn, fc.up_btn, fc.down_btn, fc.jump_btn]: rs.append(Rect2(W + b.offset_left, H + b.offset_top, BTN_W(b), BTN_W(b)))
	var sep := true
	for i in rs.size():
		for k in range(i + 1, rs.size()): if rs[i].intersects(rs[k]): sep = false
	ok(sep, "Jump does not overlap Fly/Up/Down")
	var jr: Rect2 = rs[3]
	ok(jr.position.x > W - 300 and jr.position.y > H - 420, "Jump within right-thumb reach (%s)" % jr)
	print("RESULT %d/%d passed" % [passed, passed + failed])
	quit(1 if failed else 0)
