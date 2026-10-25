class_name InteriorBuilder
## Builds an interior Node3D from a def in InteriorDefs (ported/reworked from proto3d interiors.js + buildings.js).
## Def coords: u,v in [-0.5,0.5] of the interior footprint (W x D), +v = front wall (door side, matches exterior +Z).
const K := preload("res://interiors/interior_kit.gd")
const WALL_T := 0.35
const SLAB_T := 0.25
const DOOR_W := 2.2
const DOOR_H := 3.0
const STAIR_SLOPE := 1.3        # run = rise * 1.3  (~37.6 deg, under floor_max_angle 45)

## size = exterior AABB size. Returns {node, W, D, floors:[{y,h,node,outline}], stairs, ladders, rooms, spawn, door}
static func build(id: String, def: Dictionary, size: Vector3) -> Dictionary:
	var sc: Array = def.get("scale", [0.8, 0.8])
	var W: float = snappedf(size.x * sc[0], 0.1); var D: float = snappedf(size.z * sc[1], 0.1)
	var root := Node3D.new(); root.name = "Interior_" + id
	var info := {"id": id, "node": root, "W": W, "D": D, "floors": [], "stairs": [], "ladders": [], "rooms": [], "name": def.get("name", id)}
	var fl: Array = def.floors
	var y := 0.0
	for i in fl.size():
		var f: Dictionary = fl[i]
		var fn := Node3D.new(); fn.name = "F%d" % i; root.add_child(fn)
		info.floors.append({"y": y, "h": float(f.h), "node": fn, "outline": null, "lines": []})
		y += float(f.h)
	var P := func(u: float, v: float, fy: float) -> Vector3: return Vector3(u * W, fy, v * D)
	# holes from stairs / ladders, per floor above
	var holes := {}
	for s in def.get("stairs", []):
		var f0: Dictionary = info.floors[s[0]]; var a := deg_to_rad(float(s[3])); var w: float = s[4]
		var d := Vector3(-sin(a), 0, -cos(a)); var L: float = f0.h * STAIR_SLOPE
		var base: Vector3 = P.call(s[1], s[2], f0.y)
		info.stairs.append({"floor": s[0], "base": base, "dir": d, "run": L, "rise": f0.h, "w": w})
		holes.get_or_add(s[0] + 1, []).append(_rect_along(base, d, 0.0, L + 0.05, w + 0.3))
	for l in def.get("ladders", []):
		var f0: Dictionary = info.floors[l[0]]; var a := deg_to_rad(float(l[3]))
		var d := Vector3(-sin(a), 0, -cos(a)); var p: Vector3 = P.call(l[1], l[2], f0.y)
		info.ladders.append({"floor": l[0], "pos": p, "dir": d, "top": f0.y + f0.h})
		holes.get_or_add(l[0] + 1, []).append(_rect_along(p, d, -1.2, 0.0, 1.1))
	# floors: slabs, outer walls, partitions
	for i in fl.size():
		var f: Dictionary = fl[i]; var F: Dictionary = info.floors[i]; var fn: Node3D = F.node
		var regions: Array = []
		for r in f.get("slab", [[-0.5, -0.5, 0.5, 0.5]]): regions.append(Rect2(Vector2(r[0] * W, r[1] * D), Vector2((r[2] - r[0]) * W, (r[3] - r[1]) * D)))
		for reg in regions:
			for c in _subtract(reg, holes.get(i, [])):
				K.box(fn, Vector3(c.get_center().x, F.y - SLAB_T / 2, c.get_center().y), Vector3(c.size.x, SLAB_T, c.size.y), f.get("mat", "flag"))
				F.lines.append(c)
		var wm: String = f.get("wall", "stone"); var h: float = F.h
		var hw := W / 2; var hd := D / 2
		var front_gaps: Array = [[0.5, DOOR_W]] if i == 0 else []
		_wall(fn, Vector2(-hw, hd), Vector2(hw, hd), F.y, h, front_gaps, wm)
		_wall(fn, Vector2(-hw, -hd), Vector2(hw, -hd), F.y, h, [], wm)
		_wall(fn, Vector2(-hw, -hd), Vector2(-hw, hd), F.y, h, [], wm)
		_wall(fn, Vector2(hw, -hd), Vector2(hw, hd), F.y, h, [], wm)
		# windows: glowing panes on outer walls (no openings: cheap, reads as card's leaded windows)
		var ws: float = f.get("win", 4.0)
		if ws > 0:
			for side in 4:
				var len := W if side < 2 else D
				var n := int(len / ws)
				for k in n:
					var t := (k + 0.5) / n
					if i == 0 and side == 0 and absf(t - 0.5) * len < DOOR_W: continue
					var wp: Vector3; var rot := 0.0
					match side:
						0: wp = Vector3(-hw + t * W, 0, hd - WALL_T / 2 - 0.03)
						1: wp = Vector3(-hw + t * W, 0, -hd + WALL_T / 2 + 0.03)
						2: wp = Vector3(-hw + WALL_T / 2 + 0.03, 0, -hd + t * D); rot = PI / 2
						3: wp = Vector3(hw - WALL_T / 2 - 0.03, 0, -hd + t * D); rot = PI / 2
					var wh := minf(h * 0.42, 3.2)
					wp.y = F.y + h * 0.5 + 0.2
					K.box(fn, wp, Vector3(0.9, wh, 0.04), f.get("glass", "glass"), false, rot)
					K.box(fn, wp + Vector3(0, wh / 2 + 0.06, 0), Vector3(1.1, 0.12, 0.08), "darkoak", false, rot)
		for wdef in def.get("walls", []):
			if wdef[0] != i: continue
			_wall(fn, Vector2(wdef[1] * W, wdef[2] * D), Vector2(wdef[3] * W, wdef[4] * D), F.y, h, wdef[5] if wdef.size() > 5 else [], wdef[6] if wdef.size() > 6 else wm)
			F.lines.append([Vector2(wdef[1] * W, wdef[2] * D), Vector2(wdef[3] * W, wdef[4] * D)])
	for s in info.stairs: _stair(info.floors[s.floor].node, s, fl[s.floor].get("stairmat", "oak"))
	for l in info.ladders:
		var fnode: Node3D = info.floors[l.floor].node
		var rot := rad_to_deg(atan2(-l.dir.x, -l.dir.z)) + 180.0
		var yy: float = l.pos.y
		while yy < l.top - 0.1:
			K.prop(fnode, "ladder", Vector3(l.pos.x, minf(yy, l.top - 3.0), l.pos.z) - l.dir * 0.05, rot, false); yy += 3.0
	for b in def.get("rails", []):   # balcony railings: [floor,u,v,rot,count]
		var F: Dictionary = info.floors[b[0]]; var a := deg_to_rad(float(b[3]))
		for k in int(b[4] if b.size() > 4 else 1):
			K.prop(F.node, "balcony_railing", P.call(b[1], b[2], F.y) + Vector3(cos(a), 0, -sin(a)) * 2.1 * k, b[3], true)
	for p in def.get("props", []): _prop(info, p, P)
	for l in def.get("lights", []): _light(info, l, P)
	for r in def.get("rooms", []):
		info.rooms.append({"name": r[0], "floor": r[1], "pos": P.call(r[2], r[3], info.floors[r[1]].y)})
	# void backdrop + porch
	var vb := K.box(root, Vector3(0, y / 2, 0), Vector3(W + 70, y + 70, D + 70), "void", false)
	vb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	K.box(root, Vector3(0, -SLAB_T / 2, D / 2 + 1.5), Vector3(DOOR_W + 1.6, SLAB_T, 3.0), "flag")
	for sx in [-1, 1]: K.box(root, Vector3(sx * (DOOR_W / 2 + 0.95), 1.5, D / 2 + 1.5), Vector3(0.3, 3.0, 3.0), "stone")
	K.box(root, Vector3(0, 1.5, D / 2 + 3.1), Vector3(DOOR_W + 2.2, 3.0, 0.3), "void", true)
	info.door = Vector3(0, 0, D / 2); info.spawn = Vector3(0, 0.05, D / 2 - 1.6); info.exit_z = D / 2 + 1.0
	for i in info.floors.size(): info.floors[i].outline = _outline(root, info.floors[i], W, D)
	return info

