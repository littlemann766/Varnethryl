class_name TidewrackSea
extends Node3D
## test 32: Beth's Tidewrack Sea (beth-world-art de97bc3, stages 1-4) wired into the game.
## The sea is its own world, placed at OFF (far south of the mainland map) so its map-metre coordinates (README: origin =
## Archipelago centre, north -Z, water y 0) are kept as LOCAL coordinates under this node. You set sail from the moored
## galleon at Tidewrack harbour (or Travel > Sail); Harbour Charts "Tidewrack pier" brings you home.
## - regions A (Archipelago), B (Saltglass Coast), C-N frost and C-S ash stream in with threaded loads ~150 m from their box;
## - each region keeps its fog/sky/storm-sea border; the invisible storm_col boxes are StaticBody colliders (never drawn);
##   a box between two UNLOCKED regions is dropped. B is locked until the Brinecrown Coil is beaten (save flag);
## - caves (Echo Grotto, Glasswyrm Cavern, Smugglers' Throat) are Stage 3 cells: skiff in at the mouth -> fade/teleport into
##   the cell; sail back out of the cell portal -> fade/teleport to a CLEAR open-water exit (walked out along the mouth on the
##   shore-distance map; never a fixed offset, the Echo Grotto inlet is only ~30 m wide - stage2 PROGRESS);
## - Sunken Ward: dive ring r 30 m at the dive buoy -> fade into the underwater Ward (Stage 3, world coords), swim, surface;
## - icebergs drift along the manifest headings and bounce off the shore (DM < 40 m), bobbing with the waves;
## - galleon/skiff tiers (upg_* add-ons), wind, shallows, gust charm, Shipwright at Gullhaven, Harbour Charts fast travel.
const OFF := Vector3(0.0, 0.0, 20000.0)
const R := "res://tidewrack/"
const REGIONS := {
	"A": {"rect": [-1200.0, -1300.0, 2700.0, 2600.0], "wind": Vector2(0.8, 0.6), "shore": "stage1/shaders/arch_shore_dist.png", "dir": "stage1/meshes/", "pre": "arch_", "ice": 0.0},
	"B": {"rect": [-3000.0, -1500.0, 1800.0, 3200.0], "wind": Vector2(1.0, 0.1), "shore": "stage2/shaders/coast_shore_dist.png", "dir": "stage2/meshes/", "pre": "coast_", "ice": 0.0},
	"frost": {"rect": [-2400.0, -3000.0, 3900.0, 1500.0], "wind": Vector2(0.0, 1.0), "shore": "stage4/shaders/frost_shore_dist.png", "dir": "stage4/meshes/", "pre": "frost_", "ice": 0.3},
	"ash": {"rect": [-1800.0, 1450.0, 3300.0, 1550.0], "wind": Vector2(0.0, -1.0), "shore": "stage4/shaders/ash_shore_dist.png", "dir": "stage4/meshes/", "pre": "ash_", "ice": 0.0}}
const SKIP := ["arch_storm_wall", "arch_fog_bank", "frost_iceberg_a", "frost_iceberg_b", "frost_iceberg_c"]   # old slab border (replaced by v2) / bergs are instanced
const CAVES := {"echo_grotto": "coast_echo_grotto", "glasswyrm_cavern": "coast_glasswyrm_cavern", "smugglers_throat": "coast_smugglers_throat"}
const CELL_BASE := Vector3(7000.0, 0.0, -2000.0)   # cave cells sit far east of every region
var m: Node
var M := {}                 # manifests: s1, s2, s3, s4
var active := false
var ship: TwShip
var ships := {}             # kind -> TwShip (the galleon waits where you left it while you take the skiff)
var regions := {}           # id -> {state: 0 idle / 1 loading / 2 built, node, cols:[[StaticBody3D, Vector3 centre]]}
var shore := {}             # id -> Image
var water: MeshInstance3D
var water_mats := {}
var cur_region := "A"
var bergs := []
var cells := {}
var in_cave := ""
var diving := false
var ward: Node3D
var ui: TwUi
var save: Dictionary:   # live: VSave.state can be replaced when a save loads
	get: return _load_save()
var sun_dist := 0.0
var cave_env: Environment
var under_env: Environment
var cave_cd := 0
var unlock_all := false     # Owner (cheats live only on his hero) sails anywhere
## quests-test: QuestWorld hooks (travel steps = ashore at a landing; interact prompts for quest NPCs / points / pickups)
signal went_ashore(k: String)
signal left_shore(k: String)
var quest_prompt := Callable()   # f(sea-local hero pos) -> [text, callback] or []

func setup(main: Node) -> TidewrackSea:
	m = main; name = "TidewrackSea"; position = OFF; visible = false
	for k in [["s1", "stage1/meshes/stage1_manifest.json"], ["s2", "stage2/meshes/stage2_manifest.json"], ["s3", "stage3/meshes/stage3_manifest.json"], ["s4", "stage4/meshes/stage4_manifest.json"]]:
		M[k[0]] = JSON.parse_string(FileAccess.get_file_as_string(R + k[1]))
	ui = TwUi.new(); ui.sea = self; m.add_child(ui)
	cave_env = Environment.new(); cave_env.background_mode = Environment.BG_COLOR; cave_env.background_color = Color(0.02, 0.025, 0.03)
	cave_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; cave_env.ambient_light_color = Color(0.3, 0.36, 0.42); cave_env.ambient_light_energy = 5.0
	cave_env.tonemap_exposure = 1.5
	under_env = Environment.new(); under_env.background_mode = Environment.BG_COLOR; under_env.background_color = Color(0.08, 0.32, 0.36)
	under_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; under_env.ambient_light_color = Color(0.25, 0.5, 0.55)
	under_env.fog_enabled = true; under_env.fog_light_color = Color(0.08, 0.32, 0.36); under_env.fog_density = 0.015
	return self

# ---------------------------------------------------------------- save
func _load_save() -> Dictionary:
	var st: Dictionary = m.get_tree().root.get_node("VSave").state
	if not st.has("sea"): st["sea"] = {"galleon_tier": 0, "skiff_tier": 0, "discovered_ports": ["tidewrack"], "coil_beaten": false, "items": {}}
	return st["sea"]
func write_save() -> void: m.get_tree().root.get_node("VSave").write_state()
func unlocked(id: String) -> bool:
	if unlock_all or id != "B": return true
	var story = m.get_tree().root.get_node("VSave").state.get("story", {})   # quests-test: Wren's night chart opens the Saltglass Coast
	if story is Dictionary and story.get("flags", {}).get("unlock_B", false): return true
	return bool(save.get("coil_beaten", false))

# ---------------------------------------------------------------- materials
func high() -> bool: return int(m.tier) >= 2
func _sh(path: String) -> ShaderMaterial:
	var s := ShaderMaterial.new(); s.shader = load(R + path); return s
func _mat_for(n: String) -> Material:
	var st4 := n.begins_with("frost_") or n.begins_with("ash_")
	if n.ends_with("_fog_layers"):
		var f := _sh("stage1/shaders/fog_layers.gdshader")
		if st4:
			var fc: Dictionary = M.s4.fog["frost" if n.begins_with("frost_") else "ash"]
			f.set_shader_parameter("fog_col", Color(fc.fog_col[0], fc.fog_col[1], fc.fog_col[2])); f.set_shader_parameter("fog_dark", Color(fc.fog_dark[0], fc.fog_dark[1], fc.fog_dark[2]))
		return f
	if n.ends_with("_storm_sky"): return _sh("stage1/shaders/storm_sky.gdshader")
	if n.ends_with("_storm_sea"): return _sh("stage1/shaders/storm_sea.gdshader")
	if n.ends_with("_glow"): return _sh(("stage4" if st4 else "stage3") + "/shaders/glow_vc.gdshader")
	if n == "ash_lava_seams":
		var l := _sh("stage4/shaders/lava_seam.gdshader"); l.set_shader_parameter("energy", 6.0); return l
	if n == "ash_steam": return _sh("stage4/shaders/steam_plume.gdshader")
	if n.begins_with("ash_"):   # stage 4 README: black basalt = vertex colour + metallic_specular 0.15 (else it mirrors the haze and reads beige)
		var ar := _sh("stage1/shaders/vc_flat.gdshader"); ar.set_shader_parameter("lift", 0.14); ar.set_shader_parameter("ambient", 0.8); ar.set_shader_parameter("spec", 0.075); return ar   # test 37: lifted basalt (was pure black on screen)
	return _sh("stage1/shaders/vc_flat.gdshader")   # test 37: flat normals + near-camera fade (glbs have no NORMAL)
