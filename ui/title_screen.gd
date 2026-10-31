extends Control
## Port of the #vnMenu title card (proto3d.html + varn-ui.css, v1.5.33 look).
signal play_solo
signal multiplayer_pressed
signal choose_hero
signal settings

var buttons := {}

func _ready() -> void:
	set_anchors_and_offsets_preset(PRESET_FULL_RECT); mouse_filter = MOUSE_FILTER_STOP
	var bg := TextureRect.new(); bg.texture = load("res://ui/assets/poster.webp")
	bg.set_anchors_and_offsets_preset(PRESET_FULL_RECT); bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	add_child(bg)
	var shade := ColorRect.new(); shade.color = Color(0.03, 0.04, 0.08, 0.80); shade.set_anchors_and_offsets_preset(PRESET_FULL_RECT); add_child(shade)
	var center := CenterContainer.new(); center.set_anchors_and_offsets_preset(PRESET_FULL_RECT); add_child(center)
	var card := PanelContainer.new()
	var sb := VStyle.box(Color("#1a2438f4"), Color("#bd9859"), 2, 9, 34)
	sb.shadow_color = Color(0, 0, 0, 0.7); sb.shadow_size = 24
	card.add_theme_stylebox_override("panel", sb); card.custom_minimum_size = Vector2(560, 0)
	center.add_child(card)
	var v := VBoxContainer.new(); v.alignment = BoxContainer.ALIGNMENT_CENTER; v.add_theme_constant_override("separation", 8); card.add_child(v)
	var em := TextureRect.new(); em.texture = load("res://ui/assets/emblem.webp"); em.custom_minimum_size = Vector2(128, 128)
	em.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; em.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED; v.add_child(em)
	var h := VStyle.label("VARNETHRYL", 46, VStyle.GOLD); h.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	h.add_theme_color_override("font_shadow_color", Color.BLACK); h.add_theme_constant_override("shadow_offset_y", 3); v.add_child(h)
	var lg := VStyle.label("Legends Are Forged. Kingdoms Are Conquered.", 15, VStyle.PARCH); lg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; v.add_child(lg)
	var ver := VStyle.label("VARNETHRYL v" + str(ProjectSettings.get_setting("application/config/version", "1.9.3")), 12, VStyle.PARCH); ver.name = "Version"; ver.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; v.add_child(ver)
	var rule := ColorRect.new(); rule.color = Color("#b48c4d"); rule.custom_minimum_size = Vector2(340, 1); rule.size_flags_horizontal = SIZE_SHRINK_CENTER; v.add_child(rule)
	var acts := VBoxContainer.new(); acts.custom_minimum_size = Vector2(340, 0); acts.size_flags_horizontal = SIZE_SHRINK_CENTER; acts.add_theme_constant_override("separation", 10); v.add_child(acts)
	for d in [["play", "Play Solo", "play_solo"], ["mp", "⚔ Multiplayer · Join World", "multiplayer_pressed"], ["hero", "Choose a Hero", "choose_hero"], ["settings", "Settings", "settings"]]:
		var b := Button.new(); b.text = d[1]; b.custom_minimum_size = Vector2(0, 46); b.name = "Btn_" + d[0]
		b.add_theme_font_size_override("font_size", 15)
		var sig: String = d[2]; b.pressed.connect(func(): emit_signal(sig))
		if d[0] == "play": VStyle.primary(b)
		acts.add_child(b); buttons[d[0]] = b
	var bot := VStyle.label("Your adventure continues from the existing local save. Nothing is reset.", 12, Color("#bfb39a"))
	bot.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; v.add_child(bot)

func focus_play() -> void: buttons.play.grab_focus()
