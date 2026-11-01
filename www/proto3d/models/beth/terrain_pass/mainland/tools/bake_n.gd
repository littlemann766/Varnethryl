extends SceneTree
## bake terrain_n.png (RG = normal xz *0.5+0.5, 2 m/texel, +-1024 m) from a main script's height(). args: script out.png [blur_m]
func _initialize() -> void:
	var a := OS.get_cmdline_user_args(); var M: Node3D = load(a[0]).new()
	M.noise.seed = 7; M.noise.frequency = 0.0035; M.noise.fractal_octaves = 4
	var N := 1024; var st := 2.0; var e := 3.0
	var H := PackedFloat32Array(); H.resize((N + 2) * (N + 2))
	for j in N + 2:
		for i in N + 2: H[j * (N + 2) + i] = M.height(-1024.0 + (i - 0.5) * st, -1024.0 + (j - 0.5) * st)
	var img := Image.create(N, N, false, Image.FORMAT_RGB8)
	for j in N:
		for i in N:
			var hx := H[(j + 1) * (N + 2) + i + 2] - H[(j + 1) * (N + 2) + i]; var hz := H[(j + 2) * (N + 2) + i + 1] - H[j * (N + 2) + i + 1]
			var n := Vector3(-hx, 2.0 * st, -hz).normalized()
			img.set_pixel(i, j, Color(n.x * 0.5 + 0.5, n.z * 0.5 + 0.5, 0))
	img.save_png(a[1]); M.free(); quit()
