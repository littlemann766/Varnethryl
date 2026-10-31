extends SceneTree
## Headless: godot --headless --path . -s res://tests/test_companions.gd
## Companions: in-game height vs characters/index.json, ground/shoulder follow position, never on the camera line,
## big enemies never spawn on the player.
var n := 0
var fails := 0
func ok(c: bool, what: String) -> void:
	n += 1
	if not c: fails += 1
	print(("ok   " if c else "FAIL ") + what)

func _initialize() -> void:
	_run.call_deferred()
	create_timer(240.0).timeout.connect(func(): print("TIMEOUT"); quit(2))

func _run() -> void:
	var VS = root.get_node("VSave")
	DirAccess.make_dir_recursive_absolute("user://test_comp/"); VS.dir = "user://test_comp/"
	VS.state = VS.sanitize_party(VS.fresh_state())
	var main = load("res://main.tscn").instantiate(); root.add_child(main)
	for i in 10: await process_frame
	var P = main.party
	P.set_hero("owner")
	main._teleport(Vector3(-6, 0, 60), 0.0)
	var idx: Dictionary = CharacterRig.index().characters
	for set in [["pip", "phoenix"], ["wren", "garruk"], ["selene", "rook"]]:
		P._set_companions(set)
		for i in 5: await physics_frame
		for c in P.companions:
			var r: CharacterRig = c.rig
			var want: float = float(idx[c.id].height_m)
			var h: float = CharacterRig.measure(r) * r.global_transform.basis.get_scale().y
			ok(absf(h - want) <= 0.06 * want, "%s in-game height %.3f m vs index %.3f m" % [c.id, h, want])
			ok((r.applied_scale == 1.0 or r.voxel) and is_equal_approx(c.node.global_transform.basis.get_scale().y, 1.0), "%s: no extra scale on top of Beth's armature root" % c.id)
		# walk 3 s, stop 1.5 s, then check follow positions
		main.joy_vec = Vector2(0, -1)
		for i in 180: await physics_frame
		main.joy_vec = Vector2.ZERO
		for i in 90: await physics_frame
		await process_frame
		var hp: Vector3 = main.hero.global_position
		var cp: Vector3 = main.cam.global_position
		for c in P.companions:
			var p: Vector3 = c.node.global_position
			var dy := p.y - hp.y
			if P.FLYERS.has(c.id): ok(dy > 1.0 and dy < 1.8, "%s (flyer) hovers at shoulder height: +%.2f m" % [c.id, dy])
			else: ok(absf(dy) < 0.3, "%s walks at ground level: dy=%.2f m (not over the head)" % [c.id, dy])
			var flat := Vector2(p.x - hp.x, p.z - hp.z).length()
			ok(flat > 0.6 and flat < 5.0, "%s follows at %.2f m" % [c.id, flat])
			# distance from the camera->hero line (horizontal)
			var head := hp + Vector3(0, main.cam_h, 0); var ab := head - cp
			var t := clampf((p - cp).dot(ab) / ab.length_squared(), 0.0, 1.0)
			var q := cp + ab * t
			var off := Vector2(p.x - q.x, p.z - q.z).length()
			var hidden := false
			for mi in c.rig.find_children("*", "GeometryInstance3D", true, false): hidden = hidden or mi.transparency > 0.5
			ok(off > 0.5 or hidden, "%s is not blocking the camera (%.2f m off the line, faded=%s)" % [c.id, off, hidden])
	# big creatures never spawn on the player
	for tid in ["titan", "frosttroll_a", "wolf"]:
		var e = P.director.spawn(tid, main.hero.global_position + Vector3(0.5, 0, 0.5), main.hero)
		var d := Vector2(e.global_position.x - main.hero.global_position.x, e.global_position.z - main.hero.global_position.z).length()
		ok(d >= float(e.radius) + 4.9, "%s spawned %.1f m away (radius %.1f)" % [tid, d, e.radius])
	print("RESULT %d/%d passed" % [n - fails, n])
	quit(1 if fails else 0)
