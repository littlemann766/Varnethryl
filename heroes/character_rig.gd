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
