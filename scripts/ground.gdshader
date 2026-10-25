shader_type spatial;
uniform vec4 grass_a : source_color = vec4(0.30,0.45,0.18,1.0);
uniform vec4 grass_b : source_color = vec4(0.42,0.52,0.22,1.0);
uniform vec4 road : source_color = vec4(0.58,0.52,0.42,1.0);
uniform float ring_r = 194.0;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p){ vec2 i=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
	return mix(mix(hash(i),hash(i+vec2(1,0)),f.x), mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x), f.y); }
varying vec3 wp;
void vertex(){ wp = (MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment(){
	vec2 p = wp.xz;
	float n = noise(p*0.08)*0.6 + noise(p*0.6)*0.3 + noise(p*3.0)*0.1;
	vec3 g = mix(grass_a.rgb, grass_b.rgb, n);
	// roads: N-S avenue, E-W avenue, ring, plaza, south gate road
	float d = max(abs(p.x) - 6.0, max(-150.0 - p.y, p.y - 600.0));
	d = min(d, max(abs(p.y) - 4.5, abs(p.x) - 150.0));
	d = min(d, abs(length(p) - ring_r) - 4.2);
	d = min(d, length(p) - 16.0);
	d = min(d, max(abs(p.y - 38.0) - 3.0, abs(p.x) - 32.0));
	d = min(d, max(abs(p.y - 71.0) - 3.0, abs(p.x) - 32.0));
	d = min(d, max(abs(p.x - 67.0) - 3.0, abs(p.y) - 120.0));
	d = min(d, max(abs(p.x + 67.0) - 3.0, abs(p.y) - 120.0));
	d += (noise(p*0.9)-0.5)*1.2;
	float r = 1.0 - smoothstep(-0.3, 0.6, d);
	float cob = noise(p*2.5);
	vec3 rc = road.rgb * (0.85 + 0.3*cob);
	ALBEDO = mix(g, rc, r);
	ROUGHNESS = mix(0.95, 0.8, r);
}
