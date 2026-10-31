class_name InteriorBuilder
## Builds an interior Node3D from a def in InteriorDefs (ported/reworked from proto3d interiors.js + buildings.js).
## Def coords: u,v in [-0.5,0.5] of the interior footprint (W x D), +v = front wall (door side, matches exterior +Z).
const K := preload("res://interiors/interior_kit.gd")
const WALL_T := 0.35
const SLAB_T := 0.25
const DOOR_W := 2.2
const DOOR_H := 3.0
const STAIR_SLOPE := 1.45       # run = rise * 1.45 (~34.6 deg; capsules of every size take it, under floor_max_angle 45)

## size = exterior AABB size. Returns {node, W, D, floors:[{y,h,node,outline}], stairs, ladders, rooms, spawn, door}
static func build(id: String, def: Dictionary, size: Vector3) -> Dictionary:
	# metre-mode defs are laid out at card scale (0.82 of the card2 shell); legacy fractional defs keep their tuned r3 footprint
	var sc: Array = def.get("scale", ([0.82, 0.82] if InteriorDefs.DOORS.has(id) else [0.42, 0.42]) if def.get("m", false) else [0.62, 0.62])
	if not def.get("m", false): size = InteriorDefs.LEGACY_SIZE.get(id, size)
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
	var MM: bool = def.get("m", false)   # true: def coords are metres from the centre instead of fractions
	var kx: float = 1.0 if MM else W; var kz: float = 1.0 if MM else D
	info.kx = kx; info.kz = kz
	var P := func(u: float, v: float, fy: float) -> Vector3: return Vector3(u * kx, fy, v * kz)
	# holes from stairs / ladders, per floor above
	var holes := {}
	for s0 in def.get("stairs", []):
		var s: Array = s0
		if s0[0] is String:   # ["auto", floor, side(-1 left/+1 right), width]: along a side wall, foot 1.8 m inside the front wall
			var fa: Dictionary = info.floors[s0[1]]; var wa: float = s0[3]
			var x: float = s0[2] * (W / 2 - WALL_T - wa / 2 - 0.15); var zf: float = D / 2 - 1.8 - (fa.h * STAIR_SLOPE + 1.6) * float(s0[4] if s0.size() > 4 else 0)
			s = [s0[1], x / kx, zf / kz, 0, wa]
		var f0: Dictionary = info.floors[s[0]]; var a := deg_to_rad(float(s[3])); var w: float = s[4]
		var d := Vector3(-sin(a), 0, -cos(a)); var L: float = f0.h * STAIR_SLOPE
		var base: Vector3 = P.call(s[1], s[2], f0.y)
		info.stairs.append({"floor": s[0], "base": base, "dir": d, "run": L, "rise": f0.h, "w": w})
		holes.get_or_add(s[0] + 1, []).append(_rect_along(base, d, 0.0, L + 0.02, w + 0.04))
	for l in def.get("ladders", []):
		var f0: Dictionary = info.floors[l[0]]; var a := deg_to_rad(float(l[3]))
		var d := Vector3(-sin(a), 0, -cos(a)); var p: Vector3 = P.call(l[1], l[2], f0.y)
		info.ladders.append({"floor": l[0], "pos": p, "dir": d, "top": f0.y + f0.h})
		holes.get_or_add(l[0] + 1, []).append(_rect_along(p, d, -1.2, 0.0, 1.1))
	# floors: slabs, outer walls, partitions
	for i in fl.size():
		var f: Dictionary = fl[i]; var F: Dictionary = info.floors[i]; var fn: Node3D = F.node
		var regions: Array = []
		for r in f.get("slab", [[-W / 2 / kx, -D / 2 / kz, W / 2 / kx, D / 2 / kz]]): regions.append(Rect2(Vector2(r[0] * kx, r[1] * kz), Vector2((r[2] - r[0]) * kx, (r[3] - r[1]) * kz)))
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
			_wall(fn, Vector2(wdef[1] * kx, wdef[2] * kz), Vector2(wdef[3] * kx, wdef[4] * kz), F.y, h, wdef[5] if wdef.size() > 5 else [], wdef[6] if wdef.size() > 6 else wm)
			F.lines.append([Vector2(wdef[1] * kx, wdef[2] * kz), Vector2(wdef[3] * kx, wdef[4] * kz)])
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
	if def.has("fill"): _fill(info, def, P)
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
	# balustrade colliders along both sides (stairs are entered/left only at their ends, so tiny heroes never snag a side ledge)
	for sx in [-1, 1]:
		var sbb := StaticBody3D.new(); var cb := CollisionShape3D.new(); var bb := BoxShape3D.new(); bb.size = Vector3(0.3, H + 1.0, L)
		cb.shape = bb; sbb.add_child(cb); sbb.position = b + side * ((w / 2 + 0.15) * sx) + d * (L / 2) + Vector3(0, (H + 1.0) / 2, 0); sbb.rotation.y = rot
		fn.add_child(sbb)
	# handrails (iron posts + oak rail) both sides
	for sx in [-1, 1]:
		var o: Vector3 = b + side * ((w / 2 + 0.06) * sx)
		var hyp := sqrt(L * L + H * H)
		var rail := K.box(fn, o + d * (L / 2) + Vector3(0, H / 2 + 0.95, 0), Vector3(0.08, 0.08, hyp), "darkoak", false)
		rail.basis = Basis(Vector3.UP, rot) * Basis(Vector3.RIGHT, atan2(H, L))
		for k in 5:
			var t := k / 4.0
			K.box(fn, o + d * (L * t) + Vector3(0, H * t + 0.47, 0), Vector3(0.05, 0.95, 0.05), "iron", false, rot)

