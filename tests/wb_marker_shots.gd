extends Node
## test 18 (boss: orange diamonds seen over hills across the map). Weak-point markers: shots from a far hill
## (boss hidden behind terrain) and up close, and counts visible markers. Run: WB_MARKERS=1 godot res://tests/wb_lite.tscn
var m: Node
const OUT := "/workspace/shots/godot18/"
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func vis(wb) -> int:
	var n := 0
	for mk in wb.markers: if (mk[0] as Label).visible and (mk[0] as Label).modulate.a > 0.05: n += 1
	return n
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var tag := OS.get_environment("WB_TAG"); if tag == "": tag = "after"
	m.spawn_world_boss(false); await frames(5)
	var wb = m.world_boss
	wb.place_at(5); wb.set_process(true); await frames(20)
	wb._set_state("idle")
	var bp: Vector3 = wb.global_position
	var fails := 0
	# far: ~330 m away, eye level on the ground, find a spot where terrain hides his lower body
	var cam: Camera3D = m.cam
	var dir := Vector3(1, 0, 0.35).normalized()
	var best := Vector3.ZERO
	for d in range(250, 420, 10):
		var q: Vector3 = bp + dir * d
		q.y = m.height(q.x, q.z) + 1.7
		best = q; break
	cam.fov = 60
	cam.look_at_from_position(best, bp + Vector3(0, 40, 0), Vector3.UP)
	await frames(6)
	var far_n := vis(wb)
	get_viewport().get_texture().get_image().save_png(OUT + tag + "_far_hill.png")
	# near: 45 m, looking up at him
	var nq: Vector3 = bp + dir * 45.0; nq.y = m.height(nq.x, nq.z) + 1.7
	cam.look_at_from_position(nq, bp + Vector3(0, 30, 0), Vector3.UP)
	await frames(6)
	var near_n := vis(wb)
	get_viewport().get_texture().get_image().save_png(OUT + tag + "_near_45m.png")
	print("MARKERS far(%.0f m)=%d near(45 m)=%d" % [best.distance_to(bp), far_n, near_n])
	if far_n > 0: fails += 1; print("FAIL markers visible from across the map")
	print("WBMARKERS %d failed" % fails)
	get_tree().quit(fails)
