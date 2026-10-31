extends RefCounted
class_name VStyle
## Colours/styles lifted from www/proto3d/varn-ui.css (#vnMenu) and settings3d.js (CSS2/CSS3).
const GOLD := Color("#f0d18a")
const GOLD2 := Color("#f1d98a")
const TEXT := Color("#f8e5bf")
const PARCH := Color("#d4c4a5")
const BORDER := Color("#b78d51")
static var _font: Font

static func font() -> Font:
	if _font == null:
		var base: Font = load("res://ui/fonts/Cinzel.woff") if ResourceLoader.exists("res://ui/fonts/Cinzel.woff") else ThemeDB.fallback_font
		# bundled fallbacks so ☰ ✕ ⚔ ⚙ ⛵ 🔒 🐉 render on every phone (Android has no system emoji for Godot)
		var fb: Array[Font] = []
		for f in ["res://ui/fonts/NotoSansSymbols2.ttf", "res://ui/fonts/NotoEmoji.ttf"]:
			if ResourceLoader.exists(f): fb.append(load(f))
		var fv := FontVariation.new(); fv.base_font = base; fv.fallbacks = fb
		_font = fv
	return _font

static func box(bg: Color, border: Color, bw := 1, radius := 6, pad := 10) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg; s.border_color = border
	s.set_border_width_all(bw); s.set_corner_radius_all(radius)
	s.content_margin_left = pad; s.content_margin_right = pad; s.content_margin_top = pad * 0.6; s.content_margin_bottom = pad * 0.6
	return s

static func make_theme() -> Theme:
	var t := Theme.new()
	t.default_font = font(); t.default_font_size = 16
	t.set_color("font_color", "Label", Color("#efe8ff"))
	# Button: dark steel-blue gradient look (#293a50 -> #101827), gold border.
	t.set_stylebox("normal", "Button", box(Color("#1c2a3e"), BORDER, 1, 5, 12))
	t.set_stylebox("hover", "Button", box(Color("#2a3d58"), Color("#e2bd5c"), 1, 5, 12))
	t.set_stylebox("pressed", "Button", box(Color("#b8892f"), Color("#f2dca3"), 1, 5, 12))
	t.set_stylebox("focus", "Button", box(Color(0, 0, 0, 0), Color("#fff1c2"), 2, 5, 12))
	t.set_stylebox("disabled", "Button", box(Color("#1a1f2a"), Color("#6b5a40"), 1, 5, 12))
	t.set_color("font_color", "Button", TEXT); t.set_color("font_hover_color", "Button", Color.WHITE)
	t.set_color("font_pressed_color", "Button", Color("#1a1224")); t.set_color("font_hover_pressed_color", "Button", Color("#1a1224"))
	t.set_color("font_focus_color", "Button", TEXT)
	t.set_constant("h_separation", "Button", 6)
	for k in ["normal", "focus"]:
		t.set_stylebox(k, "LineEdit", box(Color("#100c1c"), Color("#8a5cf6"), 1, 8, 10))
	t.set_stylebox("panel", "PanelContainer", box(Color("#12182a"), BORDER, 1, 9, 14))
	t.set_stylebox("normal", "OptionButton", box(Color("#2b2147"), Color(0.54, 0.36, 0.96, 0.33), 1, 12, 12))
	t.set_stylebox("hover", "OptionButton", box(Color("#3a2d5c"), Color("#c9a24a"), 1, 12, 12))
	t.set_stylebox("pressed", "OptionButton", box(Color("#3a2d5c"), Color("#c9a24a"), 1, 12, 12))
	return t

static func primary(b: Button) -> Button:
	b.add_theme_stylebox_override("normal", box(Color("#d0aa62"), Color("#f2dca3"), 1, 5, 12))
	b.add_theme_stylebox_override("hover", box(Color("#e4c689"), Color("#fff1c2"), 1, 5, 12))
	b.add_theme_color_override("font_color", Color("#151d2c")); b.add_theme_color_override("font_hover_color", Color("#151d2c"))
	return b

## gold "on" state like settings3d.js button.on
static func set_on(b: Button, on: bool) -> void:
	if on:
		b.add_theme_stylebox_override("normal", box(Color("#c9a24a"), Color("#e2bd5c"), 1, 12, 12))
		b.add_theme_color_override("font_color", Color("#1a1224"))
	else:
		b.add_theme_stylebox_override("normal", box(Color("#2b2147"), Color(0.54, 0.36, 0.96, 0.33), 1, 12, 12))
		b.add_theme_color_override("font_color", Color("#efe8ff"))

static func card(own := false) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", box(Color("#241a35cc") if own else Color("#1d1632cc"), Color("#c9a24a99") if own else Color("#6b3fd466"), 1, 14, 12))
	return p

static func label(text: String, size := 16, col := Color("#efe8ff")) -> Label:
	var l := Label.new(); l.text = text
	l.add_theme_font_size_override("font_size", size); l.add_theme_color_override("font_color", col)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l
