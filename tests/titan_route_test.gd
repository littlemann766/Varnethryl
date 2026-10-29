extends Node
## test 23: simulate the Ashen Titan's outskirts walk for 600 s (one loop is ~2.8 km = ~9 min at 5.2 m/s) (steering only, 30 Hz) and assert he visits every
## waypoint (within 30 m), never enters the town (|x|,|z| >= 260), and never orbits (net loop progress).
## Writes a top-down trace to /workspace/shots/godot23/titan_path.png.
## Run: WB_SCRIPT=res://tests/titan_route_test.gd godot --headless --path . tests/wb_lite.tscn
func _ready() -> void: _go.call_deferred()
func _go() -> void:
	var h := get_parent(); h.spawn_world_boss(false)
	var wb: WorldBoss = h.world_boss; wb.set_process(false)
	var n := wb.waypoints.size(); var seen := {}; var trace: Array[Vector2] = []; var town := 0
	var dt := 1.0 / 30.0; var T := float(OS.get_environment("TR_SECS")) if OS.get_environment("TR_SECS") != "" else 600.0
	var laps := 0; var last_wp := wb.wp
	for i in int(T / dt):
		wb.state = "walk"; wb._walk(dt)
		if wb.wp != last_wp: if wb.wp == 0: laps += 1
		last_wp = wb.wp
		var p := Vector2(wb.position.x, wb.position.z); trace.append(p)
		if maxf(absf(p.x), absf(p.y)) < 259.0: town += 1
		for k in n:
			if p.distance_to(Vector2(wb.waypoints[k].x, wb.waypoints[k].z)) < 30.0: seen[k] = true
	var path_len := 0.0
	for i in range(1, trace.size()): path_len += trace[i].distance_to(trace[i-1])
	var loop_len := 0.0
	for k in n: loop_len += wb.waypoints[k].distance_to(wb.waypoints[(k+1) % n])
	# image
	var S := 512; var img := Image.create(S, S, false, Image.FORMAT_RGB8); img.fill(Color(0.1, 0.12, 0.1))
	var f := func(v: Vector2) -> Vector2i: return Vector2i(int((v.x + 900) / 1800.0 * S), int((v.y + 900) / 1800.0 * S))
	for x in range(f.call(Vector2(-260,-260)).x, f.call(Vector2(260,260)).x): for y in range(f.call(Vector2(-260,-260)).y, f.call(Vector2(260,260)).y): img.set_pixelv(Vector2i(x, y), Color(0.35, 0.2, 0.2))
	for p in trace: var q: Vector2i = f.call(p); if q.x >= 0 and q.y >= 0 and q.x < S and q.y < S: img.set_pixelv(q, Color(1, 0.8, 0.2))
	for k in n:
		var q: Vector2i = f.call(Vector2(wb.waypoints[k].x, wb.waypoints[k].z)); var c := Color(0.2, 1, 0.3) if seen.has(k) else Color(1, 0, 0)
		for dx in range(-2, 3): for dy in range(-2, 3): img.set_pixel(clampi(q.x+dx,0,S-1), clampi(q.y+dy,0,S-1), c)
	DirAccess.make_dir_recursive_absolute("/workspace/shots/godot23"); img.save_png("/workspace/shots/godot23/titan_path.png")
	var ok := seen.size() == n and town == 0 and path_len > loop_len
	print("TITANROUTE secs=%d waypoints=%d visited=%d town_frames=%d path=%.0f m loop=%.0f m laps=%d -> %s" % [T, n, seen.size(), town, path_len, loop_len, laps, "PASS" if ok else "FAIL"])
	get_tree().quit(0 if ok else 1)
