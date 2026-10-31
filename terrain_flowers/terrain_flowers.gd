class_name TerrainFlowers
extends RefCounted
## Beth: wildflowers for VARNETHRYL. Drop-in: TerrainFlowers.build(main) once after _grass(), and
## TerrainFlowers.apply_tier(main.tier) at the end of apply_quality(). Everything lives under one Node3D "Wildflowers".
## Eight original species (see terrain_flowers.gdshader), placed by zone:
##   meadow patches in the open country, roadside verges on the outskirt dirt roads, farmstead verges,
##   cottage / house garden strips in town, lake + pond shores.
## Never on: streets/roads/door spurs/plaza/ring road (main._ok_spot), inside buildings, the harbour district + coast,
## the volcano pad, ash and lava, rock slopes, above the tree line / snow, the farm field beds.
const SHADER := "res://terrain_flowers/terrain_flowers.gdshader"
const CHUNK := 48.0
# per tier [Low, Medium, High, Ultra]: share of instances drawn, lod0 range end, lod1 range end
const SHARE := [0.22, 0.45, 1.0, 1.0]
const LOD0_END := [0.0, 0.0, 32.0, 45.0]
const LOD1_END := [38.0, 55.0, 75.0, 95.0]
enum { SUNPENNY, SKYGLASS, HEARTHPOPPY, DUSKTHISTLE, EMBERBELL, MARSHLANTERN, ROSEBUTTON, REEDBELL }
const ZONE_SPECIES := {
	"meadow": [SUNPENNY, SUNPENNY, SKYGLASS, HEARTHPOPPY, DUSKTHISTLE, SKYGLASS],
	"road": [SUNPENNY, EMBERBELL, DUSKTHISTLE, SUNPENNY],
	"farm": [HEARTHPOPPY, ROSEBUTTON, SUNPENNY, EMBERBELL],
	"garden": [ROSEBUTTON, HEARTHPOPPY, EMBERBELL, SKYGLASS, SUNPENNY],
	"water": [MARSHLANTERN, MARSHLANTERN, REEDBELL, SKYGLASS]}
static var root: Node3D
static var lod0: Array = []
static var lod1: Array = []
static var mats: Array = []   # [lod0 mat, lod1 mat]
static var stats := {}

static func _card(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, part: float) -> void:
	# a b bottom-left/right, c d top-right/left
	var uv := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)]; var v := [a, b, c, d]
	var n := (b - a).cross(d - a).normalized()
	for i in [0, 1, 2, 0, 2, 3]:
		st.set_uv(uv[i]); st.set_uv2(Vector2(part, 0)); st.set_normal(n); st.add_vertex(v[i])

static func make_mesh(lod: int) -> ArrayMesh:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var W := 0.17; var H := 1.0; var hs := 0.2
	var stems := 2 if lod == 0 else 1
	for k in stems:
		var a := k * PI / 2.0; var dx := cos(a) * W; var dz := sin(a) * W
		_card(st, Vector3(-dx, 0, -dz), Vector3(dx, 0, dz), Vector3(dx, H, dz), Vector3(-dx, H, -dz), 0.0)
	var heads := 2 if lod == 0 else 1
	for k in heads:
		var yaw := k * PI / 2.0 + 0.4; var tilt := 0.45
		var bs := Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, -PI / 2 + tilt)
		var o := Vector3(0, H * 0.97, 0)
		_card(st, o + bs * Vector3(-hs, -hs, 0), o + bs * Vector3(hs, -hs, 0), o + bs * Vector3(hs, hs, 0), o + bs * Vector3(-hs, hs, 0), 1.0)
	var m := st.commit(); m.custom_aabb = AABB(Vector3(-0.4, 0, -0.4), Vector3(0.8, 1.3, 0.8)); return m

## zone + density (instances per m2) at p, or ["", 0]
static func _zone(main: Node, p: Vector2, mask: FastNoiseLite) -> Array:
	var r := p.length()
	var ld: float = p.distance_to(main.LAKE)
	if ld > 44.0 and ld < 62.0: return ["water", 0.8 * (1.0 - smoothstep(54.0, 62.0, ld))]
	var pd: float = p.distance_to(Vector2(main.POND.x, main.POND.z))
	if pd > 18.5 and pd < 26.0: return ["water", 0.8]
	if r < 192.0:   # inside the walls: only garden strips 1.5-6 m off a house / shop
		var near := 1e9
		for b in main.buildings: near = minf(near, _rect_dist(b.rect, p))
		for f in main.fillers: if f.has("rect"): near = minf(near, _rect_dist(f.rect, p))
		if near > 1.5 and near < 5.5: return ["garden", 0.9]
		return ["", 0.0]
	var fd: float = p.distance_to(main.FARM)
	if fd < 80.0:
		var lx: float = p.x - main.FARM.x - 34.0
		if absf(lx) < 13.5 and absf(p.y - main.FARM.y) < 29.0: return ["", 0.0]   # crop + wheat beds and their fences
		if fd > 22.0: return ["farm", 0.8 * (0.5 + 0.5 * smoothstep(0.35, 0.6, mask.get_noise_2d(p.x * 2.0, p.y * 2.0) * 0.5 + 0.5))]
		return ["", 0.0]
	if r > 215.0 and r < 600.0:
		var rd: float = main._road_dist(p)
		if rd > 8.5 and rd < 14.0: return ["road", 0.65 * (0.6 + 0.4 * (mask.get_noise_2d(p.x * 3.0, p.y * 3.0) * 0.5 + 0.5))]
		var m := mask.get_noise_2d(p.x, p.y) * 0.5 + 0.5
		if m > 0.58: return ["meadow", 1.0 * smoothstep(0.58, 0.68, m) * (1.0 - smoothstep(500.0, 600.0, r))]
	return ["", 0.0]

