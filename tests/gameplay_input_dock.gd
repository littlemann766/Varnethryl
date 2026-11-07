extends SceneTree
## Play-mode input and dock regressions.
## Space jumps and does not basic-attack. J basic-attacks and does not jump.
## The moored-galleon boarding spot is on the quay, above the waterline, and shows Set sail.
## godot --headless --path . -s res://tests/gameplay_input_dock.gd
func _initialize() -> void: _run.call_deferred()
var fails := 0
func ok(c: bool, msg: String) -> void:
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1

func _collision(m, h: CharacterBody3D) -> void:
	var solid_grass := 0
	for g in m.grass_chunks:
		if g.find_children("*", "CollisionObject3D", true, false).size() > 0: solid_grass += 1
	ok(m.grass_chunks.size() > 0 and solid_grass == 0, "grass is not a solid barrier (%d chunks)" % m.grass_chunks.size())
	h.global_position = Vector3(0, m.height(0, 16) + 0.4, 16)
	h.velocity = Vector3.ZERO
	m.yaw = 0.0
	m.joy_vec = Vector2(0, -1)
	for i in 120: await physics_frame
	m.joy_vec = Vector2.ZERO
	ok(h.global_position.z > 6.5, "fountain basin stops a walk (z %.2f)" % h.global_position.z)
	var trunk_from := Transform3D(Basis(), Vector3(-150, m.height(-150, 158) + 0.2, 155))
	ok(h.test_move(trunk_from, Vector3(0, 0, 4)), "showcase tree trunk blocks a straight step")
	h.global_position = Vector3(40, m.height(40, -168) + 0.4, -168)
	h.velocity = Vector3.ZERO
	m.yaw = 0.0
	m.joy_vec = Vector2(0, -1)
	for i in 160: await physics_frame
	m.joy_vec = Vector2.ZERO
	ok(h.global_position.z > -184.5 and h.global_position.z < -175.0, "city wall stops a walk (z %.2f)" % h.global_position.z)
	var cx := -428.0
	var cz := 392.0
	h.global_position = Vector3(cx, m.height(cx, cz) + 0.4, cz)
	h.velocity = Vector3.ZERO
	m.yaw = PI / 2.0
	m.joy_vec = Vector2(0, -1)
	var ymin := h.global_position.y
	for i in 80:
		await physics_frame
		ymin = minf(ymin, h.global_position.y)
	m.joy_vec = Vector2.ZERO
	var gy: float = m.height(h.global_position.x, h.global_position.z)
	ok(ymin > -1.0 and h.global_position.y > gy - 0.6 and h.global_position.y < gy + 2.5, "coast walk stays on the heightmap (y %.2f ground %.2f min %.2f)" % [h.global_position.y, gy, ymin])
	m.set_flight(true)
	m.set_flight(false)
	ok(h.collision_mask == 1 and not m.noclip_allowed(), "fly on/off keeps collision")
	m._teleport(Vector3(-6, 0, 30), 0.0)
	ok(h.collision_mask == 1, "teleport keeps collision")
	h.collision_mask = 0
	await physics_frame
	ok(h.collision_mask == 1, "mask is restored when noclip is off")
	m.cheats.role_provider = func(): return "owner"
	ok(m.cheats.request("noclip", true) and h.collision_mask == 0 and m.noclip_allowed(), "owner plus noclip toggle disables collision")
	h.global_position = Vector3(0, m.height(0, 16) + 0.4, 16)
	h.velocity = Vector3.ZERO
	m.yaw = 0.0
	m.joy_vec = Vector2(0, -1)
	for i in 140: await physics_frame
	m.joy_vec = Vector2.ZERO
	ok(h.global_position.z < 6.0, "noclip crosses the fountain (z %.2f)" % h.global_position.z)
	ok(m.cheats.request("noclip", false) and h.collision_mask == 1 and not m.noclip_allowed(), "noclip off restores collision")
	m.cheats.role_provider = func(): return ""
	m.cheats.flags.noclip = true
	await physics_frame
	ok(h.collision_mask == 1 and not m.noclip_allowed(), "noclip flag without a cheat role does not clip")
	m.cheats.flags.noclip = false

func _key(code: Key, pressed: bool) -> void:
	var ev := InputEventKey.new()
	ev.keycode = code
	ev.physical_keycode = code
	ev.pressed = pressed
	Input.parse_input_event(ev)
	Input.flush_buffered_events()

func _run() -> void:
	var m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in 40: await process_frame
	var ui = root.get_node("VUI")
	ui._enter("solo")
	for i in 10: await physics_frame
	var h: CharacterBody3D = m.hero
	h.global_position = Vector3(0, m.height(0, 30) + 0.5, 30)
	for i in 40: await physics_frame
	ok(h.is_on_floor() and not m._input_blocked(), "in play and grounded")
	await _collision(m, h)
	h.global_position = Vector3(0, m.height(0, 30) + 0.5, 30)
	h.velocity = Vector3.ZERO
	for i in 25: await physics_frame
	var uses := [0]
	m.party.combat.used.connect(func(slot, _sk): if slot == 0: uses[0] += 1)
	var jumps0: int = m.jump_count
	_key(KEY_SPACE, true)
	for i in 8: await physics_frame
	ok(m.jump_count == jumps0 + 1, "space jumps once (%d -> %d)" % [jumps0, m.jump_count])
	ok(uses[0] == 0, "space does not basic-attack (uses %d)" % uses[0])
	_key(KEY_SPACE, false)
	for i in 50: await physics_frame
	var held: int = m.jump_count
	_key(KEY_SPACE, true)
	for i in 3: await physics_frame
	_key(KEY_SPACE, false)
	ok(m.jump_count == held + 1, "a second space press jumps once")
	for i in 50: await physics_frame
	ok(h.is_on_floor(), "landed after the jumps")
	var jumps1: int = m.jump_count
	var uses1: int = uses[0]
	_key(KEY_J, true)
	for i in 4: await physics_frame
	_key(KEY_J, false)
	ok(uses[0] == uses1 + 1, "J basic-attacks")
	ok(m.jump_count == jumps1, "J does not jump")
	var g: Array = m._galleon_pier()
	var spot: Vector3 = g[0]
	ok(spot.y > 0.4 and spot.y < 3.0, "boarding spot is on the quay, not the sea floor (y %.2f)" % spot.y)
	var ship: Node3D = m.ships[0][0]
	var horiz := Vector2(spot.x - ship.global_position.x, spot.z - ship.global_position.z).length()
	ok(horiz < 14.0, "boarding spot is beside the galleon (%.1f m)" % horiz)
	# Disembark places the hero on the spot itself (leave_to_harbour). _teleport snaps to the
	# height field, which is the sea floor under this quay, so it is not the boarding path.
	h.global_position = spot
	h.velocity = Vector3.ZERO
	m.yaw = g[1]
	for i in 20: await physics_frame
	ok(h.is_on_floor() and h.global_position.y > 0.4, "hero stands on the quay (y %.2f floor %s)" % [h.global_position.y, h.is_on_floor()])
	ok(m.sea.ui.prompt.visible and m.sea.ui.prompt.text == "Set sail", "Set sail prompt at the quay spot")
	print("INPUT_DOCK %d failed" % fails)
	quit(1 if fails else 0)