static func _rect_along(base: Vector3, d: Vector3, s0: float, s1: float, w: float) -> Rect2:
	var a := Vector2(base.x, base.z) + Vector2(d.x, d.z) * s0; var b := Vector2(base.x, base.z) + Vector2(d.x, d.z) * s1
	var side := Vector2(-d.z, d.x) * (w / 2)
	var r := Rect2(a + side, Vector2.ZERO); r = r.expand(a - side); r = r.expand(b + side); r = r.expand(b - side)
	return r

static func _subtract(reg: Rect2, holes: Array) -> Array:
	var xs := [reg.position.x, reg.end.x]; var zs := [reg.position.y, reg.end.y]
	for h in holes:
		var c: Rect2 = h.intersection(reg)
		if c.has_area(): xs += [c.position.x, c.end.x]; zs += [c.position.y, c.end.y]
	xs.sort(); zs.sort()
	var out := []
	for i in xs.size() - 1:
		for j in zs.size() - 1:
			var cell := Rect2(Vector2(xs[i], zs[j]), Vector2(xs[i + 1] - xs[i], zs[j + 1] - zs[j]))
			if cell.size.x < 0.01 or cell.size.y < 0.01: continue
			var inside := false
			for h in holes: if h.has_point(cell.get_center()): inside = true
			if not inside: out.append(cell)
	return out

