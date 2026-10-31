class_name InteriorDressing
## PASS 2 (max quality). Same API/paths as pass 1: drop-in replacement of res://interiors/pass/.
## Beth's interior detail pass (all InteriorBuilder interiors). Call once right after InteriorBuilder.build():
##   InteriorDressing.apply(info, def, tier)   # tier "high" (S26 Ultra / desktop) or "low" (phone Low/Medium)
## Purely visual, adds NO colliders and moves nothing walkable: same layout, footprint and collision as before.
## - stone / flag / oak boxes re-skinned: small ashlar blocks (0.3 x 0.6 m) with mortar normals + roughness, flagstone
##   floor, oak planks; ceilings of planks + timber beams on every floor (no more black void when the floor above hides)
## - flat glowing window panes -> stone surround, sill, iron leading, glass showing sky + hills (or stained glass);
##   windows that sat behind a wall lantern are dropped (no more lanterns floating in windows)
## - stair columns -> ashlar mass with oak treads + nosing, iron rail on the open side (High)
## - base trim + cornice on outer walls, stone door frame, pilasters with torch sconces (tall floors), rugs under tables,
##   banners pulled 8 cm off the wall (pole clipping)
## Ceilings/beams hide themselves while the camera is above them (the high over-the-walls interior camera).
const DIR := "res://interiors/pass/"
const K := preload("res://interiors/interior_kit.gd")
const WALL_T := 0.35
const SLAB_T := 0.25
static var _m := {}
static var tier_cache := ""

static func mat(kind: String, tier: String) -> Material:
	var key := kind + "/" + tier
	if _m.has(key): return _m[key]
	var td := DIR + ("tex/" if tier == "high" else "tex_low/")
	var m := StandardMaterial3D.new()
	# [texture set, tint, tile metres]
	var T := {"ashlar": ["p2_ashlar", Color(1.0, 0.97, 0.93), 2.0], "ashlar_dark": ["p2_ashlar", Color(0.62, 0.59, 0.56), 2.0],
		"rubble": ["p2_rubble", Color(1.15, 1.12, 1.08), 2.6], "flag": ["p2_flag", Color(1.15, 1.12, 1.08), 3.0], "palestone": ["p2_flag", Color(1.25, 1.2, 1.12), 3.0],
		"oak": ["p2_oak", Color(1, 1, 1), 2.2], "darkoak": ["p2_oak", Color(0.62, 0.52, 0.45), 2.2], "plaster": ["p2_plaster", Color(1.05, 1.03, 1.0), 2.6]}
	match kind:
		"iron": m.albedo_color = Color(0.14, 0.135, 0.13); m.metallic = 0.8; m.roughness = 0.5
		"brass": m.albedo_color = Color(0.72, 0.55, 0.25); m.metallic = 0.9; m.roughness = 0.32
		"cloth": m.albedo_color = Color(0.62, 0.54, 0.4); m.roughness = 1.0
		"redcloth": m.albedo_color = Color(0.5, 0.1, 0.08); m.roughness = 0.95
		"glassb": m.albedo_color = Color(0.25, 0.5, 0.35, 0.75); m.roughness = 0.1; m.metallic = 0.2; m.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
		"glassr": m.albedo_color = Color(0.55, 0.15, 0.12); m.roughness = 0.12; m.metallic = 0.2
		"hay": m.albedo_color = Color(0.78, 0.64, 0.32); m.roughness = 1.0
		"clay": m.albedo_color = Color(0.6, 0.36, 0.22); m.roughness = 0.9
		"paper": m.albedo_color = Color(0.86, 0.8, 0.64); m.roughness = 0.95
		"gold": m.albedo_color = Color(0.85, 0.66, 0.25); m.metallic = 1.0; m.roughness = 0.28
		"coal": m.albedo_color = Color(0.05, 0.04, 0.04); m.roughness = 1.0
		"ember": m.albedo_color = Color(1, 0.4, 0.1); m.emission_enabled = true; m.emission = Color(1, 0.35, 0.08); m.emission_energy_multiplier = 3.0; m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		"flame": m.albedo_color = Color(1, 0.62, 0.25); m.emission_enabled = true; m.emission = Color(1, 0.55, 0.2); m.emission_energy_multiplier = 2.6; m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		"view", "view_stained", "rose":
			m.albedo_texture = load(td + {"view": "p2_view.jpg", "view_stained": "p2_stained.jpg", "rose": "p2_rose.jpg"}[kind]); m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.albedo_color = Color(1.15, 1.12, 1.08) if kind == "view" else Color(1.45, 1.42, 1.4)
		"shaft":
			m.albedo_texture = load(td + "p2_shaft.png"); m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD; m.cull_mode = BaseMaterial3D.CULL_DISABLED
			m.albedo_color = Color(0.9, 0.8, 0.95, 0.22); m.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
		"rug", "rug_red", "rug_blue", "rug_green":
			var c := "red" if kind == "rug" else kind.substr(4)
			m.albedo_texture = load(td + "p2_rug_%s_albedo.jpg" % c); m.roughness = 0.95
			m.normal_enabled = true; m.normal_texture = load(td + "p2_rug_%s_normal.png" % c); m.normal_scale = 0.5
		_:
			var t: Array = T.get(kind, T.ashlar)
			m.albedo_texture = load(td + t[0] + "_albedo.jpg"); m.albedo_color = t[1]
			m.normal_enabled = true; m.normal_texture = load(td + t[0] + "_normal.png"); m.normal_scale = 1.15
			m.roughness_texture = load(td + t[0] + "_rough.png"); m.roughness = 1.0
			if tier == "high": m.ao_enabled = true; m.ao_texture = load(td + t[0] + "_ao.png"); m.ao_light_affect = 0.6
			m.uv1_triplanar = true; m.uv1_world_triplanar = true; m.uv1_scale = Vector3.ONE / t[2]; m.uv1_triplanar_sharpness = 4.0
	_m[key] = m
	return m

