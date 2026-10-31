shader_type spatial;
// Beth: locked-region storm wall (ribbon arch_storm_wall.glb; UV.x along the wall in wall-heights, UV.y 0 bottom..1 top).
// Unshaded + alpha, 1 draw call. Lightning flashes via `flash` uniform from script. Low tier: same shader, set detail = 0.
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;
uniform vec4 cloud : source_color = vec4(0.16, 0.18, 0.24, 1.0);
uniform vec4 rain : source_color = vec4(0.55, 0.60, 0.68, 1.0);
uniform float flash = 0.0; uniform float detail = 1.0; uniform float opacity = 0.92;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
void fragment(){
	vec2 uv = UV; float t = TIME;
	float c = noise(vec2(uv.x * 3.0 + t * 0.05, uv.y * 2.0 - t * 0.1)) * 0.6 + noise(vec2(uv.x * 9.0 - t * 0.1, uv.y * 6.0)) * 0.4 * detail;
	float streak = smoothstep(0.6, 1.0, noise(vec2(uv.x * 80.0, uv.y * 3.0 + t * 4.0))) * detail;
	vec3 col = mix(cloud.rgb, rain.rgb, streak * 0.6) * (0.7 + 0.6 * c) + vec3(0.7, 0.8, 1.0) * flash * c;
	ALBEDO = col; ALPHA = opacity * smoothstep(0.0, 0.08, uv.y) * (0.75 + 0.25 * c) * (1.0 - smoothstep(0.85, 1.0, uv.y) * 0.6);
}
