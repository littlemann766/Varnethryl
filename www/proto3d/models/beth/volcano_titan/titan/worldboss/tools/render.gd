extends Node3D
var shots=[]; var si=0; var fr=0; var titan; var cam; var lbl; var crystals=[]; var tele=[]
func mat(p): return load(p)
func quad(sz,m,pos,rot=0.0):
	var q=MeshInstance3D.new(); var pm=PlaneMesh.new(); pm.size=Vector2(sz,sz); q.mesh=pm; q.material_override=m.duplicate(); q.position=pos; q.rotation.y=rot; add_child(q); return q
func _ready():
	var env=WorldEnvironment.new(); var e=Environment.new()
	e.background_mode=Environment.BG_COLOR; e.background_color=Color(0.12,0.07,0.06)
	e.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color=Color(0.55,0.42,0.38); e.ambient_light_energy=0.7
	e.glow_enabled=true; e.tonemap_mode=Environment.TONE_MAPPER_FILMIC; env.environment=e; add_child(env)
	var sun=DirectionalLight3D.new(); sun.rotation_degrees=Vector3(-40,200,0); sun.light_energy=1.2; sun.shadow_enabled=true; add_child(sun)
	var g=MeshInstance3D.new(); var pm=PlaneMesh.new(); pm.size=Vector2(2000,2000); g.mesh=pm
	var gm=StandardMaterial3D.new(); gm.albedo_color=Color(0.2,0.17,0.15); gm.roughness=1; g.material_override=gm; add_child(g)
	titan=load("res://titan.glb").instantiate(); add_child(titan)
	var mi=titan.find_children("*","MeshInstance3D",true,false)[0]; mi.material_override=load("res://titan_lava_material.tres")
	var sk:Skeleton3D=titan.find_children("*","Skeleton3D",true,false)[0]
	var ap=titan.find_children("*","AnimationPlayer",true,false)
	var j=JSON.parse_string(FileAccess.get_file_as_string("res://out/attach_points.json"))
	for k in j.points:
		var p=j.points[k]; var ba=BoneAttachment3D.new(); ba.bone_name=p.bone; sk.add_child(ba)
		var n=Node3D.new(); var q=p.rotation_quat; n.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3.ONE*p.scale),Vector3(p.offset[0],p.offset[1],p.offset[2])); ba.add_child(n)
		var c=load("res://"+p.crystal).instantiate(); n.add_child(c); crystals.append(c)
		var cm=c.find_children("*","MeshInstance3D",true,false)[0]; cm.set_surface_override_material(0,load("res://materials/wb_crystal_mat.tres").duplicate())
	# state lineup (crystal row) far right
	var states=[["wb_crystal_forearm.glb",0.0,0,0],["wb_crystal_forearm.glb",1.0,0,0],["wb_crystal_forearm.glb",2.0,0,0],["wb_crystal_forearm.glb",1.0,1,0],["wb_crystal_forearm_broken.glb",0.0,0,1],["wb_crystal_core_lod1.glb",1.0,0,0]]
	for i in states.size():
		var s=states[i]; var c=load("res://"+s[0]).instantiate(); c.position=Vector3(200+i*2.2,0,0); add_child(c)
		var cm=c.find_children("*","MeshInstance3D",true,false)[0]; var m=load("res://materials/wb_crystal_mat.tres").duplicate()
		m.set_shader_parameter("glow",s[1]); m.set_shader_parameter("hit_flash",s[2]); m.set_shader_parameter("broken",s[3]); cm.set_surface_override_material(0,m)
	# telegraph field at x=-300
	var o=Vector3(-300,0.05,0)
	for i in 3:
		var q=quad(40,mat("res://materials/wb_crack_radial_mat.tres"),o+Vector3(-45+i*45,0,0)); q.material_override.set_shader_parameter("progress",[0.3,0.7,1.0][i])
	var fl=quad(1,mat("res://materials/wb_crack_fissure_mat.tres"),o+Vector3(0,0,45)); fl.scale=Vector3(8,1,40); fl.material_override.set_shader_parameter("progress",0.75)
	for i in 4:
		var q=quad(14,mat("res://materials/wb_target_circle_mat.tres"),o+Vector3(-40+i*20,0.02,-40)); q.material_override.set_shader_parameter("progress",[0.1,0.4,0.7,0.95][i])
	var ring=MeshInstance3D.new(); var cy=CylinderMesh.new(); cy.top_radius=1; cy.bottom_radius=1; cy.height=1; cy.cap_top=false; cy.cap_bottom=false; cy.radial_segments=48; cy.rings=1; ring.mesh=cy
	ring.material_override=load("res://materials/wb_lava_ring_mat.tres").duplicate(); ring.material_override.set_shader_parameter("rise",0.6); ring.scale=Vector3(30,10,30); ring.position=Vector3(-300,5,-120); add_child(ring)
	var st=quad(1,mat("res://materials/wb_lava_strip_mat.tres"),Vector3(-300,0.06,-80)); st.scale=Vector3(70,1,6); st.material_override.set_shader_parameter("rise",0.7)
	for i in 3:
		var h=quad(8,mat("res://materials/wb_hand_glow_mat.tres"),Vector3(-330+i*12,6,-60)); h.material_override.set_shader_parameter("charge",[0.1,0.5,1.0][i])
	var fp=quad(25,mat("res://materials/wb_footprint_mat.tres"),Vector3(-260,0.04,-60))
	var dust=load("res://wb_dust_burst.tscn").instantiate(); dust.position=Vector3(-260,0,-60); add_child(dust); dust.emitting=true
	for i in 2:
		var f=load("res://wb_ash_fiend%s.glb"%["","_lod1"][i]).instantiate(); f.position=Vector3(400+i*3,0,0); add_child(f)
		var w=load("res://wb_ember_wisp%s.glb"%["","_lod1"][i]).instantiate(); w.position=Vector3(406+i*2.5,1.6,0); add_child(w)
	cam=Camera3D.new(); cam.fov=50; cam.far=3000; add_child(cam)
	shots=[[Vector3(10,12,30),Vector3(0,10,0),"front"],[Vector3(-12,14,-26),Vector3(0,11,0),"back"],[Vector3(9,9,8),Vector3(4.5,8.5,0.5),"forearm_L"],[Vector3(-1,7,10),Vector3(-2,6.3,2.4),"knees"],[Vector3(205.5,2.2,6),Vector3(205.5,0.6,0),"states"],[Vector3(-300,70,60),Vector3(-300,0,-10),"telegraph_cracks"],[Vector3(-300,40,-10),Vector3(-300,2,-90),"telegraph_ring"],[Vector3(-245,25,-25),Vector3(-268,2,-60),"footprint_glow"],[Vector3(404,2,7),Vector3(404,1.2,0),"adds"]]
	if ap.size()>0: pass
func _process(d):
	fr+=1
	if si>=shots.size(): get_tree().quit(); return
	var s=shots[si]; cam.position=s[0]; cam.look_at(s[1])
	if fr==14:
		get_viewport().get_texture().get_image().save_png("res://out/shot_%d_%s.png"%[si,s[2]]); si+=1; fr=0
