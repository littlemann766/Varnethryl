shader_type spatial;
render_mode cull_disabled;
uniform vec4 base_col : source_color = vec4(0.18,0.32,0.10,1.0);
uniform vec4 tip_col : source_color = vec4(0.62,0.72,0.30,1.0);
varying float hgt;
void vertex(){
	hgt = UV.y;
	vec3 wp = (MODEL_MATRIX*vec4(0,0,0,1)).xyz;
	float t = TIME*1.8 + wp.x*0.15 + wp.z*0.11;
	float w = (sin(t)*0.6 + sin(t*2.3)*0.25) * (1.0 - UV.y) * (1.0 - UV.y);
	VERTEX.x += w * 0.25; VERTEX.z += w * 0.12;
	NORMAL = vec3(0,1,0);
}
void fragment(){
	vec3 wp = (INV_VIEW_MATRIX*vec4(VERTEX,1.0)).xyz;
	float v = fract(sin(dot(floor(wp.xz*0.7), vec2(12.9,78.2)))*437.5)*0.25;
	ALBEDO = mix(tip_col.rgb*(0.9+v), base_col.rgb, UV.y);
	ROUGHNESS = 0.9; SPECULAR = 0.2;
	BACKLIGHT = vec3(0.25,0.35,0.1);
}
