extends Control
## Hero roster (www/data.js HEROES, 20 heroes). Portraits are the JS assets/heroes/<id>.webp until 3D models land.
signal hero_selected(id: int)
signal closed

var grid: GridContainer
var detail: Label
var current := 0
var cards := []

func _ready() -> void:
	set_anchors_and_offsets_preset(PRESET_FULL_RECT); mouse_filter = MOUSE_FILTER_STOP
	var shade := ColorRect.new(); shade.color = Color(0.03, 0.03, 0.07, 0.92); shade.set_anchors_and_offsets_preset(PRESET_FULL_RECT); add_child(shade)
	var m := MarginContainer.new(); m.set_anchors_and_offsets_preset(PRESET_FULL_RECT)
	for k in ["left", "right", "top", "bottom"]: m.add_theme_constant_override("margin_" + k, 24)
	add_child(m)
	var v := VBoxContainer.new(); v.add_theme_constant_override("separation", 10); m.add_child(v)
	var top := HBoxContainer.new(); v.add_child(top)
	var t := VStyle.label("Choose a Hero", 30, VStyle.GOLD); t.size_flags_horizontal = SIZE_EXPAND_FILL; top.add_child(t)
	var x := Button.new(); x.text = "✕"; x.custom_minimum_size = Vector2(48, 48); x.name = "Close"; x.pressed.connect(func(): closed.emit()); top.add_child(x)
	detail = VStyle.label("", 14, VStyle.PARCH); v.add_child(detail)
	var sc := TouchScroll.new(); sc.size_flags_vertical = SIZE_EXPAND_FILL; v.add_child(sc)
	grid = GridContainer.new(); grid.columns = 5; grid.size_flags_horizontal = SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 10); grid.add_theme_constant_override("v_separation", 10); sc.add_child(grid)
	for h in VHeroData.all():
		var b := Button.new(); b.name = "Hero_%d" % h.id; b.custom_minimum_size = Vector2(0, 236); b.size_flags_horizontal = SIZE_EXPAND_FILL
		b.clip_contents = true
		var vb := VBoxContainer.new(); vb.set_anchors_and_offsets_preset(PRESET_FULL_RECT); vb.mouse_filter = MOUSE_FILTER_IGNORE; vb.offset_left = 6; vb.offset_right = -6; vb.offset_top = 6; vb.offset_bottom = -6
		var tr := TextureRect.new(); tr.texture = load(h.portrait); tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		tr.size_flags_vertical = SIZE_EXPAND_FILL; tr.mouse_filter = MOUSE_FILTER_IGNORE; vb.add_child(tr)
		var n := VStyle.label(h.name, 14, VStyle.GOLD); n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; n.mouse_filter = MOUSE_FILTER_IGNORE; vb.add_child(n)
		var c := VStyle.label("%s · %s" % [h.className, h.role], 11, VStyle.PARCH); c.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; c.mouse_filter = MOUSE_FILTER_IGNORE; vb.add_child(c)
		b.add_child(vb)
		var id: int = h.id
		b.pressed.connect(func(): select(id))
		grid.add_child(b); cards.append(b)

func open(active: int) -> void:
	current = active; _refresh(); show()

func select(id: int) -> void:
	current = id; _refresh(); hero_selected.emit(id)

func _refresh() -> void:
	for i in cards.size():
		var on: bool = i == current
		cards[i].add_theme_stylebox_override("normal", VStyle.box(Color("#3a2a12") if on else Color("#1c2a3e"), Color("#ffdd92") if on else VStyle.BORDER, 3 if on else 1, 8, 6))
	var h := VHeroData.get_hero(current)
	detail.text = "%s — %s (%s). %s · Skill: %s · Relic: %s   STR %d  DEF %d  AGI %d  MAG %d" % [h.name, h.className, h.role, h.weapon, h.skill, h.relic, h.str, h.def, h.agi, h.mag]
