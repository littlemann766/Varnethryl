extends Node
## titan-voxel: stomp + fissure slam on their ground-contact frames (worldboss_events.json contact). WB_SCRIPT host.
var m: Node
const OUT := "/workspace/shots/titanvoxel1/"
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func shot(n: String) -> void:
	await frames(1); get_viewport().get_texture().get_image().save_png(OUT + n + ".png"); print("SHOT ", n)
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	await frames(10); m.spawn_world_boss(false); await frames(5)
	var wb = m.world_boss; wb.place_at(5); await frames(20)
	var c := Camera3D.new(); c.fov = 55; c.far = 3000; m.add_child(c); c.current = true
	var p: Vector3 = wb.global_position; var side: Vector3 = wb._fwd().cross(Vector3.UP)
	c.look_at_from_position(p + side * 230.0 + Vector3(0, 45, 0) + wb._fwd() * 60.0, p + Vector3(0, 50, 0), Vector3.UP)
	await shot("titan_voxel_idle")
	wb._set_state("arrive")
	var ct: float = wb._ct("wb_stomp", 2.4)
	while wb.t_state < ct - 0.4: await get_tree().process_frame
	await shot("stomp_1_before_contact")
	while wb.t_state < ct + 0.12: await get_tree().process_frame
	await shot("stomp_2_contact"); await frames(8); await shot("stomp_3_dust")
	wb._set_state("idle"); await frames(5)
	wb.rituals_done = 0; wb._start_ritual()
	wb.t_state = wb._wind_len() - 0.05
	while wb.state != "release": await get_tree().process_frame
	var rt: float = wb._ct("wb_ritual_fissure_release", 0.9)
	while wb.t_state < rt - 0.3: await get_tree().process_frame
	await shot("fissure_1_before_contact")
	while wb.t_state < rt + 0.12: await get_tree().process_frame
	await shot("fissure_2_contact"); await frames(10); await shot("fissure_3_erupt")
	get_tree().quit(0)
