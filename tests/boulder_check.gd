extends Node
## test 23 (Beth terrain fix 2 adds 376 boulder cylinder colliders): find colliders that could block the player.
## Run: VARN_LITE=1 godot --headless --path . -- --bouldercheck   -> /workspace/shots/godot23/boulder_check.txt
## Checks per collider: the game's own placement rules (main._ok_spot: avenues, gate paths, ring road, streets,
## door spurs, buildings, walls, tree/rock blockers, outskirt roads +8 m) with the cylinder radius + hero clearance;
## every building / filler / extra door within 8 m; volcano quest pad (240 m of VOLC); lighthouse + harbour;
## the Titan's outskirts loop (info: he is not a physics body). Then a capsule sweep along every outskirt road.
var m: Node
const HERO_R := 0.45
func _ready() -> void: m = get_parent(); _run.call_deferred()
func _run() -> void:
	for i in 5: await get_tree().physics_frame
	var lines := []; var block := []
	var bc: Node = TerrainScatter.root.get_node_or_null("BoulderCollision") if TerrainScatter.root else null
	if bc == null: print("BOULDERCHECK no colliders"); get_tree().quit(1); return
	var doors := []
	for b in m.buildings + m.extra_doors: doors.append([String(b.get("name", b.id)), m.interiors.door_world(b)])
	var n := 0
	for cs in bc.get_children():
		if not (cs is CollisionShape3D): continue
		n += 1
		var p: Vector3 = (cs as Node3D).global_position; var r: float = (cs.shape as CylinderShape3D).radius if cs.shape is CylinderShape3D else 1.0
		var p2 := Vector2(p.x, p.z); var why := []
		if not m._ok_spot(p2, r + HERO_R): why.append("placement rules (road/street/spur/gate/building/blocker)")
		for d in doors:
			if Vector2(d[1].x, d[1].z).distance_to(p2) < r + 8.0: why.append("door " + d[0])
		if p2.distance_to(m.VOLC) < 240.0: why.append("volcano pad")
		if why.size(): block.append(cs); lines.append("BLOCK %s r=%.2f at (%.1f, %.1f): %s" % [cs.name, r, p.x, p.z, ", ".join(why)])
	# capsule sweep along the outskirt roads (centre line, 1 m steps)
	var space := (m as Node3D).get_world_3d().direct_space_state
	var q := PhysicsShapeQueryParameters3D.new(); var cap := CapsuleShape3D.new(); cap.radius = HERO_R; cap.height = 1.9; q.shape = cap
	var road_hits := {}
	for rd in m.ROADS:
		for i in range(1, rd.size()):
			var a := Vector2(rd[i-1][0], rd[i-1][1]); var b := Vector2(rd[i][0], rd[i][1])
			var L := a.distance_to(b)
			for k in int(L):
				var s := a.lerp(b, k / L)
				for off: float in [-2.0, 0.0, 2.0]:
					var nrm: Vector2 = (b - a).normalized().orthogonal() * off; var w: Vector2 = s + nrm
					q.transform = Transform3D(Basis(), Vector3(w.x, m.height(w.x, w.y) + 1.1, w.y))
					for h in space.intersect_shape(q, 8):
						if h.collider == bc: road_hits[h.shape] = Vector2(w.x, w.y)
	for si in road_hits:
		var cs: Node = bc.get_child(si) if si < bc.get_child_count() else null
		lines.append("ROADSWEEP hit shape %d (%s) at %s" % [si, cs.name if cs else "?", road_hits[si]])
		if cs and not block.has(cs): block.append(cs)
	var fix := OS.get_environment("BC_LIST_ONLY") == ""
	lines.append("BOULDERCHECK colliders=%d blockers=%d road_sweep_hits=%d" % [n, block.size(), road_hits.size()])
	print("\n".join(lines))
	DirAccess.make_dir_recursive_absolute("/workspace/shots/godot23")
	FileAccess.open("/workspace/shots/godot23/boulder_check.txt", FileAccess.WRITE).store_string("\n".join(lines) + "\n")
	get_tree().quit(0)
