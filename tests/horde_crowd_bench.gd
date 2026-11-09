extends SceneTree
## Desktop scale harness for the crowd sim. Headless. Not a phone and not a rendered frame.
## godot --headless --path . -s res://tests/horde_crowd_bench.gd
func _initialize() -> void: _run.call_deferred()

func _run() -> void:
	OS.set_environment("VARN_LITE", "1")
	OS.set_environment("VARN_NO_FLOWERS", "1")
	OS.set_environment("VARN_NO_HORDE", "1")
	OS.set_environment("VARN_NO_HORDE_REFILL", "1")
	await process_frame
	var m = load("res://main.tscn").instantiate()
	root.add_child(m)
	if m.cheats:
		m.cheats.flags.god = false
		m.cheats.flags.bump = false
	for _i in 8: await physics_frame
	var host: Node = m
	var cohorts := [256, 1000, 2000, 4000]
	print("BENCH platform=desktop-headless godot=%s sim_max=%d near_cap=%d render_cap=%d" % [Engine.get_version_info().string, HordeCrowd.SIM_MAX, HordeCrowd.NEAR_CAP, HordeCrowd.RENDER_CAP])
	for n in cohorts:
		var crowd := HordeCrowd.new()
		var dir := HordeDirector.new()
		dir.main = host
		dir.name = "BenchHorde"
		host.add_child(dir)
		dir.add_child(crowd)
		crowd.director = dir
		var mem0 := int(Performance.get_monitor(Performance.MEMORY_STATIC))
		var t0 := Time.get_ticks_usec()
		crowd.setup(dir, n)
		var boot_ms := float(Time.get_ticks_usec() - t0) / 1000.0
		host.hero.global_position = Vector3(0, 1, 198)
		var frames := 90
		var samples: Array = []
		var step0 := Time.get_ticks_usec()
		var inside_max := 0
		var near_peak := 0
		for _i in frames:
			var a := Time.get_ticks_usec()
			crowd.step(1.0 / 60.0)
			samples.append(float(Time.get_ticks_usec() - a) / 1000.0)
			inside_max = maxi(inside_max, crowd.inside_count())
			near_peak = maxi(near_peak, crowd.near_n)
		var step_ms := float(Time.get_ticks_usec() - step0) / 1000.0
		samples.sort()
		var p50: float = samples[int(samples.size() / 2)]
		var p95: float = samples[mini(samples.size() - 1, int(samples.size() * 0.95))]
		var pmax: float = samples[samples.size() - 1]
		var mem1 := int(Performance.get_monitor(Performance.MEMORY_STATIC))
		var nodes := 0
		for z in crowd.pool:
			if z.crowd_id >= 0: nodes += 1
		var frames_n := maxi(int(crowd.prof_us.frames), 1)
		print("BENCH_COHORT n=%d boot_ms=%.1f mean_ms=%.3f p50_ms=%.3f p95_ms=%.3f max_ms=%.3f alive=%d near_peak=%d rendered=%d mid=%d far=%d physics_bodies=%d inside=%d static_mem=%d sync_ms=%.2f integrate_ms=%.2f promote_ms=%.2f draw_ms=%.2f" % [n, boot_ms, step_ms / float(frames), p50, p95, pmax, crowd.alive_n, near_peak, crowd.rendered_n, crowd.rendered_mid, crowd.rendered_far, nodes, inside_max, mem1 - mem0, float(crowd.prof_us.sync) / 1000.0 / float(frames_n), float(crowd.prof_us.integrate) / 1000.0 / float(frames_n), float(crowd.prof_us.promote) / 1000.0 / float(frames_n), float(crowd.prof_us.draw) / 1000.0 / float(frames_n)])
		dir.queue_free()
		await process_frame
	print("BENCH_DONE")
	quit(0)
