extends Node3D
# Varnethryl Godot test: main town rebuilt from buildings.js BUILDING_DEFS (cx,cz * PK=2.8)

const PK := 2.8
const CITY_HALF := 185.0
const BETH := {"house1":"bld_house1","house2":"bld_house2","house3":"bld_house3","house4":"bld_house4",
	"farmhouse":"bld_farmhouse","thieves":"bld_thieves","barn":"bld_barn","stables":"bld_stables","windmill":"bld_windmill"}
# id, cx, cz, rot, name, blockout w,d,h (metres) for buildings Beth has not modelled yet
const DEFS := [
	["guildhall",0,-21,0.0,"Guild Hall",22,17,11], ["library",-24,-27,0.0,"Grand Library",24,24,14],
	["townhall",23,-26,0.0,"Town Hall",24,22,13], ["mage",-44,-31,0.0,"Mage Academy",27,24,14],
	["treasury",41,-27,0.0,"Treasury",20,17,12], ["keep",0,-48,0.0,"Castle Keep",37,27,17],
	["observatory",-41,-46,0.0,"Observatory",20,20,19], ["crypt",43,-45,0.0,"Crypt",17,24,9],
	["market",-24,-6,PI/2,"Market Provisioner",18,14,9], ["apothecary",-24,9,PI/2,"Apothecary",16,13,9],
	["bakery",-24,21.5,PI/2,"Bakery",16,13,9], ["inn",24,-8,-PI/2,"Inn",21,16,11],
	["smithy",24,7,-PI/2,"Blacksmith",18,14,9], ["temple",46,-8,-PI/2,"Temple",24,37,15],
	["training",45,11,-PI/2,"Training Hall",22,16,10], ["colosseum",42,38,0.0,"Colosseum",42,42,13],
	["thieves",-36.5,8,0.0,"Thieves' Den",0,0,0], ["farmhouse",-42,-9,0.0,"Farmhouse",0,0,0],
	["barn",-51,21,PI/2,"Barn",0,0,0], ["stables",-24,42,0.0,"Stables",0,0,0],
	["windmill",20,46,0.0,"Windmill",0,0,0],
	["house1",-9,19,PI,"Village House",0,0,0], ["house2",9,19,PI,"Village House",0,0,0],
	["house3",-9,31,PI,"Village House",0,0,0], ["house4",9,31,PI,"Village House",0,0,0],
]

var hero: CharacterBody3D
var hero_vis: Node3D
var pip: Node3D
var cam_pivot: Node3D
var cam_arm: SpringArm3D
var cam: Camera3D
var yaw := 0.0
var pitch := -0.35
var buildings := []   # {name, node, roof, inv(Transform3D), aabb}
var blades: Node3D
var hud_label: Label
var where_label: Label
var joy_vec := Vector2.ZERO
var joy_touch := -1
var cam_touch := -1
var joy_center := Vector2.ZERO
var joy_base: Control
var joy_knob: Control
var walk_t := 0.0
var limbs := []
var bench := false
var rng := RandomNumberGenerator.new()

func _ready() -> void:
	rng.seed = 1905
	bench = OS.get_cmdline_user_args().has("--bench")
	_env()
	_ground()
	_fountain()
	_pond()
	_walls_and_gate()
	for d in DEFS: _building(d)
	_foliage()
	_props()
	_hero()
	_hud()
	if bench: _run_bench()

# ---------- world ----------
func _env() -> void:
	var we := WorldEnvironment.new()
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.32, 0.52, 0.82); sm.sky_horizon_color = Color(0.78, 0.82, 0.86)
	sm.ground_horizon_color = Color(0.6, 0.62, 0.6); sm.ground_bottom_color = Color(0.25, 0.3, 0.22)
	sm.sun_angle_max = 20.0
	sky.sky_material = sm
	env.background_mode = Environment.BG_SKY; env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.ambient_light_energy = 0.8
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC; env.tonemap_exposure = 1.0
	env.fog_enabled = true; env.fog_light_color = Color(0.72, 0.78, 0.85)
	env.fog_density = 0.0035; env.fog_aerial_perspective = 0.4; env.fog_sky_affect = 0.3
	env.glow_enabled = true; env.glow_intensity = 0.4; env.glow_bloom = 0.05
	we.environment = env; add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-42, -35, 0)
	sun.light_color = Color(1.0, 0.94, 0.84); sun.light_energy = 1.25
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sun.directional_shadow_max_distance = 70.0
	sun.shadow_blur = 1.2
	add_child(sun)