## footprint (xz rect) of a def prop, for the wall fill pass
static func _foot(info: Dictionary, p: Array, P: Callable) -> Rect2:
	var pos: Vector3 = P.call(p[2], p[3], 0.0); var c := Vector2(pos.x, pos.z); var ex: Array = p[5] if p.size() > 5 else []
	var sz := Vector2(0.6, 0.6)
	match p[0]:
		"_runner", "_area", "_glasswall", "_bread", "_tools", "_arena": return Rect2(c, Vector2.ZERO)
		"_gear": sz = Vector2(ex[0] * 2.0, 0.4)
		"_round_table": sz = Vector2.ONE * (ex[0] + 0.75) * 2.0
		"_fountain": sz = Vector2.ONE * ex[0] * 2.0
		"_pillar": sz = Vector2.ONE * ex[1] * 2.0
		"_counter", "_pots": sz = Vector2(ex[0], ex[1]) if ex.size() > 1 else Vector2(1.2, 0.6)
		_:
			var s: Array = K.index().get(p[0], {}).get("size_m", [0.6, 0.6, 0.6]); sz = Vector2(s[0], s[2])
			if p[0] in ["rug", "lion_banner", "chandelier"]: return Rect2(c, Vector2.ZERO)
	var r: float = p[4] if p.size() > 4 else 0.0
	if absf(fmod(absf(r), 180.0) - 90.0) < 1.0: sz = Vector2(sz.y, sz.x)
	return Rect2(c - sz / 2, sz)

