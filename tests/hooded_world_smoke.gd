extends SceneTree
## Production main.tscn smoke on the normal gameplay path.
## Software Vulkan Forward Mobile when lavapipe is the only device. Not a phone and not a frame-rate claim.
const OUT := "/cursor/stores/self/transfer/test62-hooded/world"
const SHOTS := ["world_walk", "world_attack", "world_death", "world_transition", "world_field_cards", "world_relaunch"]
var card_focus := Vector3.ZERO

func _initialize() -> void: _run.call_deferred()

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	print("SMOKE_RENDER method=%s current=%s device=%s" % [
		ProjectSettings.get_setting("rendering/renderer/rendering_method"),
		RenderingServer.get_current_rendering_method(),
		RenderingServer.get_video_adapter_name()])
	print("SMOKE_IMPORT glb=%s atlas=%s" % [
		ResourceLoader.exists(HordeZombie.HOODED_GLB),
		ResourceLoader.exists("res://assets/hooded_candidate/far_impostor/impostor_atlas_8dir_1024.png")])
	var m = load("res://main.tscn").instantiate()
	root.add_child(m)
	await _wait_warm(m, "boot")
	_hide_title()
	_quiet_guards(m)
	if m.party and m.party.combat: m.party.combat.set_process(false)
	var crowd: HordeCrowd = m.horde.crowd
	var card_ok := true
	var card_n := 0
	for mi in crowd._meshes:
		card_n += 1
		if not ((mi as MultiMeshInstance3D).multimesh.mesh is QuadMesh): card_ok = false
	print("SMOKE_CARDS batches=%d quad=%s rendered=%d sim=%d" % [card_n, card_ok, crowd.rendered_n, crowd.alive_n])
	# Flat ground south of the wall, looking north, clear of the gate trolls.
	var hx := 8.0
	var hz := 210.0
	await _place_hero(m, hx, hz, 0.0, -0.2, 4.4, 42.0)
	crowd.set_physics_process(false)
	crowd.set_process(false)
	var idx := _free(crowd)
	var body := _promote_at(m, crowd, idx, hx + 1.8, hz - 3.2)
	var hood := body.get_node_or_null("Hooded") as HoodedPresenter
	print("SMOKE_NEAR hooded=%s parent=%s glb=%s clip=%s" % [
		hood != null, body.get_parent().name if body.get_parent() else "none",
		ResourceLoader.exists(HordeZombie.HOODED_GLB), hood.clip if hood else "none"])
	body.set_physics_process(false)
	body.crowd_lock = 40.0
	for _i in 10:
		_revive(m)
		body.hp = body.max_hp
		if hood: hood._saw_hp = body.hp
		var slide := hx + 2.6 - float(_i) * 0.07
		var sz := hz - 2.4
		body.global_position = Vector3(slide, m.height(slide, sz), sz)
		await process_frame
	if hood:
		print("SMOKE_MESH hood_pos=%s mats=%d" % [hood.global_position, hood._fade_mats.size()])
	print("SMOKE_WALK clip=%s state=%s dist=%.2f hp=%.0f pos=%s visible=%s" % [
		hood.clip if hood else "none", body.state, _flat(body.global_position, m.hero.global_position),
		m.party.combat.hp, body.global_position, body.visible])
	await _aim_shot(body.global_position + Vector3(0, 1.05, 0), Vector3(2.3, 1.35, 3.1), "world_walk")
	body.set_physics_process(true)
	var reached := false
	var t0 := Time.get_ticks_msec()
	while float(Time.get_ticks_msec() - t0) / 1000.0 < 6.0:
		_revive(m)
		body.hp = body.max_hp
		if hood and hood.clip == "hit": hood._saw_hp = body.hp
		var ax := hx + 1.35
		var az := hz - 0.55
		body.global_position = Vector3(ax, m.height(ax, az), az)
		body.crowd_lock = 0.0
		if body.state != "windup" and body.state != "recover":
			body.state = "approach"
		await process_frame
		if hood and hood.clip == "attack2" and hood.anim and hood.anim.current_animation_position >= 0.55:
			reached = true
			break
	var apos := hood.anim.current_animation_position if hood and hood.anim else -1.0
	print("SMOKE_ATTACK clip=%s state=%s anim=%.2f reached=%s dist=%.2f hp=%.0f" % [
		hood.clip if hood else "none", body.state, apos, reached, _flat(body.global_position, m.hero.global_position), m.party.combat.hp])
	await _aim_shot(body.global_position + Vector3(0, 1.05, 0), Vector3(2.0, 1.2, 2.4), "world_attack")
	# Open grass south of the wall. Freeze the crowd so the posed card is not promoted
	# (bodies take over inside 26 m) and does not walk off. The mesh sits in the
	# 8–14 m dither band; the card is past 14 m from the camera and past 26 m from the hero.
	body.set_physics_process(false)
	m.horde.set_physics_process(false)
	var tx := hx
	var tz := hz + 25.0
	body.global_position = Vector3(tx, m.height(tx, tz), tz)
	body.crowd_lock = 40.0
	body.state = "approach"
	var card_i := _park_card(crowd, hx + 2.8, tz + 6.0)
	var focus_t := body.global_position + Vector3(0, 1.05, 0)
	var eye_t := Vector3(-2.4, 1.55, -11.0)
	var eye := focus_t + eye_t
	var card_p := Vector3(crowd.px[card_i] if card_i >= 0 else 0.0, focus_t.y, crowd.pz[card_i] if card_i >= 0 else 0.0)
	crowd._draw(m.hero.global_position)
	print("SMOKE_TRANSITION mesh_cam=%.1f card_cam=%.1f hero_card=%.1f clip=%s card_i=%d card=(%.1f, %.1f) hp=%.0f" % [
		body.global_position.distance_to(eye), card_p.distance_to(eye),
		_flat(card_p, m.hero.global_position), hood.clip if hood else "none", card_i,
		card_p.x, card_p.z, m.party.combat.hp])
	await _aim_shot(focus_t, eye_t, "world_transition", 36.0)
	var dx := hx + 1.45
	var dz := hz - 1.6
	body.global_position = Vector3(dx, m.height(dx, dz), dz)
	await _place_hero(m, hx, hz, 0.2, -0.24, 4.0, 36.0)
	body.kill_now(Vector3.ZERO)
	t0 = Time.get_ticks_msec()
	var dpos := -1.0
	while float(Time.get_ticks_msec() - t0) / 1000.0 < 1.8:
		_revive(m)
		await process_frame
		if hood and hood.anim and hood.clip == "death":
			dpos = hood.anim.current_animation_position
			if dpos >= 0.75: break
	if hood and hood.anim and hood.anim.has_animation("death"):
		var dlen: float = hood.anim.get_animation("death").length
		hood.anim.play("death")
		hood.anim.seek(dlen * 0.82, true)
		hood.clip = "death"
		dpos = hood.anim.current_animation_position
		print("SMOKE_DEATH_LEN %.2f" % dlen)
	print("SMOKE_DEATH state=%s clip=%s anim=%.2f visible=%s alive=%s hp=%.0f" % [
		body.state, hood.clip if hood else "none", dpos, body.visible, body.alive(), m.party.combat.hp])
	await _aim_shot(body.global_position + Vector3(0, 0.55, 0), Vector3(2.4, 1.5, 2.8), "world_death")
	var parked := PackedInt32Array()
	var used: Array = []
	var row_z := hz + 36.0
	for k in 3:
		var pi := _park_card(crowd, hx - 4.0 + float(k) * 4.0, row_z, used)
		if pi >= 0: used.append(pi)
		parked.append(pi)
	crowd._draw(m.hero.global_position)
	var aim := "parked=%s" % [parked]
	print("SMOKE_FIELD rendered=%d sim=%d inside=%d %s" % [crowd.rendered_n, crowd.alive_n, crowd.inside_count(), aim])
	var card_y: float = m.height(hx, row_z)
	await _aim_shot(Vector3(hx, card_y + 1.05, row_z), Vector3(0.0, 1.7, -15.0), "world_field_cards", 32.0)
	var save = root.get_node("VSave")
	var sdir := "user://hooded_world_smoke"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(sdir))
	save.dir = sdir
	save.state = save.fresh_state()
	var snap := {"x": 18.5, "z": 40.0, "yaw": 0.4, "zone": "village", "hero": int(save.state.get("active", 0)), "at_sea": false, "at_interior": false}
	var wrote: bool = save.write_snapshot(snap)
	save.state = save.load_state()
	var preview: Dictionary = save.resume_place(save.state)
	print("SMOKE_SAVE wrote=%s resume=%s" % [wrote, preview])
	m.queue_free()
	for _i in 4: await process_frame
	var m2 = load("res://main.tscn").instantiate()
	root.add_child(m2)
	for _i in 6: await process_frame
	m2._on_play_solo()
	var place := Vector2(m2.hero.global_position.x, m2.hero.global_position.z)
	print("SMOKE_RELAUNCH pos=(%.2f, %.2f) yaw=%.2f" % [place.x, place.y, m2.yaw])
	await _wait_warm(m2, "relaunch")
	_hide_title()
	_quiet_guards(m2)
	var hood2 := 0
	if m2.horde and m2.horde.crowd:
		for z in m2.horde.crowd.pool:
			if z.get_node_or_null("Hooded") is HoodedPresenter: hood2 += 1
		var quad2 := true
		for mi2 in m2.horde.crowd._meshes:
			if not ((mi2 as MultiMeshInstance3D).multimesh.mesh is QuadMesh): quad2 = false
		print("SMOKE_RELAUNCH hooded_bodies=%d cards=%s alive=%d rendered=%d" % [hood2, quad2, m2.horde.crowd.alive_n, m2.horde.crowd.rendered_n])
	var rx: float = m2.hero.global_position.x
	var rz: float = m2.hero.global_position.z
	var ground_y: float = m2.height(rx, rz)
	print("SMOKE_RELAUNCH_GROUND y=%.2f hero_y=%.2f" % [ground_y, m2.hero.global_position.y])
	# Town trees swallow a shoulder-height camera. Sit above the canopy and look down at the saved spot.
	await _aim_shot(Vector3(rx, ground_y + 1.2, rz), Vector3(7.0, 16.0, 14.0), "world_relaunch")
	_contact()
	m2.queue_free()
	for _i in 6: await process_frame
	print("SMOKE_DONE")
	quit(0)

