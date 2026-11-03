extends Node3D
# Generic shared armour test harness (Beth; /tmp only). args: jobs json
const HIDE={
 "helm":{"bones":["head","neck","jaw","eye_L","eye_R"],"prefix":["hair"],"above_neck":true},
 "chest":{"bones":["spine","spine2","chest","upperChest","shoulder_L","shoulder_R"],"hips_above":true,"coat_above":true},
 "shoulder_L":{"bones":["upperArm_L"]},"shoulder_R":{"bones":["upperArm_R"]},
 "glove_L":{"bones":["foreArm_L","hand_L","fingers_L"],"suffix_hand":"_L"},"glove_R":{"bones":["foreArm_R","hand_R","fingers_R"],"suffix_hand":"_R"},
 "leg_L":{"bones":["thigh_L","coat_L","coat2_L"],"hips_below":1.0},"leg_R":{"bones":["thigh_R","coat_R","coat2_R"],"hips_below":-1.0},
 "boot_L":{"bones":["shin_L","foot_L","toe_L","coat3_L"]},"boot_R":{"bones":["shin_R","foot_R","toe_R","coat3_R"]}}
var ref_head=null
func _ready():
	var args=OS.get_cmdline_user_args(); var jobs=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var env=WorldEnvironment.new(); var e=Environment.new()
	var sky=Sky.new(); var sm=ProceduralSkyMaterial.new(); sm.sky_top_color=Color(0.22,0.45,0.85); sm.sky_horizon_color=Color(0.66,0.70,0.76); sm.ground_horizon_color=Color(0.55,0.52,0.48); sm.ground_bottom_color=Color(0.3,0.28,0.25); sky.sky_material=sm
	e.background_mode=Environment.BG_COLOR; e.background_color=Color(0.70,0.72,0.75); e.sky=sky
	e.ambient_light_source=Environment.AMBIENT_SOURCE_SKY; e.ambient_light_color=Color(0.75,0.68,0.58); e.ambient_light_sky_contribution=0.55; e.ambient_light_energy=1.0
	e.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	e.tonemap_mode=Environment.TONE_MAPPER_ACES; e.tonemap_exposure=1.0; e.tonemap_white=6.0; env.environment=e; add_child(env)
	var sun=DirectionalLight3D.new(); sun.rotation_degrees=Vector3(-45,-30,0); sun.light_energy=1.4; sun.light_color=Color(1.0,0.96,0.9); sun.shadow_enabled=true; add_child(sun)
	var cam=Camera3D.new(); cam.name="cam"; add_child(cam); cam.current=true
	await get_tree().process_frame
	for j in jobs: await run(j)
	get_tree().quit()
func find_t(n,cls):
	if n.is_class(cls): return n
	for c in n.get_children():
		var r=find_t(c,cls)
		if r: return r
	return null
func bodies(sk):
	var out=[]
	for mi in sk.find_children("*","MeshInstance3D",true,false):
		if mi.skin and not mi.has_meta("armor"): out.append(mi)
	return out
func vert_info(sk,mi,cb):
	# calls cb(si, arr, vi, bone_name, rest_pos)
	pass
func head_stats(sk):
	var hb=sk.get_bone_global_rest(sk.find_bone("head")).origin; var s=Vector3(); var n=0; var top=-1e9
	for mi in bodies(sk):
		var am=mi.mesh; var skin=mi.skin
		for si in am.get_surface_count():
			var arr=am.surface_get_arrays(si); var V=arr[Mesh.ARRAY_VERTEX]; var Bn=arr[Mesh.ARRAY_BONES]; var W=arr[Mesh.ARRAY_WEIGHTS]; var nb=W.size()/V.size()
			for vi in range(0,V.size(),3):
				var best=0; var bw=-1.0
				for k in nb:
					if W[vi*nb+k]>bw: bw=W[vi*nb+k]; best=Bn[vi*nb+k]
				var bone=skin.get_bind_bone(best)
				if bone<0: bone=sk.find_bone(String(skin.get_bind_name(best)))
				if sk.get_bone_name(bone)!="head": continue
				var rp=sk.get_bone_global_rest(bone)*skin.get_bind_pose(best)*V[vi]
				s+=rp; n+=1; top=max(top,rp.y)
	var c=s/max(n,1)
	return {"dx":c.x-hb.x,"dz":c.z-hb.z,"top":top-hb.y}
