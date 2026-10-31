extends Node
## test 34: find a landing spot (shore point on walkable collider + moor point in open water) for every port and island
## with content in the Tidewrack Sea. Writes res://tidewrack/landings.json. Run: -- --landgen
var m: Node
var sea: TidewrackSea
const T := [["gullhaven", "Gullhaven", "A", "s1", "gullhaven", "anchor"], ["lantern_rock", "Lantern Rock", "A", "s1", "lantern_rock", "pos"],
	["saltwatch_keep", "Saltwatch Keep", "A", "s1", "saltwatch_keep", "pos"], ["coil_isle", "Coil Isle", "A", "s1", "coil_arena", "pos"],
	["saltglass", "Saltglass Landing", "B", "s2", "saltglass_landing", "anchor"], ["beached_wreck", "Beached Wreck", "B", "s2", "beached_wreck", "pos"],
	["frostreach", "Frostreach Ice Dock", "frost", "s4", "frostreach_ice_dock", "anchor"], ["frozen_wreck", "Frozen Wreck", "frost", "s4", "frozen_wreck", "pos"],
	["aurora_arch", "Aurora Arch", "frost", "s4", "aurora_arch", "pos"], ["vent", "Vent Harbour", "ash", "s4", "vent_harbour", "anchor"],
	["ember_wreck", "Ember Wreck", "ash", "s4", "ember_wreck", "pos"], ["hot_spring", "Hot Spring Grotto", "ash", "s4", "hot_spring_grotto", "pos"],
	["obsidian_arch", "Obsidian Arch", "ash", "s4", "obsidian_arch", "pos"]]
func _ready() -> void: m = get_parent(); _run.call_deferred()
func hit(x: float, z: float) -> Dictionary:
	var w := sea.to_global(Vector3(x, 150, z)); var q := PhysicsRayQueryParameters3D.create(w, w - Vector3(0, 220, 0), 1)
	var h: Dictionary = m.get_world_3d().direct_space_state.intersect_ray(q)
	if h.is_empty(): return {}
	return {"y": sea.to_local(h.position).y, "n": h.normal}
func walk_ok(p: Vector2, d: Vector2, y0: float) -> bool:
	var y := y0
	for k in range(1, 25):
		var h := hit(p.x + d.x * k, p.y + d.y * k)
		if h.is_empty() or h.n.y < 0.6 or absf(h.y - y) > 0.7 or h.y < 0.3: return false
		var a := sea.to_global(Vector3(p.x + d.x * (k - 1), y + 1.0, p.y + d.y * (k - 1))); var b := sea.to_global(Vector3(p.x + d.x * k, h.y + 1.0, p.y + d.y * k))
		for side in [-0.5, 0.0, 0.5]:   # no wall / house across the 1 m wide path
			var o: Vector3 = Vector3(-d.y, 0, d.x) * side
			if not m.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(a + o, b + o, 1)).is_empty(): return false
		y = h.y
	return true
func _run() -> void:
	while not m.warmed: await get_tree().process_frame
	sea = m.sea; sea.enter("galleon"); sea.unlock_all = true
	var out := {}
	var only := OS.get_environment("LG_ONLY")
	if only != "": out = JSON.parse_string(FileAccess.get_file_as_string("res://tidewrack/landings.json"))
	for t in T:
		if only != "" and not (t[0] in only.split(",")): continue
		var c: Vector3 = sea._v3(sea.M[t[3]].props[t[4]][t[5]])
		sea.cur_region = t[2]; sea.ship.position = Vector3(c.x, 0, c.z); sea.ship.speed = 0.0
		for i in 2000:
			sea._stream(Vector2(c.x, c.z))
			if sea.regions.get(t[2], {}).get("state", 0) == 2: break
			await get_tree().process_frame
		for i in 5: await get_tree().physics_frame
		var best := {}; var bs := 1e9
		var nl := 0; var nh := 0
		for r in range(0, 260, 10):
			for a in 36:
				var L0 := Vector2(c.x, c.z) + Vector2(cos(a * TAU / 36.0), sin(a * TAU / 36.0)) * r
				if sea.shore_m(L0) <= 1.0:
					nl += 1
					if not hit(L0.x, L0.y).is_empty(): nh += 1
		print("LGDBG ", t[0], " state=", sea.regions.get(t[2], {}).get("state", 0), " land=", nl, " hits=", nh, " shore_c=", sea.shore_m(Vector2(c.x, c.z)))
		for r in range(0, 260, 5):
			for a in range(0, 36 if r > 0 else 1):
				var ang := a * TAU / 36.0; var L := Vector2(c.x, c.z) + Vector2(cos(ang), sin(ang)) * r
				if sea.shore_m(L) > 1.0: continue
				var h := hit(L.x, L.y)
				if h.is_empty() or h.n.y < 0.85 or h.y < 0.4 or h.y > 30.0: continue
				# nearest open water (galleon-safe) in 16 directions
				for b in 16:
					var d := Vector2(cos(b * TAU / 16.0), sin(b * TAU / 16.0))
					for s in range(4, 70, 2):
						var W := L + d * s
						if sea.shore_m(W) >= 14.0:
							var ok_pier := true
							for u in range(2, s, 2):   # pier corridor: no high rock between shore and water
								var hh := hit(L.x + d.x * u, L.y + d.y * u)
								if not hh.is_empty() and hh.y > h.y + 1.5: ok_pier = false; break
							if ok_pier and walk_ok(L, -d, h.y):
								var sc := s + 0.25 * r
								if sc < bs: bs = sc; best = {"id": t[0], "name": t[1], "region": t[2], "shore": [L.x, h.y, L.y], "moor": [W.x, 0.0, W.y], "pier_m": s, "from_content_m": r, "inland": [-d.x, -d.y]}
							break
			if bs < r * 0.25 + 4.0: break
		if best.is_empty(): print("LG NONE ", t[0])
		else: out[t[0]] = best; print("LG ", JSON.stringify(best))
	var f := FileAccess.open("res://tidewrack/landings.json", FileAccess.WRITE); f.store_string(JSON.stringify(out, " ")); f.close()
	print("LG DONE ", out.size()); get_tree().quit(0)
