shader_type spatial;
// Beth: vertex-colour seabed/ruins with moving caustics (Mobile: 2 noise taps). Use for sw_seabed, sw_buildings, sw_landmarks, sw_rubble.
uniform float caustic = 0.55; uniform float scale = 0.18;
varying vec3 wpos; varying vec3 wn;
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; wn = (MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz; }
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
void fragment(){
	vec2 p = wpos.xz * scale; float t = TIME;
	float c = abs(noise(p + vec2(t * 0.35, t * 0.2)) - noise(p * 1.3 - vec2(t * 0.25, -t * 0.3)));
	c = pow(1.0 - clamp(c * 2.2, 0.0, 1.0), 6.0) * clamp(normalize(wn).y, 0.0, 1.0) * clamp(1.0 + wpos.y / 45.0, 0.2, 1.0);
	ALBEDO = COLOR.rgb; ROUGHNESS = 0.85; EMISSION = vec3(0.55, 0.85, 0.8) * c * caustic;
}