func _static_box(pos: Vector3, size: Vector3, rot := 0.0) -> StaticBody3D:
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var bs := BoxShape3D.new()
	bs.size = size; cs.shape = bs; sb.add_child(cs); sb.position = pos; sb.rotation.y = rot; add_child(sb); return sb

func _ground() -> void:
	var mi := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(1400, 1400)
	var m := ShaderMaterial.new(); m.shader = load("res://scripts/ground.gdshader"); pm.material = m
	mi.mesh = pm; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(mi)
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); cs.shape = WorldBoundaryShape3D.new(); sb.add_child(cs); add_child(sb)

func _mat(c: Color, rough := 0.85) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.albedo_color = c; m.roughness = rough; return m

func _water_mat() -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = load("res://scripts/water.gdshader"); return m

func _fountain() -> void:
	var stone := _mat(Color(0.72, 0.7, 0.66))
	var basin := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 6.5; cm.bottom_radius = 6.8; cm.height = 0.9; cm.radial_segments = 32
	cm.material = stone; basin.mesh = cm; basin.position.y = 0.45; add_child(basin)
	var w := MeshInstance3D.new(); var cw := CylinderMesh.new(); cw.top_radius = 6.0; cw.bottom_radius = 6.0; cw.height = 0.1; cw.radial_segments = 32
	cw.material = _water_mat(); w.mesh = cw; w.position.y = 0.88; add_child(w)
	var col := MeshInstance3D.new(); var c2 := CylinderMesh.new(); c2.top_radius = 0.7; c2.bottom_radius = 1.0; c2.height = 3.2; c2.material = stone
	col.mesh = c2; col.position.y = 1.6; add_child(col)
	var lion := MeshInstance3D.new(); var sp := SphereMesh.new(); sp.radius = 1.0; sp.height = 1.6; sp.material = _mat(Color(0.12, 0.29, 0.6), 0.4)
	lion.mesh = sp; lion.position.y = 3.8; add_child(lion)
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var cy := CylinderShape3D.new(); cy.radius = 6.8; cy.height = 2.0; cs.shape = cy; sb.add_child(cs); add_child(sb)

func _pond() -> void:
	var w := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(40, 26); pm.subdivide_width = 30; pm.subdivide_depth = 20
	pm.material = _water_mat(); w.mesh = pm; w.position = Vector3(-110, 0.05, 110); add_child(w)
	var edge := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = Vector3(43, 0.3, 29); bm.material = _mat(Color(0.35, 0.3, 0.22))
	edge.mesh = bm; edge.position = Vector3(-110, -0.12, 110); add_child(edge)
	_static_box(Vector3(-110, 0.5, 110), Vector3(40, 1, 26))

func _walls_and_gate() -> void:
	var stone := _mat(Color(0.62, 0.6, 0.56))
	var H := 8.0; var T := 3.0
	var runs := [[Vector3(0, H/2, -CITY_HALF), Vector3(2*CITY_HALF, H, T)],
		[Vector3(-CITY_HALF, H/2, 0), Vector3(T, H, 2*CITY_HALF)], [Vector3(CITY_HALF, H/2, 0), Vector3(T, H, 2*CITY_HALF)],
		[Vector3(-(CITY_HALF+7)/2 - 3.5, H/2, CITY_HALF), Vector3(CITY_HALF - 7, H, T)], [Vector3((CITY_HALF+7)/2 + 3.5, H/2, CITY_HALF), Vector3(CITY_HALF - 7, H, T)]]
	for r in runs:
		var mi := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = r[1]; bm.material = stone; mi.mesh = bm; mi.position = r[0]; add_child(mi)
		_static_box(r[0], r[1])
	for s in [-1, 1]:
		var g := _place_glb("res://assets/buildings/bld_gate_tower.glb", Vector3(s * 8.2 * 1.7, 0, CITY_HALF - 1.2), PI)
		_add_trimesh(g)
	var arch := MeshInstance3D.new(); var am := BoxMesh.new(); am.size = Vector3(18, 2.0, 4); am.material = stone; arch.mesh = am; arch.position = Vector3(0, 9, CITY_HALF); add_child(arch)

