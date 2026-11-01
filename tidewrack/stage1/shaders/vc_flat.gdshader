shader_type spatial;
// test 37: vertex-colour island material with per-pixel flat face normals. Beth's island/tile glbs ship without NORMAL,
// and some imported faces came out unlit (pure black wedges ashore at Gullhaven, black cliffs at Vent Harbour).
// Same look as vc_lit.tres (vertex colour albedo, roughness 0.9) + near-camera dither fade (0.8 -> 3 m).
uniform float lift = 0.0;
uniform float ambient = 0.3;
uniform float spec = 0.5;
global uniform vec4 hero_cut;   // xyz = hero chest (world), w = 1 when the third-person camera wants the cut-out
varying vec3 wpos;
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	ALBEDO = COLOR.rgb * (1.0 - lift * 2.0) + vec3(lift, lift * 0.95, lift * 0.9);
	float d = fract(sin(dot(floor(FRAGCOORD.xy), vec2(12.9898, 78.233))) * 43758.5453);
	if (d > smoothstep(0.8, 3.0, length(VERTEX))) discard;
	if (hero_cut.w > 0.5 && wpos.y > hero_cut.y - 0.9) {   // rock/walls between the camera and the hero: dither hole around him
		vec3 hv = (VIEW_MATRIX * vec4(hero_cut.xyz, 1.0)).xyz;
		if (-VERTEX.z < -hv.z - 1.0) {
			float ang = acos(clamp(dot(normalize(VERTEX), normalize(hv)), -1.0, 1.0));
			float r = atan(2.2 / max(length(hv), 0.1));
			if (d < smoothstep(r, r * 0.6, ang) * 0.9) discard;
		}
	}
	vec3 fn = normalize(cross(dFdx(VERTEX), dFdy(VERTEX)));
	if (dot(fn, -VERTEX) < 0.0) fn = -fn;
	NORMAL = fn;
	EMISSION = ALBEDO * ambient;
	ROUGHNESS = 0.9; SPECULAR = spec;
}
