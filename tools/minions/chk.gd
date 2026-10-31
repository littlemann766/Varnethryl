extends SceneTree
func _init():
	var bad := 0
	for f in ["wb_ash_fiend","wb_ash_fiend_lod1","wb_ember_wisp","wb_ember_wisp_lod1"]:
		var ps: PackedScene = load("res://m/%s.glb" % f)
		if ps == null: print("FAIL load ", f); bad += 1; continue
		var n := ps.instantiate()
		var ap: AnimationPlayer = n.find_children("*", "AnimationPlayer", true, false)[0]
		var sk: Skeleton3D = n.find_children("*", "Skeleton3D", true, false)[0]
		var names := ap.get_animation_list()
		var info := []
		for a in names:
			var an := ap.get_animation(a); info.append("%s %.2fs %dtr" % [a, an.length, an.get_track_count()])
		print("OK ", f, " bones=", sk.get_bone_count(), " meshes=", n.find_children("*", "MeshInstance3D", true, false).size(), " anims=", info)
		n.free()
	print("BAD ", bad)
	quit()
