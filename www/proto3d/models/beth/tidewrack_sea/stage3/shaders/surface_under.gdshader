shader_type spatial;
// Beth: the sea surface seen from below (Snell window feel): bright rippling sheet, darker at grazing angles.
render_mode unshaded, cull_disabled;
uniform vec4 bright : source_color = vec4(0.62, 0.86, 0.85, 1.0);
uniform vec4 dark : source_color = vec4(0.07, 0.28, 0.32, 1.0);
varying vec3 wpos;
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
void fragment(){
	vec3 v = normalize(CAMERA_POSITION_WORLD - wpos); float up = clamp(-v.y, 0.0, 1.0);
	float n = noise(wpos.xz * 0.25 + TIME * 0.3) * 0.6 + noise(wpos.xz * 0.9 - TIME * 0.4) * 0.4;
	ALBEDO = mix(dark.rgb, bright.rgb, smoothstep(0.55, 0.95, up) * (0.7 + 0.5 * n));
}
