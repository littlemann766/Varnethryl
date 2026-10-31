extends Node
## Pass ceilings hide while the camera rides above them (InteriorManager's high over-the-walls camera);
## warm fire/torch lights flicker (cheap: energy only, 2 sines + noise, no shadow changes).
var ceilings: Array = []
var flicker: Array = []
var _base := {}
var _t := 0.0
func _process(dt: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam:
		for c in ceilings:
			if is_instance_valid(c): c.visible = cam.global_position.y < (c as Node3D).global_position.y + float(c.get_meta("ytop"))
	_t += dt
	for i in flicker.size():
		var l = flicker[i]
		if not is_instance_valid(l) or not l.is_visible_in_tree(): continue
		if not _base.has(l): _base[l] = l.light_energy
		l.light_energy = _base[l] * (0.88 + 0.08 * sin(_t * 9.0 + i * 1.7) + 0.05 * sin(_t * 23.0 + i * 3.1))