func _wait_warm(m, tag: String) -> void:
	var t0 := Time.get_ticks_msec()
	var next := 0
	while not m.warmed and float(Time.get_ticks_msec() - t0) < 600000.0:
		await process_frame
		var s := int((Time.get_ticks_msec() - t0) / 1000)
		if s >= next:
			print("SMOKE_WARM %s %ds" % [tag, s])
			next = s + 30
	print("SMOKE_WARMED %s ok=%s ms=%d" % [tag, m.warmed, Time.get_ticks_msec() - t0])

func _place_hero(m, x: float, z: float, yaw: float, pitch: float, spring: float, fov: float) -> void:
	_revive(m)
	m.hero.global_position = Vector3(x, m.height(x, z), z)
	m.yaw = yaw
	m.pitch = pitch
	m.cam_arm.spring_length = spring
	m.cam.fov = fov
	for _i in 3: await process_frame

func _promote_at(m, crowd: HordeCrowd, idx: int, x: float, z: float) -> HordeZombie:
	crowd.px[idx] = x
	crowd.pz[idx] = z
	crowd.hold_x[idx] = x
	crowd.hold_z[idx] = z
	crowd.hp[idx] = 190.0
	crowd.lock_t[idx] = 30.0
	crowd.wind_t[idx] = 0.0
	var promoted: bool = crowd._promote_index(idx, m.hero.global_position)
	var body: HordeZombie = crowd.pool[crowd.pool_i[idx]]
	body.global_position = Vector3(x, m.height(x, z), z)
	body.crowd_lock = 40.0
	body.state = "approach"
	body.t_state = 0.0
	print("SMOKE_PROMOTE %s id=%d" % [promoted, int(crowd.id[idx])])
	return body