## wall from a to b, gaps = [[t(0..1), width, (height)]]
static func _wall(fn: Node3D, a: Vector2, b: Vector2, y: float, h: float, gaps: Array, wm: String) -> void:
	var len := a.distance_to(b); var dirv := (b - a) / len; var rot := -atan2(dirv.y, dirv.x)
	var segs := []; var cur := 0.0
	var gs := gaps.duplicate(); gs.sort_custom(func(p, q): return p[0] < q[0])
	for g in gs:
		var c: float = g[0] * len; var gw: float = g[1]; var gh: float = g[2] if g.size() > 2 else DOOR_H
		segs.append([cur, c - gw / 2, 0.0, h]); segs.append([c - gw / 2, c + gw / 2, gh, h]); cur = c + gw / 2
	segs.append([cur, len, 0.0, h])
	for s in segs:
		var l: float = s[1] - s[0]
		if l < 0.02 or s[3] - s[2] < 0.02: continue
		var mid: Vector2 = a + dirv * ((s[0] + s[1]) / 2)
		K.box(fn, Vector3(mid.x, y + (s[2] + s[3]) / 2, mid.y), Vector3(l + (WALL_T if s[2] == 0.0 else 0.0), s[3] - s[2], WALL_T), wm, true, rot)

static func _stair(fn: Node3D, s: Dictionary, sm: String) -> void:
	var d: Vector3 = s.dir; var L: float = s.run; var H: float = s.rise; var w: float = s.w; var b: Vector3 = s.base
	var side := Vector3(-d.z, 0, d.x)
	var rot := atan2(-d.x, -d.z)
	var n := int(ceil(H / 0.2))
	for k in n:   # visual stepped block
		var s0 := L * k / n; var top := H * (k + 1) / n
		K.box(fn, b + d * (s0 + L / n / 2) + Vector3(0, top / 2, 0), Vector3(w, top, L / n), sm if k % 2 == 0 else "darkoak", false, rot)
	# solid wedge collision (no gap underneath -> no wedging; walking up is a choice, nothing pulls)
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var cv := ConvexPolygonShape3D.new()
	var pts := PackedVector3Array()
	for sx in [-1, 1]:
		var o: Vector3 = b + side * (w / 2 * sx)
		pts.append(o); pts.append(o + d * L); pts.append(o + d * L + Vector3(0, H, 0))
	cv.points = pts; cs.shape = cv; sb.add_child(cs); fn.add_child(sb)
	# handrails (iron posts + oak rail) both sides
	for sx in [-1, 1]:
		var o: Vector3 = b + side * ((w / 2 + 0.06) * sx)
		var hyp := sqrt(L * L + H * H)
		var rail := K.box(fn, o + d * (L / 2) + Vector3(0, H / 2 + 0.95, 0), Vector3(0.08, 0.08, hyp), "darkoak", false)
		rail.basis = Basis(Vector3.UP, rot) * Basis(Vector3.RIGHT, atan2(H, L))
		for k in 5:
			var t := k / 4.0
			K.box(fn, o + d * (L * t) + Vector3(0, H * t + 0.47, 0), Vector3(0.05, 0.95, 0.05), "iron", false, rot)