## ---- batched geometry: one MeshInstance per material per floor (draw calls stay low on Mobile)
class Batch:
	var st := {}
	var tris := 0
	func box(xf: Transform3D, size: Vector3, kind: String) -> void:
		if not st.has(kind): var s := SurfaceTool.new(); s.begin(Mesh.PRIMITIVE_TRIANGLES); st[kind] = s
		var s: SurfaceTool = st[kind]; var h := size / 2
		var faces := [[Vector3.RIGHT, Vector3.BACK, Vector3.UP], [Vector3.LEFT, Vector3.FORWARD, Vector3.UP], [Vector3.UP, Vector3.RIGHT, Vector3.BACK],
			[Vector3.DOWN, Vector3.RIGHT, Vector3.FORWARD], [Vector3.BACK, Vector3.LEFT, Vector3.UP], [Vector3.FORWARD, Vector3.RIGHT, Vector3.UP]]
		for f in faces:
			var n: Vector3 = f[0]; var u: Vector3 = f[1]; var v: Vector3 = f[2]
			var c := n * h; var uu := u * h; var vv := v * h
			var q := [c - uu - vv, c + uu - vv, c + uu + vv, c - uu + vv]
			var wn := (xf.basis * n).normalized()
			for i in [0, 1, 2, 0, 2, 3]:
				s.set_normal(wn); s.set_uv(Vector2(float(i == 1 or i == 2), float(i >= 2))); s.add_vertex(xf * q[i])
			tris += 2
	func quad(xf: Transform3D, w: float, h: float, kind: String) -> void:   # faces local +Z, single-sided
		if not st.has(kind): var s := SurfaceTool.new(); s.begin(Mesh.PRIMITIVE_TRIANGLES); st[kind] = s
		var s: SurfaceTool = st[kind]
		var q := [Vector3(-w / 2, -h / 2, 0), Vector3(w / 2, -h / 2, 0), Vector3(w / 2, h / 2, 0), Vector3(-w / 2, h / 2, 0)]
		var uv := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)]
		var wn := (xf.basis * Vector3.BACK).normalized()
		for i in [0, 2, 1, 0, 3, 2]: s.set_normal(wn); s.set_uv(uv[i]); s.add_vertex(xf * q[i])
		tris += 2
	func cyl(xf: Transform3D, r: float, h: float, seg: int, kind: String, r2 := -1.0, bulge := 0.0) -> void:   # axis local +Y, centred
		if not st.has(kind): var s0 := SurfaceTool.new(); s0.begin(Mesh.PRIMITIVE_TRIANGLES); st[kind] = s0
		var s: SurfaceTool = st[kind]; if r2 < 0: r2 = r
		var rings := 3 if bulge > 0 else 1
		for k in seg:
			var a0 := TAU * k / seg; var a1 := TAU * (k + 1) / seg
			for j in rings:
				var t0 := float(j) / rings; var t1 := float(j + 1) / rings
				var ra := lerpf(r, r2, t0) + bulge * sin(PI * t0); var rb := lerpf(r, r2, t1) + bulge * sin(PI * t1)
				var y0 := -h / 2 + h * t0; var y1 := -h / 2 + h * t1
				var p := [Vector3(cos(a0) * ra, y0, sin(a0) * ra), Vector3(cos(a1) * ra, y0, sin(a1) * ra), Vector3(cos(a1) * rb, y1, sin(a1) * rb), Vector3(cos(a0) * rb, y1, sin(a0) * rb)]
				var nn := [Vector3(cos(a0), 0, sin(a0)), Vector3(cos(a1), 0, sin(a1)), Vector3(cos(a1), 0, sin(a1)), Vector3(cos(a0), 0, sin(a0))]
				for i in [0, 1, 2, 0, 2, 3]: s.set_normal((xf.basis * nn[i]).normalized()); s.set_uv(Vector2(float(k) / seg, t0)); s.add_vertex(xf * p[i])
				tris += 2
			for cap in [[-h / 2, r, -1.0], [h / 2, r2, 1.0]]:   # caps
				var cy: float = cap[0]; var cr: float = cap[1]; var sg: float = cap[2]
				var q := [Vector3(0, cy, 0), Vector3(cos(a0) * cr, cy, sin(a0) * cr), Vector3(cos(a1) * cr, cy, sin(a1) * cr)]
				var order := [0, 1, 2] if sg > 0 else [0, 2, 1]
				for i in order: s.set_normal((xf.basis * Vector3(0, sg, 0)).normalized()); s.set_uv(Vector2(0.5, 0.5)); s.add_vertex(xf * q[i])
				tris += 1
	func commit(parent: Node3D, tier: String, nm: String, shadow := true) -> Node3D:
		var root := Node3D.new(); root.name = nm; parent.add_child(root)
		for k in st:
			var mi := MeshInstance3D.new(); mi.name = k; var s: SurfaceTool = st[k]
			mi.mesh = s.commit(); mi.material_override = InteriorDressing.mat(k, tier); mi.layers = InteriorKit.LAYER
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow and k != "rug" and not k.begins_with("view") else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			root.add_child(mi)
		return root

