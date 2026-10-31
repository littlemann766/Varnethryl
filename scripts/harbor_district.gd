class_name HarborDistrict
extends RefCounted
## Test 14 (boss: "a HUGE SW port"): the harbour district on the north shore of the SW sea, west of the old port.
## Quay + 3 timber piers, 4 warehouses, 3 cranes, the Harbour Master's office, a fish market, a tavern, crates/barrels
## and carts, plus moored and anchored ships (main._ships). Textured with the shared interior kit textures
## (fieldstone / oak / slate / cobble, world-triplanar, one material each -> few draw-call states on the phone).
## Waterline y = 0, sea floor -4 (main.height), quay deck top QY.

const QY := 0.45                 # quay / pier deck top
const SHORE_Z := 322.0           # main.SEA_NORTH_Z (sea is z > this, west of the coast)
const X0 := -580.0               # district west end
const X1 := -392.0               # east end (Tidewrack road comes in at (-387, 322))
const Z0 := 262.0                # north (inland) edge of the paved district
const PIERS := [-472.0, -505.0, -538.0]
const CRANES := [-488.0, -521.0, -556.0]
const WAREHOUSES := [-547.0, -522.0, -497.0, -472.0]   # centre x, 22 m wide, z 286..306
var m: Node3D
var root: Node3D
var mats := {}

static func pad_weight(x: float, z: float) -> float:
	# 1 inside the district rect, fading to 0 over 50 m (main.height levels the ground to ~0.25 there)
	var dx := maxf(maxf(X0 - x, x - X1), 0.0); var dz := maxf(Z0 - z, 0.0)
	return 1.0 - smoothstep(0.0, 50.0, Vector2(dx, dz).length())

func _tm(key: String, tile: float, tint := Color.WHITE) -> StandardMaterial3D:
	if mats.has(key + str(tint)): return mats[key + str(tint)]
	var s := StandardMaterial3D.new(); s.albedo_texture = load("res://interiors/tex/%s_albedo.jpg" % key); s.albedo_color = tint
	if ResourceLoader.exists("res://interiors/tex/%s_normal.png" % key): s.normal_enabled = true; s.normal_texture = load("res://interiors/tex/%s_normal.png" % key)
	s.uv1_triplanar = true; s.uv1_world_triplanar = true; s.uv1_scale = Vector3.ONE / tile; s.roughness = 0.9
	mats[key + str(tint)] = s; return s

func _box(pos: Vector3, size: Vector3, mat: Material, col := true, rot := 0.0, shadow := true) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = size; mi.mesh = bm; mi.material_override = mat
	mi.position = pos; mi.rotation.y = rot; root.add_child(mi)
	if not shadow: mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.visibility_range_end = 700.0
	if col: m._static_box(pos, size, rot)
	return mi

func _label(text: String, pos: Vector3) -> void:
	var lb := Label3D.new(); lb.text = text; lb.font_size = 56; lb.pixel_size = 0.012; lb.modulate = Color(1, 0.9, 0.6); lb.outline_size = 10
	lb.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y; lb.position = pos; lb.visibility_range_end = 90.0; root.add_child(lb)

