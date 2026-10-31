shader_type spatial;
// Beth: kelp ribbons. COLOR.a = height fraction along the strand (0 root .. 1 tip) -> sway grows towards the tip.
render_mode cull_disabled;
uniform float sway = 1.4; uniform vec2 current = vec2(0.7, 0.3);
void vertex(){
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; float h = COLOR.a; float t = TIME;
	float s = sin(t * 0.9 + wp.x * 0.15 + wp.y * 0.3) * 0.6 + sin(t * 1.7 + wp.z * 0.2) * 0.4;
	VERTEX.xz += (current * 0.6 + vec2(s, s * 0.5)) * sway * h * h;
}
void fragment(){ ALBEDO = COLOR.rgb; ROUGHNESS = 0.7; BACKLIGHT = COLOR.rgb * 0.6; }
