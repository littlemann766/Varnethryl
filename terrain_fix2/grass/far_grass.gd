class_name FarGrass
extends Node3D
## Beth terrain_fix2: grass from the edge of main._grass() (+-210 m) out to the map edge.
## A 4 x 4 grid of 48 m blocks around the camera (inner 2 x 2 = lod0 6-tri clumps, outer 12 = lod1 2-tri cards), all
## sharing ONE periodic 48 m pattern, so moving the grid by whole blocks is invisible. Heights + density are read in the
## shader from the baked textures. Blocks wholly inside the town grass square are hidden (no wasted draws in town).
## Drop-in: add_child(FarGrass.new()) once after _grass(); FarGrass.apply_tier(tier) from apply_quality().
const DATA := "res://terrain_fix2/data/"
const B := 48.0
const PER_BLOCK := [3000, 1500]   # clumps per block for lod0 / lod1 pattern (lod1 cards are wider, so half as many)
# [Low, Medium, High, Ultra]: [density, lod0 end (0 = no lod0), far end, grid half-size in blocks]
const TIER := [[0.35, 0.0, 32.0, 1], [0.6, 0.0, 50.0, 2], [1.0, 30.0, 70.0, 2], [1.0, 40.0, 72.0, 2]]
static var me: FarGrass
var blocks := []       # [mmi, ix, iz, lod]
var mats := []
var cur := Vector2i(999999, 0)
var tier_i := 2
static func apply_tier(t: int) -> void:
	if me: me._apply(t)
func _clump(lod: int) -> ArrayMesh:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var k_n := 3 if lod == 0 else 1
	for k in k_n:
		var a := k * PI / 3.0 + 0.3; var w := 0.09 if lod == 0 else 0.12
		var dx := cos(a) * w; var dz := sin(a) * w; var h := 0.42 if lod == 0 else 0.36
		var v := [Vector3(-dx, 0, -dz), Vector3(dx, 0, dz), Vector3(dx * 0.15, h, dz * 0.15), Vector3(-dx * 0.15, h, -dz * 0.15)]
		var uv := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)]
		for idx in [0, 1, 2, 0, 2, 3]: st.set_uv(uv[idx]); st.add_vertex(v[idx])
	var m := st.commit(); m.custom_aabb = AABB(Vector3(-B / 2, -20, -B / 2), Vector3(B, 520, B)); return m
func _ready() -> void:
	me = self; name = "FarGrass"
	var sh: Shader = load("res://terrain_fix2/grass/far_grass.gdshader")
	var th: Texture2D = load(DATA + "terrain_h.png"); var td: Texture2D = load(DATA + "terrain_d.png")
	var rng := RandomNumberGenerator.new(); rng.seed = 77
	var mms := []
	for lod in 2:
		var mt := ShaderMaterial.new(); mt.shader = sh; mt.set_shader_parameter("t_h", th); mt.set_shader_parameter("t_data", td); mats.append(mt)
		var mesh := _clump(lod); mesh.surface_set_material(0, mt)
		var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = mesh; mm.instance_count = PER_BLOCK[lod]
		for i in PER_BLOCK[lod]:
			var s := rng.randf_range(0.8, 1.3)
			mm.set_instance_transform(i, Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.8, 1.5), s)),
				Vector3(rng.randf_range(-B / 2, B / 2), 0, rng.randf_range(-B / 2, B / 2))))
		mms.append(mm)
	for iz in range(-2, 2):
		for ix in range(-2, 2):
			var inner := (ix == -1 or ix == 0) and (iz == -1 or iz == 0)
			var lods := [0, 1] if inner else [1]
			for lod in lods:
				var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mms[lod]; mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				add_child(mmi); blocks.append([mmi, ix, iz, lod])
	_apply(tier_i)
func _apply(t: int) -> void:
	tier_i = t; var cfg: Array = TIER[t]
	mats[0].set_shader_parameter("density", cfg[0]); mats[1].set_shader_parameter("density", cfg[0])
	mats[0].set_shader_parameter("fade_start", cfg[1] - 6.0); mats[0].set_shader_parameter("fade_end", cfg[1])
	mats[1].set_shader_parameter("near_cut", cfg[1]); mats[1].set_shader_parameter("fade_start", cfg[2] - 14.0); mats[1].set_shader_parameter("fade_end", cfg[2])
	cur = Vector2i(999999, 0)
func _process(_dt: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam == null: return
	var cp := cam.global_position
	var c := Vector2i(roundi(cp.x / B), roundi(cp.z / B))
	if c == cur: return
	cur = c
	var cfg: Array = TIER[tier_i]; var half: int = cfg[3]
	for b in blocks:
		var mmi: MultiMeshInstance3D = b[0]; var ix: int = b[1]; var iz: int = b[2]; var lod: int = b[3]
		var ctr := Vector2((c.x + ix + 0.5) * B, (c.y + iz + 0.5) * B)
		mmi.position = Vector3(ctr.x, 0, ctr.y)
		var in_grid := ix >= -half and ix < half and iz >= -half and iz < half
		var in_town := absf(ctr.x) + B / 2 < 208.0 and absf(ctr.y) + B / 2 < 208.0
		var off_map := ctr.length() > 1120.0
		mmi.visible = in_grid and not in_town and not off_map and (lod == 1 or cfg[1] > 0.0)
