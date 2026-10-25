class_name CharacterRig
extends Node3D
## Loads a rigged GLB, scales it to an exact height (fit to measured mesh height, like charscale fitMeasuredHeight)
## and drives it with an AnimationTree: locomotion blendspace (idle/walk/run) + attack and hit one-shots + death.
## Missing clips fall back (run->walk sped up; no attack/hit -> procedural lunge/flinch).

signal anim_event(name: String)

var model: Node3D
var anim_player: AnimationPlayer
var tree: AnimationTree
var clips: PackedStringArray = []
var target_height := 1.905
var measured_height := 0.0
var applied_scale := 1.0
var has_attack := false
var has_hit := false
var _lunge := 0.0
var _flinch := 0.0
var _atk_i := 0

const LOOPS := ["idle", "walk", "run", "trot", "hover", "fly", "glide"]

## height_m <= 0 means "load at scale 1" (Beth's baked-size boss).
func setup(path: String, height_m: float) -> CharacterRig:
	var ps: PackedScene = load(path)
	model = ps.instantiate()
	add_child(model)
	model.rotation.y = PI    # glTF faces +Z; the game's visual node faces -Z
	measured_height = measure(model, path)
	if path.begins_with("res://characters/"): height_m = 0.0   # Beth's size is baked on the armature root: never rescale
	if height_m > 0.0 and measured_height > 0.01:
		applied_scale = height_m / measured_height
		target_height = height_m
	else:
		target_height = measured_height
	model.scale = Vector3.ONE * applied_scale
	anim_player = _find_player(model)
	if anim_player:
		_alias_clips(path)
		if path.begins_with("res://characters/"): _strip_root_scale()
		_add_cloth()
		_build_tree()
	return self

static var _index = null
static func index() -> Dictionary:
	if _index == null:
		_index = JSON.parse_string(FileAccess.get_file_as_string("res://characters/index.json")) if FileAccess.file_exists("res://characters/index.json") else {"characters": {}}
	return _index

static func char_path(id: String) -> String:
	var c = index().characters.get(id)
	return "res://characters/" + str(c.file) if c else ""

## index.json renamed_from_source maps new clip -> source clip (attack1 <- attack). Game code and sidecars
## (volcano attackEvents, cloth) use SOURCE names, so register each renamed clip under its source name too.
## Beth re-baked every size onto the armature root (2026-10-25): a leftover root-bone scale key in a clip
## (the volcano Titan's idle had x1.84) would double it, so drop root scale tracks.
func _strip_root_scale() -> void:
	for an in anim_player.get_animation_list():
		var a := anim_player.get_animation(an)
		for t in range(a.get_track_count() - 1, -1, -1):
			if a.track_get_type(t) == Animation.TYPE_SCALE_3D and str(a.track_get_path(t)).ends_with(":root"): a.remove_track(t)

func _alias_clips(path: String) -> void:
	var fname := path.get_file()
	for id in index().characters:
		var c: Dictionary = index().characters[id]
		if c.file != fname: continue
		var lib: AnimationLibrary = anim_player.get_animation_library("")
		if lib == null: return
		for nw in c.renamed_from_source:
			var src: String = c.renamed_from_source[nw]
			if lib.has_animation(nw) and not lib.has_animation(src): lib.add_animation(src, lib.get_animation(nw))
		if not lib.has_animation("attack") and lib.has_animation("attack1"): lib.add_animation("attack", lib.get_animation("attack1"))
		return

