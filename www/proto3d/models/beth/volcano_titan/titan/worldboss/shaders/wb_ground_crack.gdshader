// Growing ground crack (radial Fissure Slam telegraph or straight fissure line). Unshaded additive-ish blend on a flat quad / PlaneMesh.
// tex: R crack mask, G reveal coordinate (radius or length 0..1), B glow halo. progress 0..1 drives the spread over the 12 s wind-up.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;
uniform sampler2D crack_tex : hint_default_black, filter_linear_mipmap;
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform float erupt : hint_range(0.0, 1.0) = 0.0; // 1 = ritual completed, lava in cracks
uniform vec3 hot : source_color = vec3(1.0, 0.55, 0.12);
uniform vec3 char_col : source_color = vec3(0.03, 0.02, 0.02);
uniform float intensity : hint_range(0.0, 8.0) = 3.0;
void fragment() {
	vec4 t = texture(crack_tex, UV);
	float edge = progress * 1.08 - t.g;            // >0 where revealed
	float rev = smoothstep(0.0, 0.06, edge);
	float front = smoothstep(0.08, 0.0, abs(edge)) * step(0.0, edge + 0.02); // bright leading edge
	float c = t.r * rev;
	float flick = 0.8 + 0.2 * sin(TIME * 9.0 + t.g * 40.0);
	vec3 col = hot * (c * (1.0 + front * 2.0) * flick + t.b * rev * 0.35 * (1.0 + erupt * 2.0));
	ALBEDO = mix(char_col, col * intensity, clamp(c + front * t.b, 0.0, 1.0));
	EMISSION = col * intensity;
	ALPHA = clamp(max(c, t.b * rev * (0.45 + erupt * 0.4)), 0.0, 1.0);
}
