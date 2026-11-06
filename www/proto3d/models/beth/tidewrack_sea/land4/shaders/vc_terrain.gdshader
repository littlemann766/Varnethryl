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
		float near = smoothstep(80.0, 12.0, dist) * detail;
		float near2 = smoothstep(28.0, 3.0, dist) * detail;
		vec2 xz = wpos.xz;
		vec2 xw = warp(xz, 5.0);
		vec3 n = normalize(wnrm);
		float slope = 1.0 - n.y;                         // 0 flat, 1 vertical
		float macro = fbm(xw * 0.011);
		float meso = fbm(warp(xz, 4.0) * 0.055);
		float fine = fbm2(warp(xz, 1.2) * 1.6);
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
		// rock only once the ground is actually steep, plus any sea cliff
		float rockv = smoothstep(0.20, 0.42, slope);
		float cliff = smoothstep(0.22, 0.48, slope) * smoothstep(8.0, 1.5, wpos.y);
		rockv = max(rockv, cliff * 0.85);
		vec3 dirt = vec3(0.32, 0.24, 0.16) * (0.85 + fine * 0.3);
		vec3 col = base * (0.88 + macro * 0.22);
		// GRASS. Rotated blades so the pattern is not a screen-aligned stripe. Contrast is local, not a blur.
		vec3 g = col;
		g = mix(g, g * vec3(1.08, 0.98, 0.62), smoothstep(0.62, 0.88, macro) * 0.45);
		g = mix(g, g * vec3(0.7, 0.95, 0.75), smoothstep(0.42, 0.15, meso) * 0.4);
		// two crossed directions, no domain-warp on the fine grain (warp turns it into contour lines)
		vec2 q1 = mat2(vec2(0.82, 0.57), vec2(-0.57, 0.82)) * xz;
		vec2 q2 = mat2(vec2(0.31, -0.95), vec2(0.95, 0.31)) * xz;
		float blades = vn(q1 * vec2(11.0, 2.6)) * 0.5 + vn(q2 * vec2(2.4, 10.0)) * 0.5;
		g *= mix(1.0, 0.78 + blades * 0.35, near);
		g *= mix(1.0, 0.66 + blades * 0.5, near2);
		g = mix(g, g * vec3(0.55, 0.72, 0.48), blades * near2 * 0.35);
		g = mix(g, dirt, smoothstep(0.72, 0.9, meso) * 0.45 * (1.0 - near * 0.3));
		// SAND / shore. Keep the baked sand hue; only the wet metre goes darker.
		vec3 s = col * (0.96 + 0.08 * (fbm2(warp(xz, 2.0) * vec2(0.7, 1.4)) - 0.5) * near);
		s = mix(s, s * vec3(0.62, 0.6, 0.55), wet);
		s = mix(s, s * vec3(0.78, 0.72, 0.58), shore * (1.0 - wet) * 0.55);
		// SNOW. Light on the flats, clearly darker in hollows, and it yields to rock on the face.
		vec3 sn = vec3(0.62, 0.66, 0.72);
		float drift = fbm(vec2(xw.x * 0.03, xw.y * 0.07));
		sn *= 0.78 + drift * 0.28;
		sn = mix(sn, vec3(0.34, 0.42, 0.55), smoothstep(0.55, 0.25, drift) * 0.55);
		// ROCK. Region stone. Frost is a dark blue-grey face, not another white.
		vec3 rk = region == 0 ? vec3(0.38, 0.36, 0.32) : region == 1 ? vec3(0.50, 0.40, 0.30) : region == 2 ? vec3(0.30, 0.38, 0.48) : vec3(0.11, 0.10, 0.095);
		rk = mix(rk, col, 0.18);
		float bedding = fbm(vec2(xz.x * 0.04 + wpos.y * 0.08, xz.y * 0.04));
		rk *= 0.82 + bedding * 0.28;
		if (region == 0) rk = mix(rk, vec3(0.36, 0.42, 0.26), smoothstep(0.6, 0.85, meso) * (1.0 - slope) * 0.35);
		if (region == 1) rk = mix(rk, vec3(0.72, 0.70, 0.62), smoothstep(0.8, 0.95, fine) * 0.18 * near * (1.0 - slope));
		if (region == 2) {
			float st = fbm(vec2((xz.x + xz.y) * 0.15, wpos.y * 0.05));
			rk = mix(vec3(0.22, 0.30, 0.42), vec3(0.48, 0.60, 0.72), smoothstep(0.3, 0.75, st));
			rk *= 0.9 + 0.15 * st;
		}
		if (region == 3) rk += vec3(0.45, 0.10, 0.02) * smoothstep(0.02, 0.0, abs(fbm(xz * 0.03) - 0.5)) * 0.35 * (1.0 - slope);
		vec3 ground = col;
		ground = mix(ground, g, wgrass * (1.0 - rockv));
		ground = mix(ground, s, max(wsand, shore * (1.0 - wsnow) * (region == 2 ? 0.25 : 0.8)) * (1.0 - rockv * 0.7));
		ground = mix(ground, sn, wsnow * (1.0 - rockv));
		ground = mix(ground, rk, rockv * (region == 2 ? 0.92 : 0.8));
		if (region == 1) ground = mix(ground, vec3(0.78, 0.82, 0.80), smoothstep(0.7, 0.9, meso) * (1.0 - rockv) * (1.0 - wgrass) * 0.35);
		if (region == 3) {
			ground = mix(ground, vec3(0.09, 0.085, 0.08) * (0.8 + 0.35 * meso), 0.5 * (1.0 - rockv));
			ground = mix(ground, vec3(0.22, 0.20, 0.18), smoothstep(0.65, 0.88, macro) * 0.35 * (1.0 - rockv));
			ground = mix(ground, vec3(0.30, 0.24, 0.05), smoothstep(0.82, 0.94, meso) * 0.4 * (1.0 - rockv));
		}
		// break large flat areas with a fine mottling that fades out, so a slope is not one colour
		ground *= 0.9 + (fine - 0.5) * 0.28 * near + (meso - 0.5) * 0.12;
		ALBEDO = ground * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
		float e = 0.6;
		vec2 bu = xz;
		float hb = fbm2(bu * 0.7);
		float hx = fbm2((bu + vec2(e, 0.0)) * 0.7) - hb;
		float hz = fbm2((bu + vec2(0.0, e)) * 0.7) - hb;
		vec3 wn = normalize(n - vec3(hx, 0.0, hz) * (0.9 * near + rockv * 0.4));
		vec3 vn_ = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
		NORMAL = normalize(mix(vn_, fn, 0.22));
		// snow must not self-light into a white sheet; the face needs shade to read
		EMISSION = ALBEDO * ambient * (1.0 - max(wsnow, rockv) * 0.65);
		if (region == 3) EMISSION += vec3(1.0, 0.28, 0.04) * smoothstep(0.02, 0.0, abs(fbm(xz * 0.03) - 0.5)) * (1.0 - slope) * 0.25 * near;
		ROUGHNESS = mix(0.92, 0.62, wet * 0.4);
		SPECULAR = spec * (region == 2 ? 0.8 : 1.0);
	}
}
