class_name InteriorKit
## Materials + props for interiors. Props load Beth's kit by file name from res://interiors/kit/<name>.glb
## (copied from /workspace/godot-art/interiors: only props the defs use, Medium, textures VRAM-compressed and capped at 512; re-run tools/sync_kit.py after
## a new pass). Phones load Medium (_lod1) by default; set InteriorKit.lod = 0 for High. Unknown names
## fall back to a block-out box so a def never breaks while a prop is missing.
const KIT := "res://interiors/kit/"
const TEX := "res://interiors/tex/"
const LAYER := 1 << 19          # interior render layer (sun excludes it)
static var lod := 1   # Medium ships (APK size); tools/sync_kit.py --high adds High for desktop
static var _index := {}
static var _mats := {}
static var _scenes := {}

static func index() -> Dictionary:
	if _index.is_empty():
		var f := FileAccess.open(KIT + "index.json", FileAccess.READ)
		if f: _index = JSON.parse_string(f.get_as_text()).get("props", {})
	return _index

static func mat(kind: String) -> Material:
	if _mats.has(kind): return _mats[kind]
	var m := StandardMaterial3D.new()
	var T := {"oak": ["oak", Color(1, 0.92, 0.85), 1.2], "darkoak": ["oak", Color(0.55, 0.42, 0.33), 1.2],
		"stone": ["fieldstone", Color(0.95, 0.93, 0.9), 1.1], "flag": ["cobblestone", Color(0.95, 0.93, 0.9), 1.0],
		"palestone": ["cobblestone", Color(1.0, 0.97, 0.9), 1.0], "plaster": ["plaster_timber", Color(1, 0.97, 0.92), 2.4],
		"slate": ["slate", Color(0.7, 0.75, 0.85), 1.0]}
	match kind:
		"blue": m.albedo_color = Color("1f3a63")
		"bluetile": m.albedo_color = Color("2f4f86"); m.roughness = 0.6
		"gold": m.albedo_color = Color("c8a240"); m.metallic = 0.8; m.roughness = 0.35
		"iron": m.albedo_color = Color(0.13, 0.13, 0.14); m.metallic = 0.7; m.roughness = 0.5
		"flame": m.albedo_color = Color(1, 0.6, 0.25); m.emission_enabled = true; m.emission = Color(1, 0.55, 0.2); m.emission_energy_multiplier = 1.4; m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		"glass": m.albedo_color = Color(0.7, 0.75, 0.8); m.emission_enabled = true; m.emission = Color(0.75, 0.8, 0.85); m.emission_energy_multiplier = 0.45
		"stained": m.albedo_color = Color(0.25, 0.42, 0.9); m.emission_enabled = true; m.emission = Color(0.25, 0.45, 1.0); m.emission_energy_multiplier = 0.8
		"water": m.albedo_color = Color(0.3, 0.55, 0.75); m.roughness = 0.05; m.metallic = 0.3
		"void": m.albedo_color = Color(0.03, 0.025, 0.02); m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; m.cull_mode = BaseMaterial3D.CULL_FRONT
		"outline": m.albedo_color = Color(0.85, 0.72, 0.5); m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED   # < glow threshold: no glow
		"checker", "bluecheck":
			var img := Image.create(2, 2, false, Image.FORMAT_RGB8)
			var a := Color("e6dcc6") if kind == "checker" else Color("3d5f97"); var b := Color("1e3a6a") if kind == "checker" else Color("6d859c")
			img.set_pixel(0, 0, a); img.set_pixel(1, 1, a); img.set_pixel(1, 0, b); img.set_pixel(0, 1, b)
			m.albedo_texture = ImageTexture.create_from_image(img); m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
			m.uv1_triplanar = true; m.uv1_world_triplanar = true; m.uv1_scale = Vector3.ONE / (2.4 if kind == "checker" else 0.7); m.roughness = 0.45
		"red": m.albedo_color = Color(0.45, 0.12, 0.1)
		"sand": m.albedo_color = Color(0.86, 0.74, 0.52); m.roughness = 1.0
		"bread": m.albedo_color = Color(0.78, 0.52, 0.25); m.roughness = 0.8
		"banner":
			m.albedo_texture = load(TEX + "banner_lion_albedo.jpg"); m.cull_mode = BaseMaterial3D.CULL_DISABLED
		_:
			var t: Array = T.get(kind, T.stone)
			m.albedo_texture = load(TEX + t[0] + "_albedo.jpg"); m.albedo_color = t[1]
			m.normal_enabled = true; m.normal_texture = load(TEX + t[0] + "_normal.png"); m.normal_scale = 0.5
			m.uv1_triplanar = true; m.uv1_world_triplanar = true; m.uv1_scale = Vector3.ONE / t[2]
			m.roughness = 0.85
	_mats[kind] = m
	return m

