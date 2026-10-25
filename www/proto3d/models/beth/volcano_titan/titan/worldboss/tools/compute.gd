extends SceneTree
# Computes weak-point attach points (bone-local) and climb hulls from the Titan GLB rest pose.
const S=1.8654074668884277 # Darius_Rig scale: mesh units = skeleton units * S
func dirs(n):
	var out=[]; var ga=PI*(3.0-sqrt(5.0))
	for i in n:
		var y=1.0-2.0*(i+0.5)/n; var r=sqrt(1.0-y*y); out.append(Vector3(cos(ga*i)*r,y,sin(ga*i)*r))
	return out
func _init():
	var t=load("res://titan.glb").instantiate(); root.add_child(t)
	var sk:Skeleton3D=t.find_children("*","Skeleton3D",true,false)[0]
	var mi:MeshInstance3D=t.find_children("*","MeshInstance3D",true,false)[0]
	var a=mi.mesh.surface_get_arrays(0)
	var V:PackedVector3Array=a[Mesh.ARRAY_VERTEX]; var N:PackedVector3Array=a[Mesh.ARRAY_NORMAL]
	var J=a[Mesh.ARRAY_BONES]; var W=a[Mesh.ARRAY_WEIGHTS]
	var stride=J.size()/V.size()
	var skin=mi.skin
	# map skin bind -> skeleton bone index
	var bind2bone={}
	for b in skin.get_bind_count():
		var nm=skin.get_bind_name(b); bind2bone[b]= sk.find_bone(nm) if nm!="" else skin.get_bind_bone(b)
	var dom=PackedInt32Array(); dom.resize(V.size())
	for i in V.size():
		var best=-1.0; var bi=0
		for k in stride:
			if W[i*stride+k]>best: best=W[i*stride+k]; bi=J[i*stride+k]
		dom[i]=bind2bone.get(bi,bi)
	var P=[]  # skeleton-space positions
	for v in V: P.append(v/S)
	var pts={}
	var spec={
		"forearm_L":["foreArm_L","hand_L",0.45,Vector3(0.75,0.15,0.65),"forearm"],
		"forearm_R":["foreArm_R","hand_R",0.45,Vector3(-0.75,0.15,0.65),"forearm"],
		"knee_L":["shin_L","",0.0,Vector3(0.15,0.1,1.0),"knee"],
		"knee_R":["shin_R","",0.0,Vector3(-0.15,0.1,1.0),"knee"],
		"chest":["chest","",0.25,Vector3(0,0.15,1.0),"core"],
		"back":["upperChest","",-0.2,Vector3(0,0.25,-1.0),"core"]}
	var size={"forearm":1.5,"knee":1.9,"core":2.6} # metres on the native 21 m Titan; scales with the Titan node
	var out={"_note":"bone-local offsets in skeleton units (Skeleton3D under Darius_Rig). Instance the crystal under BoneAttachment3D(bone) -> Node3D with transform = Transform3D(Basis(rotation_quat).scaled(Vector3.ONE*scale), offset). +Y of the crystal points out of the skin. Values are scale-agnostic: they ride the Titan node's scale.","rig_scale":S,"points":{}}
	for k in spec:
		var s=spec[k]; var bi=sk.find_bone(s[0]); var g=sk.get_bone_global_rest(bi)
		var p0=g.origin
		if s[1]!="": p0=p0.lerp(sk.get_bone_global_rest(sk.find_bone(s[1])).origin,s[2])
		else: p0+=Vector3(0,s[2],0)
		var d=s[3].normalized(); var best=-1e9; var bp=p0; var nsum=Vector3()
		for i in P.size():
			var r=P[i]-p0; var along=r.dot(d); var perp=(r-d*along).length()
			if perp<0.22 and along>best and along<3.0: best=along; bp=P[i]
		for i in P.size():
			if P[i].distance_to(bp)<0.3: nsum+=N[i]
		var n=nsum.normalized() if nsum.length()>0.001 else d
		n=(n+d).normalized()
		var lp=g.affine_inverse()*(bp-n*0.06) # sink 6 cm (11 cm mesh) into skin
		var lb=g.basis.inverse()*Basis(Quaternion(Vector3.UP,n))
		var q=lb.get_rotation_quaternion()
		out.points[k]={"bone":s[0],"crystal":"wb_crystal_%s.glb"%s[4],"offset":[snapped(lp.x,0.0001),snapped(lp.y,0.0001),snapped(lp.z,0.0001)],"rotation_quat":[snapped(q.x,0.0001),snapped(q.y,0.0001),snapped(q.z,0.0001),snapped(q.w,0.0001)],"scale":snapped(size[s[4]]/S,0.0001),"surface_mesh_units":[bp.x*S,bp.y*S,bp.z*S]}
	var f=FileAccess.open("res://out/attach_points.json",FileAccess.WRITE); f.store_string(JSON.stringify(out,"  ")); f.close()
	# climb hulls
	var hulls={"spine_back":[["spine2","chest"],Vector3(0,0,-1)],"upper_back":[["upperChest"],Vector3(0,0,-1)],"shoulder_L":[["shoulder_L","upperArm_L"],Vector3(0,1,0)],"shoulder_R":[["shoulder_R","upperArm_R"],Vector3(0,1,0)]}
	var D=dirs(48); var hj={"_note":"ConvexPolygonShape3D .tres in bone-local skeleton units. Add BoneAttachment3D(bone) -> StaticBody3D/AnimatableBody3D (layer climbable) -> CollisionShape3D(shape). Scale-agnostic: ride the Titan scale.","hulls":{}}
	for h in hulls:
		var bones=hulls[h][0]; var side=hulls[h][1]; var g=sk.get_bone_global_rest(sk.find_bone(bones[0])); var ids=[]
		for b in bones: ids.append(sk.find_bone(b))
		var sel=[]
		var cen=Vector3(); var cnt=0
		for i in P.size():
			if dom[i] in ids: cen+=P[i]; cnt+=1
		cen/=max(cnt,1)
		for i in P.size():
			if dom[i] in ids and (P[i]-cen).dot(side)>-0.05: sel.append(P[i])
		var hp=PackedVector3Array()
		for dd in D:
			var bb=-1e9; var bq=Vector3()
			for p in sel:
				var v=p.dot(dd)
				if v>bb: bb=v; bq=p
			var lq=g.affine_inverse()*bq
			if not hp.has(lq): hp.append(lq)
		var sh=ConvexPolygonShape3D.new(); sh.points=hp; sh.margin=0.02
		ResourceSaver.save(sh,"res://out/wb_climb_%s.tres"%h)
		hj.hulls[h]={"bone":bones[0],"shape":"wb_climb_%s.tres"%h,"points":hp.size(),"src_verts":sel.size()}
	f=FileAccess.open("res://out/climb_hulls.json",FileAccess.WRITE); f.store_string(JSON.stringify(hj,"  ")); f.close()
	print(JSON.stringify(out.points)); print(JSON.stringify(hj.hulls)); quit()
