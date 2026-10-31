extends SceneTree
func _initialize() -> void: _run.call_deferred()
func _rss() -> int:
	for l in FileAccess.get_file_as_string("/proc/self/status").split("\n"): if l.begins_with("VmRSS"): return int(l.split(":")[1].strip_edges().split(" ")[0]) / 1024
	return -1
func _run() -> void:
	print("MEM before %d MB" % _rss())
	var m = load("res://main.tscn").instantiate(); root.add_child(m)
	for i in 60: await process_frame
	print("MEM after %d MB static %d MB vid %d MB tex %d MB" % [_rss(), Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576, Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576, Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576])
	quit()