func _no_shadow(n: String) -> bool:
	for k in ["_fog_layers", "_storm_sky", "_storm_sea", "_glow", "_steam", "_lava_seams", "buoy_", "upg_", "_ice_floes", "_icicles"]:
		if n.find(k) >= 0: return true
	return false

# ---------------------------------------------------------------- regions / streaming
func _files(id: String) -> Array:
	var d: Dictionary = REGIONS[id]; var out := []
	for f in DirAccess.get_files_at(R + d.dir):
		var f2 := f.trim_suffix(".remap").trim_suffix(".import")
		var b := f2.trim_suffix(".glb")
		if not f2.ends_with(".glb") or not f2.begins_with(d.pre) or out.has(b): continue   # test 37: was out.has(f2) -> every region mesh (x.glb + x.glb.import) loaded and drawn twice
		if b.ends_with("_lod1") or b in SKIP: continue
		if id == "B" and b in CAVES.values(): pass
		out.append(b)
	return out
func _path(id: String, b: String) -> String:
	var d: Dictionary = REGIONS[id]
	if b.ends_with("_col"): return R + d.dir + b + ".glb"
	var lo: String = R + d.dir + b + "_lod1.glb"
	return lo if not high() and ResourceLoader.exists(lo) else R + d.dir + b + ".glb"
func _rect_dist(id: String, p: Vector2) -> float:
	var r: Array = REGIONS[id].rect
	var dx := maxf(maxf(r[0] - p.x, p.x - (r[0] + r[2])), 0.0); var dz := maxf(maxf(r[1] - p.y, p.y - (r[1] + r[3])), 0.0)
	return Vector2(dx, dz).length()
func _stream(p: Vector2) -> void:
	for id in REGIONS:
		var e: Dictionary = regions.get(id, {"state": 0})
		var d := _rect_dist(id, p)
		if e.state == 0 and (d < 150.0 or id == cur_region):
			for b in _files(id): ResourceLoader.load_threaded_request(_path(id, b))
			e.state = 1; regions[id] = e
		elif e.state == 1:
			var ready := true
			for b in _files(id):
				if ResourceLoader.load_threaded_get_status(_path(id, b)) == ResourceLoader.THREAD_LOAD_IN_PROGRESS: ready = false
			if ready: _build_region(id)
		elif e.state == 2 and d > 900.0 and id != cur_region:
			e.node.queue_free(); regions[id] = {"state": 0}
			if id == "frost": bergs.clear()
func _build_region(id: String) -> void:
	var root := Node3D.new(); root.name = "Region_" + id; add_child(root)
	var e := {"state": 2, "node": root, "cols": []}
	for b in _files(id):
		var ps: PackedScene = ResourceLoader.load_threaded_get(_path(id, b))
		if ps == null: continue
		var v: Node3D = ps.instantiate()
		if b.ends_with("_col"):   # colliders only: never drawn
			for mi: MeshInstance3D in v.find_children("*", "MeshInstance3D", true, false):
				if b.ends_with("_storm_col"):   # Beth's 4 thin 60 m boxes (one merged mesh) -> 4 separate boxes so each side can open
					var bb: AABB = _local_xf(mi, v) * mi.mesh.get_aabb(); var lo := bb.position; var hi := bb.end; var T := 4.0
					for side in [[Vector3(lo.x, 0, 0), Vector3(T, 0, bb.size.z)], [Vector3(hi.x, 0, 0), Vector3(T, 0, bb.size.z)], [Vector3(0, 0, lo.z), Vector3(bb.size.x, 0, T)], [Vector3(0, 0, hi.z), Vector3(bb.size.x, 0, T)]]:
						var c: Vector3 = bb.get_center(); c.y = (lo.y + hi.y) * 0.5
						if side[0].x != 0.0: c.x = side[0].x
						if side[0].z != 0.0: c.z = side[0].z
						var sz: Vector3 = side[1]; sz.y = bb.size.y
						var sb2 := StaticBody3D.new(); var cs2 := CollisionShape3D.new(); var bs := BoxShape3D.new(); bs.size = sz; cs2.shape = bs; sb2.add_child(cs2)
						root.add_child(sb2); sb2.position = c; e.cols.append([sb2, c])
					continue
				var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); cs.shape = mi.mesh.create_trimesh_shape(); sb.add_child(cs)
				root.add_child(sb); sb.transform = _local_xf(mi, v)
			v.free(); continue
		root.add_child(v)
		for mi: MeshInstance3D in v.find_children("*", "MeshInstance3D", true, false):
			mi.material_override = _mat_for(b)
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if _no_shadow(b) or not high() else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	regions[id] = e
	if id == "A": _place_a(root)
	if id == "B": _place_b(root)
	if id == "frost": _place_bergs(root)
	_place_landings(id, root)
	_access_patches(id, root)
	_border_update()
func _local_xf(mi: Node3D, top: Node3D) -> Transform3D:
	var t := Transform3D.IDENTITY; var n: Node = mi
	while n != null and n != top.get_parent():
		if n is Node3D: t = (n as Node3D).transform * t
		n = n.get_parent()
	return t
func _border_update() -> void:
	# drop a border box between two unlocked regions (the fog stays: you sail through it)
	for id in regions:
		var e: Dictionary = regions[id]
		if e.state != 2: continue
		for c in e.cols:
			var p := Vector2(c[1].x, c[1].z); var open := false
			for o in REGIONS:
				if o != id and unlocked(o) and unlocked(id) and _rect_dist(o, p) < 300.0: open = true
			var sb: StaticBody3D = c[0]; sb.collision_layer = 0 if open else 1
func _inst(path: String, pos: Vector3, yaw := 0.0, parent: Node = null) -> Node3D:
	var v: Node3D = load(path).instantiate(); (parent if parent else self).add_child(v); v.position = pos; v.rotation.y = yaw
	for mi: MeshInstance3D in v.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = load(R + "stage1/shaders/vc_lit.tres"); mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return v
func _lod(base: String) -> String: return base + (".glb" if high() else "_lod1.glb")
func _v3(a: Array) -> Vector3: return Vector3(a[0], a[1], a[2])
func _place_a(root: Node3D) -> void:
	var P: Dictionary = M.s1.props
	_inst(_lod(R + "stage1/meshes/buoy_dive"), _v3(P.saltwatch_keep.dive_bell) * Vector3(1, 0, 1), 0.0, root)
	# Brinecrown Coil: Lucian has not rigged it yet, so it rests (static) in its arena ring; the deck fight comes with his rig
	_inst(_lod(R + "stage1/meshes/brinecrown_coil_rest"), _v3(P.coil_arena.pos), 0.0, root)
	var reef := _v3(P.wreck_reef.pos)
	for k in 10: _inst(_lod(R + "stage1/meshes/buoy_route"), reef + Vector3(cos(k * TAU / 10.0), 0, sin(k * TAU / 10.0)) * 100.0, 0.0, root)
func _place_b(root: Node3D) -> void:
	var P: Dictionary = M.s2.props
	var c := _v3(P.sunken_ward.dive_buoy)
	for k in 6: _inst(_lod(R + "stage1/meshes/buoy_dive"), c + Vector3(cos(k * TAU / 6.0), 0, sin(k * TAU / 6.0)) * float(P.sunken_ward.ring_radius), 0.0, root)
	for cave in CAVES:   # white skiff buoy at the clear open-water point outside each mouth (never a fixed offset)
		var q: Dictionary = P[CAVES[cave]]
		var ex := clear_exit(_v3(q.pos), float(q.yaw))
		_inst(_lod(R + "stage1/meshes/buoy_skiff"), ex[0], 0.0, root)
