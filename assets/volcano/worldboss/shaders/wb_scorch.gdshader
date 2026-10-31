// worldboss2 (Lucky): scorched ash ground around the Titan; radial falloff, noisy char + faint ember specks. Mobile-safe.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, shadows_disabled;
float h(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
	return mix(mix(h(i), h(i+vec2(1,0)), f.x), mix(h(i+vec2(0,1)), h(i+vec2(1,1)), f.x), f.y); }
void fragment() {
	vec2 c = UV - 0.5; float r = length(c) * 2.0;
	float nz = n(UV * 18.0) * 0.6 + n(UV * 55.0) * 0.4;
	float a = smoothstep(1.0, 0.45, r + (nz - 0.5) * 0.35);
	ALBEDO = mix(vec3(0.05, 0.045, 0.04), vec3(0.17, 0.15, 0.13), nz);
	ROUGHNESS = 1.0;
	float sp = step(0.985, n(UV * 140.0)) * a;
	EMISSION = vec3(1.0, 0.35, 0.05) * sp * (0.6 + 0.4 * sin(TIME * 3.0 + nz * 20.0)) * 2.0;
	ALPHA = a * 0.92;
}
