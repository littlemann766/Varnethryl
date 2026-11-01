extends Node
## test 36 (boss phone shot of test 35, galleon flying): hero + companions standing visible on deck while sailing and
## flying, ▲/▼ shown while the ship flies, no Jump on a ship, no Charts while flying / out at open sea; side shot that
## matches the phone view. -- --shipfly   (SHOT_OUT dir)
var m: Node
var sea: TidewrackSea
var npass := 0
var nfail := 0
func ok(c: bool, t: String) -> void:
	if c: npass += 1; print("SF PASS ", t)
	else: nfail += 1; print("SF FAIL ", t)
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func on_deck(n: Node3D) -> bool:
	var l: Vector3 = sea.ship.global_transform.affine_inverse() * n.global_position
	return n.is_visible_in_tree() and absf(l.y - (sea.deck_y())) < 0.35 and absf(l.x) < 4.0 and absf(l.z) < 14.0
func crew_check(when: String) -> void:
	ok(on_deck(m.hero) and m.hero_vis.is_visible_in_tree() and not m.party.rig.swim_on and absf(m.party.rig.position.y) < 0.05, "%s: hero standing visible on deck (swim=%s rig y %.2f)" % [when, m.party.rig.swim_on, m.party.rig.position.y])
	for c in m.party.companions: ok(on_deck(c.node), "%s: %s on deck" % [when, c.id])
	ok(on_deck(m.pip), "%s: Pip on deck" % when)
	# nothing between the camera and the hero's chest (ship hull/rail must not hide him)
	var q := PhysicsRayQueryParameters3D.create(m.cam.global_position, m.hero.global_position + Vector3(0, 1.2, 0), 0xFFFFFFFF)
	q.exclude = [m.hero.get_rid()] + sea.ships.values().map(func(x): return x.get_rid())   # the hull box is an invisible blocker
	var hit: Dictionary = m.get_world_3d().direct_space_state.intersect_ray(q)
	var cl: Vector3 = sea.ship.global_transform.affine_inverse() * m.cam.global_position
	ok(hit.is_empty(), "%s: camera sees the hero (cam ship-local %s, blocked by %s at %s, hero %s)" % [when, str(cl), str(hit.get("collider").name) if hit else "-", str(sea.ship.global_transform.affine_inverse() * hit.position) if hit else "", str(sea.ship.global_transform.affine_inverse() * m.hero.global_position)])
