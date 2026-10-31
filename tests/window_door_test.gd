extends Node
## test 17 (boss: Arcane Academy window pokes through the front door arch): no window glass may sit
## inside any card2 building's door opening. Glass = light-blue atlas texels under the triangle's UV centroid.
var fails := 0
func _ready() -> void:
	var atlas := Image.load_from_file(ProjectSettings.globalize_path("res://assets/card2/atlas/card2_albedo.jpg"))
	var idx = JSON.parse_string(FileAccess.get_file_as_string("res://assets/card2/index.json"))
	var checked := 0
	for b in idx["buildings"]:
		if not b.has("door_points"): continue
		for tier in ["high", "medium", "low"]:
			if not b.has(tier) or not b[tier] is Dictionary: continue
			var path := "res://assets/card2/" + str(b[tier]["file"])
			if not ResourceLoader.exists(path): continue
			checked += 1
			var bad := _scan(path, b["door_points"], atlas)
			if bad > 0: fails += 1; print("FAIL %s: %d glass triangles inside a door opening" % [path.get_file(), bad])
	print("WINDOWDOOR %d models, %d failed" % [checked, fails])
	get_tree().quit(1 if fails > 0 else 0)

func _scan(path: String, doors: Array, atlas: Image) -> int:
	var root: Node3D = (load(path) as PackedScene).instantiate()
	var bad := 0
	for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
		for s in mi.mesh.get_surface_count():
			var arr := mi.mesh.surface_get_arrays(s)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]; var uv: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV]
			var ix = arr[Mesh.ARRAY_INDEX]
			var n: int = (ix as PackedInt32Array).size() if ix != null else v.size()
			for t in range(0, n, 3):
				var i0: int = ix[t] if ix != null else t; var i1: int = ix[t + 1] if ix != null else t + 1; var i2: int = ix[t + 2] if ix != null else t + 2
				var a := v[i0]; var bb := v[i1]; var c := v[i2]
				if (bb - a).cross(c - a).length() < 1e-6: continue
				for d in doors:
					var p := Vector3(d["pos"][0], 0, d["pos"][2]); var nn := Vector3(d["normal"][0], 0, d["normal"][2]); var lat := Vector3(nn.z, 0, -nn.x)
					var inside := true
					for q in [a, bb, c]:
						var r: Vector3 = q - p
						if absf(r.dot(lat)) > float(d["width"]) * 0.5 or q.y > float(d["height"]) or q.y < 0.3 or absf(r.dot(nn)) > 0.6: inside = false; break
					if not inside: continue
					var u := (uv[i0] + uv[i1] + uv[i2]) / 3.0
					var col := atlas.get_pixel(clampi(int(fposmod(u.x, 1.0) * atlas.get_width()), 0, atlas.get_width() - 1), clampi(int(fposmod(u.y, 1.0) * atlas.get_height()), 0, atlas.get_height() - 1))
					if col.b > 0.67 and col.g > 0.59 and col.b > col.r + 0.1: bad += 1
	root.free()
	return bad