## "fill": [[floor, [prop names...], gap_m]] lines the outer walls of that floor with the props (cycling), wherever
## the spot and 1.1 m in front of it are free of props, stairs/ladders (+landings), the door lane, room points and slab edges.
static func _fill(info: Dictionary, def: Dictionary, P: Callable) -> void:
	var W: float = info.W; var D: float = info.D
	for fd in def.fill:
		var fi: int = fd[0]; var names: Array = fd[1]; var gap: float = fd[2] if fd.size() > 2 else 0.15
		var F: Dictionary = info.floors[fi]
		var obst: Array = []
		for p in def.get("props", []):
			if p[1] == fi: obst.append(_foot(info, p, P))
		for st in info.stairs:
			if st.floor == fi: obst.append(_rect_along(st.base, st.dir, -1.6, st.run + 1.4, st.w + 0.8))
			if st.floor + 1 == fi: obst.append(_rect_along(st.base, st.dir, -0.2, st.run + 1.6, st.w + 0.8))
		for l in info.ladders:
			if l.floor == fi or l.floor + 1 == fi: obst.append(_rect_along(l.pos, l.dir, -1.8, 1.6, 1.8))
		if fi == 0: obst.append(Rect2(-1.4, D / 2 - 3.0, 2.8, 3.2))
		for r in info.rooms:
			if r.floor == fi: obst.append(Rect2(r.pos.x - 0.8, r.pos.z - 0.8, 1.6, 1.6))
		for wd in def.get("walls", []):
			if wd[0] != fi: continue
			var a := Vector2(wd[1] * info.kx, wd[2] * info.kz); var b := Vector2(wd[3] * info.kx, wd[4] * info.kz)
			var rr := Rect2(a, Vector2.ZERO).expand(b).grow(0.25)
			for g in (wd[5] if wd.size() > 5 else []):   # keep 1.2 m clear around partition doorways
				var c: Vector2 = a.lerp(b, g[0]); obst.append(Rect2(c - Vector2.ONE * 1.4, Vector2.ONE * 2.8))
			obst.append(rr)
		var regions: Array = []
		for r in (def.floors[fi].get("slab", [[-W / 2 / info.kx, -D / 2 / info.kz, W / 2 / info.kx, D / 2 / info.kz]])):
			regions.append(Rect2(Vector2(r[0] * info.kx, r[1] * info.kz), Vector2((r[2] - r[0]) * info.kx, (r[3] - r[1]) * info.kz)))
		var k := 0
		var _dbg := OS.has_environment("FILLDBG")
		var placed: Array = []
		for side in 4:   # 0 back(-z) 1 left(-x) 2 right(+x) 3 front(+z)
			var rot: float = [0.0, 90.0, -90.0, 180.0][side]
			var L: float = W if side in [0, 3] else D
			var t := 0.5
			while t < L - 0.5:
				var nm: String = names[k % names.size()]
				var s: Array = K.index().get(nm, {}).get("size_m", [1.0, 1.0, 0.5]); var w: float = s[0]; var d: float = s[2]
				if t + w > L - 0.3: break
				var along: float = -L / 2 + t + w / 2; var inset: float = WALL_T / 2 + d / 2 + 0.03
				var c: Vector2; var sz: Vector2; var front: Rect2
				match side:
					0: c = Vector2(along, -D / 2 + inset); sz = Vector2(w, d); front = Rect2(c.x - w / 2, c.y + d / 2, w, 1.1)
					3: c = Vector2(along, D / 2 - inset); sz = Vector2(w, d); front = Rect2(c.x - w / 2, c.y - d / 2 - 1.1, w, 1.1)
					1: c = Vector2(-W / 2 + inset, along); sz = Vector2(d, w); front = Rect2(c.x + d / 2, c.y - w / 2, 1.1, w)
					2: c = Vector2(W / 2 - inset, along); sz = Vector2(d, w); front = Rect2(c.x - d / 2 - 1.1, c.y - w / 2, 1.1, w)
				var r := Rect2(c - sz / 2, sz)
				var ok := false
				for rg in regions:
					if rg.grow(-0.05).encloses(r) and rg.grow(-0.05).encloses(front): ok = true
				if ok:
					for o in obst + placed:
						if o.intersects(r.grow(0.05)) or (o in obst and o.intersects(front)): ok = false; break
				if ok:
					K.prop(F.node, nm, Vector3(c.x, F.y, c.y), rot, true); placed.append(r); k += 1; t += w + gap
				else: t += 0.25
		if _dbg: print("FILL ", info.id, " f", fi, " placed ", k)

