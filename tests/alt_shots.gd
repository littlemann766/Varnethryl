extends Node
## test 16: owner high-altitude flight shots + no-ceiling/no-snap-back smoke test. Run: godot --path . -- --altshots
var m: Node
const OUT := "/workspace/shots/godot16/"
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	await frames(10)
	m.cheats.role_provider = func() -> String: return "owner"
	m.cheats.request("fly", true); m.set_flight(true); await frames(5)
	var fails := 0
	print("FLYCLIPS hero rig has_fly_clips=", m.party.rig.has_fly_clips)
	# flight pose shots near the ground (side camera)
	var sc := Camera3D.new(); sc.fov = 40; m.add_child(sc)
	m.fly_alt = 8.0; m.hero.position = Vector3(200, m.height(200, 420) + 8.0, 420); m.yaw = 0.0
	var poses := [["hover", Vector2.ZERO, 0.0], ["forward", Vector2(0, -1), 0.0], ["bank", Vector2(0.8, -0.6), 0.0], ["ascend", Vector2.ZERO, 1.0], ["descend", Vector2.ZERO, -1.0]]
	var fc0 = m.find_child("FlyControls", true, false)
	for pz in poses:
		m.joy_vec = pz[1]
		if fc0: fc0.hold = pz[2]
		if pz[0] == "descend": m.fly_alt = 40.0; m.hero.position.y += 32.0
		await frames(30 if pz[2] != 0.0 else 70)
		var hp: Vector3 = m.hero.global_position
		var rt: Vector3 = m.hero_vis.global_basis.x
		sc.look_at_from_position(hp + rt * 6.0 + Vector3(0, 1.5, 0), hp + Vector3(0, 1.0, 0), Vector3.UP); sc.current = true
		await frames(3)
		get_viewport().get_texture().get_image().save_png(OUT + "pose_%s.png" % pz[0])
		m.cam.current = true
	m.joy_vec = Vector2.ZERO
	if fc0: fc0.hold = 0.0
	# close-ups: cape straight in flight (default hero) + re-meshed Nyx (fly v2 48fb389 weight pass)
	m.fly_alt = 25.0; await frames(30)
	for hid in ["", "nyx"]:
		if hid != "": m.party.set_hero(hid); await frames(10)
		print("FLYCLIPS %s has_fly_clips=%s" % [hid if hid != "" else "default", m.party.rig.has_fly_clips])
		for pz2 in [["hover", Vector2.ZERO], ["forward", Vector2(0, -1)]]:
			m.joy_vec = pz2[1]; await frames(60)
			Engine.time_scale = 0.0
			var hp3: Vector3 = m.hero.global_position; var bx: Vector3 = m.hero_vis.global_basis.x; var bz: Vector3 = m.hero_vis.global_basis.z
			for side in [["side", bx * 4.5], ["back", bz * 4.5 + bx * 1.5]]:
				sc.look_at_from_position(hp3 + side[1] + Vector3(0, 1.4, 0), hp3 + Vector3(0, 0.9, 0), Vector3.UP); sc.current = true
				await frames(3)
				get_viewport().get_texture().get_image().save_png(OUT + "close_%s_%s_%s.png" % [hid if hid != "" else "aldric", pz2[0], side[0]])
			Engine.time_scale = 1.0
		m.cam.current = true
	m.joy_vec = Vector2.ZERO
	for alt in [500.0, 1500.0, 3000.0]:
		m.fly_alt = alt
		m.hero.position = Vector3(-60, m.height(-60, 260) + alt, 260)
		m.yaw = 0.0; m.pitch = -0.55
		await frames(90)
		var got: float = m.hero.position.y - m.height(m.hero.position.x, m.hero.position.z)
		var ok: bool = absf(got - alt) < alt * 0.05
		if not ok: fails += 1
		var hc := Camera3D.new(); hc.fov = 60; hc.far = m.cam.far; m.add_child(hc)
		var hp2: Vector3 = m.hero.global_position
		hc.look_at_from_position(hp2 + Vector3(0, 6, 14), hp2 + Vector3(0, -alt, -alt * 0.9), Vector3.UP); hc.current = true
		await frames(4)
		get_viewport().get_texture().get_image().save_png(OUT + "alt_%04d_down.png" % int(alt))
		m.cam.current = true; hc.queue_free()
		print("ALT target=%d got=%.0f far=%.0f fog=%.5f %s" % [alt, got, m.cam.far, m.env.fog_density, "OK" if ok else "FAIL"])
		get_viewport().get_texture().get_image().save_png(OUT + "alt_%04d.png" % int(alt))
	# climb with the HUD rate from 3000 m for 2 s: must keep rising (no ceiling)
	var fc = m.find_child("FlyControls", true, false)
	var a0: float = m.fly_alt
	if fc: fc.hold = 1.0
	await frames(60)
	if fc: fc.hold = 0.0
	print("CLIMB from %.0f to %.0f %s" % [a0, m.fly_alt, "OK" if m.fly_alt > a0 + 50.0 else "FAIL"])
	if m.fly_alt <= a0 + 50.0: fails += 1
	# co-owner keeps the 60 m cap
	m.cheats.role_provider = func() -> String: return "coowner"
	print("COOWNER cap=%.0f %s" % [m.cheats.fly_cap(), "OK" if m.cheats.fly_cap() == 60.0 else "FAIL"])
	if m.cheats.fly_cap() != 60.0: fails += 1
	# Lava Wave v3.2 on hilly ground, eye level
	m.cheats.role_provider = func() -> String: return "owner"
	m.set_flight(false); m.spawn_world_boss(false); await frames(10)
	var wb = m.world_boss
	wb.rituals_done = 1; wb._start_ritual(); wb.t_state = 7.5
	await frames(8)
	var b: Vector3 = wb.global_position
	var best := Vector3.ZERO; var bs := -1.0
	for i in 16:   # pick the eye-level spot with the most height variation along the ring
		var a := i * TAU / 16.0; var d := Vector3(cos(a), 0, sin(a))
		var v := absf(m.height(b.x + d.x * 80, b.z + d.z * 80) - m.height(b.x - d.x * 80, b.z - d.z * 80))
		if v > bs: bs = v; best = d
	var ec := Camera3D.new(); ec.fov = 70; ec.far = 3000; m.add_child(ec)
	var p := b + best * 175.0; p.y = m.height(p.x, p.z) + 1.7
	ec.look_at_from_position(p, b + Vector3(0, 15, 0), Vector3.UP); ec.current = true
	await frames(6)
	get_viewport().get_texture().get_image().save_png(OUT + "wave_slope_eye_level.png")
	print("WAVE slope dh=%.1f m gaps=%s" % [bs, wb.wave.gap_angles()])
	print("ALTSHOTS %d failed" % fails)
	get_tree().quit()
