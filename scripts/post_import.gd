@tool
extends EditorScenePostImport
# Beth's tints live in COLOR_0; Godot's glTF importer ignores them unless this is on.
func _post_import(scene: Node) -> Object:
	_walk(scene)
	return scene

func _walk(n: Node) -> void:
	if n is ImporterMeshInstance3D and n.mesh:
		for i in n.mesh.get_surface_count():
			var m = n.mesh.get_surface_material(i)
			if m is BaseMaterial3D:
				m.vertex_color_use_as_albedo = true
	elif n is MeshInstance3D and n.mesh:
		for i in n.mesh.get_surface_count():
			var m = n.mesh.surface_get_material(i)
			if m is BaseMaterial3D:
				m.vertex_color_use_as_albedo = true
	for c in n.get_children(): _walk(c)
