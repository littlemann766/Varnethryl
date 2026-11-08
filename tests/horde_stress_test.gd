extends SceneTree
## Desktop stress for the bounded horde. Not a phone result.
## godot --headless --path . -s res://tests/horde_stress_test.gd
var fails := 0

func ok(c: bool, msg: String) -> void:
	print(("PASS " if c else "FAIL ") + msg)
	if not c: fails += 1

func _initialize() -> void: _run.call_deferred()

func _run() -> void:
	OS.set_environment("VARN_LITE", "1")
	await process_frame
	var ps: PackedScene = load("res://main.tscn")
	var m = ps.instantiate()
	root.add_child(m)
	if m.cheats:
		m.cheats.flags.god = false
		m.cheats.flags.bump = false
	for _i in 30: await physics_frame
	var mem0 := int(Performance.get_monitor(Performance.MEMORY_STATIC))
	var nodes0 := _nodes(m)
	var alive_max: int = m.horde.alive_count()
	var corpse_max := 0
	var list_max: int = m.party.director.enemies.size()
	var inside_max := 0
	var horde_nodes_max := 0
	var tick_sum := 0
	var tick_n := 0
	var tick_max := 0
	var wall0 := Time.get_ticks_usec()
	var mem_series: Array = []
	# Fill to the hard cap, then run a sustained stretch and a death wave.
	var filled: int = m.horde.debug_fill(HordeDirector.HARD_CAP)
	ok(filled <= HordeDirector.HARD_CAP and filled >= HordeDirector.CAP, "fill stays within the hard cap (%d)" % filled)
	var horde0 := _horde_nodes(m)
	for sec in 12:
		var t0 := Time.get_ticks_usec()
		for _i in 60: await physics_frame
		var dt := int(Time.get_ticks_usec() - t0)
		tick_sum += dt
		tick_n += 1
		tick_max = maxi(tick_max, dt)
		alive_max = maxi(alive_max, m.horde.alive_count())
		corpse_max = maxi(corpse_max, m.horde.corpse_count())
		list_max = maxi(list_max, m.party.director.enemies.size())
		horde_nodes_max = maxi(horde_nodes_max, _horde_nodes(m))
		var mem_now := int(Performance.get_monitor(Performance.MEMORY_STATIC))
		mem_series.append(mem_now)
		print("STRESS_SEC %d mem=%d alive=%d corpses=%d list=%d horde_nodes=%d frame_ms=%.2f" % [sec + 1, mem_now, m.horde.alive_count(), m.horde.corpse_count(), m.party.director.enemies.size(), _horde_nodes(m), float(dt) / 60.0 / 1000.0])
		var inside := 0
		for e in m.party.director.enemies:
			if e is HordeZombie and e.alive() and TownHaven.body_inside(Vector2(e.global_position.x, e.global_position.z), e.radius):
				inside += 1
		inside_max = maxi(inside_max, inside)
	# Kill a wave and confirm corpses cannot pile up.
	var killed := 0
	for e in m.party.director.enemies.duplicate():
		if e is HordeZombie and e.alive() and killed < 10:
			e.kill_now(Vector3.ZERO)
			killed += 1
	for _i in 10: await physics_frame
	corpse_max = maxi(corpse_max, m.horde.corpse_count())
	list_max = maxi(list_max, m.party.director.enemies.size())
	var mem1 := int(Performance.get_monitor(Performance.MEMORY_STATIC))
	var nodes1 := _nodes(m)
	var wall_ms := float(Time.get_ticks_usec() - wall0) / 1000.0
	var mean_frame_ms := float(tick_sum) / float(maxi(tick_n, 1)) / 60.0 / 1000.0
	var max_frame_ms := float(tick_max) / 60.0 / 1000.0
	var growth := mem1 - mem0
	var tail := int(mem_series[mem_series.size() - 1]) - int(mem_series[3]) if mem_series.size() >= 8 else growth
	print("STRESS_DESKTOP seconds=%d wall_ms=%.0f mean_frame_ms=%.2f max_frame_ms=%.2f alive_max=%d corpse_max=%d list_max=%d inside_max=%d scene_nodes %d->%d horde_nodes %d->%d static_mem %d->%d growth=%d tail_growth=%d" % [
		tick_n, wall_ms, mean_frame_ms, max_frame_ms, alive_max, corpse_max, list_max, inside_max, nodes0, nodes1, horde0, horde_nodes_max, mem0, mem1, growth, tail])
	ok(alive_max <= HordeDirector.HARD_CAP, "alive never passed the hard cap")
	ok(corpse_max <= HordeDirector.CORPSE_CAP, "corpses stayed capped (%d)" % corpse_max)
	ok(list_max <= HordeDirector.HARD_CAP + HordeDirector.CORPSE_CAP + 16, "enemy list stayed bounded (%d)" % list_max)
	ok(inside_max == 0, "stress crowd never entered the town")
	ok(horde_nodes_max <= horde0 + 80, "horde node count stayed with the cap (%d -> %d)" % [horde0, horde_nodes_max])
	# After the first 4 s, further static-memory growth on this desktop run. Not a phone budget.
	ok(tail < 48 * 1024 * 1024, "static memory growth after 4s was %d bytes" % tail)
	var ev := {
		"e": "stress_desktop", "mean_frame_ms": mean_frame_ms, "max_frame_ms": max_frame_ms,
		"alive_max": alive_max, "corpse_max": corpse_max, "list_max": list_max, "inside_max": inside_max,
		"nodes0": nodes0, "nodes1": nodes1, "horde_nodes": horde0, "horde_nodes_max": horde_nodes_max,
		"mem0": mem0, "mem1": mem1, "growth": growth, "tail_growth": tail, "series": mem_series,
		"note": "Desktop headless Godot 4.7, lite town, 24 undead. Not a phone measurement.",
	}
	TownHaven.note(ev)
	DirAccess.make_dir_recursive_absolute("/opt/cursor/artifacts")
	TownHaven.write_evidence("/opt/cursor/artifacts/horde_stress_evidence.json")
	print("HORDE_STRESS %s" % ("PASS" if fails == 0 else "FAIL"))
	quit(1 if fails else 0)

func _nodes(n: Node) -> int:
	var c := 1
	for ch in n.get_children(): c += _nodes(ch)
	return c

func _horde_nodes(m) -> int:
	var c := 0
	for e in m.party.director.enemies:
		if e is HordeZombie and is_instance_valid(e): c += _nodes(e)
	return c
