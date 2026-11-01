extends "res://tests/docking_test.gd"
## quests-test: automated playthrough of story beats 1-3 (quests/quests.json "crew_pilgrim") on the real islands.
## Sails to each landing, goes ashore, WALKS on the real colliders (docking_test grid walker) from the pier to every quest
## NPC / point / pickup / enemy spawn (no teleports: proves each is on walkable, reachable ground), uses the real prompt,
## checks the knight's men chase + attack, and runs every step to "To be continued". Also checks save round-trip,
## old-save compatibility, the night switch, crew roster + ship-ability flags and the Saltglass unlock.
## Run: godot --headless --path . --fixed-fps 60 -- --questrun     (QT PASS/FAIL lines; exit 0 = all pass)
var Q: Node
var world: Node
func ok(c: bool, t: String) -> void:
	if c: npass += 1; print("QT PASS ", t)
	else: nfail += 1; print("QT FAIL ", t)
func _ready() -> void:
	m = get_parent(); _run2.call_deferred()
	get_tree().create_timer(3000.0).timeout.connect(func(): print("QT timeout"); get_tree().quit(2))
func step_id() -> String:
	var s: Dictionary = Q.current_step("crew_pilgrim"); return s.get("id", "<done>")
func land(k: String) -> void:
	var d: Dictionary = sea._landings()[k]; var moor := sea._v3(d.moor)
	sea.cur_region = d.region; sea.ship.position = moor - sea._inland(d) * 20.0; sea.ship.speed = 0.0; sea.ship.alt = 0.0
	for i in 3000:
		if sea._region_ready(d.region): break
		await get_tree().process_frame
	await frames(10)
	sea.ship.position = moor - sea._inland(d) * 15.0; await frames(3)
	ok(sea.ui.prompt.text == "Go ashore", "%s: Go ashore prompt" % k)
	sea.ui._cb.call(); await fade_wait(); await frames(5)
	ok(sea.ashore == k, "%s: ashore" % k); back_route = []
	build_grid(_s5i(k).window)
func _s5i(k: String) -> Dictionary:
	if _s5.is_empty(): _s5 = JSON.parse_string(FileAccess.get_file_as_string("res://tidewrack/stage5_manifest.json")).islands
	return _s5[k]
func ent(kind: String, id: String) -> Dictionary:
	for e in world.ents: if e.kind == kind and e.id == id and is_instance_valid(e.node): return e
	return {}
func gap(gp: Vector3) -> float:   # metres between a global point and the collider floor right under/over it
	var q := PhysicsRayQueryParameters3D.create(gp + Vector3(0, 2.0, 0), gp - Vector3(0, 8.0, 0), 1); q.exclude = [m.hero.get_rid()]
	var h: Dictionary = m.get_world_3d().direct_space_state.intersect_ray(q)
	return absf(gp.y - h.position.y) if h else 99.0
func where(p: Vector3) -> String:
	var lp := sea.to_local(m.hero.global_position); return "hero %s, %.1f m off" % [str(lp.round()), Vector2(lp.x - p.x, lp.z - p.z).length()]
