extends Node3D
## quests-test: puts the quest NPCs, interact points, pickups and enemy groups on the Tidewrack islands.
## Child of TidewrackSea, so every position is SEA-LOCAL (stage5_manifest.json coords). Spots come from Beth's stage 5
## POI walk routes (pier head -> POI, real colliders, walk-tested by tests/docking_test.gd DK_POI), so everything sits on
## walkable ground a player can reach from the pier. Spawned when you go ashore at that landing, cleared when you board.
const NEAR := 4.0
var qm: Node
var m: Node
var sea: TidewrackSea
var s5 := {}
var ents: Array = []        # [{kind, id, node, pos(local)}]
var enemies: Array = []
var here := ""

func setup(q: Node, main: Node) -> void:
	qm = q; m = main; sea = main.sea
	s5 = JSON.parse_string(FileAccess.get_file_as_string("res://tidewrack/stage5_manifest.json")).islands
	sea.went_ashore.connect(_on_ashore)
	sea.left_shore.connect(func(_k): clear())
	sea.quest_prompt = prompt_at
	qm.changed.connect(_refresh)

func poi(landing: String, name: String) -> Dictionary:
	for p in s5.get(landing, {}).get("pois", []): if p.name == name: return p
	return {}
## a walkable spot on the POI's walk route: t = 0 pier end .. 1 at the POI
func spot(landing: String, name: String, t := 1.0) -> Vector3:
	var p := poi(landing, name)
	if p.is_empty(): push_error("quest spot: no POI %s/%s" % [landing, name]); return sea.pier_head(sea.landing(landing))
	var r: Array = p.get("route", [])
	if r.is_empty(): return Vector3(p.pos[0], p.pos[1], p.pos[2])
	var a: Array = r[clampi(int(round(t * (r.size() - 1))), 0, r.size() - 1)]
	return Vector3(a[0], a[1], a[2])
func ground_local(lp: Vector3) -> Vector3:
	var w := sea.to_global(lp)
	var q := PhysicsRayQueryParameters3D.create(w + Vector3(0, 6, 0), w - Vector3(0, 20, 0), 1)
	q.exclude = [m.hero.get_rid()] + sea.ships.values().map(func(s): return s.get_rid())
	var h: Dictionary = m.get_world_3d().direct_space_state.intersect_ray(q)
	return sea.to_local(h.position) if h else lp
## global ground height for Enemy.height_fn (x, z global), searched from the enemy's own height (switchback stairs/overhangs)
func ground_near(x: float, z: float, y: float) -> float:
	var q := PhysicsRayQueryParameters3D.create(Vector3(x, y + 1.5, z), Vector3(x, y - 8.0, z), 1)
	q.exclude = [m.hero.get_rid()] + sea.ships.values().map(func(s): return s.get_rid())
	var h: Dictionary = m.get_world_3d().direct_space_state.intersect_ray(q)
	return float(h.position.y) if h else y

func _on_ashore(k: String) -> void:
	here = k
	qm.notify("travel", k)
	_refresh()
func clear() -> void:
	for e in ents: if is_instance_valid(e.node): e.node.queue_free()
	for e in enemies: if is_instance_valid(e): e.queue_free()
	ents.clear(); enemies.clear(); here = ""

func _has(kind: String, id: String) -> bool:
	for e in ents: if e.kind == kind and e.id == id: return true
	return false
## (re)spawn what this landing should show right now
func _refresh() -> void:
	if here == "" or sea.ashore != here: return
	var D: Dictionary = qm.data
	for id in D.get("npcs", {}):
		var n: Dictionary = D.npcs[id]
		var want: bool = n.landing == here and not qm.has_crew(id) and (qm.pending("talk", id) or id == "harbourmaster")
		_toggle("npc", id, want, func(): return _npc(id, n))
	for id in D.get("points", {}):
		var p: Dictionary = D.points[id]
		_toggle("point", id, p.landing == here, func(): return _point(id, p))
	for id in D.get("pickups", {}):
		var p: Dictionary = D.pickups[id]
		_toggle("pickup", id, p.landing == here and qm.pending("collect", id), func(): return _pickup(id, p))
	for id in D.get("spawns", {}):
		var s: Dictionary = D.spawns[id]
		if s.landing == here and qm.is_target("kill", id) and enemies.filter(func(e): return is_instance_valid(e)).is_empty(): _spawn_group(id, s)
	for e in ents: if e.kind == "point" and is_instance_valid(e.node): e.node.get_node("Mark").visible = qm.is_target("interact", e.id)
func _toggle(kind: String, id: String, want: bool, make: Callable) -> void:
	if want and not _has(kind, id): ents.append(make.call())
	elif not want:
		for e in ents.duplicate():
			if e.kind == kind and e.id == id:
				if is_instance_valid(e.node): e.node.queue_free()
				ents.erase(e)

func _label(parent: Node3D, t: String, y: float, col := Color(1, 0.93, 0.7)) -> Label3D:
	var l := Label3D.new(); l.text = t; l.font_size = 64; l.billboard = BaseMaterial3D.BILLBOARD_ENABLED; l.modulate = col
	l.position = Vector3(0, y, 0); parent.add_child(l); return l