static func _xf(pos: Vector3, rot := 0.0) -> Transform3D: return Transform3D(Basis(Vector3.UP, rot), pos)

## returns {"tris": added triangles, "lights": added lights, "windows": n, "bricked": n}
static func apply(info: Dictionary, def: Dictionary, tier := "high") -> Dictionary:
	var hi := tier == "high"
	var W: float = info.W; var D: float = info.D; var hw := W / 2; var hd := D / 2
	var stats := {"tris": 0, "lights": 0, "windows": 0, "bricked": 0}
	var light_cap := 4 if hi else 0
	var ceilings := []
	var base_id := String(info.id).get_slice("#", 0)
	var rough_walls: bool = base_id in ["crypt", "thieves", "smithy", "stables", "barn", "lighthouse", "harbour_warehouse"]
	var skin := {K.mat("stone"): "rubble" if rough_walls else "ashlar", K.mat("flag"): "flag", K.mat("oak"): "oak", K.mat("darkoak"): "darkoak",
		K.mat("palestone"): "palestone", K.mat("plaster"): "plaster"}
	var variant: String = def.get("variant", "")
	var rng := RandomNumberGenerator.new(); rng.seed = hash(String(info.id) + variant)
	var theme_id := base_id.trim_suffix("_" + variant) if variant != "" else base_id
	var rugk: String = ["rug_red", "rug_blue", "rug_green"][rng.randi() % 3]
	var flick := []
	var draw_layers := 0
	var nf: int = info.floors.size()
	for i in nf:
		var F: Dictionary = info.floors[i]; var fn: Node3D = F.node; var y0: float = F.y; var h: float = F.h
		var B := Batch.new()
		# props + lanterns on this floor (for window / pilaster clearance)
		var lanterns := []; var props := []
		for c in fn.get_children():
			if c is Node3D and not (c is MeshInstance3D) and not (c is OmniLight3D) and not (c is StaticBody3D):
				props.append(c)
				if String(c.name).begins_with("wall_lantern"): lanterns.append(c.position)
		# stair footprints of this floor
		var srects := []
		for s in info.stairs: if s.floor == i: srects.append(s)
		for c in fn.get_children():
			if not (c is MeshInstance3D): continue
			var mi := c as MeshInstance3D; var mo = mi.material_override
			var bm := mi.mesh as BoxMesh
			# 0) tall flat stained-glass wall (_glasswall prop: the keep's throne window) -> rose window with tracery + light shafts
			if bm and (mo == K.mat("stained") or mo == K.mat("glass")) and is_equal_approx(bm.size.z, 0.06):
				mi.visible = false
				# fit under the pass ceiling (the throne window ran 0.6 m up into the floor above)
				var gtop := minf(mi.position.y + bm.size.y / 2, y0 + h - SLAB_T - 0.95); var gbot := minf(mi.position.y - bm.size.y / 2, y0 + 1.4)
				_glasswall(B, fn, Vector3(mi.position.x, (gtop + gbot) / 2, mi.position.z), mi.rotation.y, bm.size.x + 0.6, gtop - gbot, y0, hi, stats, hw, hd)
				continue
			if bm and mo == K.mat("iron") and is_equal_approx(bm.size.x, 0.08) and is_equal_approx(bm.size.z, 0.1): mi.visible = false; continue
			# 1) flat window panes + their lintels
			if bm and (mo == K.mat("glass") or mo == K.mat("stained")) and is_equal_approx(bm.size.z, 0.04) and is_equal_approx(bm.size.x, 0.9):
				var stained: bool = mo == K.mat("stained")
				mi.visible = false
				var near := false
				for lp in lanterns: if Vector2(lp.x, lp.z).distance_to(Vector2(mi.position.x, mi.position.z)) < 1.2: near = true
				_window(B, mi.position, mi.rotation.y, bm.size.y, near, stained, hi, hw, hd)
				stats.windows += 1; if near: stats.bricked += 1
				continue
			if bm and mo == K.mat("darkoak") and bm.size.is_equal_approx(Vector3(1.1, 0.12, 0.08)): mi.visible = false; continue
			# 2) stair step columns (visual only, no collider child) -> hidden, rebuilt below
			if bm and (mo == K.mat("oak") or mo == K.mat("darkoak")) and mi.get_child_count() == 0 and _in_stair(mi.position, srects): mi.visible = false; continue
			# 3) re-skin
			if skin.has(mo): mi.material_override = mat(skin[mo], tier)
		for s in srects: _stair(B, s, hi)
		# 4) ceiling: planks under the next slab (minus stair holes) / under the roof on the top floor, beams below
		var C := Batch.new()
		var ytop := y0 + h - (SLAB_T if i < nf - 1 else 0.0) - 0.01
		var cells: Array = []
		if i < nf - 1:
			for ln in info.floors[i + 1].lines: if ln is Rect2: cells.append(ln)
		else: cells.append(Rect2(-hw, -hd, W, D))
		for r: Rect2 in cells:
			C.quad(Transform3D(Basis(Vector3.RIGHT, PI / 2), Vector3(r.get_center().x, ytop, r.get_center().y)), r.size.x, r.size.y, "oak")
		if i < nf - 1:   # roof board over atria / stair wells (shows only through holes in the slab above)
			var yroof: float = info.floors[nf - 1].y + info.floors[nf - 1].h - 0.01
			C.quad(Transform3D(Basis(Vector3.RIGHT, PI / 2), Vector3(0, yroof, 0)), W, D, "oak")
		var span_x := W <= D   # beams cross the short span
		var L := W if not span_x else D
		var step := 2.4 if hi else 4.8
		var nb := int(L / step)
		for k in range(1, nb + 1):
			var t := -L / 2 + k * L / (nb + 1)
			var c := Vector3(0, ytop - 0.17, t) if span_x else Vector3(t, ytop - 0.17, 0)
			var sz := Vector3(W - 2 * WALL_T, 0.32, 0.26) if span_x else Vector3(0.26, 0.32, D - 2 * WALL_T)
			if not _beam_hits_hole(c, sz, srects): C.box(_xf(c), sz, "darkoak")
		# wall plates (High)
		if hi: C.box(_xf(Vector3(0, ytop - 0.11, -hd + WALL_T / 2 + 0.11)), Vector3(W - WALL_T, 0.2, 0.2), "darkoak")
		if hi: C.box(_xf(Vector3(0, ytop - 0.11, hd - WALL_T / 2 - 0.11)), Vector3(W - WALL_T, 0.2, 0.2), "darkoak")
		if hi: C.box(_xf(Vector3(-hw + WALL_T / 2 + 0.11, ytop - 0.11, 0)), Vector3(0.2, 0.2, D - WALL_T), "darkoak")
		if hi: C.box(_xf(Vector3(hw - WALL_T / 2 - 0.11, ytop - 0.11, 0)), Vector3(0.2, 0.2, D - WALL_T), "darkoak")
		var cn := C.commit(fn, tier, "PassCeiling", false); cn.set_meta("ytop", ytop - 0.45); ceilings.append(cn)
		stats.tris += C.tris
		# 5) trims: baseboard + cornice on the 4 outer walls (front wall split at the door on floor 0)
		var segs := [[Vector2(-hw, -hd), Vector2(hw, -hd), 1.0], [Vector2(-hw, -hd), Vector2(-hw, hd), 1.0], [Vector2(hw, -hd), Vector2(hw, hd), -1.0]]
		if i == 0:
			segs.append([Vector2(-hw, hd), Vector2(-1.1, hd), -1.0]); segs.append([Vector2(1.1, hd), Vector2(hw, hd), -1.0])
		else: segs.append([Vector2(-hw, hd), Vector2(hw, hd), -1.0])
		for sg in segs:
			var a: Vector2 = sg[0]; var b: Vector2 = sg[1]; var dv := (b - a); var len := dv.length(); dv /= len
			var nrm := Vector2(-dv.y, dv.x) * (1.0 if absf(dv.x) > 0.5 else -1.0) * float(sg[2]) * (1.0 if absf(dv.x) > 0.5 else -1.0)
			# inward normal: towards the centre
			var mid := (a + b) / 2; var inward := (-mid).normalized()
			nrm = Vector2(inward.x, 0).normalized() if absf(dv.y) > 0.5 else Vector2(0, inward.y).normalized()
			var rot := -atan2(dv.y, dv.x)
			var off := mid + nrm * (WALL_T / 2 + 0.03)
			if hi or i == 0: B.box(_xf(Vector3(off.x, y0 + 0.14, off.y), rot), Vector3(len, 0.28, 0.07), "ashlar_dark" if i == 0 else "darkoak")
			var off2 := mid + nrm * (WALL_T / 2 + 0.07)
			if hi: B.box(_xf(Vector3(off2.x, ytop - 0.32, off2.y), rot), Vector3(len, 0.16, 0.14), "ashlar_dark")
		# door frame (floor 0 front)
		if i == 0 and hi:
			for sx in [-1, 1]: B.box(_xf(Vector3(sx * 1.25, y0 + 1.5, hd - WALL_T / 2 - 0.05)), Vector3(0.3, 3.0, WALL_T + 0.14), "ashlar_dark")
			B.box(_xf(Vector3(0, y0 + 3.15, hd - WALL_T / 2 - 0.05)), Vector3(2.8, 0.34, WALL_T + 0.16), "ashlar_dark")
		# 6) pilasters + torch sconces on tall floors, between windows on the side walls
		if h >= 3.8:
			var ws: float = (def.floors[i] as Dictionary).get("win", 4.0)
			var n := int(D / ws) if ws > 0 else 3
			for side in [-1, 1]:
				for k in range(1, n):
					var z := -hd + D * k / n
					var x: float = side * (hw - WALL_T / 2 - 0.1)
					var p := Vector3(x, y0, z)
					if _crowded(p, props, 0.9) or _in_stair(p, srects): continue
					if not hi and k % 2 == 0: continue
					B.box(_xf(p + Vector3(0, h / 2, 0)), Vector3(0.22, h - 0.1, 0.55), "ashlar")
					if hi:
						B.box(_xf(p + Vector3(-side * 0.04, 0.2, 0)), Vector3(0.32, 0.4, 0.7), "ashlar_dark")
						B.box(_xf(p + Vector3(-side * 0.04, ytop - y0 - 0.5, 0)), Vector3(0.3, 0.25, 0.68), "ashlar_dark")
					if k % 2 == 1:   # sconce: iron bracket + torch + flame
						var tp := p + Vector3(-side * 0.25, 2.5, 0)
						B.box(_xf(tp + Vector3(side * 0.1, -0.1, 0)), Vector3(0.2, 0.05, 0.05), "iron")
						B.box(_xf(tp), Vector3(0.06, 0.4, 0.06), "darkoak")
						B.box(_xf(tp + Vector3(0, 0.27, 0)), Vector3(0.12, 0.16, 0.12), "flame")
						if stats.lights < light_cap:
							var o := OmniLight3D.new(); o.position = tp + Vector3(-side * 0.15, 0.4, 0); o.light_color = Color(1.0, 0.7, 0.42)
							o.light_energy = 1.6; o.omni_range = 6.0; o.omni_attenuation = 1.3; o.shadow_enabled = false; o.light_cull_mask = K.LAYER | 1
							o.light_specular = 0.2; fn.add_child(o); stats.lights += 1; flick.append(o)
		# 6b) purpose clutter along the walls (visual only) + goods on tables/counters
		var theme: Array = InteriorProps2.THEME.get(theme_id, ["crates", "barrels"])
		var cands := _clutter_spots(info, def, i, props, srects, hw, hd)
		var dens := 7.0 if theme_id in ["harbour_warehouse", "market", "barn", "thieves"] else 12.0
		var maxn := int(clampf(W * D / dens, 3, 16)) if hi else int(clampf(W * D / (dens * 3.0), 1, 5))
		var order := range(cands.size()); _shuffle(order, rng)
		var placed := []
		for idx in order:
			if placed.size() >= maxn: break
			if dens < 10.0: pass
			var c: Array = cands[idx]; var cp: Vector3 = c[0]
			var ok := true
			for q in placed: if q.distance_to(cp) < (1.05 if dens < 10.0 else 1.5): ok = false
			if not ok: continue
			placed.append(cp)
			InteriorProps2.build(B, theme[rng.randi() % theme.size()], _xf(Vector3(cp.x, y0, cp.z), c[1]), rng, hi)
		stats["clutter"] = stats.get("clutter", 0) + placed.size()
		var topk: String = InteriorProps2.TOP.get(theme_id, "mugs")
		for pr in props:
			var nm2 := String(pr.name)
			var kn := ""
			for t in ["meeting_table", "table", "bar_counter"]: if nm2.begins_with(t) or nm2.contains("@" + t): kn = t; break
			if kn == "": continue
			var sm: Array = K.index().get(kn, {}).get("size_m", [1.4, 0.78, 0.8])
			InteriorProps2.top(B, Transform3D(pr.basis, pr.position + Vector3(0, float(sm[1]) + 0.005, 0)), topk, rng, hi, float(sm[0]) * 0.8, float(sm[2]) * 0.7)
		# 6c) decals (High): grime at the door + wall bases, soot over torches/hearths, cracks / moss on rough walls
		if hi:
			var nd := 0
			if i == 0: _decal(fn, "dirt", Vector3(0, y0, hd - 1.2), Vector3(2.6, 1.0, 2.2), 0.0, true); nd += 1
			for pr in props:
				if String(pr.name).begins_with("hearth") or String(pr.name).begins_with("forge"):
					_decal(fn, "soot", pr.position + Vector3(0, 2.2, 0) - pr.basis.z * 0.2, Vector3(1.8, 0.8, 2.2), pr.rotation.y, false); nd += 1
			for o in flick: _decal(fn, "soot", o.position + Vector3(0, 0.3, 0), Vector3(0.8, 0.8, 1.2), atan2(-o.position.x, 0.0001) if absf(o.position.x) > absf(o.position.z) else 0.0, false, true); nd += 1
			for k in 6:
				if cands.is_empty(): break
				var c: Array = cands[rng.randi() % cands.size()]; var wp: Vector3 = c[0]
				var kind2: String = ["dirt", "stain", "cracks", "moss" if rough_walls else "cracks"][k % 4]
				if kind2 == "dirt": _decal(fn, "dirt", Vector3(wp.x, y0, wp.z), Vector3(1.8, 1.0, 1.4), c[1], true)
				else: _decal(fn, kind2, Vector3(wp.x, y0 + rng.randf_range(0.6, 2.2), wp.z), Vector3(1.4, 1.2, 1.4), c[1], false)
				nd += 1
			stats["decals"] = stats.get("decals", 0) + nd
			# one reflection probe per floor (updated once; interior ambient off so the lights stay the key)
			var rp := ReflectionProbe.new(); rp.size = Vector3(W, h, D); rp.position = Vector3(0, y0 + h / 2, 0); rp.interior = true
			rp.box_projection = true; rp.update_mode = ReflectionProbe.UPDATE_ONCE; rp.cull_mask = K.LAYER; rp.max_distance = maxf(W, D)
			rp.ambient_mode = ReflectionProbe.AMBIENT_DISABLED; fn.add_child(rp)
		# warm flicker on fire / torch lights of this floor
		for c in fn.get_children():
			if c is OmniLight3D and (c as OmniLight3D).light_color.g < 0.8: flick.append(c)
		# 7) rugs under tables on stone floors; banners off the wall
		for pr in props:
			var nm := String(pr.name)
			if (nm.begins_with("meeting_table") or nm.begins_with("table")) and (def.floors[i] as Dictionary).get("mat", "flag") != "oak":
				var big := nm.begins_with("meeting")
				B.quad(Transform3D(Basis(Vector3.UP, pr.rotation.y) * Basis(Vector3.RIGHT, -PI / 2), pr.position + Vector3(0, 0.015, 0)), 2.6 if big else 2.0, 4.2 if big else 2.6, rugk)
			if nm.begins_with("lion_banner"): pr.position += pr.basis.z * 0.08
		var bn := B.commit(fn, tier, "PassDressing")
		stats.tris += B.tris
	var ctl := Node.new(); ctl.name = "PassCeilingCtl"; ctl.set_script(load(DIR + "dressing/ceiling_ctl.gd")); ctl.set("ceilings", ceilings); ctl.set("flicker", flick)
	(info.node as Node3D).add_child(ctl)
	info["pass"] = stats
	return stats

