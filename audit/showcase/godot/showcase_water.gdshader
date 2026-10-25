shader_type spatial;
render_mode cull_disabled, depth_draw_always;
// Beth showcase water: scrolling dual normals, depth-based colour + shoreline foam, fresnel; SSR/sky give reflections.
uniform vec3 deep : source_color = vec3(0.03, 0.13, 0.20);
uniform vec3 shallow : source_color = vec3(0.10, 0.36, 0.40);
uniform vec3 foam_col : source_color = vec3(0.92, 0.95, 0.97);
uniform float foam_width = 1.6;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear;
uniform sampler2D noise1 : filter_linear_mipmap, repeat_enable;
uniform sampler2D noise2 : filter_linear_mipmap, repeat_enable;
varying vec3 wpos;
void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float w = sin(wpos.x * 0.08 + TIME * 0.9) * 0.18 + cos(wpos.z * 0.11 + TIME * 0.7) * 0.14;
	VERTEX.y += w;
}
void fragment() {
	vec2 uv1 = wpos.xz * 0.045 + vec2(TIME * 0.012, TIME * 0.008);
	vec2 uv2 = wpos.xz * 0.11 - vec2(TIME * 0.018, -TIME * 0.011);
	vec3 n1 = texture(noise1, uv1).rgb * 2.0 - 1.0;
	vec3 n2 = texture(noise2, uv2).rgb * 2.0 - 1.0;
	NORMAL_MAP = normalize(vec3(n1.xy + n2.xy, 2.4)) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 0.6;
	float d = texture(depth_tex, SCREEN_UV).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	float scene_z = -v.z / v.w;
	float water_z = -VERTEX.z;
	float depth = max(scene_z - water_z, 0.0);
	float t = clamp(depth / 9.0, 0.0, 1.0);
	vec3 col = mix(shallow, deep, t);
	float f = 1.0 - smoothstep(0.0, foam_width, depth);
	float fn = texture(noise2, wpos.xz * 0.35 + TIME * 0.05).r;
	f = clamp(f * (0.6 + fn) - 0.25, 0.0, 1.0);
	ALBEDO = mix(col, foam_col, f);
	ROUGHNESS = mix(0.03, 0.6, f);
	METALLIC = 0.0;
	SPECULAR = 0.6;
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	ALPHA = clamp(mix(0.78, 1.0, max(fres, f)) , 0.0, 1.0);
}
