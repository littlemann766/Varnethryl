extends SceneTree
## Test 13: Ashen Titan quest "Stop the volcano from erupting" in the full main scene.
## godot --path . -s res://tests/titan_quest_test.gd   (xvfb)
func _initialize() -> void: _run.call_deferred()
var fails := 0
func ok(c: bool, msg: String) -> void:
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1
func near(a: float, b: float, e: float) -> bool: return absf(a - b) <= e

func _run() -> void:
	var m = load("res://main.tscn").instantiate(); root.add_child(m)
	for i in 40: await process_frame
	var q = m.titan_quest
	ok(q != null, "TitanQuest created")
	if q == null: _end(); return
	var t: VolcanoTitan = q.titan
	var B: Vector3 = q.base; var C := VolcanoTitan.CENTER
	# size: one constant, boss's 28 m
	ok(near(VolcanoTitan.TITAN_SCALE, 1.3362, 1e-6), "TITAN_SCALE 1.3362")
	ok(near(VolcanoTitan.height_m(), 28.0, 0.05), "volcano Titan 28 m (%.2f)" % VolcanoTitan.height_m())
	ok(near(t.rig.scale.x, VolcanoTitan.TITAN_SCALE, 1e-4), "rig scaled by TITAN_SCALE")
	var h := CharacterRig.measure(t.rig.model) * t.rig.scale.x
	ok(near(h, 28.0, 28.0 * 0.06), "measured Titan height %.2f m ~ 28" % h)
	ok(near(VolcanoTitan.REACH_M, 17.0, 0.01), "reach 17 m")
	ok(t.rig.clips.has("intro"), "Lucian's intro clip present")
	ok(t.rig.clips.has("death_pool"), "Lucian's death_pool clip present")
	ok((t.rig.tree.tree_root as AnimationNodeBlendTree).get_node("death_anim").animation == &"death_pool", "pool death uses death_pool")
	ok(near(Vector2(t.position.x - C.x, t.position.z - C.z).length(), 0.0, 0.01), "Titan at the pool centre (0, y, 0)")
	ok(near(rad_to_deg(t.rotation.y), 40.0, 0.5), "yaw 40")
	ok(not t.visible and not t.active and near(t.position.y - B.y, 10.0, 0.01), "hidden at y 10 before the intro")
	# root motion stripped on walk/run
	var a: Animation = t.rig.anim_player.get_animation("walk"); var drift := 0.0
	for k in a.get_track_count():
		if a.track_get_type(k) == Animation.TYPE_POSITION_3D and str(a.track_get_path(k)).ends_with(":root"):
			var v0: Vector3 = a.track_get_key_value(k, 0)
			for j in a.track_get_key_count(k): var v: Vector3 = a.track_get_key_value(k, j); drift = maxf(drift, Vector2(v.x - v0.x, v.z - v0.z).length())
	ok(drift < 1e-4, "walk root XZ motion removed (%.4f)" % drift)
	# stage 1 shown, hazards
	ok(t.lava_mat != null, "lava vein material on the Titan (%s)" % ("shader" if t.lava_hq else "fallback"))
	ok(t.drips.filter(func(d): return d.emitting).size() == 8, "8 drips in stage 1")
	ok(q.stage == 1 and q.stages[0].vis.visible and not q.stages[1].vis.visible, "stage 1 floor shown")
	ok(q.stages[0].haz.collision_layer == q.HAZARD_LAYER and q.stages[1].haz.collision_layer == 0, "stage 1 hazard active only")
	for i in 5: await physics_frame
	ok(q.in_lava(C + Vector3(0, 38.0 - 0.0 + B.y - C.y, 0) + Vector3(2, 0, 2)), "pool is lava (stage 1)")
	# a plate: probe the ring r 10..30 for a walkable spot above y 38.9
	var plate := Vector3.INF
	for r in range(12, 30, 2):
		for k in 16:
			var an := k / 16.0 * TAU; var p := C + Vector3(cos(an) * r, 0, sin(an) * r)
			var y: float = m.ground_y(p.x, p.z)
			if y > B.y + 38.9 and y < B.y + 39.4: plate = Vector3(p.x, y, p.z); break
		if plate != Vector3.INF: break
	ok(plate != Vector3.INF, "a walkable plate at ~39.05 in the arena")
	if plate != Vector3.INF: ok(not q.in_lava(plate), "plate is not lava")
	# quest: giver, then the rim triggers the intro
	m.hero.global_position = q.giver.global_position + Vector3(2, 0.5, 0)
	for i in 5: await physics_frame
	ok(q.state == "active", "giver gives the quest (%s)" % q.state)
	m.hero.global_position = plate + Vector3(0, 0.6, 0) if plate != Vector3.INF else C + Vector3(20, 40.5, 0)
	for i in 3: await physics_frame
	ok(q.state == "intro", "entering the crater starts the intro (%s)" % q.state)
	ok(q.intro_cam != null and q.intro_cam.current, "wide intro camera active")
	await create_timer(1.75).timeout
	var ymid: float = t.position.y - B.y
	ok(near(ymid, 10.0 + 16.8 * 0.5, 0.9), "linear rise: mid-way at 1.75 s (%.1f ~ 18.4)" % ymid)
	await create_timer(2.0).timeout
	ok(near(t.position.y - B.y, 26.8, 0.05), "risen to 26.8 at 3.5 s (%.2f)" % (t.position.y - B.y))
	await create_timer(2.8).timeout
	ok(q.card.visible, "name card shown at the roar")
	await create_timer(3.2).timeout
	ok(q.state == "fight" and q.bar.visible and t.active, "boss bar + fight after the intro (%s)" % q.state)
	ok(m.cam.current, "game camera restored")
	# hurtbox reachable from a plate (r >= 10)
	ok(t.radius >= 6.5, "body hurt radius %.1f lets plate fighters hit him" % t.radius)
	# stage 2
	t.hp = t.max_hp * 0.6
	for i in 3: await physics_frame
	ok(q.stage == 2 and q.stages[1].vis.visible and not q.stages[0].vis.visible, "66%% -> stage 2 floor")
	ok(q.stages[1].haz.collision_layer == q.HAZARD_LAYER and q.stages[0].haz.collision_layer == 0, "stage 2 hazard swapped")
	ok(q.shake_t > 0.0, "stage swap shakes the camera")
	ok(near(t.glow_mats[0].emission_energy_multiplier, 2.2, 0.01), "stage 2 glow 2.2")
	await create_timer(0.15).timeout
	ok(near(t.position.y - B.y, 26.8, 0.05), "sink waits 0.2 s")
	await create_timer(1.8).timeout
	ok(near(t.position.y - B.y, 21.0, 0.05), "sunk to 21.0 (%.2f)" % (t.position.y - B.y))
	ok(q.embers.amount == 24, "more embers in stage 2")
	ok(t.lava_mat != null and near(t.glow_strength, 2.2, 0.05), "lava veins glow 2.2 in stage 2 (%.2f)" % t.glow_strength)
	ok(t.drips.size() == 16 and t.drips.all(func(d): return d.emitting), "all 16 lava drips in stage 2")
	ok(t.chest_light != null, "orange chest light")
	# stage 3
	t.hp = t.max_hp * 0.3
	for i in 3: await physics_frame
	await create_timer(1.9).timeout
	ok(q.stage == 3 and t.stage == 3, "33%% -> stage 3")
	ok(near(t.position.y - B.y, 18.4, 0.05), "sunk to 18.4 (%.2f)" % (t.position.y - B.y))
	ok(near(q.ring.scale.x, 8.0, 0.01), "lava ring scale 8")
	# stage 3 rain spawns telegraphed rocks
	t.cds.rain = 0.0
	for i in 90:   # rain starts once his current attack (if any) finishes
		await physics_frame
		if t.projectiles.size() >= 4: break
	ok(t.projectiles.size() >= 4, "stage 3 rock rain (%d rocks)" % t.projectiles.size())
	# lava hurts
	var c: HeroCombat = m.party.combat; c.hp = c.max_hp
	m.hero.global_position = C + Vector3(3, 38.3 + B.y - C.y, 3)
	await create_timer(0.5).timeout
	ok(q.hazard_hits > 0.0 and c.hp < c.max_hp, "pool lava burns the player")
	c.hp = c.max_hp
	# win
	t.take_damage(int(t.hp) + 1, C)
	for i in 3: await physics_frame
	ok(q.state == "won" and not q.bar.visible, "win completes the quest")
	ok(float(m.lava_mat().get_shader_parameter("glow")) < 0.5, "volcano calms (lava glow down)")
	_end()

func _end() -> void:
	print("TITAN_QUEST %d failed" % fails)
	quit(1 if fails else 0)
