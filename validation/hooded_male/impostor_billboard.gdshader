shader_type spatial;
render_mode unshaded, cull_disabled, blend_mix, depth_draw_always, shadows_disabled;

uniform sampler2D atlas : source_color, filter_linear_mipmap;
// Added to the view index after the yaw test. 4 puts the baked front on the nose.
uniform float view_bias = 4.0;

varying float v_idx;
varying float v_fade;

void vertex() {
	vec4 origin = MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0);
	vec3 cam = CAMERA_POSITION_WORLD - origin.xyz;
	cam.y = 0.0;
	if (dot(cam, cam) < 1e-6) {
		cam = vec3(0.0, 0.0, 1.0);
	} else {
		cam = normalize(cam);
	}
	vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), cam));
	vec3 wpos = origin.xyz + right * VERTEX.x + vec3(0.0, 1.0, 0.0) * VERTEX.y;
	POSITION = PROJECTION_MATRIX * (VIEW_MATRIX * vec4(wpos, 1.0));

	// Character face yaw, radians. 0 means the face points down world -Z.
	float face_yaw = INSTANCE_CUSTOM.x;
	vec3 face = vec3(-sin(face_yaw), 0.0, -cos(face_yaw));
	float rel = atan(cam.x, cam.z) - atan(face.x, face.z);
	rel = mod(rel + 6.2831853, 6.2831853);
	float idx = floor(rel / 6.2831853 * 8.0 + 0.5);
	v_idx = mod(idx + view_bias, 8.0);
	float dist = length(CAMERA_POSITION_WORLD - origin.xyz);
	v_fade = smoothstep(8.0, 14.0, dist);
}

void fragment() {
	float col = mod(v_idx, 4.0);
	float row = floor(v_idx / 4.0);
	// QuadMesh faces +Z. PlaneMesh writes UV (1-u, 1-v) with v=0 on the low edge,
	// so UV.y is 0 at the top of the card and 1 at the feet. The atlas keeps the
	// head at the top of each cell, and Godot 4 reads UV.y 0 from the top of the
	// texture. Sampling UV.y straight keeps the head up. Inverting it plants the
	// head in the grass.
	vec2 uv = vec2((col + UV.x) / 4.0, (row + UV.y) * 0.5);
	vec4 tex = texture(atlas, uv);
	if (tex.a < 0.5) {
		discard;
	}
	float dither = fract(sin(dot(FRAGCOORD.xy, vec2(12.9898, 78.233))) * 43758.5453);
	if (v_fade < dither) {
		discard;
	}
	ALBEDO = tex.rgb;
	ALPHA = 1.0;
}