func hide_body(sk,pieces):
	var bones={}; var pre=[]; var hips_above=false; var coat_above=false; var hips_below=[]; var above_neck=false; var hand_sfx=[]
	for p in pieces:
		var r=HIDE[p]
		for b in r["bones"]: bones[b]=true
		pre+=r.get("prefix",[]); hips_above=hips_above or r.get("hips_above",false); coat_above=coat_above or r.get("coat_above",false); above_neck=above_neck or r.get("above_neck",false)
		if r.has("hips_below"): hips_below.append(r["hips_below"])
		if r.has("suffix_hand"): hand_sfx.append(r["suffix_hand"])
	var hipy=sk.get_bone_global_rest(sk.find_bone("hips")).origin.y; var cut=hipy-0.20
	var neck=sk.get_bone_global_rest(sk.find_bone("neck")).origin; var head=sk.get_bone_global_rest(sk.find_bone("head")).origin
	for mi in bodies(sk):
		var skin=mi.skin; var am=mi.mesh; var nm=ArrayMesh.new()
		for si in am.get_surface_count():
			var arr=am.surface_get_arrays(si); var V=arr[Mesh.ARRAY_VERTEX]; var Bn=arr[Mesh.ARRAY_BONES]; var W=arr[Mesh.ARRAY_WEIGHTS]; var I=arr[Mesh.ARRAY_INDEX]
			var nb=W.size()/V.size(); var hid=PackedByteArray(); hid.resize(V.size())
			for vi in V.size():
				var best=0; var bw=-1.0
				for k in nb:
					if W[vi*nb+k]>bw: bw=W[vi*nb+k]; best=Bn[vi*nb+k]
				var bone=skin.get_bind_bone(best)
				if bone<0: bone=sk.find_bone(String(skin.get_bind_name(best)))
				var bn=sk.get_bone_name(bone); var rp=sk.get_bone_global_rest(bone)*skin.get_bind_pose(best)*V[vi]
				var h=bones.has(bn)
				for q in pre: h=h or bn.begins_with(q)
				for sfx in hand_sfx:
					if bn.ends_with(sfx) and (bn.begins_with("index") or bn.begins_with("middle") or bn.begins_with("ring") or bn.begins_with("pinky") or bn.begins_with("thumb")): h=true
				if bn=="hips":
					if hips_above and rp.y>cut: h=true
					for sg in hips_below:
						if rp.y<=cut and rp.x*sg>=0: h=true
				if coat_above and bn.begins_with("coat") and rp.y>cut: h=true
				if above_neck and rp.y>neck.y+0.02 and Vector2(rp.x-head.x,rp.z-head.z).length()<0.24 and not bn.begins_with("cape"): h=true
				if h: hid[vi]=1
			var NI=PackedInt32Array()
			for t in range(0,I.size(),3):
				if int(hid[I[t]])+int(hid[I[t+1]])+int(hid[I[t+2]])>=1: continue
				NI.append(I[t]); NI.append(I[t+1]); NI.append(I[t+2])
			arr[Mesh.ARRAY_INDEX]=NI
			if NI.size()==0: continue
			nm.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arr,[],{},Mesh.ARRAY_FLAG_USE_8_BONE_WEIGHTS if nb==8 else 0)
			nm.surface_set_material(nm.get_surface_count()-1,am.surface_get_material(si))
		mi.mesh=nm
func canon(n): return n.substr(0,n.length()-2) if n.ends_with("_2") else n
const FB={"upperChest":"chest","spine2":"spine","coat_L":"thigh_L","coat_R":"thigh_R","coat2_L":"thigh_L","coat2_R":"thigh_R","coat3_L":"shin_L","coat3_R":"shin_R","toe_L":"foot_L","toe_R":"foot_R","fingers_L":"hand_L","fingers_R":"hand_R","shoulder_L":"chest","shoulder_R":"chest","chest":"spine","neck":"chest","jaw":"head","eye_L":"head","eye_R":"head"}
func fallback(sk,bn):
	while sk.find_bone(bn)<0:
		if FB.has(bn): bn=FB[bn]
		elif bn.ends_with("_L") or bn.ends_with("_R"): bn="hand"+bn.right(2) if not bn.begins_with("hair") else "head"
		else: bn="hips"
	return bn
func attach(sk,path,off):
	var inst=load(path).instantiate(); var src=find_t(inst,"Skeleton3D")
	for mi in inst.find_children("*","MeshInstance3D",true,false):
		var os=mi.skin; var ns=Skin.new(); var BP={}
		for b in os.get_bind_count():
			var bn=String(os.get_bind_name(b))
			if bn=="" and src: bn=src.get_bone_name(os.get_bind_bone(b))
			BP[canon(bn)]=os.get_bind_pose(b)
		for b in os.get_bind_count():
			var bn=String(os.get_bind_name(b))
			if bn=="" and src: bn=src.get_bone_name(os.get_bind_bone(b))
			var cn=canon(bn); var tn=fallback(sk,cn)
			ns.add_named_bind(tn,Transform3D(Basis(),off)*BP.get(tn,os.get_bind_pose(b)))   # substitute bone: bind against the reference rig's copy of it
		mi.get_parent().remove_child(mi); mi.skin=ns; mi.set_meta("armor",true); mi.name="armor_"+path.get_file().get_basename(); sk.add_child(mi); mi.skeleton=NodePath("..")
		for si in mi.mesh.get_surface_count():
			var mat=StandardMaterial3D.new(); mat.vertex_color_use_as_albedo=true; mat.vertex_color_is_srgb=true; mat.metallic=0.2; mat.roughness=0.5; mat.metallic_specular=0.4
			mi.set_surface_override_material(si,mat)
	inst.free()
