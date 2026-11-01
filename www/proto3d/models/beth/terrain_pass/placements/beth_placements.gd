## Terrain pass fix 7b (Beth): load Beth's unwired placement sets into Lucky's mainland (main.gd), with the same
## filters _dressing() uses (gate paths, roads/streets, buildings) plus volcano-titan / blocker / sea / pond checks.
## Wiring: README_LUCKY_TERRAIN_PASS.md "Fix 7b". Call after _dressing():  BethPlacements.apply(self)
class_name BethPlacements

const SETS := ["PLACEMENT_frost_town.json", "PLACEMENT_volcano.json", "PLACEMENT_hobcamps.json"]
const VOLC_KEEP := Vector2(150.0, 215.0)   # volcano dressing only in the ring just outside the Titan (r 148): scree/ash band

static func accept(m, file: String, p: Vector2, set_name: String) -> String:
	if m.has_method("_in_gate_path") and m._in_gate_path(p, 2.0): return "gate"
	if m.has_method("_on_way") and m._on_way(p, 1.2): return "road"
	if m.has_method("_in_building") and m._in_building(p, 1.5): return "building"
	var dv := p.distance_to(Vector2(405, -402))
	if set_name.contains("volcano"):
		if dv < VOLC_KEEP.x or dv > VOLC_KEEP.y: return "volcano_footprint"
	elif dv < 152.0: return "volcano_footprint"
	if "blockers" in m:
		for b in m.blockers:
			if p.distance_to(b[0]) < float(b[1]) * 0.9 and float(b[1]) < 100.0: return "blocker"
	if m.has_method("height") and m.height(p.x, p.y) < 0.6: return "water"
	if absf(p.x) < m.CITY_HALF + 4 and absf(p.y) < m.CITY_HALF + 4 and file.begins_with("hobcamp/"): return "inside_walls"
	return ""

static func apply(m) -> Dictionary:
	var groups := {}; var stats := {"kept": 0}
	for s in SETS:
		var j = JSON.parse_string(FileAccess.get_file_as_string("res://assets/data/" + s))
		for it in j["items"]:
			var file: String = it["file"]; var p: Array = (it["position"] as Array).duplicate(); var r: Array = it["rotation"]; var sc: Array = it["scale"]
			if s.contains("volcano"):   # these predate the Titan (r 148) and sit under it: push each one out radially into a 152-212 m scree/ash band
				var o := Vector2(p[0], p[2]) - Vector2(405, -402); var rr := 152.0 + clampf(o.length() / 150.0, 0.0, 1.0) * 60.0
				o = o.normalized() * rr; p[0] = 405.0 + o.x; p[2] = -402.0 + o.y; p[1] = null
			var why := accept(m, file, Vector2(p[0], p[2]), s)
			if why != "": stats[why] = stats.get(why, 0) + 1; continue
			var y: float = m.height(p[0], p[2]) if p[1] == null else float(p[1])
			var up := file.contains("totem") or file.contains("banner") or file.contains("palisade") or file.contains("tent") or file.contains("tree") or file.contains("lamp")
			var b := (Basis(Vector3.UP, r[1]) if up else Basis.from_euler(Vector3(r[0], r[1], r[2]))).scaled(Vector3(sc[0], sc[1], sc[2]))
			y -= 0.12 if not file.contains("drift") else 0.25   # seat into slope (terrain pass fix 4 rule: no floating)
			if not groups.has(file): groups[file] = []
			groups[file].append(Transform3D(b, Vector3(p[0], y, p[2]))); stats.kept += 1
	for file in groups:
		var small: bool = file.contains("drift") or file.contains("ember") or file.contains("rack") or file.contains("barrel") or file.contains("crate")
		m._multimesh("res://assets/" + file, groups[file], not small, 180.0 if small else 420.0)
	return stats
