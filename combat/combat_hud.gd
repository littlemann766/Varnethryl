extends CanvasLayer
## Minimal combat buttons (attack + 3 skills + ultimate + hero switch) and HP/MP/fury readout.
## Lives in res://combat so the UI owner can restyle/replace it; it only calls Party/HeroCombat.
var party: Party
var btns: Array = []
var hero_btn: Button
var info: Label

func setup(p: Party) -> void:
	party = p
	layer = 5   # under the VUI layer (menu, settings, title)
	# Anchored to the bottom-right corner so it scales to any phone aspect (e.g. 2340x1080) and stays
	# clear of the joystick (bottom-left), the menu button and minimap (top-right, y < 230).
	# [offset from bottom-right corner (x, y) of the button's top-left, size]
	var lay := [[Vector2(-180, -180), 150], [Vector2(-300, -116), 96], [Vector2(-282, -236), 96], [Vector2(-176, -300), 96], [Vector2(-80, -280), 70], [Vector2(-80, -366), 70]]   # test 25: slot 5 = Owner's Holy Destruction
	for i in 6:
		var b := Button.new(); var sz: int = lay[i][1]
		b.anchor_left = 1; b.anchor_right = 1; b.anchor_top = 1; b.anchor_bottom = 1
		b.offset_left = lay[i][0].x; b.offset_top = lay[i][0].y; b.offset_right = lay[i][0].x + sz; b.offset_bottom = lay[i][0].y + sz
		b.focus_mode = Control.FOCUS_NONE; b.clip_text = true; b.add_theme_font_size_override("font_size", 16 if i else 26)
		b.add_theme_font_override("font", VStyle.font())
		b.button_down.connect(func(): party.combat.use(i))
		add_child(b); btns.append(b)
	hero_btn = Button.new(); hero_btn.position = Vector2(12, 96); hero_btn.size = Vector2(200, 48)
	hero_btn.focus_mode = Control.FOCUS_NONE; hero_btn.add_theme_font_size_override("font_size", 18); hero_btn.add_theme_font_override("font", VStyle.font())
	hero_btn.pressed.connect(func(): party.next_hero())
	add_child(hero_btn)
	info = Label.new(); info.position = Vector2(12, 150); info.add_theme_font_size_override("font_size", 18)
	info.add_theme_color_override("font_outline_color", Color.BLACK); info.add_theme_constant_override("outline_size", 6)
	add_child(info)

func _process(_dt: float) -> void:
	if party == null or party.combat.kit.is_empty(): return
	var sc := get_tree().current_scene; var sea = sc.get("sea") if sc else null
	var show: bool = not (VUI.title and VUI.title.visible) and VUI.hud.visible and bool(VPrefs.prefs.get("combat", true)) and not (sea != null and sea.active)   # test 32: no combat buttons while sailing
	if visible != show: visible = show
	if not show: return
	var c := party.combat
	btns[0].text = "ATK"
	for i in range(1, btns.size()):
		var s := c.skill(i)
		btns[i].visible = not s.is_empty()
		if s.is_empty(): continue
		var cd: float = c.st.cd[i]
		var nm: String = String(s.get("name", "-"))
		var t: String = ("%s\n%.0f" % [nm, ceil(cd)]) if cd > 0.0 else nm
		if btns[i].text != t:
			btns[i].text = t; btns[i].tooltip_text = String(s.get("name", ""))
			_fit(btns[i], 16)
		btns[i].disabled = not CombatRules.can_use(c.hero_id, i, s, c.st)
	hero_btn.text = "Hero: %s ▶" % HeroRoster.display_name(party.hero_id)
	info.text = "HP %d/%d  MP %d  SP %d  Fury %d" % [c.hp, c.max_hp, c.st.mp, c.st.sp, c.st.fury]


## Auto-shrink: wrap on words, then drop the font size until every line fits the button (min 9 px).
func _fit(b: Button, max_size: int) -> void:
	b.clip_text = false; b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var f: Font = b.get_theme_font("font")
	var w := b.size.x - 10.0; var h := b.size.y - 8.0
	var fs := max_size
	while fs > 9:
		var sz := f.get_multiline_string_size(b.text, HORIZONTAL_ALIGNMENT_CENTER, w, fs, -1, TextServer.BREAK_MANDATORY | TextServer.BREAK_WORD_BOUND)
		var widest := 0.0
		for word in b.text.split(" ", false): for part in word.split("\n", false): widest = maxf(widest, f.get_string_size(part, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x)
		if widest <= w and sz.y <= h: break
		fs -= 1
	b.add_theme_font_size_override("font_size", fs)
