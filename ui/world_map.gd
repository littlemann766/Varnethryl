class_name WorldMap
extends Control
## test 33 (boss: "I wanna be able to see the whole map again by clicking on it" — the web build's minimap had "Tap for
## world map"; the Godot port lost it). Tap the minimap -> full-screen whole-world map (mainland + the Tidewrack Sea:
## Archipelago, Saltglass Coast, Frostreach, Ash straits), player marker; tap again / ✕ closes. Works on land and at sea.
## Fog of war: unexplored parts are dark on this map and on the minimap; exploring reveals them; saved per player in
## VSave.state.fog. The Owner always sees everything (role from Cheats.role(), never from the caller).
## One world frame: sea coords as-is; the mainland (main's MAP_RECT) is placed east of the Archipelago at LAND_AT.
const WORLD := Rect2(-3000, -3000, 5400, 6000)
const LAND_AT := Vector2(1900, 300)    # mainland (0,0) = the town plaza, east of the Tidewrack bay mouth (1300,300)
const CELL := 12.5
const GW := 432                        # WORLD.size / CELL
const GH := 480
const R_LAND := 45.0
const R_SEA := 260.0
var m: Node
var fog := PackedByteArray()           # GW*GH, 0 = hidden, 255 = explored
const HIDDEN := Color(0.04, 0.05, 0.07, 0.97)
const SEEN := Color(0, 0, 0, 0)
var fog_tex: ImageTexture
var sea_tex: ImageTexture
var land_tex: Texture2D
var land_rect := Rect2()
var dirty := false
var tex_dirty := false
var fog_rgba: Image
var n_seen := 0
var save_t := 0.0
var tex_t := 0.0
var player_w := Vector2.ZERO
var player_yaw := 0.0
var close_btn: Button

func setup(main: Node) -> WorldMap:
	m = main; name = "WorldMap"; visible = false; mouse_filter = MOUSE_FILTER_STOP
	set_anchors_preset(PRESET_FULL_RECT)
	close_btn = Button.new(); close_btn.text = "✕"; close_btn.custom_minimum_size = Vector2(64, 64)
	close_btn.anchor_left = 1; close_btn.anchor_right = 1; close_btn.offset_left = -80; close_btn.offset_right = -16; close_btn.offset_top = 16; close_btn.offset_bottom = 80
	close_btn.pressed.connect(close); add_child(close_btn)
	load_fog(); return self

func owner_view() -> bool:
	var ch = m.get("cheats"); return ch != null and str(ch.role()) == "owner"
func _vs() -> Node: return get_tree().root.get_node("VSave") if is_inside_tree() else Engine.get_main_loop().root.get_node("VSave")

# ---------------------------------------------------------------- fog
func load_fog() -> void:
	fog = PackedByteArray(); fog.resize(GW * GH)
	var s = _vs().state.get("fog", "")
	if s is String and s != "":
		var raw := Marshalls.base64_to_raw(s).decompress(GW * GH, FileAccess.COMPRESSION_DEFLATE)
		if raw.size() == GW * GH: fog = raw
	fog_tex = null; dirty = false; n_seen = 0
	fog_rgba = Image.create(GW, GH, false, Image.FORMAT_RGBA8); fog_rgba.fill(HIDDEN)
	for i in fog.size():
		if fog[i] > 0: n_seen += 1; fog_rgba.set_pixel(i % GW, i / GW, SEEN)
	_refresh_tex()
func save_fog() -> void:
	_vs().state["fog"] = Marshalls.raw_to_base64(fog.compress(FileAccess.COMPRESSION_DEFLATE)); _vs().write_state()
func cell(w: Vector2) -> Vector2i: return Vector2i(int((w.x - WORLD.position.x) / CELL), int((w.y - WORLD.position.y) / CELL))
func revealed(w: Vector2) -> bool:
	var c := cell(w); return c.x >= 0 and c.y >= 0 and c.x < GW and c.y < GH and fog[c.y * GW + c.x] > 0
func explored_frac() -> float:
	return float(n_seen) / fog.size()
func reveal(w: Vector2, r: float) -> int:
	var c := cell(w); var k := int(ceil(r / CELL)); var n := 0
	for y in range(maxi(0, c.y - k), mini(GH, c.y + k + 1)):
		for x in range(maxi(0, c.x - k), mini(GW, c.x + k + 1)):
			if Vector2(x - c.x, y - c.y).length() * CELL <= r and fog[y * GW + x] == 0: fog[y * GW + x] = 255; n += 1; fog_rgba.set_pixel(x, y, SEEN)
	if n > 0: dirty = true; tex_dirty = true; n_seen += n
	return n
## world-frame position of the player (sea coords at sea, mainland shifted to LAND_AT on land)
func world_pos() -> Vector2:
	var sea = m.get("sea")
	if sea and sea.active and sea.ship: return Vector2(sea.ship.position.x, sea.ship.position.z)
	return LAND_AT + Vector2(m.hero.position.x, m.hero.position.z)
