shader_type spatial;
// Beth land4 terrain. Baked COLOR is the biome. This pass is the ground itself:
// crisp near detail, slope rock, a rocky waterline, and snow that keeps its shape.
// Same uniforms as land1-3. No textures. hero_cut kept.
uniform int region = 0;
uniform float lift = 0.03;
uniform float ambient = 0.35;
uniform float spec = 0.4;
uniform float detail = 1.0;
global uniform vec4 hero_cut;
varying vec3 wpos;
varying vec3 wnrm;
float h21(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vn(vec2 p) { vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p) { float s = 0.0, a = 0.5; for (int i = 0; i < 4; i++) { s += a * vn(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }
float fbm2(vec2 p) { return vn(p) * 0.65 + vn(p * 2.07 + 5.3) * 0.35; }
vec2 warp(vec2 p, float k) { return p + vec2(fbm(p * 0.37 + 2.1) - 0.5, fbm(p * 0.41 - 8.0) - 0.5) * k; }
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz); }
void fragment() {
	float d = fract(sin(dot(floor(FRAGCOORD.xy), vec2(12.9898, 78.233))) * 43758.5453);
	if (d > smoothstep(0.8, 3.0, length(VERTEX))) discard;
	if (hero_cut.w > 0.5 && wpos.y > hero_cut.y - 0.9) {
		vec3 hv = (VIEW_MATRIX * vec4(hero_cut.xyz, 1.0)).xyz;
		if (-VERTEX.z < -hv.z - 1.0) {
			float ang = acos(clamp(dot(normalize(VERTEX), normalize(hv)), -1.0, 1.0));
			float r = atan(2.2 / max(length(hv), 0.1));
			if (d < smoothstep(r, r * 0.6, ang) * 0.9) discard;
		}
	}
	vec3 fn = normalize(cross(dFdx(VERTEX), dFdy(VERTEX)));
	if (dot(fn, -VERTEX) < 0.0) fn = -fn;
	vec3 base = COLOR.rgb;
	if (COLOR.a < 0.5) {
		ALBEDO = base * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
		NORMAL = fn; EMISSION = ALBEDO * ambient; ROUGHNESS = 0.9; SPECULAR = 0.5;
	} else {
		float dist = length(VERTEX);
		vec2 xz = wpos.xz;
		// metres of ground under one pixel. Grazing views cover many metres and must drop the fine grain
		// or it stretches into streaks. Frequencies below are isotropic (same scale in x and z).
		float px = max(length(dFdx(xz)), length(dFdy(xz)));
		float fineW = (1.0 - smoothstep(0.045, 0.14, px)) * detail;   // ~8 cm grain, only when resolved
		float midW = 1.0 - smoothstep(0.22, 0.85, px);                 // ~0.8 m clumps
		vec3 n = normalize(wnrm);
		float slope = 1.0 - n.y;
		float nFar = fbm(xz * 0.04);
		// two scales that are not integer multiples, so the value-noise lattice does not read as tiles
		float nMid = fbm(xz * 0.73) * 0.55 + fbm(xz * 1.91 + 13.0) * 0.45;
		float nFine = fbm2(xz * 4.7) * 0.5 + fbm2(xz * 9.3 + 4.0) * 0.5;
		float lum = dot(base, vec3(0.3, 0.59, 0.11));
		float sat = max(base.r, max(base.g, base.b)) - min(base.r, min(base.g, base.b));
		float wob = fbm(xz * 0.016) - 0.5;
		// classify from the baked colour. Thresholds stay tight so green islands do not turn to snow.
		float wgrass = smoothstep(0.0, 0.08, base.g - max(base.r, base.b) + wob * 0.03);
		float wsnow = smoothstep(0.62, 0.82, lum + wob * 0.04) * smoothstep(0.16, 0.04, sat);
		float wsand = smoothstep(0.01, 0.09, base.r - base.b + wob * 0.03) * (1.0 - wgrass) * (1.0 - wsnow);
		// waterline wanders by about a metre, then stops. It does not climb the hill.
		float shore_h = 0.9 + fbm(xz * 0.02) * 1.1;
		float shore = smoothstep(shore_h + 1.1, shore_h - 0.15, wpos.y);
		float wet = smoothstep(shore_h + 0.05, shore_h - 0.8, wpos.y);
		// slope rock only. No height cutoff: a height cutoff drew a hard horizontal band across frost cliffs.
		float rockv = smoothstep(0.18 + wob * 0.05, 0.40, slope);
		vec3 dirt = vec3(0.33, 0.25, 0.16);
		vec3 col = base * (0.9 + nFar * 0.18);
		// GRASS. Three round scales. Fine grain turns off when a pixel covers more than ~10 cm,
		// which is what stretched the old 4:1 blade noise into foreground streaks.
		vec3 g = col;
		g = mix(g, g * vec3(1.06, 0.97, 0.68), smoothstep(0.58, 0.84, nFar) * 0.4);
		g = mix(g, g * vec3(0.75, 0.95, 0.78), smoothstep(0.48, 0.22, nFar) * 0.3);
		g = mix(g, dirt, smoothstep(0.68, 0.88, nMid) * 0.28 * midW);
		g *= mix(1.0, 0.9 + (nMid - 0.5) * 0.16, midW);
		g *= mix(1.0, 0.82 + (nFine - 0.5) * 0.28, fineW);
		// SAND. Isotropic ripples, wet only in the last metre.
		vec3 s = col * (0.97 + 0.06 * (nFine - 0.5) * fineW);
		s = mix(s, s * vec3(0.6, 0.58, 0.52), wet);
		s = mix(s, s * vec3(0.8, 0.74, 0.58), shore * (1.0 - wet) * 0.4);
		// SNOW. Flats stay light. The face is rock, not a second white, and there is no Y stripe.
		vec3 sn = vec3(0.70, 0.74, 0.78) * (0.86 + nFar * 0.2);
		sn = mix(sn, vec3(0.40, 0.48, 0.60), smoothstep(0.62, 0.32, nMid) * 0.35 * midW);
		vec3 rk = region == 0 ? vec3(0.36, 0.34, 0.30) : region == 1 ? vec3(0.48, 0.38, 0.28) : region == 2 ? vec3(0.25, 0.34, 0.46) : vec3(0.10, 0.095, 0.09);
		rk = mix(rk, col, 0.15);
		rk *= 0.84 + fbm(xz * 0.35) * 0.22;
		if (region == 1) rk = mix(rk, vec3(0.7, 0.68, 0.6), smoothstep(0.82, 0.96, nFine) * 0.15 * fineW * (1.0 - slope));
		if (region == 3) rk += vec3(0.4, 0.09, 0.02) * smoothstep(0.02, 0.0, abs(fbm(xz * 0.03) - 0.5)) * 0.3 * (1.0 - slope);
		vec3 ground = col;
		ground = mix(ground, g, wgrass * (1.0 - rockv));
		ground = mix(ground, s, max(wsand, shore * (1.0 - wsnow) * (region == 2 ? 0.2 : 0.75)) * (1.0 - rockv));
		ground = mix(ground, sn, wsnow * (1.0 - rockv));
		ground = mix(ground, rk, rockv);
		if (region == 1) ground = mix(ground, vec3(0.76, 0.8, 0.78), smoothstep(0.72, 0.9, nMid) * (1.0 - rockv) * (1.0 - wgrass) * 0.3);
		if (region == 3) {
			ground = mix(ground, vec3(0.09, 0.085, 0.08), 0.45 * (1.0 - rockv));
			ground = mix(ground, vec3(0.22, 0.2, 0.18), smoothstep(0.62, 0.86, nFar) * 0.3 * (1.0 - rockv));
			ground = mix(ground, vec3(0.28, 0.22, 0.05), smoothstep(0.8, 0.94, nMid) * 0.35 * (1.0 - rockv));
		}
		ALBEDO = ground * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
		float e = 0.12;
		float hb = fbm2(xz * 8.0);
		float hx = fbm2((xz + vec2(e, 0.0)) * 8.0) - hb;
		float hz = fbm2((xz + vec2(0.0, e)) * 8.0) - hb;
		vec3 wn = normalize(n - vec3(hx, 0.0, hz) * fineW * 0.55);
		vec3 vn_ = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
		NORMAL = normalize(mix(vn_, fn, 0.35));
		EMISSION = ALBEDO * ambient * (1.0 - max(wsnow, rockv) * 0.55);
		if (region == 3) EMISSION += vec3(0.8, 0.22, 0.03) * smoothstep(0.02, 0.0, abs(fbm(xz * 0.03) - 0.5)) * (1.0 - slope) * 0.2 * midW;
		ROUGHNESS = mix(0.92, 0.62, wet * 0.4);
		SPECULAR = spec * (region == 2 ? 0.8 : 1.0);
	}
}
