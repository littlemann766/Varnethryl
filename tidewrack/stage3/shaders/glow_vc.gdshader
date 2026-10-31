shader_type spatial;
// Beth: glowing vertex-colour mesh (saltglass crystals, lanterns). Emission = COLOR * energy with a slow pulse; 1 draw call.
// Pair each cave with 3-6 OmniLights (positions in stage3_manifest.json) for the light it throws on the rock.
uniform float energy = 1.1; uniform float pulse = 0.25; uniform float roughness_ = 0.15;
varying vec3 wpos;
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment(){
	float p = 1.0 + pulse * sin(TIME * 1.3 + wpos.x * 0.21 + wpos.z * 0.17);
	ALBEDO = COLOR.rgb * 0.4; EMISSION = COLOR.rgb * energy * p; ROUGHNESS = roughness_; SPECULAR = 0.8;
}
