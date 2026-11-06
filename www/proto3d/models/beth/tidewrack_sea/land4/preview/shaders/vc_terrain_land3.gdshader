shader_type spatial;
// Beth land1: layered procedural ground for the Tidewrack island terrain (Mobile-safe, no textures).
// COLOR.rgb = baked biome colour (soft-blended across region borders), COLOR.a = 1 natural ground / 0 placed prop (keeps vc_flat look).
// Layers: grass (tufts, clover, dry patches), dirt, rock (slope-driven, warped strata, cracks), sand (ripples, wet shore), snow (drifts, blue shade).
uniform int region = 0;          // 0 Archipelago A, 1 Saltglass B, 2 Frost, 3 Ash
uniform float lift = 0.03;
uniform float ambient = 0.35;
uniform float spec = 0.4;
uniform float detail = 1.0;      // 0..1 (Low tier can pass 0.5)
global uniform vec4 hero_cut;
varying vec3 wpos;
varying vec3 wnrm;
float h21(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vn(vec2 p) { vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p) { float s = 0.0, a = 0.5; for (int i = 0; i < 4; i++) { s += a * vn(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }
float ridged_(vec2 p) { float s = 0.0, a = 0.5; for (int i = 0; i < 3; i++) { float v = 1.0 - abs(vn(p) * 2.0 - 1.0); s += a * v * v; p = p * 2.1 + 3.7; a *= 0.5; } return s / 0.875; }
float fbm2(vec2 p) { return vn(p) * 0.65 + vn(p * 2.1 + 5.3) * 0.35; }
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
	if (COLOR.a < 0.5) {   // placed props: unchanged vc_flat look
		ALBEDO = base * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
		NORMAL = fn; EMISSION = ALBEDO * ambient; ROUGHNESS = 0.9; SPECULAR = 0.5;
	} else {
		float dist = length(VERTEX);
		float near = smoothstep(90.0, 15.0, dist) * detail;   // fine detail fades out (no shimmer far off)
		float mid = smoothstep(420.0, 60.0, dist);
		vec2 xz = wpos.xz;
		vec3 n = normalize(wnrm);
		float slope = 1.0 - n.y;                        // 0 flat .. 1 vertical
		float macro = fbm(xz * 0.018);                  // 55 m patches
		float meso = fbm(xz * 0.11);                    // 9 m patches
		float fine = fbm2(xz * 1.7);                    // 0.6 m tufts
		float lum = dot(base, vec3(0.3, 0.59, 0.11));
		float sat = max(base.r, max(base.g, base.b)) - min(base.r, min(base.g, base.b));
		// classify the baked colour (soft weights, noise-warped thresholds => organic borders)
		float wgrass = smoothstep(0.0, 0.05, base.g - max(base.r, base.b) + (meso - 0.5) * 0.04);
		float wsnow = smoothstep(0.55, 0.75, lum + (meso - 0.5) * 0.12) * smoothstep(0.18, 0.06, sat);
		float wsand = smoothstep(0.02, 0.08, base.r - base.b) * (1.0 - wgrass) * smoothstep(0.25, 0.4, lum) * (1.0 - wsnow);
		float shore = smoothstep(2.6 + macro * 1.4, 0.6, wpos.y);
		float rockv = smoothstep(0.22 + (meso - 0.5) * 0.12, 0.42, slope);        // slope-based rock
		vec3 col = base * (0.86 + macro * 0.28);       // macro tone variation
		// GRASS: clumps, darker tuft roots, dry/yellow and lush patches, dirt breakups
		vec3 g = col;
		g = mix(g, g * vec3(1.12, 1.02, 0.7), smoothstep(0.55, 0.8, macro) * 0.6);   // sun-dried
		g = mix(g, g * vec3(0.78, 0.95, 0.8), smoothstep(0.45, 0.2, meso) * 0.5);    // lush/damp
		float near2 = smoothstep(38.0, 4.0, dist) * detail;   // land2: crisp blades close to the hero
		float blade = vn(vec2(xz.x * 9.0 + fine * 3.0, xz.y * 2.2)) * vn(vec2(xz.x * 2.4, xz.y * 8.5 + fine * 3.0));
		vec2 q1 = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * xz; vec2 q2 = mat2(vec2(0.34, -0.94), vec2(0.94, 0.34)) * xz;
		float b2 = fbm2(vec2(q1.x * 26.0, q1.y * 5.0) + fbm2(xz * 3.0) * 3.0) * 0.5 + fbm2(vec2(q2.x * 5.5, q2.y * 24.0) + fbm2(xz * 2.6 + 4.0) * 3.0) * 0.5;
		float b3 = smoothstep(0.6, 0.75, fbm2(q2 * 11.0 + 7.0));
		g *= mix(1.0, 0.7 + fine * 0.35 + blade * 0.45, near);
		g *= mix(1.0, 0.55 + b2 * 0.95 + b3 * 0.15, near2);
		g = mix(g, g * vec3(0.55, 0.7, 0.5), smoothstep(0.38, 0.22, b2) * near2 * 0.55);   // dark gaps between blades
		g = mix(g, g * vec3(1.18, 1.12, 0.75), step(0.93, h21(floor(xz * 3.0))) * near * 0.7);   // seed heads / clover
		vec3 dirt = vec3(0.30, 0.24, 0.17) * (0.8 + fine * 0.3);
		float wd = smoothstep(0.68, 0.78, meso + fine * 0.08 * near) * 0.85;
		g = mix(g, dirt, wd);
		// SAND: ripples + wet band at the waterline
		vec3 s = col * (0.95 + (region == 3 ? 0.0 : 0.08) * sin(dot(xz, vec2(0.9, 0.55)) * 3.0 + meso * 9.0 + fbm2(xz * 0.7) * 5.0) * near);
		s = mix(s, s * vec3(0.62, 0.6, 0.6), smoothstep(1.0, 0.2, wpos.y));
		// SNOW: drifts, blue-shaded slopes, faint sparkle
		// land3: off-white snow with blue shading + visible texture (sized for Mobile; Compatibility renders ~10% brighter)
		vec3 sn = vec3(0.5, 0.555, 0.65) * (0.9 + (macro - 0.5) * 0.16);
		float drift = fbm(vec2(xz.x * 0.08 + fbm(xz * 0.03) * 3.0, xz.y * 0.22));        // long wind-drift bands
		float sast = fbm2(mat2(vec2(0.9, 0.44), vec2(-0.44, 0.9)) * xz * vec2(0.9, 3.2));   // sastrugi ridges
		sn *= 0.86 + drift * 0.22;
		sn = mix(sn, sn * vec3(0.72, 0.82, 1.0), smoothstep(0.45, 0.25, drift) * 0.7);   // blue hollows
		sn *= mix(1.0, 0.84 + sast * 0.3, mid);
		sn = mix(sn, sn * vec3(0.66, 0.78, 1.0), smoothstep(0.03, 0.3, slope));            // blue shaded slopes
		sn += vec3(0.18, 0.2, 0.24) * step(0.992, h21(floor(xz * 7.0))) * near;           // sparkle
		// ROCK: region rock tone, warped horizontal strata, cracks, lichen
		vec3 rk = region == 0 ? vec3(0.40, 0.38, 0.35) : region == 1 ? vec3(0.52, 0.49, 0.45) : region == 2 ? vec3(0.36, 0.41, 0.49) : vec3(0.12, 0.11, 0.105);
		if (region == 1) rk = vec3(0.47, 0.39, 0.3);   // land2: warm sandstone, not chalk
		rk = mix(rk, col, region == 1 ? 0.12 : 0.25);
		float strata = sin(wpos.y * 0.5 + fbm(xz * 0.03 + wpos.y * 0.01) * 6.0);
		rk *= (region == 2 ? 1.0 : 1.0) * 0.86 + (region == 2 ? 0.0 : region == 1 ? 0.07 : 0.14) * strata * smoothstep(160.0, 30.0, dist) + (fbm(vec2(xz.x + wpos.y, xz.y - wpos.y) * 0.4) - 0.5) * 0.35;
		float crack = smoothstep(0.03, 0.0, abs(fbm(vec2(xz.x * 0.7 + wpos.y * 0.5, xz.y * 0.7 - wpos.y * 0.3)) - 0.5)) * near;
		rk *= 1.0 - crack * 0.5;
		if (region == 0) rk = mix(rk, vec3(0.42, 0.46, 0.3), smoothstep(0.62, 0.8, meso) * (1.0 - slope) * 0.6);   // lichen
		if (region == 1) rk = mix(rk, vec3(0.8, 0.82, 0.8), smoothstep(0.75, 0.9, fine) * 0.25 * near * (1.0 - slope));   // salt crust on ledges only
		if (region == 1) rk *= 0.85 + 0.3 * smoothstep(0.3, 0.7, vn(vec2(xz.x + xz.y, wpos.y * 4.0) * 0.4));   // sandstone bedding
		if (region == 2) {   // land2: ice cliffs - vertical blue streaks + glassy darker bands, no horizontal stripes
			float st = vn(vec2((xz.x + xz.y) * 0.35, wpos.y * 0.04)) * 0.7 + vn(vec2((xz.x - xz.y) * 1.1, wpos.y * 0.1)) * 0.3;
			rk = mix(vec3(0.6, 0.71, 0.82), vec3(0.72, 0.83, 0.92), smoothstep(0.35, 0.75, st)) * (0.92 + 0.08 * st);   // clean glacier ice faces
			rk = mix(rk, rk * vec3(0.7, 0.8, 0.95), smoothstep(6.0, 0.0, wpos.y) * 0.5);
		}
		if (region == 3) rk += vec3(0.5, 0.12, 0.02) * smoothstep(0.008, 0.0, abs(fbm(xz * 0.05) - 0.5)) * smoothstep(0.62, 0.75, macro) * 0.6 * (1.0 - slope);   // ember seams
		// compose
		vec3 ground = col;
		ground = mix(ground, g, wgrass);
		ground = mix(ground, s, max(wsand, shore * (1.0 - wsnow) * 0.7));
		ground = mix(ground, sn, wsnow * (1.0 - rockv * 0.85));
		ground = mix(ground, rk, rockv * (region == 2 ? 0.85 : 0.9));
		// region accents on flats
		if (region == 1) ground = mix(ground, vec3(0.88, 0.92, 0.92), smoothstep(0.72, 0.9, meso) * (1.0 - rockv) * (1.0 - wgrass) * 0.5);   // salt pans
		if (region == 3) {   // land2: richer volcanic ground
			float flow = ridged_(xz * 0.035);
			ground = mix(ground, vec3(0.1, 0.092, 0.088) * (0.75 + 0.5 * meso), 0.6 * (1.0 - rockv));   // land2: basalt-dark base, beige only in ash dunes
			ground = mix(ground, vec3(0.04, 0.036, 0.04), smoothstep(0.55, 0.8, flow) * 0.75 * (1.0 - rockv));      // cooled lava flows (dark, ropey)
			ground *= 0.9 + 0.2 * vn(vec2(xz.x * 0.6 + flow * 4.0, xz.y * 0.6));
			ground = mix(ground, vec3(0.24, 0.22, 0.2) * (0.9 + 0.2 * fbm2(xz * 0.8)), smoothstep(0.66, 0.86, macro) * 0.4 * (1.0 - rockv));   // pale ash dunes with ripples
			ground = mix(ground, vec3(0.32, 0.25, 0.04), smoothstep(0.8, 0.9, meso) * smoothstep(0.4, 0.2, macro) * 0.6);   // sulphur crust
			ground *= 1.0 - smoothstep(0.62, 0.7, fbm2(xz * 5.0)) * 0.4 * near;   // cinder speckle
			ground = mix(ground, vec3(0.09, 0.07, 0.06), smoothstep(0.5, 0.0, slope) * smoothstep(0.7, 0.9, fine) * 0.3 * near);
		}
		ground *= 0.92 + (fine - 0.5) * 0.25 * near;
		ALBEDO = ground * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
		// bump: blend smooth normal with facet, add noise relief (stronger on rock)
		float e = 0.35;
		float hb = (fbm2(xz * 0.9) * (0.3 + rockv * 1.2) + fine * 0.15) * near;
		float hx = (fbm2((xz + vec2(e, 0.0)) * 0.9) * (0.3 + rockv * 1.2)) * near - hb + fine * 0.15 * near;
		float hz = (fbm2((xz + vec2(0.0, e)) * 0.9) * (0.3 + rockv * 1.2)) * near - hb + fine * 0.15 * near;
		vec3 wn = normalize(n - vec3(hx, 0.0, hz) * 1.6);
		vec3 vn_ = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
		NORMAL = normalize(mix(vn_, fn, 0.18));
		EMISSION = ALBEDO * ambient * (1.0 - wsnow * 0.8);   // land2: snow no longer self-lit into pure white
		if (region == 3) EMISSION += vec3(1.0, 0.3, 0.05) * smoothstep(0.008, 0.0, abs(fbm(xz * 0.05) - 0.5)) * smoothstep(0.62, 0.75, macro) * (1.0 - slope) * 0.35 * mid;   // ember seams glow
		ROUGHNESS = mix(0.92, 0.55, wsnow * (1.0 - rockv)) - (region == 3 ? 0.1 : 0.0);
		SPECULAR = spec;
	}
}
