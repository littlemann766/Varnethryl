extends Node3D
# Equipment v1 fit / clip check renderer (Beth test harness, runs only in a /tmp copy).
# args after --: jobs json path
var jobs=[]; var attach={}; var gear_attach={}
func _ready():
	var args=OS.get_cmdline_user_args()
	jobs=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	attach=JSON.parse_string(FileAccess.get_file_as_string("res://equipment/fit/armor_attach.json"))["heroes"]
	gear_attach=JSON.parse_string(FileAccess.get_file_as_string("res://loot/gear/gear_attach.json"))["heroes"]
	var env=WorldEnvironment.new(); var e=Environment.new(); e.background_mode=Environment.BG_COLOR; e.background_color=Color(0.72,0.69,0.64)
	e.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color=Color(0.8,0.78,0.75); e.ambient_light_energy=0.9; env.environment=e; add_child(env)
	var sun=DirectionalLight3D.new(); sun.rotation_degrees=Vector3(-40,-35,0); sun.light_energy=2.2; add_child(sun)
	var cam=Camera3D.new(); cam.name="cam"; add_child(cam); cam.current=true
	await get_tree().process_frame
	for j in jobs: await run(j)
	get_tree().quit()
func xf(d):
	var q=d["rotation"]; var s=d["scale"]; var p=d["position"]
	var b=Basis(Quaternion(q[0],q[1],q[2],q[3]))*Basis.from_scale(Vector3(s[0],s[1],s[2]))
	return Transform3D(b,Vector3(p[0],p[1],p[2]))
func find_skel(n):
	if n is Skeleton3D: return n
	for c in n.get_children():
		var r=find_skel(c)
		if r: return r
	return null
func find_ap(n):
	if n is AnimationPlayer: return n
	for c in n.get_children():
		var r=find_ap(c)
		if r: return r
	return null
func attach_mesh(sk,bone,path,t):
	if not ResourceLoader.exists(path): push_warning("missing "+path); return
	var ba=BoneAttachment3D.new(); ba.bone_name=bone; sk.add_child(ba)
	var m=load(path).instantiate(); ba.add_child(m); m.transform=t
	for mi in m.find_children("*","MeshInstance3D",true,false):
		for si in mi.mesh.get_surface_count():
			var src=mi.mesh.surface_get_material(si); var mat=StandardMaterial3D.new(); mat.vertex_color_use_as_albedo=true; mat.roughness=0.75
			if src and src.resource_name.begins_with("vox_glow"):
				mat.emission_enabled=true; mat.emission_energy_multiplier=1.4; mat.emission_operator=BaseMaterial3D.EMISSION_OP_MULTIPLY; mat.emission=Color(1,1,1)
			mi.set_surface_override_material(si,mat)
func hide_verts(sk,rules):
	# collapse triangles whose vertices match a selector (dominant bone + rest model-space aabb / outside keep-sphere)
	for mi in sk.find_children("*","MeshInstance3D",true,false):
		if mi.get_parent() is BoneAttachment3D or mi.skin==null: continue
		var skin=mi.skin; var am=mi.mesh; var nm=ArrayMesh.new()
		for si in am.get_surface_count():
			var arr=am.surface_get_arrays(si); var V=arr[Mesh.ARRAY_VERTEX]; var Bn=arr[Mesh.ARRAY_BONES]; var W=arr[Mesh.ARRAY_WEIGHTS]; var I=arr[Mesh.ARRAY_INDEX]
			var nb=W.size()/V.size(); var hid=PackedByteArray(); hid.resize(V.size())
			for vi in V.size():
				var best=0
				var bw=-1.0
				for k in nb:
					if W[vi*nb+k]>bw: bw=W[vi*nb+k]; best=Bn[vi*nb+k]
				var bone_name=sk.get_bone_name(skin.get_bind_bone(best)) if skin.get_bind_bone(best)>=0 else String(skin.get_bind_name(best))
				var rp=sk.get_bone_global_rest(sk.find_bone(bone_name))*skin.get_bind_pose(best)*V[vi]
				for r in rules:
					if not (bone_name in r["bones"]): continue
					if r.has("sphere_keep"):
						var c=r["sphere_keep"]["center"]
						if rp.distance_to(Vector3(c[0],c[1],c[2]))>r["sphere_keep"]["radius"]: hid[vi]=1
					elif r["aabb"]==null: hid[vi]=1
					else:
						var a=r["aabb"]
						if rp.x>=a[0][0] and rp.y>=a[0][1] and rp.z>=a[0][2] and rp.x<=a[1][0] and rp.y<=a[1][1] and rp.z<=a[1][2]: hid[vi]=1
			var NI=PackedInt32Array()
			for t in range(0,I.size(),3):
				if hid[I[t]] or hid[I[t+1]] or hid[I[t+2]]: continue
				NI.append(I[t]); NI.append(I[t+1]); NI.append(I[t+2])
			arr[Mesh.ARRAY_INDEX]=NI
			nm.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arr,[],{},Mesh.ARRAY_FLAG_USE_8_BONE_WEIGHTS if nb==8 else 0)
			nm.surface_set_material(nm.get_surface_count()-1,am.surface_get_material(si))
		mi.mesh=nm