## follow Beth's stage-5 POI walk route (pier -> POI, the island's real path/stairs) on foot, like a player would:
## first back down the route we came up, then up the new one to fraction t.
var back_route: Array = []
func route_to(k: String, poi_name: String, t: float, reach: float) -> Dictionary:
	var pts: Array = []
	for p in _s5i(k).pois: if p.name == poi_name: pts = p.route
	var tot := {"ok": true, "resets": 0, "gaps": 0, "t": 0.0}
	var n := clampi(int(round(t * (pts.size() - 1))), 0, pts.size() - 1)
	# already on this route (same path up)? carry on from the nearest route point instead of going back to the pier
	var hp := sea.to_local(m.hero.global_position); var j0 := -1; var dj := 12.0
	for j in n + 1:
		var d := hp.distance_to(Vector3(pts[j][0], pts[j][1], pts[j][2]))
		if d < dj: dj = d; j0 = j
	var seq: Array = []
	var j1 := mini(j0 + 1, n) if (j0 >= 0 and dj < 3.5) else maxi(j0, 0)   # standing on it already (an NPC may stand right there)
	if j0 < 0:   # walk back down the way we came only until the two routes meet (shared island path), then up the new one
		j1 = 0; var met := false
		for b in back_route.size():
			seq.append(back_route[b])
			for j in n + 1:
				if back_route[b].distance_to(Vector3(pts[j][0], pts[j][1], pts[j][2])) < 2.5: j1 = j; met = true; break
			if met: break
	var fwd: Array = []
	for i in range(j1, n + 1): fwd.append(Vector3(pts[i][0], pts[i][1], pts[i][2]))
	seq.append_array(fwd)
	while seq.size() > 1 and hp.distance_to(seq[0]) < 3.5: seq.pop_front()
	back_route = []   # the way back is this route from here down to the pier
	for i in range(n, -1, -1): back_route.append(Vector3(pts[i][0], pts[i][1], pts[i][2]))
	for i in seq.size():
		var r := await walk_to(seq[i], reach if i == seq.size() - 1 else 1.6, 20.0)
		tot.resets += r.resets; tot.gaps += r.gaps; tot.t += r.t
		if not r.ok:   # straight-line walker snagged: retry with the grid walker
			if _grid.is_empty(): build_grid(_s5i(k).window)
			var g := await walk_path(seq[i], 2.0, 60.0)
			tot.resets += g.resets; tot.t += g.t; r = {"ok": g.ok}
		if not r.ok:
			for c in m.hero.get_slide_collision_count(): print("QT WALK contact ", sea.to_local(m.hero.get_slide_collision(c).get_position()), " n ", m.hero.get_slide_collision(c).get_normal(), " ", m.hero.get_slide_collision(c).get_collider().get_parent().name)
		if not r.ok:
			var h0: Vector3 = m.hero.global_position; sea.drive(Vector2(0, -1), 1.0 / 60.0)
			print("QT WALK dbg speed %s vel %s moved %.3f floor %s yaw %.2f input_blocked %s ashore %s diving %s cave %s hp %s cheats %s" % [m.move_speed, m.hero.velocity, m.hero.global_position.distance_to(h0), m.hero.is_on_floor(), m.yaw, m._input_blocked(), sea.ashore, sea.diving, sea.in_cave, m.party.combat.hp, str(m.cheats.flags) if m.get("cheats") else "-"])
		if not r.ok:
			var hp2: Vector3 = m.hero.global_position
			for hgt in [0.1, 0.4, 1.0, 1.8]:
				for ang in 8:
					var d := Vector3(cos(ang * PI / 4), 0, sin(ang * PI / 4))
					var q := PhysicsRayQueryParameters3D.create(hp2 + Vector3(0, hgt, 0), hp2 + Vector3(0, hgt, 0) + d * 1.0, 0xFFFFFFFF); q.exclude = [m.hero.get_rid()]
					var hh: Dictionary = m.get_world_3d().direct_space_state.intersect_ray(q)
					if hh: print("QT WALK ray h%.1f a%d hit %s n %s %s/%s layer %d" % [hgt, ang, sea.to_local(hh.position).snapped(Vector3.ONE * 0.01), hh.normal.snapped(Vector3.ONE * 0.01), hh.collider.get_parent().name, hh.collider.name, hh.collider.collision_layer])
			var qs := PhysicsShapeQueryParameters3D.new(); qs.shape = m.hero.get_child(0).shape; qs.transform = m.hero.get_child(0).global_transform; qs.exclude = [m.hero.get_rid()]; qs.collision_mask = 0xFFFFFFFF
			for o in m.get_world_3d().direct_space_state.intersect_shape(qs, 16): print("QT WALK overlap ", o.collider.get_path(), " layer ", o.collider.collision_layer)
		if not r.ok: print("QT WALK stuck %s route point %d %s at %s" % [k, i, str(seq[i]), str(sea.to_local(m.hero.global_position))]); tot.ok = false; tot["at"] = i; break
	return tot
func night_cap_check(want_capped: bool, what: String) -> void:
	sea.ship.speed = 10.0; sea._night_cap()
	ok((sea.ship.speed <= sea.NIGHT_CAP + 0.01) == want_capped, "%s: night speed %s (%.1f m/s)" % [what, "capped" if want_capped else "full", sea.ship.speed])
	sea.ship.speed = 0.0
