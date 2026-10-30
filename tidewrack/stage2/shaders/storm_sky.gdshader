shader_type spatial;
// Beth: stormy sky backdrop beyond the border (tall ribbon outside the region; UV.x along, UV.y 0 sea .. 1 top).
// Dark low cloud mass, slow roll, rain curtains hanging from it, occasional lightning via `flash`. Unshaded, alpha, 1 call.
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix, fog_disabled;
uniform vec4 cloud : source_color = vec4(0.18, 0.20, 0.25, 1.0);
uniform vec4 cloud_hi : source_color = vec4(0.42, 0.45, 0.52, 1.0);
uniform float flash = 0.0; uniform float rain = 1.0;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 4; i++){ s += a * noise(p); p *= 2.1; a *= 0.5; } return s; }
void fragment(){
	vec2 uv = vec2(UV.x, 1.0 - UV.y); float t = TIME;  // glTF export flips V
	float c = fbm(vec2(uv.x * 2.0 + t * 0.006, uv.y * 3.0 - t * 0.004));
	float mass = smoothstep(0.0, 0.12, uv.y) * smoothstep(0.25, 0.65, c + 0.25 - uv.y * 0.35);   // low heavy cloud, thinning and breaking up with height
	float curtain = smoothstep(0.35, 0.85, fbm(vec2(uv.x * 3.0 + t * 0.004, uv.y * 1.5))) * smoothstep(0.0, 0.04, uv.y) * (1.0 - smoothstep(0.08, 0.3, uv.y));  // soft rain curtains, low only
	float streak = smoothstep(0.6, 1.0, noise(vec2(uv.x * 160.0, uv.y * 30.0 + t * 6.0))) * rain * curtain;
	vec3 col = mix(cloud.rgb, cloud_hi.rgb, c * 0.8) + vec3(0.75, 0.8, 1.0) * flash * c;
	float a = max(mass * 0.9, curtain * (0.35 + 0.35 * streak)) * (1.0 - smoothstep(0.3, 0.75, uv.y + (c - 0.5) * 0.3)) * smoothstep(0.0, 0.05, uv.y);  // no top edge
	ALBEDO = mix(col, vec3(0.5, 0.54, 0.6), curtain * streak * 0.4); ALPHA = a;
}
