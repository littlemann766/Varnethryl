// Growing ground crack v2 (radial Fissure Slam telegraph or straight fissure line). Flat quad / PlaneMesh, Mobile-safe (5 samples).
// tex: R crack mask, G reveal coordinate (radius or length 0..1), B glow halo. progress 0..1 drives the spread over the 12 s wind-up.
// v2: cracks widened by a 5-tap max (stay readable at grazing angles from 1.7 m eye height on a 120 m decal), scorched ground
// behind the front, pulses racing outward along the cracks, brighter leading edge, ember flicker; erupt=1 floods with lava.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;
uniform sampler2D crack_tex : hint_default_black, filter_linear_mipmap;
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform float erupt : hint_range(0.0, 1.0) = 0.0;
uniform vec3 hot : source_color = vec3(1.0, 0.55, 0.12);
uniform vec3 white_hot : source_color = vec3(1.0, 0.9, 0.6);
uniform vec3 char_col : source_color = vec3(0.03, 0.02, 0.02);
uniform float intensity : hint_range(0.0, 8.0) = 3.5;
uniform float widen : hint_range(0.0, 0.01) = 0.0025; // UV units; ~0.3 m on a 120 m decal
uniform float scorch : hint_range(0.0, 1.0) = 0.45;
void fragment() {
	vec4 t = texture(crack_tex, UV);
	float r = t.r;
	r = max(r, texture(crack_tex, UV + vec2(widen, 0.0)).r);
	r = max(r, texture(crack_tex, UV - vec2(widen, 0.0)).r);
	r = max(r, texture(crack_tex, UV + vec2(0.0, widen)).r);
	r = max(r, texture(crack_tex, UV - vec2(0.0, widen)).r);
	float edge = progress * 1.08 - t.g;
	float rev = smoothstep(0.0, 0.06, edge);
	float front = smoothstep(0.07, 0.0, abs(edge)) * step(0.0, edge + 0.02);
	float race = pow(0.5 + 0.5 * sin(t.g * 55.0 - TIME * 7.0), 6.0);     // pulses running outward
	float flick = 0.8 + 0.2 * sin(TIME * 9.0 + t.g * 40.0);
	float core = smoothstep(0.55, 0.95, t.r);                              // thin white-hot centre line
	float c = r * rev;
	vec3 col = mix(hot, white_hot, core * 0.7 + front * 0.6) * (c * (1.0 + front * 2.5 + race * 1.2) * flick);
	col += hot * t.b * rev * (0.4 + erupt * 1.6) * (0.7 + 0.3 * race);
	float burnt = rev * scorch * smoothstep(1.0, 0.0, t.g) * 0.8;          // darkened ground behind the front
	float a = max(max(c, t.b * rev * (0.5 + erupt * 0.4)), burnt);
	ALBEDO = mix(char_col, col * intensity, clamp(c + front * t.b + t.b * rev * 0.5, 0.0, 1.0));
	ALPHA = clamp(a, 0.0, 1.0);
}
