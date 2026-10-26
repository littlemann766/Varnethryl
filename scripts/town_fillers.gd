class_name TownFillers
extends RefCounted
## Test 14 (boss: "the town should feel CROWDED"): rows of filler townhouses/shops along the in-town streets.
## Data-driven: res://assets/town/fillers.json is the placement list (stable ids, model, pos, yaw, door marker, path end),
## produced once by tools/gen_fillers.gd (solve()) and then never moved, so an interior can be hooked up later
## (InteriorManager would just need the id in interior_defs + an entry in main.buildings). Doors are closed for now.
## Perf (S26 Ultra): Beth's card2 LOD1/LOD2 only (no hi tier), shared mesh + material resources (load() cache),
## LOD1 to 70 m then LOD2 to 300 m, shadows from LOD1 only, Beth's -colonly collision per house.

const DATA := "res://assets/town/fillers.json"
## [card2 key, label] - Beth's small kit pieces (the big landmark models stay unique)
const KIT := [["house1", "Townhouse"], ["house2", "Townhouse"], ["house3", "Townhouse"], ["house4", "Townhouse"],
	["bakery", "Shop"], ["apothecary", "Shop"], ["smithy", "Workshop"]]
const GAP := 3.1          # front door -> street edge (same as the landmark buildings' SPUR_GAP)
const ROW_GAP := 0.7      # between neighbours in a row (dense terrace)
const LOD_BANDS := [[0.0, 70.0], [70.0, 300.0]]

static func _bbox(key: String) -> AABB:
	var j = JSON.parse_string(FileAccess.get_file_as_string("res://assets/card2/index.json"))
	for b in j.buildings:
		if b.id == key:
			var mn: Array = b.high.bbox_min; var mx: Array = b.high.bbox_max
			return AABB(Vector3(mn[0], mn[1], mn[2]), Vector3(mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]))
	return AABB()

static func _seg_hits_rect(a: Vector2, b: Vector2, r: Rect2) -> bool:
	if r.has_point(a) or r.has_point(b): return true
	var c := [r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]
	for i in 4:
		if Geometry2D.segment_intersects_segment(a, b, c[i], c[(i + 1) % 4]) != null: return true
	return false

## offline solver: walk both sides of every in-town street, pack kit houses facing the street wherever the lot is free
static func solve(m: Node) -> Array:
	var M = m.get_script()
	var boxes := {}
	for k in KIT: boxes[k[0]] = _bbox(k[0])
	var out := []; var rects := []
	var keep: Array = []   # landmark footprints, their door paths, plaza, pond, fountain, old roads
	for b in m.buildings: keep.append((b.rect as Rect2).grow(3.0))
	var gates := [Vector2(0, 185), Vector2(0, -185), Vector2(185, 0), Vector2(-185, 0)]
	var n := 0
	for si in M.STREETS.size():
		var s: Array = M.STREETS[si]
		var a := Vector2(s[0], s[1]); var b := Vector2(s[2], s[3]); var hw: float = s[4]
		var horiz := absf(a.y - b.y) < 0.01
		var along := (b - a).normalized(); var L := a.distance_to(b)
		for side in [-1, 1]:
			var nrm := Vector2(0, side) if horiz else Vector2(side, 0)   # from the street towards the house
			# house front (+Z local) must face the street: fwd = -nrm
			var rot := atan2(-nrm.x, -nrm.y)
			var t := 4.0; var k := 0
			while t < L - 4.0:
				var key: String = KIT[(si * 7 + (side + 1) * 3 + k) % KIT.size()][0]
				var bx: AABB = boxes[key]
				var halfw := maxf(-bx.position.x, bx.end.x)
				var cen := a + along * (t + halfw) + nrm * (hw + GAP + bx.end.z)
				var pos := Vector3(cen.x, 0, cen.y)
				var r: Rect2 = M._world_rect(bx.grow(0.3), pos, rot)
				var ok := absf(r.position.x) >= -172 and r.position.x >= -172 and r.end.x <= 172 and r.position.y >= -172 and r.end.y <= 172
				for g in gates: if ok and r.get_center().distance_to(g) < 34.0: ok = false
				if ok and Vector2(cen).distance_to(Vector2(m.POND.x, m.POND.z)) < 30.0: ok = false
				if ok:
					for o in keep + rects: if r.intersects(o): ok = false; break
				if ok:
					for sp in m.spurs: if _seg_hits_rect(sp[0], sp[1], r.grow(1.2)): ok = false; break
				if ok:   # footprint (+1 m) clear of every street / the plaza
					var g2 := r.grow(1.0); var x := g2.position.x
					while ok and x <= g2.end.x:
						var z := g2.position.y
						while z <= g2.end.y:
							if M.street_edge_dist(Vector2(x, z)) < 0.0: ok = false; break
							z += 0.7
						x += 0.7
				var door: Vector3 = M.card2_door(key) if M.card2_door(key) != null else Vector3(0, 0, bx.end.z)
				var dw := Vector2(cen.x, cen.y) + Vector2(door.x, door.z).rotated(-rot)
				var de := dw
				if ok:
					for q in 80:
						de = dw - nrm * (0.25 * q)
						if M.street_edge_dist(de) < -0.4: break
					for o in keep: if _seg_hits_rect(dw, de, o): ok = false; break
					for o in rects: if ok and _seg_hits_rect(dw, de, o.grow(0.3)): ok = false
				if ok:
					var id := "fill_s%02d_%s_%02d" % [si, "l" if side < 0 else "r", k]
					out.append({"id": id, "model": key, "label": KIT.filter(func(e): return e[0] == key)[0][1],
						"pos": [snappedf(pos.x, 0.01), snappedf(pos.z, 0.01)], "yaw": snappedf(rot, 0.0001),
						"door": [snappedf(dw.x, 0.01), snappedf(dw.y, 0.01)], "path_end": [snappedf(de.x, 0.01), snappedf(de.y, 0.01)],
						"rect": [r.position.x, r.position.y, r.size.x, r.size.y], "interior": ""})
					rects.append(r); n += 1; k += 1
					t += 2.0 * halfw + ROW_GAP
				else:
					t += 2.0
	return out

