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
var version: String = str(ProjectSettings.get_setting("application/config/version", "1.9.3"))
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
	var sc := TouchScroll.new(); sc.size_flags_vertical = SIZE_EXPAND_FILL; v.add_child(sc)
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
			_coowner_card()
			var dc := _card("Developer (Owner only)", "Testing and diagnostics." if is_owner else "Unlock Owner Cheats to use the developer tools.", true)
			if not is_owner:
				dc.add_child(_row([_toggle("Show FPS", "showFps", func(): return VPrefs.prefs.showFps, func(v): VPrefs.prefs.fpsSet = true; VPrefs.set_pref("showFps", v))]))
				return
			dc.add_child(_row([_toggle("Show FPS", "showFps", func(): return VPrefs.prefs.showFps, func(v): VPrefs.prefs.fpsSet = true; VPrefs.set_pref("showFps", v))]))
			dc.add_child(_row([_btn("Switch model style", "model-style", func(): dev_action.emit("model_style")), _btn("3D model gallery", "gallery", func(): dev_action.emit("gallery"))]))
			dc.add_child(_row([_btn("Approved boss models", "boss-models", func(): dev_action.emit("boss_models")), _btn("Diagnostics", "diagnostics", func(): dev_action.emit("diagnostics"))]))
			# render dev tools (moved off the HUD in test 4): handled by scripts/main.gd via VUI.dev_action
			dc.add_child(_row([_btn("Time of day (cycle)", "dev-time", func(): dev_action.emit("time")), _btn("Day speed 1×/10×", "dev-speed", func(): dev_action.emit("speed"))]))
			dc.add_child(_row([_btn("FPS cap 60/120", "dev-fps", func(): dev_action.emit("fps_cap")), _btn("Run benchmark", "dev-bench", func(): dev_action.emit("benchmark"))]))
			if is_owner: _owner_cards()

## The cheat API (combat/cheats.gd) set by main.gd; every press goes through api.request(), which checks the role.
func _api(): return VUI.get("cheat_api")

func _cheat_toggle(key: String, text: String, prefix: String) -> Button:
	return _toggle(text, prefix + key, func():
		var a = _api(); return a != null and bool(a.flags.get(key, false)),
		func(v):
			var a = _api()
			if a: a.request(key, v)
			if prefix == "owner-": cheats[key] = v)

func _cheat_btn(key: String, text: String, prefix: String, arg = true) -> Button:
	return _btn(text, prefix + key, func():
		var a = _api()
		if a: a.request(key, arg.call() if arg is Callable else arg))

func _pick(name_: String, items: Array) -> OptionButton:
	var o := OptionButton.new(); o.name = name_; o.custom_minimum_size = Vector2(150, 48)
	for it in items: o.add_item(str(it[1]) if it is Array else str(it))
	o.set_meta("vals", items.map(func(it): return it[0] if it is Array else it))
	return o

func _val(o: OptionButton): return o.get_meta("vals")[max(o.selected, 0)]

func _speed_row(prefix: String) -> HFlowContainer:
	var spd := OptionButton.new(); spd.name = prefix + "speed"; spd.custom_minimum_size = Vector2(110, 48)
	var muls := [0.5, 1.0, 2.0, 4.0, 8.0]
	for i in muls.size():
		spd.add_item("%s×" % str(muls[i]).trim_suffix(".0"), i)
		var a = _api()
		if is_equal_approx(muls[i], float(a.flags.speed) if a else 1.0): spd.select(i)
	spd.item_selected.connect(func(i): var a = _api(); if a: a.request("speed", muls[i]))
	return _row([lab("Speed"), spd])

func _self_cheats(box: VBoxContainer, prefix: String) -> void:
	box.add_child(VStyle.label("MOVEMENT", 12, VStyle.GOLD2))
	box.add_child(_row([_cheat_toggle("god", "God mode", prefix), _cheat_toggle("fly", "Fly", prefix), _cheat_toggle("noclip", "Noclip", prefix), _cheat_toggle("bump", "Bumps", prefix)]))
	box.add_child(_row([_cheat_btn("fly_up", "Fly ▲", prefix), _cheat_btn("fly_down", "Fly ▼", prefix)]))
	box.add_child(_speed_row(prefix))
	box.add_child(VStyle.label("COMBAT (own hero)", 12, VStyle.GOLD2))
	box.add_child(_row([_cheat_toggle("unlimited", "∞ MP / SP", prefix), _cheat_toggle("nocd", "No cooldowns", prefix), _cheat_btn("heal", "Heal my party", prefix)]))
	box.add_child(_row([_cheat_toggle("titan_form", "Titan form (cosmetic)", prefix)]))
	var place := _pick(prefix + "place", [["fountain", "Plaza"], ["inn", "Inn"], ["smithy", "Smithy"], ["bakery", "Bakery"], ["windmill", "Windmill"]])
	box.add_child(_row([place, _cheat_btn("tp_place", "Go building", prefix, func(): return _val(place))]))