func _place_bergs(root: Node3D) -> void:
	bergs.clear()
	for b in M.s4.icebergs:
		var v := _inst(_lod(R + "stage4/meshes/" + b.mesh), _v3(b.pos), float(b.yaw), root); v.scale = Vector3.ONE * float(b.scale)
		bergs.append({"node": v, "dir": Vector2(b.drift_dir[0], b.drift_dir[2]).normalized(), "mps": float(b.drift_mps), "spin": float(b.spin_rad_s), "r": float(b.col_radius_m)})

# ---------------------------------------------------------------- shore distance (CPU)
func region_at(p: Vector2) -> String:
	for id in ["A", "B", "frost", "ash"]:
		if _rect_dist(id, p) <= 0.0: return id
	var best := "A"; var bd := 1e9
	for id in REGIONS:
		var d := _rect_dist(id, p)
		if d < bd: bd = d; best = id
	return best
var _causeways: Array = []
func causeways() -> Array:   # [[a, b], ...] from tidewrack/stage5_manifest.json (islands.<id>.bridges)
	if _causeways.is_empty():
		var d = JSON.parse_string(FileAccess.get_file_as_string(R + "stage5_manifest.json"))
		if d is Dictionary:
			for k in d.islands:
				for br in d.islands[k].get("bridges", []): _causeways.append([_v3(br.a), _v3(br.b), k])
	return _causeways
func shore_m(p: Vector2) -> float:
	var id := region_at(p)
	if _rect_dist(id, p) > 0.0: return 255.0
	if not shore.has(id):
		var img: Image = (load(R + REGIONS[id].shore) as Texture2D).get_image()
		if img.is_compressed(): img.decompress()
		shore[id] = img
	var im: Image = shore[id]; var r: Array = REGIONS[id].rect
	var u := clampi(int((p.x - r[0]) / r[2] * im.get_width()), 0, im.get_width() - 1); var v := clampi(int((p.y - r[1]) / r[3] * im.get_height()), 0, im.get_height() - 1)
	return im.get_pixel(u, v).r * 255.0
## Beth (stage2 PROGRESS, de97bc3): walk out along the mouth's facing on the shore-distance map and stop at the last
## open-water point, so nothing spawns inside the north cliff of the ~30 m Echo Grotto inlet. Returns [pos, yaw away].
func clear_exit(mouth: Vector3, yaw: float) -> Array:
	var best := [mouth, yaw]; var bs := -1.0
	for sgn: float in [1.0, -1.0]:
		var d := Vector2(sin(yaw), cos(yaw)) * sgn; var last := Vector2(mouth.x, mouth.z); var s0 := -1.0; var hit_land := false
		for k in range(1, 61):   # 2 m steps, up to 120 m
			var p := Vector2(mouth.x, mouth.z) + d * (k * 2.0); var sd := shore_m(p)
			if sd < 3.0 and k > 4: hit_land = true; break
			if sd >= 6.0: last = p; s0 = maxf(s0, sd)
		if s0 > bs: bs = s0; best = [Vector3(last.x, 0.0, last.y), atan2(d.x, d.y)]
	return best

# ---------------------------------------------------------------- water
func _water_mat(id: String) -> ShaderMaterial:
	var key := id + ("_hi" if high() else "_lo")
	if water_mats.has(key): return water_mats[key]
	var d: Dictionary = REGIONS[id]; var path := "stage1/shaders/ocean_water.gdshader" if high() else "stage1/shaders/ocean_water_low.gdshader"
	if id == "ash" and not high(): path = "stage4/shaders/ocean_water_low_straits.gdshader"   # de97bc3: Low ash water no longer brown
	var s := _sh(path); var r: Array = d.rect
	s.set_shader_parameter("shore_dist", load(R + d.shore))
	s.set_shader_parameter("shore_rect", Vector4(r[0] + OFF.x, r[1] + OFF.z, r[2], r[3]))   # the shaders read WORLD xz
	if high(): s.set_shader_parameter("wind_dir", d.wind); s.set_shader_parameter("ice", d.ice)
	if id in ["frost", "ash"]:
		var w: Dictionary = M.s4.regions[id].water
		s.set_shader_parameter("deep", Color(w.deep[0], w.deep[1], w.deep[2])); s.set_shader_parameter("shallow", Color(w.shallow[0], w.shallow[1], w.shallow[2]))
	water_mats[key] = s; return s
func _make_water() -> void:
	water = MeshInstance3D.new(); var pm := PlaneMesh.new()
	pm.size = Vector2(1600, 1600); pm.subdivide_width = 200 if high() else 32; pm.subdivide_depth = pm.subdivide_width
	water.mesh = pm; water.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(water)

# ---------------------------------------------------------------- enter / leave
func enter(kind := "galleon", at := Vector3.INF, yaw := INF) -> void:
	if water == null: _make_water()
	unlock_all = m.party != null and str(m.party.get("hero_id")) == "owner"
	visible = true; active = true
	if at == Vector3.INF:   # Tidewrack bay mouth: open water at the east edge of the Archipelago
		at = Vector3(1300, 0, 300); yaw = -PI / 2
	_board(kind, at, yaw)
	m.hero.collision_layer = 0; m.hero.collision_mask = 0; m.pip.visible = true
	if m.party: m.party.riding = true
	sun_dist = m.sun.directional_shadow_max_distance; m.sun.directional_shadow_max_distance = 60.0   # README: 60 m shadows at sea
	cur_region = region_at(Vector2(at.x, at.z)); _stream(Vector2(at.x, at.z))
	_port_check(true)
func leave_to_harbour() -> void:
	if m.party: m.party.ground_snap = Callable()
	ashore = ""; active = false; visible = false; in_cave = ""; diving = false; m.cam.environment = null
	m.hero.collision_layer = 1; m.hero.collision_mask = 1; m.pip.visible = true; unseat_crew()
	m.sun.directional_shadow_max_distance = sun_dist
	var g: Array = m._galleon_pier()
	m.hide_where(); m.hero.global_position = g[0]; m.hero.velocity = Vector3.ZERO; m.yaw = g[1]
	ui.set_prompt("", Callable())
func _board(kind: String, at: Vector3, yaw: float) -> void:
	if not ships.has(kind):
		var s := TwShip.new().setup(kind, int(save.get(kind + "_tier", 0)), high()); add_child(s)
		s.shallow_fn = shore_m; ships[kind] = s
	ship = ships[kind]; ship.alt = 0.0; ship.position = Vector3(at.x, 0.0, at.z); ship.heading = yaw; ship.speed = 0.0; ship.throttle = 0.0
	if kind == "skiff" and ships.has("galleon"): ships.galleon.visible = true
	ship.visible = true

func cam_dist() -> float: return 24.0 if ship and ship.kind == "galleon" else 11.0

## test 33 (boss): with the fly cheat on, the whole ship flies (target = main.fly_alt, min SHIP_FLY_MIN, max SHIP_FLY_MAX),
## level, steerable, fly up/down buttons work. Fly off over water -> settles back onto the sea; fly off over land -> it
## holds just above the ground (never drops onto land) and settles once it is back over water.
const SHIP_FLY_MIN := 14.0
const SHIP_FLY_MAX := 300.0
func ship_flying() -> bool:
	var ch = m.get("cheats"); return ch != null and bool(ch.flags.get("fly", false)) and in_cave == "" and not diving
