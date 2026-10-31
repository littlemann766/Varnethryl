extends PanelContainer
## Passphrase prompt for the Owner gate (cheatpanel.js flow). Text is secret, never logged.
signal unlocked
var gate: VOwnerGate
var field: LineEdit
var msg: Label
var btn: Button

func _ready() -> void:
	name = "OwnerDialog"
	add_theme_stylebox_override("panel", VStyle.box(Color("#171127f8"), Color("#c9a24a"), 2, 14, 16))
	custom_minimum_size = Vector2(380, 0); set_anchors_and_offsets_preset(PRESET_CENTER, PRESET_MODE_MINSIZE)
	var v := VBoxContainer.new(); v.add_theme_constant_override("separation", 8); add_child(v)
	v.add_child(VStyle.label("🔒 Owner Cheats", 18, VStyle.GOLD2))
	field = LineEdit.new(); field.secret = true; field.max_length = VOwnerGate.MAX_PASS_LEN; field.placeholder_text = "Owner passphrase"; field.custom_minimum_size = Vector2(0, 46); v.add_child(field)
	field.text_submitted.connect(func(_t): _go())
	var h := HBoxContainer.new(); v.add_child(h)
	btn = Button.new(); btn.text = "Unlock"; btn.custom_minimum_size = Vector2(0, 46); btn.size_flags_horizontal = SIZE_EXPAND_FILL; btn.pressed.connect(_go); h.add_child(btn)
	var c := Button.new(); c.text = "Cancel"; c.custom_minimum_size = Vector2(0, 46); c.pressed.connect(func(): hide()); h.add_child(c)
	msg = VStyle.label("", 12, VStyle.PARCH); v.add_child(msg)

func open_dialog() -> void:
	field.text = ""; msg.text = ""; show(); field.grab_focus()
	var st := gate.status()
	if st.locked: msg.text = "Too many tries. Wait %ds." % ceili(st.retryMs / 1000.0)

func _go() -> void:
	var p := field.text; field.text = ""
	btn.disabled = true; msg.text = "Checking…"
	gate.unlock_async(p, func(r: Dictionary):
		btn.disabled = false
		if r.ok: msg.text = "Unlocked."; hide(); unlocked.emit()
		elif r.reason == "throttled": msg.text = "Too many tries. Wait %ds." % ceili(r.retryMs / 1000.0)
		elif r.reason == "server-mode": msg.text = "Owner is verified by the server."
		else: msg.text = "Wrong passphrase. %d free tries left." % r.get("triesLeft", 0))
