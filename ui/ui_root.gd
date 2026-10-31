extends CanvasLayer
## Autoload "VUI": title → hero select → HUD + ☰ menu + settings. Owns no gameplay; talks to other branches via signals.
## HOOKS for other branches (connect in their _ready):
##   VUI.play_solo()                        title "Play Solo" (also fired on auto-resume)
##   VUI.multiplayer_requested(world)       title/menu multiplayer ("" = open lobby)
##   VUI.hero_selected(id)                  www/data.js hero index; save.active already updated
##   VUI.travel_requested(dest)             "town" | "sail" | "hydra"
##   VUI.returned_to_title()                session cleared; disconnect MP, stop combat
##   VUI.menu_toggled(open)                 pause input / camera while true
##   VUI.combat_toggled(on)
##   VUI.owner_cheat(key, value)            see settings_panel.gd; only fired when the owner gate passed
##   VUI.coowner_requested(), VUI.dev_action(key)
##   VPrefs.changed(prefs) + VPrefs.tier()  graphics tier 0..3 for scripts/main.gd apply_quality()
##   VUI.hud.minimap.set_player(Vector2(x,z), yaw) / set_map_texture(...)
##   VUI.set_fps(fps); VUI.get_snapshot = func() -> {x,z,yaw,zone,hero} for autosave
signal play_solo
signal multiplayer_requested(world: String)
signal hero_selected(id: int)
signal travel_requested(dest: String)
signal returned_to_title
signal menu_toggled(open: bool)
signal combat_toggled(on: bool)
signal owner_cheat(key: String, value)
signal coowner_requested
signal owner_set(on: bool)
signal dev_action(key: String)

## test 13: one source of truth = project setting application/config/version (export versionName matches)
static var VERSION: String = str(ProjectSettings.get_setting("application/config/version", "1.9.3"))
var root: Control
var title: Control
var heroes: Control
var quick: PanelContainer
var settings: PanelContainer
var hud: Control
var owner_dlg: PanelContainer
var gate := VOwnerGate.new()
var is_owner := false
var cheat_api = null   # combat/cheats.gd, set by scripts/main.gd (role-checked)
var mode := "solo"
var get_snapshot: Callable
var _autosave_t := 0.0
var _hero_from_title := false

func _ready() -> void:
	layer = 20; process_mode = Node.PROCESS_MODE_ALWAYS
	root = Control.new(); root.name = "UIRoot"; root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = VStyle.make_theme(); add_child(root)
	hud = preload("res://ui/hud.gd").new(); hud.version = VERSION; root.add_child(hud); hud.menu_pressed.connect(toggle_menu)
	quick = preload("res://ui/quick_menu.gd").new(); root.add_child(quick); quick.hide()
	quick.resume.connect(func(): toggle_menu(false))
	quick.heroes.connect(func(): toggle_menu(false); open_heroes(false))
	quick.settings.connect(func(): toggle_menu(false); open_settings())
	quick.return_to_title.connect(return_to_title)
	quick.travel.connect(func(d): toggle_menu(false); travel_requested.emit(d))
	quick.multiplayer_world.connect(func(w): toggle_menu(false); mode = "multi"; multiplayer_requested.emit(w))
	settings = preload("res://ui/settings_panel.gd").new(); settings.version = VERSION; root.add_child(settings); settings.hide()
	settings.closed.connect(func(): settings.hide())
	settings.customize_hud.connect(func(): settings.hide(); hud.begin_edit())
	settings.combat_toggled.connect(func(on): combat_toggled.emit(on))
	settings.owner_cheats_requested.connect(_owner_entry)
	settings.coowner_requested.connect(func(): coowner_requested.emit())
	settings.dev_action.connect(func(k): dev_action.emit(k))
	settings.owner_cheat.connect(_on_owner_cheat)
	heroes = preload("res://ui/hero_select.gd").new(); root.add_child(heroes); heroes.hide()
	heroes.hero_selected.connect(_pick_hero)
	heroes.closed.connect(func(): heroes.hide(); if _hero_from_title: title.show())
	title = preload("res://ui/title_screen.gd").new(); root.add_child(title)
	title.play_solo.connect(func(): _enter("solo"))
	title.multiplayer_pressed.connect(func(): _enter("multi"); multiplayer_requested.emit(""))
	title.choose_hero.connect(func(): title.hide(); open_heroes(true))
	title.settings.connect(func(): open_settings())
	owner_dlg = preload("res://ui/owner_dialog.gd").new(); owner_dlg.gate = gate; root.add_child(owner_dlg); owner_dlg.hide()
	owner_dlg.unlocked.connect(func(): _set_owner(true); open_settings(true))
	_set_owner(gate.is_owner())
	VPrefs.changed.connect(func(_p): hud.set_fps(Engine.get_frames_per_second(), VPrefs.prefs.showFps))
	# varn-menu.js: a recreated app resumes straight into the game, never the title.
	var s = VSave.read_session()
	if s and not OS.get_cmdline_user_args().has("--nosave"):
		mode = "multi" if s.get("mode") == "multi" else "solo"
		title.hide(); (func(): play_solo.emit()).call_deferred()
	else: show_title()

