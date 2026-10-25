shader_type spatial;
uniform vec4 grass_a : source_color = vec4(0.27,0.43,0.16,1.0);
uniform vec4 grass_b : source_color = vec4(0.44,0.54,0.22,1.0);
uniform vec4 road : source_color = vec4(0.60,0.54,0.44,1.0);
uniform vec4 rock : source_color = vec4(0.45,0.42,0.38,1.0);
uniform vec4 snow : source_color = vec4(0.93,0.95,1.0,1.0);
uniform float ring_r = 194.0;
uniform vec4 segs[64];
uniform float seg_hw[64];
uniform int seg_n = 0;
uniform int street_n = 0;   // segs[street_n..] are door footpaths: packed dirt, narrower, no cobbles
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
	d = min(d, abs(length(p) - ring_r) - 4.2);
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
	float cob = noise(p*2.5) * noise(p*7.0 + 3.1);
	vec3 rc = road.rgb * (0.8 + 0.5*cob);
	float slope = 1.0 - clamp(wn.y, 0.0, 1.0);
	float fr = (1.0 - smoothstep(-0.15, 0.25, fd + (noise(p*1.7)-0.5)*0.35)) * (1.0 - r);
	vec3 col = mix(g, rc, r);
	col = mix(col, path_col.rgb * (0.85 + 0.3*noise(p*4.0)), fr);
	col = mix(col, rock.rgb * (0.8 + 0.4*n), smoothstep(0.25, 0.45, slope));
	col = mix(col, snow.rgb, smoothstep(48.0, 60.0, wp.y + n*6.0) * (1.0 - smoothstep(0.55, 0.75, slope)));
	ALBEDO = col;
	ROUGHNESS = mix(0.95, 0.75, r);
}
