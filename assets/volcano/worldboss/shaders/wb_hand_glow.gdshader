// Wind-up glow ring around the Titan's hand / chest core. Billboarded quad (BoneAttachment3D on hand_L/R or upperChest).
// charge 0..1 over the wind-up: ring contracts, runes spin faster, core brightens.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled;
uniform float charge : hint_range(0.0, 1.0) = 0.0;
uniform vec3 color : source_color = vec3(1.0, 0.45, 0.08);
uniform float intensity : hint_range(0.0, 8.0) = 3.0;
void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz),0,0,0), vec4(0,length(MODEL_MATRIX[1].xyz),0,0), vec4(0,0,length(MODEL_MATRIX[2].xyz),0), vec4(0,0,0,1));
}
void fragment() {
	vec2 p = UV * 2.0 - 1.0; float r = length(p); float a = atan(p.y, p.x);
	float R = mix(0.95, 0.55, charge);
	float ring = smoothstep(0.05, 0.0, abs(r - R));
	float runes = step(0.6, fract(a * 8.0 / 6.2831 + TIME * (0.2 + charge * 1.5))) * smoothstep(0.04, 0.0, abs(r - R - 0.08));
	float core = exp(-r * r * mix(14.0, 5.0, charge)) * charge;
	float rays = pow(max(0.0, sin(a * 6.0 + TIME * 2.0)), 8.0) * smoothstep(R, 0.0, r) * charge * 0.5;
	float v = ring * (0.5 + charge) + runes * 0.8 + core * 1.5 + rays;
	v *= 0.85 + 0.15 * sin(TIME * (6.0 + charge * 14.0));
	ALBEDO = color * v * intensity; ALPHA = clamp(v, 0.0, 1.0);
}
