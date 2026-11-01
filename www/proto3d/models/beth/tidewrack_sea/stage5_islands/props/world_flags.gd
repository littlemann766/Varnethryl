class_name WorldFlags
## Beth stage 9: tiny persistent flag store (user://world_flags.cfg). Lucky: swap the two funcs for your save system if you have one.
const PATH := "user://world_flags.cfg"
static func get_flag(key: String) -> bool:
	var c := ConfigFile.new()
	if c.load(PATH) != OK: return false
	return bool(c.get_value("flags", key, false))
static func set_flag(key: String, v: bool = true) -> void:
	var c := ConfigFile.new(); c.load(PATH); c.set_value("flags", key, v); c.save(PATH)