func _place_glb(path: String, pos: Vector3, rot: float) -> Node3D:
	var n: Node3D = load(path).instantiate(); n.position = pos; n.rotation.y = rot; add_child(n); return n

func _meshes(n: Node, out: Array) -> Array:
	if n is MeshInstance3D: out.append(n)
	for c in n.get_children(): _meshes(c, out)
	return out

func _add_trimesh(n: Node3D, skip := "roof") -> void:
	for mi in _meshes(n, []):
		if skip != "" and String(mi.name).to_lower().contains(skip): continue
		if String(mi.get_parent().name).to_lower().contains(skip): continue
		mi.create_trimesh_collision()

func _building(d: Array) -> void:
	var id: String = d[0]; var pos := Vector3(float(d[1]) * PK, 0, float(d[2]) * PK); var rot: float = d[3]
	if BETH.has(id):
		var n := _place_glb("res://assets/buildings/%s.glb" % BETH[id], pos, rot)
		_add_trimesh(n)
		var roof: Node3D = n.find_child("roof", true, false)
		var aabb := AABB()
		var first := true
		for mi in _meshes(n, []):
			var a: AABB = (n.global_transform.affine_inverse() * mi.global_transform) * mi.get_aabb()
			if first: aabb = a; first = false
			else: aabb = aabb.merge(a)
		buildings.append({"name": d[4], "node": n, "roof": roof, "aabb": aabb})
		if id == "windmill": blades = n.find_child("blades", true, false)
	else:
		var w: float = d[5]; var dd: float = d[6]; var h: float = d[7]
		var root := Node3D.new(); root.position = pos; root.rotation.y = rot; add_child(root)
		var hue := rng.randf_range(-0.04, 0.04)
		var body := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = Vector3(w, h, dd); bm.material = _mat(Color(0.68 + hue, 0.64 + hue, 0.58))
		body.mesh = bm; body.position.y = h / 2; root.add_child(body)
		var rf := MeshInstance3D.new(); var pr := PrismMesh.new(); pr.size = Vector3(w + 1.2, h * 0.4, dd + 1.2); pr.material = _mat(Color(0.32, 0.36, 0.44))
		rf.mesh = pr; rf.position.y = h + h * 0.2; root.add_child(rf)
		var door := MeshInstance3D.new(); var dm := BoxMesh.new(); dm.size = Vector3(3, 4, 0.3); dm.material = _mat(Color(0.3, 0.2, 0.12))
		door.mesh = dm; door.position = Vector3(0, 2, dd / 2 + 0.1); root.add_child(door)
		var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var bs := BoxShape3D.new(); bs.size = Vector3(w, h, dd)
		cs.shape = bs; cs.position.y = h / 2; sb.add_child(cs); root.add_child(sb)

# ---------- foliage (MultiMesh + wind shader) ----------
func _first_mesh(path: String) -> Array:
	var n: Node = load(path).instantiate()
	var out := []
	for mi in _meshes(n, []): out.append([mi.mesh, mi.transform])
	n.free()
	return out

func _wind_mats(mesh: Mesh, sway: float) -> Array:
	var mats := []
	for i in mesh.get_surface_count():
		var src = mesh.surface_get_material(i)
		var m := ShaderMaterial.new(); m.shader = load("res://scripts/wind.gdshader")
		if src is BaseMaterial3D:
			m.set_shader_parameter("albedo_tex", src.albedo_texture)
			m.set_shader_parameter("tint", src.albedo_color)
		m.set_shader_parameter("sway", sway)
		mats.append(m)
	return mats

