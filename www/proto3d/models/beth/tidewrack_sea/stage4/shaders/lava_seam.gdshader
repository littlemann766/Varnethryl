shader_type spatial;
// Beth: glowing lava seams/rivulets/crater lake (ash_lava_seams.glb). COLOR.r = intensity (stored linear -> decoded), COLOR.g = phase.
// Slow crawl of hot/cool patches; no lights needed (emission + glow). Cheap: 1 noise tap.
uniform vec4 hot : source_color = vec4(1.0, 0.62, 0.18, 1.0);
uniform vec4 cool : source_color = vec4(0.55, 0.06, 0.02, 1.0);
uniform float energy = 6.0;
varying vec3 wpos;
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
void fragment(){
	float inten = pow(COLOR.r, 1.0 / 2.2); float ph = COLOR.g * 6.28;
	float n = noise(wpos.xz * 0.35 + vec2(TIME * 0.12, -TIME * 0.08) + ph);
	float h = clamp(inten * (0.55 + 0.6 * n) + 0.08 * sin(TIME * 1.5 + ph), 0.0, 1.0);
	vec3 c = mix(cool.rgb, hot.rgb, h * h);
	ALBEDO = c * 0.2; EMISSION = c * energy * (0.35 + h); ROUGHNESS = 0.6;
}