func _park_card(crowd: HordeCrowd, x: float, z: float, used: Array = []) -> int:
	if crowd.on_sea(x, z): return -1
	for i in crowd.id.size():
		if used.has(i): continue
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		crowd.px[i] = x
		crowd.pz[i] = z
		crowd.hold_x[i] = x
		crowd.hold_z[i] = z
		return i
	return -1

func _aim_card(m, crowd: HordeCrowd) -> String:
	var hx: float = m.hero.global_position.x
	var hz: float = m.hero.global_position.z
	var best := -1
	var best_d := 80.0
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		var d := Vector2(crowd.px[i] - hx, crowd.pz[i] - hz).length()
		if d < 30.0 or d > best_d: continue
		if crowd.on_sea(crowd.px[i], crowd.pz[i]): continue
		best = i
		best_d = d
	if best < 0:
		best = _park_card(crowd, hx, hz - 34.0)
		if best < 0: return "none"
		best_d = 34.0
	var cx := crowd.px[best]
	var cz := crowd.pz[best]
	var dir := Vector2(cx - hx, cz - hz)
	if dir.length() < 0.1: dir = Vector2(0, -1)
	dir = dir.normalized()
	var stand := Vector2(cx, cz) - dir * 32.0
	var yaw := atan2(-dir.x, -dir.y)
	await _place_hero(m, stand.x, stand.y, yaw, -0.08, 3.4, 16.0)
	card_focus = Vector3(cx, m.height(cx, cz), cz)
	var cam_d: float = m.cam.global_position.distance_to(Vector3(cx, m.height(cx, cz) + 1.0, cz))
	return "card_id=%d at=(%.1f, %.1f) hero_dist=%.1f cam_dist=%.1f rendered=%d" % [
		int(crowd.id[best]), cx, cz, Vector2(cx - m.hero.global_position.x, cz - m.hero.global_position.z).length(), cam_d, crowd.rendered_n]