static func _crowded(p: Vector3, props: Array, r: float) -> bool:
	for pr in props: if Vector2(pr.position.x, pr.position.z).distance_to(Vector2(p.x, p.z)) < r: return true
	return false

static func _in_stair(p: Vector3, srects: Array) -> bool:
	for s in srects:
		var rel: Vector3 = p - s.base; var along: float = rel.x * s.dir.x + rel.z * s.dir.z
		var lat: float = absf(rel.x * -s.dir.z + rel.z * s.dir.x)
		if along > -0.05 and along < s.run + 0.05 and lat < s.w / 2 + 0.05: return true
	return false

static func _beam_hits_hole(c: Vector3, sz: Vector3, srects: Array) -> bool:
	var r := Rect2(Vector2(c.x - sz.x / 2, c.z - sz.z / 2), Vector2(sz.x, sz.z))
	for s in srects:
		var top: Vector3 = s.base + s.dir * s.run
		var sr := Rect2(Vector2(s.base.x, s.base.z), Vector2.ZERO).expand(Vector2(top.x, top.z)).grow(s.w / 2 + 0.1)
		if r.intersects(sr): return true
	return false

static func _window(B: Batch, p: Vector3, rot: float, wh: float, bricked: bool, stained: bool, hi: bool, hw: float, hd: float) -> void:
	# inward normal (pane sits 0.03 inside the wall face)
	var fwd := Vector3(sin(rot), 0, cos(rot))
	var inward := fwd if fwd.dot(-Vector3(p.x, 0, p.z)) > 0 else -fwd
	var r := rot
	var w := 1.0; var face := p - inward * 0.02
	if bricked: return   # window dropped: the lantern stays on a solid wall
	B.quad(Transform3D(Basis(Vector3.UP, atan2(inward.x, inward.z)), face - inward * 0.0), w, wh, "view_stained" if stained else "view")
	if not hi:   # Low: glass + sill only
		B.box(_xf(face + inward * 0.1 + Vector3(0, -wh / 2 - 0.07, 0), r), Vector3(w + 0.5, 0.14, 0.28), "ashlar_dark"); return
	for sx in [-1, 1]: B.box(_xf(face + inward * 0.06 + (Vector3(cos(r), 0, -sin(r)) * sx * (w / 2 + 0.11)), r), Vector3(0.22, wh + 0.1, 0.16), "ashlar_dark")
	B.box(_xf(face + inward * 0.1 + Vector3(0, -wh / 2 - 0.07, 0), r), Vector3(w + 0.5, 0.14, 0.28), "ashlar_dark")   # sill
	B.box(_xf(face + inward * 0.06 + Vector3(0, wh / 2 + 0.11, 0), r), Vector3(w + 0.44, 0.22, 0.18), "ashlar_dark")       # head
	if hi: B.box(_xf(face + inward * 0.06 + Vector3(0, wh / 2 + 0.3, 0), r), Vector3(0.3, 0.2, 0.2), "ashlar_dark")  # keystone
	# leading: mullion + 2 transoms
	B.box(_xf(face + inward * 0.015, r), Vector3(0.04, wh, 0.03), "iron")
	for ty in ([-wh / 6, wh / 6] if hi else [0.0]): B.box(_xf(face + inward * 0.015 + Vector3(0, ty, 0), r), Vector3(w, 0.03, 0.03), "iron")

