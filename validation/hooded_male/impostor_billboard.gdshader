shader_type spatial;
render_mode unshaded, cull_disabled, blend_mix, depth_draw_always, shadows_disabled;

uniform sampler2D atlas : source_color, filter_linear_mipmap;
uniform float fade = 1.0;
// Added to the view index after the yaw test. 0 until an orbit shows the cells are shifted.
uniform float view_bias = 4.0;

varying float v_idx;

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
}

void fragment() {
	float col = mod(v_idx, 4.0);
	float row = floor(v_idx / 4.0);
	// Quad UV.y is 0 at the feet. The atlas stores the head at the top of the cell,
	// which is the high-V side, so the feet sample the low-V side of the cell.
	float v_in = 1.0 - UV.y;
	vec2 uv = vec2((col + UV.x) / 4.0, (1.0 - (row + 1.0) / 2.0) + v_in / 2.0);
	vec4 tex = texture(atlas, uv);
	if (tex.a < 0.5) {
		discard;
	}
	float dither = fract(sin(dot(FRAGCOORD.xy, vec2(12.9898, 78.233))) * 43758.5453);
	if (fade < dither) {
		discard;
	}
	ALBEDO = tex.rgb;
	ALPHA = 1.0;
}
