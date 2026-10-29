// Beth exterior pass: card2 shared atlas + world-space weathering (Mobile-safe; no screen textures).
// HIGH: macro tone breakup, rain streaks under ledges, ground grime/splash, moss on up-facing surfaces, detail normal.
// LOW (define LOW via exterior_card2_low.gdshader): grime + macro only, no extra normal sampling.
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D orm_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D emissive_tex : source_color, hint_default_black, filter_linear_mipmap, repeat_enable;
uniform sampler2D weather_tex : hint_default_black, filter_linear_mipmap, repeat_enable;
uniform sampler2D detail_normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform vec4 emission_color : source_color = vec4(1.0, 0.72, 0.38, 1.0);
uniform float emission_energy = 0.0;
uniform float normal_scale = 1.0;
uniform float grime_height = 1.3;     // metres above the building base
uniform float grime_strength = 0.6;
uniform float streak_strength = 0.45;
uniform float moss_strength = 0.6;
uniform float macro_strength = 0.25;
uniform float detail_strength = 0.5;
uniform float detail_fade = 30.0;     // detail normal fades out by this distance (m)
varying vec3 wpos;
varying vec3 wnrm;
varying float hbase;
void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	hbase = wpos.y - MODEL_MATRIX[3].y;
}
void fragment() {
	vec3 alb = texture(albedo_tex, UV).rgb;
	vec3 orm = texture(orm_tex, UV).rgb;
	vec2 side_uv = vec2(wpos.x + wpos.z, wpos.y);           // cheap biplanar for walls
	vec4 w_side = texture(weather_tex, side_uv * 0.11);
	vec4 w_top = texture(weather_tex, wpos.xz * 0.09);
	float up = clamp(wnrm.y, 0.0, 1.0);
	vec4 w = mix(w_side, w_top, step(0.6, up));
	// macro tone breakup (kills visible atlas repetition at street distance)
	alb *= 1.0 + (w.r - 0.5) * 2.0 * macro_strength;
	float rough = orm.g;
	// ground grime / rain splash band
	float g = 1.0 - smoothstep(0.0, grime_height * (0.6 + 0.8 * w.a), hbase);
	g *= (1.0 - up * 0.5);
	alb = mix(alb, alb * vec3(0.55, 0.5, 0.45), g * grime_strength);
	rough = mix(rough, 1.0, g * 0.5);
#ifndef LOW
	// rain streaks on vertical faces (stronger high up, under eaves/sills)
	float vert = 1.0 - abs(wnrm.y);
	float s = w_side.g * vert * smoothstep(0.5, 3.5, hbase);
	alb *= 1.0 - s * streak_strength;
	// moss / lichen on up-facing surfaces (roofs, ledges, steps)
	float m = smoothstep(0.45, 0.8, w_top.b) * smoothstep(0.35, 0.8, up);
	alb = mix(alb, vec3(0.2, 0.27, 0.12) * (0.7 + 0.6 * w_top.a), m * moss_strength);
	rough = mix(rough, 0.95, m);
#endif
	ALBEDO = alb;
	ROUGHNESS = rough;
	METALLIC = orm.b;
	AO = orm.r;
	AO_LIGHT_AFFECT = 0.4;
	vec3 n = texture(normal_tex, UV).rgb * 2.0 - 1.0;
#ifndef LOW
	float df = (1.0 - smoothstep(detail_fade * 0.5, detail_fade, length(VERTEX))) * detail_strength;
	vec3 dn = texture(detail_normal_tex, side_uv * 0.6).rgb * 2.0 - 1.0;
	n = normalize(vec3(n.xy + dn.xy * df, n.z));
#endif
	NORMAL_MAP = n * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = normal_scale;
	EMISSION = texture(emissive_tex, UV).rgb * emission_color.rgb * emission_energy;
}
