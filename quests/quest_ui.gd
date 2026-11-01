extends CanvasLayer
## quests-test: on-screen quest tracker (left side), Journal button + panel, and the NPC dialogue box (bottom centre).
var qm: Node
var tracker: Label
var journal_b: Button
var journal: PanelContainer
var box: PanelContainer
var who: Label
var line: Label
var next_b: Button
var queue: Array = []

func setup(q: Node) -> void:
	qm = q; layer = 41
	tracker = Label.new(); tracker.name = "QuestTracker"; tracker.position = Vector2(16, 244); tracker.add_theme_font_size_override("font_size", 20)
	tracker.add_theme_color_override("font_color", Color(1, 0.95, 0.75)); tracker.add_theme_color_override("font_shadow_color", Color.BLACK); tracker.add_theme_constant_override("shadow_offset_y", 2)
	tracker.custom_minimum_size = Vector2(380, 0); tracker.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; add_child(tracker)
	journal_b = Button.new(); journal_b.name = "JournalButton"; journal_b.text = "Journal"; journal_b.position = Vector2(16, 190); journal_b.custom_minimum_size = Vector2(120, 44)
	journal_b.add_theme_font_size_override("font_size", 20); journal_b.pressed.connect(toggle_journal); add_child(journal_b)
	box = PanelContainer.new(); box.name = "Dialogue"; box.visible = false
	box.anchor_left = 0.5; box.anchor_right = 0.5; box.anchor_top = 1.0; box.anchor_bottom = 1.0
	box.offset_left = -300; box.offset_right = 300; box.offset_top = -330; box.offset_bottom = -200; add_child(box)
	var v := VBoxContainer.new(); box.add_child(v)
	who = Label.new(); who.add_theme_font_size_override("font_size", 22); who.add_theme_color_override("font_color", Color(1, 0.85, 0.4)); v.add_child(who)
	line = Label.new(); line.add_theme_font_size_override("font_size", 22); line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; line.custom_minimum_size = Vector2(580, 0); v.add_child(line)
	next_b = Button.new(); next_b.text = "Next"; next_b.custom_minimum_size = Vector2(120, 40); next_b.size_flags_horizontal = Control.SIZE_SHRINK_END; next_b.pressed.connect(advance); v.add_child(next_b)
	qm.changed.connect(_refresh); qm.dialogue.connect(say)
	qm.quest_done.connect(func(_q, t): if t != "": say([["", t]]))
	_refresh()

func _process(_dt: float) -> void:
	var vui = get_tree().root.get_node_or_null("VUI")
	var on: bool = vui != null and vui.hud != null and vui.hud.visible and not (vui.title and vui.title.visible)
	tracker.visible = on and tracker.text != ""; journal_b.visible = on
	if not on and journal: journal.visible = false

func _refresh() -> void:
	tracker.text = qm.tracker_text()
	if journal and journal.visible: _fill_journal()

func say(lines: Array) -> void:
	queue.append_array(lines)
	if not box.visible: advance()
func advance() -> void:
	if queue.is_empty(): box.visible = false; return
	var l: Array = queue.pop_front()
	who.text = str(l[0]); who.visible = str(l[0]) != ""; line.text = str(l[1]); box.visible = true
	next_b.text = "Next" if not queue.is_empty() else "Close"

func toggle_journal() -> void:
	if journal and journal.visible: journal.visible = false; return
	if journal == null:
		journal = PanelContainer.new(); journal.name = "Journal"; journal.position = Vector2(160, 190); add_child(journal)
	journal.visible = true; _fill_journal()
func _fill_journal() -> void:
	for c in journal.get_children(): c.queue_free()
	var v := VBoxContainer.new(); journal.add_child(v)
	var add := func(t: String, sz: int, col: Color):
		var l := Label.new(); l.text = t; l.add_theme_font_size_override("font_size", sz); l.add_theme_color_override("font_color", col); v.add_child(l)
	add.call("Journal", 28, Color(1, 0.85, 0.4))
	var st: Dictionary = qm.story()
	for qid in st.quests:
		var q: Dictionary = st.quests[qid]; var d: Dictionary = qm.quest_def(qid)
		add.call(str(d.get("title", qid)) + ("  (done)" if q.get("done", false) else ""), 22, Color(1, 0.95, 0.75))
		var steps: Array = d.get("steps", [])
		for i in mini(int(q.step) + 1, steps.size()):
			add.call(("  [x] " if i < int(q.step) or q.get("done", false) else "  [ ] ") + str(steps[i].text), 18, Color.WHITE)
		if q.get("done", false) and d.has("end_text"): add.call("  " + str(d.end_text), 18, Color(0.8, 0.8, 1))
	var crew := []
	for id in st.crew: crew.append("%s (%s)" % [qm.crew_def(id).get("name", id), qm.crew_def(id).get("role", "")])
	add.call("Crew: " + (", ".join(crew) if crew else "none yet"), 20, Color(0.7, 1, 0.8))
	var ab := []
	for f in ["night_sailing", "cave_diving"]: if qm.flag(f): ab.append(f.replace("_", " "))
	add.call("Ship: " + (", ".join(ab) if ab else "-"), 20, Color(0.7, 1, 0.8))
	var it := []
	for k in st.items: if int(st.items[k]) > 0: it.append(k.replace("_", " "))
	add.call("Items: " + (", ".join(it) if it else "-"), 20, Color.WHITE)
	var b := Button.new(); b.text = "Close"; b.pressed.connect(toggle_journal); v.add_child(b)
