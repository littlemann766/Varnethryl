extends Node
## Desktop window chrome only. Does not change gameplay or Net.
## Mobile and headless runs leave the window alone.

func _desktop() -> bool:
	if DisplayServer.get_name() == "headless":
		return false
	if OS.has_feature("mobile") or OS.get_name() == "Android" or OS.get_name() == "iOS":
		return false
	return true

func _ready() -> void:
	if not _desktop():
		return
	var win := get_window()
	if win == null:
		return
	win.unresizable = false
	# project.godot asks for a maximized 1600x900 window; set it again once the window exists.
	win.mode = Window.MODE_MAXIMIZED

func _unhandled_input(e: InputEvent) -> void:
	if not _desktop():
		return
	if not (e is InputEventKey and e.pressed and not e.echo):
		return
	var k := e as InputEventKey
	var toggle := k.keycode == KEY_F11 or (k.alt_pressed and (k.keycode == KEY_ENTER or k.keycode == KEY_KP_ENTER))
	if not toggle:
		return
	var win := get_window()
	if win.mode == Window.MODE_FULLSCREEN or win.mode == Window.MODE_EXCLUSIVE_FULLSCREEN:
		win.mode = Window.MODE_WINDOWED
		win.mode = Window.MODE_MAXIMIZED
	else:
		win.mode = Window.MODE_FULLSCREEN
	get_viewport().set_input_as_handled()
