// Ash Fiend / Ember Wisp material (Titan lava style). Godot 4.7 Mobile, 0 textures.
// Vertex colour: R ember-crack mask, G ash variation, B heat. spirit=true for the wisp (whole body is fire, R=1).
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform vec3 lava_hot : source_color = vec3(1.0, 0.62, 0.16);
uniform vec3 lava_cool : source_color = vec3(0.75, 0.10, 0.02);
uniform vec3 ash_dark : source_color = vec3(0.045, 0.038, 0.034);
uniform vec3 ash_light : source_color = vec3(0.16, 0.14, 0.13);
uniform float glow_strength : hint_range(0.0, 8.0) = 1.6;
uniform float flow_speed : hint_range(0.0, 4.0) = 0.8;
uniform float hit_flash : hint_range(0.0, 1.0) = 0.0;
uniform bool spirit = false;
uniform float flicker : hint_range(0.0, 0.2) = 0.04; // wisp vertex flicker (m)
varying vec3 lp;
void vertex() {
	lp = VERTEX;
	if (spirit) {
		float w = COLOR.b; // hot core stays still, tongues flicker
		VERTEX += NORMAL * flicker * (1.0 - w) * sin(TIME * 9.0 + VERTEX.y * 14.0 + VERTEX.x * 7.0);
		VERTEX.y += 0.05 * sin(TIME * 2.0); // bob
	}
}
void fragment() {
	float crack = COLOR.r; float var_ = COLOR.g; float heat = COLOR.b;
	float phase = (lp.y * 9.0 + var_ * 6.0) - TIME * flow_speed * 3.0;
	float flow = 0.6 + 0.4 * sin(phase) * sin(phase * 0.37 + 1.7);
	float pulse = 0.85 + 0.15 * sin(TIME * 2.3 + var_ * 6.28);
	if (spirit) {
		vec3 c = mix(lava_cool, lava_hot, clamp(heat * 1.4 + flow * 0.3, 0.0, 1.0));
		c = mix(c, vec3(1.0, 0.95, 0.8), smoothstep(0.75, 1.0, heat));
		ALBEDO = c * 0.2 * crack + ash_dark * (1.0 - crack);
		ROUGHNESS = 0.5;
		EMISSION = c * crack * glow_strength * 2.0 * flow * pulse;
	} else {
		float v = smoothstep(0.15, 0.85, crack);
		vec3 lava = mix(lava_cool, lava_hot, clamp(v * v * flow * 1.4, 0.0, 1.0));
		ALBEDO = mix(mix(ash_dark, ash_light, var_), lava * 0.25, v * 0.85);
		ROUGHNESS = mix(0.95, 0.6, v);
		EMISSION = lava * v * flow * pulse * glow_strength * (0.6 + 0.6 * heat);
	}
	EMISSION += vec3(1.0, 0.9, 0.8) * hit_flash * 4.0;
}
