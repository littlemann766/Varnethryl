shader_type spatial;
// Beth terrain_fix2: grass past the town grass, out to the map edge. One periodic tile of clumps rides with the camera
// (snapped to the tile, so it never pops); heights come from the baked terrain height texture (same triangles as the
// terrain/collision mesh), density from the baked mask (off roads, water, sea, harbour, volcano, rock, fields, buildings).
render_mode cull_disabled, world_vertex_coords;
uniform sampler2D t_h : filter_nearest, repeat_disable;     // RG8 16-bit height
uniform sampler2D t_data : filter_linear, repeat_disable;   // R = grass density
uniform float t_extent = 1024.0;
uniform float hmin = -16.0;
uniform float hmax = 496.0;
uniform float fade_start = 50.0;
uniform float fade_end = 70.0;
uniform float near_cut = 0.0;     // lod1: grows in over [near_cut-6, near_cut]
uniform float density = 1.0;      // tier thinning (hash test, keeps an even subset)
uniform vec4 base_col : source_color = vec4(0.18,0.32,0.10,1.0);
uniform vec4 tip_col : source_color = vec4(0.62,0.72,0.30,1.0);
uniform vec4 dry_col : source_color = vec4(0.70,0.64,0.32,1.0);
varying float hgt;
varying float dryv;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p){ vec2 i=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
	return mix(mix(hash(i),hash(i+vec2(1,0)),f.x), mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x), f.y); }
float h_at(ivec2 c){ vec2 rg = texelFetch(t_h, clamp(c, ivec2(0), ivec2(1023)), 0).rg; return hmin + (rg.r * 65280.0 + rg.g * 255.0) / 65535.0 * (hmax - hmin); }
float height_at(vec2 p){
	vec2 f = (p / (2.0 * t_extent) + 0.5) * 1024.0 - 0.5; ivec2 i = ivec2(floor(f)); vec2 t = fract(f);
	return mix(mix(h_at(i), h_at(i + ivec2(1, 0)), t.x), mix(h_at(i + ivec2(0, 1)), h_at(i + ivec2(1, 1)), t.x), t.y);
}
void vertex(){
	hgt = UV.y;
	vec3 org = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec2 p = org.xz;
	float rnd = hash(floor(p * 3.0) + 0.37);
	float m = texture(t_data, p / (2.0 * t_extent) + 0.5).r;
	float d = distance(p, CAMERA_POSITION_WORLD.xz);
	float s = (1.0 - smoothstep(fade_start, fade_end, d)) * step(rnd, m * density);
	if (near_cut > 0.0) s *= smoothstep(near_cut - 6.0, near_cut, d);
	s *= 0.7 + 0.7 * hash(p + 5.1);
	dryv = smoothstep(0.55, 0.85, noise(p * 0.011 + 3.1));
	float t = TIME * 1.8 + p.x * 0.15 + p.y * 0.11;
	float w = (sin(t) * 0.6 + sin(t * 2.3) * 0.25) * (1.0 - UV.y) * (1.0 - UV.y);
	// world-space: scale about the clump root, sway, then drop the root onto the baked terrain height
	vec3 lv = (VERTEX - org) * s;
	lv.x += w * 0.25 * s; lv.z += w * 0.12 * s;
	VERTEX = vec3(org.x, height_at(p), org.z) + lv;
	NORMAL = vec3(0, 1, 0);
}
void fragment(){
	vec3 wp = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float v = fract(sin(dot(floor(wp.xz * 0.7), vec2(12.9, 78.2))) * 437.5) * 0.25;
	vec3 tip = mix(tip_col.rgb, dry_col.rgb, dryv * 0.7);
	ALBEDO = mix(tip * (0.9 + v), base_col.rgb, UV.y);
	ROUGHNESS = 0.9; SPECULAR = 0.2;
	BACKLIGHT = vec3(0.25, 0.35, 0.1);
}
