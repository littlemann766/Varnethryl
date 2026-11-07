class_name SaveStatus
extends RefCounted
## Title and toast copy from the save that is already on disk. Does not write the save.

static func fail_line() -> String:
	return "Save failed. Nothing new was written."

static func _vs() -> Node:
	return (Engine.get_main_loop() as SceneTree).root.get_node("VSave")

static func title_line(owner_unlocked: bool) -> String:
	var disk: Dictionary = _vs().read_save()
	if disk.status == "none":
		return "No save yet. Play Solo starts in town."
	if disk.status != "ok":
		return "Save could not be read. It was not replaced. Play Solo starts in town."
	var s: Dictionary = disk.state
	var place: Dictionary = _vs().resume_place(s)
	if str(place.get("kind", "town")) == "town":
		return "Saved place can't be used. Play Solo starts in town."
	var who := str(_vs().resume_skin(s, owner_unlocked))
	if who == "": who = _from_active(s)
	var name := HeroRoster.display_name(who) if who != "" else "Your hero"
	return "Saved: %s, %s. You stay in town until Play Solo." % [name, _where(place)]

static func resume_done(kind: String, hero: String, detail: String, restored: bool) -> String:
	var name := HeroRoster.display_name(hero) if hero != "" else "You"
	if not restored:
		return "No saved place restored. You are in town."
	match kind:
		"land": return "Resumed %s on the mainland." % name
		"sea": return "Resumed %s aboard the %s." % [name, detail if detail != "" else "ship"]
		"interior", "interior_legacy": return "Resumed %s inside the %s." % [name, detail if detail != "" else "building"]
		_: return "No saved place restored. You are in town."

static func _where(place: Dictionary) -> String:
	match str(place.get("kind", "town")):
		"land": return "on the mainland"
		"sea": return "aboard the %s" % str(place.get("ship", "galleon"))
		"interior": return "inside the %s" % str(place.get("id", "building")).capitalize()
		"interior_legacy": return "inside a saved building"
		_: return "in town"

static func _from_active(s: Dictionary) -> String:
	if not (s.get("active") is int or s.get("active") is float): return ""
	return str(_vs().skin_for_index(int(s.active)))