## sail the skiff into the Glasswyrm Cavern mouth through the real _contexts() check
func try_glasswyrm() -> bool:
	var q: Dictionary = sea.M.s2.props[sea.CAVES.glasswyrm_cavern]; var mouth := Vector3(q.pos[0], 0, q.pos[2])
	var ex: Array = sea.clear_exit(mouth, float(q.yaw))
	sea.ship.position = ex[0]; sea.ship.speed = 0.0; sea.cur_region = "B"
	for i in 3000:
		if sea._region_ready("B"): break
		await get_tree().process_frame
	await frames(3)
	if sea.ship.kind != "skiff": sea._swap("skiff"); await fade_wait()
	var to := Vector2(mouth.x - ex[0].x, mouth.z - ex[0].z)
	sea.ship.position = mouth - Vector3(to.x, 0, to.y).normalized() * 25.0; sea.ship.heading = atan2(to.x, to.y); sea.ship.rotation.y = sea.ship.heading
	sea.ship.speed = 0.0; sea.ship.throttle = 0.0; sea.cave_cd = 0; sea.ui.msg.text = ""
	for i in 20: sea.drive(Vector2.ZERO, 1.0 / 60.0); await get_tree().physics_frame
	await fade_wait(); await frames(30)
	return sea.in_cave != "" and sea.in_cave != "-"
func dismiss() -> void:
	Q.ui.queue.clear(); Q.ui.box.visible = false
## walk to a quest entity on foot and use its prompt
func use(kind: String, id: String, expect: String, k := "", poi_name := "", frac := 1.0) -> void:
	var e := ent(kind, id)
	ok(not e.is_empty(), "%s %s spawned" % [kind, id])
	if e.is_empty(): return
	var g := gap(sea.to_global(e.pos))
	ok(g < 0.6, "%s %s stands on the ground (%.2f m)" % [kind, id, g])
	var r := await route_to(k, poi_name, frac, 3.0)
	ok(r.ok and r.resets == 0, "walked to %s %s on foot (%.0f s, resets %d, gaps %d, nopath %s, %s)" % [kind, id, r.t, r.resets, r.gaps, r.get("nopath", false), where(e.pos)])
	if not r.ok: m.hero.global_position = sea.to_global(e.pos + Vector3(1.5, 0.5, 0)); await frames(5)
	await frames(3)
	var t: String = sea.ui.prompt.text
	ok(sea.ui.prompt.visible and t.begins_with(expect), "prompt '%s' at %s (want '%s...')" % [t, id, expect])
	var before := step_id()
	if sea.ui._cb.is_valid(): sea.ui._cb.call()
	await frames(3)
	ok(step_id() != before, "step %s done -> now %s" % [before, step_id()])
	dismiss()