func over_water(p: Vector2) -> bool: return shore_m(p) >= 8.0
func _fly_step(dt: float) -> void:
	var ch = m.get("cheats")
	ship.speed_mul = clampf(float(ch.flags.get("speed", 1.0)), 0.1, 50.0) if ch != null else 1.0
	var p := Vector2(ship.position.x, ship.position.z); var want := 0.0
	if ship_flying(): want = clampf(float(m.fly_alt), SHIP_FLY_MIN, SHIP_FLY_MAX)
	elif ship.alt > 0.0 and not over_water(p): want = SHIP_FLY_MIN
	var was := ship.alt
	ship.alt = move_toward(ship.alt, want, maxf(8.0, absf(want - ship.alt) * 1.5) * dt)
	if ship.alt < 0.05 and want == 0.0: ship.alt = 0.0
	ship.collision_mask = 0 if ship.alt > 1.0 else ship_mask0
	if was > 0.0 and ship.alt == 0.0: ui.toast("Back on the water.")
var ship_mask0 := 1

## test 33 (boss: Pip swam beside the boat): Pip + companions ride ON the deck at fixed seats (ship-local), facing the
## bow, rising with the ship when it flies; party follow AI is off while riding and comes back on disembark.
const SEATS := {"galleon": [Vector3(1.4, 0, -2.6), Vector3(-1.6, 0, -1.0), Vector3(1.6, 0, 1.2), Vector3(-1.6, 0, 3.0), Vector3(1.6, 0, 4.6)],
	"skiff": [Vector3(0.35, 0, 0.2), Vector3(-0.35, 0, 1.0), Vector3(0.3, 0, 1.8), Vector3(-0.3, 0, 2.4), Vector3(0.0, 0, -0.5)]}
func deck_y() -> float: return (2.78 if ship.kind == "galleon" else 0.62) + ship.vis.position.y - TwShip.MODEL[ship.kind][1]
func seat_pos(i: int) -> Vector3:
	var S: Array = SEATS[ship.kind]; var o: Vector3 = S[mini(i, S.size() - 1)]
	return ship.global_position + ship.global_basis * Vector3(o.x, deck_y(), o.z)
func seat_crew() -> void:
	if ship == null or diving: return
	if m.party: m.party.riding = true
	var k := 0
	if m.pip: m.pip.visible = true; m.pip.global_position = seat_pos(k); m.pip.rotation = Vector3(0, ship.heading + PI, 0); k += 1
	if m.party:
		for c in m.party.companions:
			c.node.global_position = seat_pos(k); c.node.rotation = Vector3(0, ship.heading + PI, 0); k += 1
			if c.rig: c.rig.set_move_mps(0.0); c.rig.set_flight(false)
func unseat_crew() -> void:
	if m.party:
		m.party.riding = false; m.party.trail = PackedVector3Array()
		var i := 0
		for c in m.party.companions: c.node.global_position = m.hero.global_position + Vector3(1.0 + i, 0, 1.0); c.node.rotation = Vector3.ZERO; i += 1
	if m.pip: m.pip.position = m.hero.position + Vector3(1, 0, 1)
	snap_crew()
## test 36 (boss: companion hovering ~1 m beside the hero at Gullhaven): feet of Pip + every walking companion on the floor.
func floor_y(w: Vector3) -> float:
	var q := PhysicsRayQueryParameters3D.create(Vector3(w.x, m.hero.global_position.y + 4.0, w.z), Vector3(w.x, m.hero.global_position.y - 12.0, w.z), 1)
	q.exclude = [m.hero.get_rid()] + ships.values().map(func(s): return s.get_rid())
	var hit: Dictionary = m.get_world_3d().direct_space_state.intersect_ray(q)
	return float(hit.position.y) if hit else NAN
func snap_crew() -> void:
	if ashore == "": return
	var nodes: Array = []
	if m.pip: nodes.append(m.pip)
	if m.party:
		for c in m.party.companions:
			if not m.party.FLYERS.has(c.id): nodes.append(c.node)
	for n in nodes:
		var gy := floor_y(n.global_position)
		if is_nan(gy):   # off the pier/beach edge: stand beside the hero instead
			n.global_position = m.hero.global_position + (n.global_position - m.hero.global_position).normalized() * 1.0; gy = floor_y(n.global_position)
		if not is_nan(gy): n.global_position.y = gy

# ---------------------------------------------------------------- per frame (called from main._physics_process)
func drive(inp: Vector2, dt: float) -> void:
	if diving: _swim(inp, dt); return
	if ashore != "": _walk(inp, dt); return
	ship.wind = REGIONS[cur_region].wind
	var before := ship.position
	_fly_step(dt)
	ship.drive(inp, dt)
	_night_cap()
	var p := Vector2(ship.position.x, ship.position.z)
	if in_cave == "" and ship.alt > 0.0:   # airborne: over reefs, bergs and shores, but the storm locks still hold
		var r3 := region_at(p)
		if not unlocked(r3) and _rect_dist(r3, p) < 60.0:
			ship.position = before; ship.speed = -ship.speed * 0.3; ui.toast("The crew refuses to sail into the storm.")
		elif r3 != cur_region and _rect_dist(r3, p) <= 0.0: cur_region = r3
		_stream(p)
	elif in_cave == "":
		# Wreck Reef no-go ring for the galleon (skiff-only shallows) and the drifting icebergs
		var reef := _v3(M.s1.props.wreck_reef.pos)
		if ship.kind == "galleon" and p.distance_to(Vector2(reef.x, reef.z)) < 95.0:
			var o := (p - Vector2(reef.x, reef.z)).normalized() * 95.0 + Vector2(reef.x, reef.z); ship.position = Vector3(o.x, 0, o.y); ship.speed *= 0.3
		for cw in causeways():   # test 36: Beth's stage-5 causeways sit ~0.3 m above the water: hulls never pass through them
			var a2 := Vector2(cw[0].x, cw[0].z); var b2 := Vector2(cw[1].x, cw[1].z); var ab := b2 - a2
			var q := a2 + ab * clampf((p - a2).dot(ab) / maxf(ab.length_squared(), 0.001), 0.0, 1.0)
			var rr2 := 9.0 if ship.kind == "galleon" else 4.0
			if p.distance_to(q) < rr2:
				var o3 := q + ((p - q).normalized() if p.distance_to(q) > 0.01 else ab.orthogonal().normalized()) * rr2
				ship.position = Vector3(o3.x, 0, o3.y); ship.speed *= 0.3; p = o3
		for b in bergs:
			var bp := Vector2(b.node.position.x, b.node.position.z); var rr: float = b.r + (8.0 if ship.kind == "galleon" else 3.0)
			if p.distance_to(bp) < rr:
				var o2 := bp + (p - bp).normalized() * rr; ship.position = Vector3(o2.x, 0, o2.y); ship.speed *= 0.3
		var r2 := region_at(p)
		if not unlocked(r2) and _rect_dist(r2, p) < 60.0:
			ship.position = before; ship.speed = -ship.speed * 0.3; ui.toast("The crew refuses to sail into the storm.")
		elif r2 != cur_region and _rect_dist(r2, p) <= 0.0: cur_region = r2
		_stream(p)
	# the hero rides on deck; main's camera follows the hero, so he faces the bow
	var deck := 2.78 if ship.kind == "galleon" else 0.62   # test 33: skiff floor (model y 0.25) raised above the swell
	m.hero.global_position = ship.global_position + ship.global_basis * Vector3(0, deck + ship.vis.position.y - TwShip.MODEL[ship.kind][1], -4.0 if ship.kind == "galleon" else -1.0)
	m.hero.velocity = Vector3.ZERO; m.hero_vis.rotation.y = ship.heading + PI
	if m.party and m.party.get("rig"): m.party.rig.set_move_mps(0.0)
	seat_crew()
	water.global_position = Vector3(snappedf(m.cam.global_position.x, 8.0), 0.0, snappedf(m.cam.global_position.z, 8.0))
	water.material_override = _water_mat(cur_region)
	water.visible = in_cave == ""
	_tick_bergs(dt)
	_contexts()
