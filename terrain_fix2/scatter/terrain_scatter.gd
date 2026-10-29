class_name TerrainScatter
extends RefCounted
## Beth terrain_fix2: foothill rocks + bushes, road-verge pebbles, farm hay + fence-edge long grass.
## Drop-in: TerrainScatter.build(main) once (after _foliage()), TerrainScatter.apply_tier(tier) from apply_quality().
const SCN := "res://terrain_fix2/scatter/terrain_scatter.scn"
# [Low, Medium, High, Ultra] range ends (m): foothill lod0 / lod1, pebble lod0 / lod1, farm lod0 / lod1, tufts
const R_FH := [[0.0, 160.0], [60.0, 220.0], [80.0, 300.0], [110.0, 380.0]]
const R_PB := [[0.0, 22.0], [0.0, 30.0], [18.0, 38.0], [24.0, 45.0]]
const R_FM := [[0.0, 120.0], [40.0, 160.0], [50.0, 200.0], [70.0, 250.0]]
const R_TF := [25.0, 35.0, 45.0, 60.0]
static var root: Node3D
static func build(main: Node) -> void:
	root = (load(SCN) as PackedScene).instantiate(); main.add_child(root)
	# boulders block the player + enemies like the existing scattered rocks do
static func apply_tier(tier: int) -> void:
	if root == null: return
	for c in root.get_children():
		if not c is GeometryInstance3D: continue
		var g: GeometryInstance3D = c; var lod: int = g.get_meta("lod", 0); var kind: String = g.get_meta("kind", "")
		var r: Array
		match kind:
			"foothill": r = R_FH[tier]
			"pebble": r = R_PB[tier]
			"farm": r = R_FM[tier]
			"tuft": r = [R_TF[tier], 0.0]
			_: continue
		var e0: float = r[0]; var e1: float = r[1]
		g.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		g.visibility_range_begin_margin = 4.0; g.visibility_range_end_margin = 4.0
		if kind == "tuft": g.visibility_range_end = e0; g.visible = true; continue
		if lod == 0: g.visible = e0 > 0.0; g.visibility_range_begin = 0.0; g.visibility_range_end = e0
		else: g.visible = true; g.visibility_range_begin = e0; g.visibility_range_end = e1
