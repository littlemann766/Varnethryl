shader_type spatial;
// Beth: rough dark storm water band laid over the normal sea at the border (UV.y 0 = inner edge, 1 = far out).
// Sits ~1 m above the calm sea (above its wave crests) so the two never interleave into stripes. Choppy steep-normal fragments + whitecaps; fades in over the first 25% so it blends from calm water. 1 draw call, alpha.
render_mode cull_disabled, depth_draw_opaque, blend_mix;
uniform vec4 deep : source_color = vec4(0.04, 0.07, 0.10, 1.0);
uniform vec4 crest : source_color = vec4(0.22, 0.28, 0.32, 1.0);
varying vec3 wpos;
void vertex(){ float vy = 1.0 - UV.y; wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; float t = TIME; VERTEX.y += 0.95 * smoothstep(0.0, 0.1, vy) + (sin(wpos.x * 0.21 + t * 1.7) * cos(wpos.z * 0.17 - t * 1.3)) * 0.45 * smoothstep(0.0, 0.3, vy); }
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
void fragment(){
	float vy = 1.0 - UV.y;  // glTF export flips V: vy 0 = inner edge
	vec2 p = wpos.xz; float t = TIME;
	float n1 = noise(p * 0.12 + vec2(t * 0.5, t * 0.3)); float n2 = noise(p * 0.45 - vec2(t * 0.6, -t * 0.4)); float n3 = noise(p * 1.3 + t);
	NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4((n1 - 0.5) * 1.1 + (n3 - 0.5) * 0.5, 0.0, (n2 - 0.5) * 1.1, 0.0)).xyz);
	float caps = smoothstep(0.72, 0.9, n1 * 0.6 + n2 * 0.5) * smoothstep(0.05, 0.35, vy);
	ALBEDO = mix(mix(deep.rgb, crest.rgb, n2 * 0.6), vec3(0.8, 0.84, 0.86), caps * 0.8); ROUGHNESS = 0.25 + caps * 0.5; SPECULAR = 0.35;
	ALPHA = smoothstep(0.0, 0.1, vy);
}
