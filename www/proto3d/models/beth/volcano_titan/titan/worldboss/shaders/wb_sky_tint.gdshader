// Meteor Call red sky tint. Full-screen ColorRect in a CanvasLayer (layer below HUD). amount 0..1 tween over 1.5 s. 1 screen read.
shader_type canvas_item;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform float amount : hint_range(0.0, 1.0) = 0.0;
uniform vec3 tint : source_color = vec3(1.0, 0.32, 0.18);
void fragment() {
	vec3 c = texture(screen_tex, SCREEN_UV).rgb;
	float l = dot(c, vec3(0.3, 0.59, 0.11));
	vec3 red = vec3(min(1.0, l * 1.35 + 0.08), l * 0.55, l * 0.35) * tint * 1.4;
	float vig = smoothstep(0.35, 0.95, length(SCREEN_UV - 0.5) * 1.4);
	COLOR = vec4(mix(c, red, amount * (0.65 + 0.35 * vig)), 1.0);
}
