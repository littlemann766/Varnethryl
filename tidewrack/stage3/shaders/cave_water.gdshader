shader_type spatial;
// Beth: dark still cave water: slow ripples, picks up the crystal/lantern glow as a tint (glow_tint), 1 draw call.
uniform vec4 deep : source_color = vec4(0.03, 0.09, 0.11, 1.0);
uniform vec4 glow_tint : source_color = vec4(0.25, 0.75, 0.85, 1.0);
uniform float glow_amt = 0.6;
varying vec3 wpos;
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
void fragment(){
	vec2 p = wpos.xz; float t = TIME; float n1 = noise(p * 0.4 + t * 0.15); float n2 = noise(p * 1.1 - t * 0.2);
	NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4((n1 - 0.5) * 0.25, 0.0, (n2 - 0.5) * 0.25, 0.0)).xyz);
	ALBEDO = deep.rgb + glow_tint.rgb * glow_amt * (0.15 + n1 * 0.25); ROUGHNESS = 0.04; SPECULAR = 0.9; METALLIC = 0.2;
}
