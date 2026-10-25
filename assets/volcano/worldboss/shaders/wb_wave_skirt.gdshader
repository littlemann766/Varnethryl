// Lava Wave v3: ground glow skirt + heat-haze bands ahead of the wall. PlaneMesh 2x2 child of the wave root (scale 1.0;
// the root's x/z scale = wave radius). Draws an annulus from r=1.0 (wall) out to r=skirt_out. Additive, 0 textures, no screen reads
// (heat haze is faked with bright shimmer bands racing outward, which is what reads on a phone).
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled;
uniform float rise : hint_range(0.0, 1.0) = 1.0;
uniform vec3 hot : source_color = vec3(1.0, 0.42, 0.08);
uniform float skirt_out = 1.35;
uniform vec3 safe_col : source_color = vec3(0.35, 0.85, 1.0); // subtle safe marker at gap edges
uniform float safe_strength : hint_range(0.0, 4.0) = 1.2;
uniform bool use_gaps = true;
uniform int gap_count : hint_range(0, 8) = 4;
uniform float gap_width_deg : hint_range(0.0, 30.0) = 6.5;  // 9 m at 80 m radius
uniform float gap_offset_deg = 0.0;                          // rotate per cast
uniform float gap_edge_deg : hint_range(0.0, 15.0) = 5.0;    // cooled dark rim beside each gap
// returns signed angular distance (deg) from the nearest gap edge: <0 inside the gap
float gap_dist(vec2 xz) {
	if (!use_gaps || gap_count <= 0) return 999.0;
	float a = degrees(atan(xz.y, xz.x)) - gap_offset_deg;
	float step_deg = 360.0 / float(gap_count);
	float m = mod(a + step_deg * 0.5, step_deg) - step_deg * 0.5; // centred on a gap at 0
	return abs(m) - gap_width_deg * 0.5;
}
uniform float intensity : hint_range(0.0, 8.0) = 3.0;
void fragment() {
	vec2 p = (UV * 2.0 - 1.0) * skirt_out; float r = length(p); float a = atan(p.y, p.x);
	if (r < 0.97 || r > skirt_out) discard;
	float t = (r - 1.0) / (skirt_out - 1.0);                      // 0 at the wall .. 1 at the outer edge
	float glow = exp(-t * 4.0);
	float bands = pow(0.5 + 0.5 * sin(t * 40.0 - TIME * 6.0 + sin(a * 30.0) * 0.6), 6.0) * (1.0 - t);
	float flick = 0.85 + 0.15 * sin(a * 90.0 + TIME * 4.0);
	float edge = smoothstep(0.04, 0.0, abs(t - 0.98)) * 0.6;       // outer warning line = "outrun this"
	float gd = gap_dist(p);
	vec3 lava_c = hot * (glow * 1.2 + bands * 0.7 + edge) * flick * intensity * (0.3 + 0.7 * rise);
	lava_c *= smoothstep(0.0, gap_edge_deg, gd);                     // fade the heat out toward the gap
	// safe marker: two thin cool lines on the gap edges + faint chevrons pointing through the gap
	float line = smoothstep(0.6, 0.0, abs(gd + 0.4)) ;
	float inside = step(gd, 0.0);
	float chev = inside * step(0.6, fract(t * 6.0 - TIME * 0.8)) * 0.25;
	ALBEDO = lava_c + safe_col * (line * 1.0 + chev) * safe_strength * (0.4 + 0.6 * rise) * (1.0 - t * 0.5);
}
