extends SceneTree
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var M: Node3D = load("res://scripts/main_tp.gd").new()
	M.noise.seed = 7; M.noise.frequency = 0.0035; M.noise.fractal_octaves = 4
	M._terrain(); M._roads()
	var minroad := 1e9; var minwall := 1e9; var minvolc := 1e9
	for i in 720:
		var a := i / 720.0 * TAU; var d := Vector2(cos(a), sin(a))
		for rr in range(20, 121, 2):
			var p: Vector2 = M.LAKE + d * rr
			if p.length() > 216.0 and M.height(p.x, p.y) < -0.3:
				minroad = min(minroad, M._road_dist(p)); minvolc = min(minvolc, p.distance_to(M.VOLC))
				minwall = min(minwall, Vector2(maxf(0, absf(p.x) - 185), maxf(0, absf(p.y) - 185)).length())
	print("LAKECHK road=%.1f wall=%.1f volc=%.1f" % [minroad, minwall, minvolc]); quit()
