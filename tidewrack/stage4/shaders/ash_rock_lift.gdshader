shader_type spatial;
// test 37 (t36 shots: Vent Harbour / Hot Spring ground read as pure black on screen): basalt vertex colour lifted to a dark
// grey floor so it keeps its shape under the ash haze; same 0.9 roughness / 0.15 specular as the stage 4 README material.
uniform float lift = 0.1;
void fragment() {
	ALBEDO = COLOR.rgb * 0.8 + vec3(lift, lift * 0.95, lift * 0.9);
	float cd = length(VERTEX);   // near-camera dither fade (0.8 -> 3 m)
	float d = fract(sin(dot(floor(FRAGCOORD.xy), vec2(12.9898, 78.233))) * 43758.5453);
	if (d > smoothstep(0.8, 3.0, cd)) discard;
	vec3 fn = normalize(cross(dFdx(VERTEX), dFdy(VERTEX)));   // flat face normal, always facing the camera
	if (dot(fn, -VERTEX) < 0.0) fn = -fn;
	NORMAL = fn;
	EMISSION = ALBEDO * 0.18;   // ash-haze ambient floor: never pure black
	ROUGHNESS = 0.9; SPECULAR = 0.15 * 0.5;
}