func tick(dt: float) -> void:
	var sea = m.get("sea"); var at_sea: bool = sea != null and sea.active
	player_w = world_pos(); player_yaw = (sea.ship.heading + PI) if at_sea and sea.ship else m.hero_vis.rotation.y
	reveal(player_w, R_SEA if at_sea else R_LAND)
	tex_t -= dt; save_t -= dt
	if tex_dirty and tex_t <= 0.0: tex_t = 0.5; tex_dirty = false; _refresh_tex()
	if dirty and save_t <= 0.0: save_t = 4.0; dirty = false; save_fog()
	var mm = VUI.hud.minimap if VUI.hud else null
	if mm:   # minimap shows the mainland: give it the fog in mainland coords (none for the Owner)
		mm.fog_tex = null if owner_view() else fog_tex
		mm.fog_rect = Rect2(WORLD.position - LAND_AT, WORLD.size)
	if visible: queue_redraw()
func _refresh_tex() -> void:
	if fog_tex == null: fog_tex = ImageTexture.create_from_image(fog_rgba)
	else: fog_tex.update(fog_rgba)

# ---------------------------------------------------------------- map art
func _build_sea() -> void:
	var sea = m.get("sea"); var W := 540; var H := 600
	var img := Image.create(W, H, false, Image.FORMAT_RGBA8); img.fill(Color(0.12, 0.25, 0.38))
	if sea:
		for y in H:
			for x in W:
				var w := WORLD.position + Vector2(x + 0.5, y + 0.5) * (WORLD.size / Vector2(W, H))
				var s: float = sea.shore_m(w)
				if s < 255.0:
					var c := Color(0.16, 0.36, 0.52).lerp(Color(0.10, 0.24, 0.40), clampf(s / 120.0, 0.0, 1.0))
					if s <= 0.5: c = Color(0.52, 0.47, 0.33) if sea.region_at(w) != "frost" else Color(0.82, 0.86, 0.9)
					if s <= 0.5 and sea.region_at(w) == "ash": c = Color(0.3, 0.27, 0.26)
					img.set_pixel(x, y, c)
	sea_tex = ImageTexture.create_from_image(img)
func open() -> void:
	if sea_tex == null: _build_sea()
	var mm = VUI.hud.minimap if VUI.hud else null
	if mm: land_tex = mm.map_tex; land_rect = Rect2(mm.world_rect.position + LAND_AT, mm.world_rect.size)
	tick(0.0); _refresh_tex(); visible = true; move_to_front(); queue_redraw()
func close() -> void: visible = false
func toggle() -> void:
	if visible: close()
	else: open()
func _gui_input(e: InputEvent) -> void:
	if (e is InputEventMouseButton and not e.pressed and e.button_index == MOUSE_BUTTON_LEFT) or (e is InputEventScreenTouch and not e.pressed): close(); accept_event()

func _fit() -> Rect2:
	var s := size; var k := minf((s.x - 40) / WORLD.size.x, (s.y - 90) / WORLD.size.y)
	var sz := WORLD.size * k; return Rect2(Vector2((s.x - sz.x) * 0.5, 70 + (s.y - 90 - sz.y) * 0.5), sz)
func w2s(w: Vector2, r: Rect2) -> Vector2: return r.position + (w - WORLD.position) / WORLD.size * r.size
func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.03, 0.04, 0.06, 0.96))
	var r := _fit()
	draw_string(get_theme_default_font(), Vector2(r.position.x, 50), "WORLD MAP" + ("   (Owner: fully revealed)" if owner_view() else "   %.1f%% explored" % (explored_frac() * 100.0)), HORIZONTAL_ALIGNMENT_LEFT, -1, 30, Color("#f3d98b"))
	if sea_tex: draw_texture_rect(sea_tex, r, false)
	if land_tex:
		var a := w2s(land_rect.position, r); var b := w2s(land_rect.end, r); var lr := Rect2(a, b - a).grow(0)
		draw_texture_rect(land_tex, lr, false)
		draw_rect(lr, Color("#f3d98b"), false, 1.5)
	var sea = m.get("sea")
	if sea:
		for k in sea.ports():
			var pv = sea.ports()[k][1]; var w: Vector2 = Vector2(1300, 300) if pv == null else Vector2(pv.x, pv.z)
			if owner_view() or revealed(w):
				var p := w2s(w, r); draw_circle(p, 6, Color("#ffd27a")); draw_string(get_theme_default_font(), p + Vector2(9, 5), str(sea.ports()[k][0]), HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
	if not owner_view() and fog_tex: draw_texture_rect(fog_tex, r, false)
	draw_rect(r, Color("#8a7340"), false, 2.0)
	var c := w2s(player_w, r); var f := Vector2(-sin(player_yaw), -cos(player_yaw)); var sd := Vector2(-f.y, f.x)
	draw_circle(c, 13, Color(0, 0, 0, 0.5))
	draw_colored_polygon(PackedVector2Array([c + f * 12, c - f * 8 + sd * 8, c - f * 4, c - f * 8 - sd * 8]), Color("#ffe9a8"))