static func _rect_dist(rc: Rect2, p: Vector2) -> float:
	var dx := maxf(maxf(rc.position.x - p.x, p.x - rc.end.x), 0.0); var dy := maxf(maxf(rc.position.y - p.y, p.y - rc.end.y), 0.0)
	return Vector2(dx, dy).length() if (dx > 0.0 or dy > 0.0) else -1.0

static func _banned(main: Node, p: Vector2) -> bool:
	if p.distance_to(main.VOLC) < 235.0: return true                 # volcano pad, ash + lava
	if main.near_port(p, 40.0): return true                         # harbour quay + district
	if HarborDistrict.pad_weight(p.x, p.y) > 0.05: return true
	if main.sea_mask(p.x, p.y) > 0.0 or (p.x < main.SEA_COAST_X + 25.0 and p.y > main.SEA_NORTH_Z - 25.0): return true   # beach / sea
	if not main._ok_spot(p, 0.4): return true                        # streets, roads, plaza, gates, walls, buildings, trees
	return false

const BAKE := "res://terrain_flowers/flowers_bake.bin"
## Fast path for the phone: load the baked chunk buffers (made on the box with bake_to()) instead of sampling the
## terrain at startup (~13 s of GDScript on the box). Falls back to build() if the bake is missing.
static func build(main: Node, seed_ := 4242) -> void:
	if OS.get_environment("TF_REBUILD") == "" and FileAccess.file_exists(BAKE):
		var f := FileAccess.open(BAKE, FileAccess.READ); var data: Dictionary = f.get_var(); f.close()
		_make_nodes(main, data.chunks, data.stats); return
	_sample(main, seed_)

static func bake_to(path: String) -> void:
	var chunks := {}
	for mmi in lod0: chunks[mmi.get_meta("key")] = mmi.multimesh.buffer
	var f := FileAccess.open(path, FileAccess.WRITE); f.store_var({"chunks": chunks, "stats": stats}); f.close()

static func _make_nodes(main: Node, chunks: Dictionary, st: Dictionary) -> void:
	var t0 := Time.get_ticks_msec()
	root = Node3D.new(); root.name = "Wildflowers"; main.add_child(root)
	lod0.clear(); lod1.clear(); mats.clear()
	var shader: Shader = load(SHADER)
	for k in 2:
		var mt := ShaderMaterial.new(); mt.shader = shader; mats.append(mt)
	var meshes := [make_mesh(0), make_mesh(1)]
	for k in 2: meshes[k].surface_set_material(0, mats[k])
	for key in chunks:
		var buf: PackedFloat32Array = chunks[key]
		for lod in 2:
			var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.use_custom_data = true
			mm.mesh = meshes[lod]; mm.instance_count = buf.size() / 16; mm.buffer = buf
			var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm; mmi.name = "fl_%d_%d_l%d" % [key.x, key.y, lod]; mmi.set_meta("key", key)
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mmi.visibility_range_end_margin = 6.0; mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
			root.add_child(mmi); (lod0 if lod == 0 else lod1).append(mmi)
	stats = st.duplicate(); stats["load_ms"] = Time.get_ticks_msec() - t0
	print("FLOWERS ", stats)

