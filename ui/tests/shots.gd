extends Node
## Screenshots: VK_ICD_FILENAMES=... xvfb-run -a godot res://ui/tests/shots.tscn -- [--world]
const OUT := "/workspace/godot-wt/shots/ui/"
func _snap(n: String) -> void:
	for i in 6: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(OUT + n + ".png"); print("shot ", n)

func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var d := "user://shots_ui/"; DirAccess.make_dir_recursive_absolute(d)
	VSave.dir = d; VUI.gate.dir = d; VPrefs.path = d + "p.json"; VSave.state = VSave.fresh_state()
	if OS.get_cmdline_user_args().has("--world"):
		add_child(load("res://main.tscn").instantiate())
		for i in 60: await get_tree().process_frame
	var ui = VUI
	ui.show_title(); await _snap("01_title")
	ui.title.hide(); ui.open_heroes(true); await _snap("02_heroes")
	ui.heroes.hide(); ui._enter("solo"); VPrefs.prefs.showFps = true
	ui.hud.minimap.set_markers([{"pos": Vector2(8, -5), "color": Color.RED}, {"pos": Vector2(-10, 6), "color": Color("#5fd35f")}])
	ui.hud.minimap.set_player(Vector2.ZERO, 0.6); await _snap("03_hud_minimap")
	ui.toggle_menu(true); ui.quick.buttons.travel.pressed.emit(); await _snap("04_menu")
	ui.toggle_menu(false)
	for t in ["graphics", "controls", "gameplay"]:
		ui.settings.selected_tab = t; ui.open_settings(); await _snap("05_settings_" + t)
	for i in 5: ui.settings.tap_about(i * 100)
	await _snap("06_settings_owner_dev")
	ui.settings.is_owner = true; ui.settings.build(); await _snap("07_owner_cards_preview")
	ui.settings.is_owner = false; ui.settings.hide(); ui.owner_dlg.open_dialog(); await _snap("08_owner_gate")
	get_tree().quit()
