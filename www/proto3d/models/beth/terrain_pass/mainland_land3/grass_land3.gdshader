shader_type spatial;
render_mode cull_disabled;
uniform vec4 base_col : source_color = vec4(0.18,0.32,0.10,1.0);
uniform vec4 tip_col : source_color = vec4(0.62,0.72,0.30,1.0);
varying float hgt;
varying float dryv;
varying float varv;
uniform vec2 volc_c = vec2(405.0, -402.0);
uniform vec4 dry_col : source_color = vec4(0.70,0.64,0.32,1.0);
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p){ vec2 i=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
	return mix(mix(hash(i),hash(i+vec2(1,0)),f.x), mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x), f.y); }
void vertex(){
	hgt = UV.y;
	vec3 wp = (MODEL_MATRIX*vec4(0,0,0,1)).xyz;
	float t = TIME*1.8 + wp.x*0.15 + wp.z*0.11;
	float w = (sin(t)*0.6 + sin(t*2.3)*0.25) * (1.0 - UV.y) * (1.0 - UV.y);
	VERTEX.x += w * 0.25; VERTEX.z += w * 0.12;
	// Beth land3: collapse blades on the scorched volcano ground, dry them toward its edge, meadow tint variety
	float dvc = length(wp.xz - volc_c) + (noise(wp.xz * 0.02) - 0.5) * 90.0;
	VERTEX *= smoothstep(170.0, 235.0, dvc);
	dryv = max(smoothstep(0.55, 0.85, noise(wp.xz * 0.011 + 3.1)) * 0.7, 1.0 - smoothstep(235.0, 340.0, dvc));
	varv = noise(wp.xz * 0.05 + 11.0);
	NORMAL = vec3(0,1,0);
}
void fragment(){
	vec3 wp = (INV_VIEW_MATRIX*vec4(VERTEX,1.0)).xyz;
	float v = fract(sin(dot(floor(wp.xz*0.7), vec2(12.9,78.2)))*437.5)*0.25;
	vec3 tip = mix(tip_col.rgb, dry_col.rgb, dryv);
	tip = mix(tip, tip * vec3(0.72, 0.95, 0.75), smoothstep(0.6, 0.85, varv) * 0.7);
	tip = mix(tip, vec3(0.7, 0.62, 0.55), smoothstep(0.25, 0.1, varv) * 0.35);
	ALBEDO = mix(tip*(0.9+v), base_col.rgb, UV.y);
	ROUGHNESS = 0.9; SPECULAR = 0.2;
	BACKLIGHT = vec3(0.25,0.35,0.1);
}
