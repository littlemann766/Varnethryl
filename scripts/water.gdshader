shader_type spatial;
render_mode blend_mix, cull_back, specular_schlick_ggx;
uniform vec4 deep : source_color = vec4(0.05,0.22,0.32,0.85);
uniform vec4 shallow : source_color = vec4(0.2,0.55,0.6,0.75);
void vertex() {
	float t = TIME;
	vec3 w = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz;
	VERTEX.y += sin(w.x*0.6 + t*1.5)*0.04 + cos(w.z*0.5 + t*1.2)*0.04;
}
void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX,1.0)).xyz;
	float t = TIME;
	vec2 p = w.xz;
	float n = sin(p.x*1.7+t*2.0)*cos(p.y*1.3-t*1.6) + sin((p.x+p.y)*2.3+t*2.7)*0.5;
	NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4(n*0.12, 0.0, cos(p.x*1.1-t)*0.12, 0.0)).xyz);
	float f = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	ALBEDO = mix(deep.rgb, shallow.rgb, 0.5 + 0.5*n*0.4);
	ALPHA = mix(deep.a, 1.0, f);
	METALLIC = 0.0;
	ROUGHNESS = 0.05;
	SPECULAR = 0.8;
}
