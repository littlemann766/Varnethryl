class_name InteriorExtraDoors
## Makes the copies main.gd places outside DEFS enterable: appends them to main.extra_doors (InteriorManager already
## walks buildings + extra_doors). Call once at the end of main._ready(), after _harbour(), the gate towers and the
## lighthouse exist:   InteriorExtraDoors.register(self)
## Door points are building-local thresholds (port: Beth's card2 index.json door_points; gate tower: probed opening).
const PORT_DOORS := [["harbour_warehouse", Vector3(-8.0, 1.2, -5.0)], ["harbour_shop", Vector3(3.5, 1.2, -4.75)],
	["harbour_house", Vector3(-15.0, 1.2, -5.0)], ["harbour_house_b", Vector3(12.0, 1.2, -5.25)], ["harbour_house_c", Vector3(-2.5, 1.2, -6.5)]]
## pass 2: one guardroom variant per gate (main.GATES order: S, N, E, W; two towers each)
const GATE_VARIANT := ["gatetower_s", "gatetower_s", "gatetower_n", "gatetower_n", "gatetower_e", "gatetower_e", "gatetower_w", "gatetower_w"]
const GATE_DOOR := Vector3(0.0, 0.0, 10.1)   # bld_gate_tower.glb: 2-3 m opening centred on +Z, face at z 10.1
const LIGHTHOUSE_DOOR := Vector3(0.97, 7.59, 1.2)

static func _entry(id: String, node: Node3D, door: Vector3) -> Dictionary:
	# aabb only feeds the trigger depth (reach_z) and the exit spot: end.z = the door face
	var ab := AABB(Vector3(door.x - 1.5, door.y, door.z - 1.0), Vector3(3.0, 3.0, 1.0))
	return {"id": id, "name": InteriorExtraDefs.D[id].name, "node": node, "aabb": ab, "door": door, "rect": Rect2()}

static func register(main: Node) -> Array:
	var added := []
	var hb: Node3D = main.get_node_or_null("Harbour")
	if hb: for pd in PORT_DOORS: added.append(_entry(pd[0], hb, pd[1]))
	var gts: Array = main.get("gate_towers")
	for k in gts.size(): added.append(_entry(GATE_VARIANT[k] if k < GATE_VARIANT.size() else "gatetower", gts[k], GATE_DOOR))
	var lh: Node3D = main.get_node_or_null("Lighthouse")
	if lh:
		for c in lh.get_children():   # door_points are in the tower model's space
			if String(c.scene_file_path).contains("lighthouse_tower"): added.append(_entry("lighthouse", c, LIGHTHOUSE_DOOR)); break
	(main.get("extra_doors") as Array).append_array(added)
	return added