func _tick_bergs(dt: float) -> void:
	for b in bergs:
		var n: Node3D = b.node; var d: Vector2 = b.dir
		var np: Vector2 = Vector2(n.position.x, n.position.z) + d * float(b.mps) * dt
		if shore_m(np + d * b.r) < 40.0: b.dir = -d   # bounce off the shore (DM < 40)
		else: n.position.x = np.x; n.position.z = np.y
		n.rotation.y += b.spin * dt
		n.position.y = ship.wave_h(Vector2(n.global_position.x, n.global_position.z), ship.bob_t) * 0.3 if ship else 0.0

func _contexts() -> void:
	var p := Vector2(ship.position.x, ship.position.z)
	if in_cave == "-": return
	if in_cave != "":
		var cell: Node3D = cells[in_cave]; var lp := cell.to_local(ship.global_position)
		if lp.z > 8.0: _cave_exit()
		ui.set_prompt("", Callable()); return
	var P2: Dictionary = M.s2.props
	for cave in CAVES:
		var q: Dictionary = P2[CAVES[cave]]
		var to := Vector2(q.pos[0], q.pos[2]) - p
		if to.length() < 30.0 and Time.get_ticks_msec() > cave_cd:
			if ship.kind == "skiff" and to.normalized().dot(Vector2(sin(ship.heading), cos(ship.heading))) > 0.4:
				if not can_dive_caves():   # quests-test: cave diving is Brynn's ability
					ui.toast("Only a diver knows the way into the sea caves. Find Brynn at Saltglass Landing.")
					ship.speed = -absf(ship.speed) * 0.5; cave_cd = Time.get_ticks_msec() + 2500; return
				_cave_enter(cave); return
			ui.toast("Only the skiff fits in there.")
	var dv := _v3(P2.sunken_ward.dive_buoy)
	if p.distance_to(Vector2(dv.x, dv.z)) < float(P2.sunken_ward.ring_radius) and absf(ship.speed) < 3.0:
		ui.set_prompt("Dive", dive); return
	for cave in CAVES:   # skiff launch / recovery at the white skiff buoys
		var q2: Dictionary = P2[CAVES[cave]]; var ex: Array = clear_exit(_v3(q2.pos), float(q2.yaw))
		if p.distance_to(Vector2(ex[0].x, ex[0].z)) < 25.0 and absf(ship.speed) < 3.0:
			if ship.kind == "galleon": ui.set_prompt("Launch skiff", func(): _swap("skiff")); return
			if ships.has("galleon") and ships.galleon.position.distance_to(ship.position) < 60.0: ui.set_prompt("Board galleon", func(): _swap("galleon")); return
	if p.distance_to(Vector2(1300, 300)) < 60.0 and absf(ship.speed) < 3.0 and ship.alt <= 0.5 and ship.kind == "galleon":   # test 34: mainland Tidewrack pier
		ui.set_prompt("Go ashore", func(): ui.fade(leave_to_harbour)); return
	var gh := _v3(M.s1.props.gullhaven.anchor)
	var ln := "" if p.distance_to(Vector2(gh.x, gh.z)) < 20.0 else landing_near(p, 40.0)   # right at the Gullhaven anchor: Shipwright wins
	if ln != "" and absf(ship.speed) < 3.0 and ship.alt <= 0.5:
		_port_check(false); ui.set_prompt("Go ashore", func(): go_ashore(ln)); return
	if _port_check(false): return
	ui.set_prompt("", Callable())
func _swap(kind: String) -> void:
	var at := ship.position + ship.global_basis.x * (14.0 if kind == "skiff" else 0.0)
	if kind == "galleon": at = ships.galleon.position
	ui.fade(func(): _board(kind, at, ship.heading))

# ---------------------------------------------------------------- ports, charts, shipwright
func ports() -> Dictionary:
	return {"tidewrack": ["Tidewrack pier", null, "A"],
		"gullhaven": ["Gullhaven", _v3(M.s1.props.gullhaven.anchor), "A"],
		"saltglass": ["Saltglass Landing", _v3(M.s2.props.saltglass_landing.anchor), "B"],
		"frostreach": ["Frostreach Ice Dock", _v3(M.s4.props.frostreach_ice_dock.anchor), "frost"],
		"vent": ["Vent Harbour", _v3(M.s4.props.vent_harbour.anchor), "ash"]}
func _port_check(_first: bool) -> bool:
	if ship == null: return false
	var P := ports()
	for k in P:
		if P[k][1] == null: continue
		if Vector2(ship.position.x, ship.position.z).distance_to(Vector2(P[k][1].x, P[k][1].z)) < 45.0 and absf(ship.speed) < 3.0:
			if not save.discovered_ports.has(k): save.discovered_ports.append(k); write_save(); ui.toast("%s added to the Harbour Charts." % P[k][0])
			if k == "gullhaven": ui.set_prompt("Shipwright", ui.open_shipwright); return true
	return false
func chart_travel(k: String) -> String:
	var P := ports()
	if not save.discovered_ports.has(k): return "Not charted yet."
	if in_cave != "" or diving: return "Not from here."
	if not unlocked(P[k][2]): return "That sea is closed by the storm."
	if is_night() and not can_sail_night(): return "Too dark to chart a course at night. You need a navigator."
	var fee := 0 if int(save.galleon_tier) >= 2 else 50
	var st: Dictionary = m.get_tree().root.get_node("VSave").state
	if int(st.get("gold", 0)) < fee: return "Not enough gold (%d)." % fee
	st.gold = int(st.gold) - fee; write_save()
	if k == "tidewrack": ui.fade(leave_to_harbour); return ""
	ui.fade(func(): _board("galleon", P[k][1], ship.heading); cur_region = P[k][2]; _stream(Vector2(P[k][1].x, P[k][1].z)), 3.2)   # "sails filling"
	return ""
const COST := {1: [400, {"Driftwood": 10}], 2: [1500, {"Coil Scale": 6, "Saltglass": 4}], 3: [4000, {"Stormsilk Bolt": 1, "Glasswyrm Shard": 3}]}
## test 33 (boss: "We should be allowed to upgrade our ships too"): Owner and the server-verified CoOwner
## upgrade their OWN ship free (no boss wins, gold or items). Role comes only from Cheats.role(), never the caller.
func free_upgrade() -> bool:
	if unlock_all: return true
	var ch = m.get("cheats")
	if ch == null: return false
	var r: String = ch.role()
	return r == "owner" or (r == "coowner" and ch.allowed("ship_upgrade", r))
func upgrade(kind: String) -> String:
	var t := int(save.get(kind + "_tier", 0)) + 1
	if t > 3: return "Fully upgraded."
	var free := free_upgrade()
	if t == 2 and not bool(save.coil_beaten) and not free: return "Needs the Brinecrown Coil beaten."
	if t == 3 and not bool(save.get("glasswyrm_beaten", false)) and not free: return "Needs the Glasswyrm beaten."
	var st: Dictionary = m.get_tree().root.get_node("VSave").state; var c: Array = COST[t]; var items: Dictionary = save.get("items", {})
	if not free:
		if int(st.get("gold", 0)) < c[0]: return "Needs %d gold." % c[0]
		for it in c[1]:
			if int(items.get(it, 0)) < c[1][it]: return "Needs %d %s." % [c[1][it], it]
		st.gold = int(st.gold) - c[0]
		for it in c[1]: items[it] = int(items[it]) - c[1][it]
	save[kind + "_tier"] = t; write_save()
	if ships.has(kind): ships[kind].set_tier(t)
	return ""