const GRP={"helm":["head"],"chest":["spine","spine2","chest","upperChest"],"shoulder_L":["upperArm_L"],"shoulder_R":["upperArm_R"],"glove_L":["foreArm_L"],"glove_R":["foreArm_R"],"leg_L":["thigh_L"],"leg_R":["thigh_R"],"boot_L":["shin_L"],"boot_R":["shin_R"]}
var REFS=null
func group_stats(sk):
	# per piece: mean body position of its group's dominant verts, relative to the group's first bone (rest)
	var acc={}; var bone_of={}
	for p in GRP:
		acc[p]=[Vector3(),0,-1e9]
		for b in GRP[p]: bone_of[b]=p
	for mi in bodies(sk):
		var am=mi.mesh; var skin=mi.skin
		for si in am.get_surface_count():
			var arr=am.surface_get_arrays(si); var V=arr[Mesh.ARRAY_VERTEX]; var Bn=arr[Mesh.ARRAY_BONES]; var W=arr[Mesh.ARRAY_WEIGHTS]; var nb=W.size()/V.size()
			for vi in range(0,V.size(),2):
				var best=0; var bw=-1.0
				for k in nb:
					if W[vi*nb+k]>bw: bw=W[vi*nb+k]; best=Bn[vi*nb+k]
				var bone=skin.get_bind_bone(best)
				if bone<0: bone=sk.find_bone(String(skin.get_bind_name(best)))
				var bn=sk.get_bone_name(bone)
				if not bone_of.has(bn): continue
				var p=bone_of[bn]; var rp=sk.get_bone_global_rest(bone)*skin.get_bind_pose(best)*V[vi]
				var r0=sk.get_bone_global_rest(sk.find_bone(GRP[p][0])).origin
				acc[p][0]+=rp-r0; acc[p][1]+=1; acc[p][2]=max(acc[p][2],rp.y-r0.y)
	var out={}
	for p in acc: out[p]={"c":acc[p][0]/max(acc[p][1],1),"top":acc[p][2]}
	return out
func run(j):
	var root=load(j["rig"]).instantiate(); add_child(root); var sk=find_t(root,"Skeleton3D"); var ap=find_t(root,"AnimationPlayer")
	var st=group_stats(sk)
	if REFS==null: REFS=st   # first job = reference male rig (Darius)
	var pieces=j.get("pieces",[]); var offs={}
	for p in GRP:
		var d=st[p]["c"]-REFS[p]["c"]; var o=Vector3(0,0,clamp(d.z,-0.2,0.2))
		if p=="helm": o=Vector3(clamp(d.x,-0.05,0.05),clamp(st[p]["top"]-REFS[p]["top"],-0.08,0.08),clamp(d.z,-0.2,0.2))
		offs[p]=o
	var zs=[]
	for p in ["chest","shoulder_L","shoulder_R","leg_L","leg_R","boot_L","boot_R"]: zs.append(offs[p].z)
	zs.sort(); var zm=(zs[3])
	for p in offs: offs[p]=Vector3(0,offs[p].y,zm) if p!="helm" else Vector3(0,offs[p].y,offs[p].z)   # one shared depth shift per hero (skeleton sits behind the modelled body on some rigs)
	print("OFFS ",j["rig"]," ",offs)
	for p in pieces: attach(sk,"res://armor/generic_male_plate_%s.glb"%p,offs[p])
	if pieces.size(): hide_body(sk,pieces)
	var cam=get_node("cam")
	for shot in j["shots"]:
		var clip=shot.get("clip","rest")
		if ap:
			if clip=="rest": ap.stop(); sk.reset_bone_poses()
			else:
				var nm=""
				for a in ap.get_animation_list():
					if a==clip or a.ends_with("/"+clip): nm=a
				if nm!="": ap.play(nm); ap.seek(ap.get_animation(nm).length*shot.get("t",0.5),true); ap.pause()
		var yaw=deg_to_rad(shot.get("yaw",0.0)); cam.projection=Camera3D.PROJECTION_ORTHOGONAL
		var tgt=Vector3(0,shot.get("cy",0.98),0); cam.size=shot.get("size",2.15)
		if shot.has("bone"): tgt=sk.global_transform*sk.get_bone_global_pose(sk.find_bone(shot["bone"])).origin+Vector3(0,shot.get("up",0.0),0)
		cam.position=tgt+Vector3(sin(yaw)*6,shot.get("el",0.9),cos(yaw)*6); cam.look_at(tgt)
		await get_tree().process_frame; await get_tree().process_frame; await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(shot["out"])
	root.queue_free(); await get_tree().process_frame
