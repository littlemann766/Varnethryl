// World-boss Ashen Titan skin (114 m). Godot 4.7 Forward Mobile. 6 texture samples, no screen reads.
// Dense 3D-baked crack network (seam-safe) + pulsing seams that travel up the body + tiled rock detail
// so a 1.9 m player standing at his shin still sees stone grain, cavities and hairline embers.
shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D rm_tex : hint_default_white, filter_linear_mipmap, repeat_disable;
uniform sampler2D lava_mask : hint_default_black, filter_linear_mipmap, repeat_disable; // R vein, G heat halo, B flow phase (rises with height), A original glow
uniform sampler2D detail_tex : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable; // RG normal, B cavity, A micro-crack

uniform float glow_strength : hint_range(0.0, 12.0) = 4.5;   // volcano stage 3 = 4.0; world boss idle 5, ritual 7-8
uniform float vein_scale : hint_range(0.0, 1.5) = 1.0;
uniform float vein_lo : hint_range(0.0, 1.0) = 0.66; // lower = wider cracks (ritual/enrage can drop to 0.55)
uniform float flow_speed : hint_range(0.0, 4.0) = 0.35;     // slow, heavy lava
uniform float seam_pulse_speed : hint_range(0.0, 4.0) = 0.22; // pulses climbing the body (cycles/s)
uniform float seam_pulse_gain : hint_range(0.0, 6.0) = 2.5;
uniform float halo_glow : hint_range(0.0, 2.0) = 0.03;      // heat bleeding into rock beside cracks
uniform vec3 lava_hot : source_color = vec3(1.0, 0.66, 0.2);
uniform vec3 lava_cool : source_color = vec3(0.8, 0.12, 0.02);
uniform float char_amount : hint_range(0.0, 1.0) = 0.85;
uniform vec3 charcoal : source_color = vec3(0.085, 0.08, 0.078); // plate colour
uniform float rock_desat : hint_range(0.0, 1.0) = 0.7;  // pull his reddish base toward neutral stone
uniform float rock_keep : hint_range(0.0, 1.0) = 0.55;  // how much of his original rock detail survives on plates
uniform float base_glow : hint_range(0.0, 4.0) = 1.0;
uniform float detail_scale_a = 46.0;  // fine grain (UV repeats)
uniform float detail_scale_b = 11.0;  // chunky plates
uniform float detail_strength : hint_range(0.0, 2.0) = 1.0;
uniform float detail_fade_far = 140.0; // metres: beyond this only the baked maps show
uniform float micro_glow : hint_range(0.0, 4.0) = 0.7;
uniform float hit_flash : hint_range(0.0, 1.0) = 0.0;       // body hit feedback
uniform float stagger_dim : hint_range(0.0, 1.0) = 0.0;     // 1 while staggered/knocked down: lava cools

void fragment() {
	vec4 m = texture(lava_mask, UV);
	vec3 base = texture(albedo_tex, UV).rgb;
	vec3 rm = texture(rm_tex, UV).rgb;
	vec3 nb = texture(normal_tex, UV).rgb;
	vec4 da = texture(detail_tex, UV * detail_scale_a);
	vec4 db = texture(detail_tex, UV * detail_scale_b + vec2(0.37, 0.61));

	float dist = length(VERTEX);
	float dfade = clamp(1.0 - dist / detail_fade_far, 0.0, 1.0) * detail_strength;
	// whiteout-ish blend of the two detail normals onto the baked normal
	vec2 dn = ((da.rg - 0.5) * 1.0 + (db.rg - 0.5) * 0.8) * dfade;
	NORMAL_MAP = vec3(clamp(nb.rg + dn, 0.0, 1.0), nb.b);
	NORMAL_MAP_DEPTH = 1.25;

	float vein = smoothstep(vein_lo, 0.97, clamp(m.r * vein_scale, 0.0, 1.0));
	float phase = m.b * 18.0 - TIME * flow_speed * 3.0;
	float flow = 0.55 + 0.45 * sin(phase) * sin(phase * 0.37 + 1.7);
	// seam pulse: narrow bright bands climbing the body (m.b rises with height)
	float sp = fract(m.b * 2.0 - TIME * seam_pulse_speed);
	float seam = pow(1.0 - abs(sp - 0.5) * 2.0, 10.0) * seam_pulse_gain;
	float breathe = 0.85 + 0.15 * sin(TIME * 0.9 + m.b * 6.2831);
	float core = vein * vein;
	vec3 lava = mix(lava_cool, lava_hot, clamp(core * flow * 1.3 + seam * 0.3, 0.0, 1.0));

	float cav = mix(1.0, da.b * db.b * 1.6, dfade);
	vec3 crust = vec3(0.04, 0.034, 0.03);
	float lum = dot(base, vec3(0.3, 0.55, 0.15));
	vec3 stone = mix(base, vec3(lum) * vec3(1.0, 0.97, 0.94), rock_desat);
	// plates = his own (desaturated) stone over charcoal; only right beside a seam does it char to black
	vec3 plate = mix(charcoal, stone, rock_keep) * (0.75 + 0.5 * lum);
	float scorch = smoothstep(0.55, 0.95, m.g) * char_amount;
	vec3 alb = mix(plate, crust, scorch) * clamp(cav, 0.35, 1.15);
	alb = mix(alb, lava * 0.2, vein * 0.85);
	ALBEDO = alb;
	ROUGHNESS = mix(rm.g, 0.95, m.g * 0.6);
	METALLIC = rm.b * (1.0 - vein);

	float heat = (1.0 - stagger_dim * 0.75);
	vec3 e = lava * vein * flow * breathe * (1.0 + seam) * glow_strength;
	e += lava_cool * m.g * (1.0 - vein) * halo_glow * glow_strength * 0.25 * (0.7 + 0.3 * breathe);
	// hairline embers visible only up close, only near hot seams
	float micro = max(da.a, db.a * 0.6) * smoothstep(0.6, 0.95, m.g) * dfade;
	e += lava_hot * micro * micro_glow * breathe;
	e += lava_hot * m.a * base_glow * 0.5 * (1.0 - vein);
	EMISSION = e * heat + vec3(1.0, 0.9, 0.75) * hit_flash * 1.5;
}