func _ok_spot(p: Vector2, pad: float) -> bool:
	if abs(p.x) < 9 + pad and p.y > -150: return false
	if abs(p.y) < 8 + pad and abs(p.x) < 152: return false
	if p.length() < 20 + pad: return false
	if abs(p.length() - 194.0) < 7 + pad: return false
	if abs(p.y - 38) < 5 or abs(p.y - 71) < 5: return false
	if (abs(p.x - 67) < 5 or abs(p.x + 67) < 5) and abs(p.y) < 120: return false
	if abs(p.x) > CITY_HALF - 4 and abs(p.x) < CITY_HALF + 4: return false
	if abs(p.y) > CITY_HALF - 4 and abs(p.y) < CITY_HALF + 4: return false
	if Rect2(-132, 95, 44, 30).has_point(p): return false
	for d in DEFS:
		var c := Vector2(float(d[1]) * PK, float(d[2]) * PK)
		var r: float = 16.0 if BETH.has(d[0]) else max(float(d[5]), float(d[6])) * 0.75
		if p.distance_to(c) < r + pad: return false
	return true

func _scatter(path: String, count: int, area: float, minr: float, sway: float, smin: float, smax: float, shadow: bool) -> void:
	var parts := _first_mesh(path)
	var xf := []
	var tries := 0
	while xf.size() < count and tries < count * 40:
		tries += 1
		var p := Vector2(rng.randf_range(-area, area), rng.randf_range(-area, area))
		if p.length() < minr or not _ok_spot(p, 2.0): continue
		var s := rng.randf_range(smin, smax)
		xf.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(p.x, 0, p.y)))
	for part in parts:
		var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = part[0]; mm.instance_count = xf.size()
		for i in xf.size(): mm.set_instance_transform(i, xf[i] * part[1])
		var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm
		var mats := _wind_mats(part[0], sway)
		if mats.size() > 0: mmi.material_override = mats[0]
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mmi.visibility_range_end = 260.0
		add_child(mmi)
	if shadow:
		for t in xf:
			_static_box(t.origin + Vector3(0, 1.5, 0), Vector3(0.7, 3, 0.7))

func _foliage() -> void:
	_scatter("res://assets/trees/tree_oak_a_lod1.glb", 90, 175, 0, 0.05, 0.9, 1.3, true)
	_scatter("res://assets/trees/tree_oak_b_lod1.glb", 70, 175, 0, 0.05, 0.9, 1.3, true)
	_scatter("res://assets/trees/tree_birch_a_lod1.glb", 60, 175, 0, 0.07, 0.9, 1.2, true)
	_scatter("res://assets/trees/tree_apple_blossom_lod1.glb", 40, 120, 0, 0.05, 0.9, 1.1, true)
	_scatter("res://assets/trees/tree_oak_autumn_lod1.glb", 40, 175, 0, 0.05, 0.9, 1.3, true)
	_scatter("res://assets/trees/tree_pine_a_lod1.glb", 260, 420, 200, 0.03, 1.0, 1.6, false)
	_scatter("res://assets/veg/bush_a.glb", 160, 175, 0, 0.12, 0.8, 1.3, false)
	_scatter("res://assets/veg/bush_b.glb", 120, 175, 0, 0.12, 0.8, 1.3, false)
	_scatter("res://assets/veg/flowers_red.glb", 200, 160, 0, 0.25, 0.8, 1.2, false)
	_scatter("res://assets/veg/flowers_yellow.glb", 200, 160, 0, 0.25, 0.8, 1.2, false)
	_scatter("res://assets/veg/grass_a.glb", 500, 170, 0, 0.3, 0.8, 1.4, false)
	_scatter("res://assets/rocks/rock_mossy.glb", 40, 420, 190, 0.0, 1.0, 2.5, false)