static func box(parent: Node3D, pos: Vector3, size: Vector3, kind: String, collide := true, rot := 0.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = size; mi.mesh = bm
	mi.material_override = mat(kind); mi.position = pos; mi.rotation.y = rot; mi.layers = LAYER
	parent.add_child(mi)
	if collide:
		var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var sh := BoxShape3D.new(); sh.size = size
		cs.shape = sh; sb.add_child(cs); mi.add_child(sb)
	return mi

static func set_layers(n: Node, shadow := true) -> void:
	if n is VisualInstance3D: n.layers = LAYER
	if n is GeometryInstance3D: n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for c in n.get_children(): set_layers(c, shadow)

## test 13 (boss: gold piles were smooth green-gold blobs): a heap of individual coins. A dark-gold mound core
## (squashed sphere) under ~420 tilted coins (one MultiMesh, 1 draw call) heaped densest at the centre.
static var _coin_mm: Mesh
static func _coin_heap(root: Node3D, sz: Array) -> void:
	var rx: float = sz[0] * 0.5; var rz: float = sz[2] * 0.5; var h: float = sz[1]
	var core := MeshInstance3D.new(); var sm := SphereMesh.new(); sm.radius = 1.0; sm.height = 2.0; sm.radial_segments = 16; sm.rings = 8; core.mesh = sm
	var cm := StandardMaterial3D.new(); cm.albedo_color = Color(0.62, 0.45, 0.12); cm.metallic = 0.7; cm.roughness = 0.5; core.material_override = cm
	core.scale = Vector3(rx * 0.92, h * 0.9, rz * 0.92); core.position.y = -h * 0.12; core.layers = LAYER; root.add_child(core)
	if _coin_mm == null:
		var cy := CylinderMesh.new(); cy.top_radius = 0.038; cy.bottom_radius = 0.038; cy.height = 0.009; cy.radial_segments = 10; cy.rings = 0
		var gm := StandardMaterial3D.new(); gm.albedo_color = Color(0.95, 0.74, 0.25); gm.metallic = 0.9; gm.roughness = 0.28
		cy.material = gm; _coin_mm = cy
	var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = _coin_mm; mm.instance_count = 420
	var rng := RandomNumberGenerator.new(); rng.seed = hash(root.position)
	for i in mm.instance_count:
		var r := sqrt(rng.randf()); var a := rng.randf() * TAU
		var x := cos(a) * r * rx; var z := sin(a) * r * rz
		var y := h * 0.78 * maxf(0.0, 1.0 - r * r) + 0.005 + rng.randf() * 0.02
		var b := Basis(Vector3.UP, rng.randf() * TAU) * Basis(Vector3.RIGHT, rng.randf_range(-0.6, 0.6) + (r * 0.5))
		mm.set_instance_transform(i, Transform3D(b, Vector3(x, y, z)))
	var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm; mmi.layers = LAYER; mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; root.add_child(mmi)

## Place prop `name` (kit file name). rot in degrees; kit props face +Z (front) at origin = floor centre.
static func prop(parent: Node3D, name: String, pos: Vector3, rot_deg := 0.0, collide := true) -> Node3D:
	var root := Node3D.new(); root.name = name; root.position = pos; root.rotation.y = deg_to_rad(rot_deg)
	parent.add_child(root)
	var info: Dictionary = index().get(name, {})
	var path := KIT + name + ("_lod1" if lod == 1 else "") + ".glb"
	if not ResourceLoader.exists(path): path = KIT + name + ".glb"
	if name == "gold_pile":
		_coin_heap(root, info.get("size_m", [1.0, 0.45, 1.0]))
	elif ResourceLoader.exists(path):
		if not _scenes.has(name): _scenes[name] = load(path)
		var v: Node3D = _scenes[name].instantiate(); root.add_child(v)
		set_layers(v, info.get("size_m", [1, 1, 1])[1] > 0.5)
	else:
		var s: Array = info.get("size_m", [0.8, 0.8, 0.8])
		box(root, Vector3(0, s[1] / 2.0, 0), Vector3(s[0], s[1], s[2]), "darkoak", false)
	if collide and name == "gold_pile":   # test 13: a low walkable coin mound, never a trap wall
		var gsb := StaticBody3D.new(); var gcs := CollisionShape3D.new(); var gsh := CylinderShape3D.new()
		gsh.radius = 0.5; gsh.height = 0.12; gcs.shape = gsh; gcs.position.y = 0.06; gsb.add_child(gcs); root.add_child(gsb)
	elif collide and info.has("collision_box"):
		var cb: Dictionary = info.collision_box
		var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var sh := BoxShape3D.new()
		sh.size = Vector3(cb.extents[0], cb.extents[1], cb.extents[2]); cs.shape = sh
		cs.position = Vector3(cb.center[0], cb.center[1], cb.center[2]); sb.add_child(cs); root.add_child(sb)
	return root