func _owner_cards() -> void:
	var box := _card("Owner (save is marked cheated)", "Every Owner cheat. Scroll for more.", true)
	_self_cheats(box, "owner-")
	box.add_child(_row([_cheat_toggle("bamboo", "Bamboo Stick (test weapon)", "owner-")]))
	box.add_child(VStyle.label("GOLD / XP / LEVEL", 12, VStyle.GOLD2))
	box.add_child(_row([_cheat_toggle("inf_gold", "∞ Gold", "owner-"), _cheat_btn("gold", "+1M gold", "owner-", 1000000)]))
	box.add_child(_row([_cheat_btn("xp", "+1k XP", "owner-"), _cheat_btn("xp_big", "+50k XP", "owner-")]))
	var lvl := SpinBox.new(); lvl.name = "ownerLevel"; lvl.min_value = 1; lvl.max_value = 80; lvl.value = 40; lvl.custom_minimum_size = Vector2(110, 48)
	box.add_child(_row([lvl, _cheat_btn("level_active", "Set active", "owner-", func(): return int(lvl.value)), _cheat_btn("level_party", "Set party", "owner-", func(): return int(lvl.value))]))
	box.add_child(_row([_cheat_btn("remax", "Re-max active hero", "owner-")]))
	box.add_child(VStyle.label("ITEMS", 12, VStyle.GOLD2))
	var kind := _pick("ownerKind", ["weapon", "armor", "charm"])
	var il := _pick("ownerItemLv", range(16).map(func(i): return [i, "Lv %d" % i])); il.select(15)
	box.add_child(_row([kind, il, _cheat_btn("item", "Spawn item", "owner-", func(): return [_val(kind), _val(il)])]))
	box.add_child(VStyle.label("ENEMIES / BOSSES", 12, VStyle.GOLD2))
	box.add_child(_row([_cheat_btn("kill", "Kill enemies", "owner-"), _cheat_btn("fight_test", "Fight test", "owner-")]))
	var foe := _pick("ownerFoe", [["frosttroll_a", "Frost Troll Krag"], ["frosttroll_b", "Frost Troll Mog"]])
	box.add_child(_row([foe, _cheat_btn("spawn_enemy", "Spawn enemy", "owner-", func(): return _val(foe))]))
	var boss := _pick("ownerBossPick", [["titan", "Ashen Titan"], ["frosttroll_a", "Frost Troll — Krag"], ["frosttroll_b", "Frost Troll — Mog"]])
	box.add_child(_row([boss, _cheat_btn("spawn_boss", "Summon boss", "owner-", func(): return _val(boss)), _cheat_btn("titan", "Spawn Ashen Titan", "owner-")]))
	box.add_child(_row([_cheat_btn("spawn_worldboss", "Spawn World Boss", "owner-")]))
	box.add_child(VStyle.label("TELEPORT", 12, VStyle.GOLD2))
	var zone := _pick("ownerZone", [["village", "Kingdom / Main"], ["hydra", "Hydra Mire"], ["sailing", "Tidewrack Ocean"], ["frost", "Frost Cave"]])
	box.add_child(_row([zone, _cheat_btn("tp_zone", "Go zone", "owner-", func(): return _val(zone))]))
	box.add_child(VStyle.label("ONLINE (server-verified)", 12, VStyle.GOLD2))
	var pid := LineEdit.new(); pid.name = "ownerOnlineId"; pid.placeholder_text = "player id"; pid.custom_minimum_size = Vector2(150, 48)
	box.add_child(_row([_cheat_btn("online_list", "List online", "owner-"), pid, _cheat_btn("online_jump", "Teleport beside", "owner-", func(): return pid.text)]))
	box.add_child(_row([_btn("🔓 Lock owner", "owner-lock", func(): owner_cheat.emit("lock", true))]))
	box.add_child(VStyle.label("God mode starts ON for the owner; your choice is remembered.", 11, Color(1, 1, 1, 0.7)))

## CoOwner: server-verified password (Net coowner-auth). Only self-only play cheats; enforced again in Cheats.request().
func _coowner_card() -> void:
	var a = _api()
	var authed: bool = a != null and a.role() == "coowner"
	var box := _card("CoOwner tools", "Server-verified. Personal play cheats for your own hero only." if authed else "Join a multiplayer world, then unlock with the CoOwner password.", true)
	if not authed:
		var pw := LineEdit.new(); pw.name = "coownerPass"; pw.secret = true; pw.placeholder_text = "CoOwner password"; pw.custom_minimum_size = Vector2(200, 48)
		var st := VStyle.label("", 12, Color(1, 1, 1, 0.75))
		box.add_child(_row([pw, _btn("Unlock CoOwner", "coowner-unlock", func():
			if not Net.is_online(): st.text = "Join a multiplayer world first."; return
			if pw.text == "": st.text = "Enter the CoOwner password."; return
			st.text = "Verifying with the Varnethryl server…"
			if not Net.coowner_login(pw.text): st.text = "Cannot reach the Varnethryl server."
			pw.text = "")]))
		box.add_child(st)
		return
	_self_cheats(box, "coowner-")
	var pid := LineEdit.new(); pid.name = "coownerPlayerId"; pid.placeholder_text = "player id"; pid.custom_minimum_size = Vector2(150, 48)
	box.add_child(_row([pid, _cheat_btn("coowner_jump", "Teleport beside player", "coowner-", func(): return pid.text)]))
	box.add_child(_row([_btn("🔒 Lock CoOwner", "coowner-lock", func(): var a2 = _api(); if a2: a2.request("coowner_lock"); build())]))

