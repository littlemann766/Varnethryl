shader_type spatial;
// Beth: VARNETHRYL wildflowers. One mesh for every species; the species, size and sway phase ride in INSTANCE_CUSTOM.
// UV2.x marks the part (0 = stem/leaf card, 1 = flower head card). Petals are drawn procedurally (alpha scissor, no textures).
render_mode cull_disabled, depth_draw_opaque;
uniform float fade_start = 55.0;   // distance fade: the flower shrinks into the grass between start and end
uniform float fade_end = 70.0;
uniform float near_cut = 0.0;      // lod1 chunks: shrink IN between near_cut-6 and near_cut (cross-fade with lod0)
uniform float wind_strength = 1.0;
varying float part;
varying float species;
varying float tintv;
const vec3 PETAL[8] = vec3[8](
	vec3(1.00, 0.80, 0.16),  // 0 Sunpenny     - golden daisy, brown eye (meadow, roadside)
	vec3(0.30, 0.52, 1.00),  // 1 Skyglass     - five-point blue star (meadow, high grass)
	vec3(0.92, 0.14, 0.10),  // 2 Hearthpoppy  - red four-petal cup, dark heart (cottages, farm, meadow)
	vec3(0.62, 0.28, 0.86),  // 3 Duskthistle  - violet puff (meadow, roadside)
	vec3(1.00, 0.52, 0.12),  // 4 Emberbell    - nodding orange bells (roadside, cottages)
	vec3(0.95, 0.96, 1.00),  // 5 Marshlantern - clustered white lanterns (lake + pond shore)
	vec3(1.00, 0.55, 0.72),  // 6 Rosebutton   - pink double button (cottage gardens, farm)
	vec3(0.70, 0.62, 1.00)); // 7 Reedbell     - lilac spike (water's edge)
void vertex(){
	part = UV2.x;
	species = floor(INSTANCE_CUSTOM.r * 8.0 + 0.5);
	tintv = INSTANCE_CUSTOM.a;
	vec3 org = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float d = distance(org, CAMERA_POSITION_WORLD);
	float s = 1.0 - smoothstep(fade_start, fade_end, d);
	if (near_cut > 0.0) s *= smoothstep(near_cut - 6.0, near_cut, d);
	float h = max(VERTEX.y, 0.0);
	float t = TIME * 1.6 + INSTANCE_CUSTOM.b * 6.283 + org.x * 0.13 + org.z * 0.09;
	float w = (sin(t) * 0.7 + sin(t * 2.7) * 0.3) * h * h * 0.18 * wind_strength;
	VERTEX.x += w; VERTEX.z += w * 0.45;
	VERTEX *= s;
	if (part > 0.5) NORMAL = normalize(mix(NORMAL, vec3(0.0, 1.0, 0.0), 0.6));
}
float petals(vec2 q, float n, float round_, float rmax){
	float r = length(q); float a = atan(q.y, q.x);
	float edge = rmax * mix(abs(cos(a * n * 0.5)), 1.0, round_);
	return step(r, edge);
}
void fragment(){
	vec2 uv = UV;
	vec3 col; float keep = 0.0;
	int sp = int(species);
	vec3 pc = PETAL[sp] * (0.88 + 0.24 * tintv);
	if (part < 0.5) {
		// stem + two leaves
		float stem = step(abs(uv.x - 0.5), 0.035);
		vec2 l1 = (uv - vec2(0.33, 0.72)) * vec2(1.0, 2.6); vec2 l2 = (uv - vec2(0.67, 0.58)) * vec2(1.0, 2.6);
		float leaf = max(step(length(l1), 0.17), step(length(l2), 0.15));
		keep = max(stem * step(0.05, uv.y), leaf);
		col = mix(vec3(0.20, 0.38, 0.10), vec3(0.30, 0.50, 0.14), uv.y);
		if (sp == 7) { // reedbell: lilac florets up the spike, on the stem card
			float spike = step(abs(uv.x - 0.5), 0.09 * (1.0 - uv.y * 0.9)) * step(uv.y, 0.45) * step(0.5, fract(uv.y * 14.0) + 0.2);
			keep = max(keep, spike); col = mix(col, pc, spike);
		}
		if (sp == 4) { // emberbell: two nodding bells hanging off the stem card
			vec2 b1 = (uv - vec2(0.30, 0.20)) * vec2(1.0, 1.3); vec2 b2 = (uv - vec2(0.70, 0.30)) * vec2(1.0, 1.3);
			float bell = max(step(length(b1), 0.11) * step(0.15, uv.y), step(length(b2), 0.10) * step(0.26, uv.y));
			keep = max(keep, bell); col = mix(col, pc * (0.8 + 0.4 * uv.y), bell);
		}
	} else {
		vec2 q = uv * 2.0 - 1.0; float r = length(q);
		if (sp == 0) { keep = petals(q, 12.0, 0.35, 0.95); col = mix(vec3(0.35, 0.2, 0.06), pc, step(0.28, r)); }
		else if (sp == 1) { keep = petals(q, 5.0, 0.15, 0.95); col = mix(vec3(1.0, 0.95, 0.7), pc * (0.75 + 0.35 * r), step(0.18, r)); }
		else if (sp == 2) { keep = petals(q, 4.0, 0.7, 0.92); col = mix(vec3(0.08, 0.04, 0.05), pc * (0.8 + 0.25 * r), step(0.2, r)); }
		else if (sp == 3) { float fz = fract(sin(dot(floor(q * 9.0), vec2(12.9, 78.2))) * 437.5); keep = step(r, 0.55 + 0.35 * fz); col = pc * (0.75 + 0.4 * fz); }
		else if (sp == 4) { keep = petals(q, 6.0, 0.5, 0.45); col = pc * 0.9; }
		else if (sp == 5) { vec2 c = fract(q * 1.6 + 0.5) - 0.5; keep = step(length(c), 0.3) * step(r, 0.95); col = mix(pc, vec3(1.0, 0.92, 0.55), step(0.7, r) * 0.0 + step(length(c), 0.09)); }
		else if (sp == 6) { keep = max(petals(q, 8.0, 0.55, 0.9), petals(q * 1.5, 8.0, 0.55, 0.9)); col = pc * mix(1.15, 0.8, r); }
		else { keep = step(r, 0.35); col = pc; }
	}
	if (keep < 0.5) discard;
	ALBEDO = col;
	ROUGHNESS = 0.8; SPECULAR = 0.25;
	BACKLIGHT = col * 0.35;
}
