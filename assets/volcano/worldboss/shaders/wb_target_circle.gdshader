// Meteor target / stomp warning circle. Procedural (0 textures). Put on a 1x1 PlaneMesh scaled to the radius*2.
// progress 0..1 = time until impact: inner disc fills toward the rim; strobe in the last 15%.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled;
uniform vec3 color : source_color = vec3(1.0, 0.18, 0.06);
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform float intensity : hint_range(0.0, 8.0) = 2.0;
void fragment() {
	vec2 p = UV * 2.0 - 1.0; float r = length(p); float a = atan(p.y, p.x);
	if (r > 1.0) discard;
	float rim = smoothstep(0.93, 0.97, r) * smoothstep(1.0, 0.98, r);
	float ticks = step(0.5, fract(a * 12.0 / 6.2831 - TIME * 0.3)) * smoothstep(0.84, 0.86, r) * smoothstep(0.91, 0.89, r);
	float fill = smoothstep(progress + 0.01, progress - 0.01, r) * 0.28;
	float edge = smoothstep(0.03, 0.0, abs(r - progress)) * 0.9;
	float cross = (smoothstep(0.02, 0.0, abs(p.x)) + smoothstep(0.02, 0.0, abs(p.y))) * step(r, 0.15);
	float strobe = progress > 0.85 ? 0.6 + 0.4 * step(0.5, fract(TIME * 6.0)) : 1.0;
	float v = (rim + ticks * 0.6 + fill + edge + cross) * strobe;
	ALBEDO = color * v * intensity; ALPHA = clamp(v, 0.0, 1.0);
}