static func _stair(B: Batch, s: Dictionary, hi: bool) -> void:
	var d: Vector3 = s.dir; var Lr: float = s.run; var H: float = s.rise; var w: float = s.w; var b: Vector3 = s.base
	var rot := atan2(-d.x, -d.z); var side := Vector3(-d.z, 0, d.x)
	var n := int(ceil(H / 0.2)); var run := Lr / n
	for k in n:
		var s0 := Lr * k / n; var top := H * (k + 1) / n
		var c := b + d * (s0 + run / 2)
		if not hi: B.box(_xf(c + Vector3(0, top / 2, 0), rot), Vector3(w, top, run), "ashlar"); continue
		B.box(_xf(c + Vector3(0, (top - 0.05) / 2, 0), rot), Vector3(w, top - 0.05, run), "ashlar")
		B.box(_xf(c + Vector3(0, top - 0.025, 0) - d * 0.03, rot), Vector3(w + 0.04, 0.05, run + 0.06), "oak")
	if hi:   # iron rail on both sides: posts every 3 steps + sloped handrail
		for sx in [-1, 1]:
			for k in range(0, n, 3):
				var c2: Vector3 = b + d * (Lr * (k + 0.5) / n) + side * sx * (w / 2 - 0.04)
				var top2 := H * (k + 1) / n
				B.box(_xf(c2 + Vector3(0, top2 + 0.45, 0), rot), Vector3(0.04, 0.9, 0.04), "iron")
			var mid: Vector3 = b + d * (Lr / 2) + side * sx * (w / 2 - 0.04) + Vector3(0, H / 2 + 0.92, 0)
			var bas := Basis(Vector3.UP, rot) * Basis(Vector3.RIGHT, atan2(H, Lr))
			B.box(Transform3D(bas, mid), Vector3(0.05, 0.05, sqrt(Lr * Lr + H * H)), "iron")

