shader_type spatial;
// Beth: underwater god-rays (cones from the surface). Additive, unshaded, fades with depth and towards the cone edge.
render_mode unshaded, cull_disabled, depth_draw_never, blend_add, shadows_disabled, fog_disabled;
uniform vec4 ray : source_color = vec4(0.55, 0.85, 0.80, 1.0);
uniform float strength = 0.12;   // per cone; each shaft = 3 nested cones (Stage 4) so the core adds up softly
varying vec3 wpos; varying vec3 wnrm;
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz); }
void fragment(){
	vec3 v = normalize(CAMERA_POSITION_WORLD - wpos); float rim = smoothstep(0.0, 0.75, abs(dot(normalize(wnrm), v)));   // soft silhouette
	float depth = clamp(-wpos.y / 30.0, 0.0, 1.0); float flick = 0.75 + 0.25 * sin(TIME * 0.7 + wpos.x * 0.1);
	float near = smoothstep(3.0, 30.0, length(CAMERA_POSITION_WORLD - wpos)); float top = smoothstep(1.0, 14.0, -wpos.y);   // Stage 4: long fade under the surface (no hard bright cone tops)
	ALBEDO = ray.rgb * strength * rim * (1.0 - depth) * flick * near * top; 
}
