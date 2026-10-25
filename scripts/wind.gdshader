shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap;
uniform vec4 tint : source_color = vec4(1.0);
uniform float sway = 0.06;
uniform float alpha_cut = 0.5;
void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(0.0,0.0,0.0,1.0)).xyz;
	float h = max(VERTEX.y, 0.0);
	float t = TIME * 1.6 + wp.x * 0.07 + wp.z * 0.05;
	VERTEX.x += sin(t) * sway * h * h * 0.15;
	VERTEX.z += cos(t * 0.8) * sway * h * h * 0.1;
}
void fragment() {
	vec4 c = texture(albedo_tex, UV) * tint * COLOR;
	if (c.a < alpha_cut) discard;
	ALBEDO = c.rgb;
	ROUGHNESS = 0.9;
}
