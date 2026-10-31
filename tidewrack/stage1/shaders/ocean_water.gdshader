shader_type spatial;
// Beth: Tidewrack Sea water, HIGH tier (Mobile renderer). ONE draw call: camera-following grid (~200x200 quads),
// 3 Gerstner waves in the vertex, 2 scrolling detail normals, crest foam, shore foam + shallow tint from the baked
// shore-distance texture (arch_shore_dist.png, R = metres to land). Ships bob from the same wave sum on the CPU (see README_LUCKY).
render_mode cull_back, depth_draw_opaque;
uniform float wave_amp = 1.0;
uniform vec2 wind_dir = vec2(0.8, 0.6);          // per region (Archipelago: SW trade)
uniform vec4 deep : source_color = vec4(0.03, 0.16, 0.26, 1.0);
uniform vec4 shallow : source_color = vec4(0.12, 0.50, 0.50, 1.0);
uniform sampler2D shore_dist : filter_linear, repeat_disable;  // region A bake
uniform vec4 shore_rect = vec4(-1200.0, -1300.0, 2700.0, 2600.0); // x0, z0, width, depth (m)
uniform float foam_width = 14.0;
uniform float ice = 0.0;                          // Frost strait reuses this shader
varying float crest; varying vec3 wpos;
vec3 gerstner(vec2 p, vec2 dir, float L, float A, float t, inout float c){
	float k = 6.2832 / L; float w = sqrt(9.8 * k); float ph = k * dot(dir, p) - w * t; c += max(sin(ph), 0.0) * A;
	return vec3(dir.x * A * cos(ph), A * sin(ph), dir.y * A * cos(ph));
}
float sdist(vec2 p){ vec2 uv = (p - shore_rect.xy) / shore_rect.zw; if (any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0)))) return 255.0; return texture(shore_dist, uv).r * 255.0; }
void vertex(){
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; float c = 0.0; float t = TIME; vec2 d0 = normalize(wind_dir);
	float calm = clamp(sdist(wp.xz) / 60.0, 0.25, 1.0);   // waves calm down in the shallows
	vec3 o = gerstner(wp.xz, d0, 38.0, 0.55, t, c) + gerstner(wp.xz, normalize(d0 + vec2(-0.9, 0.5)), 17.0, 0.25, t, c) + gerstner(wp.xz, normalize(vec2(d0.y, -d0.x) + d0), 7.0, 0.08, t, c);
	VERTEX += o * wave_amp * calm; crest = c * wave_amp * calm; wpos = wp;
}
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
void fragment(){
	vec2 p = wpos.xz; float t = TIME;
	float n1 = noise(p * 0.35 + vec2(t * 0.3, t * 0.2)); float n2 = noise(p * 0.9 - vec2(t * 0.25, -t * 0.4));
	NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4((n1 - 0.5) * 0.35 + (n2 - 0.5) * 0.2, 0.0, (n2 - 0.5) * 0.35, 0.0)).xyz);
	float sd = sdist(p); float sh = 1.0 - smoothstep(0.0, 70.0, sd);
	vec3 col = mix(deep.rgb, shallow.rgb, clamp(crest * 0.4 + n1 * 0.15 + sh * 0.9, 0.0, 1.0));
	float foam = smoothstep(0.75, 0.95, crest + n2 * 0.2);
	float band = foam_width * (0.6 + 0.8 * noise(p * 0.05));                     // broken surf line
	float sfoam = (1.0 - smoothstep(0.0, band, sd)) * smoothstep(0.35, 0.7, noise(p * 0.25 + vec2(t * 0.15, 0.0)) + 0.35 * sin(sd * 0.8 - t * 2.0));
	foam = max(foam, sfoam);
	col = mix(col, vec3(0.92, 0.96, 0.97), clamp(foam, 0.0, 1.0) * 0.8);
	col = mix(col, vec3(0.85, 0.92, 0.96), ice * smoothstep(0.55, 0.75, noise(p * 0.08)));
	ALBEDO = col; ROUGHNESS = 0.06 + foam * 0.6; SPECULAR = 0.6;
}
