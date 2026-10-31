# Lava Wave v3.1 driver: gaps (safe openings) shared by wall, crest, skirt, spray + a damage helper.
# Root position = boss feet. Gap angles are measured in the wave's local XZ plane: angle = atan2(z, x), degrees, CCW from +X,
# gap i is centred at gap_offset_deg + i * 360/gap_count. Width is set in metres at the 80 m start radius.
@tool
extends Node3D
@export_range(0, 8) var gap_count: int = 4: set = _set_count
@export var gap_width_m: float = 9.0: set = _set_width        # at base_radius
@export var gap_offset_deg: float = 0.0: set = _set_offset    # randomise per cast: randomize_gaps()
@export_range(0.0, 1.0) var rise: float = 0.0: set = _set_rise
@export var wall_height: float = 24.0
@export var post_height: float = 9.0        # safe-gap marker posts (world metres)
@export var show_posts: bool = true: set = _set_posts
const POST_MAT := preload("res://assets/volcano/worldboss/materials/wb_gap_post_mat.tres")
var _posts: Node3D
var _gap_key := ""
var _post_mats: Array[ShaderMaterial] = []
const BASE_RADIUS := 80.0
# --- v3.2 terrain follow -------------------------------------------------------------------------------------------
## Raycast the ground around the ring and lift wall/crest/skirt/posts/spray onto it (flat ground = no change).
@export var follow_ground: bool = true
@export_flags_3d_physics var ground_mask: int = 1
@export var ground_ray_up: float = 150.0     # ray starts this far above the wave root
@export var ground_ray_down: float = 150.0   # and ends this far below it
@export var ground_update_interval: float = 0.1   # s; re-sampled at most this often, and only when the ring moved/grew
## Optional: Callable(world_pos: Vector3) -> float world ground Y. Use for a heightmap terrain without collision
## (and on a headless server). When valid it replaces the raycasts.
var height_provider: Callable
const GH_N := 64
const SKIRT_OUT := 1.35          # must match wb_wave_skirt.gdshader skirt_out
var ground_h := PackedFloat32Array()      # at the wall radius (80 local)
var ground_h_out := PackedFloat32Array()  # at the skirt outer edge (108 local)
var ground_h_m1 := PackedFloat32Array()   # skirt 1/3 across (~89 local)
var ground_h_m2 := PackedFloat32Array()   # skirt 2/3 across (~99 local)
var _gh_key := Vector4(INF, 0, 0, 0)
var _gh_timer := 0.0

func _ready() -> void:
	for n in ["Wall", "Crest", "Skirt"]:
		var mi: MeshInstance3D = get_node(n)
		mi.set_surface_override_material(0, mi.get_surface_override_material(0).duplicate())
	$Skirt.mesh = _annulus_mesh()
	ground_h.resize(GH_N); ground_h_out.resize(GH_N); ground_h_m1.resize(GH_N); ground_h_m2.resize(GH_N)
	_apply()
	if height_provider.is_valid(): sample_ground()   # raycasts wait for the first physics tick (bodies registered)

func gap_width_deg() -> float:
	return rad_to_deg(gap_width_m / BASE_RADIUS)

func randomize_gaps(rng: RandomNumberGenerator = null) -> void:
	var r := rng if rng else RandomNumberGenerator.new()
	gap_offset_deg = r.randf_range(0.0, 360.0 / max(gap_count, 1))

## True if a world position is inside a safe gap (skip wave damage there). Uses angle only, so it stays valid while the wave expands.
func is_in_gap(world_pos: Vector3, margin_deg: float = 0.5) -> bool:
	if gap_count <= 0: return false
	var l := to_local(world_pos)
	var a := rad_to_deg(atan2(l.z, l.x)) - gap_offset_deg
	var step := 360.0 / gap_count
	var m := fposmod(a + step * 0.5, step) - step * 0.5
	return absf(m) <= gap_width_deg() * 0.5 - margin_deg

## Gap centre angles (deg) for the server / other clients.
func gap_angles() -> PackedFloat32Array:
	var out := PackedFloat32Array()
	for i in gap_count: out.append(fposmod(gap_offset_deg + i * 360.0 / gap_count, 360.0))
	return out

func _set_count(v): gap_count = v; _apply()
func _set_width(v): gap_width_m = v; _apply()
func _set_offset(v): gap_offset_deg = v; _apply()
func _set_rise(v): rise = v; _apply()
func _set_posts(v): show_posts = v; _apply()