func run(j):
	var h=j["hero"]; var root=load("res://heroes/%s_voxel.glb"%h).instantiate(); add_child(root)
	var sk=find_skel(root); var ap=find_ap(root); var A=attach.get(h,{}); var fam=j["family"]; var r=j["rarity"]
	var rules=[]
	for slot in j["slots"]:
		var parts={"helmet":["helmet"],"chest":["chest"],"shoulders":["shoulder_L","shoulder_R"],"gloves":["glove_L","glove_R"],"legs":["leg_L","leg_R"],"boots":["boot_shin_L","boot_shin_R","boot_foot_L","boot_foot_R"],"belt":["belt"],"cloak":["cloak"]}[slot]
		for p in parts:
			var d=A["parts"][p]; var mp=d.get("mirror_of",p)
			attach_mesh(sk,d["bone"],"res://equipment/meshes/%s/%s_%s_%s.glb"%[fam,fam,r,mp],xf(d))
		if slot=="helmet": rules+=A["hide"]["helmet_full" if fam in ["plate"] else "helmet_open"]
		if slot=="cloak": rules+=A["hide"]["cloak"]
		if slot=="boots": rules+=A["hide"]["boots"]
	if j.get("weapon",""):
		rules+=A["hide"]["baked_weapon"]
		var g=gear_attach[h]["slots"]
		var wm=j.get("weapon_mesh","res://loot/gear/meshes/%s.glb"%j["weapon"])
		attach_mesh(sk,g["weapon"]["bone"],wm,xf(g["weapon"]))
		if j.get("weapon2","") and g.has("weapon_offhand"): attach_mesh(sk,g["weapon_offhand"]["bone"],j.get("weapon_mesh","res://loot/gear/meshes/%s.glb"%j["weapon2"]),xf(g["weapon_offhand"]))
		if j.get("shield","") and g.has("shield"): attach_mesh(sk,g["shield"]["bone"],"res://loot/gear/meshes/%s.glb"%j["shield"],xf(g["shield"]))
	for ex in j.get("extra",[]): attach_mesh(sk,ex["bone"],ex["mesh"],xf(ex))
	if j.get("hide",true) and rules.size(): hide_verts(sk,rules)
	var cam=get_node("cam"); var ab=AABB()
	for mi in root.find_children("*","MeshInstance3D",true,false):
		if mi.get_parent() is BoneAttachment3D: continue
		ab=ab.merge(mi.get_aabb()) if ab.size!=Vector3.ZERO else mi.get_aabb()
	var H=max(ab.end.y,1.0)+0.15
	for shot in j["shots"]:
		var clip=shot["clip"]
		if ap and clip!="rest":
			var nm=""
			for a in ap.get_animation_list():
				if a==clip or a.ends_with("/"+clip): nm=a
			if nm=="": continue
			ap.play(nm); ap.seek(ap.get_animation(nm).length*shot.get("t",0.5),true); ap.pause()
		var yaw=deg_to_rad(shot.get("yaw",30.0)); var dist=H*1.9
		cam.projection=Camera3D.PROJECTION_ORTHOGONAL; cam.size=shot.get("size",H*1.08)
		var cy=shot.get("cy",H*0.47)
		cam.position=Vector3(sin(yaw)*6,cy+0.9*shot.get("el",1.0),cos(yaw)*6); cam.look_at(Vector3(0,cy,0))
		await get_tree().process_frame; await get_tree().process_frame; await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(shot["out"])
	root.queue_free(); await get_tree().process_frame