func _props() -> void:
	var lamp := "res://assets/props/lamp_post.glb"
	for z in range(-140, 180, 24):
		for s in [-1, 1]: _place_glb(lamp, Vector3(s * 7.5, 0, z), 0.0)
	for x in range(-140, 141, 24):
		if abs(x) < 20: continue
		for s in [-1, 1]: _place_glb(lamp, Vector3(x, 0, s * 6.0), 0.0)
	var spots := [["barrel", Vector3(-55, 0, -12)], ["barrel", Vector3(-56, 0, -10)], ["crate", Vector3(-55, 0, -8)], ["cart", Vector3(-52, 0, 4)],
		["crate", Vector3(52, 0, 14)], ["barrel", Vector3(53, 0, 18)], ["cart", Vector3(-14, 0, 30)], ["barrel", Vector3(14, 0, 30)]]
	for s in spots:
		var g := _place_glb("res://assets/props/%s.glb" % s[0], s[1], rng.randf() * TAU)
		_static_box(s[1] + Vector3(0, 0.6, 0), Vector3(1.2, 1.2, 1.2))
	for i in 12:
		_place_glb("res://assets/props/fence_2m.glb", Vector3(-125 + i * 2.0, 0, -120), 0.0)

# ---------- hero + Pip ----------
func _limb(parent: Node3D, mesh: Mesh, mat: Material, pos: Vector3) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); mi.mesh = mesh; mi.material_override = mat; mi.position = pos; parent.add_child(mi); return mi

func _hero() -> void:
	hero = CharacterBody3D.new(); hero.position = Vector3(-25, 0.1, 30)
	var cs := CollisionShape3D.new(); var cap := CapsuleShape3D.new(); cap.height = 1.905; cap.radius = 0.32; cs.shape = cap; cs.position.y = 1.905 / 2
	hero.add_child(cs); add_child(hero)
	hero_vis = Node3D.new(); hero.add_child(hero_vis)
	var skin := _mat(Color(0.86, 0.68, 0.55), 0.6); var tunic := _mat(Color(0.45, 0.12, 0.14), 0.7); var dark := _mat(Color(0.15, 0.13, 0.12)); var gold := _mat(Color(0.85, 0.65, 0.2), 0.3)
	gold.metallic = 0.8
	# proportions sum to 1.905 m: legs 0.95, torso 0.62, neck+head 0.335
	var leg := CapsuleMesh.new(); leg.radius = 0.11; leg.height = 0.95
	var arm := CapsuleMesh.new(); arm.radius = 0.08; arm.height = 0.72
	var torso := CapsuleMesh.new(); torso.radius = 0.24; torso.height = 0.72
	var head := SphereMesh.new(); head.radius = 0.13; head.height = 0.27
	for s in [-1, 1]:
		var hip := Node3D.new(); hip.position = Vector3(s * 0.12, 0.95, 0); hero_vis.add_child(hip)
		_limb(hip, leg, dark, Vector3(0, -0.475, 0)); limbs.append([hip, s])
		var sh := Node3D.new(); sh.position = Vector3(s * 0.31, 1.48, 0); hero_vis.add_child(sh)
		_limb(sh, arm, tunic, Vector3(0, -0.34, 0)); limbs.append([sh, -s])
	_limb(hero_vis, torso, tunic, Vector3(0, 1.27, 0))
	_limb(hero_vis, head, skin, Vector3(0, 1.775, 0))
	var crown := CylinderMesh.new(); crown.top_radius = 0.12; crown.bottom_radius = 0.13; crown.height = 0.05
	_limb(hero_vis, crown, gold, Vector3(0, 1.88, 0))
	var cape := BoxMesh.new(); cape.size = Vector3(0.5, 0.9, 0.04)
	_limb(hero_vis, cape, _mat(Color(0.1, 0.15, 0.35)), Vector3(0, 1.1, 0.26))
	# Pip companion, 0.52 m tall
	pip = Node3D.new(); pip.position = hero.position + Vector3(1.2, 0, 1.2); add_child(pip)
	var fur := _mat(Color(0.95, 0.78, 0.25), 0.8)
	var pb := SphereMesh.new(); pb.radius = 0.17; pb.height = 0.3; _limb(pip, pb, fur, Vector3(0, 0.2, 0))
	var ph := SphereMesh.new(); ph.radius = 0.12; ph.height = 0.22; _limb(pip, ph, fur, Vector3(0, 0.38, -0.04))
	var ear := PrismMesh.new(); ear.size = Vector3(0.05, 0.13, 0.03)
	_limb(pip, ear, dark, Vector3(-0.07, 0.52 - 0.065, -0.04)); _limb(pip, ear, dark, Vector3(0.07, 0.52 - 0.065, -0.04))
	# camera
	cam_pivot = Node3D.new(); add_child(cam_pivot)
	cam_arm = SpringArm3D.new(); cam_arm.spring_length = 6.0; cam_arm.margin = 0.3
	var sph := SphereShape3D.new(); sph.radius = 0.25; cam_arm.shape = sph
	cam_arm.add_excluded_object(hero.get_rid())
	cam_pivot.add_child(cam_arm)
	cam = Camera3D.new(); cam.fov = 62; cam.far = 600; cam_arm.add_child(cam); cam.current = true