func _revive(m) -> void:
	var c = m.party.combat
	if c == null: return
	if c.hp <= 0.0 and c.rig: c.rig.set_dead(false)
	c.hp = c.max_hp

func _hide_title() -> void:
	var ui := root.get_node_or_null("VUI")
	if ui and ui.get("title") and ui.title: ui.title.hide()
	if ui and ui.get("hud") and ui.hud: ui.hud.visible = true

func _quiet_guards(m) -> void:
	if m.get("guards") == null or m.guards == null: return
	for g in m.guards.guards:
		g.down_t = 999.0
		g.tgt = null

func _free(crowd: HordeCrowd) -> int:
	for i in crowd.id.size():
		if (crowd.flags[i] & 1) == 0 or (crowd.flags[i] & 2) != 0: continue
		return i
	return 0

func _flat(a: Vector3, b: Vector3) -> float:
	return Vector2(a.x - b.x, a.z - b.z).length()

func _shot(cam: Camera3D, name: String) -> void:
	if cam: cam.current = true
	await process_frame
	await RenderingServer.frame_post_draw
	var img := cam.get_viewport().get_texture().get_image()
	var path := "%s/%s.png" % [OUT, name]
	img.save_png(path)
	print("SHOT %s %dx%d" % [path, img.get_width(), img.get_height()])

## The follow camera sits behind the hero, so a body in front is hidden by the hero or the wall.
## This aims the same production camera at a world point after the game updates it.
func _aim_shot(focus: Vector3, eye_offset: Vector3, name: String, fov: float = 42.0) -> void:
	var cam := Camera3D.new()
	cam.fov = fov
	cam.current = true
	root.add_child(cam)
	var eye := focus + eye_offset
	cam.global_position = eye
	cam.look_at(focus)
	var aim := func():
		cam.current = true
		cam.global_position = eye
		cam.look_at(focus)
	RenderingServer.frame_pre_draw.connect(aim, CONNECT_ONE_SHOT)
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	var path := "%s/%s.png" % [OUT, name]
	img.save_png(path)
	print("SHOT %s %dx%d eye=%s focus=%s" % [path, img.get_width(), img.get_height(), eye, focus])
	cam.queue_free()

func _contact() -> void:
	var cell_w := 480
	var cell_h := 270
	var sheet := Image.create(cell_w * 3, cell_h * 2, false, Image.FORMAT_RGBA8)
	sheet.fill(Color(0.05, 0.05, 0.05))
	for i in SHOTS.size():
		var img := Image.load_from_file("%s/%s.png" % [OUT, SHOTS[i]])
		if img == null: continue
		img.convert(Image.FORMAT_RGBA8)
		img.resize(cell_w, cell_h, Image.INTERPOLATE_LANCZOS)
		sheet.blit_rect(img, Rect2i(0, 0, cell_w, cell_h), Vector2i((i % 3) * cell_w, int(i / 3) * cell_h))
	var path := "%s/contact_sheet.png" % OUT
	sheet.save_png(path)
	print("SHOT %s %dx%d" % [path, sheet.get_width(), sheet.get_height()])
