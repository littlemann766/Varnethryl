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

func _ready() -> void:
	for n in ["Wall", "Crest", "Skirt"]:
		var mi: MeshInstance3D = get_node(n)
		mi.set_surface_override_material(0, mi.get_surface_override_material(0).duplicate())
	_apply()

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
			var p := Node3D.new(); p.position = Vector3(cos(a), 0, sin(a)) * 82.0; _posts.add_child(p)
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

func _counter_scale() -> void:
	if _posts == null: return
	for p in _posts.get_children():
		p.scale = Vector3(1.0 / max(scale.x, 0.001), 1.0, 1.0 / max(scale.z, 0.001))

func _process(_d: float) -> void:
	_counter_scale()
