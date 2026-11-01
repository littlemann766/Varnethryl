extends Node3D
## Beth stage 9: Saltglass shortcut portcullis (Dark Souls style). LOCKED from the dock side; the lever stands on the ramp side,
## so it can only be reached by coming DOWN the shortcut from the plateau (after climbing the stairs once). Pulling it raises the
## gate and saves the flag; on later loads the gate starts open.
## Scene: this node at gate.pos (world, yaw 0 - leaf spans z), children: Leaf (sg_shortcut_gate.glb + StaticBody3D box 0.3x3.4x4.0,
## centre y 1.7), Lever (sg_lever.glb) at lever.pos. Hook: from tw_sea._walk, `var p = gate.prompt_for(hero_pos)` -> ui.set_prompt(p[0], p[1]).
@export var flag := "saltglass_shortcut_open"
@export var raise_m := 3.6
@export var raise_time := 2.5
@export var lever_reach := 2.2
@onready var leaf: Node3D = $Leaf
@onready var lever: Node3D = $Lever
var open := false
func _ready() -> void:
	open = WorldFlags.get_flag(flag)
	if open: leaf.position.y = raise_m; _lever_down()
func _lever_down() -> void: lever.rotation.z = deg_to_rad(-55.0)
func prompt_for(hero_pos: Vector3) -> Array:
	if open: return ["", Callable()]
	if hero_pos.distance_to(lever.global_position) < lever_reach: return ["Pull lever", unlock]
	if hero_pos.distance_to(leaf.global_position) < 3.0 and hero_pos.x < global_position.x: return ["Locked from the other side", Callable()]
	return ["", Callable()]
func unlock() -> void:
	if open: return
	open = true; WorldFlags.set_flag(flag, true); _lever_down()
	var tw := create_tween(); tw.set_process_mode(Tween.TWEEN_PROCESS_PHYSICS); tw.tween_property(leaf, "position:y", raise_m, raise_time).set_trans(Tween.TRANS_SINE)
