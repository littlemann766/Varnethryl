// Lava Wave safe-gap marker: glowing cool post (CylinderMesh) or flare (QuadMesh, billboard=true). Unshaded, 0 textures, Mobile-safe.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled;
uniform vec3 safe_col : source_color = vec3(0.35, 0.9, 1.0);
uniform vec3 core_col : source_color = vec3(0.85, 1.0, 1.0);
uniform float intensity : hint_range(0.0, 8.0) = 2.5;
uniform float rise : hint_range(0.0, 1.0) = 1.0;
uniform bool billboard = false;
void vertex() {
	if (billboard) {
		MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
		MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz),0,0,0), vec4(0,length(MODEL_MATRIX[1].xyz),0,0), vec4(0,0,length(MODEL_MATRIX[2].xyz),0), vec4(0,0,0,1));
	}
}
void fragment() {
	float pulse = 0.75 + 0.25 * sin(TIME * 3.0);
	float v;
	if (billboard) {
		vec2 p = UV * 2.0 - 1.0; float r = length(p);
		float rays = pow(max(0.0, 1.0 - abs(p.x) * 6.0), 2.0) + pow(max(0.0, 1.0 - abs(p.y) * 6.0), 2.0);
		v = exp(-r * r * 6.0) * 1.4 + rays * 0.5 * (1.0 - r);
		v *= pulse;
	} else {
		float side = abs(dot(NORMAL, VIEW));
		float h = UV.y;                      // 0 top .. 1 bottom
		float band = 0.6 + 0.4 * step(0.5, fract(h * 4.0 - TIME * 1.5)); // energy bands rising
		v = (0.35 + 0.65 * side) * band * (0.5 + 0.5 * (1.0 - h * 0.4)) * pulse;
	}
	vec3 c = mix(safe_col, core_col, clamp(v - 0.8, 0.0, 1.0));
	ALBEDO = c * v * intensity * (0.25 + 0.75 * rise);
}
