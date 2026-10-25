extends RefCounted
## Beth's terrain-following road network (replaces main.gd _roads()).
## - Catmull-Rom smoothed centreline, shared cross-sections (no gaps at bends)
## - every vertex sits on the *rendered* terrain triangle surface (same 140x140 / 10 m
##   triangulation as main._terrain()), so terrain can never poke through
## - 8.8 m road + 1.8 m soft grass skirt each side (vertex alpha), dirt outside the walls,
##   cobble inside r<215 (vertex colour .r), 3 LODs per ~64 m chunk via visibility ranges.
## Usage (main.gd):  add_child(load("res://assets/roads/road_builder.gd").new().build(self, ROADS))

const N := 140
const S := 1400.0
const HALF := 4.4          # core half-width (matches old road / _road_dist)
const SKIRT := 1.8         # grass blend beyond the core
const LODS := [            # [step along m, across offsets (fraction of HALF, >1 = skirt), lift m, vis_begin, vis_end]
	[1.0, [-1.41, -1.2, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.2, 1.41], 0.06, 0.0, 140.0],
	[2.5, [-1.41, -1.0, -0.5, 0.0, 0.5, 1.0, 1.41], 0.10, 140.0, 380.0],
	[6.0, [-1.41, -1.0, 0.0, 1.0, 1.41], 0.22, 380.0, 0.0],
]
const CHUNK := 64.0
var hs := PackedFloat32Array()
var step := S / N

func _grid(main) -> void:
	hs.resize((N + 1) * (N + 1))
	for j in N + 1:
		for i in N + 1:
			hs[j * (N + 1) + i] = main.height(-S / 2 + i * step, -S / 2 + j * step)

## height of the rendered terrain mesh (exactly matches main._terrain() triangles)
func th(x: float, z: float) -> float:
	var gx := clampf((x + S / 2) / step, 0.0, N - 0.0001); var gz := clampf((z + S / 2) / step, 0.0, N - 0.0001)
	var i := int(gx); var j := int(gz); var fx := gx - i; var fz := gz - j
	var h00 := hs[j * (N + 1) + i]; var h10 := hs[j * (N + 1) + i + 1]
	var h01 := hs[(j + 1) * (N + 1) + i]; var h11 := hs[(j + 1) * (N + 1) + i + 1]
	if fx + fz <= 1.0: return h00 + fx * (h10 - h00) + fz * (h01 - h00)
	return h11 + (1.0 - fx) * (h01 - h11) + (1.0 - fz) * (h10 - h11)

func _centre(r: Array, ds: float) -> PackedVector2Array:
	var p: Array = []
	for q in r: p.append(Vector2(q[0], q[1]))
	var out := PackedVector2Array()
	for i in range(p.size() - 1):
		var p0: Vector2 = p[max(i - 1, 0)]; var p1: Vector2 = p[i]; var p2: Vector2 = p[i + 1]; var p3: Vector2 = p[min(i + 2, p.size() - 1)]
		var n := maxi(1, int(ceil(p1.distance_to(p2) / ds)))
		for k in n:
			var t := float(k) / n; var t2 := t * t; var t3 := t2 * t
			out.append(0.5 * ((2.0 * p1) + (-p0 + p2) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3))
	out.append(p[-1])
	return out

func _material() -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = load("res://assets/roads/road.gdshader")
	for k in ["dirt_albedo", "dirt_normal", "dirt_rough", "cobble_albedo", "cobble_normal", "cobble_rough", "edge_noise"]:
		m.set_shader_parameter(k, load("res://assets/roads/textures/%s.png" % k))
	return m

func build(main, roads: Array) -> Node3D:
	_grid(main)
	var root := Node3D.new(); root.name = "Roads"
	var mat := _material()
	for ri in roads.size():
		for li in LODS.size():
			var L: Array = LODS[li]
			var c := _centre(roads[ri], L[0])
			if c.size() < 2: continue
			var dacc := PackedFloat32Array(); dacc.resize(c.size()); dacc[0] = 0.0
			for i in range(1, c.size()): dacc[i] = dacc[i - 1] + c[i].distance_to(c[i - 1])
			var offs: Array = L[1]; var cols := offs.size()
			var start := 0
			while start < c.size() - 1:
				var end_i := start
				while end_i < c.size() - 1 and dacc[end_i] - dacc[start] < CHUNK: end_i += 1
				var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
				for i in range(start, end_i + 1):
					var a := c[max(i - 1, 0)]; var b := c[min(i + 1, c.size() - 1)]
					var dir := (b - a).normalized(); var side := Vector2(-dir.y, dir.x)
					var cob := 1.0 - smoothstep(205.0, 225.0, c[i].length())
					for o in offs:
						var w: float = o * HALF if absf(o) <= 1.0 else signf(o) * (HALF + (absf(o) - 1.0) / 0.41 * SKIRT)
						var p := c[i] + side * w
						var al := 1.0 if absf(o) <= 1.0 else 1.0 - (absf(o) - 1.0) / 0.41
						st.set_color(Color(cob, 0.0, 0.0, al))
						st.set_uv(Vector2((w + HALF) / (2.0 * HALF), dacc[i] / (2.0 * HALF)))
						st.set_uv2(p)
						st.add_vertex(Vector3(p.x, th(p.x, p.y) + L[2], p.y))
				var rows := end_i - start + 1
				for rr in rows - 1:
					for k in cols - 1:
						var v0 := rr * cols + k
						st.add_index(v0); st.add_index(v0 + cols); st.add_index(v0 + 1)
						st.add_index(v0 + 1); st.add_index(v0 + cols); st.add_index(v0 + cols + 1)
				st.generate_normals(); st.generate_tangents()
				var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat
				mi.name = "road%d_c%d_lod%d" % [ri, start, li]
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				mi.visibility_range_begin = L[3]; mi.visibility_range_end = L[4]
				mi.visibility_range_begin_margin = 8.0 if L[3] > 0.0 else 0.0; mi.visibility_range_end_margin = 8.0 if L[4] > 0.0 else 0.0
				root.add_child(mi)
				start = end_i
	return root