static func _prop(info: Dictionary, p: Array, P: Callable) -> void:
	var name: String = p[0]; var F: Dictionary = info.floors[p[1]]; var fn: Node3D = F.node
	var pos: Vector3 = P.call(p[2], p[3], F.y); var rot: float = p[4] if p.size() > 4 else 0.0
	var ex: Array = p[5] if p.size() > 5 else []
	match name:
		"_runner":   # carpet runner [len_v, width_m, mat]
			var bm := K.box(fn, pos + Vector3(0, 0.012, 0), Vector3(ex[1], 0.02, ex[0] * (info.D if info.kz != 1.0 else 1.0)), ex[2] if ex.size() > 2 else "blue", false, deg_to_rad(rot))
			K.box(fn, pos + Vector3(0, 0.01, 0), Vector3(ex[1] + 0.3, 0.015, ex[0] * (info.D if info.kz != 1.0 else 1.0) + 0.3), "gold", false, deg_to_rad(rot))
			bm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		"_area":     # floor inlay [w_m, d_m, mat]
			K.box(fn, pos + Vector3(0, 0.01, 0), Vector3(ex[0], 0.02, ex[1]), ex[2], false, deg_to_rad(rot))
		"_pillar":   # [height, radius, mat]
			var mi := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = ex[1]; cm.bottom_radius = ex[1]; cm.height = ex[0]
			mi.mesh = cm; mi.material_override = K.mat(ex[2] if ex.size() > 2 else "palestone"); mi.position = pos + Vector3(0, ex[0] / 2, 0); mi.layers = K.LAYER; fn.add_child(mi)
			var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var sh := CylinderShape3D.new(); sh.radius = ex[1]; sh.height = ex[0]; cs.shape = sh; sb.add_child(cs); mi.add_child(sb)
		"_gear":   # wooden gear wheel standing upright, faces along the rot direction [radius, hub height]
			var r: float = ex[0]; var hy: float = ex[1] if ex.size() > 1 else r + 0.2
			var g := Node3D.new(); g.position = pos + Vector3(0, hy, 0); g.rotation.y = deg_to_rad(rot); fn.add_child(g)
			var mi := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = r; cm.bottom_radius = r; cm.height = 0.18; cm.radial_segments = 24
			mi.mesh = cm; mi.material_override = K.mat("oak"); mi.rotation.x = PI / 2; mi.layers = K.LAYER; g.add_child(mi)
			K.box(g, Vector3.ZERO, Vector3(0.22, 0.22, 1.2), "iron", false)
			for k in 16:
				var a: float = TAU * k / 16.0
				var t := K.box(g, Vector3(cos(a), sin(a), 0) * (r + 0.08), Vector3(0.16, 0.16, 0.2), "darkoak", false); t.rotation.z = a
			for k in 4:
				var sp := K.box(g, Vector3.ZERO, Vector3(r * 2.0 - 0.1, 0.1, 0.1), "darkoak", false); sp.rotation.z = PI / 4 * k
			var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var sh := BoxShape3D.new(); sh.size = Vector3(r * 2.0, hy + r, 0.4)
			cs.shape = sh; cs.position.y = (hy + r) / 2.0; sb.add_child(cs); sb.position = pos; sb.rotation.y = deg_to_rad(rot); fn.add_child(sb)
		"_arena":   # round sand pit + low barrier + stepped stands [r_sand, r_barrier, r_stand0, r_stand1, steps, gap_half]
			var rs: float = ex[0]; var rb: float = ex[1]; var r0: float = ex[2]; var r1: float = ex[3]; var n: int = ex[4]; var gh: float = ex[5]
			var mi := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = rs; cm.bottom_radius = rs; cm.height = 0.04; cm.radial_segments = 48
			mi.mesh = cm; mi.material_override = K.mat("sand"); mi.position = pos + Vector3(0, 0.02, 0); mi.layers = K.LAYER; fn.add_child(mi)
			var ring := func(r: float, wd: float, h: float, y0: float, m: String, segs: int) -> void:
				for k in segs:
					var a: float = TAU * (k + 0.5) / segs; var c := Vector3(sin(a), 0, cos(a)) * r
					if absf(c.x) < gh + wd * 0.5: continue   # front (+z) and back (-z) passages
					var ln: float = TAU * r / segs + 0.06
					K.box(fn, pos + c + Vector3(0, y0 + h / 2, 0), Vector3(ln, h, wd), m, true, a)
			ring.call(rb, 0.3, 1.1, 0.0, "palestone", 40)
			for k in n:   # stands: each tier a solid ring, rising outward
				var w: float = (r1 - r0) / n; var r: float = r0 + w * (k + 0.5)
				ring.call(r, w + 0.02, 1.1 + 0.45 * (k + 1), 0.0, "stone" if k % 2 == 0 else "palestone", 40)
				ring.call(r, w * 0.5, 0.06, 1.1 + 0.45 * (k + 1), "blue" if k % 2 == 0 else "darkoak", 40)
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
			K.box(fn, pos + Vector3(0, ex[2] + ex[1] / 2, 0), Vector3(ex[0], ex[1], 0.06), ex[3] if ex.size() > 3 else "glass", false, deg_to_rad(rot))
			K.box(fn, pos + Vector3(0, ex[2] + ex[1] / 2, 0), Vector3(0.08, ex[1], 0.1), "iron", false, deg_to_rad(rot))
		"_pots":   # hanging pots/rack over kitchen [w]
			K.box(fn, pos + Vector3(0, 2.6, 0), Vector3(ex[0], 0.06, 0.06), "iron", false, deg_to_rad(rot))
			for k in 5: K.box(fn, pos + Vector3((k - 2) * ex[0] / 5.0, 2.3, 0).rotated(Vector3.UP, deg_to_rad(rot)), Vector3(0.3, 0.25, 0.3), "gold", false)
		"_tools":   # wall board of hanging smith tools (tongs, hammers, files) [width]
			var r := deg_to_rad(rot); var fw := Vector3(sin(r), 0, cos(r)); var rt := Vector3(cos(r), 0, -sin(r))
			K.box(fn, pos + Vector3(0, 1.9, 0) + fw * 0.03, Vector3(ex[0], 0.9, 0.05), "darkoak", false, r)
			K.box(fn, pos + Vector3(0, 2.3, 0) + fw * 0.08, Vector3(ex[0], 0.04, 0.04), "iron", false, r)
			var n := int(ex[0] / 0.22)
			for k in n:
				var L := 0.35 + 0.25 * float((k * 7) % 3)
				K.box(fn, pos + rt * ((k - (n - 1) / 2.0) * 0.22) + Vector3(0, 2.28 - L / 2, 0) + fw * 0.1, Vector3(0.035, L, 0.035), "iron", false, r)
				if k % 2 == 0: K.box(fn, pos + rt * ((k - (n - 1) / 2.0) * 0.22) + Vector3(0, 2.28 - L, 0) + fw * 0.1, Vector3(0.12, 0.07, 0.07), "iron", false, r)
		"_bread":   # loaves heaped on a counter/display [w, d, y]
			var r2 := deg_to_rad(rot)
			for k in int(ex[0] / 0.25) * 2:
				var o := Vector3(-ex[0] / 2 + 0.12 + (k / 2) * 0.25, 0, (-0.12 if k % 2 == 0 else 0.12) * ex[1] / 0.5).rotated(Vector3.UP, r2)
				var mi := MeshInstance3D.new(); var sm := SphereMesh.new(); sm.radius = 0.1; sm.height = 0.12; mi.mesh = sm
				var bm := K.mat("bread"); mi.material_override = bm; mi.position = pos + o + Vector3(0, ex[2] + 0.05, 0); mi.scale = Vector3(1.4, 1, 1); mi.layers = K.LAYER; fn.add_child(mi)
		"_gear":   # standing wooden gear wheel with iron axle [radius, y]
			var mi := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = ex[0]; cm.bottom_radius = ex[0]; cm.height = 0.25
			mi.mesh = cm; mi.material_override = K.mat("darkoak"); mi.position = pos + Vector3(0, ex[1], 0); mi.rotation = Vector3(PI / 2, deg_to_rad(rot), 0); mi.layers = K.LAYER; fn.add_child(mi)
			for k in 12:
				var a := TAU * k / 12.0
				K.box(fn, pos + Vector3(0, ex[1], 0) + Vector3(cos(a) * ex[0], sin(a) * ex[0], 0).rotated(Vector3.UP, deg_to_rad(rot)), Vector3(0.18, 0.18, 0.3), "oak", false, deg_to_rad(rot))
			K.box(fn, pos + Vector3(0, ex[1] / 2, 0), Vector3(0.2, ex[1], 0.2), "iron", true)
		_:
			var y_off: float = ex[0] if ex.size() > 0 else 0.0
			var pr := K.prop(fn, name, pos + Vector3(0, y_off, 0), rot, not (ex.size() > 1 and ex[1] == false))
			if name == "throne_dais": _dais_runner(pr)