func build(main: Node3D) -> Node3D:
	m = main; root = Node3D.new(); root.name = "HarborDistrict"; m.add_child(root)
	var stone := _tm("fieldstone", 2.2, Color(0.82, 0.8, 0.76)); var oak := _tm("oak", 1.6); var slate := _tm("slate", 2.0)
	var cobble := _tm("cobblestone", 3.0, Color(0.9, 0.88, 0.85)); var plaster := _tm("plaster_timber", 3.0)
	var xc: float = m.SEA_COAST_X
	# paved district floor (cobbles) from the warehouses down to the quay, and over to the Tidewrack road
	var pv := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(xc + 1.0 - X0, SHORE_Z - Z0 + 1.0); pv.mesh = pm
	pv.material_override = cobble; pv.position = Vector3((X0 + xc + 1.0) * 0.5, m.HARBOR_Y + 0.06, (Z0 + SHORE_Z) * 0.5); pv.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(pv)
	var pv2 := MeshInstance3D.new(); var pm2 := PlaneMesh.new(); pm2.size = Vector2(X1 - xc, 60.0); pv2.mesh = pm2; pv2.material_override = cobble
	pv2.position = Vector3((xc + X1) * 0.5, m.HARBOR_Y + 0.06, Z0 + 30.0); pv2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(pv2)
	# test 32: one flat collider under the whole paved district (top = pave level) so the walkable ground matches the
	# cobbles everywhere and there are no heightfield seams (rays exactly on the 10 m grid lines used to miss)
	m._static_box(Vector3((X0 + xc) * 0.5, m.HARBOR_Y + 0.06 - 0.5, (Z0 + SHORE_Z) * 0.5), Vector3(xc - X0, 1.0, SHORE_Z - Z0 + 1.0))
	# quay: solid dressed-stone wall along the north shore, deck at QY, bollards
	var qz := SHORE_Z + 2.0
	_box(Vector3((X0 + xc) * 0.5, QY - 2.5, qz), Vector3(xc - X0, 5.0, 6.0), stone)
	for x in range(int(X0) + 6, int(xc) - 4, 12):
		var bo := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 0.28; cm.bottom_radius = 0.34; cm.height = 0.8; bo.mesh = cm
		bo.material_override = _tm("fieldstone", 1.0, Color(0.35, 0.33, 0.32)); bo.position = Vector3(x, QY + 0.4, qz + 2.6); root.add_child(bo)
	# piers: oak decks on posts, out over the water
	for px in PIERS:
		var L := 34.0
		_box(Vector3(px, QY - 0.15, qz + 3.0 + L * 0.5), Vector3(4.2, 0.3, L), oak)
		for k in range(0, int(L) + 1, 4):
			for sd in [-1.9, 1.9]:
				var po := MeshInstance3D.new(); var cm2 := CylinderMesh.new(); cm2.top_radius = 0.18; cm2.bottom_radius = 0.2; cm2.height = 5.0; po.mesh = cm2
				po.material_override = oak; po.position = Vector3(px + sd, QY - 2.6, qz + 3.0 + k); root.add_child(po)
		for k in 3: m._street_prop(["crate_stack", "barrel_group", "crate_stack"][k], Vector3(px + 1.2, QY, qz + 8.0 + k * 9.0), PI * 0.5 * k)
	# cranes: timber tower + jib over the water, rope + a hanging crate
	for cx in CRANES:
		var base := Vector3(cx, QY, qz + 1.0)
		_box(base + Vector3(0, 0.4, 0), Vector3(3.0, 0.8, 3.0), stone)
		_box(base + Vector3(0, 5.6, 0), Vector3(1.1, 9.6, 1.1), oak, false)
		var jib := _box(base + Vector3(0, 10.0, 4.5), Vector3(0.7, 0.7, 12.0), oak, false)
		var brace := _box(base + Vector3(0, 7.6, 2.0), Vector3(0.45, 0.45, 5.8), oak, false); brace.rotation.x = deg_to_rad(-40)
		var rope := MeshInstance3D.new(); var rc := CylinderMesh.new(); rc.top_radius = 0.04; rc.bottom_radius = 0.04; rc.height = 5.0; rope.mesh = rc
		rope.material_override = m._mat(Color(0.55, 0.45, 0.3)); rope.position = base + Vector3(0, 7.5, 10.0); root.add_child(rope)
		_box(base + Vector3(0, 4.4, 10.0), Vector3(1.4, 1.2, 1.4), oak, false)
		var wheel := MeshInstance3D.new(); var tm := TorusMesh.new(); tm.inner_radius = 1.0; tm.outer_radius = 1.25; wheel.mesh = tm
		wheel.material_override = oak; wheel.position = base + Vector3(1.0, 1.8, -0.5); wheel.rotation.z = PI / 2; root.add_child(wheel)
	# warehouses: stone ground floor, timber-framed upper floor, slate gable roof, big oak doors facing the quay
	for wx in WAREHOUSES:
		var zc := 296.0; var W := 22.0; var D := 20.0; var y0: float = m.HARBOR_Y
		var hgt: float = 6.5 + fmod(absf(wx) * 0.37, 2.0)
		_box(Vector3(wx, y0 + hgt * 0.35, zc), Vector3(W, hgt * 0.7, D), stone)
		_box(Vector3(wx, y0 + hgt * 0.85, zc), Vector3(W - 0.4, hgt * 0.3, D - 0.4), plaster, false)
		for sd in [-1, 1]:
			var rf := _box(Vector3(wx, y0 + hgt + 2.0, zc + sd * D * 0.25), Vector3(W + 1.0, 0.35, D * 0.56), slate, false)
			rf.rotation.x = -sd * deg_to_rad(28)
		_box(Vector3(wx, y0 + hgt + 3.9, zc), Vector3(W + 1.0, 0.5, 0.6), slate, false)
		for gx in [-W * 0.5 + 0.1, W * 0.5 - 0.1]:   # gable ends
			var gm := MeshInstance3D.new(); var pr := PrismMesh.new(); pr.size = Vector3(D, 4.2, 0.4); gm.mesh = pr; gm.material_override = plaster
			gm.position = Vector3(wx + gx, y0 + hgt + 2.0, zc); gm.rotation.y = PI / 2; root.add_child(gm)
		_box(Vector3(wx, y0 + 2.2, zc + D * 0.5 + 0.05), Vector3(5.0, 4.4, 0.25), _tm("oak", 1.0, Color(0.6, 0.45, 0.32)), false)
		for k in 2: m._street_prop(["crate_stack", "barrel_group"][k], Vector3(wx + (k * 2 - 1) * 6.0, y0, zc + D * 0.5 + 2.5), 0.0)
	_label("Warehouses", Vector3(WAREHOUSES[1] + 12.0, m.HARBOR_Y + 12.0, 308.0))
	# landmark kit buildings (Beth's card2 LOD1/LOD2 + -colonly collision), fronts facing the water (+z)
	for b in [["house4", Vector2(-447.0, 300.0), "Harbour Master"], ["market", Vector2(-428.0, 291.0), "Fish Market"], ["inn", Vector2(-405.0, 300.0), "The Salty Anchor (Tavern)"]]:
		var pos := Vector3(b[1].x, m.HARBOR_Y, b[1].y)
		var n := Node3D.new(); n.name = b[2]; n.position = pos; root.add_child(n)
		for k in 2:
			var v: Node3D = load(m._card2_path(b[0], ["_lod1", "_lod2"][k])).instantiate(); n.add_child(v)
			for mi: MeshInstance3D in v.find_children("*", "MeshInstance3D", true, false):
				mi.visibility_range_begin = [0.0, 90.0][k]; mi.visibility_range_end = [90.0, 0.0][k]   # test 17: lod2 stays drawn from any height
				if k == 1: mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		m._add_col(m._card2_path(b[0], "_col"), pos, 0.0)
		_label(b[2], pos + Vector3(0, 13.0, 8.0))
	# fish market stalls + carts on the quay front
	for k in 4: m._street_prop("market_cart", Vector3(-436.0 + k * 5.5, m.HARBOR_Y, 314.0), PI * (k % 2))
	for k in 6: m._street_prop(["barrel_group", "crate_stack"][k % 2], Vector3(-560.0 + k * 17.0, QY, qz - 1.6), k * 0.7)
	for k in 5: m._street_prop("lantern_post", Vector3(-565.0 + k * 30.0, QY, qz - 2.6), 0.0)
	return root
