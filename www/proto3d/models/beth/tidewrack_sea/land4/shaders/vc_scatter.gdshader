shader_type spatial;
// Island scatter. Vertex colour only, so it adds no samplers beside the terrain arrays.
// Soft foliage and solid trunks share this material. Collision stays in the *_col.glb files.
render_mode cull_disabled;
varying vec3 vcol;
void vertex() { vcol = COLOR.rgb; }
void fragment() {
	ALBEDO = vcol;
	ROUGHNESS = 0.9;
	SPECULAR = 0.05;
}
void light() {
	// A little wrap so a canopy is not a black card on the shade side. No texture reads.
	float ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0);
	float wrap = clamp(dot(NORMAL, LIGHT) * 0.55 + 0.45, 0.0, 1.0);
	DIFFUSE_LIGHT += (ndl * 0.72 + wrap * 0.28) * ATTENUATION * LIGHT_COLOR * ALBEDO;
}
