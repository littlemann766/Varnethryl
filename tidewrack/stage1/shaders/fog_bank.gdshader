shader_type spatial;
// Beth: soft fog bank ribbon just inside the storm wall (arch_fog_bank.glb). Unshaded, alpha, fades near the camera.
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;
uniform vec4 fog_col : source_color = vec4(0.78, 0.84, 0.88, 1.0);
uniform float opacity = 0.55;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
void fragment(){
	float n = noise(vec2(UV.x * 4.0 + TIME * 0.03, UV.y * 2.0)); float near = smoothstep(20.0, 120.0, length(VERTEX));
	ALBEDO = fog_col.rgb; ALPHA = opacity * n * (1.0 - UV.y) * smoothstep(0.0, 0.15, UV.y) * near;
}
