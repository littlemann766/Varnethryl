extends Node3D
## Beth stage 10: the lift keeper in his toll booth. Children: Keeper (lift_keeper.glb, AnimationPlayer with "idle" 2.5 s and
## "crank" 2.0 s = 2 turns), Crank (sg_crank_handle.glb at the axle). The handle spins about local X at 1 rev/s while cranking.
@export var crank_rps := 1.0
var cranking := false
var ap: AnimationPlayer
@onready var crank: Node3D = $Crank
func _ready() -> void:
	var l := find_children("*", "AnimationPlayer", true, false)
	if l.size() > 0:
		ap = l[0]
		for a in ["idle", "crank"]:
			if ap.has_animation(a): ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR
		ap.play("idle")
func set_cranking(on: bool) -> void:
	cranking = on
	if ap: ap.play("crank" if on else "idle", 0.25)
func _process(dt: float) -> void:
	if cranking: crank.rotation.x -= TAU * crank_rps * dt   # same sense as the clip: grip goes over the top toward the keeper