# ---------------------------------------------------------------- caves (Stage 3 cells)
func _cell(cave: String) -> Node3D:
	if cells.has(cave): return cells[cave]
	var idx := CAVES.keys().find(cave); var cell := Node3D.new(); cell.name = "Cave_" + cave; add_child(cell)
	cell.position = CELL_BASE + Vector3(0, 0, idx * 800.0)
	var D := R + "stage3/meshes/cave_%s_" % cave
	for part in ["shell", "glow", "props", "water", "portal"]:
		var f: String = D + part + ("_lod1.glb" if not high() and ResourceLoader.exists(D + part + "_lod1.glb") else ".glb")
		var v: Node3D = load(f).instantiate(); cell.add_child(v)
		var mat: Material
		match part:
			"glow": mat = _sh("stage3/shaders/glow_vc.gdshader")
			"water": mat = _sh("stage3/shaders/cave_water.gdshader")
			"portal": mat = _sh("stage3/shaders/cave_portal.gdshader")
			_: var s := StandardMaterial3D.new(); s.vertex_color_use_as_albedo = true; s.roughness = 0.9; s.cull_mode = BaseMaterial3D.CULL_DISABLED; mat = s
		for mi: MeshInstance3D in v.find_children("*", "MeshInstance3D", true, false):
			mi.material_override = mat; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var col: Node3D = load(D + "col.glb").instantiate()
	for mi: MeshInstance3D in col.find_children("*", "MeshInstance3D", true, false):
		var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); cs.shape = mi.mesh.create_trimesh_shape(); sb.add_child(cs); cell.add_child(sb); sb.transform = _local_xf(mi, col)
	col.free()
	var lights: Array = M.s3.caves[cave].get("lights", [])
	for i in mini(6, lights.size()):   # README: <= 6 OmniLights, energy 14, range 50, no shadows
		var o := OmniLight3D.new(); o.light_energy = 14.0; o.omni_range = 50.0; o.shadow_enabled = false; o.light_color = Color(0.6, 0.85, 0.95)
		cell.add_child(o); o.position = _v3(lights[i]) + Vector3(0, 6, 0)
	cell.visible = false; cells[cave] = cell; return cell
func _cave_enter(cave: String) -> void:
	in_cave = "-"
	ui.fade(func():
		var cell := _cell(cave); cell.visible = true; in_cave = cave
		ship.position = cell.position + Vector3(0, 0, -6.0); ship.heading = PI; ship.speed = 2.0   # into the cell (-Z)
		m.cam.environment = cave_env
		for id in regions: if regions[id].state == 2: regions[id].node.visible = false)
func _cave_exit() -> void:
	var cave := in_cave; in_cave = "-"
	ui.fade(func():
		cells[cave].visible = false; m.cam.environment = null
		for id in regions: if regions[id].state == 2: regions[id].node.visible = true
		var q: Dictionary = M.s2.props[CAVES[cave]]; var ex := clear_exit(_v3(q.pos), float(q.yaw))
		ship.position = ex[0]; ship.heading = ex[1]; ship.speed = 1.0; in_cave = ""; cave_cd = Time.get_ticks_msec() + 5000)

# ---------------------------------------------------------------- Sunken Ward dive
func dive() -> void:
	ui.fade(func():
		if ward == null: _build_ward()
		ward.visible = true; diving = true
		var c := _v3(M.s2.props.sunken_ward.dive_buoy)
		m.hero.global_position = global_transform * (c + Vector3(0, -6, 20)); m.hero.collision_layer = 1; m.hero.collision_mask = 1
		m.cam.environment = under_env)
func _build_ward() -> void:
	ward = Node3D.new(); ward.name = "SunkenWard"; add_child(ward)
	var D := R + "stage3/meshes/"
	for p in [["sw_seabed", "seabed_caustics"], ["sw_buildings", "seabed_caustics"], ["sw_landmarks", "seabed_caustics"], ["sw_rubble", "seabed_caustics"],
			["sw_kelp", "kelp_sway"], ["sw_light_shafts", "light_shaft"], ["sw_surface_under", "surface_under"]]:
		var f: String = D + p[0] + ("_lod1.glb" if not high() and ResourceLoader.exists(D + p[0] + "_lod1.glb") else ".glb")
		var v: Node3D = load(f).instantiate(); ward.add_child(v); var mat := _sh("stage3/shaders/%s.gdshader" % p[1])
		for mi: MeshInstance3D in v.find_children("*", "MeshInstance3D", true, false):
			mi.material_override = mat; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var col: Node3D = load(D + "sw_seabed_col.glb").instantiate()
	for mi: MeshInstance3D in col.find_children("*", "MeshInstance3D", true, false):
		var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); cs.shape = mi.mesh.create_trimesh_shape(); sb.add_child(cs); ward.add_child(sb); sb.transform = _local_xf(mi, col)
	col.free()
func _swim(inp: Vector2, dt: float) -> void:
	var h: CharacterBody3D = m.hero; var yaw: float = m.yaw; var pitch: float = m.pitch
	var fwd := Vector3(-sin(yaw) * cos(pitch), sin(pitch), -cos(yaw) * cos(pitch)); var right := Vector3(cos(yaw), 0, -sin(yaw))
	var dir := right * inp.x + fwd * -inp.y
	h.velocity = dir.limit_length(1.0) * 4.0; h.move_and_slide()
	if dir.length() > 0.1: m.hero_vis.rotation.y = atan2(-dir.x, -dir.z)
	if m.party and m.party.get("rig"): m.party.rig.set_flight(true, Vector3(0, 0, -dir.length() * 4.0))
	ui.set_prompt("Surface", surface)
	if to_local(h.global_position).y > -0.6: surface()
func surface() -> void:
	if not diving: return
	diving = false
	ui.fade(func():
		ward.visible = false; m.cam.environment = null
		if m.party and m.party.get("rig"): m.party.rig.set_flight(false)
		m.hero.collision_layer = 0; m.hero.collision_mask = 0)

# ---------------------------------------------------------------- test 34: landings (boss Oct 31: "the ship needs to allow us
## to have either ports or locations to get off the ship to explore"). tidewrack/landings.json (tests/landing_gen.gd, real
## colliders): every port + every island/coast with content has a shore point on walkable ground (20 m inland checked) and a
## moor point in galleon-safe water. Near the moor -> "Go ashore": the ship parks level at the moor (parallel to the shore),
## the hero + Pip + companions walk ashore on a pier; near the pier head -> "Board ship" puts everyone back on deck.
## Ashore safety: never fall through / get stuck: last safe floor spot is kept; water, a fall or 1.5 s without floor -> back.
var landings := {}
var ashore := ""
var _safe := Vector3.ZERO
var _air_t := 0.0
var _stuck_t := 0.0
func _landings() -> Dictionary:
	if landings.is_empty():
		var d = JSON.parse_string(FileAccess.get_file_as_string(R + "landings.json"))
		if d is Dictionary: landings = d
	return landings
func landing(k: String) -> Dictionary: return _landings().get(k, {})
func landing_near(p: Vector2, r: float) -> String:
	for k in _landings():
		var L: Dictionary = landings[k]
		if unlocked(L.region) and p.distance_to(Vector2(L.moor[0], L.moor[2])) < r: return k
	return ""
func _inland(L: Dictionary) -> Vector3: return Vector3(L.inland[0], 0, L.inland[1]).normalized()
func moor_heading(L: Dictionary) -> float:
	var d := _inland(L); return atan2(-d.z, d.x)   # bow along the shore (broadside to the pier)
func pier_head(L: Dictionary) -> Vector3:
	return _v3(L.shore) + Vector3(0, 0.2, 0)
func pier_foot(L: Dictionary) -> Vector3:
	return _v3(L.moor) + _inland(L) * (4.8 if ship == null or ship.kind == "galleon" else 1.8) + Vector3(0, 1.0, 0)
