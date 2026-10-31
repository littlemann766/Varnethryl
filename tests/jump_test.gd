extends SceneTree
## Test 13 Jump in the real main scene: ~1.2 m apex, floor-only (no double jump), a running jump clears a 3 m gap.
func _initialize() -> void: _run.call_deferred()
var fails := 0
func ok(c: bool, msg: String) -> void:
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1

func _run() -> void:
	var m = load("res://main.tscn").instantiate(); root.add_child(m)
	for i in 40: await process_frame
	var h: CharacterBody3D = m.hero
	h.global_position = Vector3(0, m.height(0, 30) + 0.5, 30)
	for i in 60: await physics_frame
	ok(h.is_on_floor(), "hero grounded")
	var y0 := h.global_position.y; var top := y0
	m.request_jump()
	for i in 90:
		await physics_frame
		top = maxf(top, h.global_position.y)
		if i == 15: m.request_jump()   # mid-air press
	ok(absf((top - y0) - 1.2) < 0.15, "apex %.2f m ~ 1.2" % (top - y0))
	ok(m.jump_count == 1, "no double jump (%d jumps)" % m.jump_count)
	# running jump: air distance
	for i in 20: await physics_frame
	m.yaw = 0.0; m.joy_vec = Vector2(0, -1)
	for i in 30: await physics_frame
	m.request_jump(); await physics_frame; await physics_frame
	var p0 := h.global_position; var airborne := 0
	while not h.is_on_floor() and airborne < 120: await physics_frame; airborne += 1
	var dist := Vector2(h.global_position.x - p0.x, h.global_position.z - p0.z).length()
	m.joy_vec = Vector2.ZERO
	ok(dist >= 3.0, "running jump covers %.2f m (clears 2-3 m gaps)" % dist)
	print("JUMP %d failed" % fails); quit(1 if fails else 0)
