// Lava Wave: rising molten wall. Open CylinderMesh (radius 1, height 1, no caps, 48 segs), scale (R, wall_h, R).
// rise 0..1 grows the wall over the 10 s wind-up. Whole wall is molten: dark crust plates drifting on bright flowing lava,
// hot glowing crest lip, darker base. ground_mode=true on a flat strip = warning band (UV.y across the band).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;
uniform float rise : hint_range(0.0, 1.0) = 0.0;
uniform vec3 hot : source_color = vec3(1.0, 0.62, 0.14);
uniform vec3 mid : source_color = vec3(0.95, 0.25, 0.03);
uniform vec3 crust : source_color = vec3(0.12, 0.03, 0.01);
uniform float intensity : hint_range(0.0, 8.0) = 2.2;
uniform bool ground_mode = false;
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
	return mix(mix(h21(i),h21(i+vec2(1,0)),f.x), mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x), f.y); }
float fbm(vec2 p){ return vn(p)*0.55 + vn(p*2.1+3.1)*0.3 + vn(p*4.3+7.7)*0.15; }
void fragment() {
	vec2 uv = vec2(UV.x * 48.0, ground_mode ? UV.y * 3.0 : (1.0 - UV.y) * 6.0);
	float y = ground_mode ? abs(UV.y * 2.0 - 1.0) : 1.0 - UV.y;   // 0 = base/centre, 1 = top/edge
	// lava pours up-and-over: flow scrolls upward, crust plates drift slower
	float fl = fbm(uv * vec2(1.0, 1.6) + vec2(TIME * 0.15, -TIME * 1.2));
	float cr = fbm(uv * 1.3 + vec2(-TIME * 0.08, -TIME * 0.45) + fl * 1.2);
	float plates = smoothstep(0.52, 0.62, cr);                      // dark crust islands
	float seams = 1.0 - smoothstep(0.0, 0.08, abs(cr - 0.57));      // glowing seams around plates
	vec3 lava = mix(mid, hot, smoothstep(0.35, 0.8, fl));
	vec3 col = mix(lava, crust, plates * 0.85) + hot * seams * 0.6;
	float a;
	if (ground_mode) {
		float band = smoothstep(1.0, 0.75, y);
		float pulse = 0.55 + 0.45 * sin(TIME * 5.0 - UV.x * 60.0);
		col = mix(col, hot, 0.3) * (0.6 + 0.6 * rise);
		a = band * (0.5 + 0.4 * pulse) * (0.35 + 0.65 * rise);
	} else {
		float crest = rise + 0.05 * (fbm(vec2(UV.x * 30.0 + TIME, TIME * 2.0)) - 0.5);
		float body = smoothstep(crest + 0.01, crest - 0.02, y);
		float lip = smoothstep(0.07, 0.0, abs(y - crest)) * step(0.0, crest - 0.02);
		col = mix(col, crust * 1.5, smoothstep(0.25, 0.0, y) * 0.6);     // darker base where it meets the ground
		col = mix(col, vec3(1.0, 0.9, 0.55), lip * 0.7);
		a = max(body * 0.96, lip);
	}
	ALBEDO = col * intensity * 0.6;
	ALPHA = clamp(a, 0.0, 1.0);
}
