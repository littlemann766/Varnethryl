class_name HudOverlap
## test 36 (boss: "make sure no HUD texts overlap anywhere"): every visible on-screen text (Label / Button with text, on
## any CanvasLayer or the root viewport) gets its text box; any two boxes that intersect (not parent/child) are reported.
static func _text_rect(c: Control) -> Rect2:
	var r := c.get_global_rect()
	if c is Label and (c as Label).autowrap_mode == TextServer.AUTOWRAP_OFF:
		var l := c as Label
		var f := l.get_theme_font("font"); var fs := l.get_theme_font_size("font_size")
		var w := 0.0; var lines := l.text.split("\n")
		for t in lines: w = maxf(w, f.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x)
		var h := f.get_height(fs) * lines.size()
		w = minf(w, r.size.x) if r.size.x > 1.0 else w
		var x := r.position.x
		if l.horizontal_alignment == HORIZONTAL_ALIGNMENT_CENTER: x += (r.size.x - w) * 0.5
		elif l.horizontal_alignment == HORIZONTAL_ALIGNMENT_RIGHT: x += r.size.x - w
		var y := r.position.y
		if l.vertical_alignment == VERTICAL_ALIGNMENT_CENTER: y += (r.size.y - h) * 0.5
		elif l.vertical_alignment == VERTICAL_ALIGNMENT_BOTTOM: y += r.size.y - h
		return Rect2(x, y, w, minf(h, maxf(r.size.y, h)))
	return r
static func _collect(n: Node, out: Array) -> void:
	if n is CanvasItem and not (n as CanvasItem).visible: return
	if n is Control:
		var c := n as Control
		if c.is_visible_in_tree() and c.modulate.a > 0.05 and c.self_modulate.a > 0.05:
			if (c is Label or c is Button) and str(c.get("text")).strip_edges() != "": out.append(c)
	for ch in n.get_children(): _collect(ch, out)
static func overlaps(root: Node) -> Array:
	var items: Array = []; _collect(root, items)
	var res: Array = []
	for i in items.size():
		for j in range(i + 1, items.size()):
			var a: Control = items[i]; var b: Control = items[j]
			if a.is_ancestor_of(b) or b.is_ancestor_of(a): continue
			var ra := _text_rect(a); var rb := _text_rect(b)
			if ra.grow(-1.0).intersects(rb.grow(-1.0)): res.append("'%s' %s x '%s' %s" % [str(a.get("text")).left(24), str(ra), str(b.get("text")).left(24), str(rb)])
	return res
