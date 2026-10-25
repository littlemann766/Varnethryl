extends PanelContainer
## Port of settings3d.js (v1.5.34 player tabs): Graphics · Controls · Gameplay, plus hidden "Owner & Dev"
## revealed by 5 quick taps on the About version line (settingsboot.js / cheatboot.js createTapCounter) or the ` key.
signal closed
signal customize_hud
signal combat_toggled(on: bool)
signal owner_cheats_requested       # Access › Owner Cheats (root shows gate if not owner)
signal coowner_requested            # Access › CoOwner Tools (server-verified; multiplayer branch)
signal owner_cheat(key: String, value)  # god, fly, noclip, bump, unlimited, nocd, speed, remax, titan, bamboo, lock
signal dev_action(key: String)      # diagnostics, gallery, model_style, boss_models

const TABS := [["graphics", "Graphics"], ["controls", "Controls"], ["gameplay", "Gameplay"]]
const QNAMES := {"auto": "Auto (adapts to your device)", "ultra": "Ultra (max effects)", "high": "High (sharpest)", "balanced": "Balanced", "low": "Low (fastest)"}
var selected_tab := "graphics"
var hidden_unlocked := false
var is_owner := false
var cheats := {"god": true, "fly": false, "noclip": false, "bump": true, "unlimited": false, "nocd": false, "speed": 1.0, "bamboo": false}
var version := "1.5.33"
var tap := VTapCounter.new()
var body: VBoxContainer
var syncs: Array[Callable] = []
var about_label: Button

func _ready() -> void:
	name = "Settings"
	add_theme_stylebox_override("panel", VStyle.box(Color("#130f20f5"), Color("#c9a24a88"), 1, 16, 12))
	set_anchors_preset(PRESET_RIGHT_WIDE); offset_left = -420; offset_right = -8; offset_top = 52; offset_bottom = -8
	var v := VBoxContainer.new(); add_child(v)
	var hd := HBoxContainer.new(); v.add_child(hd)
	var t := VStyle.label("Settings", 20, VStyle.GOLD2); t.size_flags_horizontal = SIZE_EXPAND_FILL; hd.add_child(t)
	var x := Button.new(); x.text = "✕"; x.name = "setClose"; x.custom_minimum_size = Vector2(44, 44); x.pressed.connect(func(): closed.emit()); hd.add_child(x)
	var sc := ScrollContainer.new(); sc.size_flags_vertical = SIZE_EXPAND_FILL; sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED; v.add_child(sc)
	body = VBoxContainer.new(); body.size_flags_horizontal = SIZE_EXPAND_FILL; body.add_theme_constant_override("separation", 8); sc.add_child(body)
	VPrefs.changed.connect(func(_p): for s in syncs: s.call())

func unlock_hidden() -> void:
	hidden_unlocked = true; selected_tab = "hidden"; build()

func tap_about(t: int = Time.get_ticks_msec()) -> void:
	if tap.tap(t): unlock_hidden()

func _unhandled_key_input(e: InputEvent) -> void:
	if visible and e is InputEventKey and e.pressed and e.keycode == KEY_QUOTELEFT: unlock_hidden(); get_viewport().set_input_as_handled()

func _row(kids: Array) -> HFlowContainer:
	var r := HFlowContainer.new(); r.add_theme_constant_override("h_separation", 6); r.add_theme_constant_override("v_separation", 6)
	for k in kids: r.add_child(k)
	return r

func _card(title: String, desc: String, own := false) -> VBoxContainer:
	var c := VStyle.card(own); body.add_child(c)
	var v := VBoxContainer.new(); v.add_theme_constant_override("separation", 6); c.add_child(v)
	v.add_child(VStyle.label(title.to_upper(), 13, VStyle.GOLD2))
	if desc != "": var d := VStyle.label(desc, 12, Color(0.94, 0.91, 1, 0.7)); v.add_child(d)
	return v

func _btn(text: String, key: String, cb: Callable) -> Button:
	var b := Button.new(); b.text = text; b.name = "set_" + key; b.custom_minimum_size = Vector2(48, 48); b.pressed.connect(cb); return b

