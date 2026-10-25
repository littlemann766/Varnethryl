// Lava Wave v3: curling crest. TorusMesh (inner 0.92, outer 1.0, rings 64, ring_segments 10) as a child of the wave root,
// placed at the wall top; its fat outer half reads as lava curling over toward the players. Opaque, emissive, 0 textures.
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled;
uniform float rise : hint_range(0.0, 1.0) = 1.0;
uniform vec3 hot : source_color = vec3(1.0, 0.62, 0.14);
uniform vec3 white_hot : source_color = vec3(1.0, 0.92, 0.6);
uniform vec3 crust : source_color = vec3(0.14, 0.035, 0.01);
uniform float intensity : hint_range(0.0, 8.0) = 3.0;
varying vec3 wp;
varying vec3 lpos;
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

// v3.2 terrain follow: wb_lava_wave.gd raycasts GH_N ground heights around the ring (world metres relative to the wave root,
// index i at local angle i*360/GH_N, atan2(z,x)) and uploads them; vertex() lifts each vertex by the interpolated height.
uniform bool follow_ground = false;
uniform float ground_h[64];
float gh_at(vec2 xz) {
	float f = fract(atan(xz.y, xz.x) / 6.2831853 + 1.0) * 64.0;
	int i0 = int(floor(f)) % 64; int i1 = (i0 + 1) % 64;
	return mix(ground_h[i0], ground_h[i1], fract(f));
}
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
	return mix(mix(h21(i),h21(i+vec2(1,0)),f.x), mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x), f.y); }
void vertex() {
	lpos = VERTEX;
	// curl: push the outer/top of the tube outward and down, wobble along the ring
	float ang = atan(VERTEX.z, VERTEX.x);
	float wob = sin(ang * 23.0 + TIME * 2.0) * 0.012 + sin(ang * 57.0 - TIME * 3.1) * 0.006;
	vec2 dir = normalize(VERTEX.xz);
	VERTEX.xz += dir * (max(VERTEX.y, 0.0) * 1.5 + wob);
	VERTEX.y *= (0.4 + 0.6 * rise);
	if (follow_ground) VERTEX.y += gh_at(lpos.xz) / max(length(MODEL_MATRIX[1].xyz), 0.001);
	wp = VERTEX;
}
void fragment() {
	float ang = atan(wp.z, wp.x);
	float fl = vn(vec2(ang * 60.0 + TIME * 0.4, UV.y * 6.0 - TIME * 2.2)) * 0.6 + vn(vec2(ang * 140.0, UV.y * 12.0 - TIME * 3.5)) * 0.4;
	float plates = smoothstep(0.62, 0.72, fl);
	float top = smoothstep(0.0, 0.03, wp.y * 10.0);
	vec3 col = mix(hot, white_hot, smoothstep(0.4, 0.9, fl) * top);
	col = mix(col, crust, plates * 0.7);
	float gd = gap_dist(lpos.xz);
	if (gd < 0.0) discard;
	col = mix(col, crust, (1.0 - smoothstep(0.0, gap_edge_deg * 1.5, gd)) * 0.85);
	ALBEDO = col * intensity * (0.5 + 0.5 * rise);
}