func _marker(parent: Node3D, y: float, col: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); mi.name = "Mark"; var b := BoxMesh.new(); b.size = Vector3(0.35, 0.6, 0.35); mi.mesh = b
	var mat := StandardMaterial3D.new(); mat.albedo_color = col; mat.emission_enabled = true; mat.emission = col; mat.emission_energy_multiplier = 2.0
	mi.material_override = mat; mi.position = Vector3(0, y, 0); parent.add_child(mi); return mi
static func tint(n: Node, c: Color) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		if mi.mesh == null: continue
		for si in mi.mesh.get_surface_count():
			var mat = mi.get_active_material(si)
			if mat is BaseMaterial3D:
				var d: BaseMaterial3D = mat.duplicate(); d.albedo_color = d.albedo_color * c; mi.set_surface_override_material(si, d)

func _npc(id: String, n: Dictionary) -> Dictionary:
	var lp := ground_local(spot(n.landing, n.poi, float(n.get("route_t", 1.0))))
	var node := Node3D.new(); node.name = "NPC_" + id; add_child(node); node.position = lp
	var mdl: String = n.get("model", id)
	var rig := CharacterRig.new().setup(HeroRoster.model(mdl, true), HeroRoster.height(mdl)); node.add_child(rig)
	if n.has("tint"): (func(): tint(rig, Color(n.tint[0], n.tint[1], n.tint[2]))).call_deferred()
	_label(node, n.name, HeroRoster.height(mdl) + 0.5)
	_marker(node, HeroRoster.height(mdl) + 1.2, Color(1.0, 0.85, 0.2))
	var to_pier := sea.pier_head(sea.landing(n.landing)) - lp; node.rotation.y = atan2(-to_pier.x, -to_pier.z)
	return {"kind": "npc", "id": id, "node": node, "pos": lp, "name": n.name}
func _point(id: String, p: Dictionary) -> Dictionary:
	var lp := ground_local(spot(p.landing, p.poi, 1.0))
	var node := Node3D.new(); node.name = "Point_" + id; add_child(node); node.position = lp
	_marker(node, 2.4, Color(0.4, 0.9, 1.0))
	return {"kind": "point", "id": id, "node": node, "pos": lp, "name": p.name, "verb": p.get("verb", "Use")}
func _pickup(id: String, p: Dictionary) -> Dictionary:
	var lp := ground_local(spot(p.landing, p.poi, float(p.get("route_t", 1.0))))
	var node := Node3D.new(); node.name = "Pickup_" + id; add_child(node); node.position = lp
	var c := Color(p.color[0], p.color[1], p.color[2]) if p.has("color") else Color(1, 1, 0.4)
	var mi := MeshInstance3D.new(); var cy := CylinderMesh.new(); cy.top_radius = 0.18; cy.bottom_radius = 0.25; cy.height = 0.5; mi.mesh = cy
	var mat := StandardMaterial3D.new(); mat.albedo_color = c; mat.emission_enabled = true; mat.emission = c; mi.material_override = mat; mi.position.y = 0.25; node.add_child(mi)
	var ol := OmniLight3D.new(); ol.light_color = c; ol.omni_range = 5.0; ol.position.y = 1.0; node.add_child(ol)
	_label(node, p.name, 1.2)
	return {"kind": "pickup", "id": id, "node": node, "pos": lp, "name": p.name}
func _spawn_group(id: String, s: Dictionary) -> void:
	var d: EnemyDirector = m.party.director if m.party else null
	if d == null: return
	for t in s.route_t:
		var lp := ground_local(spot(s.landing, s.poi, float(t)))
		var e: Enemy = d.spawn(s.enemy, sea.to_global(lp), m.hero)
		e.position.y = sea.to_global(lp).y; e.home = e.position
		e.height_fn = func(x: float, z: float) -> float: return ground_near(x, z, e.position.y) if is_instance_valid(e) else 0.0
		if s.has("tint"): (func(): if is_instance_valid(e): tint(e.rig, Color(s.tint[0], s.tint[1], s.tint[2]))).call_deferred()
		e.died.connect(func(_e): qm.notify("kill", id))
		enemies.append(e)

## TidewrackSea._walk asks this every frame ashore: [text, callback] or []
func prompt_at(lp: Vector3) -> Array:
	var best: Dictionary = {}; var bd := NEAR
	for e in ents:
		if not is_instance_valid(e.node): continue
		var d: float = Vector2(lp.x - e.pos.x, lp.z - e.pos.z).length()
		if d < bd and absf(lp.y - e.pos.y) < 4.0: bd = d; best = e
	if best.is_empty(): return []
	var e := best
	match e.kind:
		"npc": return ["Talk: " + e.name, func(): interact(e)]
		"pickup": return ["Pick up " + e.name, func(): interact(e)]
		_: return ["%s %s" % [e.verb, e.name], func(): interact(e)]
func interact(e: Dictionary) -> void:
	match e.kind:
		"npc":
			if not qm.notify("talk", e.id): qm.dialogue.emit([[e.name, "Safe winds, captain."]])
		"pickup":
			if qm.notify("collect", e.id): sea.ui.toast("Got %s." % e.name)
		"point":
			if not qm.notify("interact", e.id): sea.ui.toast("%s. Nothing more to do here for now." % e.name)
	_refresh()