func _hud() -> void:
	var cl := CanvasLayer.new(); add_child(cl)
	hud_label = Label.new(); hud_label.position = Vector2(12, 8); hud_label.add_theme_font_size_override("font_size", 22)
	hud_label.add_theme_color_override("font_outline_color", Color.BLACK); hud_label.add_theme_constant_override("outline_size", 6); cl.add_child(hud_label)
	where_label = Label.new(); where_label.position = Vector2(500, 20); where_label.add_theme_font_size_override("font_size", 30)
	where_label.add_theme_color_override("font_outline_color", Color.BLACK); where_label.add_theme_constant_override("outline_size", 8); cl.add_child(where_label)
	joy_base = Panel.new(); joy_base.size = Vector2(220, 220); joy_base.position = Vector2(60, 460)
	var sb := StyleBoxFlat.new(); sb.bg_color = Color(1, 1, 1, 0.15); sb.set_corner_radius_all(110); sb.border_color = Color(1, 1, 1, 0.5); sb.set_border_width_all(3)
	joy_base.add_theme_stylebox_override("panel", sb); joy_base.mouse_filter = Control.MOUSE_FILTER_IGNORE; cl.add_child(joy_base)
	joy_knob = Panel.new(); joy_knob.size = Vector2(90, 90)
	var kb := StyleBoxFlat.new(); kb.bg_color = Color(1, 1, 1, 0.55); kb.set_corner_radius_all(45)
	joy_knob.add_theme_stylebox_override("panel", kb); joy_knob.mouse_filter = Control.MOUSE_FILTER_IGNORE; joy_base.add_child(joy_knob)
	joy_knob.position = Vector2(65, 65)
	joy_center = joy_base.position + Vector2(110, 110)

func _input(e: InputEvent) -> void:
	var vw := get_viewport().get_visible_rect().size
	if e is InputEventScreenTouch:
		if e.pressed:
			if e.position.x < vw.x * 0.45 and joy_touch == -1:
				joy_touch = e.index; joy_center = e.position
				joy_base.position = joy_center - Vector2(110, 110); _joy(e.position)
			elif cam_touch == -1: cam_touch = e.index
		else:
			if e.index == joy_touch: joy_touch = -1; joy_vec = Vector2.ZERO; joy_knob.position = Vector2(65, 65)
			if e.index == cam_touch: cam_touch = -1
	elif e is InputEventScreenDrag:
		if e.index == joy_touch: _joy(e.position)
		elif e.index == cam_touch:
			yaw -= e.relative.x * 0.006; pitch = clamp(pitch - e.relative.y * 0.004, -1.2, 0.35)

func _joy(p: Vector2) -> void:
	var d := (p - joy_center).limit_length(100.0)
	joy_vec = d / 100.0; joy_knob.position = Vector2(65, 65) + d

