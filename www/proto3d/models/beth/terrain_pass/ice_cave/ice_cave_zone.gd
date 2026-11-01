## Terrain pass fix 7 (Beth): Frost Troll Ice Cave zone. Self-contained: builds the cave at CAVE_ORIGIN (deep under the
## legacy frost-realm x, far outside the 2.4 km mainland and below the y=0 sea), its collision, lights, Beth's
## PLACEMENT_frost_realm.json floor dressing, and returns spawn points. Wiring: README_LUCKY_TERRAIN_PASS.md "Fix 7".
class_name IceCaveZone
extends Node3D

const CAVE_ORIGIN := Vector3(2250.0, -600.0, 0.0)
const DIR := "res://assets/ice_cave/"
var info: Dictionary
var env_node: WorldEnvironment

func build(parent: Node, with_env := true) -> IceCaveZone:
	name = "IceCave"; position = CAVE_ORIGIN; parent.add_child(self)
	info = JSON.parse_string(FileAccess.get_file_as_string(DIR + "ice_cave.json"))
	var vc := StandardMaterial3D.new(); vc.vertex_color_use_as_albedo = true; vc.roughness = 0.55; vc.cull_mode = BaseMaterial3D.CULL_DISABLED
	var lods := [[DIR + "ice_cave.glb", 0.0, 140.0], [DIR + "ice_cave_lod1.glb", 130.0, 0.0]]
	for l in lods:
		var n: Node3D = load(l[0]).instantiate(); add_child(n)
		for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false):
			mi.material_override = vc; mi.visibility_range_begin = l[1]; mi.visibility_range_end = l[2]
	var gm := StandardMaterial3D.new(); gm.vertex_color_use_as_albedo = true; gm.emission_enabled = true; gm.emission = Color(0.35, 0.8, 1.0); gm.emission_energy_multiplier = 1.4
	var g: Node3D = load(DIR + "ice_cave_glow.glb").instantiate(); add_child(g)
	for mi: MeshInstance3D in g.find_children("*", "MeshInstance3D", true, false): mi.material_override = gm; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var c: Node3D = load(DIR + "ice_cave_col.glb").instantiate()
	for mi: MeshInstance3D in c.find_children("*", "MeshInstance3D", true, false):
		var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var sh := ConcavePolygonShape3D.new()
		sh.set_faces(mi.mesh.get_faces()); sh.backface_collision = true; cs.shape = sh; sb.add_child(cs); add_child(sb); sb.transform = mi.transform
	c.free()
	for p in info.lights:
		var o := OmniLight3D.new(); o.position = Vector3(p[0], p[1], p[2]); o.light_color = Color(0.6, 0.82, 1.0); o.light_energy = 2.2; o.omni_range = 55.0; o.omni_attenuation = 1.1; add_child(o)
	var ex := OmniLight3D.new(); ex.position = Vector3(-8, 4, -60); ex.light_color = Color(1.0, 0.95, 0.85); ex.light_energy = 3.0; ex.omni_range = 25.0; add_child(ex)   # daylight at the mouth
	if with_env:
		env_node = WorldEnvironment.new(); var e := Environment.new()
		e.background_mode = Environment.BG_COLOR; e.background_color = Color(0.05, 0.07, 0.10)
		e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color = Color(0.45, 0.58, 0.75); e.ambient_light_energy = 0.55
		e.fog_enabled = true; e.fog_light_color = Color(0.32, 0.42, 0.55); e.fog_density = 0.004; e.fog_height = CAVE_ORIGIN.y + 5.0; e.fog_height_density = 0.03   # fog_height is world-space
		e.tonemap_mode = Environment.TONE_MAPPER_FILMIC; env_node.environment = e; add_child(env_node)
	await get_tree().physics_frame
	_dress()
	return self

## Ground under a cave-local point (raycast; the cave floor is not a heightfield).
func floor_y(x: float, z: float) -> float:
	var sp := get_world_3d().direct_space_state
	var a := to_global(Vector3(x, 4, z)); var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(a, a + Vector3(0, -12, 0)))
	return (h.position.y - CAVE_ORIGIN.y) if h else NAN

func world(p: Array) -> Vector3: return to_global(Vector3(p[0], p[1], p[2]))
func spawn_point() -> Vector3: return world(info.spawn)
func troll_spawn(id: String) -> Vector3:
	var p: Array = info.troll_spawns[id]; return to_global(Vector3(p[0], floor_y(p[0], p[2]), p[2]))

var dressed := 0
var dropped := 0
func _dress() -> void:
	var j = JSON.parse_string(FileAccess.get_file_as_string("res://assets/data/PLACEMENT_frost_realm.json"))
	for it in j["items"]:
		var p: Array = it["position"]; var y := floor_y(p[0], p[2])
		if is_nan(y) or Vector2(p[0], p[2]).distance_to(Vector2(info.spawn[0], info.spawn[2])) < 4.0: dropped += 1; continue
		var r: Array = it["rotation"]; var s: Array = it["scale"]
		var n: Node3D = load("res://assets/" + it["file"]).instantiate(); add_child(n)
		n.transform = Transform3D(Basis.from_euler(Vector3(r[0], r[1], r[2])).scaled(Vector3(s[0], s[1], s[2])), Vector3(p[0], y - 0.05, p[2]))
		dressed += 1
