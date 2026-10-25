shader_type spatial;
render_mode cull_back, specular_schlick_ggx;
uniform vec4 deep : source_color = vec4(0.02,0.12,0.18,1.0);
uniform vec4 shallow : source_color = vec4(0.12,0.38,0.42,1.0);
uniform float wave = 0.04;
void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz;
	VERTEX.y += (sin(w.x*0.6 + TIME*1.5) + cos(w.z*0.5 + TIME*1.2)) * wave;
}
vec2 h2(vec2 p){ return fract(sin(vec2(dot(p,vec2(127.1,311.7)),dot(p,vec2(269.5,183.3))))*43758.5453); }
void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX,1.0)).xyz;
	vec2 p = w.xz; float t = TIME;
	vec2 g = vec2(
		cos(p.x*1.7+t*2.0)*0.6 + cos((p.x+p.y)*3.1+t*2.9)*0.3 + cos(p.x*7.0 - t*4.0)*0.1,
		sin(p.y*1.3-t*1.6)*0.6 + sin((p.x-p.y)*2.7+t*2.3)*0.3 + sin(p.y*6.5 + t*3.7)*0.1);
	vec3 nw = normalize(vec3(g.x*0.10, 1.0, g.y*0.10));
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
	float f = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	ALBEDO = mix(deep.rgb, shallow.rgb, 0.5 + 0.25*g.x) * (1.0 - f*0.6);
	METALLIC = 0.6 + 0.3*f;
	ROUGHNESS = 0.02;
	SPECULAR = 1.0;
}