func _run() -> void:
	var out := OS.get_environment("SHOT_OUT") if OS.get_environment("SHOT_OUT") != "" else "/workspace/shots/t37/shipfly/"
	DirAccess.make_dir_recursive_absolute(out)
	while not m.warmed: await get_tree().process_frame
	m._set_time(10.7); m.party.set_hero("owner"); m.party._set_companions(["garruk"])
	var C: Cheats = m.cheats; C.role_provider = func() -> String: return "owner"
	sea = m.sea; sea.save.discovered_ports = ["tidewrack", "gullhaven"]; sea.enter("galleon"); sea.unlock_all = true; await frames(10)
	var an: Vector3 = sea._v3(sea.M.s1.props.gullhaven.anchor)
	var open := an
	for k in 60:
		var q2 := an + Vector3(cos(k * 0.7), 0, sin(k * 0.7)) * (220.0 + k * 10.0)
		if sea.over_water(Vector2(q2.x, q2.z)) and sea.shore_m(Vector2(q2.x, q2.z)) > 120.0: open = q2; break
	sea.ship.position = Vector3(open.x, 0, open.z); sea.ship.speed = 0.0
	for i in 120: sea.ship.throttle = 1.0; sea.drive(Vector2.ZERO, 1.0 / 60.0); await get_tree().physics_frame
	crew_check("sailing")
	var fc: FlyControls = m.fly_controls
	ok(not fc.jump_btn.is_visible_in_tree(), "sailing: no Jump on a ship")
	ok(not sea.ui.charts_b.visible, "open sea: Charts hidden (not near a harbour)")
	C.request("fly", true); m.fly_alt = 40.0
	for i in 400: sea.ship.throttle = 1.0; sea.drive(Vector2.ZERO, 1.0 / 60.0); await get_tree().physics_frame
	ok(sea.ship.alt > 30.0, "ship flying (alt %.1f)" % sea.ship.alt)
	crew_check("flying")
	ok(not m.party.rig.fly_on, "flying ship: hero stands (no flight pose on deck)")
	ok(fc.up_btn.is_visible_in_tree() and fc.down_btn.is_visible_in_tree(), "flying ship: ▲/▼ shown")
	ok(not fc.jump_btn.is_visible_in_tree(), "flying ship: no Jump")
	ok(not sea.ui.charts_b.visible, "flying ship: Charts hidden")
	var a0: float = m.fly_alt; fc.up_btn.button_down.emit(); for i in 30: fc.step(1.0 / 60.0)
	fc.up_btn.button_up.emit(); ok(m.fly_alt > a0, "▲ raises the flying ship's target altitude")
	if OS.get_environment("SF_PROBE") != "":
		var sp: Vector3 = sea.ship.global_position
		for id in RenderingServer.instances_cull_aabb(AABB(sp + Vector3(-20, -sp.y + 0.5, -20), Vector3(40, sp.y - 1.0, 40)), m.get_world_3d().scenario):
			var o = instance_from_id(id)
			if o is Node3D and (o as Node3D).global_position.distance_to(sp) < 200: print("SFP ", o.get_path(), " ", o.get_class(), " at ", (o as Node3D).global_position - sp, " vis=", o.is_visible_in_tree())
	m.yaw = sea.ship.heading + PI * 0.5   # side view like the phone shot
	for i in 60: sea.drive(Vector2.ZERO, 1.0 / 60.0); await get_tree().physics_frame
	if DisplayServer.get_name() != "headless": get_viewport().get_texture().get_image().save_png(out + "galleon_flying_side.png")
	if OS.get_environment("SF_PROBE") != "":
		var vs: Vector2 = get_viewport().get_visible_rect().size; var r := Rect2i(Vector2i(Vector2(430, 440) * vs / Vector2(1024, 576)), Vector2i(Vector2(60, 40) * vs / Vector2(1024, 576)))
		var base := get_viewport().get_texture().get_image().get_region(r)
		var cnt := func(im: Image) -> int:
			var n := 0
			for y in im.get_height():
				for x in im.get_width():
					var c := im.get_pixel(x, y)
					if c.get_luminance() < 0.42 and c.b < 0.5: n += 1
			return n
		var b0: int = cnt.call(base); print("SFB base dark ", b0, " of ", base.get_width() * base.get_height())
		for gi in m.find_children("*", "GeometryInstance3D", true, false):
			if not is_instance_valid(gi): continue
			if (gi as Node3D).global_position.distance_to(sea.ship.global_position) > 400.0 and not sea.is_ancestor_of(gi): continue
			if not is_instance_valid(gi) or not gi.is_visible_in_tree(): continue
			gi.visible = false; await frames(2)
			var im := get_viewport().get_texture().get_image().get_region(r); gi.visible = true
			var n1: int = cnt.call(im)
			if n1 < b0 * 0.5: print("SFB ", gi.get_path(), " dark ", n1)
	m.yaw = sea.ship.heading + PI
	for i in 60: sea.drive(Vector2.ZERO, 1.0 / 60.0); await get_tree().physics_frame
	if DisplayServer.get_name() != "headless": get_viewport().get_texture().get_image().save_png(out + "galleon_flying_behind.png")
	C.request("fly", false)
	sea.ship.position = an + Vector3(40, 0, 0); sea.ship.alt = 0.0; sea.ship.speed = 0.0; await frames(5)
	ok(sea.ui.charts_b.visible, "near Gullhaven harbour on the water: Charts shown")
	print("SF DONE pass=%d fail=%d" % [npass, nfail]); get_tree().quit(0 if nfail == 0 else 1)
