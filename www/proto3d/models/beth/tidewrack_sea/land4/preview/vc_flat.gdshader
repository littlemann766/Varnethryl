shader_type spatial;
// Flat vertex-colour material for props and scatter. Same uniforms the game passes to vc_flat.
uniform float lift = 0.03;
uniform float ambient = 0.35;
uniform float spec = 0.4;
global uniform vec4 hero_cut;
varying vec3 wpos;
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	float d = fract(sin(dot(floor(FRAGCOORD.xy), vec2(12.9898, 78.233))) * 43758.5453);
	if (d > smoothstep(0.8, 3.0, length(VERTEX))) discard;
	vec3 base = COLOR.rgb;
	ALBEDO = base * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
	EMISSION = ALBEDO * ambient;
	ROUGHNESS = 0.9;
	SPECULAR = spec * 0.5;
}