func _place_landings(id: String, root: Node3D) -> void:
	var wood := StandardMaterial3D.new(); wood.albedo_color = Color(0.45, 0.31, 0.19); wood.roughness = 0.9
	var lamp := StandardMaterial3D.new(); lamp.albedo_color = Color(1.0, 0.8, 0.4); lamp.emission_enabled = true; lamp.emission = Color(1.0, 0.75, 0.35); lamp.emission_energy_multiplier = 3.0
	for k in _landings():
		var L: Dictionary = landings[k]
		if L.region != id: continue
		var n := Node3D.new(); n.name = "Landing_" + k; root.add_child(n)
		var a := _v3(L.moor) + _inland(L) * 3.0 + Vector3(0, 1.0, 0); var b := pier_head(L) - Vector3(0, 0.2, 0) + _inland(L) * 1.5
		var hz := Vector2(b.x - a.x, b.z - a.z).length()   # test 36: steep landings (up to 49 deg) -> raise the sea end on taller piles so the boards are <= 18 deg (walkable)
		a.y = maxf(a.y, b.y - hz * tan(deg_to_rad(11.0)))   # test 37: 18 -> 11 deg (Beth walker failed 6 landings at 18)
		var len := a.distance_to(b); var mid := (a + b) * 0.5
		var mi := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = Vector3(3.2, 0.3, len); mi.mesh = bm; mi.material_override = wood; n.add_child(mi)
		mi.look_at_from_position(n.to_global(mid), n.to_global(b), Vector3.UP)   # test 37: was sea-local coords as GLOBAL -> boards sat 20 km north (OFF), never under the pier
		var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var bs := BoxShape3D.new(); bs.size = bm.size; cs.shape = bs; sb.add_child(cs); n.add_child(sb); sb.transform = mi.transform
		for t in [0.0, 0.33, 0.66]:   # piles down into the sea
			var pp := a.lerp(b, t)
			if pp.y < 0.5 and t > 0.0: continue
			var pm := MeshInstance3D.new(); var cy := CylinderMesh.new(); cy.top_radius = 0.22; cy.bottom_radius = 0.22; cy.height = pp.y + 3.0; pm.mesh = cy; pm.material_override = wood; n.add_child(pm)
			pm.position = pp - Vector3(0, cy.height * 0.5, 0) + _inland(L).cross(Vector3.UP) * 1.5
		var post := MeshInstance3D.new(); var pc := CylinderMesh.new(); pc.top_radius = 0.15; pc.bottom_radius = 0.2; pc.height = 4.0; post.mesh = pc; post.material_override = wood; n.add_child(post)
		post.position = pier_head(L) + Vector3(0, 2.0, 0) + _inland(L).cross(Vector3.UP) * 2.0
		var lb := MeshInstance3D.new(); var sp := SphereMesh.new(); sp.radius = 0.4; sp.height = 0.8; lb.mesh = sp; lb.material_override = lamp; n.add_child(lb); lb.position = post.position + Vector3(0, 2.2, 0)
		var ol := OmniLight3D.new(); ol.light_color = Color(1, 0.8, 0.45); ol.light_energy = 3.0; ol.omni_range = 14.0; n.add_child(ol); ol.position = lb.position
		var lab := Label3D.new(); lab.text = str(L.name); lab.font_size = 96; lab.billboard = BaseMaterial3D.BILLBOARD_ENABLED; lab.no_depth_test = false; lab.modulate = Color(1, 0.93, 0.7); n.add_child(lab); lab.position = lb.position + Vector3(0, 1.6, 0)
## quests-test: invisible walk-access patches (sea-local coords) where story routes snag on Beth's island colliders.
## ["deck", region, a, b, width, lift]: a thin walkable plank whose top runs a->b (+lift) over rock seams/lips;
## ["guide", region, a, b, height]: a vertical slab a->b that turns a dead corner into a funnel.
## Merge note: new const + func, called once in _build_region after _place_landings; independent of the pier boards.
const ACCESS_PATCHES := [
	# Saltglass pier stair foot: coming off the pier head (6 m west of the stair) the hero wedged in the V between the
	# stair's west cheek (x -2119.46) and the island face (normal 0.37,0,0.93). Slab along that face -> slide onto the stair.
	["guide", "B", Vector3(-2122.6, 20.3, -91.3), Vector3(-2119.42, 20.3, -93.3), 2.6],
	# ...and the island face's corner pokes ~0.4 m over the flight's west edge for its first metres: smooth wall along it
	["guide", "B", Vector3(-2119.35, 20.3, -92.9), Vector3(-2119.35, 20.3, -96.5), 3.0],
	# Saltglass plateau path to the Glass-diver's Chest (route idx 108-117): rock seams/overhang lips stopped the hero ~16 m short.
	["deck", "B", Vector3(-2206.66, 94.95, 55.73), Vector3(-2198.66, 95.58, 61.73), 5.0, 0.2],
	["deck", "B", Vector3(-2198.66, 95.58, 61.73), Vector3(-2186.66, 96.34, 67.73), 5.0, 0.2],
	["deck", "B", Vector3(-2186.66, 96.34, 67.73), Vector3(-2174.24, 96.44, 73.94), 5.0, 0.2],
]
func _access_patches(id: String, root: Node3D) -> void:
	for P in ACCESS_PATCHES:
		if P[1] != id: continue
		var a: Vector3 = P[2]; var b: Vector3 = P[3]
		var sb := StaticBody3D.new(); sb.name = "AccessPatch"; root.add_child(sb)
		var cs := CollisionShape3D.new(); var bs := BoxShape3D.new(); cs.shape = bs; sb.add_child(cs)
		if P[0] == "deck":
			var lift := Vector3(0, float(P[5]), 0)
			bs.size = Vector3(float(P[4]), 0.3, a.distance_to(b) + 1.0)
			sb.look_at_from_position(to_global((a + b) * 0.5 + lift), to_global(b + lift), Vector3.UP)
			sb.global_position -= sb.global_basis.y * 0.15
		else:
			var flat := Vector3(b.x, a.y, b.z)
			bs.size = Vector3(0.3, float(P[4]), a.distance_to(flat))
			sb.look_at_from_position(to_global((a + flat) * 0.5 + Vector3(0, float(P[4]) * 0.5, 0)), to_global(flat + Vector3(0, float(P[4]) * 0.5, 0)), Vector3.UP)
func _region_ready(id: String) -> bool: return regions.get(id, {}).get("state", 0) == 2
func go_ashore(k: String) -> void:
	var L := landing(k)
	if L.is_empty() or diving or in_cave != "": return
	ui.fade(func():
		ship.alt = 0.0; ship.speed = 0.0; ship.throttle = 0.0; ship.heading = moor_heading(L); ship.position = Vector3(L.moor[0], 0.0, L.moor[2])
		ship.rotation = Vector3(0, ship.heading, 0); ship.vis.position.y = TwShip.MODEL[ship.kind][1]   # parked dead level, no bob
		ashore = k; _air_t = 0.0; _stuck_t = 0.0
		var h: CharacterBody3D = m.hero
		h.collision_layer = 1; h.collision_mask = 1; h.velocity = Vector3.ZERO
		h.global_position = to_global(pier_head(L) + Vector3(0, 0.6, 0)); _safe = pier_head(L) + Vector3(0, 0.6, 0)
		m.yaw = atan2(-_inland(L).x, -_inland(L).z) + PI; m.hero_vis.rotation.y = atan2(-_inland(L).x, -_inland(L).z)
		if m.party: m.party.ground_snap = func(w: Vector3) -> float: return floor_y(w)
		unseat_crew()
		if m.pip: m.pip.global_position = h.global_position + Vector3(1, 0, 1)
		snap_crew()
		if not save.discovered_ports.has(k) and ports().has(k): save.discovered_ports.append(k); write_save()
		ui.set_prompt("", Callable()); ui.toast("Ashore at %s." % L.name)
		went_ashore.emit(k))
func board_ship() -> void:
	if ashore == "": return
	ui.fade(func():
		var was := ashore
		ashore = ""
		left_shore.emit(was)
		if m.party: m.party.ground_snap = Callable()
		m.hero.collision_layer = 0; m.hero.collision_mask = 0; m.hero.velocity = Vector3.ZERO
		seat_crew(); ui.set_prompt("", Callable()); ui.toast("All aboard."))
func _ray_floor(lp: Vector3, up := 3.0, down := 40.0) -> Dictionary:
	var w := to_global(lp); var q := PhysicsRayQueryParameters3D.create(w + Vector3(0, up, 0), w - Vector3(0, down, 0), 1)
	q.exclude = [m.hero.get_rid()] + ships.values().map(func(s): return s.get_rid())
	return m.get_world_3d().direct_space_state.intersect_ray(q)
