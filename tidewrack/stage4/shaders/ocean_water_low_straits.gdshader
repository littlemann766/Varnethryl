shader_type spatial;
// Beth: Tidewrack Sea water, LOW tier - Stage 4 Straits variant (stage1 shader untouched). Cooler, less mirror-like so the ash haze sky
// does not tint the flat water brown: lower specular, mid roughness, cool fresnel sheen.
// Based on stage1 ocean_water_low. Flat 32x32 grid (no vertex waves), 1 scrolling normal, shore foam from the
// same baked texture (1 sample). Ship bob is done by script. One draw call.
render_mode cull_back;
uniform vec4 deep : source_color = vec4(0.03, 0.16, 0.26, 1.0);
uniform vec4 shallow : source_color = vec4(0.12, 0.50, 0.50, 1.0);
uniform float rough = 0.4;
uniform float spec = 0.18;
uniform vec4 sheen : source_color = vec4(0.10, 0.17, 0.21, 1.0);
uniform sampler2D shore_dist : filter_linear, repeat_disable;
uniform vec4 shore_rect = vec4(-1200.0, -1300.0, 2700.0, 2600.0);
varying vec3 wpos;
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment(){
	vec2 uv = (wpos.xz - shore_rect.xy) / shore_rect.zw; float sd = (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) ? 255.0 : texture(shore_dist, uv).r * 255.0;
	float n = fract(sin(dot(floor(wpos.xz * 0.5 + TIME * 0.4), vec2(12.9, 78.2))) * 43758.5);
	vec3 col = mix(deep.rgb, shallow.rgb, 1.0 - smoothstep(0.0, 70.0, sd));
	col = mix(col, vec3(0.9, 0.95, 0.96), (1.0 - smoothstep(4.0, 12.0, sd)) * 0.7);
	NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4((n - 0.5) * 0.08, 0.0, 0.0, 0.0)).xyz);
	float fr = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	col = mix(col, sheen.rgb, fr * 0.6);
	ALBEDO = col; ROUGHNESS = rough; SPECULAR = spec;
}
