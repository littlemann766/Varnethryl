// Meteor target / stomp warning circle v2. Procedural (0 textures). 1x1 PlaneMesh scaled to radius*2 (e.g. 14 m).
// progress 0..1 = time until impact. v2: thick double rim (reads as a bold ellipse at eye height), chevron rings crawling
// inward, danger fill that darkens+reddens toward impact, outer soft halo, strobe in the last 15%. Pair with wb_meteor_beam.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;
uniform vec3 color : source_color = vec3(1.0, 0.2, 0.05);
uniform vec3 hot : source_color = vec3(1.0, 0.75, 0.3);
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform float intensity : hint_range(0.0, 8.0) = 2.5;
void fragment() {
	vec2 p = UV * 2.0 - 1.0; float r = length(p); float a = atan(p.y, p.x);
	if (r > 1.08) discard;
	float rim = smoothstep(0.88, 0.92, r) * smoothstep(1.0, 0.97, r);
	float rim2 = smoothstep(0.80, 0.815, r) * smoothstep(0.835, 0.82, r) * 0.7;
	float halo = smoothstep(1.08, 1.0, r) * step(1.0, r) * 0.5;
	float seg = step(0.35, fract(a * 16.0 / 6.2831 + TIME * 0.4));
	float chev = smoothstep(0.1, 0.0, abs(fract(r * 3.0 + TIME * (0.6 + progress * 1.8)) - 0.5) - 0.32) * step(r, 0.8) * seg * 0.55;
	float fill = smoothstep(progress + 0.02, progress - 0.02, r);
	float edge = smoothstep(0.035, 0.0, abs(r - progress)) * step(r, 0.8);
	float cross = (smoothstep(0.03, 0.0, abs(p.x)) + smoothstep(0.03, 0.0, abs(p.y))) * step(r, 0.18);
	float strobe = progress > 0.85 ? 0.55 + 0.45 * step(0.5, fract(TIME * 7.0)) : 1.0;
	float glow = (rim + rim2 + halo + chev + edge * 1.2 + cross) * strobe;
	vec3 col = mix(color, hot, rim * 0.5 + edge * 0.6) * glow * intensity;
	vec3 base = mix(vec3(0.05, 0.0, 0.0), color * 0.6, progress);
	ALBEDO = col + base * fill * (0.25 + 0.35 * progress);
	ALPHA = clamp(glow + fill * (0.18 + 0.32 * progress), 0.0, 1.0);
}