func _walk(inp: Vector2, dt: float) -> void:
	var h: CharacterBody3D = m.hero; var yaw: float = m.yaw
	var fwd := Vector3(-sin(yaw), 0, -cos(yaw)); var right := Vector3(cos(yaw), 0, -sin(yaw))
	var dir := right * inp.x + fwd * -inp.y
	var ch = m.get("cheats"); var mul := 1.0
	if ch != null: mul = clampf(float(ch.flags.get("speed", 1.0)), 0.1, 50.0)
	var spd: float = float(m.move_speed) * mul * clampf(inp.length(), 0.0, 1.0)
	if dir.length() > 0.05: dir = dir.normalized()
	h.velocity.x = dir.x * spd; h.velocity.z = dir.z * spd
	h.velocity.y = -1.0 if h.is_on_floor() else h.velocity.y - 20.0 * dt
	if m.get("jump_req") and h.is_on_floor(): h.velocity.y = float(m.JUMP_V); m.jump_req = false
	h.floor_snap_length = 0.6; h.floor_max_angle = deg_to_rad(50.0)
	var before := h.global_position
	h.move_and_slide()
	_step_up(h, before, dir * spd * dt)
	if spd > 0.1: m.hero_vis.rotation.y = lerp_angle(m.hero_vis.rotation.y, atan2(-dir.x, -dir.z), 10 * dt)
	var lp := to_local(h.global_position)
	# safety: on floor -> remember; in the sea / falling / no floor -> back to the last safe spot
	if h.is_on_floor():
		_air_t = 0.0
		if lp.y > 0.25: _safe = lp + Vector3(0, 0.3, 0)
	else: _air_t += dt
	var moved := h.global_position.distance_to(before)
	_stuck_t = _stuck_t + dt if spd > 0.5 and moved < spd * dt * 0.05 else 0.0
	if _air_t > 1.5 and not _ray_floor(lp, 0.5, 4.0).is_empty(): _air_t = 0.0   # sliding on a steep bit right above the ground: not lost
	if lp.y < -0.2 or _air_t > 1.5 or _stuck_t > 2.0:
		var f := _ray_floor(_safe)
		h.global_position = (f.position + Vector3(0, 0.3, 0)) if f else to_global(pier_head(landing(ashore)) + Vector3(0, 0.6, 0))
		print("ASHORE reset y=%.2f air=%.2f stuck=%.2f at %s" % [lp.y, _air_t, _stuck_t, str(lp)])
		h.velocity = Vector3.ZERO; _air_t = 0.0; _stuck_t = 0.0
		ui.toast("Careful - back on solid ground.")
	# Pip trots along on the real ground
	if m.pip:
		var tgt: Vector3 = h.global_position + m.hero_vis.global_transform.basis.z * 1.3 + m.hero_vis.global_transform.basis.x * 0.7
		var dp: Vector3 = tgt - m.pip.global_position; dp.y = 0
		if dp.length() > 0.3: m.pip.global_position += dp * minf(1.0, 4.0 * dt); m.pip.rotation.y = lerp_angle(m.pip.rotation.y, atan2(-dp.x, -dp.z), 8 * dt)
		var pf := _ray_floor(to_local(m.pip.global_position), 3.0, 10.0)
		m.pip.global_position.y = pf.position.y if pf else h.global_position.y
	water.global_position = Vector3(snappedf(m.cam.global_position.x, 8.0), 0.0, snappedf(m.cam.global_position.z, 8.0)) + Vector3(0, global_position.y, 0)
	_stream(Vector2(lp.x, lp.z))
	var L := landing(ashore)
	var qp: Array = quest_prompt.call(lp) if quest_prompt.is_valid() else []
	if not qp.is_empty(): ui.set_prompt(qp[0], qp[1])
	elif lp.distance_to(pier_head(L)) < 10.0: ui.set_prompt("Board ship", board_ship)
	elif ashore == "gullhaven" and Vector2(lp.x, lp.z).distance_to(Vector2(M.s1.props.gullhaven.anchor[0], M.s1.props.gullhaven.anchor[2])) < 90.0: ui.set_prompt("Shipwright", ui.open_shipwright)
	else: ui.set_prompt("", Callable())
## quests-test: stair/lip step-up ashore. CharacterBody3D can't climb a vertical edge, so a hero walking into a small lip
## (Saltglass pier-stair foot cheek, stair-top seam, rock seams on the plateau path to the Glass-diver's Chest) stalled.
## Blocked while pushing on the floor -> try lifting up to 0.55 m and moving on; only if there is head room and the spot
## ahead is free. Gravity/floor snap settle the hero next frame. Never fires mid-air, so no wall climbing.
const STEP_UP := [0.2, 0.35, 0.55]
func _step_up(h: CharacterBody3D, before: Vector3, want: Vector3) -> void:
	if want.length() < 0.001 or not (h.is_on_floor() or _air_t < 0.1): return
	var got := Vector2(h.global_position.x - before.x, h.global_position.z - before.z).length()
	if got > want.length() * 0.6: return
	var fwd := want.normalized() * maxf(want.length(), 0.08)
	for up in STEP_UP:
		var t := h.global_transform
		if h.test_move(t, Vector3(0, up, 0)):
			# no head room, or the capsule sank a few cm into a sloped seam (seen on the Saltglass Lookout path): if the
			# spot `up` higher is free, lift there (unstick); otherwise give up
			if _shape_free(h, t.translated(Vector3(0, up, 0))): h.global_position.y += up; h.velocity.y = 0.0
			return
		var t2 := t.translated(Vector3(0, up, 0))
		if h.test_move(t2, fwd): continue                      # still blocked at this height
		var t3 := t2.translated(fwd)
		var down := PhysicsTestMotionResult3D.new()
		if not h.test_move(t3, Vector3(0, -(up + 0.3), 0)): continue   # must land on something within the step (no stepping off ledges)
		h.global_position = t3.origin; h.velocity.y = 0.0
		return
# ---------------------------------------------------------------- quests-test: crew ship abilities (story flags in VSave.state.story)
const NIGHT_CAP := 3.0   # m/s: without a navigator the crew only creeps along at night
var _night_warned := 0
func story_flag(k: String) -> bool:
	var st = m.get_tree().root.get_node("VSave").state.get("story", {})
	return st is Dictionary and bool(st.get("flags", {}).get(k, false))
func is_night() -> bool: return float(m.tod) >= 20.0 or float(m.tod) < 5.0
## Wren (night_sailing), or the story's own night sail to Lantern Rock (the harbourmaster's chart), or the Owner
func can_sail_night() -> bool:
	if unlock_all or story_flag("night_sailing"): return true
	var q := m.get_tree().root.get_node_or_null("Quests")
	return q != null and q.has_method("night_sail_active") and q.night_sail_active()
func can_dive_caves() -> bool: return unlock_all or story_flag("cave_diving")
func _night_cap() -> void:
	if in_cave != "" or not is_night() or can_sail_night() or absf(ship.speed) <= NIGHT_CAP: return
	ship.speed = signf(ship.speed) * NIGHT_CAP
	if Time.get_ticks_msec() > _night_warned:
		_night_warned = Time.get_ticks_msec() + 6000; ui.toast("Too dark to sail at speed. You need a navigator.")
## Wren aboard: switch day/night at sea (TwUi "Night"/"Day" button)
func toggle_night() -> void:
	if not story_flag("night_sailing") and not unlock_all: return
	m._set_time(11.0 if is_night() else 22.5)
	ui.toast("Wren reads the stars: sailing by night." if is_night() else "Dawn breaks.")
func _shape_free(h: CharacterBody3D, xf: Transform3D) -> bool:
	var cs: CollisionShape3D = h.get_child(0)
	var q := PhysicsShapeQueryParameters3D.new(); q.shape = cs.shape; q.transform = xf * cs.transform; q.collision_mask = h.collision_mask
	q.exclude = [h.get_rid()]; q.margin = 0.02
	return m.get_world_3d().direct_space_state.intersect_shape(q, 1).is_empty()
func sailing() -> bool: return active and ashore == "" and not diving
