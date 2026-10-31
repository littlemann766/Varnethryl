class_name TouchScroll extends ScrollContainer
## Phone-friendly scrolling: drag anywhere in the list (even starting on a button, slider or toggle)
## scrolls it. Presses inside are held back until the gesture is known: a vertical drag past
## DEADZONE scrolls (with fling inertia), a tap or a horizontal drag is replayed to the control.

const DEADZONE := 14.0
const FRICTION := 4.0  # 1/s exponential decay of fling speed

var _down := false
var _dragging := false
var _replaying := false
var _start := Vector2.ZERO
var _press: InputEventMouseButton
var _vel := 0.0
var _last_t := 0
var _scroll := 0.0

func _ready() -> void:
	horizontal_scroll_mode = SCROLL_MODE_DISABLED
	scroll_deadzone = int(DEADZONE)
	var bar := get_v_scroll_bar()
	bar.custom_minimum_size.x = 16
	var g := StyleBoxFlat.new(); g.bg_color = Color("#c9a24acc"); g.set_corner_radius_all(8); g.content_margin_left = 16
	var tr := StyleBoxFlat.new(); tr.bg_color = Color("#ffffff22"); tr.set_corner_radius_all(8); tr.content_margin_left = 16
	for s in ["grabber", "grabber_highlight", "grabber_pressed"]: bar.add_theme_stylebox_override(s, g)
	bar.add_theme_stylebox_override("scroll", tr)
	set_process(false)

func _inside(p: Vector2) -> bool:
	return is_visible_in_tree() and get_global_rect().has_point(p) and not get_v_scroll_bar().get_global_rect().has_point(p)

func _input(e: InputEvent) -> void:
	if _replaying: return
	if (e is InputEventScreenDrag or e is InputEventScreenTouch) and (_down or _inside(e.position)):
		get_viewport().set_input_as_handled(); return  # the emulated mouse events drive us; stop the built-in double scroll
	if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT:
		if e.pressed and _inside(e.position):
			_down = true; _dragging = false; _start = e.position; _press = e.duplicate(); _vel = 0.0
			_scroll = scroll_vertical; _last_t = Time.get_ticks_usec(); set_process(false)
			get_viewport().set_input_as_handled()
		elif not e.pressed and _down:
			_down = false
			if _dragging:
				get_viewport().set_input_as_handled(); _dragging = false
				if absf(_vel) > 60.0: set_process(true)
			else:  # a tap: give the control its press + release
				get_viewport().set_input_as_handled(); _replay(_press); _replay(e)
	elif e is InputEventMouseMotion and _down:
		var d: Vector2 = e.position - _start
		if not _dragging:
			if absf(d.y) > DEADZONE and absf(d.y) > absf(d.x): _dragging = true
			elif absf(d.x) > DEADZONE:  # horizontal (slider): hand the gesture over
				_down = false; get_viewport().set_input_as_handled(); _replay(_press); _replay(e); return
			else:
				get_viewport().set_input_as_handled(); return
		var now := Time.get_ticks_usec(); var dt := maxf((now - _last_t) / 1e6, 0.001); _last_t = now
		var dy: float = -e.relative.y
		_vel = lerpf(_vel, dy / dt, 0.5)
		_scroll = clampf(_scroll + dy, 0.0, _max()); scroll_vertical = int(_scroll)
		get_viewport().set_input_as_handled()

func drag_by(dy: float) -> void:  ## for tests/benches
	_scroll = clampf(scroll_vertical + dy, 0.0, _max()); scroll_vertical = int(_scroll)

func _max() -> float:
	var b := get_v_scroll_bar(); return maxf(b.max_value - b.page, 0.0)

var _queue: Array[InputEvent] = []
func _replay(ev: InputEvent) -> void:
	# deferred: pushing input from inside _input is swallowed by the handled flag of the current event
	_queue.append(ev.duplicate())
	if _queue.size() == 1: _flush.call_deferred()
func _flush() -> void:
	var q := _queue.duplicate(); _queue.clear()
	_replaying = true
	for ev in q: get_viewport().push_input(ev, true)  # already in viewport coords
	_replaying = false

func _process(delta: float) -> void:
	_vel *= exp(-FRICTION * delta)
	_scroll = clampf(_scroll + _vel * delta, 0.0, _max()); scroll_vertical = int(_scroll)
	if absf(_vel) < 20.0 or _scroll <= 0.0 or _scroll >= _max(): set_process(false)

func flinging() -> bool: return is_processing()
