extends SceneTree
## Software-GL contact frames for the hooded body and the far cards. Not a phone.
## LIBGL_ALWAYS_SOFTWARE=1 godot --display-driver x11 --rendering-method gl_compatibility --rendering-driver opengl3 -s res://tests/hooded_shots.gd
const OUT := "/cursor/stores/self/transfer/test61-hooded/shots"

class Dummy:
	extends Node3D
	var state := "approach"
	var hp := 100.0
	var runner := false
	var speed_mps := 1.25
	func alive() -> bool: return state != "defeated"

func _initialize() -> void: _run.call_deferred()

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var world := Node3D.new()
	root.add_child(world)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.62, 0.64, 0.66)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.85, 0.85, 0.85)
	e.ambient_light_energy = 1.0
	env.environment = e
	world.add_child(env)
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(40, 40)
	var gmat := StandardMaterial3D.new()
	gmat.albedo_color = Color(0.55, 0.56, 0.54)
	gmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	plane.material = gmat
	ground.mesh = plane
	world.add_child(ground)
	var cam := Camera3D.new()
	cam.current = true
	world.add_child(cam)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 30, 0)
	world.add_child(sun)
	var body := Dummy.new()
	body.position = Vector3(0, 0, 0)
	world.add_child(body)
	var vis := HoodedPresenter.new()
	body.add_child(vis)
	var mark := MeshInstance3D.new()
	var dot := SphereMesh.new()
	dot.radius = 0.06
	var dmat := StandardMaterial3D.new()
	dmat.albedo_color = Color(1.0, 0.45, 0.05)
	dmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	dot.material = dmat
	mark.mesh = dot
	mark.position = Vector3(0, 1.15, -1.05)
	world.add_child(mark)
	for _i in 8: await process_frame
	cam.position = Vector3(1.6, 1.35, 2.4)
	cam.look_at(Vector3(0, 1.0, 0))
	await _shot(cam, "hooded_idle")
	body.state = "windup"
	for _i in 18: await process_frame
	await _shot(cam, "hooded_attack_reach")
	body.state = "defeated"
	body.hp = 0.0
	for _i in 40: await process_frame
	await _shot(cam, "hooded_death")
	body.queue_free()
	mark.visible = false
	var card := MeshInstance3D.new()
	var quad := QuadMesh.new()
	quad.size = Vector2(1.0687, 2.1374)
	quad.center_offset = Vector3(0, 1.0687, 0)
	var mat := ShaderMaterial.new()
	mat.shader = load("res://validation/hooded_male/impostor_billboard.gdshader")
	mat.set_shader_parameter("atlas", load("res://assets/hooded_candidate/far_impostor/impostor_atlas_8dir_1024.png"))
	mat.set_shader_parameter("view_bias", 4.0)
	quad.material = mat
	card.mesh = quad
	card.position = Vector3(0, 0, -16)
	world.add_child(card)
	cam.position = Vector3(0, 1.6, -2)
	cam.look_at(Vector3(0, 1.0, -16))
	for _i in 4: await process_frame
	await _shot(cam, "hooded_card_far")
	print("HOODED_SHOTS done")
	quit(0)

func _shot(cam: Camera3D, name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := cam.get_viewport().get_texture().get_image()
	var path := "%s/%s.png" % [OUT, name]
	img.save_png(path)
	print("SHOT %s %dx%d" % [path, img.get_width(), img.get_height()])
