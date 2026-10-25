shader_type spatial;
render_mode cull_disabled, depth_draw_opaque, diffuse_lambert_wrap;
// Tree/plant shader for Beth's kit: alpha-cut atlas, COLOR_0 tint, wind sway.
// Keeps the authored (spherical) normals on BOTH faces: Godot's default flips the normal
// on back faces, which made the leaf cards render as flat dark/grey sheets.
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float sway = 0.06;
uniform float alpha_cut = 0.5;
varying vec3 vcol;
varying vec3 vnorm;
void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(0.0,0.0,0.0,1.0)).xyz;
	float h = max(VERTEX.y, 0.0);
	float t = TIME * 1.6 + wp.x * 0.07 + wp.z * 0.05;
	VERTEX.x += sin(t) * sway * h * h * 0.15;
	VERTEX.z += cos(t * 0.8) * sway * h * h * 0.1;
	vcol = COLOR.rgb;
	vnorm = (MODELVIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
}
void fragment() {
	vec4 tex = texture(albedo_tex, UV);
	if (tex.a < alpha_cut) discard;
	ALBEDO = tex.rgb * tint.rgb * vcol;
	NORMAL = normalize(vnorm);
	ROUGHNESS = 0.85;
	SPECULAR = 0.2;
	BACKLIGHT = vec3(0.35, 0.4, 0.3) * ALBEDO;
}
