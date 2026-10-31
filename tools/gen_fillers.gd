extends SceneTree
## Test 14: solve the filler rows once and write res://assets/town/fillers.json (main skips fillers while it is absent).
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TownFillers.DATA))
	var m = load("res://main.tscn").instantiate(); root.add_child(m)
	for i in 20: await process_frame
	var list := TownFillers.solve(m)
	var f := FileAccess.open(TownFillers.DATA, FileAccess.WRITE); f.store_string(JSON.stringify(list, "  ")); f.close()
	print("FILLERS %d" % list.size()); quit()
