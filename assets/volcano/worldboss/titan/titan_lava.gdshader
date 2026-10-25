// Ashen Titan lava veins - Godot 4.7, Mobile/Compatibility friendly.
// 4 texture samples, no screen reads. Works on the skinned mesh as a material override.
shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap, repeat_disable;
uniform sampler2D rm_tex : hint_default_white, filter_linear_mipmap, repeat_disable; // G=rough B=metal (glTF)
uniform sampler2D lava_mask : hint_default_black, filter_linear_mipmap, repeat_disable; // R vein, G char halo, B flow phase, A original glow

uniform float glow_strength : hint_range(0.0, 8.0) = 1.0; // stage 1/2/3 = 1.0 / 2.2 / 4.0
uniform float flow_speed : hint_range(0.0, 4.0) = 0.6;
uniform float pulse_speed : hint_range(0.0, 6.0) = 1.4;
uniform vec3 lava_hot : source_color = vec3(1.0, 0.62, 0.16);
uniform vec3 lava_cool : source_color = vec3(0.75, 0.10, 0.02);
uniform float char_amount : hint_range(0.0, 1.0) = 0.8;
uniform float base_glow : hint_range(0.0, 4.0) = 1.0; // original ember glow
uniform float vein_scale : hint_range(0.0, 1.5) = 1.0; // grow veins per stage (0.85/1.0/1.2)

void fragment() {
	vec4 m = texture(lava_mask, UV);
	vec3 base = texture(albedo_tex, UV).rgb;
	vec3 rm = texture(rm_tex, UV).rgb;
	NORMAL_MAP = texture(normal_tex, UV).rgb;

	float vein = smoothstep(0.45, 0.95, clamp(m.r * vein_scale, 0.0, 1.0));
	// travelling flow: phase from baked noise + world-down bias, no extra samples
	float phase = m.b * 18.0 - TIME * flow_speed * 3.0;
	float flow = 0.55 + 0.45 * sin(phase) * sin(phase * 0.37 + 1.7);
	float pulse = 0.8 + 0.2 * sin(TIME * pulse_speed + m.b * 6.2831);
	float core = vein * vein;
	vec3 lava = mix(lava_cool, lava_hot, clamp(core * flow * 1.3, 0.0, 1.0));

	vec3 crust = vec3(0.045, 0.038, 0.034);
	vec3 alb = mix(base, crust, m.g * char_amount);
	alb = mix(alb, lava * 0.25, vein * 0.8);
	ALBEDO = alb;
	ROUGHNESS = mix(rm.g, 0.95, m.g * 0.6);
	METALLIC = 0.0;
	vec3 e = lava * vein * flow * pulse * glow_strength * 1.1;
	e += lava_hot * m.a * base_glow * (0.6 + 0.4 * pulse) * (0.4 + 0.3 * glow_strength) * (1.0 - vein);
	EMISSION = e;
}