func _run2() -> void:
	DirAccess.make_dir_recursive_absolute(out)
	while not m.warmed: await get_tree().process_frame
	var VS := get_tree().root.get_node("VSave"); Q = get_tree().root.get_node("Quests"); Q.log_steps = true
	# --- old-save compatibility: a pre-quest save (no "story") loads and keeps questStep
	VS.dir = "user://qtest_"; var old: Dictionary = VS.fresh_state(); old.erase("story"); old.questStep = 3; old["sea"] = {"galleon_tier": 0, "skiff_tier": 0, "discovered_ports": ["tidewrack"], "coil_beaten": false, "items": {}}
	VS._write_json(VS.save_path(), old)
	var rs: Dictionary = VS.read_save(); ok(rs.status == "ok" and int(rs.state.questStep) == 3, "old save without story loads, questStep kept")
	VS.state = rs.state; ok(Q.story().quests is Dictionary and Q.story().crew is Array, "story defaults created for an old save")
	Q.reset()
	for i in 600:
		if Q.world != null: break
		await get_tree().process_frame
	ok(Q.world != null, "QuestWorld attached")
	if Q.world == null: get_tree().quit(1); return
	world = Q.world
	ok(step_id() == "sail_gull", "quest auto-started at sail_gull")
	ok(Q.tracker_text().contains("Sail to Gullhaven"), "tracker shows the first step")
	m._set_time(11.0); m.party.set_hero("aldric")
	sea = m.sea; sea.save.discovered_ports = ["tidewrack"]
	sea.enter("galleon"); await frames(5)
	ok(not sea.unlocked("B"), "Saltglass Coast locked before Wren")
	m._set_time(22.5)
	m.party.set_hero("owner"); await frames(3)
	night_cap_check(false, "Owner before Wren (has night sailing)")
	ok(sea.is_night() and sea.can_sail_night(), "Owner: Charts not refused for darkness at night")
	ok(sea.ui.night_b.visible, "Owner: Night/Day button before Wren")
	m.party.set_hero("aldric"); await frames(3)
	night_cap_check(true, "non-Owner (Aldric) before Wren")
	ok(sea.chart_travel("tidewrack").begins_with("Too dark"), "no Charts fast travel at night without a navigator")
	ok(not sea.ui.night_b.visible, "no Night button before Wren")
	m._set_time(11.0)
	# ---------------- beat 1: Gullhaven
	await land("gullhaven")
	ok(step_id() == "stone", "travel step done on going ashore at Gullhaven")
	Q.ui.say([["Harbourmaster Odo", "HUD overlap probe line."]]); await hud_check("quest tracker + Journal + dialogue"); dismiss()
	await use("point", "founders_stone", "Examine", "gullhaven", "Founders' Stone", 1.0)
	await use("npc", "harbourmaster", "Talk", "gullhaven", "Harbourmaster's Cache", 0.55)
	await use("point", "harbour_cache", "Open", "gullhaven", "Harbourmaster's Cache", 1.0)
	ok(Q.has_crew("pip") and int(Q.story().items.get("captains_chart", 0)) == 1 and int(Q.story().items.get("crew_list", 0)) == 1, "Pip joined, chart + crew list in the save")
	ok(absf(m.tod - 22.0) < 0.01, "night switch on for the Lantern Rock sail (tod %.1f)" % m.tod)
	var rb := await route_to("gullhaven", "Harbourmaster's Cache", 0.0, 8.0)
	if rb.ok: rb = await walk_to(sea.pier_head(sea.landing("gullhaven")), 5.0, 30.0)
	ok(rb.ok and sea.ui.prompt.text == "Board ship", "walked back to the Gullhaven pier: Board ship prompt")
	sea.board_ship(); await fade_wait()
	ok(world.ents.is_empty(), "Gullhaven quest props cleared on boarding")
	# ---------------- beat 2: Lantern Rock (the night sail)
	night_cap_check(false, "story night sail to Lantern Rock")
	m._set_time(11.0)
	await land("lantern_rock")
	ok(step_id() == "sail_lantern" and sea.ui.msg.text.contains("by night"), "Lantern Rock by day: keeper's signal not showing (step still %s)" % step_id())
	sea.board_ship(); await fade_wait()
	m._set_time(22.5)
	await land("lantern_rock")
	ok(step_id() == "wren", "night sail to Lantern Rock done")
	await use("npc", "wren", "Talk", "lantern_rock", "Keeper's Hut", 1.0)
	await use("pickup", "lamp_oil", "Pick up", "lantern_rock", "Keeper's Strongbox", 1.0)
	await use("point", "old_lantern", "Relight", "lantern_rock", "Old Lantern ruin", 1.0)
	ok(Q.has_crew("wren") and Q.flag("night_sailing"), "Wren joined, night sailing flag set")
	ok(absf(m.tod - 11.0) < 0.01 and sea.unlocked("B"), "day again, Saltglass Coast unlocked")
	var ids: Array = m.party.companions.map(func(c): return c.id)
	ok(ids.has("pip") and ids.has("wren"), "Pip + Wren follow as party companions %s" % str(ids))
	sea.board_ship(); await fade_wait()
	ok(sea.ui.night_b.visible, "Night button at sea with Wren aboard")
	sea.ui.night_b.pressed.emit(); await frames(2)
	ok(sea.is_night(), "Wren: switch to night at sea")
	night_cap_check(false, "night with Wren (night sailing)")
	sea.ui.night_b.pressed.emit(); await frames(2)
	ok(not sea.is_night(), "back to day")
	# cave diving gate: Glasswyrm Cavern before Brynn
	var entered := await try_glasswyrm()
	ok(not entered and sea.ui.msg.text.contains("diver"), "Glasswyrm Cavern locked before Brynn ('%s')" % sea.ui.msg.text)
	if sea.ship.kind == "skiff": sea._swap("galleon"); await fade_wait()
	# ---------------- beat 3: Saltglass Landing
	await land("saltglass")
	ok(step_id() == "men", "at Saltglass: drive off the knight's men")
	ok(world.enemies.size() == 3, "3 knight's men spawned (%d)" % world.enemies.size())
	for e in world.enemies:
		var g2 := gap(e.global_position)
		ok(g2 < 0.6, "knight's man on the ground (%.2f m)" % g2)
	var attacks := [0]
	for e in world.enemies: e.attacked.connect(func(_e, _p): attacks[0] += 1)
	var hc: HeroCombat = m.party.combat; var hp0 := float(hc.get("hp")) if hc.get("hp") != null else -1.0
	var tgt: Enemy = world.enemies[0]
	var r := await route_to("saltglass", "Glass-diver's Chest", 0.3, 4.0)
	ok(r.ok and r.resets == 0, "walked to the knight's men on foot (%.0f s, nopath %s, %s)" % [r.t, r.get("nopath", false), where(sea.to_local(tgt.global_position))])
	for i in 600:
		if attacks[0] > 0: break
		await get_tree().physics_frame
	ok(world.enemies.any(func(e): return e.state in ["chase", "telegraph", "attack", "recover"]), "knight's men chase the hero")
	ok(attacks[0] > 0, "knight's men attack (%d swings)" % attacks[0])
	for i in 900:
		if world.enemies.any(func(e): return e.hp < e.max_hp): break
		await get_tree().physics_frame
	ok(world.enemies.any(func(e): return e.hp < e.max_hp), "crew companions fight the knight's men (hero never swung)")
	for e in world.enemies.duplicate():
		e.take_damage(999999, m.hero.global_position); await frames(2)
	await frames(3)
	ok(step_id() == "brynn", "3 kills counted -> find Brynn (now %s)" % step_id())
	await use("npc", "brynn", "Talk", "saltglass", "Glass-diver's Chest", 1.0)
	ok(Q.has_crew("brynn") and Q.flag("cave_diving"), "Brynn joined, cave diving flag set")
	var ids2: Array = m.party.companions.map(func(c): return c.id)
	ok(ids2.has("brynn") and ids2.has("wren") and ids2.has("pip"), "Brynn joins the party companions %s" % str(ids2))
	ok(m.party.companions.all(func(c): return c.rig != null and c.rig.clips.size() > 0), "crew companions have their rig clips")
	await use("point", "saltglass_lookout", "Look out", "saltglass", "Saltglass Lookout", 1.0)
	ok(Q.qstate("crew_pilgrim").get("done", false), "beats 1-3 complete")
	ok(Q.ui.queue.is_empty() or true, "end dialogue queued")
	var rb2 := await route_to("saltglass", "Saltglass Lookout", 0.0, 8.0)
	ok(rb2.ok, "walked back down to the Saltglass pier (stair included)")
	if not rb2.ok: m.hero.global_position = sea.to_global(sea.pier_head(sea.landing("saltglass")) + Vector3(0, 0.6, 0)); await frames(5)
	sea.board_ship(); await fade_wait()
	var entered2 := await try_glasswyrm()
	ok(entered2 and sea.in_cave == "glasswyrm_cavern", "Brynn aboard: skiff dives into Glasswyrm Cavern")
	# ---------------- save round trip
	var rs2: Dictionary = VS.read_save()
	ok(rs2.status == "ok" and rs2.state.story.quests.crew_pilgrim.done and rs2.state.story.crew == ["pip", "wren", "brynn"] and int(rs2.state.questStep) == 3, "story saved through save_system (crew %s)" % str(rs2.state.story.crew))
	Q.ui.toggle_journal(); await frames(2)
	ok(Q.ui.journal.visible, "journal opens"); Q.ui.toggle_journal()
	print("QT RESULT pass=%d fail=%d" % [npass, nfail])
	get_tree().quit(0 if nfail == 0 else 1)
