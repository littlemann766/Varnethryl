extends SceneTree
## Terrain pass fix 4 (Beth): re-seat the baked wildflowers + terrain_fix2 scatter on the DRAWN ground (main._terrain's
## 10 m triangle grid of the patched height), keeping each instance's own offset to the ground it was baked against.
## args: old_main.gd new_main.gd out_dir
var Mo: Node3D
var Mn: Node3D
var S := 2400.0
var st := 10.0
func surf(M: Node3D, x: float, z: float) -> float:
	var fx := (x + S / 2) / st; var fz := (z + S / 2) / st; var i := floori(fx); var j := floori(fz); var u := fx - i; var v := fz - j
	var x0 := -S / 2 + i * st; var z0 := -S / 2 + j * st
	var h00: float = M.height(x0, z0); var h10: float = M.height(x0 + st, z0); var h01: float = M.height(x0, z0 + st); var h11: float = M.height(x0 + st, z0 + st)
	if u + v <= 1.0: return h00 + (h10 - h00) * u + (h01 - h00) * v
	return h11 + (h01 - h11) * (1.0 - u) + (h10 - h11) * (1.0 - v)
func fix_buf(buf: PackedFloat32Array, stride: int, stats: Dictionary) -> PackedFloat32Array:
	var out := buf.duplicate()
	for k in range(0, buf.size(), stride):
		var x := buf[k + 3]; var y := buf[k + 7]; var z := buf[k + 11]
		var off: float = y - Mo.height(x, z)                      # what the bake intended (e.g. -0.02 sink, clump slope)
		off = clampf(off, -0.25, 0.1)
		var before: float = y - surf(Mo, x, z); var ny: float = surf(Mn, x, z) + off
		out[k + 7] = ny
		stats.n += 1; stats.float_b += int(before > 0.35); stats.buried_b += int(before < -0.6)
		var after := ny - surf(Mn, x, z); stats.float_a += int(after > 0.35); stats.buried_a += int(after < -0.6)
	return out
func _initialize() -> void:
	var a := OS.get_cmdline_user_args(); var od: String = a[2]
	Mo = load(a[0]).new(); Mn = load(a[1]).new()
	for M in [Mo, Mn]: M.noise.seed = 7; M.noise.frequency = 0.0035; M.noise.fractal_octaves = 4
	# --- wildflowers bake
	var f := FileAccess.open("res://terrain_flowers/flowers_bake.bin", FileAccess.READ); var data: Dictionary = f.get_var(); f.close()
	var fs := {"n": 0, "float_b": 0, "buried_b": 0, "float_a": 0, "buried_a": 0}
	for key in data.chunks: data.chunks[key] = fix_buf(data.chunks[key], 16, fs)
	var fo := FileAccess.open(od + "/flowers_bake.bin", FileAccess.WRITE); fo.store_var(data); fo.close()
	print("RESEAT flowers ", fs)
	# --- scatter scene
	var root: Node = (load("res://terrain_fix2/scatter/terrain_scatter.scn") as PackedScene).instantiate()
	var ss := {"n": 0, "float_b": 0, "buried_b": 0, "float_a": 0, "buried_a": 0}
	for c in root.get_children():
		if c is MultiMeshInstance3D and c.multimesh:
			var mm: MultiMesh = c.multimesh
			var stride := 12 + (4 if mm.use_colors else 0) + (4 if mm.use_custom_data else 0)
			if mm.transform_format != MultiMesh.TRANSFORM_3D: continue
			var nb := fix_buf(mm.buffer, stride, ss); mm = mm.duplicate(); mm.buffer = nb; c.multimesh = mm
	var bc := root.get_node_or_null("BoulderCollision")
	if bc:
		for cs in bc.get_children():
			var p: Vector3 = cs.position; var off := clampf(p.y - Mo.height(p.x, p.z), -3.0, 3.0); cs.position.y = surf(Mn, p.x, p.z) + off
	for c in root.get_children(): _own(c, root)
	var ps := PackedScene.new(); ps.pack(root); ResourceSaver.save(ps, od + "/terrain_scatter.scn")
	print("RESEAT scatter ", ss); quit()
func _own(n: Node, r: Node) -> void:
	if n != r: n.owner = r
	for c in n.get_children(): _own(c, r)
