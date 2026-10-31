// Lava Wave: rising molten wall. Open CylinderMesh (radius 1, height 1, no caps, 48 segs), scale (R, wall_h, R).
// rise 0..1 grows the wall over the 10 s wind-up. Whole wall is molten: dark crust plates drifting on bright flowing lava,
// hot glowing crest lip, darker base. ground_mode=true on a flat strip = warning band (UV.y across the band).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;
uniform float rise : hint_range(0.0, 1.0) = 0.0;
uniform vec3 hot : source_color = vec3(1.0, 0.62, 0.14);
uniform vec3 mid : source_color = vec3(0.95, 0.25, 0.03);
uniform vec3 crust : source_color = vec3(0.12, 0.03, 0.01);
uniform float intensity : hint_range(0.0, 8.0) = 2.8;
uniform bool ground_mode = false;
uniform bool use_gaps = false;
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
uniform float ground_sink = 1.0; // m the wall base is pushed below the sampled ground (hides seams between samples)
varying vec3 lpos;
void vertex() {
	lpos = VERTEX;
	if (follow_ground && !ground_mode) {
		float sy = max(length(MODEL_MATRIX[1].xyz), 0.001);
		VERTEX.y += (gh_at(VERTEX.xz) - step(VERTEX.y, 0.0) * ground_sink) / sy;
	}
}
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
	return mix(mix(h21(i),h21(i+vec2(1,0)),f.x), mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x), f.y); }
float fbm(vec2 p){ return vn(p)*0.55 + vn(p*2.1+3.1)*0.3 + vn(p*4.3+7.7)*0.15; }
void fragment() {
	vec2 uv = vec2(UV.x * 48.0, ground_mode ? UV.y * 3.0 : (1.0 - UV.y) * 6.0);
	float y = ground_mode ? abs(UV.y * 2.0 - 1.0) : 1.0 - UV.y;   // 0 = base/centre, 1 = top/edge
	// lava pours up-and-over: flow scrolls upward, crust plates drift slower
	float fl = fbm(uv * vec2(1.0, 1.6) + vec2(TIME * 0.15, -TIME * 1.2));
	float cr = fbm(uv * 1.3 + vec2(-TIME * 0.08, -TIME * 0.45) + fl * 1.2);
	float plates = smoothstep(0.52, 0.62, cr);                      // dark crust islands
	float seams = 1.0 - smoothstep(0.0, 0.08, abs(cr - 0.57));      // glowing seams around plates
	vec3 lava = mix(mid, hot, smoothstep(0.35, 0.8, fl));
	vec3 col = mix(lava, crust, plates * 0.85) + hot * seams * 0.6;
	float a;
	if (ground_mode) {
		float band = smoothstep(1.0, 0.75, y);
		float pulse = 0.55 + 0.45 * sin(TIME * 5.0 - UV.x * 60.0);
		// v2: outward chevrons show which way the wave travels; brighter outer edge line
		float chev = step(0.5, fract(UV.x * 96.0 + abs(UV.y * 2.0 - 1.0) * 1.5 - TIME * 1.2)) * smoothstep(0.85, 0.6, y);
		float lineo = smoothstep(0.08, 0.0, abs(y - 0.92));
		col = mix(col, hot, 0.3 + chev * 0.35 + lineo * 0.5) * (0.6 + 0.6 * rise);
		a = max(band * (0.45 + 0.35 * pulse + chev * 0.2) * (0.35 + 0.65 * rise), lineo);
	} else {
		float crest = rise + 0.05 * (fbm(vec2(UV.x * 30.0 + TIME, TIME * 2.0)) - 0.5);
		float body = smoothstep(crest + 0.01, crest - 0.02, y);
		float lip = smoothstep(0.07, 0.0, abs(y - crest)) * step(0.0, crest - 0.02);
		col = mix(col, crust * 1.5, smoothstep(0.25, 0.0, y) * 0.6);     // darker base where it meets the ground
		col = mix(col, vec3(1.0, 0.9, 0.55), lip * 0.85);
		// v2: bright spill streaks pouring down the face + glow band where it meets the ground
		float spill = smoothstep(0.82, 1.0, vn(vec2(UV.x * 140.0, (1.0 - UV.y) * 2.0 + TIME * 1.6))) * body;
		col += hot * spill * 0.8 + hot * smoothstep(0.08, 0.0, y) * 0.6;
		a = max(body * 0.97, lip);
	}
	if (!ground_mode) {
		float gd = gap_dist(lpos.xz);
		if (gd < 0.0) discard;
		float cool = (1.0 - smoothstep(0.0, gap_edge_deg, gd));              // lava cools to dark crust at the gap edge
		float rock = vn(vec2(UV.x * 300.0, UV.y * 20.0));
		vec3 cooled = crust * (1.2 + rock) + hot * 0.15 * step(0.8, rock);        // dark cooled rock with a few embers
		col = mix(col, cooled, pow(cool, 0.7));
		a = max(a, step(0.001, a) * cool);
	}
	ALBEDO = col * intensity * 0.6;
	ALPHA = clamp(a, 0.0, 1.0);
}
