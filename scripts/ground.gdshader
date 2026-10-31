shader_type spatial;
uniform vec4 grass_a : source_color = vec4(0.27,0.43,0.16,1.0);
uniform vec4 grass_b : source_color = vec4(0.44,0.54,0.22,1.0);
uniform vec4 road : source_color = vec4(0.60,0.54,0.44,1.0);
uniform vec4 rock : source_color = vec4(0.45,0.42,0.38,1.0);
uniform vec4 snow : source_color = vec4(0.93,0.95,1.0,1.0);
uniform float ring_r = 194.0;
uniform vec2 volc_c = vec2(405.0, -402.0);   // test 12: no snow on the volcano pad (it sits ~56 m up in the hills)
uniform vec4 segs[64];
uniform float seg_hw[64];
uniform int seg_n = 0;
uniform int street_n = 0;   // segs[street_n..] are door footpaths: packed dirt, narrower, no cobbles
uniform sampler2D cobble_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D cobble_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 path_col : source_color = vec4(0.47,0.37,0.25,1.0);
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p){ vec2 i=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
	return mix(mix(hash(i),hash(i+vec2(1,0)),f.x), mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x), f.y); }
varying vec3 wp;
varying vec3 wn;
void vertex(){ wp = (MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; wn = normalize((MODEL_MATRIX*vec4(NORMAL,0.0)).xyz); }
void fragment(){
	vec2 p = wp.xz;
	float n = noise(p*0.08)*0.6 + noise(p*0.6)*0.3 + noise(p*3.0)*0.1;
	vec3 g = mix(grass_a.rgb, grass_b.rgb, n);
	// in-town streets + door spurs from main.gd STREETS / spurs (test 11), plaza disc, ring road outside the walls
	float d = length(p) - 36.4;
	// test 32 (boss): the ring road just outside the town wall is removed (ring_r kept only so old params still bind)
	// d = min(d, abs(length(p) - ring_r) - 4.2);
	float fd = 1e6;
	for (int i = 0; i < seg_n; i++) {
		vec2 a = segs[i].xy; vec2 b = segs[i].zw; vec2 ab = b - a;
		float t = clamp(dot(p - a, ab) / max(dot(ab, ab), 0.001), 0.0, 1.0);
		vec2 q = abs(p - (a + ab * t));
		float di = max(q.x, q.y) - seg_hw[i];   // square ends: axis-aligned streets
		if (i < street_n) d = min(d, di); else fd = min(fd, di);
	}
	d += (noise(p*0.9)-0.5)*0.8;
	float r = 1.0 - smoothstep(-0.2, 0.4, d);
	// test 13 (boss: flat grey patch under the gates): streets use Beth's road cobble texture (same 4.4 m tile, world UV)
	vec2 uvc = p / 4.4;
	vec3 rc = texture(cobble_albedo, uvc).rgb * (0.92 + 0.16 * noise(p * 0.3));
	float slope = 1.0 - clamp(wn.y, 0.0, 1.0);
	float fr = (1.0 - smoothstep(-0.15, 0.25, fd + (noise(p*1.7)-0.5)*0.35)) * (1.0 - r);
	vec3 col = mix(g, rc, r);
	col = mix(col, path_col.rgb * (0.85 + 0.3*noise(p*4.0)), fr);
	// test 14: mountain rock with layered strata + large-scale tone variation (no checker), snow cap with a ragged line
	float big = noise(p*0.012);
	float strata = 0.5 + 0.5*sin(wp.y*0.45 + noise(p*0.05)*5.0);
	vec3 rk = mix(rock.rgb*0.72, rock.rgb*1.12, strata*0.6 + n*0.4) * mix(vec3(0.95,0.93,0.9), vec3(1.05,1.0,0.95), big);
	rk *= 0.85 + 0.3*noise(p*1.9);
	float hi_rock = smoothstep(70.0, 110.0, wp.y);   // bare rock above the tree line even on gentler slopes
	col = mix(col, rk, max(smoothstep(0.25, 0.45, slope), hi_rock * smoothstep(0.08, 0.2, slope)));
	float snow_line = 48.0 + smoothstep(600.0, 900.0, length(p)) * 92.0 + (noise(p*0.03) - 0.5) * 30.0;
	float sn = smoothstep(snow_line, snow_line + 14.0, wp.y + n*6.0) * smoothstep(170.0, 240.0, length(p - volc_c)) * (1.0 - smoothstep(0.62, 0.8, slope));
	col = mix(col, snow.rgb * (0.92 + 0.08*n), sn);
	ALBEDO = col;
	NORMAL_MAP = mix(vec3(0.5, 0.5, 1.0), texture(cobble_normal, uvc).rgb, r * (1.0 - smoothstep(0.25, 0.45, slope)));
	ROUGHNESS = mix(0.95, 0.75, r);
}
