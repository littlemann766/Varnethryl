shader_type spatial;
render_mode cull_disabled;
// test 13 (boss: flat tiled yellow floor): procedural molten rock in world space -> no tiling.
// Dark cooled crust plates, bright cracks between them (cellular), slow two-layer flow, pulsing glow.
uniform float glow = 1.0;          // TitanQuest: 1.0 / 1.4 / 1.9 per stage, 0.35 when calmed
uniform float calm = 0.0;        // 1 after the Titan falls: cracks close, crust cools
uniform vec2 flow = vec2(0.035, 0.02);
uniform float scale = 0.11;
varying vec3 wp;
void vertex() { wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
vec2 h2(vec2 p) { p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3))); return fract(sin(p) * 43758.5453); }
float vn(vec2 p) { vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
	float a = h2(i).x, b = h2(i + vec2(1, 0)).x, c = h2(i + vec2(0, 1)).x, d = h2(i + vec2(1, 1)).x;
	return mix(mix(a, b, u.x), mix(c, d, u.x), u.y); }
float fbm(vec2 p) { float s = 0.0, a = 0.5; for (int i = 0; i < 4; i++) { s += a * vn(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }
// distance to the nearest cell border (cracks)
float cells(vec2 p) { vec2 i = floor(p), f = fract(p); float d1 = 8.0, d2 = 8.0;
	for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) { vec2 g = vec2(float(x), float(y));
		vec2 o = h2(i + g); vec2 r = g + o - f; float d = dot(r, r);
		if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) d2 = d; }
	return sqrt(d2) - sqrt(d1); }
void fragment() {
	vec2 p = wp.xz * scale;
	float t = TIME;
	vec2 warp = vec2(fbm(p * 0.7 + t * flow * 3.0), fbm(p * 0.7 - t * flow * 2.0 + 5.2)) - 0.5;
	vec2 q = p + warp * 0.9 + t * flow;
	float edge = cells(q * 1.6);
	float crack = 1.0 - smoothstep(0.0, 0.12 + 0.05 * fbm(q * 3.0), edge);
	float fine = 1.0 - smoothstep(0.0, 0.06, cells(q * 4.3 + 3.1));
	float heat0 = clamp(crack + fine * 0.45 + (fbm(q * 2.0 - t * flow * 4.0) - 0.55) * 0.9, 0.0, 1.0);
	float heat = heat0 * mix(1.0, 0.35, calm);
	float pulse = 0.85 + 0.15 * sin(t * 1.3 + fbm(p * 1.3) * 6.0);
	vec3 crust = mix(vec3(0.045, 0.035, 0.03), vec3(0.13, 0.09, 0.07), fbm(q * 5.0));
	vec3 hot = mix(vec3(0.9, 0.18, 0.02), vec3(1.0, 0.75, 0.25), heat * heat);
	ALBEDO = mix(crust, hot * 0.6, heat);
	ROUGHNESS = mix(0.95, 0.4, heat);
	EMISSION = hot * heat * (2.6 * glow * pulse);
}
