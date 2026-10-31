extends SceneTree
## test 22 (boss walked out of the exit door from the second storey): for every multi-storey interior, standing over
## the exit spot on an upper floor must NOT leave; the same spot on the ground floor must.
## Run: godot --headless --fixed-fps 60 --path . -s res://tests/exit_floor_test.gd
const DEF := preload("res://interiors/interior_defs.gd")
var fails := 0; var passes := 0
func _initialize() -> void: _run.call_deferred()
func pf(n: int) -> void:
	for i in n: await physics_frame
func _run() -> void:
	var M := Node3D.new(); M.set_script(load("res://tests/fake_main.gd")); root.add_child(M)
	var hero := CharacterBody3D.new(); M.add_child(hero); M.hero = hero
	var mgr := InteriorManager.new(); M.add_child(mgr); mgr.setup(M); M.interiors = mgr
	var ids: Array = DEF.D.keys() + InteriorExtraDefs.D.keys()
	for id in ids:
		var bn := Node3D.new(); M.add_child(bn)
		var b := {"id": id, "name": id, "node": bn, "aabb": AABB(Vector3(-5, 0, -5), Vector3(10, 6, 10))}
		mgr.enter(b); await pf(2)
		var info: Dictionary = mgr.cur
		var nf: int = info.floors.size()
		var spot := Vector3(info.spawn.x, 0, info.exit_z + 0.5)
		if nf > 1:
			for f in range(1, nf):
				mgr.cooldown = 0.0
				hero.global_position = info.node.to_global(spot + Vector3(0, info.floors[f].y, 0)); hero.velocity = Vector3.ZERO
				await pf(3)
				var stayed := mgr.active()
				if stayed: passes += 1
				else: fails += 1
				print(("PASS " if stayed else "FAIL ") + "%s floor %d (y %.1f): exit door ignored" % [id, f, info.floors[f].y])
				if not stayed: mgr.enter(b); await pf(2); info = mgr.cur
		mgr.cooldown = 0.0
		hero.global_position = info.node.to_global(spot); await pf(3)
		var left := not mgr.active()
		if left: passes += 1
		else: fails += 1
		print(("PASS " if left else "FAIL ") + "%s ground floor: exit door works (%d floors)" % [id, nf])
		if mgr.active(): mgr.exit()
		await pf(2); bn.queue_free()
	print("EXITFLOOR %d passed, %d failed" % [passes, fails])
	quit(1 if fails else 0)