## test 13 (boss: flat rug floating across the dais steps): Beth's dais rug is stripped from the kit copy and replaced by
## a stair runner that follows every tread and riser, same rug texture (atlas region of the old rug), centred on the steps.
## Dais profile (kit, +Z front): floor y0 z 0.98..1.6 | tread y0.2 z 0.62..0.98 | y0.4 z 0.30..0.62 | top y0.6 z -0.4..0.30
const RUNNER_UV := Rect2(0.7622, 0.5122, 0.2256, 0.2256)
static func _dais_runner(pr: Node3D) -> void:
	var mat: Material = null
	for mi in pr.find_children("*", "MeshInstance3D", true, false): mat = (mi as MeshInstance3D).get_active_material(0); break
	var segs := [[Vector3(0, 0.605, -0.4), Vector3(0, 0.605, 0.3)], [Vector3(0, 0.605, 0.3), Vector3(0, 0.405, 0.3)],
		[Vector3(0, 0.405, 0.3), Vector3(0, 0.405, 0.62)], [Vector3(0, 0.405, 0.62), Vector3(0, 0.205, 0.62)],
		[Vector3(0, 0.205, 0.62), Vector3(0, 0.205, 0.98)], [Vector3(0, 0.205, 0.98), Vector3(0, 0.005, 0.98)],
		[Vector3(0, 0.005, 0.98), Vector3(0, 0.005, 1.6)]]
	var total := 0.0
	for sg in segs: total += (sg[1] - sg[0]).length()
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var hw := 0.6; var acc := 0.0
	for sg in segs:
		var a: Vector3 = sg[0]; var b: Vector3 = sg[1]; var L := (b - a).length()
		var riser := absf(a.y - b.y) > 0.01
		var off := Vector3(0, 0, 0.006) if riser else Vector3.ZERO     # risers sit just proud of the stone face
		var n := Vector3(0, 0, 1) if riser else Vector3.UP
		var v0 := RUNNER_UV.position.y + RUNNER_UV.size.y * acc / total; var v1 := RUNNER_UV.position.y + RUNNER_UV.size.y * (acc + L) / total
		var u0 := RUNNER_UV.position.x; var u1 := RUNNER_UV.end.x
		var q := [[a + Vector3(-hw, 0, 0) + off, Vector2(u0, v0)], [a + Vector3(hw, 0, 0) + off, Vector2(u1, v0)], [b + Vector3(hw, 0, 0) + off, Vector2(u1, v1)], [b + Vector3(-hw, 0, 0) + off, Vector2(u0, v1)]]
		for idx in [0, 2, 1, 0, 3, 2, 0, 1, 2, 0, 2, 3]:   # both windings (atlas material is single-sided)
			st.set_normal(n); st.set_uv(q[idx][1]); st.add_vertex(q[idx][0])
		acc += L
	var mi2 := MeshInstance3D.new(); mi2.name = "StairRunner"; mi2.mesh = st.commit(); mi2.layers = K.LAYER
	mi2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if mat: mi2.material_override = mat
	pr.add_child(mi2)

