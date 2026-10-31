class_name TwUi
extends CanvasLayer
## test 32: Tidewrack Sea HUD: context prompt (Set sail / Launch skiff / Dive / Shipwright...), gust charm, Harbour Charts,
## Shipwright panel, toast, and the black fade used for every teleport (cave mouths, dive, fast travel).
var sea: Node
var prompt: Button
var gust_b: Button
var charts_b: Button
var panel: PanelContainer
var veil: ColorRect
var msg: Label
var _cb := Callable()

func _ready() -> void:
	layer = 40
	prompt = _b("", Vector2(-160, -470), func(): if _cb.is_valid(): _cb.call()); prompt.visible = false
	gust_b = _b("Gust", Vector2(-420, -470), func(): if sea.ship and sea.ship.gust(): toast("Gust!"))
	charts_b = _b("Charts", Vector2(-560, -470), open_charts)
	msg = Label.new(); msg.position = Vector2(40, 160); msg.add_theme_font_size_override("font_size", 26); add_child(msg)
	veil = ColorRect.new(); veil.color = Color(0, 0, 0, 0); veil.set_anchors_preset(Control.PRESET_FULL_RECT); veil.mouse_filter = Control.MOUSE_FILTER_IGNORE; add_child(veil)
func _b(t: String, off: Vector2, cb: Callable) -> Button:
	var b := Button.new(); b.text = t; b.custom_minimum_size = Vector2(130, 64); b.add_theme_font_size_override("font_size", 22)
	b.anchor_left = 1.0; b.anchor_right = 1.0; b.anchor_top = 1.0; b.anchor_bottom = 1.0; b.position = off; b.pressed.connect(cb); add_child(b); return b
func _process(_dt: float) -> void:
	var on: bool = sea.active and not sea.diving and sea.in_cave == ""
	gust_b.visible = on and sea.ship != null and sea.ship.tier > 0
	if gust_b.visible: gust_b.text = "Gust" if sea.ship.gust_cd <= 0.0 else "Gust %ds" % int(ceil(sea.ship.gust_cd))
	charts_b.visible = on and sea.ship != null and sea.ship.kind == "galleon"
	if not sea.active:   # on land: "Set sail" beside the moored galleon at the Tidewrack main pier
		var g: Array = sea.m._galleon_pier()
		var near: bool = sea.m.hero.global_position.distance_to(g[0]) < 14.0
		set_prompt("Set sail" if near else "", (func(): fade(func(): sea.enter())) if near else Callable())
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
