shader_type spatial;
// Beth land4 terrain. Baked COLOR picks the biome. The surface is tiled CC0
// albedo, normal and roughness (see textures/TEXTURES.md), two world scales
// blended so the repeat does not line up. Tile sizes are in metres.
// hero_cut kept. Placed props (vertex alpha < 0.5) stay vertex colour.
uniform int region = 0;
uniform float lift = 0.03;
uniform float ambient = 0.35;
uniform float spec = 0.4;
uniform float detail = 1.0;
uniform sampler2D grass_col : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D grass_nrm : repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D grass_rgh : repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D earth_col : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D earth_nrm : repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D earth_rgh : repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D sand_col : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D sand_nrm : repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D sand_rgh : repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D rock_col : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D rock_nrm : repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D rock_rgh : repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D snow_col : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D snow_nrm : repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D snow_rgh : repeat_enable, filter_linear_mipmap_anisotropic;
global uniform vec4 hero_cut;
varying vec3 wpos;
varying vec3 wnrm;
float h21(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vn(vec2 p) { vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p) { float s = 0.0, a = 0.5; for (int i = 0; i < 3; i++) { s += a * vn(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }
// Second tap is the same photograph at a larger scale, mixed everywhere.
// A spatial mask here turned into diamond cells at eye height, so it is not used.
vec3 sample_col(sampler2D tex, vec2 xz, float meters) {
	vec3 a = texture(tex, xz / meters).rgb;
	vec3 b = texture(tex, xz / (meters * 3.1) + vec2(8.2, 3.4)).rgb;
	return mix(a, b, 0.22);
}
vec3 sample_nrm(sampler2D tex, vec2 xz, float meters) {
	return texture(tex, xz / meters).xyz * 2.0 - 1.0;
}
float sample_rgh(sampler2D tex, vec2 xz, float meters) { return texture(tex, xz / meters).r; }
vec3 tri_col(sampler2D tex, vec3 p, vec3 n, float meters) {
	vec3 b = pow(abs(n), vec3(4.0));
	b /= b.x + b.y + b.z;
	return sample_col(tex, p.zy, meters) * b.x + sample_col(tex, p.xz, meters) * b.y + sample_col(tex, p.xy, meters) * b.z;
}
vec3 tri_nrm(sampler2D tex, vec3 p, vec3 nrm, float meters) {
	vec3 b = pow(abs(nrm), vec3(4.0));
	b /= b.x + b.y + b.z;
	vec3 tx = sample_nrm(tex, p.zy, meters);
	vec3 ty = sample_nrm(tex, p.xz, meters);
	vec3 tz = sample_nrm(tex, p.xy, meters);
	vec3 wx = vec3(tx.z * sign(nrm.x + 1e-4), tx.y, tx.x);
	vec3 wy = vec3(ty.x, ty.z * sign(nrm.y + 1e-4), ty.y);
	vec3 wz = vec3(tz.x, tz.y, tz.z * sign(nrm.z + 1e-4));
	return normalize(wx * b.x + wy * b.y + wz * b.z);
}
vec3 grade_grass(vec3 c) {
	float l = dot(c, vec3(0.30, 0.59, 0.11));
	c = mix(c, vec3(l * 0.62, l * 0.70, l * 0.40), 0.22);
	return c * vec3(0.72, 0.78, 0.58);
}
vec3 grade_earth(vec3 c) { return c * vec3(0.86, 0.78, 0.64); }
vec3 grade_sand(vec3 c) { return c * vec3(0.94, 0.86, 0.70); }
vec3 grade_snow(vec3 c) { return c * vec3(0.52, 0.56, 0.62); }
vec3 grade_rock(vec3 c) {
	vec3 tint = vec3(0.78, 0.74, 0.68);
	if (region == 1) tint = vec3(0.92, 0.78, 0.60);
	if (region == 2) tint = vec3(0.62, 0.70, 0.82);
	if (region == 3) tint = vec3(0.28, 0.32, 0.38);
	return c * tint;
}
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz); }
void fragment() {
	float d = fract(sin(dot(floor(FRAGCOORD.xy), vec2(12.9898, 78.233))) * 43758.5453);
	if (length(VERTEX) < 0.2) discard;
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
		vec2 xz = wpos.xz;
		float px = max(length(dFdx(xz)), length(dFdy(xz)));
		vec3 n = normalize(wnrm);
		float slope = 1.0 - n.y;
		float lum = dot(base, vec3(0.3, 0.59, 0.11));
		float sat = max(base.r, max(base.g, base.b)) - min(base.r, min(base.g, base.b));
		float wob = fbm(xz * 0.016) - 0.5;
		float wgrass = smoothstep(0.0, 0.08, base.g - max(base.r, base.b) + wob * 0.03);
		float wsnow = smoothstep(0.62, 0.82, lum + wob * 0.04) * smoothstep(0.16, 0.04, sat);
		float wsand = smoothstep(0.01, 0.09, base.r - base.b + wob * 0.03) * (1.0 - wgrass) * (1.0 - wsnow);
		float shore_h = 0.9 + fbm(xz * 0.02) * 1.1;
		float shore = smoothstep(shore_h + 1.1, shore_h - 0.15, wpos.y);
		float wet = smoothstep(shore_h + 0.05, shore_h - 0.8, wpos.y);
		float rockv = smoothstep(0.18 + wob * 0.05, 0.40, slope);
		// 2 m grass and soil, 2.4 m sand, 3.2 m snow, 1.8 m rock. Mipmaps cover distance.
		vec3 gcol = grade_grass(sample_col(grass_col, xz, 2.0));
		vec3 ecol = grade_earth(sample_col(earth_col, xz, 2.0));
		vec3 scol = grade_sand(sample_col(sand_col, xz, 2.4));
		vec3 ncol = grade_snow(sample_col(snow_col, xz, 3.2));
		vec3 rcol = grade_rock(tri_col(rock_col, wpos, n, 1.8));
		float wear = clamp(0.12 + (1.0 - sat) * 0.25 + smoothstep(0.45, 0.78, fbm(xz * 0.09)) * 0.45, 0.08, 0.7);
		vec3 meadow = mix(gcol, ecol, wear);
		if (region == 1) meadow = mix(meadow, scol * vec3(1.08, 1.06, 1.0), (1.0 - wgrass) * 0.62);
		if (region == 3) {
			meadow = mix(rcol, ecol * vec3(0.72, 0.64, 0.52), 0.42);
			meadow = mix(meadow, vec3(0.46, 0.38, 0.16), smoothstep(0.74, 0.92, vn(xz * 0.07)) * 0.32);
		}
		float sandw = max(wsand, shore * (1.0 - wsnow) * (region == 2 ? 0.22 : 0.8));
		vec3 ground = meadow;
		ground = mix(ground, scol, sandw * (1.0 - rockv));
		ground = mix(ground, ncol, wsnow * (1.0 - rockv));
		ground = mix(ground, rcol, rockv);
		ground = mix(ground, ground * vec3(0.52, 0.56, 0.58), wet * clamp(sandw + shore, 0.0, 1.0));
		ground *= 0.92 + 0.14 * vn(xz * 0.028);
		// a little of the baked colour so islands in one region are not identical, without covering the photo
		ground *= mix(vec3(1.0), clamp(base / max(lum, 0.18), vec3(0.45), vec3(1.35)), 0.18);
		ALBEDO = ground * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
		vec3 tg = sample_nrm(grass_nrm, xz, 2.0);
		vec3 te = sample_nrm(earth_nrm, xz, 2.0);
		vec3 tsand = sample_nrm(sand_nrm, xz, 2.4);
		vec3 tsn = sample_nrm(snow_nrm, xz, 3.2);
		vec3 ts = normalize(mix(mix(mix(tg, te, wear), tsand, sandw), tsn, wsnow));
		float ns = detail * mix(0.9, 0.28, smoothstep(0.05, 0.4, px));
		ts.xy *= ns;
		vec3 N = n;
		vec3 T = normalize(vec3(1.0, 0.0, 0.0) - N * N.x);
		vec3 B = normalize(vec3(0.0, 0.0, 1.0) - N * N.z);
		vec3 wG = normalize(T * ts.x + B * ts.y + N * ts.z);
		vec3 wR = tri_nrm(rock_nrm, wpos, n, 1.8);
		vec3 wN = normalize(mix(wG, wR, rockv));
		NORMAL = normalize(mix(normalize((VIEW_MATRIX * vec4(wN, 0.0)).xyz), fn, 0.22));
		EMISSION = ALBEDO * min(ambient, 0.32) * 0.4;
		if (region == 3) EMISSION += vec3(0.55, 0.16, 0.03) * smoothstep(0.03, 0.0, abs(fbm(xz * 0.03) - 0.5)) * (1.0 - slope) * 0.18;
		float rg = mix(mix(mix(sample_rgh(grass_rgh, xz, 2.0), sample_rgh(earth_rgh, xz, 2.0), wear), sample_rgh(sand_rgh, xz, 2.4), sandw), sample_rgh(snow_rgh, xz, 3.2), wsnow);
		rg = mix(rg, sample_rgh(rock_rgh, wpos.xz, 1.8), rockv);
		rg = mix(rg, 0.32, wet * 0.65);
		rg = mix(rg, max(rg, 0.82), wsnow);
		ROUGHNESS = clamp(rg, 0.28, 1.0);
		SPECULAR = spec * mix(0.45, 0.12, wsnow);
	}
}
