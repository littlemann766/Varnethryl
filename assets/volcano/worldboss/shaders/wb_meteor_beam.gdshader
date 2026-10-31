// Meteor Call: falling-meteor guide beam. Open CylinderMesh (r 1, h 1, no caps, 16 segs), node scale (3, 140, 3) (thinner than the 7 m circle),
// base at the target circle centre (position.y = 70). Readable from the ground at any angle. Additive, 0 textures.
// progress 0..1 (same as the circle): beam narrows and brightens toward impact; sparks stream downward.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled;
uniform vec3 color : source_color = vec3(1.0, 0.35, 0.08);
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform float intensity : hint_range(0.0, 8.0) = 0.9;
float h(float x){ return fract(sin(x * 91.7) * 43758.5); }
void fragment() {
	float y = UV.y;                                   // 0 top .. 1 ground
	float side = abs(dot(NORMAL, VIEW));               // fade the silhouette edge -> soft column
	float core = pow(side, 2.0 + 6.0 * progress);
	float fadev = smoothstep(0.0, 0.5, y) * (0.6 + 0.4 * y);
	float col_id = floor(UV.x * 24.0);
	float streak = smoothstep(0.85, 1.0, fract(y * 3.0 + TIME * (1.5 + h(col_id) * 2.0) + h(col_id + 3.0))) * step(0.6, h(col_id + 7.0));
	float strobe = progress > 0.85 ? 0.6 + 0.4 * step(0.5, fract(TIME * 7.0)) : 1.0;
	float v = (core * 0.6 + streak * 0.8) * fadev * (0.3 + 0.9 * progress) * strobe;
	ALBEDO = color * v * intensity;
}
