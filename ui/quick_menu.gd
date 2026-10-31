extends PanelContainer
## Port of #vnQuickMenu (☰ menu): Resume, Heroes, Travel, Multiplayer, Settings, Return to title.
signal resume
signal heroes
signal travel(dest: String)
signal multiplayer_world(world: String)
signal settings
signal return_to_title

const TRAVEL := [["town", "↩ Kingdom"], ["sail", "⛵ Tidewrack Ocean"], ["hydra", "🐉 Hydra Mire"]]
const WORLDS := ["Liongate-1", "Liongate-2", "Ashen-Ruins"]
var travel_box: VBoxContainer
var mp_box: VBoxContainer
var buttons := {}

func _ready() -> void:
	name = "QuickMenu"
	add_theme_stylebox_override("panel", VStyle.box(Color("#121a2bf2"), Color("#bd9859"), 2, 10, 14))
	set_anchors_preset(PRESET_TOP_RIGHT); custom_minimum_size = Vector2(320, 0)
	offset_left = -336; offset_right = -16; offset_top = 64
	var v := VBoxContainer.new(); v.add_theme_constant_override("separation", 8); add_child(v)
	var hd := HBoxContainer.new(); v.add_child(hd)
	var t := VStyle.label("VARNETHRYL", 18, VStyle.GOLD); t.size_flags_horizontal = SIZE_EXPAND_FILL; hd.add_child(t)
	var x := Button.new(); x.text = "✕"; x.custom_minimum_size = Vector2(44, 44); x.pressed.connect(func(): resume.emit()); hd.add_child(x)
	var g := GridContainer.new(); g.columns = 2; g.add_theme_constant_override("h_separation", 8); g.add_theme_constant_override("v_separation", 8); v.add_child(g)
	for d in [["resume", "▶ Resume"], ["heroes", "⚔ Heroes"], ["travel", "⌖ Travel"], ["mp", "⚔ Multiplayer"], ["settings", "⚙ Settings"], ["title", "⌂ Return to title"]]:
		var b := Button.new(); b.text = d[1]; b.name = "Q_" + d[0]; b.custom_minimum_size = Vector2(148, 48); b.size_flags_horizontal = SIZE_EXPAND_FILL
		b.add_theme_font_size_override("font_size", 14); g.add_child(b); buttons[d[0]] = b
	buttons.resume.pressed.connect(func(): resume.emit())
	buttons.heroes.pressed.connect(func(): heroes.emit())
	buttons.settings.pressed.connect(func(): settings.emit())
	buttons.title.pressed.connect(func(): return_to_title.emit())
	travel_box = _section(v, "World travel"); mp_box = _section(v, "Multiplayer · Worlds")
	for d in TRAVEL:
		var b := Button.new(); b.text = d[1]; b.name = "T_" + d[0]; var id: String = d[0]; b.pressed.connect(func(): travel.emit(id)); travel_box.add_child(b)
	for w in WORLDS:
		var b := Button.new(); b.text = "Join " + w; var ww: String = w; b.pressed.connect(func(): multiplayer_world.emit(ww)); mp_box.add_child(b)
	mp_box.add_child(VStyle.label("Server lobby hooks up in the multiplayer branch.", 11, VStyle.PARCH))
	# Accordion: only one section open at a time (varn-menu.js).
	buttons.travel.pressed.connect(func(): _toggle(travel_box))
	buttons.mp.pressed.connect(func(): _toggle(mp_box))

func _section(parent: Control, title: String) -> VBoxContainer:
	var b := VBoxContainer.new(); b.visible = false
	b.add_child(VStyle.label(title, 13, VStyle.GOLD2)); parent.add_child(b); return b

func _toggle(sec: VBoxContainer) -> void:
	var open := not sec.visible
	travel_box.visible = false; mp_box.visible = false; sec.visible = open
	buttons.travel.set_pressed_no_signal(false)

func close_sections() -> void:
	travel_box.visible = false; mp_box.visible = false
