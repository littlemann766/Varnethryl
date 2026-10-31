extends Node
## test 25: Arcane Academy title shows on entry, gone while flying outside. -- --whereshots
var m: Node
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func shot(n: String) -> void:
	await frames(3); get_viewport().get_texture().get_image().save_png("/workspace/shots/voxel25/" + n + ".png"); print("SHOT ", n, " title_visible=", m.where_label.visible)
func _run() -> void:
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0)
	if m.fly_controls: m.fly_controls.process_mode = Node.PROCESS_MODE_DISABLED
	for b in m.buildings:
		if b.id == "mage": m.interiors.enter(b); break
	await frames(20); await shot("title_1_academy_entry")
	m.flight = true; m.cheat["fly"] = true
	m.hero.global_position = Vector3(-124, 60, -200); m.pitch = -0.6
	await frames(30); await shot("title_2_flying_outside")
	get_tree().quit(0)