static func _shuffle(a: Array, rng: RandomNumberGenerator) -> void:
	for i in range(a.size() - 1, 0, -1):
		var j := rng.randi_range(0, i); var t = a[i]; a[i] = a[j]; a[j] = t

## wall spots 0.5 m in from the outer walls, facing the room; clear of props, doors, stairs, room waypoints, partitions
static func _clutter_spots(info: Dictionary, def: Dictionary, i: int, props: Array, srects: Array, hw: float, hd: float) -> Array:
	var out := []; var inset := WALL_T / 2 + 0.45
	var small: bool = hw * hd * 4.0 < 60.0   # cottages / shops: tighter clearances (still off the walk lines)
	var F: Dictionary = info.floors[i]
	var parts := []
	for wd in def.get("walls", []):
		if wd[0] == i: parts.append([Vector2(wd[1] * info.kx, wd[2] * info.kz), Vector2(wd[3] * info.kx, wd[4] * info.kz)])
	var sides := [[Vector2(-hw + inset, -hd + inset), Vector2(hw - inset, -hd + inset), 0.0], [Vector2(-hw + inset, -hd + inset), Vector2(-hw + inset, hd - inset), PI / 2],
		[Vector2(hw - inset, -hd + inset), Vector2(hw - inset, hd - inset), -PI / 2], [Vector2(-hw + inset, hd - inset), Vector2(hw - inset, hd - inset), PI]]
	for sd in sides:
		var a: Vector2 = sd[0]; var b: Vector2 = sd[1]; var L := a.distance_to(b); var n := int(L / (0.8 if small else 1.1))
		for k in range(1, n):
			var p2 := a.lerp(b, float(k) / n); var p := Vector3(p2.x, F.y, p2.y)
			if i == 0 and absf(p.x) < 2.6 and p.z > hd - 3.2: continue
			if _in_stair_grow(p, srects, 0.9): continue
			var bad := false
			for pr in props:
				var big: bool = String(pr.name).contains("table") or String(pr.name).contains("bed") or String(pr.name).contains("dais") or String(pr.name).contains("counter")
				if Vector2(pr.position.x, pr.position.z).distance_to(p2) < ((1.2 if small else 1.6) if big else (0.8 if small else 1.0)): bad = true; break
			if not bad:
				for r in info.rooms: if r.floor == i and Vector2(r.pos.x, r.pos.z).distance_to(p2) < (0.8 if small else 1.3): bad = true; break
			if not bad:
				for pw in parts: if Geometry2D.get_closest_point_to_segment(p2, pw[0], pw[1]).distance_to(p2) < 0.9: bad = true; break
			if not bad and Vector2(info.get("spawn", Vector3(0, 0, 99)).x, info.get("spawn", Vector3(0, 0, 99)).z).distance_to(p2) < 1.5 and i == 0: bad = true
			if not bad: out.append([p, sd[2]])
	return out

