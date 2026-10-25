// World-boss weak-point magma crystal v2. Godot 4.7 Mobile. 0 textures.
// v2: churning molten interior (object-space noise drifting upward), hot facet edges/rim, stronger read at 100-300 m.
// state: glow 0=dim(idle) 1=intact 2=wind-up glowing; hit_flash 0..1 (set 1 on hit, tween to 0 in ~0.15 s); broken 0..1 (1 = dead/dark).
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx, fog_disabled;
uniform vec3 core_hot : source_color = vec3(1.0, 0.78, 0.32);
uniform vec3 core_deep : source_color = vec3(0.85, 0.16, 0.02);
uniform float glow : hint_range(0.0, 3.0) = 1.0;
uniform float hit_flash : hint_range(0.0, 1.0) = 0.0;
uniform float broken : hint_range(0.0, 1.0) = 0.0;
uniform float pulse_speed : hint_range(0.0, 8.0) = 2.2;
uniform float energy : hint_range(0.0, 16.0) = 4.0;
uniform float churn_scale = 3.0;
varying vec3 lp;
float h3(vec3 p){ return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
float vn(vec3 p){ vec3 i=floor(p); vec3 f=fract(p); f=f*f*(3.0-2.0*f);
	return mix(mix(mix(h3(i),h3(i+vec3(1,0,0)),f.x),mix(h3(i+vec3(0,1,0)),h3(i+vec3(1,1,0)),f.x),f.y),
	           mix(mix(h3(i+vec3(0,0,1)),h3(i+vec3(1,0,1)),f.x),mix(h3(i+vec3(0,1,1)),h3(i+vec3(1,1,1)),f.x),f.y),f.z); }
void vertex() { lp = VERTEX; }
void fragment() {
	float ndv = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float fres = pow(1.0 - ndv, 2.5);
	float facet = h3(floor(NORMAL * 7.0));
	float sp = pulse_speed * (1.0 + glow * 0.6);
	// interior churn: seen "through" the facet by offsetting along the view ray (cheap fake depth)
	vec3 q = lp * churn_scale - VIEW * (0.6 * ndv) + vec3(0.0, -TIME * 0.35 * (0.6 + glow * 0.4), 0.0);
	float churn = vn(q) * 0.6 + vn(q * 2.3 + 4.1) * 0.4;
	float pulse = 0.65 + 0.35 * sin(TIME * sp - lp.y * 3.0);
	float inner = smoothstep(0.35, 0.85, churn) * pulse;
	vec3 col = mix(core_deep, core_hot, clamp(inner * 0.8 + fres * 0.5 + facet * 0.15, 0.0, 1.0));
	vec3 dead = vec3(0.07, 0.05, 0.045);
	ALBEDO = mix(col * 0.3, dead, broken);
	ROUGHNESS = mix(0.12, 0.9, broken);
	SPECULAR = 0.8;
	METALLIC = 0.0;
	float e = energy * (0.2 + glow * 0.8) * (0.35 + 0.9 * inner + 0.6 * fres) * (1.0 - broken);
	e += broken * 0.15 * (0.5 + 0.5 * sin(TIME * 0.7 + lp.y * 9.0));
	EMISSION = col * e + core_hot * fres * glow * 1.5 * (1.0 - broken) + vec3(1.0, 0.95, 0.85) * hit_flash * 10.0;
}