func _set_owner(v: bool) -> void:
	is_owner = v; settings.is_owner = v; owner_set.emit(v)
	if settings.visible: settings.build()

func show_title() -> void:
	quick.hide(); settings.hide(); heroes.hide(); title.show(); hud.visible = false; title.focus_play()

func _enter(m: String) -> void:
	mode = m; title.hide(); hud.visible = true
	_save_session()
	if m == "solo": play_solo.emit()

func open_heroes(from_title: bool) -> void:
	_hero_from_title = from_title; heroes.open(int(VSave.state.get("active", 0)))

func _pick_hero(id: int) -> void:
	var s: Dictionary = VSave.state
	if not s.unlocked.has(id): s.unlocked.append(id)
	if not s.party.has(id):
		if s.party.size() >= int(s.get("partyCap", 3)): s.party[s.party.size() - 1] = id
		else: s.party.append(id)
	s.active = id
	VSave.write_state(VSave.sanitize_party(s))
	hero_selected.emit(id)

func open_settings(hidden := false) -> void:
	if hidden: settings.unlock_hidden()
	else: settings.build()
	settings.show()

func toggle_menu(open = null) -> void:
	var o: bool = (not quick.visible) if open == null else open
	quick.visible = o
	if not o: quick.close_sections()
	menu_toggled.emit(o)

func return_to_title() -> void:
	toggle_menu(false); _save_now(); VSave.clear_session(); mode = "solo"
	returned_to_title.emit(); show_title()

func _owner_entry() -> void:
	if gate.is_owner(): _set_owner(true); settings.build(); owner_cheat.emit("panel", true)
	else: owner_dlg.open_dialog()

func _on_owner_cheat(key: String, value) -> void:
	if not gate.is_owner(): _set_owner(false); return
	if key == "lock": gate.lock(); _set_owner(false); return
	VSave.state["cheated"] = true; VSave.write_state()
	owner_cheat.emit(key, value)

func set_fps(fps: float) -> void: hud.set_fps(fps, VPrefs.prefs.showFps)

func _save_session() -> void:
	var snap: Dictionary = get_snapshot.call() if get_snapshot.is_valid() else {}
	VSave.save_session(mode, "", "", snap)
func _save_now() -> void:
	if get_snapshot.is_valid():
		var snap: Dictionary = get_snapshot.call()
		if not snap.is_empty(): VSave.write_snapshot(snap)
	if not title.visible: _save_session()

func _process(dt: float) -> void:
	if hud.visible and VPrefs.prefs.showFps: hud.set_fps(Engine.get_frames_per_second(), true)
	_autosave_t += dt
	if _autosave_t > 5.0: _autosave_t = 0.0; if not title.visible: _save_now()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_APPLICATION_FOCUS_OUT: _save_now()

func _unhandled_key_input(e: InputEvent) -> void:
	if not (e is InputEventKey and e.pressed and not e.echo): return
	var k: InputEventKey = e
	if k.ctrl_pressed and k.shift_pressed and k.keycode == KEY_G: _owner_entry(); return   # cheatboot.js
	if title.visible or k.ctrl_pressed or k.alt_pressed or k.meta_pressed: return
	if k.keycode == KEY_ESCAPE:
		if owner_dlg.visible: owner_dlg.hide()
		elif settings.visible: settings.hide()
		elif quick.visible: toggle_menu(false)
		else: open_settings()
	elif k.keycode == KEY_M: open_settings()
	elif k.keycode == KEY_QUOTELEFT: open_settings(true)
	elif k.keycode == KEY_P: return_to_title()