func _toggle(text: String, key: String, getter: Callable, setter: Callable) -> Button:
	var b := Button.new(); b.text = text; b.name = "set_" + key; b.custom_minimum_size = Vector2(48, 48)
	var s := func(): VStyle.set_on(b, bool(getter.call()))
	b.pressed.connect(func(): setter.call(not bool(getter.call())); s.call()); s.call(); syncs.append(s); return b

func _choice(key: String, val: String, text: String, getter: Callable, setter: Callable) -> Button:
	var b := Button.new(); b.text = text; b.name = "set_%s_%s" % [key, val]; b.custom_minimum_size = Vector2(48, 48)
	var s := func(): VStyle.set_on(b, getter.call() == val)
	b.pressed.connect(func(): setter.call(val); for f in syncs: f.call()); s.call(); syncs.append(s); return b

func lab(t: String) -> Label:
	var l := VStyle.label(t, 14); l.autowrap_mode = TextServer.AUTOWRAP_OFF; l.custom_minimum_size = Vector2(120, 0); return l

func build() -> void:
	syncs.clear()
	for c in body.get_children(): body.remove_child(c); c.queue_free()
	var P: Dictionary = VPrefs.prefs
	var tabs := TABS.duplicate()
	if hidden_unlocked: tabs.append(["hidden", "Owner & Dev"])
	if not tabs.any(func(t): return t[0] == selected_tab): selected_tab = "graphics"
	var bar := HBoxContainer.new(); bar.add_theme_constant_override("separation", 6); body.add_child(bar)
	for t in tabs:
		var b := Button.new(); b.text = t[1]; b.name = "tab_" + t[0]; b.size_flags_horizontal = SIZE_EXPAND_FILL; b.custom_minimum_size = Vector2(0, 44)
		b.add_theme_font_size_override("font_size", 13); VStyle.set_on(b, t[0] == selected_tab)
		var k: String = t[0]; b.pressed.connect(func(): selected_tab = k; build()); bar.add_child(b)
	match selected_tab:
		"graphics":
			var g := _card("Graphics", "Quality and shadows. Lower is faster.")
			var q := OptionButton.new(); q.name = "setQuality"; q.custom_minimum_size = Vector2(220, 48)
			for i in VPrefs.QUALITIES.size():
				q.add_item(QNAMES[VPrefs.QUALITIES[i]], i)
				if VPrefs.QUALITIES[i] == P.quality: q.select(i)
			q.item_selected.connect(func(i): VPrefs.set_pref("quality", VPrefs.QUALITIES[i]))
			g.add_child(_row([lab("Quality"), q]))
			g.add_child(_row([_toggle("Shadows", "shadows", func(): return VPrefs.prefs.shadows, func(v): VPrefs.set_pref("shadows", v))]))
		"controls":
			var cc := _card("Camera", "How the view follows your hero.")
			var gv := func(): return VPrefs.prefs.view
			var sv := func(v): VPrefs.set_pref("view", v)
			cc.add_child(_row([lab("View"), _choice("view", "third", "Third person", gv, sv), _choice("view", "first", "First person", gv, sv)]))
			var gm := func(): return VPrefs.prefs.camMode
			var sm := func(v): VPrefs.set_pref("camMode", v)
			cc.add_child(_row([lab("Camera follow"), _choice("cam", "follow", "On", gm, sm), _choice("cam", "free", "Off", gm, sm)]))
			var sl := HSlider.new(); sl.name = "set_camSens"; sl.min_value = VPrefs.SENS_MIN; sl.max_value = VPrefs.SENS_MAX; sl.step = 0.05; sl.value = P.lookSens
			sl.custom_minimum_size = Vector2(170, 48); sl.size_flags_horizontal = SIZE_EXPAND_FILL
			var out := VStyle.label("%.2f×" % P.lookSens, 14)
			sl.value_changed.connect(func(v): out.text = "%.2f×" % v; VPrefs.prefs.lookSens = v; VPrefs.prefs.zoomSens = v; VPrefs.save_prefs())
			cc.add_child(_row([lab("Camera sensitivity"), sl, out]))
			var hc := _card("On-screen buttons", "Drag controls to move them, then Save HUD. Reset is inside the editor.")
			hc.add_child(_row([_btn("Customize HUD", "editbtns", func(): customize_hud.emit())]))
			hc.add_child(VStyle.label("Joystick or tap to move · drag to look · pinch to zoom. Keys: F attack · Space dodge · Q lock-on · 1–4 skills · R potion · V view.", 11, Color(1, 1, 1, 0.7)))
		"gameplay":
			var gc := _card("Combat", "Fight mode and on-screen combat buttons.")
			var cb := Button.new(); cb.name = "set_combat"; cb.custom_minimum_size = Vector2(48, 48)
			var cs := func(): var on: bool = VPrefs.prefs.combat; VStyle.set_on(cb, on); cb.text = "Combat: On" if on else "Combat: Off"
			cb.pressed.connect(func(): var on: bool = not VPrefs.prefs.combat; VPrefs.prefs.combatSet = true; VPrefs.set_pref("combat", on); combat_toggled.emit(on)); cs.call(); syncs.append(cs)
			gc.add_child(_row([cb]))
			var ac := _card("About", "")
			about_label = Button.new(); about_label.name = "about_version"; about_label.flat = true; about_label.text = "Varnethryl · v" + version
			about_label.alignment = HORIZONTAL_ALIGNMENT_LEFT; about_label.custom_minimum_size = Vector2(0, 44)
			about_label.add_theme_color_override("font_color", Color("#f1d28a")); about_label.add_theme_color_override("font_pressed_color", Color("#f1d28a"))
			about_label.button_up.connect(func(): tap_about())
			ac.add_child(about_label)
			ac.add_child(_row([_btn("Restore default settings", "reset", func(): VPrefs.restore_defaults(); build())]))
		"hidden":
			var oc := _card("Access", "Password-protected. Gates are unchanged.", true)
			oc.add_child(_row([_btn("🔒 Owner Cheats", "owner-cheats", func(): owner_cheats_requested.emit()), _btn("🔒 CoOwner Tools", "coowner-tools", func(): coowner_requested.emit())]))
			var dc := _card("Developer", "Testing and diagnostics.", true)
			dc.add_child(_row([_toggle("Show FPS", "showFps", func(): return VPrefs.prefs.showFps, func(v): VPrefs.prefs.fpsSet = true; VPrefs.set_pref("showFps", v))]))
			dc.add_child(_row([_btn("Switch model style", "model-style", func(): dev_action.emit("model_style")), _btn("3D model gallery", "gallery", func(): dev_action.emit("gallery"))]))
			dc.add_child(_row([_btn("Approved boss models", "boss-models", func(): dev_action.emit("boss_models")), _btn("Diagnostics", "diagnostics", func(): dev_action.emit("diagnostics"))]))
			if is_owner: _owner_cards()

