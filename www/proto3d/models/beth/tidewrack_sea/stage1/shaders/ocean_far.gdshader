shader_type spatial;
// Beth terrain pass fix 5: far-ocean ring around the camera-following water grid. Flat, 1 draw call, ~400 tris.
// Starts under the grid's edge (r 700 m, y -0.25) and runs to r 9 km, colour = the region's deep water, fading into
// the horizon/fog colour so the sea meets the sky instead of ending in a dark rectangle.
render_mode cull_back, depth_draw_opaque, specular_schlick_ggx;
uniform vec4 deep : source_color = vec4(0.03, 0.16, 0.26, 1.0);
uniform vec4 horizon : source_color = vec4(0.62, 0.72, 0.82, 1.0);  // = sky horizon / fog colour (set per time of day)
uniform float fade_start = 900.0;
uniform float fade_end = 6500.0;
varying vec3 wpos;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment(){
	float d = length(wpos.xz - CAMERA_POSITION_WORLD.xz);
	float k = smoothstep(fade_start, fade_end, d);
	float n = noise(wpos.xz * 0.004 + TIME * 0.01) * 0.5 + noise(wpos.xz * 0.02 - TIME * 0.02) * 0.5;
	vec3 c = deep.rgb * (0.9 + 0.2 * n);
	ALBEDO = mix(c, horizon.rgb * 0.92, k * k);
	ROUGHNESS = mix(0.18, 0.6, k); METALLIC = 0.0; SPECULAR = 0.5 * (1.0 - k);
	NORMAL = normalize((VIEW_MATRIX * vec4(vec3((n - 0.5) * 0.04, 1.0, (n - 0.5) * 0.04), 0.0)).xyz);
}
