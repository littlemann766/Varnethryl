class_name FlyControls
extends Control
## test 11 (boss: flying controllable outside the menu) + test 13 changes:
## - ✈ Fly shows ONLY once the Fly cheat is on in the cheats menu (owner/coowner, Cheats.role() gate-verified).
##   The button toggles real flight (main.set_flight); turning the cheat off hides ✈ ▲ ▼ and ends flight with a soft landing.
## - ⤒ Jump for every hero, right-thumb spot above the skill cluster; ~1.2 m, floor-only (no double jump).
##   While flying it acts as Up (hold).
const CLIMB_RATE := 8.0      # m/s of target altitude while ▲/▼ (or Jump in flight) is held
const BTN := 84              # touch target (>= 48 dp at phone scale)
const JUMP_OFF := Vector2(-124, -394)   # above the top-right skills, clear of ATK/skills/Fly column
var cheats: Cheats
var main: Node
var fly_btn: Button
var up_btn: Button
var down_btn: Button
var jump_btn: Button
var hold := 0.0   # +1 while ▲ held, -1 while ▼ held (button_down/up, so multi-touch with the joystick works)
var jump_hold := false

func _ready() -> void: build()

func build() -> void:
	if fly_btn: return
	name = "FlyControls"; set_anchors_and_offsets_preset(PRESET_FULL_RECT); mouse_filter = MOUSE_FILTER_IGNORE
	# skills occupy x in [-300, -30] from the right edge; this column sits at [-404, -320]
	fly_btn = _mk("FlyBtn", "✈ Fly", Vector2(-404, -116)); fly_btn.toggle_mode = true
	fly_btn.toggled.connect(func(on: bool): if main and main.has_method("set_flight"): main.set_flight(on and unlocked()))
	up_btn = _mk("FlyUp", "▲", Vector2(-404, -312))
	down_btn = _mk("FlyDown", "▼", Vector2(-404, -214))
	up_btn.button_down.connect(func(): hold = 1.0); up_btn.button_up.connect(func(): hold = 0.0)
	down_btn.button_down.connect(func(): hold = -1.0); down_btn.button_up.connect(func(): hold = 0.0)
	jump_btn = _mk("JumpBtn", "⤒ Jump", JUMP_OFF)
	jump_btn.button_down.connect(_jump_down); jump_btn.button_up.connect(func(): jump_hold = false)
	_sync()

func _jump_down() -> void:
	if flying(): jump_hold = true
	elif main and main.has_method("request_jump"): main.request_jump()

func _mk(nm: String, t: String, off: Vector2) -> Button:
	var b := Button.new(); b.name = nm; b.text = t; b.focus_mode = Control.FOCUS_NONE
	b.anchor_left = 1; b.anchor_right = 1; b.anchor_top = 1; b.anchor_bottom = 1
	b.offset_left = off.x; b.offset_top = off.y; b.offset_right = off.x + BTN; b.offset_bottom = off.y + BTN
	b.add_theme_font_size_override("font_size", 20 if t.length() > 2 else 34)
	add_child(b); return b

func allowed() -> bool:
	return cheats != null and (cheats.role() == "owner" or cheats.role() == "coowner")

## the menu's Fly cheat unlocks the HUD button
func unlocked() -> bool: return allowed() and bool(cheats.flags.get("fly", false))

func flying() -> bool: return unlocked() and main != null and bool(main.get("flight"))

func _sync() -> void:
	var u := unlocked()
	fly_btn.visible = u
	if not u and main and bool(main.get("flight")): main.set_flight(false)   # cheat off -> land safely
	var f := flying()
	up_btn.visible = f; down_btn.visible = f
	if fly_btn.button_pressed != f: fly_btn.set_pressed_no_signal(f)
	# test 14 (boss: duplicate "▲ Up"): in flight the HUD ▲/▼ pair climbs; Jump hides instead of becoming a 2nd Up
	jump_btn.visible = not f; jump_btn.text = "⤒ Jump"

func step(dt: float) -> void:
	_sync()
	if not flying() or main == null: jump_hold = false; return
	if not up_btn.visible: hold = 0.0
	var d := hold if hold != 0.0 else (1.0 if jump_hold else 0.0)
	# test 16: climb rate scales with altitude (8 m/s near the ground, ~0.6x altitude up high, max 900 m/s); owner has no ceiling
	var rate := CLIMB_RATE if main.fly_alt < 60.0 else minf(CLIMB_RATE + (float(main.fly_alt) - 60.0) * 0.6, 900.0)
	if d != 0.0: main.fly_alt = clampf(main.fly_alt + d * rate * dt, 0.0, cheats.fly_cap() if cheats else 60.0)

func _process(dt: float) -> void: if fly_btn: step(dt)