func _physics_process(dt: float) -> void:
	if hero == null: return
	var inp := joy_vec
	var k := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if k.length() > 0.1: inp = k
	var fwd := Vector3(-sin(yaw), 0, -cos(yaw)); var right := Vector3(cos(yaw), 0, -sin(yaw))
	var dir := right * inp.x + fwd * -inp.y
	var speed: float = 6.0 * clamp(inp.length(), 0.0, 1.0)
	if dir.length() > 0.05: dir = dir.normalized()
	hero.velocity.x = dir.x * speed; hero.velocity.z = dir.z * speed
	hero.velocity.y = 0.0 if hero.is_on_floor() else hero.velocity.y - 20.0 * dt
	hero.move_and_slide()
	if speed > 0.1:
		hero_vis.rotation.y = lerp_angle(hero_vis.rotation.y, atan2(-dir.x, -dir.z), 10 * dt)
		walk_t += dt * speed * 1.6
	else: walk_t = lerp(walk_t, round(walk_t / PI) * PI, 8 * dt)
	for l in limbs: l[0].rotation.x = sin(walk_t) * 0.6 * l[1]
	# Pip follows behind, hopping
	var tgt := hero.position + hero_vis.global_transform.basis.z * 1.3 + hero_vis.global_transform.basis.x * 0.7
	var dp := tgt - pip.position; dp.y = 0
	if dp.length() > 0.3:
		pip.position += dp * min(1.0, 4.0 * dt)
		pip.rotation.y = lerp_angle(pip.rotation.y, atan2(-dp.x, -dp.z), 8 * dt)
		pip.position.y = abs(sin(Time.get_ticks_msec() * 0.012)) * 0.12
	else: pip.position.y = 0.0

func _process(dt: float) -> void:
	if hero == null: return
	cam_pivot.position = hero.position + Vector3(0, 1.7, 0)
	cam_pivot.rotation = Vector3(pitch, yaw, 0)
	if blades: blades.rotate_object_local(Vector3(0, 0, 1), dt * 0.8)
	var inside := ""
	for b in buildings:
		var lp: Vector3 = b.node.global_transform.affine_inverse() * hero.global_position
		var a: AABB = b.aabb.grow(-0.6)
		var ins: bool = lp.x > a.position.x and lp.x < a.end.x and lp.z > a.position.z and lp.z < a.end.z
		if b.roof: b.roof.visible = not ins
		if ins: inside = b.name
	cam_arm.spring_length = 3.5 if inside != "" else 6.0
	where_label.text = inside
	hud_label.text = "Varnethryl Godot test 1  |  FPS %d  |  draw calls %d  |  prims %dk" % [Engine.get_frames_per_second(),
		Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000)]

# ---------- headless bench / screenshots ----------
func _shot(name: String, pos: Vector3, yw: float, pt: float, frames := 40) -> void:
	hero.position = pos; yaw = yw; pitch = pt
	pip.position = pos + Vector3(1, 0, 1)
	for i in frames: await get_tree().process_frame
	var t0 := Time.get_ticks_usec(); var n := 30
	var dc := 0.0
	for i in n:
		await get_tree().process_frame
		dc += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	var ms := (Time.get_ticks_usec() - t0) / 1000.0 / n
	print("BENCH %s draw_calls=%d frame_ms_cpu_sw=%.1f prims=%d objects=%d" % [name, int(dc / n), ms,
		Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)])
	var img := get_viewport().get_texture().get_image()
	img.save_png("user://shot_%s.png" % name)

func _run_bench() -> void:
	await get_tree().create_timer(0.5).timeout
	await _shot("1_plaza", Vector3(-6, 0.1, 22), 0.25, -0.3)
	await _shot("2_houses", Vector3(0, 0.1, 40), PI * 0.82, -0.25)
	await _shot("3_inside_house1", Vector3(-25.2, 0.1, 52), PI * 0.1, -0.55)
	await _shot("4_gate", Vector3(0, 0.1, 160), 0.0, -0.15)
	await _shot("5_windmill", Vector3(40, 0.1, 110), 0.6, -0.2)
	get_tree().quit()
