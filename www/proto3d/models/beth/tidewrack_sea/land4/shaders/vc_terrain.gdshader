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
// The blend used to sit at 0.42–0.58, so both copies of the tile stayed visible
// and a cliff showed a stable grid. This weight drifts over about 25 m. The
// second tap is a larger scale, kept under a third, so the metre-scale photo
// stays and the repeat does not line up. No third tap.
float tile_w(vec2 world) { return smoothstep(0.22, 0.78, fbm(world * 0.04 + 1.7)); }
vec2 bend(vec2 world) {
	return vec2(fbm(world * 0.046 + 1.3), fbm(world * 0.046 + 6.8)) - 0.5;
}
vec3 sample_col(sampler2D tex, vec2 world, float meters, float w, float warp_amp, float lo, float hi) {
	vec2 uv = world / meters + bend(world) * warp_amp;
	vec2 uvb = mat2(vec2(0.82, -0.57), vec2(0.57, 0.82)) * (uv * 0.37) + vec2(4.7, 2.2);
	vec3 a = texture(tex, uv).rgb;
	vec3 b = texture(tex, uvb).rgb;
	return mix(a, b, mix(lo, hi, w));
}
vec3 sample_nrm(sampler2D tex, vec2 world, float meters, float warp_amp) {
	vec2 uv = world / meters + bend(world) * warp_amp;
	return texture(tex, uv).xyz * 2.0 - 1.0;
}
// The CC0 roughness photos are smooth (grass median ~0.25). Used raw they read as
// polished carpet, and an sRGB decode would make that worse. Keep the photo's
// variation, but sit it in a dry range. Wet sand is lowered later, on purpose.
float rough_in(sampler2D tex, vec2 world, float meters, float lo, float hi) {
	vec2 uv = world / meters + bend(world) * 0.46;
	return mix(lo, hi, clamp(texture(tex, uv).r, 0.0, 1.0));
}
vec3 tri_col(sampler2D tex, vec3 p, vec3 n, float meters) {
	vec3 b = pow(abs(n), vec3(4.0));
	b /= b.x + b.y + b.z;
	// Each plane carries its own weight, including height, so a vertical face
	// does not repeat in a straight column.
	// Rock mixes widely between a bent copy and a rotated larger copy, so a
	// cliff face does not keep one straight tile column.
	return sample_col(tex, p.zy, meters, tile_w(p.zy), 1.35, 0.18, 0.74) * b.x
		+ sample_col(tex, p.xz, meters, tile_w(p.xz), 1.35, 0.18, 0.74) * b.y
		+ sample_col(tex, p.xy, meters, tile_w(p.xy), 1.35, 0.18, 0.74) * b.z;
}
vec3 tri_nrm(sampler2D tex, vec3 p, vec3 nrm, float meters) {
	vec3 b = pow(abs(nrm), vec3(4.0));
	b /= b.x + b.y + b.z;
	vec3 tx = sample_nrm(tex, p.zy, meters, 1.35);
	vec3 ty = sample_nrm(tex, p.xz, meters, 1.35);
	vec3 tz = sample_nrm(tex, p.xy, meters, 1.35);
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
		float wgrass = smoothstep(-0.03, 0.16, base.g - max(base.r, base.b) + wob * 0.07);
		float wsnow = smoothstep(0.62, 0.82, lum + wob * 0.04) * smoothstep(0.16, 0.04, sat);
		float wsand = smoothstep(-0.03, 0.18, base.r - base.b + wob * 0.08) * (1.0 - wgrass) * (1.0 - wsnow);
		float shore_h = 0.3 + fbm(xz * 0.012) * 2.4;
		float shore = smoothstep(shore_h + 2.6, shore_h - 0.55, wpos.y);
		float wet = smoothstep(shore_h + 0.2, shore_h - 1.1, wpos.y);
		float rockv = smoothstep(0.08 + wob * 0.12, 0.58, slope);
		float tw = tile_w(xz);
		// 2 m grass and soil, 2.4 m sand, 3.2 m snow, 1.8 m rock. Mipmaps cover distance.
		vec3 gcol = grade_grass(sample_col(grass_col, xz, 2.0, tw, 0.42, 0.12, 0.34));
		vec3 ecol = grade_earth(sample_col(earth_col, xz, 2.0, tw, 0.42, 0.12, 0.34));
		vec3 scol = grade_sand(sample_col(sand_col, xz, 2.4, tw, 0.42, 0.12, 0.34));
		vec3 ncol = grade_snow(sample_col(snow_col, xz, 3.2, tw, 0.42, 0.12, 0.34));
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
		ground *= 0.90 + 0.14 * fbm(xz * 0.008);
		// Frost vertex colour is pale blue-grey but not bright enough to pass the snow
		// test, so the grass and earth mix was painting mustard bands across the snow.
		// Flats are cold snow. Steep faces, including a triangle the smoothed normal
		// still calls gentle, are darker blue-grey rock. No grass, no sand.
		float fr = 0.0;
		if (region == 2) {
			vec3 fw = cross(dFdx(wpos), dFdy(wpos));
			float fl = length(fw);
			float faceSlope = fl > 1e-4 ? (1.0 - abs(fw.y / fl)) : slope;
			fr = smoothstep(0.06, 0.55, max(slope, faceSlope));
			vec3 snowF = ncol * vec3(1.18, 1.26, 1.40);
			vec3 rockF = rcol * vec3(0.30, 0.34, 0.44);
			ground = mix(snowF, rockF, fr);
			ground = mix(ground, rockF * vec3(0.70, 0.76, 0.86), shore * (1.0 - fr) * 0.7);
			ground *= 0.96 + 0.05 * fbm(xz * 0.02);
		} else {
			// a little of the baked colour so islands in one region are not identical, without covering the photo
			ground *= mix(vec3(1.0), clamp(base / max(lum, 0.18), vec3(0.45), vec3(1.35)), 0.18);
		}
		ALBEDO = ground * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
		vec3 tg = sample_nrm(grass_nrm, xz, 2.0, 0.42);
		vec3 te = sample_nrm(earth_nrm, xz, 2.0, 0.42);
		vec3 tsand = sample_nrm(sand_nrm, xz, 2.4, 0.42);
		vec3 tsn = sample_nrm(snow_nrm, xz, 3.2, 0.42);
		vec3 ts = normalize(mix(mix(mix(tg, te, wear), tsand, sandw), tsn, wsnow));
		if (region == 2) ts = tsn;
		float ns = detail * mix(0.42, 0.12, smoothstep(0.05, 0.45, px));
		ts.xy *= ns * (region == 2 ? 1.7 : 1.0);
		vec3 N = n;
		vec3 T = normalize(vec3(1.0, 0.0, 0.0) - N * N.x);
		vec3 B = normalize(vec3(0.0, 0.0, 1.0) - N * N.z);
		vec3 wG = normalize(T * ts.x + B * ts.y + N * ts.z);
		vec3 wR = tri_nrm(rock_nrm, wpos, n, 1.8);
		vec3 wN = normalize(mix(wG, wR, region == 2 ? fr : rockv));
		vec3 vN = normalize((VIEW_MATRIX * vec4(wN, 0.0)).xyz);
		if (region == 2) {
			// Averaged vertex normal, plus a little relief. The flat face normal is
			// what made each large triangle shade as one card. The triangle edges
			// in the silhouette are unchanged.
			vec3 vSmooth = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
			NORMAL = normalize(mix(vSmooth, vN, 0.72));
		} else {
			// The flat face normal is what made a large triangle shade as one card.
			NORMAL = normalize(mix(vN, fn, 0.05));
		}
		EMISSION = ALBEDO * min(ambient, 0.32) * 0.4;
		if (region == 3) EMISSION += vec3(0.55, 0.16, 0.03) * smoothstep(0.03, 0.0, abs(fbm(xz * 0.03) - 0.5)) * (1.0 - slope) * 0.18;
		float rg = mix(rough_in(grass_rgh, xz, 2.0, 0.90, 0.98), rough_in(earth_rgh, xz, 2.0, 0.88, 0.96), wear);
		rg = mix(rg, rough_in(sand_rgh, xz, 2.4, 0.84, 0.94), sandw);
		rg = mix(rg, rough_in(snow_rgh, xz, 3.2, 0.93, 0.99), wsnow);
		rg = mix(rg, rough_in(rock_rgh, wpos.xz, 1.8, 0.80, 0.92), rockv);
		rg = mix(rg, 0.58, wet * clamp(sandw + shore * 0.5, 0.0, 1.0));
		if (region == 2) rg = mix(mix(0.96, 0.86, fr), 0.70, shore * (1.0 - fr));
		ROUGHNESS = clamp(rg, 0.5, 1.0);
		SPECULAR = min(spec, 0.16) * mix(0.35, 1.0, wet * sandw);
	}
}
