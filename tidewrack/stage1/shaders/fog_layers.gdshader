shader_type spatial;
// Beth: soft layered storm-fog bank (Mobile). 5 stacked ribbons, COLOR.r = layer (0 inner/faint/low .. 1 outer/dense/tall).
// No hard top: fbm-broken vertical fade; thickens as the camera approaches (far = faint haze, near = dense), and thins
// right at the camera so you sail *into* it instead of clipping a card. Unshaded, alpha, no depth write: 1 draw call.
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix, fog_disabled;
uniform vec4 fog_col : source_color = vec4(0.62, 0.66, 0.72, 1.0);
uniform vec4 fog_dark : source_color = vec4(0.34, 0.37, 0.43, 1.0);
uniform float opacity = 0.75;
uniform float near_full = 140.0;   // fully thick inside this distance
uniform float far_fade = 1100.0;   // faint haze beyond this
varying vec3 wpos; varying float layer;
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; layer = COLOR.r; }
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 4; i++){ s += a * noise(p); p *= 2.03; a *= 0.5; } return s; }
void fragment(){
	float t = TIME; float hgt = 55.0 + 80.0 * layer; float v = clamp((wpos.y + 6.0) / hgt, 0.0, 1.0);
	float along = (wpos.x + wpos.z) * 0.012;
	vec2 q = vec2(along + t * 0.012 * (1.0 + layer), v * 2.2 - t * 0.02);
	float n = fbm(q * 2.0 + vec2(layer * 7.3, 0.0)); float n2 = fbm(q * 5.0 - vec2(t * 0.03, layer * 3.1));
	float top = 1.0 - smoothstep(0.25 + 0.45 * n, 0.95, v);          // ragged, soft top: no edge line
	float bottom = mix(0.25, 1.0, smoothstep(-1.0, 24.0, wpos.y));      // soft base: no hard line where a card meets the sea
	float puff = smoothstep(0.25, 0.75, n * 0.75 + n2 * 0.4);
	float d = length(CAMERA_POSITION_WORLD - wpos);
	float thick = mix(0.18, 1.0, 1.0 - smoothstep(near_full, far_fade, d)) * smoothstep(6.0, 35.0, d);
	float a = opacity * puff * top * bottom * thick * mix(0.55, 1.0, layer);
	ALBEDO = mix(fog_dark.rgb, fog_col.rgb, clamp(v * 0.6 + n2 * 0.6, 0.0, 1.0)); ALPHA = clamp(a, 0.0, 1.0);
}
