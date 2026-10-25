shader_type spatial;
uniform vec4 grass_a : source_color = vec4(0.27,0.43,0.16,1.0);
uniform vec4 grass_b : source_color = vec4(0.44,0.54,0.22,1.0);
uniform vec4 road : source_color = vec4(0.60,0.54,0.44,1.0);
uniform vec4 rock : source_color = vec4(0.45,0.42,0.38,1.0);
uniform vec4 snow : source_color = vec4(0.93,0.95,1.0,1.0);
uniform float ring_r = 194.0;
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
	// streets match the three.js game: N-S 9 m, E-W 7.2 m, plaza r 36.4, ring 8.4 m
	float d = max(abs(p.x) - 4.5, max(-150.0 - p.y, p.y - 190.0));
	d = min(d, max(abs(p.y) - 3.6, abs(p.x) - 185.0));
	d = min(d, abs(length(p) - ring_r) - 4.2);
	d = min(d, length(p) - 36.4);
	d = min(d, max(abs(p.y - 38.0) - 3.0, abs(p.x) - 32.0));
	d = min(d, max(abs(p.y - 71.0) - 3.0, abs(p.x) - 32.0));
	d = min(d, max(abs(p.x - 67.0) - 3.0, abs(p.y) - 120.0));
	d = min(d, max(abs(p.x + 67.0) - 3.0, abs(p.y) - 120.0));
	d += (noise(p*0.9)-0.5)*0.8;
	float r = 1.0 - smoothstep(-0.2, 0.4, d);
	float cob = noise(p*2.5) * noise(p*7.0 + 3.1);
	vec3 rc = road.rgb * (0.8 + 0.5*cob);
	float slope = 1.0 - clamp(wn.y, 0.0, 1.0);
	vec3 col = mix(g, rc, r);
	col = mix(col, rock.rgb * (0.8 + 0.4*n), smoothstep(0.25, 0.45, slope));
	col = mix(col, snow.rgb, smoothstep(48.0, 60.0, wp.y + n*6.0) * (1.0 - smoothstep(0.55, 0.75, slope)));
	ALBEDO = col;
	ROUGHNESS = mix(0.95, 0.75, r);
}
