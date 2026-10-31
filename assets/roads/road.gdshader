shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;
uniform sampler2D dirt_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D dirt_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D dirt_rough : hint_roughness_r, filter_linear_mipmap, repeat_enable;
uniform sampler2D cobble_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D cobble_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D cobble_rough : hint_roughness_r, filter_linear_mipmap, repeat_enable;
uniform sampler2D edge_noise : filter_linear_mipmap, repeat_enable;
uniform vec4 grass_a : source_color = vec4(0.27,0.43,0.16,1.0);   // = ground.gdshader
uniform vec4 grass_b : source_color = vec4(0.44,0.54,0.22,1.0);
uniform float cobble_scale = 0.5;   // cobble tile = 4.4 m
varying vec2 wxz;
void vertex(){ wxz = UV2; }
void fragment(){
	float cob = COLOR.r;
	vec2 uvc = wxz * (1.0 / (8.8 * cobble_scale));
	vec3 da = texture(dirt_albedo, UV).rgb;
	vec3 ca = texture(cobble_albedo, uvc).rgb;
	vec3 alb = mix(da, ca, cob);
	vec3 nm = mix(texture(dirt_normal, UV).rgb, texture(cobble_normal, uvc).rgb, cob);
	float rg = mix(texture(dirt_rough, UV).r, texture(cobble_rough, uvc).r, cob);
	// ragged grass edge: vertex alpha fades the 1.8 m skirt; noise breaks up the line
	float n = texture(edge_noise, wxz * 0.11).r * 0.6 + texture(edge_noise, wxz * 0.45).r * 0.4;
	float a = smoothstep(0.0, 1.0, COLOR.a * 1.6 - 0.35 + (n - 0.5) * 0.9);
	// grass-tinted fringe so the dirt never ends in a hard brown line
	float fr = 1.0 - smoothstep(0.55, 1.0, a);
	vec3 g = mix(grass_a.rgb, grass_b.rgb, n);
	ALBEDO = mix(alb, mix(alb, g, 0.55), fr * (1.0 - cob));
	NORMAL_MAP = nm;
	NORMAL_MAP_DEPTH = 1.2;
	ROUGHNESS = rg;
	ALPHA = a;
}