## build from the data list; returns [{id, node, door (world Vector3), path [a, b], rect}]
static func build(m: Node3D) -> Array:
	if not FileAccess.file_exists(DATA): return []
	var list: Array = JSON.parse_string(FileAccess.get_file_as_string(DATA))
	var M = m.get_script()
	var res := []
	var pmat := StandardMaterial3D.new(); pmat.albedo_color = Color(0.47, 0.37, 0.25); pmat.roughness = 1.0
	var root := Node3D.new(); root.name = "TownFillers"; m.add_child(root)
	for f in list:
		var pos := Vector3(f.pos[0], 0, f.pos[1]); var rot: float = f.yaw
		var n := Node3D.new(); n.name = f.id; n.position = pos; n.rotation.y = rot; root.add_child(n)
		n.set_meta("filler_id", f.id); n.set_meta("interior", f.interior)
		for k in 2:
			var v: Node3D = load(M._card2_path(f.model, ["_lod1", "_lod2"][k])).instantiate(); n.add_child(v)
			for mi: MeshInstance3D in v.find_children("*", "MeshInstance3D", true, false):
				mi.visibility_range_begin = LOD_BANDS[k][0]; mi.visibility_range_end = 0.0 if k == LOD_BANDS.size() - 1 else LOD_BANDS[k][1]   # test 17: last LOD open-ended so roofs show from any height
				mi.visibility_range_begin_margin = 4.0; mi.visibility_range_end_margin = 4.0
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if k == 0 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		m._add_col(M._card2_path(f.model, "_col"), pos, rot)
		# door marker (closed door for now; an interior hooks up here later)
		var dm := Marker3D.new(); dm.name = "Door"; n.add_child(dm)
		var dl: Vector3 = M.card2_door(f.model) if M.card2_door(f.model) != null else Vector3.ZERO
		dm.position = dl
		# footpath strip door -> street
		var a := Vector2(f.door[0], f.door[1]); var b := Vector2(f.path_end[0], f.path_end[1])
		var strip := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(1.5, maxf(a.distance_to(b), 0.5)); pm.material = pmat; strip.mesh = pm
		strip.position = Vector3((a.x + b.x) * 0.5, 0.025, (a.y + b.y) * 0.5); strip.rotation.y = atan2(b.x - a.x, b.y - a.y)
		strip.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(strip)
		var r := Rect2(f.rect[0], f.rect[1], f.rect[2], f.rect[3])
		m.blockers.append([r.get_center(), maxf(r.size.x, r.size.y) * 0.55 + 1.0])
		res.append({"id": f.id, "model": f.model, "node": n, "door": Vector3(a.x, 0, a.y), "path": [a, b], "rect": r})
	return res
