extends Node3D
## test 17: lean host for the world-boss ground/facing/footprint check (the full town OOMs on the shared box).
## Exposes just what WorldBoss reads from main: tier, env, hero, cam, party, cheat, height(). Rolling hills test slopes.
var tier := 2
var env: Environment
var hero: Node3D = null
var cam: Camera3D
var party = null
var cheat := {}
var time_mode := 1
var world_boss: WorldBoss
func height(x: float, z: float) -> float:
	return 14.0 * sin(x / 70.0) * cos(z / 55.0) + 6.0 * sin((x + z) / 31.0)
func _set_time(_h: float) -> void: pass
func spawn_world_boss(_near := true) -> bool:
	if world_boss == null: world_boss = WorldBoss.new(); add_child(world_boss); world_boss.setup(self)
	return true
func _ready() -> void:
	var we := WorldEnvironment.new(); env = Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.55, 0.65, 0.8)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color.WHITE; env.ambient_light_energy = 0.5; we.environment = env; add_child(we)
	var sun := DirectionalLight3D.new(); sun.rotation = Vector3(-0.8, 0.6, 0); sun.shadow_enabled = true; add_child(sun)
	cam = Camera3D.new(); cam.far = 3000; add_child(cam); cam.current = true
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var S := 6.0; var R := 520
	for ix in range(-R, R, int(S)):
		for iz in range(-R, R, int(S)):
			var x := float(ix); var z := float(iz)
			var a := Vector3(x, height(x, z), z); var b := Vector3(x + S, height(x + S, z), z); var c := Vector3(x, height(x, z + S), z + S); var d := Vector3(x + S, height(x + S, z + S), z + S)
			for q in [a, b, c, b, d, c]: st.add_vertex(q)
	st.generate_normals(); var mi := MeshInstance3D.new(); mi.mesh = st.commit()
	var mat := StandardMaterial3D.new(); mat.albedo_color = Color(0.32, 0.42, 0.22); mat.cull_mode = BaseMaterial3D.CULL_DISABLED; mi.material_override = mat; add_child(mi)
	add_child(load(OS.get_environment("WB_SCRIPT") if OS.get_environment("WB_SCRIPT") != "" else ("res://tests/wb_marker_shots.gd" if OS.get_environment("WB_MARKERS") != "" else "res://tests/wb_ground_check.gd")).new())
