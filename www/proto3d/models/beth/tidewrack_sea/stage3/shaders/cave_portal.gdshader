shader_type spatial;
// Beth: the bright way out (card just outside the entrance of a cave cell). Unshaded, soft edges, slight flicker.
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix, fog_disabled;
uniform vec4 sky : source_color = vec4(0.75, 0.86, 0.95, 1.0);
void fragment(){ vec2 d = abs(UV - vec2(0.5)) * 2.0; float a = (1.0 - smoothstep(0.6, 1.0, max(d.x, d.y * 0.9))); ALBEDO = sky.rgb * (0.95 + 0.05 * sin(TIME * 2.0)); ALPHA = a; }
