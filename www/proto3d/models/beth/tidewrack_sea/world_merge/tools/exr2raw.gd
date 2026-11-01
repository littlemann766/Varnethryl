extends SceneTree
func _initialize() -> void:
	var a := OS.get_cmdline_user_args(); var im := Image.load_from_file(a[0]); im.convert(Image.FORMAT_RF)
	var f := FileAccess.open(a[1], FileAccess.WRITE); f.store_buffer(im.get_data()); print(im.get_width()); quit()
