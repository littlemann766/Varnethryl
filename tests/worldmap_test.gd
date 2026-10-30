extends Node
## test 33: minimap tap -> whole-world map (land + sea), fog of war per player (saved), Owner sees all. -- --worldmap
var m: Node
var npass := 0
var nfail := 0
var out := "/workspace/shots/voxel33/"
func ok(c: bool, t: String) -> void:
	if c: npass += 1; print("WM PASS ", t)
	else: nfail += 1; print("WM FAIL ", t)
func _ready() -> void: m = get_parent(); _run.call_deferred()
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func shot(n: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await frames(6); get_viewport().get_texture().get_image().save_png(out + "map_%s.png" % n); print("WM SHOT ", n)
func tap(c: Control) -> void:
	for p in [true, false]:
		var e := InputEventMouseButton.new(); e.button_index = MOUSE_BUTTON_LEFT; e.pressed = p; e.position = c.size * 0.5; c._gui_input(e)
func _run() -> void:
	DirAccess.make_dir_recursive_absolute(out)
	while not m.warmed: await get_tree().process_frame
	m._set_time(11.0); m.party._set_companions([]); m.party.set_hero("aldric")
	var W: WorldMap = m.world_map; var C: Cheats = m.cheats; var rp0: Callable = C.role_provider
	var VSn: Node = get_tree().root.get_node("VSave"); var fog0 = VSn.state.get("fog", "")
	C.role_provider = func() -> String: return ""
	VSn.state.erase("fog"); W.load_fog(); await frames(3)
	ok(W != null and not W.visible, "world map exists, closed")
	var mm: Control = VUI.hud.minimap
	tap(mm); await frames(2); ok(W.visible, "tap minimap opens the full map")
	ok(W.sea_tex != null and W.land_tex != null, "full map has the mainland + Tidewrack Sea")
	var here := W.world_pos(); ok(W.revealed(here), "player's spot is revealed")
	var far := Vector2(-2500, -2500); ok(not W.revealed(far), "unexplored far sea is fogged")
	ok(mm.fog_tex != null, "minimap gets fog for a normal player")
	m._teleport(Vector3(60, 0, 60), 0.0); await frames(10)
	ok(W.revealed(WorldMap.LAND_AT + Vector2(60, 60)), "walking reveals new ground")
	m._teleport(Vector3(0, 0, 0), 0.0); await frames(5)
	await shot("player_fogged")
	tap(W); await frames(2); ok(not W.visible, "tap again closes")
	W.toggle(); await frames(2); W.close_btn.pressed.emit(); await frames(1); ok(not W.visible, "✕ closes")
	# save / reload per player
	W.save_fog(); var frac: float = W.explored_frac(); var r = VSn.read_save()
	ok(r.status == "ok" and str(r.state.get("fog", "")) != "", "fog written to the save")
	VSn.state["fog"] = r.state.fog; W.load_fog(); ok(absf(W.explored_frac() - frac) < 1e-6 and W.revealed(WorldMap.LAND_AT + Vector2(60, 60)), "fog survives a reload")
	# at sea
	var sea = m.sea; sea.enter("galleon", Vector3(-500, 0, 400), 0.0); await frames(10)
	ok(W.revealed(Vector2(sea.ship.position.x, sea.ship.position.z)) and not W.revealed(far), "sailing reveals the sea around the ship")
	W.open(); await frames(2); ok(W.visible, "full map opens while sailing")
	await shot("player_sailing"); W.close()
	# coowner uses fog
	C.role_provider = func() -> String: return "coowner"
	await frames(2); ok(not W.owner_view() and mm.fog_tex != null, "coowner: fog of war applies")
	# owner sees all
	C.role_provider = func() -> String: return "owner"
	await frames(2); ok(W.owner_view() and mm.fog_tex == null, "owner: minimap fully revealed")
	W.open(); await frames(2); await shot("owner_full"); W.close()
	sea.leave_to_harbour(); await frames(5)
	C.role_provider = rp0
	if str(fog0) != "": VSn.state["fog"] = fog0
	else: VSn.state.erase("fog")
	VSn.write_state(); W.load_fog()
	print("WM DONE pass=%d fail=%d" % [npass, nfail]); get_tree().quit(0 if nfail == 0 else 1)
