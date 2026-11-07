shader_type spatial;
// Scatter: bark photo on the old trunk vertices, cutout leaf cards on top.
// Four samplers. The terrain shader is a different material and is not touched.
// COLOR.a picks the surface: ~0 flat vertex colour, ~0.22 rock, ~0.45 bark, 1 leaf.
render_mode cull_disabled;

uniform sampler2D bark_col : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D bark_nrm : filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_col : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D leaf_atlas : source_color, filter_linear_mipmap, repeat_disable;

varying vec3 vcol;
varying float kind;
varying vec3 wpos;
varying vec3 wnorm;

void vertex() {
	vcol = COLOR.rgb;
	kind = COLOR.a;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnorm = normalize(mat3(MODEL_MATRIX) * NORMAL);
}

void fragment() {
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
	ALPHA_SCISSOR_THRESHOLD = 0.42;
	vec3 tint = vcol / max(max(vcol.r, max(vcol.g, vcol.b)), 0.001);
	if (kind > 0.75) {
		vec4 t = texture(leaf_atlas, UV);
		// The old cone colours are very dark. Use them as a hue nudge, not a brightness.
		ALBEDO = t.rgb * mix(vec3(0.92), tint, 0.4);
		ALPHA = t.a;
		ALPHA_SCISSOR_THRESHOLD = 0.42;
		ROUGHNESS = 0.74;
		SPECULAR = 0.06;
	} else if (kind > 0.35) {
		vec3 b = texture(bark_col, UV).rgb;
		float gain = clamp(dot(vcol, vec3(0.62, 0.30, 0.12)) * 1.65, 0.28, 1.12);
		ALBEDO = b * mix(vec3(1.0), tint, 0.22) * gain;
		NORMAL_MAP = texture(bark_nrm, UV).rgb;
		ALPHA = 1.0;
		ROUGHNESS = 0.84;
		SPECULAR = 0.04;
	} else if (kind > 0.12) {
		vec3 wn = normalize(wnorm);
		vec3 n = abs(wn);
		n /= n.x + n.y + n.z + 0.0001;
		vec3 r = texture(rock_col, wpos.yz * 0.55).rgb * n.x
			+ texture(rock_col, wpos.xz * 0.55).rgb * n.y
			+ texture(rock_col, wpos.xy * 0.55).rgb * n.z;
		float gain = clamp(dot(vcol, vec3(0.33, 0.42, 0.25)) * 2.0, 0.35, 1.25);
		ALBEDO = r * mix(vec3(1.0), tint, 0.35) * gain;
		ALPHA = 1.0;
		ROUGHNESS = 0.9;
		SPECULAR = 0.04;
	} else {
		ALBEDO = vcol;
		ALPHA = 1.0;
		ROUGHNESS = 0.7;
		SPECULAR = 0.08;
	}
}

void light() {
	float ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0);
	float wrap = clamp(dot(NORMAL, LIGHT) * 0.5 + 0.5, 0.0, 1.0);
	float shade = mix(ndl, ndl * 0.62 + wrap * 0.38, step(0.75, kind));
	DIFFUSE_LIGHT += shade * ATTENUATION * LIGHT_COLOR * ALBEDO;
}