static func _prop(info: Dictionary, p: Array, P: Callable) -> void:
	var name: String = p[0]; var F: Dictionary = info.floors[p[1]]; var fn: Node3D = F.node
	var pos: Vector3 = P.call(p[2], p[3], F.y); var rot: float = p[4] if p.size() > 4 else 0.0
	var ex: Array = p[5] if p.size() > 5 else []
	match name:
		"_runner":   # carpet runner [len_v, width_m, mat]
			var bm := K.box(fn, pos + Vector3(0, 0.012, 0), Vector3(ex[1], 0.02, ex[0] * info.D), ex[2] if ex.size() > 2 else "blue", false, deg_to_rad(rot))
			K.box(fn, pos + Vector3(0, 0.01, 0), Vector3(ex[1] + 0.3, 0.015, ex[0] * info.D + 0.3), "gold", false, deg_to_rad(rot))
			bm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		"_area":     # floor inlay [w_m, d_m, mat]
			K.box(fn, pos + Vector3(0, 0.01, 0), Vector3(ex[0], 0.02, ex[1]), ex[2], false, deg_to_rad(rot))
		"_pillar":   # [height, radius, mat]
			var mi := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = ex[1]; cm.bottom_radius = ex[1]; cm.height = ex[0]
			mi.mesh = cm; mi.material_override = K.mat(ex[2] if ex.size() > 2 else "palestone"); mi.position = pos + Vector3(0, ex[0] / 2, 0); mi.layers = K.LAYER; fn.add_child(mi)
			var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var sh := CylinderShape3D.new(); sh.radius = ex[1]; sh.height = ex[0]; cs.shape = sh; sb.add_child(cs); mi.add_child(sb)
		"_round_table":  # [radius, chairs]
			var mi := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = ex[0]; cm.bottom_radius = ex[0]; cm.height = 0.1
			mi.mesh = cm; mi.material_override = K.mat("darkoak"); mi.position = pos + Vector3(0, 0.78, 0); mi.layers = K.LAYER; fn.add_child(mi)
			K.box(fn, pos + Vector3(0, 0.4, 0), Vector3(ex[0] * 0.5, 0.75, ex[0] * 0.5), "darkoak")
			var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var sh := CylinderShape3D.new(); sh.radius = ex[0]; sh.height = 0.85; cs.shape = sh; cs.position.y = 0.42; sb.add_child(cs); sb.position = pos; fn.add_child(sb)
			for k in int(ex[1]):
				var a: float = TAU * k / ex[1]
				K.prop(fn, "chair", pos + Vector3(sin(a), 0, cos(a)) * (ex[0] + 0.45), rad_to_deg(a) + 180.0, false)
		"_fountain":   # [radius]
			var r: float = ex[0]
			for k in 2:
				var mi := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = r * (1.0 - 0.06 * k); cm.bottom_radius = r * (1.0 - 0.06 * k)
				cm.height = 0.6 - 0.05 * k; mi.mesh = cm; mi.material_override = K.mat("palestone" if k == 0 else "water")
				mi.position = pos + Vector3(0, 0.3 + 0.03 * k, 0); mi.layers = K.LAYER; fn.add_child(mi)
			K.box(fn, pos + Vector3(0, 0.9, 0), Vector3(0.5, 1.8, 0.5), "palestone", false)
			K.box(fn, pos + Vector3(0, 1.9, 0), Vector3(1.2, 0.15, 1.2), "gold", false)
			var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var sh := CylinderShape3D.new(); sh.radius = r; sh.height = 1.0; cs.shape = sh; cs.position.y = 0.5; sb.add_child(cs); sb.position = pos; fn.add_child(sb)
		"_counter":   # [w, h, d, mat]
			K.box(fn, pos + Vector3(0, ex[1] / 2, 0), Vector3(ex[0], ex[1], ex[2]), ex[3] if ex.size() > 3 else "darkoak", true, deg_to_rad(rot))
			K.box(fn, pos + Vector3(0, ex[1] + 0.03, 0), Vector3(ex[0] + 0.1, 0.06, ex[2] + 0.1), "oak", false, deg_to_rad(rot))
		"_glasswall":  # tall stained-glass window [w, h, y0]
			K.box(fn, pos + Vector3(0, ex[2] + ex[1] / 2, 0), Vector3(ex[0], ex[1], 0.06), "glass", false, deg_to_rad(rot))
			K.box(fn, pos + Vector3(0, ex[2] + ex[1] / 2, 0), Vector3(0.08, ex[1], 0.1), "iron", false, deg_to_rad(rot))
		"_pots":   # hanging pots/rack over kitchen [w]
			K.box(fn, pos + Vector3(0, 2.6, 0), Vector3(ex[0], 0.06, 0.06), "iron", false, deg_to_rad(rot))
			for k in 5: K.box(fn, pos + Vector3((k - 2) * ex[0] / 5.0, 2.3, 0).rotated(Vector3.UP, deg_to_rad(rot)), Vector3(0.3, 0.25, 0.3), "gold", false)
		_:
			var y_off: float = ex[0] if ex.size() > 0 else 0.0
			K.prop(fn, name, pos + Vector3(0, y_off, 0), rot, not (ex.size() > 1 and ex[1] == false))

