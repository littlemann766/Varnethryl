class_name ExteriorDressing
## Beth exterior pass: swaps the shared card2 atlas material on every exterior for a weathering shader (macro tone,
## ground grime, rain streaks, moss on up-facing surfaces, near detail normal). Visual only: no meshes, doors or
## colliders change. Call after _swap_buildings() (and again after any tier change that reloads buildings):
##   ExteriorDressing.apply(self, "high" if tier >= 2 else "low")
const DIR := "res://exterior_pass/"
static var _mat := {}
static var _proxy: EmissionProxy

## main.gd drives night windows with `m.emission_energy_multiplier = em` on main.emissive_mats; this forwards it.
class EmissionProxy extends RefCounted:
	var mats: Array = []
	var emission_energy_multiplier := 0.0:
		set(v):
			emission_energy_multiplier = v
			for m in mats: (m as ShaderMaterial).set_shader_parameter("emission_energy", v)

static func material_for(src: BaseMaterial3D, tier: String) -> ShaderMaterial:
	var key := str(src.get_instance_id()) + tier
	if _mat.has(key): return _mat[key]
	var m := ShaderMaterial.new()
	m.shader = load(DIR + ("shaders/exterior_card2.gdshader" if tier == "high" else "shaders/exterior_card2_low.gdshader"))
	m.set_shader_parameter("albedo_tex", src.albedo_texture)
	m.set_shader_parameter("normal_tex", src.normal_texture)
	m.set_shader_parameter("normal_scale", src.normal_scale)
	m.set_shader_parameter("orm_tex", src.orm_texture if src is ORMMaterial3D else src.roughness_texture)
	m.set_shader_parameter("emissive_tex", src.emission_texture)
	m.set_shader_parameter("emission_energy", src.emission_energy_multiplier if src.emission_enabled else 0.0)
	m.set_shader_parameter("weather_tex", load(DIR + "tex/ext_weather.png"))
	m.set_shader_parameter("detail_normal_tex", load(DIR + "tex/ext_detail_normal.png"))
	_mat[key] = m
	return m

static func _is_card2(m: Material) -> bool:
	return m is BaseMaterial3D and (m as BaseMaterial3D).albedo_texture != null and (m as BaseMaterial3D).albedo_texture.resource_path.contains("card2_albedo")

## returns number of surfaces swapped
static func apply(root: Node, tier := "high") -> int:
	var n := 0
	if _proxy == null: _proxy = EmissionProxy.new()
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var m3 := mi as MeshInstance3D
		if m3.mesh == null: continue
		for s in m3.mesh.get_surface_count():
			var mk := "ext_src_%d" % s
			var src: Material = m3.get_meta(mk) if m3.has_meta(mk) else m3.get_active_material(s)   # tier change: start from the original
			if _is_card2(src):
				m3.set_meta(mk, src)
				var sm := material_for(src, tier); m3.set_surface_override_material(s, sm); n += 1
				if not _proxy.mats.has(sm): _proxy.mats.append(sm)
	var em = root.get("emissive_mats")
	if em is Array:
		var keep := []
		for m in em: if m != _proxy and not (m is Material and _is_card2(m)): keep.append(m)   # test 22 (Lucky): the proxy is not a Material
		keep.append(_proxy); em.clear(); em.append_array(keep)
	return n
