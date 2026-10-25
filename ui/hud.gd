extends Control
## HUD shell: version/fps badge (#hud), ☰ Menu button (#vnMenuBtn), minimap. Customize HUD = drag to move, Save HUD.
signal menu_pressed
const LAYOUT_PATH := "user://vn_hud_layout.json"
var badge: Label
var menu_btn: Button
var minimap: Control
var editing := false
var drag_target: Control
var drag_off := Vector2.ZERO
var edit_bar: HBoxContainer
var version: String = str(ProjectSettings.get_setting("application/config/version", "1.9.3"))
var movable: Array[Control] = []
var defaults := {}

func _ready() -> void:
	name = "HUD"; set_anchors_and_offsets_preset(PRESET_FULL_RECT); mouse_filter = MOUSE_FILTER_IGNORE
	badge = VStyle.label("VARNETHRYL v" + version, 14, VStyle.GOLD); badge.name = "Badge"; badge.autowrap_mode = TextServer.AUTOWRAP_OFF
	badge.position = Vector2(12, 10); badge.add_theme_color_override("font_shadow_color", Color.BLACK); badge.add_theme_constant_override("shadow_offset_y", 2); add_child(badge)
	menu_btn = Button.new(); menu_btn.name = "MenuBtn"; menu_btn.text = "☰ Menu"; menu_btn.size = Vector2(110, 44)
	menu_btn.anchor_left = 1; menu_btn.anchor_right = 1; menu_btn.offset_left = -126; menu_btn.offset_right = -16; menu_btn.offset_top = 10; menu_btn.offset_bottom = 54; menu_btn.pressed.connect(func(): if not editing: menu_pressed.emit()); add_child(menu_btn)
	minimap = preload("res://ui/minimap.gd").new(); add_child(minimap); minimap.anchor_left = 1; minimap.anchor_right = 1; minimap.offset_left = -186; minimap.offset_right = -16; minimap.offset_top = 60; minimap.offset_bottom = 230
	movable = [menu_btn, minimap]
	for m in movable: defaults[m.name] = Vector4(m.offset_left, m.offset_top, m.offset_right, m.offset_bottom)
	edit_bar = HBoxContainer.new(); edit_bar.visible = false; edit_bar.set_anchors_preset(PRESET_CENTER); add_child(edit_bar)
	edit_bar.add_child(VStyle.label("Drag controls to move them", 14, VStyle.GOLD))
	for d in [["Save HUD", func(): end_edit(true)], ["Reset", func(): reset_layout()], ["Cancel", func(): end_edit(false)]]:
		var b := Button.new(); b.text = d[0]; b.custom_minimum_size = Vector2(90, 44); b.pressed.connect(d[1]); edit_bar.add_child(b)
	load_layout()

func set_fps(fps: float, show: bool) -> void:
	badge.text = "VARNETHRYL v%s%s" % [version, ("   %d fps" % roundi(fps)) if show else ""]

func begin_edit() -> void:
	editing = true; edit_bar.visible = true
	for m in movable: m.modulate = Color(1, 1, 0.7, 0.85)
func end_edit(save: bool) -> void:
	editing = false; edit_bar.visible = false
	for m in movable: m.modulate = Color.WHITE
	if save: save_layout()
	else: load_layout()
func reset_layout() -> void:
	for m in movable:
		var o: Vector4 = defaults[m.name]; m.offset_left = o.x; m.offset_top = o.y; m.offset_right = o.z; m.offset_bottom = o.w

func save_layout() -> void:
	var d := {}
	for m in movable: d[m.name] = [m.position.x, m.position.y]
	var f := FileAccess.open(LAYOUT_PATH, FileAccess.WRITE)
	if f: f.store_string(JSON.stringify(d))
func load_layout() -> void:
	reset_layout()
	if not FileAccess.file_exists(LAYOUT_PATH): return
	var d = JSON.parse_string(FileAccess.get_file_as_string(LAYOUT_PATH))
	if typeof(d) != TYPE_DICTIONARY: return
	for m in movable:
		if d.has(m.name) and d[m.name] is Array: m.position = Vector2(d[m.name][0], d[m.name][1]).clamp(Vector2.ZERO, size - m.size)

func _input(e: InputEvent) -> void:
	if not editing: return
	var pos: Vector2
	if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT or e is InputEventScreenTouch:
		pos = e.position
		if e.pressed:
			for m in movable:
				if Rect2(m.position, m.size).has_point(pos): drag_target = m; drag_off = pos - m.position; get_viewport().set_input_as_handled()
		else: drag_target = null
	elif (e is InputEventMouseMotion or e is InputEventScreenDrag) and drag_target:
		drag_target.position = (e.position - drag_off).clamp(Vector2.ZERO, size - drag_target.size); get_viewport().set_input_as_handled()
