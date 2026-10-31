shader_type spatial;
// Beth: soft rising steam from vents / chimneys / hot spring (ash_steam.glb, 3 crossed cards per plume).
// COLOR.r = height fraction (linear-stored -> decoded), COLOR.g = phase, COLOR.b = 0/1 card side (soft edges). Mobile-cheap, no textures.
render_mode blend_mix, depth_draw_never, cull_disabled, shadows_disabled, unshaded;
uniform vec4 steam : source_color = vec4(0.86, 0.85, 0.83, 1.0);
uniform vec2 wind = vec2(0.0, -1.0);   // hot S wind pushes plumes north
uniform float opacity = 0.42;
varying vec3 wpos; varying float t; varying float ph; varying float side;
void vertex(){
	t = pow(COLOR.r, 1.0 / 2.2); ph = COLOR.g * 6.28; side = COLOR.b;
	VERTEX.xz += wind * t * t * 6.0 + vec2(sin(TIME * 0.8 + ph + t * 4.0), cos(TIME * 0.6 + ph)) * t * 1.5;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
void fragment(){
	float edge = 1.0 - abs(side * 2.0 - 1.0); edge = smoothstep(0.0, 0.8, edge);
	float n = noise(vec2(side * 3.0 + ph, wpos.y * 0.18 - TIME * 0.9)) * 0.6 + noise(vec2(side * 7.0 - ph, wpos.y * 0.5 - TIME * 1.7)) * 0.4;
	float a = edge * smoothstep(0.0, 0.12, t) * (1.0 - smoothstep(0.55, 1.0, t)) * (0.45 + 0.75 * n);
	ALBEDO = steam.rgb * (0.85 + 0.15 * n); ALPHA = clamp(a * opacity, 0.0, 1.0);
}