func _apply() -> void:
	if not is_inside_tree(): return
	for n in ["Wall", "Crest", "Skirt"]:
		var mi: MeshInstance3D = get_node_or_null(n)
		if mi == null: continue
		var m: ShaderMaterial = mi.get_surface_override_material(0)
		m.set_shader_parameter("use_gaps", true)
		m.set_shader_parameter("gap_count", gap_count)
		m.set_shader_parameter("gap_width_deg", gap_width_deg())
		m.set_shader_parameter("gap_offset_deg", gap_offset_deg)
		m.set_shader_parameter("rise", rise)
		m.set_shader_parameter("follow_ground", follow_ground)
	$Crest.position.y = wall_height * rise
	$CrestSpray.position.y = wall_height * rise + 3.0
	var key := "%d|%.3f|%.3f|%s" % [gap_count, gap_width_m, gap_offset_deg, show_posts]
	if key != _gap_key:   # only rebuild when the gap layout changes (rise is tweened every frame)
		_gap_key = key; _rebuild_spray(); _rebuild_posts()
	_update_posts()

func _rebuild_spray() -> void:
	# ring of emission points with the gaps (plus 1 deg) left out
	var sp: CPUParticles3D = get_node_or_null("CrestSpray")
	if sp == null: return
	var pts := PackedVector3Array()
	var n := 720
	for i in n:
		var a := i * 360.0 / n
		var l := Vector3(cos(deg_to_rad(a)), 0, sin(deg_to_rad(a))) * 81.5
		if is_in_gap(to_global(l) if is_inside_tree() else l, -3.5): continue   # keep 3.5 deg clear so spray does not drift into gaps
		if follow_ground and ground_h.size() == GH_N: l.y = ground_at_angle(a)
		pts.append(l)
	sp.emission_shape = CPUParticles3D.EMISSION_SHAPE_POINTS
	sp.emission_points = pts

func _rebuild_posts() -> void:
	# one cool glowing post + billboard flare on each gap edge, just outside the wall (r 82). Children of the root,
	# so they ride the outward scale tween; _process undoes the x/z stretch so they stay round and 1.2 m thick.
	if _posts: _posts.free(); _posts = null
	if not show_posts or gap_count <= 0: return
	_posts = Node3D.new(); _posts.name = "GapPosts"; add_child(_posts)
	var mat: ShaderMaterial = POST_MAT.duplicate()
	var fmat: ShaderMaterial = POST_MAT.duplicate(); fmat.set_shader_parameter("billboard", true)
	_post_mats = [mat, fmat]
	var cyl := CylinderMesh.new(); cyl.top_radius = 0.45; cyl.bottom_radius = 0.7; cyl.height = 1.0; cyl.radial_segments = 8; cyl.rings = 1; cyl.cap_top = false; cyl.cap_bottom = false
	var quad := QuadMesh.new(); quad.size = Vector2(1, 1)
	var half := gap_width_deg() * 0.5
	for i in gap_count:
		var c := gap_offset_deg + i * 360.0 / gap_count
		for e in [-1.0, 1.0]:
			var a := deg_to_rad(c + e * half)
			var p := Node3D.new(); p.position = Vector3(cos(a), 0, sin(a)) * 82.0; p.set_meta("ang", rad_to_deg(a)); _posts.add_child(p)
			var post := MeshInstance3D.new(); post.name = "Post"; post.mesh = cyl; post.material_override = mat
			post.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; p.add_child(post)
			var fl := MeshInstance3D.new(); fl.mesh = quad; fl.material_override = fmat; fl.name = "Flare"; fl.scale = Vector3.ONE * 6.0
			fl.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; p.add_child(fl)
	_counter_scale()

func _update_posts() -> void:
	if _posts == null: return
	var h := post_height * (0.3 + 0.7 * rise)
	for m in _post_mats: m.set_shader_parameter("rise", rise)
	for p in _posts.get_children():
		p.get_node("Post").scale = Vector3(1, h, 1); p.get_node("Post").position.y = h * 0.5
		p.get_node("Flare").position.y = h + 0.5
		p.position.y = ground_at_angle(p.get_meta("ang", 0.0)) if follow_ground else 0.0

func _counter_scale() -> void:
	if _posts == null: return
	for p in _posts.get_children():
		p.scale = Vector3(1.0 / max(scale.x, 0.001), 1.0, 1.0 / max(scale.z, 0.001))

