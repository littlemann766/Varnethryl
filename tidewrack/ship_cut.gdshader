shader_type spatial;
render_mode cull_disabled;
// test 37: the ship's own material + an occlusion cut-out: sail/mast/rigging pixels (above the deck) that sit between the
// camera and the hero are dither-faded in a small circle around him, so a camera behind the ship still sees the hero.
uniform sampler2D tex : source_color, filter_linear_mipmap;
uniform vec4 tint : source_color = vec4(1.0);
uniform float use_tex = 1.0;
uniform float cut_on = 0.0;
uniform vec3 hero_pos;
uniform float cut_min_y = 0.0;
uniform float cut_r = 4.0;
varying vec3 wpos;
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	vec3 c = tint.rgb;
	if (use_tex > 0.5) c *= texture(tex, UV).rgb;
	ALBEDO = c * COLOR.rgb;
	ROUGHNESS = 0.9;
	if (cut_on > 0.5 && wpos.y > cut_min_y) {
		vec3 hv = (VIEW_MATRIX * vec4(hero_pos, 1.0)).xyz;
		if (-VERTEX.z < -hv.z - 1.0) {
			float ang = acos(clamp(dot(normalize(VERTEX), normalize(hv)), -1.0, 1.0));
			float r = atan(cut_r / max(length(hv), 0.1));
			float fade = smoothstep(r, r * 0.6, ang);
			float d = fract(sin(dot(floor(FRAGCOORD.xy), vec2(12.9898, 78.233))) * 43758.5453);
			if (d < fade * 0.88) discard;
		}
	}
}
