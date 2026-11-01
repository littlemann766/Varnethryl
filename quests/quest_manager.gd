extends Node
## quests-test (story beats 1-3, varn-core design/story_crew_pilgrim.md @1ef8e2a): data-driven quests.
## Autoload "Quests". Data: res://quests/quests.json. Step types: talk, collect, interact, travel (ashore at a landing), kill.
## Progress lives in VSave.state["story"] and is written with VSave.write_state(); old saves without "story" just start
## fresh (the existing "questStep" key and TitanQuest are untouched).
## story = {quests: {qid: {step: int, counts: {}, done: bool}}, crew: [ids], flags: {}, items: {}}
signal changed
signal step_done(qid: String, step: Dictionary)
signal quest_done(qid: String, end_text: String)
signal dialogue(lines: Array)
signal recruited(id: String)

const DATA := "res://quests/quests.json"
var data: Dictionary = {}
var main: Node            # the game scene (main.gd) once it exists
var world: Node           # QuestWorld (spawns NPCs / points / pickups / enemies on the islands)
var ui: Node              # QuestUi (tracker, journal, dialogue)
var log_steps := false

func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(DATA))
	data = d if d is Dictionary else {"quests": {}}
	if not (d is Dictionary): push_error("quests.json failed to parse")

func _vs() -> Node: return get_tree().root.get_node("VSave")
func story() -> Dictionary:
	var st: Dictionary = _vs().state
	if not (st.get("story") is Dictionary): st["story"] = {}
	var s: Dictionary = st["story"]
	for k in ["quests", "flags", "items"]: if not (s.get(k) is Dictionary): s[k] = {}
	if not (s.get("crew") is Array): s["crew"] = []
	return s
func save() -> void: _vs().write_state()

## attach to the game scene when it shows up (main.gd has `sea` once _ready ran)
func _process(_dt: float) -> void:
	if main != null and is_instance_valid(main): return
	var cs := get_tree().current_scene
	if cs == null or cs.get("sea") == null: return
	main = cs
	world = load("res://quests/quest_world.gd").new(); world.name = "QuestWorld"; main.sea.add_child(world); world.setup(self, main)
	ui = load("res://quests/quest_ui.gd").new(); ui.name = "QuestUi"; main.add_child(ui); ui.setup(self)
	start_auto()

func start_auto() -> void:
	for qid in data.quests:
		if data.quests[qid].get("auto_start", false) and not story().quests.has(qid): start(qid)

# ---------------------------------------------------------------- queries
func quest_def(qid: String) -> Dictionary: return data.quests.get(qid, {})
func qstate(qid: String) -> Dictionary: return story().quests.get(qid, {})
func active_ids() -> Array:
	var out := []
	for qid in story().quests: if not story().quests[qid].get("done", false): out.append(qid)
	return out
func current_step(qid: String) -> Dictionary:
	var q := qstate(qid); var steps: Array = quest_def(qid).get("steps", [])
	if q.is_empty() or q.get("done", false) or int(q.step) >= steps.size(): return {}
	return steps[int(q.step)]
func step_index(qid: String, step_id: String) -> int:
	var steps: Array = quest_def(qid).get("steps", [])
	for i in steps.size(): if steps[i].id == step_id: return i
	return -1
## is `target` the current step of an active quest (of type t, "" = any)
func is_target(t: String, target: String) -> bool:
	for qid in active_ids():
		var s := current_step(qid)
		if not s.is_empty() and s.target == target and (t == "" or s.type == t): return true
	return false
## has the step with this target (type t) not been finished yet (it is current or still ahead)
func pending(t: String, target: String) -> bool:
	for qid in quest_def_ids():
		var q := qstate(qid)
		var steps: Array = quest_def(qid).get("steps", [])
		for i in steps.size():
			if steps[i].type == t and steps[i].target == target:
				if q.is_empty() or (not q.get("done", false) and int(q.step) <= i): return true
	return false
func quest_def_ids() -> Array: return data.quests.keys()
func flag(k: String) -> bool: return bool(story().flags.get(k, false))
func has_crew(id: String) -> bool: return story().crew.has(id)
func tracker_text() -> String:
	var lines := []
	for qid in active_ids():
		var s := current_step(qid)
		if s.is_empty(): continue
		var t: String = s.text
		if s.type in ["collect", "kill"] and int(s.get("count", 1)) > 1: t += " (%d/%d)" % [int(qstate(qid).counts.get(s.id, 0)), int(s.count)]
		lines.append("%s\n> %s" % [quest_def(qid).title, t])
	return "\n".join(lines)

# ---------------------------------------------------------------- progress
func start(qid: String) -> void:
	if quest_def(qid).is_empty(): return
	story().quests[qid] = {"step": 0, "counts": {}, "done": false}
	save(); _on_step_active(qid); changed.emit()

## the one entry point for gameplay: notify("travel", "gullhaven"), notify("kill", "knights_men")...
func notify(t: String, target: String, n := 1) -> bool:
	var hit := false
	for qid in active_ids():
		var s := current_step(qid)
		if s.is_empty() or s.type != t or s.target != target: continue
		hit = true
		var q := qstate(qid)
		var need := int(s.get("count", 1))
		var c := int(q.counts.get(s.id, 0)) + n
		q.counts[s.id] = c
		if c >= need: _complete_step(qid, s)
		else: save(); changed.emit()
	return hit

func _complete_step(qid: String, s: Dictionary) -> void:
	var q := qstate(qid); var st := story()
	for it in s.get("give", {}): st.items[it] = int(st.items.get(it, 0)) + int(s.give[it])
	for f in s.get("flags", {}): st.flags[f] = s.flags[f]
	if s.has("recruit"): recruit(str(s.recruit), false)
	if s.get("flags", {}).get("day", false) and main and main.has_method("_set_time"): main._set_time(11.0)
	if s.has("dialogue"): dialogue.emit(s.dialogue)
	if log_steps: print("QUEST step done %s/%s" % [qid, s.id])
	q.step = int(q.step) + 1
	step_done.emit(qid, s)
	if int(q.step) >= quest_def(qid).steps.size():
		q.done = true; save(); changed.emit()
		if log_steps: print("QUEST done %s" % qid)
		quest_done.emit(qid, str(quest_def(qid).get("end_text", "")))
		return
	save(); _on_step_active(qid); changed.emit()

func _on_step_active(qid: String) -> void:
	var s := current_step(qid)
	if s.is_empty(): return
	if s.type == "travel" and s.get("night", false) and main and main.has_method("_set_time"): main._set_time(22.0)   # simple night switch
	# already standing ashore at the target (e.g. a loaded save): count it
	if s.type == "travel" and main and main.sea and main.sea.ashore == s.target: notify.call_deferred("travel", s.target)

# ---------------------------------------------------------------- crew roster
func crew_def(id: String) -> Dictionary: return data.get("crew", {}).get(id, {})
func recruit(id: String, write := true) -> void:
	var st := story()
	if not st.crew.has(id): st.crew.append(id)
	var ab := str(crew_def(id).get("ability", ""))
	if ab != "": st.flags[ab] = true
	party_hook(id)
	if write: save()
	recruited.emit(id)
## STUB for later beats: recruits will join party.gd as fight companions. Today Pip already follows the hero.
func party_hook(_id: String) -> void:
	pass

## debug / tests: wipe story progress
func reset() -> void:
	_vs().state["story"] = {}; story(); save(); start_auto(); changed.emit()
