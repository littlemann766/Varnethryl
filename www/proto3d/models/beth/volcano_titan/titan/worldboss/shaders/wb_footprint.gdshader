// 25 m footprint decal on a flat quad (PlaneMesh 1x1 scaled 25 x 25, lift 0.05 m). fade 1 -> 0 over 120 s; heat cools first.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, shadows_disabled;
uniform sampler2D foot_tex : hint_default_black, filter_linear_mipmap; // R depth, G rim, B cracks, A coverage
uniform float fade : hint_range(0.0, 1.0) = 1.0;
uniform float heat : hint_range(0.0, 1.0) = 1.0;
uniform vec3 ground_dark : source_color = vec3(0.05, 0.04, 0.035);
uniform vec3 rim_col : source_color = vec3(0.32, 0.27, 0.23);
void fragment() {
	vec4 t = texture(foot_tex, UV);
	ALBEDO = mix(mix(rim_col * 0.55, ground_dark, smoothstep(0.05, 0.6, t.r)), rim_col, t.g);
	ROUGHNESS = 1.0;
	EMISSION = vec3(1.0, 0.35, 0.05) * t.b * heat * 3.0 * (0.8 + 0.2 * sin(TIME * 3.0));
	ALPHA = t.a * fade;
}
