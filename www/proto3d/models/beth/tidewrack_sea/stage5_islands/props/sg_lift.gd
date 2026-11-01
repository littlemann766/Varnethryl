extends AnimatableBody3D
## Beth stage 9: Saltglass dock lift, 20.4 -> 108.68 m (88.3 m) at 6 m/s (~15 s). Platform = sg_lift_platform.glb, origin = deck top centre.
## Collision (children): deck box 3.6x0.3x3.6 at y -0.15, rails 3.6x1.1x0.12 at z -1.74, 0.12x1.1x3.6 at x +-1.74 (door side +z open).
## sync_to_physics = true so the hero (CharacterBody3D) rides it. Call levers at both stops (call_bottom / call_top in the manifest).
## Locked: if `requires_flag` is set and not yet saved, the lift parks at the TOP and the bottom call says it's locked from above
## (its own flag; riding it down from the top once saves it. Clear requires_flag to have it always open.)
@export var bottom := Vector3(-2104.0, 20.4, -82.0)
@export var top := Vector3(-2104.0, 108.68, -82.0)
@export var speed := 6.0
@export var requires_flag := "saltglass_lift_unlocked"
@export var call_bottom := Vector3(-2105.8, 20.4, -77.7)
@export var call_top := Vector3(-2105.8, 108.68, -77.7)
@export var reach := 2.4
var moving := false
func _ready() -> void:
	sync_to_physics = true
	global_position = top if (requires_flag != "" and not WorldFlags.get_flag(requires_flag)) else bottom
func unlocked() -> bool: return requires_flag == "" or WorldFlags.get_flag(requires_flag)
func at_top() -> bool: return global_position.distance_to(top) < 0.1
func prompt_for(hero_pos: Vector3) -> Array:
	if moving: return ["", Callable()]
	var on := Vector2(hero_pos.x - global_position.x, hero_pos.z - global_position.z).length() < 1.7 and absf(hero_pos.y - global_position.y) < 1.5
	if on: return ["Ride down" if at_top() else "Ride up", func(): go(bottom if at_top() else top)]
	if hero_pos.distance_to(call_bottom) < reach and at_top(): return ["Call lift", func(): go(bottom)] if unlocked() else ["The lift is locked from above", Callable()]
	if hero_pos.distance_to(call_top) < reach and not at_top(): return ["Call lift", func(): go(top)]
	return ["", Callable()]
func go(to: Vector3) -> void:
	if moving: return
	moving = true
	if to == bottom and requires_flag != "" and not WorldFlags.get_flag(requires_flag): WorldFlags.set_flag(requires_flag, true)   # riding down from the top = the shortcut is found
	var tw := create_tween(); tw.set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
	tw.tween_property(self, "global_position", to, global_position.distance_to(to) / speed).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.finished.connect(func(): moving = false)