static func _light(info: Dictionary, l: Array, P: Callable) -> void:
	# [kind, floor, u, v, rot, energy, range, shadow]
	var kind: String = l[0]; var F: Dictionary = info.floors[l[1]]; var fn: Node3D = F.node
	var pos: Vector3 = P.call(l[2], l[3], F.y); var rot: float = l[4]
	var e: float = l[5] * 2.4; var rng: float = l[6] * 1.25; var sh: bool = l[7] if l.size() > 7 else false
	var lp := pos
	match kind:
		"chandelier":
			var cy: float = maxf(F.h - 2.1, 2.2)
			var ch := K.prop(fn, "iron_chandelier", pos + Vector3(0, cy, 0), rot, false)
			K.set_layers(ch, false)   # test 13: its own light sits above it -> it cast a dark disc/octagon on the floor
			K.box(fn, pos + Vector3(0, cy + 2.0 + (F.h - cy - 2.0) / 2, 0), Vector3(0.04, maxf(F.h - cy - 2.0, 0.01), 0.04), "iron", false)
			lp = pos + Vector3(0, cy + 0.6, 0)
		"lantern":
			K.prop(fn, "wall_lantern", pos + Vector3(0, 2.1, 0), rot, false); lp = pos + Vector3(0, 2.3, 0) + Vector3(sin(deg_to_rad(rot)), 0, cos(deg_to_rad(rot))) * 0.4
		"fire": lp = pos + Vector3(0, 0.8, 0)
		_: lp = pos + Vector3(0, 2.5, 0)
	var o := OmniLight3D.new(); o.position = lp; o.light_color = Color(1.0, 0.89, 0.74) if kind != "fire" else Color(1.0, 0.72, 0.45)
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
