// World-boss weak-point magma crystal. Godot 4.7 Mobile. No textures, 0 samples.
// state: glow 0=dim(idle) 1=intact 2=wind-up glowing; hit_flash 0..1 (set to 1 on hit, tween to 0 in ~0.15 s); broken 0..1 (1 = dead/dark).
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform vec3 core_hot : source_color = vec3(1.0, 0.72, 0.25);
uniform vec3 core_deep : source_color = vec3(0.85, 0.16, 0.02);
uniform float glow : hint_range(0.0, 3.0) = 1.0;
uniform float hit_flash : hint_range(0.0, 1.0) = 0.0;
uniform float broken : hint_range(0.0, 1.0) = 0.0;
uniform float pulse_speed : hint_range(0.0, 8.0) = 2.2;
uniform float energy : hint_range(0.0, 16.0) = 4.0;
varying float h;
void vertex() { h = VERTEX.y; }
void fragment() {
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
	float facet = fract(sin(dot(floor(NORMAL * 7.0), vec3(12.9, 78.2, 37.7))) * 43758.5); // per-facet sparkle
	float pulse = 0.65 + 0.35 * sin(TIME * pulse_speed * (1.0 + glow * 0.5) - h * 3.0);
	vec3 col = mix(core_deep, core_hot, clamp(fres * 0.6 + facet * 0.4, 0.0, 1.0));
	vec3 dead = vec3(0.07, 0.05, 0.045);
	ALBEDO = mix(col * 0.35, dead, broken);
	ROUGHNESS = mix(0.25, 0.9, broken);
	METALLIC = 0.0;
	float e = energy * (0.25 + glow * 0.75) * pulse * (0.6 + 0.4 * facet) * (1.0 - broken);
	e += broken * 0.15 * (0.5 + 0.5 * sin(TIME * 0.7 + h * 9.0)); // faint dying embers
	EMISSION = col * e + vec3(1.0, 0.95, 0.85) * hit_flash * 10.0;
}
