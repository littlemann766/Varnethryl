shader_type spatial;
// Beth land4: land3 ground, with the tiling and the hard layer lines broken up.
// COLOR.rgb = baked biome colour (soft-blended). COLOR.a = 1 natural ground / 0 placed prop.
// Same uniforms as land1-3: lift, ambient, spec, region (0 A, 1 B, 2 frost, 3 ash), detail.
// Mobile-safe: no textures. hero_cut + near fade kept so gameplay clipping still matches.
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
// one domain warp, used everywhere a pattern used to repeat in a straight line
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
		float near = smoothstep(90.0, 14.0, dist) * detail;
		float near2 = smoothstep(36.0, 3.5, dist) * detail;
		float mid = smoothstep(460.0, 70.0, dist);
		vec2 xz = wpos.xz;
		vec2 xw = warp(xz, 6.0);
		vec3 n = normalize(wnrm);
		float slope = 1.0 - n.y;
		float macro = fbm(xw * 0.012);                 // ~80 m, warped so patches don't tile
		float meso = fbm(warp(xz, 6.0) * 0.07);
		float fine = fbm2(warp(xz, 1.4) * 1.35);
		float lum = dot(base, vec3(0.3, 0.59, 0.11));
		float sat = max(base.r, max(base.g, base.b)) - min(base.r, min(base.g, base.b));
		// wide, noise-wandered weights: the grass / sand / snow / rock borders are ragged, not contours
		float wob = (fbm(xz * 0.02 + macro) - 0.5);
		float wgrass = smoothstep(-0.02, 0.09, base.g - max(base.r, base.b) + wob * 0.07 + (meso - 0.5) * 0.05);
		float wsnow = smoothstep(0.50, 0.78, lum + wob * 0.10 + (meso - 0.5) * 0.08) * smoothstep(0.22, 0.05, sat);
		float wsand = smoothstep(0.0, 0.10, base.r - base.b + wob * 0.04) * (1.0 - wgrass) * smoothstep(0.20, 0.46, lum) * (1.0 - wsnow);
		// shore band follows a wandering height, so the wet line is not a bathtub ring
		float shore_h = 1.15 + fbm(xz * 0.018) * 1.9 + fbm(xz * 0.06) * 0.55;
		float shore = smoothstep(shore_h + 2.4, shore_h - 0.35, wpos.y);
		float wet = smoothstep(shore_h + 0.15, shore_h - 1.35, wpos.y);
		float rockv = smoothstep(0.16 + wob * 0.08 + (meso - 0.5) * 0.10, 0.46, slope);
		vec3 col = base * (0.84 + macro * 0.32);
		// GRASS: clumps at several sizes, rotated blade directions, dark gaps that are not a grid
		vec3 g = col;
		g = mix(g, g * vec3(1.10, 1.00, 0.68), smoothstep(0.58, 0.86, macro) * 0.55);
		g = mix(g, g * vec3(0.72, 0.92, 0.78), smoothstep(0.48, 0.18, meso) * 0.55);
		float clump = smoothstep(0.32, 0.72, fbm(warp(xz, 4.0) * 0.085));
		vec2 q1 = mat2(vec2(0.82, 0.57), vec2(-0.57, 0.82)) * xw;
		vec2 q2 = mat2(vec2(0.31, -0.95), vec2(0.95, 0.31)) * xz;
		vec2 q3 = mat2(vec2(-0.54, 0.84), vec2(-0.84, -0.54)) * warp(xz, 2.2);
		float b1 = fbm2(vec2(q1.x * 22.0, q1.y * 4.6) + fbm2(xz * 2.4) * 3.0);
		float b2 = fbm2(vec2(q2.x * 5.1, q2.y * 19.0) + fbm2(xz * 1.7 + 4.0) * 2.6);
		float b3 = fbm2(vec2(q3.x * 13.0, q3.y * 9.0) + fine);
		float blades = b1 * 0.42 + b2 * 0.36 + b3 * 0.22;
		g *= mix(1.0, 0.82 + fine * 0.16 + blades * 0.22, near);
		g *= mix(1.0, 0.78 + blades * 0.35, near2 * mix(0.55, 1.0, clump));
		g = mix(g, g * vec3(0.62, 0.74, 0.55), smoothstep(0.42, 0.18, blades) * near2 * 0.28 * clump);
		// soft flower drift — a blurred patch, not a grid of squares (hard hash cells stretch into quads on slopes)
		float bloom = smoothstep(0.68, 0.9, fbm2(warp(xz, 2.0) * 0.85));
		vec3 bloom_c = region == 1 ? vec3(0.62, 0.60, 0.46) : vec3(0.55, 0.52, 0.22);
		g = mix(g, g * 0.55 + bloom_c * 0.45, bloom * near2 * 0.28 * wgrass);
		vec3 dirt = vec3(0.30, 0.24, 0.17) * (0.8 + fine * 0.3);
		g = mix(g, dirt, smoothstep(0.62, 0.82, meso + fine * 0.06 * near) * 0.7);
		// SAND: warped ripples, not parallel stripes. Wet darkens toward the water.
		float rip = fbm2(warp(xz, 2.5) * vec2(1.6, 0.55) + meso);
		vec3 s = col * (0.94 + (region == 3 ? 0.0 : 0.10) * (rip - 0.5) * near);
		s = mix(s, s * vec3(0.55, 0.56, 0.58), wet);
		s = mix(s, s * vec3(0.72, 0.70, 0.62), shore * 0.65);
		// wrack specks on the wet line
		float wrack = smoothstep(0.72, 0.9, fbm2(warp(xz, 1.2) * 0.55)) * shore * (1.0 - wet);
		s = mix(s, s * vec3(0.55, 0.50, 0.40), wrack * near * 0.35);
		// SNOW: land3 off-white blue-grey, but the sastrugi are broad and quiet (the old tight ridges read as corrugation)
		vec3 sn = vec3(0.50, 0.555, 0.65) * (0.90 + (macro - 0.5) * 0.14);
		float drift = fbm(vec2(xw.x * 0.045 + fbm(xz * 0.02) * 2.0, xw.y * 0.11));
		float sast = fbm2(warp(xz, 3.0) * vec2(0.35, 0.9));
		sn *= 0.90 + drift * 0.16;
		sn = mix(sn, sn * vec3(0.74, 0.84, 1.0), smoothstep(0.42, 0.22, drift) * 0.55);
		sn *= mix(1.0, 0.92 + sast * 0.12, mid);   // land4: was a hard ridge; now a soft wind shade
		sn = mix(sn, sn * vec3(0.68, 0.80, 1.0), smoothstep(0.04, 0.34, slope));
		sn += vec3(0.05, 0.055, 0.06) * smoothstep(0.82, 0.97, fbm2(xz * 1.7)) * near2;
		// ROCK: region tone, faint warped bedding (not a stack of horizontal stripes), cracks, lichen / salt / ice
		vec3 rk = region == 0 ? vec3(0.40, 0.38, 0.35) : region == 1 ? vec3(0.47, 0.39, 0.30) : region == 2 ? vec3(0.36, 0.41, 0.49) : vec3(0.12, 0.11, 0.105);
		rk = mix(rk, col, region == 1 ? 0.14 : 0.28);
		float strata = sin(wpos.y * 0.22 + fbm(xz * 0.03 + wpos.y * 0.02) * 8.0 + wob * 6.0);
		float strata_amp = region == 2 ? 0.0 : region == 1 ? 0.05 : 0.07;
		rk *= 0.90 + strata_amp * strata * smoothstep(180.0, 28.0, dist);
		rk *= 0.86 + fbm(warp(vec2(xz.x + wpos.y * 0.4, xz.y - wpos.y * 0.3), 2.0) * 0.35) * 0.28;
		float crack = smoothstep(0.025, 0.0, abs(fbm(warp(vec2(xz.x * 0.55 + wpos.y * 0.35, xz.y * 0.55), 1.5)) - 0.5)) * near;
		rk *= 1.0 - crack * 0.45;
		if (region == 0) rk = mix(rk, vec3(0.40, 0.46, 0.30), smoothstep(0.58, 0.82, meso) * (1.0 - slope) * 0.55);
		if (region == 1) {
			rk = mix(rk, vec3(0.80, 0.82, 0.80), smoothstep(0.78, 0.94, fine) * 0.22 * near * (1.0 - slope));
			rk *= 0.88 + 0.22 * fbm(vec2(xz.x * 0.15 + xz.y * 0.05, wpos.y * 0.18));
		}
		if (region == 2) {
			float st = fbm(vec2((xz.x + xz.y) * 0.22 + wob, wpos.y * 0.035));
			rk = mix(vec3(0.58, 0.70, 0.82), vec3(0.74, 0.84, 0.93), smoothstep(0.30, 0.75, st));
			rk = mix(rk, rk * vec3(0.72, 0.82, 0.96), smoothstep(5.0, 0.0, wpos.y) * 0.45);
			rk *= 0.94 + 0.08 * fbm(xz * 0.08 + wpos.y * 0.02);
		}
		if (region == 3) rk += vec3(0.50, 0.12, 0.02) * smoothstep(0.012, 0.0, abs(fbm(warp(xz, 8.0) * 0.04) - 0.48)) * smoothstep(0.55, 0.8, macro) * 0.55 * (1.0 - slope);
		vec3 ground = col;
		ground = mix(ground, g, wgrass * (1.0 - rockv * 0.85));
		ground = mix(ground, s, max(wsand, shore * (1.0 - wsnow) * (region == 2 ? 0.35 : 0.72)));
		// foam freckles where the wet line crosses a fine crest
		float foam = smoothstep(0.78, 0.94, fine) * shore * (1.0 - wet) * (1.0 - wsnow) * near2;
		ground = mix(ground, vec3(0.75, 0.78, 0.74), foam * (region == 3 ? 0.08 : 0.22));
		ground = mix(ground, sn, wsnow * (1.0 - rockv * 0.75));
		ground = mix(ground, rk, rockv * (region == 2 ? 0.82 : 0.88));
		if (region == 1) ground = mix(ground, vec3(0.86, 0.90, 0.90), smoothstep(0.66, 0.9, meso + wob * 0.2) * (1.0 - rockv) * (1.0 - wgrass) * 0.42);
		if (region == 3) {
			float flow = fbm(warp(xz, 10.0) * 0.03);
			ground = mix(ground, vec3(0.10, 0.092, 0.088) * (0.78 + 0.4 * meso), 0.55 * (1.0 - rockv));
			ground = mix(ground, vec3(0.045, 0.040, 0.042), smoothstep(0.58, 0.82, flow) * 0.45 * (1.0 - rockv));
			ground = mix(ground, vec3(0.24, 0.22, 0.20) * (0.9 + 0.2 * fbm2(xz * 0.7)), smoothstep(0.62, 0.88, macro) * 0.38 * (1.0 - rockv));
			ground = mix(ground, vec3(0.32, 0.25, 0.05), smoothstep(0.78, 0.92, meso) * smoothstep(0.42, 0.2, macro) * 0.5);
			ground *= 1.0 - smoothstep(0.66, 0.78, fbm2(warp(xz, 1.2) * 4.0)) * 0.28 * near;
		}
		ground *= 0.94 + (fine - 0.5) * 0.18 * near;
		ALBEDO = ground * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
		float e = 0.55;
		vec2 bu = warp(xz, 1.1);
		float hb = fbm2(bu * 0.55) * (0.25 + rockv);
		float hx = fbm2((bu + vec2(e, 0.0)) * 0.55) * (0.25 + rockv) - hb;
		float hz = fbm2((bu + vec2(0.0, e)) * 0.55) * (0.25 + rockv) - hb;
		vec3 wn = normalize(n - vec3(hx, 0.0, hz) * (0.85 * near));
		// shore: ease the normal toward up so the lip doesn't catch a hard specular knife
		wn = normalize(mix(wn, vec3(0.0, 1.0, 0.0), shore * (1.0 - rockv) * 0.35));
		vec3 vn_ = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
		NORMAL = normalize(mix(vn_, fn, 0.16));
		EMISSION = ALBEDO * ambient * (1.0 - wsnow * 0.8);
		if (region == 3) EMISSION += vec3(1.0, 0.30, 0.05) * smoothstep(0.012, 0.0, abs(fbm(warp(xz, 8.0) * 0.04) - 0.48)) * smoothstep(0.55, 0.8, macro) * (1.0 - slope) * 0.32 * mid;
		ROUGHNESS = mix(0.94, 0.58, max(wsnow * (1.0 - rockv), wet * 0.35)) - (region == 3 ? 0.08 : 0.0);
		SPECULAR = spec;
	}
}
