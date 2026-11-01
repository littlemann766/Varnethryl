shader_type spatial;
// test 37: vertex-colour island material with per-pixel flat face normals. Beth's island/tile glbs ship without NORMAL,
// and some imported faces came out unlit (pure black wedges ashore at Gullhaven, black cliffs at Vent Harbour).
// Same look as vc_lit.tres (vertex colour albedo, roughness 0.9) + near-camera dither fade (0.8 -> 3 m).
uniform float lift = 0.0;
uniform float ambient = 0.08;
uniform float spec = 0.5;
void fragment() {
	ALBEDO = COLOR.rgb * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
	float d = fract(sin(dot(floor(FRAGCOORD.xy), vec2(12.9898, 78.233))) * 43758.5453);
	if (d > smoothstep(0.8, 3.0, length(VERTEX))) discard;
	vec3 fn = normalize(cross(dFdx(VERTEX), dFdy(VERTEX)));
	if (dot(fn, -VERTEX) < 0.0) fn = -fn;
	NORMAL = fn;
	EMISSION = ALBEDO * ambient;
	ROUGHNESS = 0.9; SPECULAR = spec;
}
