class_name HoodedPresenter
extends Node3D
## Isolated visual for the hooded candidate. HordeZombie does not reference this.
## The glTF faces +Z. This node turns it to the game's -Z, same as CharacterRig.
## Clips are the ones embedded in the file. They are not kael clips.

const MODEL := "res://assets/hooded_candidate/hooded_male_mobile.glb"
const FACING_YAW := PI
const BLEND := 0.30
## Authored in-place speeds from the handoff. The controller's speed_mps is faster.
const WALK_ROOT := 0.91
const RUN_ROOT := 2.0

var model: Node3D
var anim: AnimationPlayer
var skel: Skeleton3D
var clips: PackedStringArray = []
var clip := ""
var notes: PackedStringArray = []
var _last_pos := Vector2(INF, INF)
var _hit_left := 0.0
var _saw_hp := -1.0
var _death_started := false
var _in_swing := false
var _fade_mats: Array[StandardMaterial3D] = []

func _ready() -> void:
	_load(MODEL)

func use_model(path: String) -> void:
	if model:
		remove_child(model)
		model.free()
		model = null
		anim = null
		skel = null
		clips = PackedStringArray()
	_load(path)

func _load(path: String) -> void:
	var packed := load(path) as PackedScene
	if packed == null:
		notes.append("load failed %s" % path)
		return
	model = packed.instantiate()
	model.rotation.y = FACING_YAW
	add_child(model)
	anim = _find_player(model)
	skel = _find_skel(model)
	if anim == null:
		notes.append("no AnimationPlayer")
		return
	clips = anim.get_animation_list()
	for c in ["idle", "walk", "run"]:
		if anim.has_animation(c):
			anim.get_animation(c).loop_mode = Animation.LOOP_LINEAR
	for c in ["attack2", "hit", "death"]:
		if anim.has_animation(c):
			anim.get_animation(c).loop_mode = Animation.LOOP_NONE
	_fix_materials(model)
	anim.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_IDLE
	play_clip("idle", 0.0, 1.0)

func play_clip(nm: String, blend: float, speed: float) -> void:
	if anim == null or not anim.has_animation(nm):
		notes.append("missing clip %s" % nm)
		return
	anim.speed_scale = speed
	if clip == nm and blend > 0.0:
		return
	anim.play(nm, blend, 1.0)
	clip = nm

func restart_clip(nm: String, blend: float, speed: float) -> void:
	clip = ""
	play_clip(nm, blend, speed)

## Drive from a HordeZombie parent when one exists. The production script is not modified.
func _process(dt: float) -> void:
	var z := get_parent()
	# Property check, not a hard type, so this file still loads in a project that has not compiled HordeZombie.
	if z == null or z.get("state") == null:
		return
	if _saw_hp < 0.0:
		_saw_hp = z.hp
	var dead: bool = z.state == "defeated" or not z.alive()
	if dead:
		if not _death_started:
			play_clip("death", BLEND, 1.0)
			_death_started = true
		_apply_distance_fade()
		return
	if z.hp < _saw_hp - 0.5 and _hit_left <= 0.0 and z.state != "windup":
		play_clip("hit", BLEND, 1.0)
		_hit_left = 0.375
	_saw_hp = z.hp
	if _hit_left > 0.0:
		_hit_left -= dt
		if _hit_left > 0.0:
			return
	if z.state == "windup" or z.state == "recover":
		if not _in_swing:
			restart_clip("attack2", BLEND, 1.0)
			_in_swing = true
		else:
			play_clip("attack2", BLEND, 1.0)
		_apply_distance_fade()
		return
	_in_swing = false
	var here := Vector2(z.global_position.x, z.global_position.z)
	var moving := _last_pos != Vector2(INF, INF) and here.distance_to(_last_pos) > 0.004
	_last_pos = here
	if not moving:
		play_clip("idle", BLEND, 1.0)
		_apply_distance_fade()
		return
	if z.runner:
		var spd := float(z.speed_mps) / RUN_ROOT
		play_clip("run", BLEND, clampf(spd, 0.75, 2.0))
	else:
		var spd2 := float(z.speed_mps) / WALK_ROOT
		play_clip("walk", BLEND, clampf(spd2, 0.75, 1.8))
	_apply_distance_fade()

## Near body fades out across 8–14 m while the far card fades in. Hash dither, not a hard pop.
func _apply_distance_fade() -> void:
	var cam := get_viewport().get_camera_3d() if is_inside_tree() else null
	if cam == null or _fade_mats.is_empty(): return
	var dist := global_position.distance_to(cam.global_position)
	var away := clampf((dist - 8.0) / 6.0, 0.0, 1.0)
	for sm in _fade_mats:
		sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_HASH
		sm.albedo_color.a = 1.0 - away

func _find_player(n: Node) -> AnimationPlayer:
	if n is AnimationPlayer:
		return n
	for c in n.get_children():
		var p := _find_player(c)
		if p:
			return p
	return null

func _find_skel(n: Node) -> Skeleton3D:
	if n is Skeleton3D:
		return n
	for c in n.get_children():
		var s := _find_skel(c)
		if s:
			return s
	return null

func _fix_materials(n: Node) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		if mi.mesh:
			for i in mi.mesh.get_surface_count():
				var m: Material = mi.get_active_material(i)
				if m == null:
					m = mi.mesh.surface_get_material(i)
				if m is StandardMaterial3D:
					var sm := m as StandardMaterial3D
					var changed := false
					if sm.albedo_texture == null and not sm.vertex_color_use_as_albedo:
						sm.vertex_color_use_as_albedo = true
						sm.metallic_specular = 0.0
						changed = true
						notes.append("surface %d uses vertex color as albedo" % i)
					if sm.cull_mode != BaseMaterial3D.CULL_DISABLED or sm.metallic > 0.001:
						sm = sm.duplicate() as StandardMaterial3D
						sm.cull_mode = BaseMaterial3D.CULL_DISABLED
						sm.metallic = 0.0
						sm.metallic_specular = 0.0
						mi.set_surface_override_material(i, sm)
						changed = true
						notes.append("material override surface %d metallic->0 double-sided" % i)
					if changed and sm.albedo_texture == null:
						mi.set_surface_override_material(i, sm)
				if mi.get_surface_override_material(i) is StandardMaterial3D:
					var used := mi.get_surface_override_material(i) as StandardMaterial3D
					if not _fade_mats.has(used): _fade_mats.append(used)
				elif m is StandardMaterial3D and not _fade_mats.has(m):
					_fade_mats.append(m)
	for c in n.get_children():
		_fix_materials(c)