static var _measure_cache := {}
## Height of the SKINNED mesh in rest pose (CPU skinning of every vertex), so scale baked on bones
## (e.g. Beth's volcano titan) is included. Cached per scene path.
static func measure(n: Node, key := "") -> float:
	if key != "" and _measure_cache.has(key): return _measure_cache[key]
	var lo := INF; var hi := -INF
	for mi: MeshInstance3D in _meshes(n, []):
		var xf := _rel_xf(n, mi)
		var sk: Skeleton3D = mi.get_node_or_null(mi.skeleton) as Skeleton3D
		var skin: Skin = mi.skin
		var mats := []
		if sk and skin:
			var skxf := _rel_xf(n, sk)
			for b in skin.get_bind_count():
				var bi := skin.get_bind_bone(b)
				if bi < 0: bi = sk.find_bone(skin.get_bind_name(b))
				mats.append(skxf * sk.get_bone_global_rest(bi) * skin.get_bind_pose(b))
		for si in mi.mesh.get_surface_count():
			var arr: Array = mi.mesh.surface_get_arrays(si)
			var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			if mats.is_empty() or arr[Mesh.ARRAY_BONES] == null:
				for v in vs:
					var y := (xf * v).y; lo = min(lo, y); hi = max(hi, y)
				continue
			var bones = arr[Mesh.ARRAY_BONES]; var w: PackedFloat32Array = arr[Mesh.ARRAY_WEIGHTS]
			var k: int = bones.size() / vs.size()
			for i in vs.size():
				var p := Vector3.ZERO
				for j in k:
					var ww := w[i * k + j]
					if ww > 0.0: p += (mats[bones[i * k + j]] * vs[i]) * ww
				lo = min(lo, p.y); hi = max(hi, p.y)
	var h := hi - lo if hi > lo else 0.0
	if key != "": _measure_cache[key] = h
	return h

static func _rel_xf(root: Node, n: Node3D) -> Transform3D:
	var t := Transform3D.IDENTITY
	var c: Node = n
	while c and c != root:
		if c is Node3D: t = (c as Node3D).transform * t
		c = c.get_parent()
	return t

static func _meshes(n: Node, out: Array) -> Array:
	if n is MeshInstance3D and (n as MeshInstance3D).mesh: out.append(n)
	for c in n.get_children(): _meshes(c, out)
	return out

func _find_player(n: Node) -> AnimationPlayer:
	if n is AnimationPlayer: return n
	for c in n.get_children():
		var p := _find_player(c)
		if p: return p
	return null

func _clip(names: Array) -> String:
	for nm in names:
		if clips.has(nm): return nm
	return ""

func _build_tree() -> void:
	clips = anim_player.get_animation_list()
	for c in clips:
		var a := anim_player.get_animation(c)
		a.loop_mode = Animation.LOOP_LINEAR if LOOPS.has(c) else Animation.LOOP_NONE
	has_attack = clips.has("attack")
	has_hit = clips.has("hit")
	var bt := AnimationNodeBlendTree.new()
	var loco := AnimationNodeBlendSpace1D.new()
	loco.min_space = 0.0; loco.max_space = 2.0
	var idle := _clip(["idle", "hover"]); var walk := _clip(["walk", "trot", "idle"]); var run := _clip(["run", "fly", "trot", "walk"])
	for pt in [[idle, 0.0], [walk, 1.0], [run, 2.0]]:
		var an := AnimationNodeAnimation.new(); an.animation = pt[0]; loco.add_blend_point(an, pt[1], -1, "p%d" % int(pt[1]))
	bt.add_node("loco", loco)
	var atk_anim := AnimationNodeAnimation.new(); atk_anim.animation = _clip(["attack", "idle"])
	bt.add_node("atk_anim", atk_anim)
	var ts := AnimationNodeTimeScale.new(); bt.add_node("atk_speed", ts)
	var atk := AnimationNodeOneShot.new(); atk.fadein_time = 0.05; atk.fadeout_time = 0.12; atk.filter_enabled = false
	bt.add_node("attack", atk)
	var hit_anim := AnimationNodeAnimation.new(); hit_anim.animation = _clip(["hit", "idle"])
	bt.add_node("hit_anim", hit_anim)
	var hit := AnimationNodeOneShot.new(); hit.fadein_time = 0.04; hit.fadeout_time = 0.1
	bt.add_node("hit", hit)
	var death_anim := AnimationNodeAnimation.new(); death_anim.animation = _clip(["death", "idle"])
	bt.add_node("death_anim", death_anim)
	var dead := AnimationNodeBlend2.new(); bt.add_node("dead", dead)
	bt.connect_node("atk_speed", 0, "atk_anim")
	bt.connect_node("attack", 0, "loco"); bt.connect_node("attack", 1, "atk_speed")
	bt.connect_node("hit", 0, "attack"); bt.connect_node("hit", 1, "hit_anim")
	bt.connect_node("dead", 0, "hit"); bt.connect_node("dead", 1, "death_anim")
	bt.connect_node("output", 0, "dead")
	tree = AnimationTree.new()
	tree.tree_root = bt
	add_child(tree)
	tree.anim_player = tree.get_path_to(anim_player)
	tree.root_node = tree.get_path_to(model)
	tree.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_IDLE
	tree.active = true
	tree.set("parameters/atk_speed/scale", 1.6)