static func _sample(main: Node, seed_: int) -> void:
	var t0 := Time.get_ticks_msec()
	root = Node3D.new(); root.name = "Wildflowers"; main.add_child(root)
	lod0.clear(); lod1.clear(); mats.clear()
	var mask := FastNoiseLite.new(); mask.seed = 91; mask.frequency = 0.012; mask.fractal_octaves = 2
	var rng := RandomNumberGenerator.new(); rng.seed = seed_
	var shader: Shader = load(SHADER)
	for k in 2:
		var mt := ShaderMaterial.new(); mt.shader = shader; mats.append(mt)
	var meshes := [make_mesh(0), make_mesh(1)]
	for k in 2: meshes[k].surface_set_material(0, mats[k])
	var chunks := {}   # Vector2i -> [xf, custom]
	var counts := {}
	var R := 600.0; var cell := 2.0   # jittered grid sample, then density test
	var n := int(2.0 * R / cell)
	for j in n:
		for i in n:
			var p := Vector2(-R + (i + rng.randf()) * cell, -R + (j + rng.randf()) * cell)
			if p.length() > R: continue
			var z := _zone(main, p, mask)
			var dens: float = z[1]
			if dens <= 0.0: continue
			# clumps: dens is per m2, a cell is 4 m2, each accepted cell drops a clump of 1-4 flowers of one species
			if rng.randf() > dens * cell * cell / 2.5: continue
			if _banned(main, p): continue
			var y: float = main.height(p.x, p.y)
			if y > 60.0: continue                                   # rock / snow above the meadows
			var gx: float = main.height(p.x + 1.5, p.y) - y; var gz: float = main.height(p.x, p.y + 1.5) - y
			if Vector2(gx, gz).length() / 1.5 > 0.45: continue       # steep: ground shader turns to rock
			var list: Array = ZONE_SPECIES[z[0]]
			var sp: int = list[rng.randi() % list.size()]
			var nclump := rng.randi_range(3, 7)
			for c in nclump:
				var q := p + Vector2(rng.randf_range(-0.9, 0.9), rng.randf_range(-0.9, 0.9))
				var hgt := rng.randf_range(0.38, 0.62) * (1.25 if sp == REEDBELL else 1.0)
				var s := rng.randf_range(0.85, 1.15)
				var b := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, hgt, s))
				var key := Vector2i(floori(q.x / CHUNK), floori(q.y / CHUNK))
				if not chunks.has(key): chunks[key] = []
				chunks[key].append([Transform3D(b, Vector3(q.x, y - 0.02 + (gx * (q.x - p.x) + gz * (q.y - p.y)) / 1.5, q.y)), Color(sp / 8.0, s, rng.randf(), rng.randf())])
				counts[z[0]] = counts.get(z[0], 0) + 1
	var total := 0
	for key in chunks:
		var arr: Array = chunks[key]
		# shuffle so a tier's visible_instance_count takes an even random subset (Low = sparse, not a cut-off patch)
		for i in range(arr.size() - 1, 0, -1):
			var k := rng.randi() % (i + 1); var tmp = arr[i]; arr[i] = arr[k]; arr[k] = tmp
		for lod in 2:
			var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.use_custom_data = true
			mm.mesh = meshes[lod]; mm.instance_count = arr.size()
			for i in arr.size(): mm.set_instance_transform(i, arr[i][0]); mm.set_instance_custom_data(i, arr[i][1])
			var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm; mmi.name = "fl_%d_%d_l%d" % [key.x, key.y, lod]; mmi.set_meta("key", key)
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mmi.visibility_range_end_margin = 6.0; mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
			root.add_child(mmi); (lod0 if lod == 0 else lod1).append(mmi)
		total += arr.size()
	stats = {"instances": total, "chunks": chunks.size(), "zones": counts, "build_ms": Time.get_ticks_msec() - t0,
		"tris_lod0": meshes[0].get_faces().size() / 3, "tris_lod1": meshes[1].get_faces().size() / 3}
	print("FLOWERS ", stats)

static func apply_tier(tier: int) -> void:
	if root == null: return
	var e0: float = LOD0_END[tier]; var e1: float = LOD1_END[tier]
	for mmi in lod0:
		var cap := int(mmi.multimesh.instance_count * SHARE[tier])
		mmi.multimesh.visible_instance_count = cap
		mmi.visible = e0 > 0.0 and cap > 0
		mmi.visibility_range_end = e0 + 6.0
	for mmi in lod1:
		var cap := int(mmi.multimesh.instance_count * SHARE[tier])
		mmi.multimesh.visible_instance_count = cap
		mmi.visible = cap > 0
		mmi.visibility_range_begin = maxf(e0 - 12.0, 0.0)   # chunk-level; the per-flower swap is the shader cross-fade
		mmi.visibility_range_end = e1 + 6.0
	# lod0 shrinks out over [e0-6, e0], lod1 grows in over the same band, then fades out at its own range end
	if e0 > 0.0:
		mats[0].set_shader_parameter("fade_start", e0 - 6.0); mats[0].set_shader_parameter("fade_end", e0)
		mats[1].set_shader_parameter("near_cut", e0)
	else:
		mats[1].set_shader_parameter("near_cut", 0.0)
	mats[1].set_shader_parameter("fade_start", e1 - 12.0); mats[1].set_shader_parameter("fade_end", e1)
	mats[1].set_shader_parameter("wind_strength", 1.0 if tier >= 1 else 0.6)