static func _light(info: Dictionary, l: Array, P: Callable) -> void:
	# [kind, floor, u, v, rot, energy, range, shadow]
	var kind: String = l[0]; var F: Dictionary = info.floors[l[1]]; var fn: Node3D = F.node
	var pos: Vector3 = P.call(l[2], l[3], F.y); var rot: float = l[4]
	var e: float = l[5]; var rng: float = l[6]; var sh: bool = l[7] if l.size() > 7 else false
	var lp := pos
	match kind:
		"chandelier":
			var cy: float = F.h - 2.4
			K.prop(fn, "iron_chandelier", pos + Vector3(0, cy, 0), rot, false)
			K.box(fn, pos + Vector3(0, cy + 2.0 + (F.h - cy - 2.0) / 2, 0), Vector3(0.04, maxf(F.h - cy - 2.0, 0.01), 0.04), "iron", false)
			lp = pos + Vector3(0, cy + 0.6, 0)
		"lantern":
			K.prop(fn, "wall_lantern", pos + Vector3(0, 2.1, 0), rot, false); lp = pos + Vector3(0, 2.3, 0) + Vector3(sin(deg_to_rad(rot)), 0, cos(deg_to_rad(rot))) * 0.4
		"fire": lp = pos + Vector3(0, 0.8, 0)
		_: lp = pos + Vector3(0, 2.5, 0)
	var o := OmniLight3D.new(); o.position = lp; o.light_color = Color(1.0, 0.68, 0.38) if kind != "fire" else Color(1.0, 0.5, 0.2)
	o.light_energy = e; o.omni_range = rng; o.omni_attenuation = 1.2; o.shadow_enabled = sh; o.light_cull_mask = K.LAYER | 1
	o.light_specular = 0.3
	fn.add_child(o)

static func _outline(root: Node3D, F: Dictionary, W: float, D: float) -> MeshInstance3D:
	var im := ImmediateMesh.new()
	im.surface_begin(Mesh.PRIMITIVE_LINES, K.mat("outline"))
	var seg := func(a: Vector2, b: Vector2, y: float) -> void:
		im.surface_add_vertex(Vector3(a.x, y, a.y)); im.surface_add_vertex(Vector3(b.x, y, b.y))
	for yy in [F.y + 0.02, F.y + F.h]:
		var c := [Vector2(-W / 2, -D / 2), Vector2(W / 2, -D / 2), Vector2(W / 2, D / 2), Vector2(-W / 2, D / 2)]
		for k in 4: seg.call(c[k], c[(k + 1) % 4], yy)
	for k in 4:
		var c2: Vector2 = [Vector2(-W / 2, -D / 2), Vector2(W / 2, -D / 2), Vector2(W / 2, D / 2), Vector2(-W / 2, D / 2)][k]
		im.surface_add_vertex(Vector3(c2.x, F.y, c2.y)); im.surface_add_vertex(Vector3(c2.x, F.y + F.h, c2.y))
	for ln in F.lines:
		if ln is Array: seg.call(ln[0], ln[1], F.y + 0.02)
	im.surface_end()
	var mi := MeshInstance3D.new(); mi.mesh = im; mi.layers = K.LAYER; mi.visible = false
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(mi)
	return mi
