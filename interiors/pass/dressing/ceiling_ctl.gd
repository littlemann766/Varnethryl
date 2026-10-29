extends Node
## Hides the pass ceilings while the camera rides above them (InteriorManager's high over-the-walls camera).
var ceilings: Array = []
func _process(_dt: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam == null: return
	for c in ceilings:
		if is_instance_valid(c): c.visible = cam.global_position.y < (c as Node3D).global_position.y + float(c.get_meta("ytop"))
