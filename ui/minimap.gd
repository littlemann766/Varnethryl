extends Control
## Minimap shell: circular map, player arrow, markers, and the clean gold ring (www/assets/hud/minimap-ring.svg
## with the four zig-zag "thorn" decorations removed, as the boss asked).
## Hook: set_map_texture(tex, world_rect) once; set_player(pos_xz, yaw) every frame; set_markers([{pos:Vector2,color:Color}]).
var map_tex: Texture2D
var world_rect := Rect2(-60, -60, 120, 120)   # world XZ covered by map_tex
var view_radius := 30.0                        # metres shown from centre to edge
var player := Vector2.ZERO
var yaw := 0.0
var markers: Array = []
var ring: Texture2D
signal tapped   # test 33: tap -> full world map
var fog_tex: Texture2D   # test 33: fog of war overlay (null = all revealed, e.g. the Owner)
var fog_rect := Rect2()
var _down := Vector2.INF

func _ready() -> void:
	name = "Minimap"; custom_minimum_size = Vector2(170, 170); size = custom_minimum_size; mouse_filter = MOUSE_FILTER_PASS
	ring = load("res://ui/assets/minimap-ring.svg")

func _gui_input(e: InputEvent) -> void:
	var hud = get_parent()
	if hud and hud.get("editing"): return
	if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT:
		if e.pressed: _down = e.position
		elif _down != Vector2.INF and e.position.distance_to(_down) < 24.0: _down = Vector2.INF; tapped.emit(); accept_event()
func set_map_texture(t: Texture2D, rect: Rect2) -> void: map_tex = t; world_rect = rect; queue_redraw()
func set_player(p: Vector2, y: float) -> void: player = p; yaw = y; queue_redraw()
func set_markers(m: Array) -> void: markers = m; queue_redraw()

func _w2m(w: Vector2, c: Vector2, r: float) -> Vector2:
	return c + (w - player) / view_radius * r

func _draw() -> void:
	var s := minf(size.x, size.y); var c := Vector2(s, s) * 0.5; var r := s * 0.36
	draw_circle(c, r, Color("#1b2a22"))
	if map_tex:
		# Sample the map as a textured circle polygon (UV from world coords).
		var pts := PackedVector2Array(); var uvs := PackedVector2Array()
		for i in 48:
			var a := TAU * i / 48.0; var o := Vector2(cos(a), sin(a))
			pts.append(c + o * r)
			var w := player + o * view_radius
			uvs.append((w - world_rect.position) / world_rect.size)
		draw_colored_polygon(pts, Color.WHITE, uvs, map_tex)
	if fog_tex and fog_rect.size.x > 0.0:
		var fp := PackedVector2Array(); var fu := PackedVector2Array()
		for i in 48:
			var a2 := TAU * i / 48.0; var o2 := Vector2(cos(a2), sin(a2)); fp.append(c + o2 * r)
			fu.append((player + o2 * view_radius - fog_rect.position) / fog_rect.size)
		draw_colored_polygon(fp, Color.WHITE, fu, fog_tex)
	for m in markers:
		var p := _w2m(m.pos, c, r)
		if p.distance_to(c) < r - 3: draw_circle(p, 3.5, m.get("color", Color.RED))
	# player arrow (yaw 0 = facing -Z = up)
	var f := Vector2(-sin(yaw), -cos(yaw)); var sd := Vector2(-f.y, f.x)
	draw_colored_polygon(PackedVector2Array([c + f * 9, c - f * 6 + sd * 6, c - f * 3, c - f * 6 - sd * 6]), Color("#ffe9a8"))
	if ring: draw_texture_rect(ring, Rect2(Vector2.ZERO, Vector2(s, s)), false)
