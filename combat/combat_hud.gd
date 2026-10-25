extends CanvasLayer
## Minimal combat buttons (attack + 3 skills + ultimate + hero switch) and HP/MP/fury readout.
## Lives in res://combat so the UI owner can restyle/replace it; it only calls Party/HeroCombat.
var party: Party
var btns: Array = []
var hero_btn: Button
var info: Label

func setup(p: Party) -> void:
	party = p
	var vw := Vector2(1280, 720)
	var pos := [Vector2(1100, 540), Vector2(960, 600), Vector2(990, 470), Vector2(1100, 400), Vector2(1200, 410)]
	var sizes := [150, 96, 96, 96, 70]
	for i in 5:
		var b := Button.new(); b.position = pos[i]; b.size = Vector2(sizes[i], sizes[i])
		b.focus_mode = Control.FOCUS_NONE; b.add_theme_font_size_override("font_size", 18 if i else 26)
		b.button_down.connect(func(): party.combat.use(i))
		add_child(b); btns.append(b)
	hero_btn = Button.new(); hero_btn.position = Vector2(12, 300); hero_btn.size = Vector2(200, 56)
	hero_btn.focus_mode = Control.FOCUS_NONE; hero_btn.add_theme_font_size_override("font_size", 20)
	hero_btn.pressed.connect(func(): party.next_hero())
	add_child(hero_btn)
	info = Label.new(); info.position = Vector2(12, 360); info.add_theme_font_size_override("font_size", 20)
	info.add_theme_color_override("font_outline_color", Color.BLACK); info.add_theme_constant_override("outline_size", 6)
	add_child(info)

func _process(_dt: float) -> void:
	if party == null or party.combat.kit.is_empty(): return
	var c := party.combat
	btns[0].text = "ATK"
	for i in range(1, 5):
		var s := c.skill(i)
		var cd: float = c.st.cd[i]
		var nm: String = String(s.get("name", "-")).substr(0, 9)
		btns[i].text = ("%s\n%.0f" % [nm, ceil(cd)]) if cd > 0.0 else nm
		btns[i].disabled = not CombatRules.can_use(c.hero_id, i, s, c.st)
	hero_btn.text = "Hero: %s ▶" % HeroRoster.display_name(party.hero_id)
	info.text = "HP %d/%d  MP %d  SP %d  Fury %d" % [c.hp, c.max_hp, c.st.mp, c.st.sp, c.st.fury]
