// Lava Wave: rising lava ring wall. Use on an open CylinderMesh (top/bottom caps off, radius 1, height 1) scaled to radius 80 m x wall height.
// rise 0..1 grows the wall during the 10 s wind-up; also usable flat (ground_mode) as the warning strip on a ring/plane.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled;
uniform float rise : hint_range(0.0, 1.0) = 0.0;
uniform vec3 hot : source_color = vec3(1.0, 0.5, 0.08);
uniform vec3 deep : source_color = vec3(0.6, 0.06, 0.0);
uniform float intensity : hint_range(0.0, 8.0) = 2.5;
uniform bool ground_mode = false; // true on a flat strip: UV.y across the strip
float n(vec2 x){ return sin(x.x) * sin(x.y * 1.3 + 1.7); }
void fragment() {
	float u = UV.x * 40.0; float y = ground_mode ? abs(UV.y * 2.0 - 1.0) : 1.0 - UV.y; // 0 bottom/centre .. 1 top/edge
	float crest = rise + 0.06 * n(vec2(u + TIME * 2.0, TIME * 3.0));
	float body = ground_mode ? smoothstep(1.0, 0.6, y) * (0.5 + 0.5 * sin(UV.x * 300.0 - TIME * 8.0)) * (0.4 + rise) : step(y, crest);
	float lip = ground_mode ? smoothstep(0.9, 1.0, y) * 0.0 : smoothstep(0.08, 0.0, abs(y - crest));
	float flow = 0.6 + 0.4 * n(vec2(u * 0.7, y * 12.0 - TIME * 4.0));
	vec3 col = mix(deep, hot, clamp(flow * 0.8 + lip, 0.0, 1.0));
	float a = clamp(body * (ground_mode ? 1.0 : 0.85 - y * 0.4) + lip, 0.0, 1.0);
	ALBEDO = col * intensity * a; ALPHA = a;
}