func _process(_d: float) -> void:
	_counter_scale()

func _physics_process(d: float) -> void:
	if not follow_ground or Engine.is_editor_hint(): return
	_gh_timer -= d
	if _gh_timer > 0.0: return
	_gh_timer = ground_update_interval
	var g := global_transform
	var key := Vector4(g.origin.x, g.origin.y, g.origin.z, g.basis.x.length())
	if key.is_equal_approx(_gh_key) or (key - _gh_key).length() < 0.25: return   # ring has not moved/grown enough
	sample_ground()

## Ground height (m, relative to the wave root) at a local angle in degrees (atan2(z, x), same convention as the gaps).
func ground_at_angle(deg: float) -> float:
	if ground_h.size() != GH_N: return 0.0
	var f := fposmod(deg, 360.0) / 360.0 * GH_N
	var i0 := int(floor(f)) % GH_N
	return lerpf(ground_h[i0], ground_h[(i0 + 1) % GH_N], f - floor(f))

## Re-sample all 4 height rings now (call after teleporting the wave). 4 x 64 rays.
func sample_ground() -> void:
	if not is_inside_tree() or not follow_ground: return
	var g := global_transform
	_gh_key = Vector4(g.origin.x, g.origin.y, g.origin.z, g.basis.x.length())
	var space := get_world_3d().direct_space_state if not height_provider.is_valid() else null
	var q: PhysicsRayQueryParameters3D
	if space:
		q = PhysicsRayQueryParameters3D.new(); q.collision_mask = ground_mask; q.hit_back_faces = false
	var rings := [ground_h, ground_h_m1, ground_h_m2, ground_h_out]
	for ring in 4:
		var r := BASE_RADIUS * (1.0 + (SKIRT_OUT - 1.0) * ring / 3.0)
		for i in GH_N:
			var a := TAU * i / GH_N
			var w := g * (Vector3(cos(a), 0, sin(a)) * r)
			var y := g.origin.y
			if height_provider.is_valid():
				y = float(height_provider.call(w))
			elif space:
				q.from = Vector3(w.x, g.origin.y + ground_ray_up, w.z); q.to = Vector3(w.x, g.origin.y - ground_ray_down, w.z)
				var hit := space.intersect_ray(q)
				if hit: y = hit.position.y
			var arr: PackedFloat32Array = rings[ring]; arr[i] = y - g.origin.y; rings[ring] = arr
	ground_h = rings[0]; ground_h_m1 = rings[1]; ground_h_m2 = rings[2]; ground_h_out = rings[3]
	for n in ["Wall", "Crest", "Skirt"]:
		var mi: MeshInstance3D = get_node_or_null(n)
		if mi == null: continue
		var m: ShaderMaterial = mi.get_surface_override_material(0)
		m.set_shader_parameter("ground_h", ground_h)
		if n == "Skirt": m.set_shader_parameter("ground_h_m1", ground_h_m1); m.set_shader_parameter("ground_h_m2", ground_h_m2)
		if n == "Skirt": m.set_shader_parameter("ground_h_out", ground_h_out)
	_rebuild_spray(); _update_posts()

func _annulus_mesh() -> ArrayMesh:
	# ground skirt as a 64 x 7 annulus (896 tris) instead of a 2x2 plane: enough vertices to drape on slopes.
	# Local radius 1 = skirt_out (node scale 108); UV = xz*0.5+0.5 so the shader's p = (UV*2-1)*skirt_out is unchanged.
	var radii := [0.96, 1.0, 1.06, 1.1167, 1.175, 1.2333, 1.29, 1.36]   # vertices on every height ring
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for j in radii.size() - 1:
		for i in GH_N:
			var a0 := TAU * i / GH_N; var a1 := TAU * (i + 1) / GH_N
			var quad := [[a0, radii[j]], [a1, radii[j]], [a1, radii[j + 1]], [a0, radii[j]], [a1, radii[j + 1]], [a0, radii[j + 1]]]
			for v in quad:
				var xz: Vector2 = Vector2(cos(float(v[0])), sin(float(v[0]))) * float(v[1]) / SKIRT_OUT
				st.set_normal(Vector3.UP); st.set_uv(xz * 0.5 + Vector2(0.5, 0.5)); st.add_vertex(Vector3(xz.x, 0, xz.y))
	return st.commit()
