class_name FlyControls
extends Control
## test 11 (boss: flying controllable outside the menu). On-screen ✈ Fly toggle + hold-to-climb ▲ / hold-to-descend ▼,
## a column just left of the combat skill cluster (bottom-right), clear of the joystick (bottom-left) and the skills.
## Shown only when the cheat role is owner or coowner (Cheats.role(), gate-verified - never taken from the UI).
## The toggle goes through Cheats.request("fly") so it stays in sync with the Owner/CoOwner menu toggle both ways.
const CLIMB_RATE := 8.0      # m/s of target altitude while ▲/▼ is held
const BTN := 84              # touch target (>= 48 dp at phone scale)
var cheats: Cheats
var main: Node
var fly_btn: Button
var up_btn: Button
var down_btn: Button
var hold := 0.0   # +1 while ▲ held, -1 while ▼ held (button_down/up, so multi-touch with the joystick works)

func _ready() -> void: build()

func build() -> void:
	if fly_btn: return
	name = "FlyControls"; set_anchors_and_offsets_preset(PRESET_FULL_RECT); mouse_filter = MOUSE_FILTER_IGNORE
	# skills occupy x in [-300, -30] from the right edge; this column sits at [-404, -320]
	fly_btn = _mk("FlyBtn", "✈ Fly", Vector2(-404, -116)); fly_btn.toggle_mode = true
	fly_btn.toggled.connect(func(on: bool): if cheats and bool(cheats.flags.get("fly", false)) != on: cheats.request("fly", on))
	up_btn = _mk("FlyUp", "▲", Vector2(-404, -312))
	down_btn = _mk("FlyDown", "▼", Vector2(-404, -214))
	up_btn.button_down.connect(func(): hold = 1.0); up_btn.button_up.connect(func(): hold = 0.0)
	down_btn.button_down.connect(func(): hold = -1.0); down_btn.button_up.connect(func(): hold = 0.0)
	_sync()

func _mk(nm: String, t: String, off: Vector2) -> Button:
	var b := Button.new(); b.name = nm; b.text = t; b.focus_mode = Control.FOCUS_NONE
	b.anchor_left = 1; b.anchor_right = 1; b.anchor_top = 1; b.anchor_bottom = 1
	b.offset_left = off.x; b.offset_top = off.y; b.offset_right = off.x + BTN; b.offset_bottom = off.y + BTN
	b.add_theme_font_size_override("font_size", 22 if t.length() > 2 else 34)
	add_child(b); return b

func allowed() -> bool:
	return cheats != null and (cheats.role() == "owner" or cheats.role() == "coowner")

func flying() -> bool: return cheats != null and bool(cheats.flags.get("fly", false))

func _sync() -> void:
	var ok := allowed()
	fly_btn.visible = ok
	var f := ok and flying()
	up_btn.visible = f; down_btn.visible = f
	if fly_btn.button_pressed != f: fly_btn.set_pressed_no_signal(f)

func step(dt: float) -> void:
	_sync()
	if not flying() or main == null: return
	if not up_btn.visible: hold = 0.0
	var d := hold
	if d != 0.0: main.fly_alt = clampf(main.fly_alt + d * CLIMB_RATE * dt, 0.0, 60.0)

func _process(dt: float) -> void: if fly_btn: step(dt)