func _owner_cards() -> void:
	var box := _card("Owner (save is marked cheated)", "", true)
	var own := func(key: String, text: String):
		return _toggle(text, "owner-" + key, func(): return cheats[key], func(v): cheats[key] = v; owner_cheat.emit(key, v))
	box.add_child(_row([own.call("god", "God mode"), own.call("fly", "Fly"), own.call("noclip", "Noclip"), own.call("bump", "Bumps")]))
	box.add_child(_row([own.call("unlimited", "Unlimited MP/SP"), own.call("nocd", "No cooldowns (Owner skin)")]))
	box.add_child(_row([own.call("bamboo", "Bamboo Stick (test weapon)")]))
	var spd := OptionButton.new(); spd.name = "setSpeed"
	var muls := [0.5, 1.0, 2.0, 4.0, 8.0]
	for i in muls.size():
		spd.add_item("%s×" % str(muls[i]).trim_suffix(".0"), i)
		if is_equal_approx(muls[i], float(cheats.speed)): spd.select(i)
	spd.item_selected.connect(func(i): cheats.speed = muls[i]; owner_cheat.emit("speed", muls[i]))
	box.add_child(_row([lab("Speed"), spd]))
	box.add_child(_row([_btn("Re-max active hero", "owner-max", func(): owner_cheat.emit("remax", true)), _btn("Spawn Ashen Titan", "owner-titan", func(): owner_cheat.emit("titan", true)), _btn("🔓 Lock owner", "owner-lock", func(): owner_cheat.emit("lock", true))]))
	box.add_child(VStyle.label("God mode starts ON for the owner; your choice is remembered.", 11, Color(1, 1, 1, 0.7)))