static func _in_stair_grow(p: Vector3, srects: Array, g: float) -> bool:
	for s in srects:
		var rel: Vector3 = p - s.base; var along: float = rel.x * s.dir.x + rel.z * s.dir.z
		var lat: float = absf(rel.x * -s.dir.z + rel.z * s.dir.x)
		if along > -g - 1.0 and along < s.run + g and lat < s.w / 2 + g: return true
	return false

static func _decal(fn: Node3D, kind: String, pos: Vector3, size: Vector3, rot: float, floor_decal: bool, side := false) -> void:
	var d := Decal.new(); d.texture_albedo = load(DIR + "tex/p2_decal_%s.png" % kind); d.size = size; d.position = pos
	d.cull_mask = K.LAYER; d.upper_fade = 0.3; d.lower_fade = 0.3; d.distance_fade_enabled = true; d.distance_fade_begin = 25.0; d.distance_fade_length = 8.0
	if floor_decal: d.rotation.y = rot
	else:   # wall decal: project along the facing of the wall spot (spot faces the room, wall is behind it)
		d.basis = Basis(Vector3.UP, rot) * Basis(Vector3.RIGHT, PI / 2)
		d.position = pos - Basis(Vector3.UP, rot).z * 0.4
	fn.add_child(d)

## tall glass wall -> pointed-arch rose window: deep stone surround, tracery, leaded rose glass, 2 crossed light shafts + spot (High)
static func _glasswall(B: Batch, fn: Node3D, p: Vector3, rot: float, w: float, h: float, y0: float, hi: bool, stats: Dictionary, hw := 0.0, hd := 0.0) -> void:
	var fwd := Vector3(sin(rot), 0, cos(rot)); var inward := fwd if fwd.dot(-Vector3(p.x, 0, p.z)) > 0 else -fwd
	var tan := Vector3(cos(rot), 0, -sin(rot)); var face := p
	# the _glasswall prop sits inside the wall: bring the glass out onto the inner wall face
	if absf(inward.z) > 0.5 and hd > 0: face.z = -signf(inward.z) * (hd - WALL_T / 2 - 0.02)
	elif hw > 0: face.x = -signf(inward.x) * (hw - WALL_T / 2 - 0.02)
	var bq := Basis(Vector3.UP, atan2(inward.x, inward.z))
	B.quad(Transform3D(bq, face), w, h, "rose")
	# jambs + sill + stepped pointed arch
	for sx in [-1, 1]:
		B.box(_xf(face + inward * 0.12 + tan * sx * (w / 2 + 0.16), rot), Vector3(0.32, h + 0.2, 0.34), "ashlar_dark")
		if hi: B.box(_xf(face + inward * 0.2 + tan * sx * (w / 2 + 0.36), rot), Vector3(0.14, h + 0.6, 0.18), "ashlar")   # outer column
	B.box(_xf(face + inward * 0.18 + Vector3(0, -h / 2 - 0.1, 0), rot), Vector3(w + 0.8, 0.2, 0.45), "ashlar_dark")
	var segs := 7 if hi else 3
	for k in segs:
		var t := (k + 0.5) / segs; var ang := lerpf(-1.0, 1.0, t)
		var x := ang * (w / 2 + 0.16); var yy := h / 2 + 0.1 + (1.0 - absf(ang)) * 0.75
		B.box(Transform3D(Basis(Vector3.UP, rot) * Basis(Vector3.BACK, -ang * 0.9), face + inward * 0.12 + tan * x + Vector3(0, yy, 0)), Vector3(w / segs + 0.18, 0.3, 0.34), "ashlar_dark")
	if hi:   # tympanum fill above the glass + keystone
		B.box(_xf(face + inward * 0.03 + Vector3(0, h / 2 + 0.4, 0), rot), Vector3(w, 0.6, 0.06), "ashlar")
		B.box(_xf(face + inward * 0.18 + Vector3(0, h / 2 + 0.95, 0), rot), Vector3(0.3, 0.36, 0.4), "ashlar")
		for sx in [-1, 1]: B.box(_xf(face + inward * 0.03 + tan * sx * w / 6, rot), Vector3(0.06, h, 0.06), "ashlar_dark")   # mullions
		B.box(_xf(face + inward * 0.03 + Vector3(0, h / 6, 0), rot), Vector3(w, 0.06, 0.06), "ashlar_dark")
		# light shafts: from the glass down into the room
		var top := face + Vector3(0, 0.0, 0); var land := Vector3(face.x, y0, face.z) + inward * 5.5
		var axis := (land - top); var L := axis.length(); axis /= L
		for k in 2:
			var xa := tan.rotated(axis, k * 1.1)
			var za := xa.cross(axis).normalized()
			B.quad(Transform3D(Basis(xa, axis, za), (top + land) / 2), w * 1.15, L, "shaft")
		var sp := SpotLight3D.new(); sp.position = face + inward * 0.4; sp.light_color = Color(0.95, 0.85, 1.0); sp.light_energy = 4.0
		sp.spot_range = 9.0; sp.spot_angle = 28.0; sp.shadow_enabled = false; sp.light_cull_mask = K.LAYER | 1
		sp.transform = Transform3D(Basis.looking_at(land - sp.position, Vector3.UP), sp.position); fn.add_child(sp)
		stats.lights += 1
	stats["glasswalls"] = stats.get("glasswalls", 0) + 1
