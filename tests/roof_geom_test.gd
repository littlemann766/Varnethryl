extends Node
## test 17: every building model (all LOD files) must show a closed, outward-facing roof from straight above.
## Rays down over the inner footprint: the first hit must be a triangle that faces up as drawn
## (front-facing by winding, or a double-sided material). Catches hollow tops, inverted roofs, missing roof meshes.
## Run: godot --headless --path . res://tests/roof_geom_test.tscn   (scene run so autoloads exist)
var M
var fails := 0
# Open-top by design (checked from a top render): keep courtyard ring, open-air market stalls.
# For these, rays may pass through to the ground, but nothing may be a back face from above.
const OPEN_TOP := ["bld_keep_card2", "bld_market_card2"]
func _ready() -> void:
	M = load("res://scripts/main.gd")
	var paths := {}
	for d in M.DEFS:
		for suf in ["", "_lod1", "_lod2"]:
			paths[M._card2_path(d[0], suf) if M.CARD2.has(d[0]) else "res://assets/hi/buildings/bld_%s%s.glb" % [d[0], suf]] = d[0]
	for suf in ["", "_lod1", "_lod2"]: paths["res://assets/hi/buildings/bld_gate_tower%s.glb" % suf] = "gate_tower"
	for k in ["house1", "house2", "house3", "house4", "bakery", "apothecary", "smithy", "market", "inn"]:
		for suf in ["_lod1", "_lod2"]: paths[M._card2_path(k, suf)] = "filler/harbor " + k
	var checked := 0
	for p in paths:
		if not ResourceLoader.exists(p): continue
		checked += 1; _check(p, paths[p])
	print("ROOFGEOM %d models, %d failed" % [checked, fails])
	get_tree().quit(1 if fails > 0 else 0)

func _check(path: String, id: String) -> void:
	var root: Node3D = (load(path) as PackedScene).instantiate()
	var tris := []   # [a, b, c, double_sided]
	var aabb := AABB(); var first := true
	for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
		if mi.mesh == null: continue
		var xf := _xf(root, mi)
		for s in mi.mesh.get_surface_count():
			var mat := mi.get_active_material(s)
			var ds: bool = mat is BaseMaterial3D and (mat as BaseMaterial3D).cull_mode == BaseMaterial3D.CULL_DISABLED
			var arr := mi.mesh.surface_get_arrays(s)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var idx = arr[Mesh.ARRAY_INDEX]
			var n := (idx as PackedInt32Array).size() if idx != null else v.size()
			for t in range(0, n, 3):
				var a: Vector3 = xf * v[idx[t] if idx != null else t]; var b: Vector3 = xf * v[idx[t + 1] if idx != null else t + 1]; var c: Vector3 = xf * v[idx[t + 2] if idx != null else t + 2]
				tris.append([a, b, c, ds])
				if first: aabb = AABB(a, Vector3.ZERO); first = false
				aabb = aabb.expand(a).expand(b).expand(c)
	root.free()
	var bad := 0; var tot := 0
	var xs := []; var zs := []
	for i in 5: xs.append(lerpf(aabb.position.x, aabb.end.x, 0.3 + 0.1 * i)); zs.append(lerpf(aabb.position.z, aabb.end.z, 0.3 + 0.1 * i))
	var bins := []; for k in 25: bins.append([])
	for tr in tris:   # bin each triangle under the rays its xz bounds cover
		var mnx := minf(tr[0].x, minf(tr[1].x, tr[2].x)); var mxx := maxf(tr[0].x, maxf(tr[1].x, tr[2].x))
		var mnz := minf(tr[0].z, minf(tr[1].z, tr[2].z)); var mxz := maxf(tr[0].z, maxf(tr[1].z, tr[2].z))
		for i in 5:
			if xs[i] < mnx or xs[i] > mxx: continue
			for j in 5:
				if zs[j] >= mnz and zs[j] <= mxz: bins[i * 5 + j].append(tr)
	for i in 5:
		for j in 5:
			var o := Vector3(xs[i], aabb.end.y + 5.0, zs[j])
			var best := INF; var face := 0
			for tr in bins[i * 5 + j]:
				var r = Geometry3D.ray_intersects_triangle(o, Vector3.DOWN, tr[0], tr[1], tr[2])
				if r != null and o.y - r.y < best:
					best = o.y - r.y
					# Godot draws clockwise-wound triangles as front faces: seen from above a front face has winding normal y < 0
					var wn: Vector3 = (tr[1] - tr[0]).cross(tr[2] - tr[0])
					face = 1 if (tr[3] or wn.y < 0.0) else -1
			tot += 1
			var open_top := false
			for k in OPEN_TOP: if path.get_file().begins_with(k): open_top = true
			if face < 0 or (best == INF and not open_top): bad += 1
	if bad > tot * 0.2:
		fails += 1; print("FAIL %s (%s): %d/%d rays from above see no front-facing roof" % [path, id, bad, tot])
	else: print("ok %s %d/%d" % [path.get_file(), tot - bad, tot])

func _xf(root: Node3D, n: Node3D) -> Transform3D:
	var t := Transform3D(); var c: Node = n
	while c != null and c != root:
		if c is Node3D: t = (c as Node3D).transform * t
		c = c.get_parent()
	return t