## speed_ratio: 0 idle, 1 walk, 2 run
func set_locomotion(speed_ratio: float) -> void:
	if tree: tree.set("parameters/loco/blend_position", clamp(speed_ratio, 0.0, 2.0))

## Fast, spammable: re-firing restarts the one-shot (no timing window). clip: optional explicit clip name.
func play_attack(clip := "", speed := 1.6) -> void:
	_lunge = 0.18
	if not tree or not has_attack: return
	var nm := clip
	if nm == "" or not clips.has(nm):
		_atk_i += 1
		nm = "attack2" if (_atk_i % 2 == 0 and clips.has("attack2")) else "attack"
	(tree.tree_root as AnimationNodeBlendTree).get_node("atk_anim").animation = nm
	tree.set("parameters/atk_speed/scale", speed)
	tree.set("parameters/attack/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)

func play_hit() -> void:
	_flinch = 0.15
	if tree and has_hit: tree.set("parameters/hit/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)

func set_dead(d: bool) -> void:
	if tree: tree.set("parameters/dead/blend_amount", 1.0 if d else 0.0)

func set_active(on: bool) -> void:
	if tree: tree.active = on

func clip_length(nm: String) -> float:
	return anim_player.get_animation(nm).length if anim_player and clips.has(nm) else 0.0

func _process(dt: float) -> void:
	# procedural fallback for clips a model doesn't have (Selene / Asha have no attack or hit clips)
	if _lunge > 0.0 or _flinch > 0.0:
		_lunge = max(0.0, _lunge - dt); _flinch = max(0.0, _flinch - dt)
		var z := 0.0
		if not has_attack: z -= sin(_lunge / 0.18 * PI) * 0.25 * target_height / 1.905
		if not has_hit: z += sin(_flinch / 0.15 * PI) * 0.12 * target_height / 1.905
		model.position.z = z


## Test 7: real cape. Bone chains named cape, cape2.. / hood, hood2.. (Beth's cloth sidecar groups) are driven by a
## SpringBoneSimulator3D instead of baked clip keys: the baked cape keys are what twisted and flared the cape, so
## they are stripped and the chain hangs from its straight rest pose, swaying and trailing with movement.
## Cost: 5+3 joints and 5 capsule colliders per caped character, all native code. Cheap on mobile.
const CLOTH := {"cape": {"stiffness": 0.9, "drag": 0.55, "gravity": 2.2, "radius": 0.035},
	"hood": {"stiffness": 2.0, "drag": 0.6, "gravity": 0.8, "radius": 0.03}}
var cloth: SpringBoneSimulator3D

func _add_cloth() -> void:
	var sk: Skeleton3D = null
	for c in model.find_children("*", "Skeleton3D", true, false): sk = c; break
	if sk == null: return
	var chains := []
	for g in CLOTH:
		if sk.find_bone(g) < 0: continue
		var last: String = g; var i := 2
		while sk.find_bone("%s%d" % [g, i]) >= 0: last = "%s%d" % [g, i]; i += 1
		chains.append([g, last])
	if chains.is_empty(): return
	# strip baked keys on the chain bones so the simulation starts from the straight rest pose
	var names := {}
	for ch in chains:
		var b := sk.find_bone(ch[1])
		while b >= 0:
			names[sk.get_bone_name(b)] = true
			if sk.get_bone_name(b) == ch[0]: break
			b = sk.get_bone_parent(b)
	for an in anim_player.get_animation_list():
		var a := anim_player.get_animation(an)
		for t in range(a.get_track_count() - 1, -1, -1):
			var tp := str(a.track_get_path(t))
			if names.has(tp.get_slice(":", 1)): a.remove_track(t)
	_fix_chain_rest(sk, names)
	for bn in names: sk.reset_bone_pose(sk.find_bone(bn))
	if chains[0][0] == "cape": _reshape_cape(sk)
	cloth = SpringBoneSimulator3D.new(); cloth.name = "Cloth"; sk.add_child(cloth)
	cloth.set_setting_count(chains.size())
	for i in chains.size():
		var P: Dictionary = CLOTH[chains[i][0]]
		cloth.set_root_bone_name(i, chains[i][0]); cloth.set_end_bone_name(i, chains[i][1])
		cloth.set_extend_end_bone(i, true); cloth.set_end_bone_length(i, 0.22)
		cloth.set_end_bone_direction(i, SpringBoneSimulator3D.BONE_DIRECTION_FROM_PARENT)
		cloth.set_stiffness(i, P.stiffness); cloth.set_drag(i, P.drag); cloth.set_gravity(i, P.gravity)
		cloth.set_gravity_direction(i, Vector3.DOWN); cloth.set_radius(i, P.radius)
		cloth.set_enable_all_child_collisions(i, true)
	# body colliders (from the cloth sidecar's capsule list): torso + legs, so the cape never sinks into the body
	for c in [["hips", 0.17, 0.75, Vector3(0, 0.3, 0)], ["thigh_L", 0.11, 0.5, Vector3(0, 0.22, 0)], ["thigh_R", 0.11, 0.5, Vector3(0, 0.22, 0)],
			["shin_L", 0.08, 0.45, Vector3(0, 0.2, 0)], ["shin_R", 0.08, 0.45, Vector3(0, 0.2, 0)]]:
		if sk.find_bone(c[0]) < 0: continue
		var col := SpringBoneCollisionCapsule3D.new(); col.bone_name = c[0]
		col.radius = c[1]; col.height = c[2]; col.position_offset = c[3]
		cloth.add_child(col)


## Beth's export leaves the cape/hood bone rests at identity (only the clips placed them). Rebuild each chain
## bone's rest from the skin's inverse bind poses so the stripped chain hangs where the mesh was bound.
func _fix_chain_rest(sk: Skeleton3D, names: Dictionary) -> void:
	var bind := {}
	for mi: MeshInstance3D in _meshes(model, []):
		if mi.skin == null: continue
		for i in mi.skin.get_bind_count():
			var bn := mi.skin.get_bind_name(i)
			if bn == "" and mi.skin.get_bind_bone(i) >= 0: bn = sk.get_bone_name(mi.skin.get_bind_bone(i))
			if not bind.has(bn): bind[bn] = mi.skin.get_bind_pose(i).affine_inverse()
	var order := names.keys(); order.sort_custom(func(x, y): return sk.find_bone(x) < sk.find_bone(y))
	for bn in order:
		if not bind.has(bn): continue
		var b := sk.find_bone(bn); var p := sk.get_bone_parent(b)
		var pg: Transform3D = (bind[sk.get_bone_name(p)] if bind.has(sk.get_bone_name(p)) else sk.get_bone_global_rest(p)) if p >= 0 else Transform3D()
		sk.set_bone_rest(b, pg.affine_inverse() * bind[bn])


## The source cape mesh is a wide stiff bell (flares to ~3x shoulder width, down to the ground). Reshape it once
## per mesh (cached): vertices skinned to the cape chain are pulled into a flat, shoulder-width sheet that hangs
## just behind the chain bones and ends at calf height. The spring chain then gives it sway/trail.
const CAPE_HALF_W := 0.25      # m, half shoulder width at the hem (0.19 at the collar)
const CAPE_HEM_Y := 0.40       # m, calf
static var _cape_cache := {}

func _reshape_cape(sk: Skeleton3D) -> void:
	for mi: MeshInstance3D in _meshes(model, []):
		if mi.skin == null or mi.mesh == null: continue
		if _cape_cache.has(mi.mesh.resource_path) and mi.mesh.resource_path != "":
			mi.mesh = _cape_cache[mi.mesh.resource_path]; continue
		# skin bind index -> is cape bone, and the cape chain's z at each height (rest, skeleton space)
		var is_cape := {}
		for b in mi.skin.get_bind_count():
			var bn := mi.skin.get_bind_name(b)
			if bn == "" and mi.skin.get_bind_bone(b) >= 0: bn = sk.get_bone_name(mi.skin.get_bind_bone(b))
			if bn.begins_with("cape"): is_cape[b] = true
		if is_cape.is_empty(): continue
		var top: Vector3 = sk.get_bone_global_rest(sk.find_bone("cape")).origin
		var am := ArrayMesh.new()
		var changed := 0
		for si in mi.mesh.get_surface_count():
			var arr: Array = mi.mesh.surface_get_arrays(si)
			var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var bones = arr[Mesh.ARRAY_BONES]; var w: PackedFloat32Array = arr[Mesh.ARRAY_WEIGHTS]
			var nrm: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
			if bones != null and vs.size() > 0:
				var k: int = bones.size() / vs.size()
				# cape extent (only verts mostly on the cape)
				var lo := INF; var maxw := 0.0
				var cw := PackedFloat32Array(); cw.resize(vs.size())
				for i in vs.size():
					var s := 0.0
					for j in k: if is_cape.has(bones[i * k + j]): s += w[i * k + j]
					cw[i] = s
					if s > 0.5: lo = minf(lo, vs[i].y); maxw = maxf(maxw, absf(vs[i].x))
				# back profile of the body (incl. the fox tail) under the cape: min z per 5 cm height band
				var prof := {}
				for i in vs.size():
					if cw[i] < 0.05 and absf(vs[i].x) < 0.24 and vs[i].y > 0.3:
						var bi := int(vs[i].y / 0.05); prof[bi] = minf(prof.get(bi, 0.0), vs[i].z)
				if lo < INF:
					var span := maxf(top.y - lo, 0.01)
					for i in vs.size():
						if cw[i] <= 0.0: continue
						var v := vs[i]
						var t := clampf((top.y - v.y) / span, 0.0, 1.0)            # 0 collar .. 1 hem
						var ny := top.y - t * (top.y - CAPE_HEM_Y)                   # shorten to calf
						var half := lerpf(0.19, CAPE_HALF_W, t)
						var nx := v.x / maxf(maxw, 0.01) * half * 1.0 if absf(v.x) > 0.0 else 0.0
						nx = clampf(v.x * half / maxf(maxw * lerpf(0.5, 1.0, t), 0.01), -half, half)
						var back := top.z - 0.03 - 0.02 * t                          # sheet just behind the chain
						var nz := back + 0.025 * pow(absf(nx) / half, 2.0)          # slight wrap at the edges
						# drape over the fox tail (rigid, sticks out to z=-0.33 around y=0.76): bulge back below the hips
						var bb := int(ny / 0.05); var pz := 0.0
						for d in range(-2, 3): pz = minf(pz, prof.get(bb + d, 0.0))
						pz = minf(pz, lerpf(0.0, -0.46, smoothstep(1.1, 0.85, ny)))   # the animated fox tail swings out to ~-0.35: drape over it
						nz = minf(nz, pz - 0.035 + 0.025 * pow(absf(nx) / half, 2.0))   # always outside body/tail
						var tgt := Vector3(nx, ny, nz)
						vs[i] = v.lerp(tgt, clampf(cw[i] * 1.25, 0.0, 1.0) if t > 0.08 else cw[i] * 0.5)
						if nrm.size() == vs.size():
							var outward := Vector3(0, 0, -1) if nrm[i].z <= 0.0 else Vector3(0, 0, 1)
							nrm[i] = nrm[i].lerp(outward, cw[i]).normalized()
						changed += 1
				arr[Mesh.ARRAY_VERTEX] = vs; arr[Mesh.ARRAY_NORMAL] = nrm
				arr[Mesh.ARRAY_TANGENT] = null
			var fmt: int = mi.mesh.surface_get_format(si)
			am.add_surface_from_arrays(mi.mesh.surface_get_primitive_type(si), arr, [], {}, (fmt & ~Mesh.ARRAY_FORMAT_TANGENT) & ~Mesh.ARRAY_FLAG_COMPRESS_ATTRIBUTES)
			var mat: Material = mi.mesh.surface_get_material(si)
			if mat is BaseMaterial3D:  # the flattened cape is a single sheet: draw both sides
				mat = mat.duplicate(); mat.cull_mode = BaseMaterial3D.CULL_DISABLED
			am.surface_set_material(am.get_surface_count() - 1, mat)
		if changed > 0:
			if mi.mesh.resource_path != "": _cape_cache[mi.mesh.resource_path] = am
			mi.mesh = am
