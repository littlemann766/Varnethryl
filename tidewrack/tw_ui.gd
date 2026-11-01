class_name TwUi
extends CanvasLayer
## test 32: Tidewrack Sea HUD: context prompt (Set sail / Launch skiff / Dive / Shipwright...), gust charm, Harbour Charts,
## Shipwright panel, toast, and the black fade used for every teleport (cave mouths, dive, fast travel).
var sea: Node
var prompt: Button
var gust_b: Button
var charts_b: Button
var night_b: Button   # quests-test: Wren's night sailing
var panel: PanelContainer
var veil: ColorRect
var msg: Label
var _cb := Callable()

func _ready() -> void:
	layer = 40
	prompt = _b("", Vector2(-160, -470), func(): if _cb.is_valid(): _cb.call()); prompt.visible = false
	gust_b = _b("Gust", Vector2(-420, -470), func(): if sea.ship and sea.ship.gust(): toast("Gust!"))
	charts_b = _b("Charts", Vector2(-560, -470), open_charts)
	# right-hand sea button row (Gust -420, Night -290, prompt -160), clear of the ship in the middle of the screen
	night_b = _b("Night", Vector2(-290, -470), func(): sea.toggle_night()); night_b.visible = false
	# test 36 (boss: toast sat on the HP/MP line): top-centre, under the badge row, clear of the minimap and Menu button
	msg = Label.new(); msg.name = "Toast"; msg.add_theme_font_size_override("font_size", 26); msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	msg.add_theme_color_override("font_shadow_color", Color.BLACK); msg.add_theme_constant_override("shadow_offset_y", 2)
	msg.anchor_left = 0.5; msg.anchor_right = 0.5; msg.offset_left = 0; msg.offset_right = 0; msg.offset_top = 16; msg.grow_horizontal = Control.GROW_DIRECTION_BOTH; add_child(msg)
	veil = ColorRect.new(); veil.color = Color(0, 0, 0, 0); veil.set_anchors_preset(Control.PRESET_FULL_RECT); veil.mouse_filter = Control.MOUSE_FILTER_IGNORE; add_child(veil)
func _b(t: String, off: Vector2, cb: Callable) -> Button:
	var b := Button.new(); b.text = t; b.custom_minimum_size = Vector2(130, 64); b.add_theme_font_size_override("font_size", 22)
	b.anchor_left = 1.0; b.anchor_right = 1.0; b.anchor_top = 1.0; b.anchor_bottom = 1.0; b.position = off; b.pressed.connect(cb); add_child(b); return b
func _process(_dt: float) -> void:
	var on: bool = sea.active and not sea.diving and sea.in_cave == ""
	gust_b.visible = on and sea.ship != null and sea.ship.tier > 0
	if gust_b.visible: gust_b.text = "Gust" if sea.ship.gust_cd <= 0.0 else "Gust %ds" % int(ceil(sea.ship.gust_cd))
	charts_b.visible = on and sea.ship != null and sea.ship.kind == "galleon" and charts_here()
	night_b.visible = on and sea.sailing() and sea.has_night_sailing()
	if night_b.visible: night_b.text = "Day" if sea.is_night() else "Night"
	if not sea.active:   # on land: "Set sail" beside the moored galleon at the Tidewrack main pier
		var g: Array = sea.m._galleon_pier()
		var near: bool = sea.m.hero.global_position.distance_to(g[0]) < 14.0
		set_prompt("Set sail" if near else "", (func(): fade(func(): sea.enter())) if near else Callable())
## test 36 (boss: Charts showed far inland): Harbour Charts only aboard, or ashore within 12 m of the pier (18 m of the moored ship / pier.
func charts_here() -> bool:   # test 36: never while the ship flies; afloat only near a harbour / landing
	if sea.ship.alt > 0.5: return false
	if sea.ashore == "":
		var p := Vector2(sea.ship.position.x, sea.ship.position.z)
		for k in sea.ports():
			var a = sea.ports()[k][1]
			if a != null and p.distance_to(Vector2(a.x, a.z)) < 180.0: return true
		return sea.landing_near(p, 60.0) != ""
	var L: Dictionary = sea.landing(sea.ashore); var lp: Vector3 = sea.to_local(sea.m.hero.global_position)
	return lp.distance_to(sea.pier_head(L)) < 12.0 or lp.distance_to(sea.ship.position) < 18.0
func set_prompt(t: String, cb: Callable) -> void:
	prompt.visible = t != ""; prompt.text = t; _cb = cb
func toast(t: String) -> void:
	if msg.text == t: return
	msg.text = t; get_tree().create_timer(3.0).timeout.connect(func(): if msg.text == t: msg.text = "")
func fade(mid: Callable, hold := 0.35) -> void:
	var tw := create_tween(); tw.tween_property(veil, "color:a", 1.0, 0.35)
	tw.tween_callback(mid); tw.tween_interval(hold); tw.tween_property(veil, "color:a", 0.0, 0.45)
func _panel(title: String) -> VBoxContainer:
	if panel: panel.queue_free()
	panel = PanelContainer.new(); panel.position = Vector2(500, 120); add_child(panel)
	var v := VBoxContainer.new(); panel.add_child(v)
	var l := Label.new(); l.text = title; l.add_theme_font_size_override("font_size", 28); v.add_child(l)
	return v
func _row(v: VBoxContainer, t: String, cb: Callable) -> void:
	var b := Button.new(); b.text = t; b.custom_minimum_size = Vector2(520, 56); b.add_theme_font_size_override("font_size", 22); b.pressed.connect(cb); v.add_child(b)
func open_charts() -> void:
	var v := _panel("Harbour Charts")
	var P: Dictionary = sea.ports()
	for k in P:
		if sea.save.discovered_ports.has(k): _row(v, P[k][0], func(): var e: String = sea.chart_travel(k); panel.queue_free(); if e != "": toast(e))
	_row(v, "Close", func(): panel.queue_free())
func open_shipwright() -> void:
	var v := _panel("Gullhaven Shipwright")
	for kind in ["galleon", "skiff"]:
		var t := int(sea.save.get(kind + "_tier", 0))
		var nm: String = ["Base", "Patched Canvas", "Gullwing Rig", "Stormsilk"][mini(t + 1, 3)]
		var cost: Array = sea.COST.get(t + 1, [0, {}])
		var txt := "%s: T%d -> T%d %s (%d gold%s)" % [kind.capitalize(), t, t + 1, nm, cost[0], "".join(cost[1].keys().map(func(i): return " + %d %s" % [cost[1][i], i]))] if t < 3 else "%s: T3 Stormsilk (max)" % kind.capitalize()
		_row(v, txt, func(): var e: String = sea.upgrade(kind); panel.queue_free(); toast(e if e != "" else "%s upgraded." % kind.capitalize()))
	_row(v, "Close", func(): panel.queue_free())
