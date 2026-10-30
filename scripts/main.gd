extends Node3D
# Varnethryl Godot test 2: main town from buildings.js BUILDING_DEFS (cx,cz * PK=2.8), Beth r3 art,
# terrain, day/night, quality tiers Low/Medium/High/Ultra (Forward+).

const PK := 2.8
const CITY_HALF := 185.0
## test 33: the HUD test number comes from ONE setting (project.godot application/config/test_build), bumped per build;
## run_tests checks it == export_presets version/code - 1.
var VERSION: String = str(ProjectSettings.get_setting("application/config/test_build", "?"))
## test 11 layout (boss: buildings on the gate road / walkways through buildings): positions in METRES, solved by
## /workspace/layout/solve.py from Beth's collision footprints (+1 m margin): every building sits beside a STREET with its
## front (+Z, all door_points) facing it, a short spur path from each front door to the street, nothing on a street,
## no overlaps, walls/gates clear (|x|,|z| <= 172). Closest free slot to the v1.5.33 spot (BUILDING_DEFS * 2.8).
## The barn is gone: Beth's farmhouse_tripo is the whole farmstead; its barn doors lead into the barn interior.
const DEFS := [
	["colosseum",118.0,100.5,PI,"Colosseum"], ["keep",-29.0,-105.0,PI/2,"Castle Keep"], ["farmhouse",-290.0,-288.0,-PI/2,"Farmhouse"],
	["temple",129.5,-22.0,PI/2,"Temple"], ["mage",-124.0,-87.5,0.0,"Arcane Academy"], ["stables",-59.1,108.0,-PI/2,"Stables"],
	["observatory",130.0,-149.0,0.0,"Observatory"], ["windmill",56.0,112.8,0.0,"Windmill"], ["training",127.0,30.0,PI/2,"Training Hall"],
	["library",-57.5,-56.0,-PI/2,"Grand Library"], ["treasury",114.0,-84.0,0.0,"Treasury"], ["market",-63.2,-22.6,0.0,"Market Provisioner"],
	["thieves",-101.2,13.6,PI,"Thieves' Den"], ["townhall",59.5,-84.0,PI/2,"Town Hall"], ["guildhall",-14.0,-54.5,PI,"Guild Hall"],
	["crypt",120.0,-114.0,PI,"Crypt"], ["inn",59.5,-23.4,PI/2,"Inn"], ["bakery",-64.2,56.0,0.0,"Bakery"],
	["smithy",62.5,20.0,PI/2,"Blacksmith"], ["house3",-25.4,83.0,PI,"Village House"], ["apothecary",-62.5,25.4,-PI/2,"Apothecary"],
	["house1",-25.7,58.5,0.0,"Village House"], ["house2",25.0,57.5,0.0,"Village House"], ["house4",26.0,80.5,PI,"Village House"],
]
## Test 6: Beth's Godot "card2" buildings (metres, footprint-centred, +Z front, shared 2048 atlas) replace these.
const CARD2 := {"guildhall": "guildhall", "library": "library", "townhall": "townhall", "mage": "mage_academy", "treasury": "treasury",
	"keep": "keep", "observatory": "observatory", "crypt": "crypt", "market": "market", "apothecary": "apothecary", "bakery": "bakery",
	"inn": "inn", "smithy": "smithy", "temple": "temple", "training": "training_hall", "colosseum": "colosseum", "thieves": "thieves_den",
	"house1": "house1", "house2": "house2", "house3": "house3", "house4": "house4",
	"farmhouse": "tripo/bld_farmhouse_tripo"}
## Heavy pieces ship and render LOD1 as their best tier (phone High): colosseum, library, mage academy, Tripo models.
func _add_col(path: String, pos: Vector3, rot: float) -> Node3D:
	var c: Node3D = load(path).instantiate(); c.position = pos; c.rotation.y = rot; add_child(c)
	for m in _meshes(c, []): m.visible = false
	return c

static var _c2_top := {}
## index.json phone_high_lod: buildings whose best phone tier is lod1 (no High file is shipped for them).
static func card2_lod1_top(id: String) -> bool:
	if String(CARD2.get(id, "")).begins_with("tripo/"): return true
	if _c2_top.is_empty():
		var j = JSON.parse_string(FileAccess.get_file_as_string("res://assets/card2/index.json"))
		for b in j.get("buildings", []): _c2_top[str(b.id)] = str(b.get("phone_high_lod", "high")) == "lod1"
	return _c2_top.get(String(CARD2.get(id, "")), false)

static var _c2_doors := {}
## Beth's buildings/index.json door_points (threshold in the building's local space) for the card2/Tripo
## exteriors, so interior door triggers sit in the real door openings of the _col.glb walls.
static func card2_door(id: String) -> Variant:
	if not CARD2.has(id): return null
	if _c2_doors.is_empty():
		var j = JSON.parse_string(FileAccess.get_file_as_string("res://assets/card2/index.json"))
		for b in (j.get("buildings", []) + j.get("tripo_buildings", [])):
			if b.get("door_points", []).size() > 0:
				var p: Array = b.door_points[0].pos; _c2_doors[str(b.id)] = Vector3(p[0], p[1], p[2])
	var key: String = String(CARD2[id]).get_file().trim_prefix("bld_")
	return _c2_doors.get(key, null)

## every front door of a card2/Tripo building (building-local), from index.json door_points (z > 0 = front)
static var _c2_all_doors := {}
static func card2_doors(id: String) -> Array:
	if not CARD2.has(id): return []
	if _c2_all_doors.is_empty():
		var j = JSON.parse_string(FileAccess.get_file_as_string("res://assets/card2/index.json"))
		for b in (j.get("buildings", []) + j.get("tripo_buildings", [])):
			var arr := []
			for d in b.get("door_points", []):
				if float(d.pos[2]) > 0.0: arr.append(Vector3(d.pos[0], d.pos[1], d.pos[2]))
			_c2_all_doors[str(b.id)] = arr
	return _c2_all_doors.get(String(CARD2[id]).get_file().trim_prefix("bld_"), [])

static func _world_rect(a: AABB, pos: Vector3, rot: float) -> Rect2:
	var bs := Basis(Vector3.UP, rot); var r := Rect2(); var first := true
	for lx in [a.position.x, a.end.x]:
		for lz in [a.position.z, a.end.z]:
			var w: Vector3 = pos + bs * Vector3(lx, 0, lz)
			if first: r = Rect2(w.x, w.z, 0, 0); first = false
			else: r = r.expand(Vector2(w.x, w.z))
	return r

## distance from p to the nearest in-town street edge (negative inside); plaza disc included
static func street_edge_dist(p: Vector2) -> float:
	var best := p.length() - PLAZA_R
	for r in STREETS:
		var a := Vector2(r[0], r[1]); var b := Vector2(r[2], r[3]); var ab := b - a
		var t: float = clampf((p - a).dot(ab) / maxf(ab.length_squared(), 0.001), 0.0, 1.0)
		best = minf(best, p.distance_to(a + ab * t) - float(r[4]))
	return best

static func _card2_path(id: String, suf: String) -> String:
	var v: String = CARD2[id]
	if suf == "" and card2_lod1_top(id): suf = "_lod1"
	return ("res://assets/card2/%s%s.glb" % [v, suf]) if v.begins_with("tripo/") else ("res://assets/card2/bld_%s_card2%s.glb" % [v, suf])
const CHIMNEYS := ["house1","house2","house3","house4","bakery","inn","smithy","farmhouse","thieves"]
const PORT := Vector2(-425.6, 392)
const ROADS := [
	[[0,194],[-65,204],[-145,219],[-211,220],[-269,231],[-336,269],[-387,322],[-425.6,375]],
	[[0,-194],[-10,-247],[-42,-283],[-101,-327],[-99,-391],[-68,-439],[-8,-463],[62,-446],[95,-412],[105,-360]],
	[[-558,-6],[-474,-12],[-398,-7],[-322,0],[-270,6],[-232,4],[-185,0]],
	[[-315,0],[-305,-67],[-313,-132],[-330,-203],[-366,-273],[-315,-284],[-308,-289],[-308,-297]],   # test 14: runs on to the farmstead doors
	[[185,0],[264,-3],[335,0],[421,-2],[500,0],[558,-7]],
	[[345,0],[377,62],[387,127],[354,190],[309,247],[285,311],[304,356],[269,315],[214,259],[150,225],[76,200],[0,194]],
	[[0,194],[5,265],[9,344],[0,440],[-6,558]],
	# (test 11) the in-town avenue stubs are gone: ground.gdshader draws the streets; their road mesh rendered as the
	# boss's black strip between the north gate towers (back-facing quads under CULL_DISABLED)
]
## in-town streets (test 11): [x0, z0, x1, z1, half width], axis-aligned; drawn by ground.gdshader, plus the plaza disc
## (r 36.4) and the ring road outside the walls (r 194). Buildings + door spurs are laid out against these.
const STREETS := [
	[0, -194, 0, 194, 4.5],
	[-194, 0, 194, 0, 3.6],
	[-150, -70, 150, -70, 3.0],
	[-150, 70, 150, 70, 3.0],
	[-150, -130, 150, -130, 3.0],
	[-150, 130, 150, 130, 3.0],
	[-75, -150, -75, 150, 3.0],
	[75, -150, 75, 150, 3.0],
	[-150, -150, -150, 150, 3.0],
	[150, -150, 150, 150, 3.0]]
const PLAZA_R := 36.4
const SPUR_GAP := 3.1     # m from a front door to the street edge (solver GAP 2.5 + 0.6)
var terrain_mat: ShaderMaterial
var fillers := []         # test 14: TownFillers.build() -> [{id, node, door, path, rect}]
var spurs := []           # [door Vector2, end Vector2, half width, building id]
var extra_doors := []     # second entrances that lead to their own interior (the farmstead's barn doors)
const GATES := [[Vector2(0, 1), PI, "South Gate"], [Vector2(0, -1), 0.0, "North Gate"], [Vector2(1, 0), -PI / 2, "East Gate"], [Vector2(-1, 0), PI / 2, "West Gate"]]
const TIERS := ["Low", "Medium", "High", "Ultra"]

var tier := 2
var fps_cap := 60
var f_btn: Button
var b_btn: Button
var bench_label: Label
var bench_running := false
var ft_acc := 0.0
var ft_n := 0
var ft_max := 0.0
var ft_txt := ""
var probe: ReflectionProbe
var time_mode := 0          # index into TIME_PRESETS last chosen
var speed_x := 1.0
const TIME_PRESETS := [["Morning", 7.5], ["Noon", 12.0], ["Sunset", 18.2], ["Night", 22.5]]
const DAY_SECONDS := 1200.0   # full cycle = 20 real minutes
var s_btn: Button
var tod := 10.0              # hours
var hero: CharacterBody3D
var hero_vis: Node3D
var pip: Node3D
var party: Node              # heroes/party.gd (port-heroes hook)
var move_speed := 6.0          # set per hero by Party
var cam_h := 1.7               # camera pivot height, set per hero by Party
var cam_pivot: Node3D
var cam_arm: SpringArm3D
var cam: Camera3D
var yaw := 0.0
var pitch := -0.35
var buildings := []
var gate_towers := []
var gate_lods := []
var windmill_blades := []
var plaza_glow := []
var tree_lods := []         # [mmi, lod]
var hi_terrain := []        # [node, lod]
var cur_suffix := "?"
var blockers := []           # [Vector2 center, radius]
var blades: Node3D
var hud_label: Label
var where_label: Label
var q_btn: Button
var t_btn: Button
var joy_vec := Vector2.ZERO
var joy_touch := -1
var cam_touch := -1
var joy_center := Vector2.ZERO
var joy_base: Control
var joy_knob: Control
var walk_t := 0.0
var limbs := []
var bench := false
var guards: TownGuards
var rng := RandomNumberGenerator.new()
var noise := FastNoiseLite.new()
var env: Environment
var sun: DirectionalLight3D
var interiors: InteriorManager   # res://interiors (walk-in interiors)
var sky_mat: ProceduralSkyMaterial
var emissive_mats := []
var _ext_tier := ""   # test 22: ExteriorDressing tier applied (re-scan only when it changes)
var hero_fill: OmniLight3D
var door_lights: Array[OmniLight3D] = []   # door + street lanterns; only the nearest few are on (per tier)
var _dl_t := 0.0
const DOOR_LIGHTS_MAX := [3, 5, 8, 14]      # Low, Medium, High, Ultra
const DOOR_LIGHT_RANGE := 45.0
var lamp_lights := []        # [OmniLight3D, min_tier]
var glow_mm: Array = []      # lantern glow multimeshes
var glow_mat: StandardMaterial3D
var grass_chunks := []
var fx_day := []             # [node, min_tier]
var fx_night := []
var fx_any := []
var tree_mmis := []
var terrain_lods := []       # [node, lod]
var shot_dir := "user://"
var menu_open := false
var lamp_shadow_t := 0.0
var cheats: Cheats
var world_map: WorldMap
var fly_alt := 6.0
const JUMP_H := 1.2
var JUMP_V := sqrt(2.0 * 20.0 * JUMP_H)
var jump_req := false
var jump_count := 0
var flight := false      # test 13: HUD ✈ toggles real flight; the menu "fly" cheat only unlocks the button
var landing := false
func flying_now() -> bool: return flight and bool(cheat.get("fly", false))
## test 26 (boss: Owner "standing on the water"): over the open sea the hero swims / treads water instead of walking.
func in_sea(p: Vector3) -> bool:
	return not flying_now() and p.x < SEA_COAST_X - 3.0 and p.z > SEA_NORTH_Z + 2.0 and sea_mask(p.x, p.z) > 0.5
func request_jump() -> void: jump_req = true
func set_flight(on: bool) -> void:
	if flight and not on: landing = true
	flight = on
var fly_controls: FlyControls
var net_proxy: Node
const JS_UNITS := 1.4205   # JS world units per metre (server/JS clients use world units)
var cheat := {"speed": 1.0, "fly": false, "noclip": false, "god": false}
var remotes := {}            # Net peer id -> {node, target, yaw}
var net_send_t := 0.0
var warmed := false
const MAP_RECT := Rect2(-260, -260, 520, 520)

func _ready() -> void:
	rng.seed = 1905
	noise.seed = 7; noise.frequency = 0.0035; noise.fractal_octaves = 4
	var args := OS.get_cmdline_user_args()
	bench = args.has("--bench")
	_load_settings()
	_env()
	_terrain()
	_roads()
	_fountain()
	_pond()
	_walls_and_gate()
	for d in DEFS: _building(d)
	if OS.get_environment("VARN_LITE") == "": _street_kit()   # test 17: lean world for shared-box checks
	if OS.get_environment("VARN_LITE") == "": _farm_fields()   # test 17: lean world for shared-box checks
	if OS.get_environment("VARN_NO_FILLERS") == "": fillers = TownFillers.build(self)   # test 14: rows of filler houses/shops from assets/town/fillers.json
	_streets_to_shader()
	# test 10: boss "Fix the castle and or get rid of it" - the Tripo backdrop castle reads as shredded/floating, removed
	_harbour()
	if OS.get_environment("VARN_NO_HARBOR") == "": harbor = HarborDistrict.new().build(self)
	if OS.get_environment("VARN_LITE") == "": _ships()   # test 17: lean world for shared-box checks
	sea = TidewrackSea.new(); add_child(sea); sea.setup(self)   # test 32: Beth's Tidewrack Sea (idle + hidden until you set sail)
	if OS.get_environment("VARN_LITE") == "": _dressing()   # test 17: lean world for shared-box checks
	_hi_terrain()
	if OS.get_environment("VARN_LITE") == "": _showcase()   # test 17: lean world for shared-box checks
	if OS.get_environment("VARN_LITE") == "": _foliage()   # test 17: lean world for shared-box checks
	if not args.has("--wbshots") and not args.has("--altshots") and not args.has("--roofshots") and not args.has("--wbcheck"): _grass()   # shot capture on the shared box: skip grass to save RAM
	if OS.get_environment("VARN_NO_FLOWERS") == "": TerrainFlowers.build(self)   # test 23: Beth's wildflowers (baked placement)
	if OS.get_environment("VARN_NO_TFIX2") == "": add_child(FarGrass.new()); TerrainScatter.build(self); _drop_blocking_boulders()   # test 23: far grass + foothill rocks/bushes/pebbles/farm
	_hero()
	_fx()
	_hud()
	if not bench: tier = VPrefs.tier()
	party = load("res://heroes/party.gd").new(); add_child(party); party.setup(self, not bench)
	interiors = InteriorManager.new(); add_child(interiors); interiors.setup(self)
	if not bench or OS.get_environment("BENCH_ONLY") == "flywarm": guards = TownGuards.new().setup(self, CITY_HALF, GATES); add_child(guards)   # voxel-heroes
	apply_quality()
	if not bench and volcano_quest_done(): spawn_world_boss(false)   # test 15: the world boss roams outside the walls only after the volcano quest (story)
	_hook_ui()
	if bench: _run_bench()
	else: _warm_up()
	if args.has("--wbshots"): add_child(load("res://tests/wb_shots.gd").new())
	if args.has("--altshots"): add_child(load("res://tests/alt_shots.gd").new())   # test 16
	if args.has("--roofshots"): add_child(load("res://tests/roof_shots.gd").new())   # test 17
	if args.has("--wbcheck"): add_child(load("res://tests/wb_ground_check.gd").new())   # test 17
	if args.has("--crystalcheck"): add_child(load("res://tests/crystal_reach_test.gd").new())   # test 24
	if args.has("--bouldercheck"): add_child(load("res://tests/boulder_check.gd").new())   # test 23
	if args.has("--whereshots"): add_child(load("res://tests/where_shots.gd").new())   # test 25
	if args.has("--voxclose"): add_child(load("res://tests/voxel_close.gd").new())   # test 25
	if args.has("--worldmap"): add_child(load("res://tests/worldmap_test.gd").new())   # test 33
	if args.has("--capeshots"): add_child(load("res://tests/cape_shots.gd").new())   # test 33
	if args.has("--ownershots"): add_child(load("res://tests/owner_shots.gd").new())   # test 26
	if args.has("--shiplevel"): add_child(load("res://tests/ship_level.gd").new())   # test 28
	if args.has("--shipcam"): add_child(load("res://tests/ship_cam.gd").new())   # test 29
	if args.has("--vox30"): add_child(load("res://tests/vox30_shots.gd").new())   # test 30
	if args.has("--tidewrack"): add_child(load("res://tests/tidewrack_test.gd").new())   # test 32
	if args.has("--vox31"): add_child(load("res://tests/vox31_shots.gd").new())   # test 31
	if args.has("--voxshots"): add_child(load("res://tests/voxel_shots.gd").new())   # voxel-heroes
	if args.has("--tfshots"): add_child(load("res://tests/tf_shots.gd").new())   # test 23
	if args.has("--extshots"): add_child(load("res://tests/ext_shots.gd").new())   # test 22
	if args.has("--intcheck"): add_child(load("res://tests/interior_pass_check.gd").new())   # test 21
	InteriorExtraDoors.register(self)   # test 21: Beth's pass - harbour warehouse/shop/cottages, gate towers, lighthouse enterable
	_register_shell_doors()   # test 22: filler houses/shops + harbour landmarks were hollow shells you could walk into

# ---------- settings ----------
func _load_settings() -> void:
	var cf := ConfigFile.new()
	if cf.load("user://settings.cfg") == OK:
		tier = int(cf.get_value("gfx", "tier3", 2)); time_mode = int(cf.get_value("gfx", "time", 0)) % 4
		fps_cap = int(cf.get_value("gfx", "fps", 60))

func _save_settings() -> void:
	var cf := ConfigFile.new(); cf.set_value("gfx", "tier3", tier); cf.set_value("gfx", "fps", fps_cap); cf.set_value("gfx", "time", time_mode); cf.save("user://settings.cfg")

# ---------- terrain ----------
func height(x: float, z: float) -> float:
	var r := Vector2(x, z).length()
	if r < 215.0: return 0.0
	var ld := Vector2(x, z).distance_to(LAKE)
	if ld < 100.0: return lerp(-4.0, _height_raw(x, z, r), smoothstep(45.0, 100.0, ld))
	var h := _height_raw(x, z, r)
	# test 12: Beth's volcano_titan stands on a level pad (its base ring is flat at y=0, r 147 m)
	var dv := Vector2(x, z).distance_to(VOLC)
	if dv < 200.0:
		if is_nan(_volc_h0): _volc_h0 = _height_raw_v13(VOLC.x, VOLC.y, VOLC.length())
		h = lerpf(_volc_h0, h, smoothstep(150.0, 200.0, dv))
	# test 14 (boss: "put the farmstead here"): the farmstead moved out to the end of the west dirt road; level pad
	var fd := Vector2(x, z).distance_to(FARM)
	if fd < 70.0:
		if is_nan(_farm_h0): _farm_h0 = _height_raw(FARM.x, FARM.y, FARM.length())
		h = lerpf(_farm_h0, h, smoothstep(30.0, 70.0, fd))
	# SW-corner port: level harbour platform (+0.6) blending out to the hills by 170 m, then the sea floor
	var pd := Vector2(x, z).distance_to(PORT)
	if pd < 260.0: h = lerpf(0.05, h, smoothstep(80.0, 260.0, pd))
	# hills fall away gently to the SW coast (no sheer wall at the sea edge)
	var dsea := Vector2(maxf(0.0, x - SEA_COAST_X), maxf(0.0, SEA_NORTH_Z - z)).length()
	if dsea < 160.0: h *= smoothstep(0.0, 160.0, dsea)
	# test 14: big harbour district pad
	var hw := HarborDistrict.pad_weight(x, z)
	if hw > 0.0: h = lerpf(h, HARBOR_Y, hw)
	var sm := sea_mask(x, z)
	# test 32 (boss's docks shot): the sea_mask slope started ~10 m inland of the quay wall and carved a 3-4 m trench
	# between the warehouses and the wall. Behind the quay wall (z < its inner face) the district stays at pad level.
	if hw > 0.99 and z < HarborDistrict.SHORE_Z - 1.0: sm = 0.0
	if x < SEA_COAST_X + 1.0 and z > SEA_NORTH_Z - 2.0: h = maxf(h, 0.7)   # over the sea plane: beach stays above the water
	if sm > 0.0: h = lerpf(h, -4.0, sm)
	return h

## test 14 (boss: mountains were hollow shells, too close): the mountains are now part of the terrain heightfield
## (closed, seamless, textured by ground.gdshader rock/snow) and stand far back at r 880-1150 m; the old 430-650 m
## hill wall is lowered to gentle foothills so there is open country between the city and the range.
const MTN_R0 := 880.0
const MTN_R1 := 1120.0
func _height_raw(x: float, z: float, r: float) -> float:
	var t := smoothstep(215.0, 340.0, r)
	var n := noise.get_noise_2d(x, z) * 0.5 + 0.5
	var h := t * (4.0 + 30.0 * n) + smoothstep(560.0, 840.0, r) * 26.0 * (0.6 + n)
	var mr := smoothstep(MTN_R0, MTN_R1, r + (n - 0.5) * 160.0)
	if mr > 0.0:
		var rg := 1.0 - absf(noise.get_noise_2d(x * 2.3 + 900.0, z * 2.3 - 400.0))   # ridged peaks
		var rg2 := 1.0 - absf(noise.get_noise_2d(x * 5.1 - 300.0, z * 5.1 + 700.0))
		var massif := smoothstep(0.25, 0.75, noise.get_noise_2d(x * 0.45 + 1500.0, z * 0.45 - 800.0) * 0.5 + 0.5)   # separate massifs + saddles
		h += mr * (60.0 + (40.0 + 230.0 * rg * rg) * (0.3 + 0.7 * massif) + 45.0 * rg2 * rg2 * mr)
	return _road_soften(x, z, h)

## the test 13 hills, kept only for the volcano pad height so the arena does not move
func _height_raw_v13(x: float, z: float, r: float) -> float:
	var t := smoothstep(215.0, 340.0, r)
	var n := noise.get_noise_2d(x, z) * 0.5 + 0.5
	return _road_soften(x, z, t * (4.0 + 30.0 * n) + smoothstep(430.0, 650.0, r) * 55.0 * (0.6 + n))

func _road_soften(x: float, z: float, h: float) -> float:
	# keep roads gentle: pull terrain down near outskirt roads
	var rd := _road_dist(Vector2(x, z))
	h *= lerp(0.35, 1.0, smoothstep(6.0, 40.0, rd))
	return h

func _road_dist(p: Vector2) -> float:
	var best := 1e9
	for r in ROADS:
		for i in range(1, r.size()):
			var a := Vector2(r[i-1][0], r[i-1][1]); var b := Vector2(r[i][0], r[i][1])
			var ab := b - a; var t: float = clamp((p - a).dot(ab) / max(ab.length_squared(), 0.001), 0.0, 1.0)
			best = min(best, p.distance_to(a + ab * t))
	return best

func _terrain() -> void:
	var N := 240; var S := 2400.0; var step := S / N   # test 14: 2.4 km so the far range + its back slopes hide the edge
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var hs := PackedFloat32Array(); hs.resize((N + 1) * (N + 1))
	for j in N + 1:
		for i in N + 1:
			hs[j * (N + 1) + i] = height(-S / 2 + i * step, -S / 2 + j * step)
	for j in N + 1:
		for i in N + 1:
			st.set_uv(Vector2(i, j)); st.add_vertex(Vector3(-S / 2 + i * step, hs[j * (N + 1) + i], -S / 2 + j * step))
	for j in N:
		for i in N:
			var a := j * (N + 1) + i
			st.add_index(a); st.add_index(a + 1); st.add_index(a + N + 1)
			st.add_index(a + 1); st.add_index(a + N + 2); st.add_index(a + N + 1)
	st.generate_normals()
	var mi := MeshInstance3D.new(); mi.mesh = st.commit()
	var m := ShaderMaterial.new(); mi.material_override = m
	if OS.get_environment("VARN_NO_TFIX2") == "":   # test 23: Beth's terrain fix 2 (ground layers, baked smooth normals, dirt wear)
		m.shader = load("res://terrain_fix2/ground/ground2.gdshader")
		for k in [["t_norm", "res://terrain_fix2/data/terrain_n.png"], ["t_data", "res://terrain_fix2/data/terrain_d.png"], ["grass_detail", "res://terrain_fix2/data/grass_detail.png"], ["dirt_albedo", "res://assets/roads/textures/dirt_albedo.png"], ["dirt_normal", "res://assets/roads/textures/dirt_normal.png"]]:
			m.set_shader_parameter(k[0], load(k[1]))
	else: m.shader = load("res://scripts/ground.gdshader")
	m.set_shader_parameter("cobble_albedo", load("res://assets/roads/textures/cobble_albedo.png")); m.set_shader_parameter("cobble_normal", load("res://assets/roads/textures/cobble_normal.png"))
	terrain_mat = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(mi)
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var hm := HeightMapShape3D.new()
	hm.map_width = N + 1; hm.map_depth = N + 1; hm.map_data = hs; cs.shape = hm; cs.scale = Vector3(step, 1, step)
	sb.add_child(cs); add_child(sb)

func _roads() -> void:
	# Beth (test 12): terrain-following ribbons on the rendered 10 m triangle surface, smooth bends, grass skirt, 3 LODs
	add_child(load("res://assets/roads/road_builder.gd").new().build(self, ROADS))

# ---------- environment / lighting ----------
func _env() -> void:
	var we := WorldEnvironment.new(); env = Environment.new()
	var sky := Sky.new(); sky_mat = ProceduralSkyMaterial.new(); sky.sky_material = sky_mat
	sky_mat.sky_cover = _star_tex()
	env.background_mode = Environment.BG_SKY; env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_color = Color(0.75, 0.68, 0.58); env.ambient_light_sky_contribution = 0.55
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES; env.tonemap_exposure = 1.0; env.tonemap_white = 6.0
	env.fog_enabled = true; env.fog_density = 0.0011; env.fog_aerial_perspective = 0.5; env.fog_sky_affect = 0.25   # test 14: density was 0.0022 (far range read as a milky wall)
	env.glow_enabled = true; env.glow_intensity = 0.6; env.glow_bloom = 0.08; env.glow_hdr_threshold = 1.0
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.adjustment_enabled = true; env.adjustment_contrast = 1.08; env.adjustment_saturation = 1.12
	we.environment = env; add_child(we)
	sun = DirectionalLight3D.new(); sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.shadow_bias = 0.03; sun.shadow_normal_bias = 1.0
	add_child(sun)

func _star_tex() -> ImageTexture:
	var w := 2048; var h := 1024
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8); img.fill(Color(0, 0, 0, 0))
	for i in 2600:
		var x := rng.randi() % w; var y := rng.randi() % (h / 2)
		var b := pow(rng.randf(), 3.0)
		var c := Color(0.8 + 0.2 * b, 0.85 + 0.15 * b, 1.0, 0.35 + 0.65 * b)
		img.set_pixel(x, y, c)
		if b > 0.7: img.set_pixel((x + 1) % w, y, c * 0.6); img.set_pixel(x, y + 1, c * 0.6)
	return ImageTexture.create_from_image(img)

func _set_time(h: float) -> void:
	tod = fposmod(h, 24.0)
	var day := clampf(sin((tod - 6.0) / 12.0 * PI), -1.0, 1.0)      # 1 at noon, 0 at 6/18, <0 night
	var elev := day * 62.0
	var night := day < 0.0
	var sunset := 1.0 - smoothstep(0.0, 0.35, abs(day))
	if night:
		sun.rotation_degrees = Vector3(-35, -35 + tod * 5, 0)     # moon
		sun.light_color = Color(0.6, 0.7, 1.0); sun.light_energy = 0.38   # test 7: brighter moon (night street read too dark)
		sun.light_volumetric_fog_energy = 0.4
	else:
		sun.rotation_degrees = Vector3(-max(elev, 4.0), -100 + (tod - 6.0) * 15.0, 0)
		sun.light_color = Color(1.0, 0.95, 0.86).lerp(Color(1.0, 0.65, 0.4), sunset)
		sun.light_energy = lerp(1.4, 0.9, sunset)
		sun.light_volumetric_fog_energy = lerp(1.0, 3.0, sunset)
	var nf := smoothstep(0.05, -0.25, day)    # 0 day -> 1 night
	sky_mat.sky_top_color = Color(0.22, 0.45, 0.85).lerp(Color(0.3, 0.32, 0.6), sunset).lerp(Color(0.01, 0.02, 0.06), nf)
	sky_mat.sky_horizon_color = Color(0.75, 0.82, 0.9).lerp(Color(1.0, 0.66, 0.45), sunset).lerp(Color(0.05, 0.07, 0.14), nf)
	sky_mat.ground_horizon_color = sky_mat.sky_horizon_color
	sky_mat.ground_bottom_color = Color(0.2, 0.22, 0.2).lerp(Color(0.01, 0.01, 0.02), nf)
	sky_mat.sun_angle_max = 25.0; sky_mat.sun_curve = 0.1
	sky_mat.sky_cover_modulate = Color(1, 1, 1, nf)
	env.ambient_light_energy = lerp(0.9, 0.4, nf)
	env.fog_light_color = sky_mat.sky_horizon_color
	env.volumetric_fog_albedo = Color(0.9, 0.9, 0.95).lerp(Color(1.0, 0.7, 0.5), sunset)
	env.tonemap_exposure = lerp(1.0, 1.15, nf)
	var em: float = lerp(0.0, 3.0, smoothstep(0.25, -0.1, day)) if tier > 0 else 0.0
	for m in emissive_mats: m.emission_energy_multiplier = em
	if glow_mat: glow_mat.emission_energy_multiplier = em * 2.0   # null with VARN_LITE (no street kit)
	for gm in glow_mm: gm.visible = em > 0.05
	var lamp_on := em > 0.3
	# soft warm fill that follows the hero at night so the Owner reads clearly on dark streets (no shadows: cheap)
	if hero_fill == null and hero:
		hero_fill = OmniLight3D.new(); hero_fill.name = "HeroNightFill"; hero_fill.light_color = Color(1.0, 0.85, 0.65)
		hero_fill.light_energy = 0.9; hero_fill.omni_range = 7.0; hero_fill.position = Vector3(0, 2.6, 1.2); hero_fill.shadow_enabled = false
		hero.add_child(hero_fill)
	if hero_fill: hero_fill.visible = nf > 0.3
	for l in lamp_lights:
		l[0].visible = lamp_on and tier >= l[1]
		if not (tier == 3 and lamp_on): l[0].shadow_enabled = false
	for f in fx_night: f[0].emitting = night and tier >= f[1]; f[0].visible = f[0].emitting
	for f in fx_day: f[0].emitting = not night and tier >= f[1]; f[0].visible = f[0].emitting
	if titan_quest and titan_quest.has_method("reapply_aftermath"): titan_quest.reapply_aftermath()   # test 24

var _rs_atlas := -1
var _rs_soft := -1
func apply_quality() -> void:
	if titan_quest and titan_quest.titan and titan_quest.titan.lava_mat and titan_quest.titan.lava_hq != (tier >= 2):   # test 14: veins shader on High/Ultra only
		titan_quest.titan.lava_veins(tier >= 2); titan_quest.titan.lava_stage(maxi(1, titan_quest.stage), false)
	if not ships.is_empty(): _ships_tier()
	for f in volc_fx: f.visible = tier > 0   # volcano smoke + lava lights off on Low
	if titan_quest and titan_quest.has_method("reapply_aftermath"): titan_quest.reapply_aftermath()   # test 24: quest aftermath survives tier swaps
	# Test 3: Mobile renderer for every tier. Cost drivers kept in check: render scale + FSR,
	# one shadowed light (the sun) with short distance, no shadowed lamps, LOD/HLOD everywhere.
	var vp := get_viewport()
	Engine.max_fps = fps_cap
	# test 20: these two are global renderer settings; calling them (even with the same value) dropped the scene
	# pipelines, so every apply_quality() (tier change, settings, benchmark start) re-compiled shaders mid-walk.
	# Only touch them when the value really changes.
	var atlas: int = [1024, 2048, 2048, 4096][tier]
	if atlas != _rs_atlas: _rs_atlas = atlas; RenderingServer.directional_shadow_atlas_set_size(atlas, true)
	var prefs_shadows: bool = bench or bool(VPrefs.prefs.get("shadows", true))
	var sq: int = [RenderingServer.SHADOW_QUALITY_HARD, RenderingServer.SHADOW_QUALITY_SOFT_VERY_LOW, RenderingServer.SHADOW_QUALITY_SOFT_LOW, RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM][tier]
	if sq != _rs_soft: _rs_soft = sq; RenderingServer.directional_soft_shadow_filter_set_quality(sq)
	sun.shadow_enabled = prefs_shadows
	sun.directional_shadow_max_distance = [30.0, 45.0, 60.0, 140.0][tier]
	sun.directional_shadow_mode = [DirectionalLight3D.SHADOW_ORTHOGONAL, DirectionalLight3D.SHADOW_ORTHOGONAL, DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS, DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS][tier]
	sun.light_angular_distance = 0.0
	_pass_tier_set("high" if tier >= 2 else "low")
	sun.shadow_blur = [0.5, 1.0, 1.5, 1.5][tier]
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR   # FSR1 is Forward+-only in 4.7
	vp.scaling_3d_scale = [0.5, 0.6, 0.7, 1.0][tier]
	vp.fsr_sharpness = 0.3
	# test 26 (boss: the voxel skin still looks speckled on the phone): the heroes are 1.8 cm cubes, ~1-2 px each on
	# screen, rendered at 50-70% 3D scale and then FXAA'd. One sample per pixel lands on a random cube colour (geometric
	# aliasing -> speckle) and FXAA's edge blend turns every cube edge into noise. Mobile-only: the box's Compatibility
	# renderer has no FXAA / 3D scaling, so it never showed. Now: no FXAA; MSAA (cheap on tiled phone GPUs) on
	# Medium+ averages the sub-pixel cubes into their real colours.
	HeroRoster.lod1 = false   # test 26: the hero always uses full detail (LOD0) on every tier
	HeroRoster.comp_lod1 = tier <= 1
	vp.msaa_3d = [Viewport.MSAA_DISABLED, Viewport.MSAA_2X, Viewport.MSAA_2X, Viewport.MSAA_4X][tier]
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	env.glow_enabled = tier >= 1
	env.ssao_enabled = false; env.ssil_enabled = false; env.ssr_enabled = false; env.sdfgi_enabled = false
	env.volumetric_fog_enabled = false
	env.fog_enabled = true; env.fog_density = 0.0011   # test 14 (was 0.0028: the far mountains read as a milky wall)
	if probe: probe.visible = tier >= 1
	for c in grass_chunks:
		var cap := int(c.multimesh.instance_count * [0.0, 0.2, 0.35, 1.0][tier])
		c.multimesh.visible_instance_count = cap; c.visible = cap > 0
		c.visibility_range_end = [0.0, 30.0, 40.0, 95.0][tier]
		c.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
	for f in fx_any: f[0].visible = tier >= f[1]; f[0].emitting = tier >= f[1]
	_swap_buildings()
	var ext_t := "high" if tier >= 2 else "low"   # test 22: Beth's exterior weathering pass (card2 atlas -> weathering shader)
	if ext_t != _ext_tier and OS.get_environment("VARN_NO_EXT") == "": _ext_tier = ext_t; ExteriorDressing.apply(self, ext_t)
	var tr: Array = [[[-1, -1], [0, 40], [40, 0]], [[-1, -1], [0, 70], [70, 0]], [[0, 30], [30, 120], [120, 0]], [[0, 50], [50, 200], [200, 0]]][tier]
	for t in tree_lods:
		var r: Array = tr[t[1]]; var n2: GeometryInstance3D = t[0]
		n2.visible = r[0] >= 0
		n2.visibility_range_begin = max(r[0], 0); n2.visibility_range_end = max(r[1], 0)
		n2.visibility_range_begin_margin = 4.0; n2.visibility_range_end_margin = 4.0
		var casts: bool = t[1] == 0 or (t[1] == 1 and tier <= 1)
		n2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if casts else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var trr: Array = [[[-1, -1], [-1, -1], [0, 0]], [[-1, -1], [0, 350], [350, 0]], [[-1, -1], [0, 450], [450, 0]], [[0, 300], [300, 650], [650, 0]]][tier]
	for t in hi_terrain:
		var r: Array = trr[t[1]]; var n3: GeometryInstance3D = t[0]
		n3.visible = r[0] >= 0
		n3.visibility_range_begin = max(r[0], 0); n3.visibility_range_end = max(r[1], 0)
		n3.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if (t[1] == 0) else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	TerrainFlowers.apply_tier(tier)   # test 23
	if OS.get_environment("VARN_NO_TFIX2") == "":
		FarGrass.apply_tier(tier); TerrainScatter.apply_tier(tier); terrain_mat.set_shader_parameter("beth_detail", tier >= 2)
	_set_time(tod)

func _mat(c: Color, rough := 0.85) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.albedo_color = c; m.roughness = rough; return m

func _water_mat() -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = load("res://scripts/water.gdshader"); return m

func _static_box(pos: Vector3, size: Vector3, rot := 0.0) -> void:
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var bs := BoxShape3D.new()
	bs.size = size; cs.shape = bs; sb.add_child(cs); sb.position = pos; sb.rotation.y = rot; add_child(sb)

func _fountain() -> void:
	# test 13 (boss: square shadow + blocky look): round 3-tier stone fountain. Every piece is a cylinder/torus, the
	# water discs never cast shadows (the old 12 m water PLANE cast a square one), collision = the round basin only.
	var stone := _mat(Color(0.74, 0.72, 0.68)); var dark := _mat(Color(0.56, 0.54, 0.5))
	var cyl := func(r0: float, r1: float, h: float, y: float, m: Material, segs := 48, shadow := true) -> MeshInstance3D:
		var mi := MeshInstance3D.new(); var c := CylinderMesh.new(); c.top_radius = r0; c.bottom_radius = r1; c.height = h; c.radial_segments = segs; c.rings = 1
		c.material = m; mi.mesh = c; mi.position.y = y
		if not shadow: mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi); return mi
	var ring := func(r: float, t: float, y: float, m: Material) -> void:
		var mi := MeshInstance3D.new(); var tm := TorusMesh.new(); tm.inner_radius = r - t; tm.outer_radius = r + t; tm.rings = 48; tm.ring_segments = 10
		tm.material = m; mi.mesh = tm; mi.position.y = y; add_child(mi)
	var wm := _water_mat(); wm.set_shader_parameter("wave", 0.015)
	cyl.call(7.1, 7.3, 0.25, 0.12, dark)                 # round plinth step
	cyl.call(6.6, 6.8, 0.75, 0.62, stone)                # outer basin wall
	ring.call(6.55, 0.22, 1.0, stone)                    # rounded lip
	cyl.call(6.25, 6.25, 0.04, 0.84, wm, 64, false)      # lower pool
	cyl.call(0.9, 1.1, 2.2, 1.6, stone)                  # stem
	cyl.call(2.7, 1.2, 0.5, 2.6, stone)                  # middle bowl
	ring.call(2.68, 0.12, 2.86, stone)
	cyl.call(2.5, 2.5, 0.04, 2.8, wm, 48, false)         # middle pool
	cyl.call(0.45, 0.6, 1.2, 3.4, stone)                 # upper stem
	cyl.call(1.25, 0.6, 0.35, 4.1, stone)                # top bowl
	cyl.call(1.1, 1.1, 0.04, 4.25, wm, 32, false)
	var fin := MeshInstance3D.new(); var sp := SphereMesh.new(); sp.radius = 0.35; sp.height = 0.7
	var lm := _mat(Color(0.12, 0.29, 0.6), 0.25); lm.metallic = 0.4; sp.material = lm; fin.mesh = sp; fin.position.y = 4.65; add_child(fin)
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var cy := CylinderShape3D.new(); cy.radius = 6.8; cy.height = 2.0; cs.shape = cy; sb.add_child(cs); add_child(sb)
	# falling sheets from the middle + top bowls into the pools below
	for tier in [[2.6, 2.8, 2.0], [1.15, 4.25, 1.4]]:
		var pf := _particles(160, 0.9, _soft_quad(Color(0.85, 0.93, 1.0, 0.55), 0.14, false), 0)
		var pp: ParticleProcessMaterial = pf.process_material
		pp.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_RING; pp.emission_ring_radius = tier[0]; pp.emission_ring_inner_radius = tier[0] - 0.1
		pp.emission_ring_height = 0.05; pp.emission_ring_axis = Vector3.UP; pp.direction = Vector3(0, -1, 0); pp.spread = 5; pp.radial_velocity_min = 0.4; pp.radial_velocity_max = 0.7
		pp.initial_velocity_min = 0.2; pp.initial_velocity_max = 0.5; pp.gravity = Vector3(0, -9.8, 0)
		pf.position = Vector3(0, tier[1], 0); add_child(pf); fx_any.append([pf, 1])
	blockers.append([Vector2.ZERO, 9.0])
	probe = ReflectionProbe.new(); probe.size = Vector3(90, 30, 90); probe.position = Vector3(0, 6, 0)
	probe.update_mode = ReflectionProbe.UPDATE_ONCE; probe.box_projection = true; probe.max_distance = 120
	add_child(probe)
	for i in 8:
		var a := i / 8.0 * TAU + PI / 8.0
		var lp := Vector3(cos(a) * 30.0, 0, sin(a) * 30.0)
		var post := _place_glb("res://assets/dressing/lantern_post.glb", lp, -a)
		var top: AABB = _meshes(post, [])[0].get_aabb()
		var l := OmniLight3D.new(); l.position = lp + Vector3(0, top.end.y - 0.4, 0); l.light_color = Color(1.0, 0.72, 0.4)
		l.light_energy = 3.0; l.omni_range = 18.0; l.omni_attenuation = 1.1
		l.set_meta("shadow_ultra", true)
		add_child(l); lamp_lights.append([l, 1])
		plaza_glow.append(l.position)
	# spray
	var p := _particles(400, 1.6, _soft_quad(Color(0.85, 0.93, 1.0, 0.7), 0.18, false), 0)
	var pm: ParticleProcessMaterial = p.process_material
	pm.direction = Vector3(0, 1, 0); pm.spread = 18; pm.initial_velocity_min = 4.0; pm.initial_velocity_max = 5.0; pm.gravity = Vector3(0, -9.8, 0)
	p.position = Vector3(0, 4.7, 0); add_child(p); fx_any.append([p, 1])

## test 14 (boss: flat blue rectangle with tan discs by the Stables): natural irregular pond, soft muddy bank, reeds,
## notched lily pads. No collision box (it was a hidden 40x26 wall); shallow water is walkable.
const POND := Vector3(-110, 0, 110)
func _pond_r(a: float) -> float:
	return 1.0 + 0.13 * sin(a * 3.0 + 0.7) + 0.08 * sin(a * 5.0 + 2.1) + 0.05 * sin(a * 9.0)

func _pond() -> void:
	var RX := 17.0; var RZ := 11.0; var N := 72
	var water := SurfaceTool.new(); water.begin(Mesh.PRIMITIVE_TRIANGLES)
	var bank := SurfaceTool.new(); bank.begin(Mesh.PRIMITIVE_TRIANGLES)
	var mud := Color(0.27, 0.22, 0.15); var grass := Color(0.36, 0.5, 0.22)
	for i in N:
		var a0 := TAU * i / N; var a1 := TAU * (i + 1) / N
		var p0 := Vector3(cos(a0) * RX * _pond_r(a0), 0, sin(a0) * RZ * _pond_r(a0))
		var p1 := Vector3(cos(a1) * RX * _pond_r(a1), 0, sin(a1) * RZ * _pond_r(a1))
		for v in [Vector3.ZERO, p1, p0]: water.set_normal(Vector3.UP); water.set_uv(Vector2(v.x, v.z) / 8.0); water.add_vertex(v)
		# bank: inner (under the water edge, mud) -> outer (+3.5 m, fades into grass), slight rise
		var q0 := p0 * (1.0 + 3.5 / p0.length()); var q1 := p1 * (1.0 + 3.5 / p1.length())
		var i0 := p0 * 0.9; var i1 := p1 * 0.9
		var vs := [[i0, mud, -0.04], [p1 * 0.9, mud, -0.04], [q1, grass, 0.03], [i0, mud, -0.04], [q1, grass, 0.03], [q0, grass, 0.03]]
		for t in vs:
			bank.set_color(t[1]); bank.set_normal(Vector3.UP); var v: Vector3 = t[0]; v.y = t[2]; bank.add_vertex(v)
	var bm := StandardMaterial3D.new(); bm.vertex_color_use_as_albedo = true; bm.roughness = 0.95
	var bmi := MeshInstance3D.new(); bmi.mesh = bank.commit(); bmi.material_override = bm; bmi.position = POND + Vector3(0, 0.03, 0)
	bmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(bmi)
	var wmi := MeshInstance3D.new(); wmi.mesh = water.commit(); wmi.material_override = _water_mat(); wmi.position = POND + Vector3(0, 0.07, 0)
	wmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(wmi)
	var rng := RandomNumberGenerator.new(); rng.seed = 1414
	# reeds: clumps of thin tapered blades along the bank
	var reed := MultiMeshInstance3D.new(); var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.use_colors = true
	var rm := CylinderMesh.new(); rm.top_radius = 0.0; rm.bottom_radius = 0.035; rm.height = 1.0; rm.radial_segments = 4; rm.rings = 1
	var rmat := StandardMaterial3D.new(); rmat.vertex_color_use_as_albedo = true; rmat.roughness = 0.9; rm.material = rmat
	mm.mesh = rm; mm.instance_count = 420
	for k in 420:
		var a := rng.randf() * TAU
		if fmod(a, 1.6) > 1.0: a = rng.randf() * TAU   # clumpy
		var r := rng.randf_range(0.85, 1.05)
		var p := Vector3(cos(a) * RX * _pond_r(a) * r, 0, sin(a) * RZ * _pond_r(a) * r)
		var hgt := rng.randf_range(0.9, 1.9)
		var bs := Basis(Vector3(rng.randf_range(-1, 1), 0, rng.randf_range(-1, 1)).normalized(), rng.randf_range(0.0, 0.25)).scaled(Vector3(1, hgt, 1))
		mm.set_instance_transform(k, Transform3D(bs, p + Vector3(0, hgt * 0.5, 0)))
		mm.set_instance_color(k, Color(0.32, 0.45, 0.18).lerp(Color(0.55, 0.5, 0.25), rng.randf() * 0.5))
	reed.multimesh = mm; reed.position = POND; add_child(reed)
	# lily pads: green discs with a wedge notch, a few pink flowers
	var pad := SurfaceTool.new(); pad.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in 14:
		var a0 := 0.5 + (TAU - 0.5) * i / 14.0; var a1 := 0.5 + (TAU - 0.5) * (i + 1) / 14.0
		for v in [Vector3.ZERO, Vector3(cos(a1), 0, sin(a1)) * 0.5, Vector3(cos(a0), 0, sin(a0)) * 0.5]: pad.set_normal(Vector3.UP); pad.add_vertex(v)
	var pm := StandardMaterial3D.new(); pm.albedo_color = Color(0.2, 0.42, 0.14); pm.roughness = 0.6; pm.cull_mode = BaseMaterial3D.CULL_DISABLED
	var padm := pad.commit()
	for k in 26:
		var a := rng.randf() * TAU; var r := rng.randf_range(0.35, 0.8)
		var p := Vector3(cos(a) * RX * _pond_r(a) * r, 0.09, sin(a) * RZ * _pond_r(a) * r)
		var lp := MeshInstance3D.new(); lp.mesh = padm; lp.material_override = pm; lp.position = POND + p
		lp.rotation.y = rng.randf() * TAU; lp.scale = Vector3.ONE * rng.randf_range(0.8, 1.6); lp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(lp)
		if k % 5 == 0:
			var fl := MeshInstance3D.new(); var sm := SphereMesh.new(); sm.radius = 0.13; sm.height = 0.14; fl.mesh = sm
			var fm := StandardMaterial3D.new(); fm.albedo_color = Color(0.95, 0.6, 0.75); fl.material_override = fm; fl.position = lp.position + Vector3(0.1, 0.05, 0); add_child(fl)
	blockers.append([Vector2(POND.x, POND.z), 20.0])

## test 14: crop fields + paddock fence beside the relocated farmstead (behind it, away from the road end)
func _farm_fields() -> void:
	var soil := StandardMaterial3D.new(); soil.albedo_color = Color(0.36, 0.27, 0.17); soil.roughness = 1.0
	var crop := StandardMaterial3D.new(); crop.albedo_color = Color(0.42, 0.55, 0.2); crop.roughness = 0.9
	var wheat := StandardMaterial3D.new(); wheat.albedo_color = Color(0.78, 0.66, 0.32); wheat.roughness = 0.9
	for f in [[Vector2(FARM.x + 34.0, FARM.y - 14.0), crop], [Vector2(FARM.x + 34.0, FARM.y + 14.0), wheat]]:
		var c: Vector2 = f[0]; var y := height(c.x, c.y)
		var bed := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(22, 24); pm.material = soil; bed.mesh = pm
		bed.position = Vector3(c.x, y + 0.04, c.y); bed.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(bed)
		var mmi := MultiMeshInstance3D.new(); var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D
		var bm := BoxMesh.new(); bm.size = Vector3(20.5, 0.55, 0.7); bm.material = f[1]; mm.mesh = bm; mm.instance_count = 11
		for k in 11: mm.set_instance_transform(k, Transform3D(Basis.IDENTITY, Vector3(0, 0.3, -10.5 + k * 2.1)))
		mmi.multimesh = mm; mmi.position = bed.position; add_child(mmi)
		for side in 4:   # fence ring of Beth's fence prop
			for k in 4:
				var off := Vector2(-9.0 + k * 6.0, 13.0) if side % 2 == 0 else Vector2(12.0, -9.0 + k * 6.0)
				if side >= 2: off = -off
				var fp := c + off
				_street_prop("fence", Vector3(fp.x, height(fp.x, fp.y), fp.y), 0.0 if side % 2 == 0 else PI / 2)
	blockers.append([FARM + Vector2(34, 0), 32.0]); blockers.append([FARM, 26.0])

func _walls_and_gate() -> void:
	# test 13 (boss: flat untextured grey wall/lintel): fieldstone texture, world triplanar
	var stone := StandardMaterial3D.new(); stone.albedo_texture = load("res://interiors/tex/fieldstone_albedo.jpg"); stone.albedo_color = Color(0.86, 0.84, 0.8)
	stone.normal_enabled = true; stone.normal_texture = load("res://interiors/tex/fieldstone_normal.png"); stone.normal_scale = 0.8
	stone.uv1_triplanar = true; stone.uv1_world_triplanar = true; stone.uv1_scale = Vector3.ONE / 2.2; stone.roughness = 0.9
	var H := 8.0; var T := 3.0
	var G := 7.0   # half gate opening
	var L := CITY_HALF - G; var cpos := (CITY_HALF + G) / 2.0
	var runs := []
	for sd in [-1, 1]:
		for z in [-CITY_HALF, CITY_HALF]: runs.append([Vector3(sd * cpos, H/2, z), Vector3(L, H, T)])
		for x in [-CITY_HALF, CITY_HALF]: runs.append([Vector3(x, H/2, sd * cpos), Vector3(T, H, L)])
	for r in runs:
		var mi := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = r[1]; bm.material = stone; mi.mesh = bm; mi.position = r[0]; add_child(mi)
		_static_box(r[0], r[1])
	# 4 gates: [outward dir, tower yaw]
	for gd in GATES:
		var out := Vector3(gd[0].x, 0, gd[0].y); var along := Vector3(out.z, 0, -out.x)
		for sd in [-1, 1]:
			var g := _place_glb("res://assets/buildings/bld_gate_tower.glb", out * (CITY_HALF - 1.2) + along * (sd * 8.2 * 1.7), gd[1])
			_add_trimesh(g)
			for mi in _meshes(g, []): mi.visible = false
			gate_towers.append(g)
		# gatehouse top: textured lintel with a stepped crenellation + a round arch of voussoirs under it
		var gc := out * CITY_HALF
		var lint := MeshInstance3D.new(); var am := BoxMesh.new(); am.size = Vector3(18, 2.2, 4.4) if out.x == 0 else Vector3(4.4, 2.2, 18)
		am.material = stone; lint.mesh = am; lint.position = gc + Vector3(0, 9.1, 0); add_child(lint)
		for k in 7:   # merlons
			var mm := MeshInstance3D.new(); var mb := BoxMesh.new(); mb.size = Vector3(1.4, 1.2, 4.6) if out.x == 0 else Vector3(4.6, 1.2, 1.4); mb.material = stone
			mm.mesh = mb; mm.position = gc + along * ((k - 3) * 2.5) + Vector3(0, 10.8, 0); add_child(mm)
		var n := 11; var R := G
		for k in n:   # voussoirs: half circle, springing at y 3.2 between the towers
			var a := PI * (k + 0.5) / n
			var vm := MeshInstance3D.new(); var vb := BoxMesh.new(); vb.size = Vector3(PI * R / n + 0.15, 1.0, 4.2); vb.material = stone; vm.mesh = vb
			vm.position = gc + along * (cos(a) * R) + Vector3(0, 3.2 + sin(a) * (8.0 - 3.2) / 1.0 * 0.95, 0)
			vm.basis = Basis(Vector3.UP, atan2(out.x, out.z)) * Basis(Vector3(0, 0, 1), -(a - PI / 2) * (1.0 if out.x == 0 else 1.0))
			add_child(vm)

## test 8: Beth's street kit (assets/card2/prop_*, shared card2 atlas, 3 LODs). Dressed by each building's door,
## kept 2.4 m+ to the side of the doorway so door lanes and interior triggers stay clear.
const STREET := {"inn": ["barrel_group", "lantern_post"], "smithy": ["crate_stack", "barrel_group"], "bakery": ["flower_planter", "bench"],
	"market": ["market_cart", "crate_stack"], "apothecary": ["flower_planter", "signpost"], "guildhall": ["lantern_post", "lantern_post"],
	"townhall": ["flower_planter", "flower_planter"], "temple": ["lantern_post", "bench"], "treasury": ["lantern_post", "crate_stack"],
	"thieves": ["barrel_group", "crate_stack"], "training": ["barrel_group", "signpost"], "house1": ["bench", "flower_planter"],
	"house2": ["flower_planter", "barrel_group"], "house3": ["bench", "lantern_post"], "house4": ["flower_planter", "crate_stack"],
	"crypt": ["lantern_post", "lantern_post"], "observatory": ["bench", "lantern_post"], "keep": ["lantern_post", "lantern_post"],
	"farmhouse": ["hay_bale", "fence"], "library": ["bench", "lantern_post"], "mage": ["lantern_post", "flower_planter"]}
const PROP_FLAT := ["cobble_edge"]
func _streets_to_shader() -> void:
	var segs := PackedVector4Array(); var hws := PackedFloat32Array()
	for r in STREETS: segs.append(Vector4(r[0], r[1], r[2], r[3])); hws.append(r[4])
	for sp in spurs: segs.append(Vector4(sp[0].x, sp[0].y, sp[1].x, sp[1].y)); hws.append(sp[2])
	segs.resize(64); hws.resize(64)
	terrain_mat.set_shader_parameter("segs", segs); terrain_mat.set_shader_parameter("seg_hw", hws)
	terrain_mat.set_shader_parameter("seg_n", mini(STREETS.size() + spurs.size(), 64)); terrain_mat.set_shader_parameter("street_n", STREETS.size())

## on a street, the plaza, a door footpath or an outside road (+pad)
func _on_way(p: Vector2, pad: float) -> bool:
	if absf(p.x) < CITY_HALF + 2 and absf(p.y) < CITY_HALF + 2 and street_edge_dist(p) < pad: return true
	for sp in spurs:
		if Geometry2D.get_closest_point_to_segment(p, sp[0], sp[1]).distance_to(p) < sp[2] + pad: return true
	return _road_dist(p) < 4.4 + pad

func _crosses_street(a: Vector2, b: Vector2) -> bool:
	for k in 9:
		if _on_way(a.lerp(b, k / 8.0), -0.35): return true
	return false

func _in_building(p: Vector2, pad: float) -> bool:
	for b in buildings:
		if (b.rect as Rect2).grow(pad).has_point(p): return true
	return false

func _street_prop(kind: String, pos: Vector3, rot: float) -> void:
	var root := Node3D.new(); root.name = "prop_" + kind; root.position = pos; root.rotation.y = rot; add_child(root)
	var bands := [[0.0, 30.0], [30.0, 70.0], [70.0, 160.0]]
	var sufs := ["", "_lod1", "_lod2"]
	var hi: AABB
	for k in 3:
		var v: Node3D = load("res://assets/card2/prop_%s%s.glb" % [kind, sufs[k]]).instantiate(); root.add_child(v)
		for mi in _meshes(v, []):
			mi.visibility_range_begin = bands[k][0]; mi.visibility_range_end = bands[k][1]
			if k == 0: hi = mi.get_aabb() if hi.size == Vector3.ZERO else hi.merge(mi.get_aabb())
			if k > 0: mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if kind == "lantern_post": _door_light(root.global_transform * Vector3(0.6, hi.end.y - 0.5, 0))
	if not PROP_FLAT.has(kind) and hi.size.y > 0.3:
		var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var bx := BoxShape3D.new()
		bx.size = hi.size; cs.shape = bx; cs.position = hi.get_center(); sb.add_child(cs); root.add_child(sb)

func _street_kit() -> void:
	for b in buildings:
		if not STREET.has(b.id): continue
		var n: Node3D = b.node
		var d = card2_door(b.id)
		var dl: Vector3 = d if d != null else Vector3(0, 0, b.aabb.end.z)
		var kinds: Array = STREET[b.id]
		for k in kinds.size():
			var side := -1.0 if k == 0 else 1.0
			var lp := Vector3(dl.x + side * 2.6, 0, dl.z + 1.2)
			var wp: Vector3 = n.global_transform * lp; wp.y = height(wp.x, wp.z)
			if _in_gate_path(Vector2(wp.x, wp.z), 2.0): continue
			_street_prop(kinds[k], wp, n.rotation.y + (PI / 2 if kinds[k] in ["bench", "fence"] else 0.0))
		# cobble kerb under the doorway
		var cw: Vector3 = n.global_transform * Vector3(dl.x, 0, dl.z + 0.4); cw.y = height(cw.x, cw.z) + 0.01
		_street_prop("cobble_edge", cw, n.rotation.y)
	# signposts + well at the plaza edge and by each gate road
	_street_prop("well", Vector3(18, height(18, -18), -18), 0.0)
	for g in [[Vector3(0, 0, 150), PI], [Vector3(0, 0, -150), 0.0], [Vector3(150, 0, 0), -PI / 2], [Vector3(-150, 0, 0), PI / 2]]:
		var gp: Vector3 = g[0] + Vector3(4, 0, 4); gp.y = height(gp.x, gp.z)
		_street_prop("signpost", gp, g[1])

## test 8: Beth's tripo2 backdrop castle (70 m silhouette, already metres) on the northern horizon; no collision.
## test 9: Beth's port is a whole harbour (77k High / 37k lod1). No coast in the world, so it sits on the lake's
## town-side shore, piers (-Z) out over the water. lod1 on phone High (phone_high_lod), lod2 beyond 120 m.
func _harbour() -> void:
	var c: Vector2 = harbour_spot()[0]; var inward: Vector2 = harbour_spot()[1]
	# model: shops/warehouses along z=-5 (doors face +z), quay + piers out to z=+17 -> +z points into the lake
	var root := Node3D.new(); root.name = "Harbour"; root.position = Vector3(c.x, 0.0, c.y); root.rotation.y = atan2(inward.x, inward.y); add_child(root)
	var sufs := ["_lod1", "_lod2"]; var bands := [[0.0, 120.0], [120.0, 600.0]]
	for k in 2:
		var v: Node3D = load("res://assets/card2/bld_port_card2%s.glb" % sufs[k]).instantiate(); root.add_child(v)
		for mi in _meshes(v, []):
			mi.visibility_range_begin = bands[k][0]; mi.visibility_range_end = bands[k][1]
			if k == 1: mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_add_col("res://assets/card2/bld_port_card2_col.glb", root.position, root.rotation.y)
	var d = _c2_door_raw("port")
	if d != null: _door_light(root.global_transform * (d + Vector3(0.9, 2.6, 0.7)))

## Harbour in the SW corner on the coast (test 10). Returns [centre, unit vector into the sea].
static func harbour_spot() -> Array:
	# quay edge (model z=0) 2 m inland of the coast; shops (model z -20..-5) on land, piers/boats out to z=+17 over the
	# sea to the west. Shifted 8 m south so the Tidewrack road's end (-425.6, 375) stays clear of the shop row.
	return [Vector2(SEA_COAST_X + 2.0, PORT.y + 8.0), Vector2(-1, 0)]

## test 11 (boss: "Need the ship models added"): the boss's own ships, cleaned up by Beth (godot-art/ships, index.json):
## waterline y=0, bow +Z, metres. Tidewrack sailing ship 30 m (phone High = lod1) along the harbour's main pier,
## boat_02 (6.4 m) and boat_sail (7.2 m) at the two smaller piers, a second boat_sail out at sea.
## Harbour local (lx, lz) -> world (root.x - lz, root.z + lx); piers run along local +z (world -x) -> bow yaw -PI/2.
## Tier-capped (Low 2 / Medium 3 / High 4 / Ultra 4), gentle bob + roll, Beth's _col hulls (static, at rest pose).
const SHIP_MAX := [3, 6, 10, 12]   # test 14: many ships (far ones are LOD2, no shadows)
var ships := []   # [node, base_y, phase]
var sea: TidewrackSea   # test 32
var _pier_spot := []
## the moored galleon at the Tidewrack main pier: [deck-side spot on the pier, yaw]
func _galleon_pier() -> Array:
	var r: Node3D = ships[0][0] if ships.size() > 0 else null
	if r == null: return [Vector3(PORT.x, 0.5, PORT.y), 0.0]
	if _pier_spot.is_empty():   # whichever side of the hull has the pier deck under it (ray onto the colliders)
		var best := r.global_position + r.global_basis.x * 6.5; var by := -99.0
		for sd in [1.0, -1.0]:
			for dd in [5.0, 6.5, 8.0]:
				var c: Vector3 = r.global_position + r.global_basis.x * (sd * dd); var q := PhysicsRayQueryParameters3D.create(c + Vector3(0, 20, 0), c - Vector3(0, 20, 0), 1)
				var h := get_world_3d().direct_space_state.intersect_ray(q)
				if h and h.position.y > by and h.position.y < 3.0 and not (h.collider in ships.map(func(x): return x[3])): by = h.position.y; best = h.position
		if by < 0.0: return [best, r.rotation.y]   # not ready yet: physics may still be settling
		_pier_spot = [best + Vector3(0, 0.3, 0), r.rotation.y]
	return _pier_spot
func _ships() -> void:
	var hs := harbour_spot(); var c: Vector2 = hs[0]
	var L := func(lx: float, lz: float) -> Vector2: return Vector2(c.x - lz, c.y + lx)
	# [world pos, model, near/far switch (m), yaw, phase]
	var spots := [[L.call(-29.0, 18.0), "tidewrack_sailing_ship", 120.0, -PI / 2 + 0.02, 0.0],
		[L.call(4.5, 10.0), "boat_02", 60.0, -PI / 2 - 0.05, 2.2],
		[L.call(20.5, 10.0), "boat_sail", 60.0, -PI / 2 + 0.06, 3.7],
		[c + Vector2(-85.0, 35.0), "boat_sail", 60.0, 2.4, 1.3],
		# test 14 harbour district: one moored at each new pier, two galleons + boats at anchor in the bay
		[Vector2(HarborDistrict.PIERS[0] + 5.2, 348.0), "boat_02", 60.0, 0.03, 0.8],
		[Vector2(HarborDistrict.PIERS[1] + 5.2, 350.0), "boat_sail", 60.0, -0.04, 2.9],
		[Vector2(HarborDistrict.PIERS[2] - 14.0, 352.0), "tidewrack_sailing_ship", 120.0, 0.02, 4.1],
		[Vector2(-520.0, 430.0), "tidewrack_sailing_ship", 120.0, 2.6, 1.7],
		[Vector2(-600.0, 380.0), "boat_sail", 60.0, 1.1, 0.4],
		[Vector2(-470.0, 520.0), "boat_02", 60.0, -0.7, 3.3],
		[Vector2(-650.0, 470.0), "boat_sail", 60.0, 0.5, 5.0],
		[Vector2(-560.0, 600.0), "tidewrack_sailing_ship", 120.0, -2.2, 2.4]]
	for i in spots.size():
		var sp: Array = spots[i]; var id: String = sp[1]
		var root := Node3D.new(); root.name = "Ship%d_%s" % [i, id]; add_child(root)
		root.position = Vector3(sp[0].x, 0.0, sp[0].y); root.rotation.y = sp[3]
		# test 12: tidewrack gets Beth's High mesh up close (<40 m); its UVs were re-normalized in the project copy (see /workspace/layout/fix_uv.py)
		var files := ["ship_%s_lod1" % id, "ship_%s_lod2" % id]; var bands := [[0.0, sp[2]], [sp[2], 600.0]]
		if id == "tidewrack_sailing_ship": files = ["ship_%s" % id] + files; bands = [[0.0, 40.0], [40.0, sp[2]], [sp[2], 600.0]]
		for k in files.size():
			var v: Node3D = load("res://assets/ships/%s.glb" % files[k]).instantiate(); root.add_child(v)
			for mi in _meshes(v, []):
				mi.visibility_range_begin = bands[k][0]; mi.visibility_range_end = bands[k][1]
				# thin double-sided sails self-shadow into acne, and the sea doesn't show ship shadows: no casting
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				if id == "tidewrack_sailing_ship":   # test 26: lossless atlas, anisotropic (hull no longer smeared at grazing angles), solid both-sided sails
					for si in mi.mesh.get_surface_count():
						var sm = mi.mesh.surface_get_material(si)
						if sm is BaseMaterial3D:
							sm = sm.duplicate(); sm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
							sm.cull_mode = BaseMaterial3D.CULL_DISABLED; sm.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED; mi.set_surface_override_material(si, sm)
		# hull draft: Beth's origin is ~1 m above the painted waterline on the galleon, ~0.3 m on the boats
		# test 26 (boss: "it's sunk"): test 27 (boss: now floating in the air): test 29: hull levelled in the GLB (keel flat at y ~-1.05) -> keel ~1.4 m under, waterline ~1/3 up the hull
		var sink := -0.35 if id == "tidewrack_sailing_ship" else -0.3
		root.position.y = sink   # test 27: set the float height first so the collision hull matches the raised galleon
		var col := _add_col("res://assets/ships/ship_%s_col.glb" % id, root.position, root.rotation.y); col.name = "ShipCol%d" % i
		ships.append([root, sink, float(sp[4]), col])
	_ships_tier()

func _ships_tier() -> void:
	var n: int = SHIP_MAX[clampi(tier, 0, 3)]
	for i in ships.size():
		var r: Node3D = ships[i][0]; r.visible = i < n
		var col: Node3D = ships[i][3]; col.process_mode = Node.PROCESS_MODE_INHERIT if i < n else Node.PROCESS_MODE_DISABLED
		for sb in col.find_children("*", "CollisionObject3D", true, false): (sb as CollisionObject3D).collision_layer = 1 if i < n else 0

var _ship_t := 0.0
func _soft_dot() -> ImageTexture:
	var n := 64; var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for y in n:
		for x in n:
			var d := Vector2(x - n * 0.5 + 0.5, y - n * 0.5 + 0.5).length() / (n * 0.5)
			img.set_pixel(x, y, Color(1, 1, 1, clampf(1.0 - d, 0.0, 1.0) ** 1.6))
	return ImageTexture.create_from_image(img)

func _shot_here(n: String) -> void:
	for i in 20: await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png("user://shot_%s.png" % n); print("BENCH ", n)

func _bob_ships(dt: float) -> void:
	_ship_t += dt
	for s in ships:
		var r: Node3D = s[0]
		if not r.visible: continue
		var ph: float = s[2]
		r.position.y = s[1] + sin(_ship_t * 0.7 + ph) * 0.06
		# test 28 (boss: "the ship isn't even horizontal"): no roll/pitch rock -- every hull stays level (deck flat, masts vertical); vertical bob only
		r.rotation.x = 0.0; r.rotation.z = 0.0

static func _c2_door_raw(key: String) -> Variant:
	if _c2_doors.is_empty(): card2_door("inn")
	return _c2_doors.get(key, null)

func _backdrop_castle() -> void:
	var root := Node3D.new(); root.name = "BackdropCastle"; root.position = Vector3(480, 0, -110); root.position.y = height(480, -110) - 1.0
	root.rotation.y = PI * 0.5; add_child(root)
	var sufs := ["_lod1", "_lod2"]; var bands := [[0.0, 300.0], [300.0, 0.0]]
	for k in 2:
		var v: Node3D = load("res://assets/backdrop/backdrop_castle%s.glb" % sufs[k]).instantiate(); root.add_child(v)
		for mi in _meshes(v, []):
			mi.visibility_range_begin = bands[k][0]; mi.visibility_range_end = bands[k][1]; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			if OS.get_environment("T8_PART") == "c": print("CASTLE ", root.position, " ", mi.get_aabb())

func _door_light(p: Vector3) -> void:
	var l := OmniLight3D.new(); l.name = "DoorLight"; l.position = p; l.light_color = Color(1.0, 0.72, 0.42)
	l.light_energy = 1.6; l.omni_range = 7.5; l.omni_attenuation = 1.2; l.shadow_enabled = false
	l.distance_fade_enabled = true; l.distance_fade_begin = DOOR_LIGHT_RANGE - 12.0; l.distance_fade_length = 12.0
	l.visible = false; add_child(l); door_lights.append(l)

## Mobile-safe door lights: at night only the N nearest within 45 m are enabled (N by tier), refreshed 4x/s.
func _update_door_lights(dt: float) -> void:
	_dl_t -= dt
	if _dl_t > 0.0 or hero == null: return
	_dl_t = 0.25
	var night := lamp_lights.size() > 0 and (lamp_lights[0][0] as OmniLight3D).visible or (hero_fill != null and hero_fill.visible)
	var hp := hero.global_position; var near := []
	for l in door_lights:
		var d := l.global_position.distance_to(hp)
		if night and d < DOOR_LIGHT_RANGE: near.append([d, l])
		else: l.visible = false
	near.sort_custom(func(a, b): return a[0] < b[0])
	var cap: int = DOOR_LIGHTS_MAX[clampi(tier, 0, 3)]
	for i in near.size(): near[i][1].visible = i < cap

func active_door_lights() -> int:
	var c := 0
	for l in door_lights: c += int(l.visible)
	return c

func _place_glb(path: String, pos: Vector3, rot: float) -> Node3D:
	var n: Node3D = load(path).instantiate(); n.position = pos; n.rotation.y = rot; add_child(n); return n

func _meshes(n: Node, out: Array) -> Array:
	if n is MeshInstance3D: out.append(n)
	for c in n.get_children(): _meshes(c, out)
	return out

func _add_trimesh(n: Node3D, skip := "roof") -> void:
	for mi in _meshes(n, []):
		if skip != "" and (String(mi.name).to_lower().contains(skip) or String(mi.get_parent().name).to_lower().contains(skip)): continue
		mi.create_trimesh_collision()

func _building(d: Array) -> void:
	var id: String = d[0]; var pos := Vector3(float(d[1]), 0, float(d[2])); var rot: float = d[3]
	var outside := maxf(absf(pos.x), absf(pos.z)) > CITY_HALF
	if outside: pos.y = height(pos.x, pos.z) - 0.15   # snapped onto its levelled pad (base sunk 15 cm: no gap)
	var card := CARD2.has(id)
	var n := _place_glb(_card2_path(id, "_lod1") if card else "res://assets/buildings/bld_%s.glb" % id, pos, rot)
	if card: _add_col(_card2_path(id, "_col"), pos, rot)   # Beth's -colonly collision: walls + walkable door openings
	else: _add_trimesh(n, "roof")
	var aabb := AABB(); var first := true
	for mi in _meshes(n, []):
		var a: AABB = (n.global_transform.affine_inverse() * mi.global_transform) * mi.get_aabb()
		if first: aabb = a; first = false
		else: aabb = aabb.merge(a)
	for mi in _meshes(n, []): mi.visible = false      # r3 shell = collision proxy; visuals come from Beth r4 hi tiers
	var fpa := aabb
	if card:
		var colp: Node3D = load(_card2_path(id, "_col")).instantiate()
		for mi in _meshes(colp, []): fpa = fpa.merge(mi.transform * mi.get_aabb())
		colp.free()
	var fr := _world_rect(fpa, pos, rot)
	buildings.append({"id": id, "name": d[4], "node": n, "roof": null, "roofs": [], "lods": [], "vis": null, "aabb": aabb, "rect": fr})
	# short spur path from every front door to its street (test 11, boss: walkways end at doors)
	var fwd := Vector2(sin(rot), cos(rot))
	var fronts := {}   # one path per door column: the outermost door (the keep's inner gate shares the outer one's path)
	for dp in card2_doors(id) if card else [Vector3(0, 0, aabb.end.z)]:
		var kx := snappedf(dp.x, 1.0)
		if not fronts.has(kx) or dp.z > fronts[kx].z: fronts[kx] = dp
	for dp in fronts.values():
		var w: Vector3 = n.global_transform * dp; var w2 := Vector2(w.x, w.z); var e := w2
		for k in 120:   # walk out from the door until 0.4 m onto the street
			e = w2 + fwd * (0.25 * k)
			if (not outside and street_edge_dist(e) < -0.4) or (outside and _road_dist(e) < 1.6): break
		spurs.append([w2, e, 1.0 if dp.x > 3.0 and id == "farmhouse" else 0.85, id])   # narrow footpaths: 1.7 m (2 m to the barn doors)
	if id == "farmhouse":
		# the barn half of the welded farmstead: its 4 m doors enter the barn interior (InteriorManager.extra_doors)
		extra_doors.append({"id": "barn", "name": "Barn", "node": n, "aabb": aabb, "door": card2_doors(id)[1], "rect": fr})
	blockers.append([Vector2(pos.x, pos.z), max(aabb.size.x, aabb.size.z) * 0.55 + 2.0])
	# test 9: warm door lantern light at Beth's door_point (lantern height, beside the doorway), pooled + culled
	var dp = card2_door(id) if card else null
	var dl: Vector3 = dp if dp != null else Vector3(0, 0, aabb.end.z)
	_door_light(n.global_transform * Vector3(dl.x + 0.9, dl.y + 2.6, dl.z + 0.7))

func _swap_buildings() -> void:
	# HLOD: every building carries all three of Beth's tiers; the tier only changes the distance bands.
	if cur_suffix == "?":
		cur_suffix = "hlod"
		for b in buildings:
			b.lods = []; b.roofs = []
			for suf in ["", "_lod1", "_lod2"]:
				var vp := _card2_path(b.id, suf) if CARD2.has(b.id) else "res://assets/hi/buildings/bld_%s%s.glb" % [b.id, suf]
				var v: Node3D = load(vp).instantiate()
				b.node.add_child(v); b.lods.append(v)
				var rf = v.find_child("roof", true, false)
				if rf: b.roofs.append(rf)
				if b.id == "windmill": windmill_blades.append(v.find_child("blades", true, false))
			b.vis = b.lods[0]
		for g in gate_towers:
			var gl := []
			for suf in ["", "_lod1", "_lod2"]:
				var v2: Node3D = load("res://assets/hi/buildings/bld_gate_tower%s.glb" % suf).instantiate(); g.add_child(v2); gl.append(v2)
			gate_lods.append(gl)
		_collect_emissive()
	var bands: Array = [[[-1, -1], [-1, -1], [0, 0]], [[-1, -1], [0, 70], [70, 0]], [[0, 55], [55, 140], [140, 0]], [[0, 120], [120, 260], [260, 0]]][tier]
	var sets := []
	for b in buildings: sets.append(b.lods)
	for gl in gate_lods: sets.append(gl)
	for lods in sets:
		for i in 3:
			var r: Array = bands[i]
			for mi in _meshes(lods[i], []):
				mi.visible = r[0] >= 0
				mi.visibility_range_begin = max(r[0], 0); mi.visibility_range_end = max(r[1], 0)
				mi.visibility_range_begin_margin = 3.0; mi.visibility_range_end_margin = 3.0
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if i == 2 else GeometryInstance3D.SHADOW_CASTING_SETTING_ON

func _collect_emissive() -> void:
	var seen := {}
	emissive_mats.clear()
	for b in buildings:
		for lv in b.lods:
			for mi in _meshes(lv, []):
				for i in mi.mesh.get_surface_count():
					var m = mi.get_active_material(i)
					if m is BaseMaterial3D and m.emission_texture and not seen.has(m):
						seen[m] = true; m.emission_enabled = true; m.emission = Color(1.0, 0.72, 0.38); emissive_mats.append(m)

# ---------- Beth dressing / decals ----------
func _mesh_parts(path: String) -> Array:
	var n: Node = load(path).instantiate()
	var out := []
	for mi in _meshes(n, []): out.append([mi.mesh, mi.transform])
	n.free()
	return out

func _multimesh(path: String, xf: Array, shadow := true, vis_end := 0.0) -> Array:
	var made := []
	for part in _mesh_parts(path):
		var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = part[0]; mm.instance_count = xf.size()
		for i in xf.size(): mm.set_instance_transform(i, xf[i] * part[1])
		var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if vis_end > 0: mmi.visibility_range_end = vis_end
		add_child(mmi); made.append(mmi)
	return made

func _load_items(f: String) -> Array:
	var j = JSON.parse_string(FileAccess.get_file_as_string("res://assets/data/" + f))
	return j["items"]

func _dressing() -> void:
	var groups := {}
	var items := _load_items("PLACEMENT_dressing_town.json") + _load_items("PLACEMENT_dressing_roads.json") + _load_items("PLACEMENT_decals.json")
	for it in items:
		var file: String = it["file"]
		if file.contains("wall_cap") or file.contains("puddle"): continue
		var p: Array = it["position"]; var r: Array = it["rotation"]; var s: Array = it["scale"]
		if _in_gate_path(Vector2(p[0], p[2]), 1.0) and not file.contains("decals/"): continue
		if absf(p[0]) < CITY_HALF and absf(p[2]) < CITY_HALF and _in_building(Vector2(p[0], p[2]), 0.5): continue   # test 11 relayout
		var y: float = height(p[0], p[2]) if p[1] == null else float(p[1])
		if file.contains("decals/") and (file.contains("ground") or file.contains("puddle") or file.contains("leaves")): y += 0.03
		var b := Basis.from_euler(Vector3(r[0], r[1], r[2])).scaled(Vector3(s[0], s[1], s[2]))
		# test 13 city sweep (boss crossroads): these placements predate the test 11/12 relayout
		var p2 := Vector2(p[0], p[2])
		if file.contains("curb") or file.contains("cobble_edge"):
			var ax: Vector3 = b.x.normalized(); var hl: float = 1.0 * float(s[0]) + 0.3
			var a2: Vector2 = p2 + Vector2(ax.x, ax.z) * hl; var b2: Vector2 = p2 - Vector2(ax.x, ax.z) * hl
			if _crosses_street(a2, b2): continue   # curbs stop at intersections/paths
		elif file.contains("decals/"):
			if not file.contains("road") and _on_way(p2, 0.6): continue   # green/leaf blobs off the roads
		elif _on_way(p2, 0.6): continue                                 # no props standing on roads/paths
		if file.contains("lantern") or file.contains("signpost") or file.contains("banner_pole") or file.contains("milestone"):
			b = Basis(Vector3.UP, r[1]).scaled(Vector3(s[0], s[1], s[2]))   # always upright
		if not groups.has(file): groups[file] = []
		groups[file].append(Transform3D(b, Vector3(p[0], y, p[2])))
	glow_mat = StandardMaterial3D.new(); glow_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	glow_mat.albedo_color = Color(1.0, 0.8, 0.45); glow_mat.emission_enabled = true; glow_mat.emission = Color(1.0, 0.7, 0.35)
	var glow_mesh := SphereMesh.new(); glow_mesh.radius = 0.16; glow_mesh.height = 0.32; glow_mesh.radial_segments = 8; glow_mesh.rings = 4; glow_mesh.material = glow_mat
	var pg := []
	for gp in plaza_glow: pg.append(Transform3D(Basis(), gp))
	if pg.size() > 0:
		var pmm := MultiMesh.new(); pmm.transform_format = MultiMesh.TRANSFORM_3D; pmm.mesh = glow_mesh; pmm.instance_count = pg.size()
		for i in pg.size(): pmm.set_instance_transform(i, pg[i])
		var pmi := MultiMeshInstance3D.new(); pmi.multimesh = pmm; pmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(pmi); glow_mm.append(pmi)
	for file in groups:
		var xf: Array = groups[file]
		var is_decal: bool = file.begins_with("decals/")
		var small: bool = file.contains("curb") or file.contains("cobble") or is_decal or file.contains("rubble")
		_multimesh("res://assets/" + file, xf, not small, 160.0 if small else 300.0)
		if file.contains("lantern"):
			var parts := _mesh_parts("res://assets/" + file)
			var top: AABB = parts[0][0].get_aabb()
			var head := Vector3(top.get_center().x, top.end.y - 0.35, top.get_center().z)
			var gx := []
			for t in xf:
				gx.append(Transform3D(Basis(), t * head))
				if file.contains("lantern_post") or rng.randf() < 0.4:
					var l := OmniLight3D.new(); l.position = t * head; l.light_color = Color(1.0, 0.72, 0.4)
					l.light_energy = 1.6; l.omni_range = 11.0 if file.contains("post") else 7.0; l.omni_attenuation = 1.4
					l.distance_fade_enabled = true; l.distance_fade_begin = 70; l.distance_fade_length = 20
					add_child(l); lamp_lights.append([l, 2 if file.contains("post") else 3])
			var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = glow_mesh; mm.instance_count = gx.size()
			for i in gx.size(): mm.set_instance_transform(i, gx[i])
			var gmi := MultiMeshInstance3D.new(); gmi.multimesh = mm; gmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(gmi); glow_mm.append(gmi)

func _lod_instances(base: String, xf: Transform3D, shadow: bool) -> void:
	for lod in 3:
		var path: String = base + ["", "_lod1", "_lod2"][lod] + ".glb"
		if not ResourceLoader.exists(path): continue
		var n: Node3D = load(path).instantiate(); n.transform = xf; add_child(n)
		for mi in _meshes(n, []):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if (shadow and lod == 0) else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			hi_terrain.append([mi, lod])

const LAKE := Vector2(250, -200)
## test 12: Beth's volcano_titan (godot-art/volcano, built on the boss's volcano_game): 296 m across, 77 m tall, origin =
## cone centre at ground level, scale 1. Phone High = lod1 (87k tris); caldera arena r 33 m at y 39 ringed by a lava moat;
## 6.5 m spiral path from path_start (SW foot) to path_end (arena). The Ashen Titan stands at titan_spawn.
const VOLC := Vector2(405, -402)
const FARM := Vector2(-290.0, -288.0)   # test 14: farmstead pad centre (outside the walls, end of the west dirt road)
const OLD_FARM_LOT := Vector2(-132.0, 48.4)   # its old in-town lot, now a garden green
var _farm_h0 := NAN
var _volc_h0 := NAN
var volc_base := Vector3.ZERO
var lava_mats: Array[BaseMaterial3D] = []
var _lava_sm: ShaderMaterial
## test 13: one shared procedural molten-rock material (scripts/lava.gdshader) for every lava surface
func lava_mat() -> ShaderMaterial:
	if _lava_sm == null: _lava_sm = ShaderMaterial.new(); _lava_sm.shader = load("res://scripts/lava.gdshader")
	return _lava_sm
var volc_fx: Array[Node3D] = []
var pool_lights: Array[OmniLight3D] = []
var titan_quest: Node   # scripts/titan_quest.gd (test 13)
var volc_vj := {}
func _volcano_titan() -> void:
	volc_vj = JSON.parse_string(FileAccess.get_file_as_string("res://assets/volcano/index.json"))
	volc_base = Vector3(VOLC.x, height(VOLC.x, VOLC.y) - 0.3, VOLC.y)
	var root := Node3D.new(); root.name = "VolcanoTitan"; root.position = volc_base; add_child(root)
	for k in 2:
		var v: Node3D = load("res://assets/volcano/volcano_titan_lod%d.glb" % (k + 1)).instantiate(); root.add_child(v)
		for mi in _meshes(v, []):
			mi.visibility_range_begin = 0.0 if k == 0 else 420.0; mi.visibility_range_end = 420.0 if k == 0 else 0.0
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if k == 0 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			for si in mi.mesh.get_surface_count():
				var m := mi.get_active_material(si) as BaseMaterial3D
				if m and m.resource_name.begins_with("volcano_lava"):
					mi.set_surface_override_material(si, lava_mat())
				hi_terrain.append([mi, k + 1])
	_add_col("res://assets/volcano/volcano_titan_col.glb", volc_base, 0.0)
	# warm light over the lava moat + the caldera floor, no shadows
	var aj: Array = volc_vj.arena.center
	var arena := volc_base + Vector3(aj[0], aj[1], aj[2])
	for i in 3:
		var a := i / 3.0 * TAU
		var gl := OmniLight3D.new(); gl.light_color = Color(1.0, 0.45, 0.15); gl.light_energy = 1.4; gl.omni_range = 18.0
		gl.position = arena + Vector3(cos(a) * 36.0, 2.0, sin(a) * 36.0); gl.shadow_enabled = false; add_child(gl); volc_fx.append(gl)
	var cg := OmniLight3D.new(); cg.light_color = Color(1.0, 0.5, 0.2); cg.light_energy = 0.5; cg.omni_range = 40.0
	cg.position = arena + Vector3(0, 14, 0); add_child(cg); volc_fx.append(cg)
	# smoke plume + ash at Beth's vent markers
	for vt in volc_vj.vents:
		var vp: Array = vt.pos
		var big: bool = vt.kind == "crater_plume"
		volc_fx.append(_smoke(volc_base + Vector3(vp[0], vp[1], vp[2]), 26 if big else 6, 16.0 if big else 6.0, 14.0 if big else 8.0,
			Color(0.3, 0.28, 0.28, 0.75) if big else Color(0.22, 0.2, 0.2, 0.6)))
	# test 13: the Titan stands IN the central lava pool (Beth titan_pool); TitanQuest owns stages, intro and FX
	var tp: Array = volc_vj.titan_pool.center
	VolcanoTitan.CENTER = volc_base + Vector3(tp[0], 0.0, tp[2])
	VolcanoTitan.CHASE_BREAK = float(volc_vj.arena.radius_m) + 42.0
	for i in 6:   # lava lights around the pool
		var a := i / 6.0 * TAU
		var pl := OmniLight3D.new(); pl.light_color = Color(1.0, 0.42, 0.12); pl.light_energy = 1.6; pl.omni_range = 14.0; pl.shadow_enabled = false
		pl.position = volc_base + Vector3(tp[0] + cos(a) * 9.0, 39.0, tp[2] + sin(a) * 9.0); add_child(pl); volc_fx.append(pl); pool_lights.append(pl)
	blockers.append([VOLC, 155.0])

func _smoke(at: Vector3, amount: int, size: float, life: float, col: Color) -> CPUParticles3D:
	var sm := CPUParticles3D.new(); sm.amount = amount; sm.lifetime = life; sm.preprocess = life
	sm.position = at; sm.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE; sm.emission_sphere_radius = size * 0.3
	sm.direction = Vector3(0.15, 1, 0); sm.spread = 12.0; sm.gravity = Vector3(0.6, 0.8, 0); sm.initial_velocity_min = size * 0.2; sm.initial_velocity_max = size * 0.32
	var cv := Curve.new(); cv.add_point(Vector2(0, 0.4)); cv.add_point(Vector2(1, 1.0)); sm.scale_amount_curve = cv
	var gr := Gradient.new(); gr.set_color(0, Color(col.r, col.g, col.b, 0.0)); gr.set_color(1, Color(col.r + 0.2, col.g + 0.2, col.b + 0.2, 0.0)); gr.add_point(0.12, col); sm.color_ramp = gr
	var q := QuadMesh.new(); q.size = Vector2(size, size)
	var smat := StandardMaterial3D.new(); smat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; smat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	smat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES; smat.vertex_color_use_as_albedo = true; smat.albedo_texture = _soft_dot()
	smat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED; q.material = smat; sm.mesh = q; sm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	sm.visibility_range_end = 1400.0; add_child(sm); return sm

## enemies' ground: terrain, or the volcano's collision inside its footprint (the Titan's caldera at y ~39)
func ground_y(x: float, z: float) -> float:
	if Vector2(x, z).distance_to(VOLC) > 150.0 or not is_inside_tree(): return height(x, z)
	var q := PhysicsRayQueryParameters3D.create(Vector3(x, volc_base.y + 120.0, z), Vector3(x, volc_base.y - 5.0, z), 1)
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	return float(hit.position.y) if hit else height(x, z)
## test 10 (boss: "Port is supposed to be in the corner"): Tidewrack harbour sits in the SOUTH-WEST corner exactly as in
## v1.5.33 (bossregions.js PORT_CENTER = (-425.6, 392); the Tidewrack road already ends at its gate, (-425.6, 375)).
## The original harbour opens WEST onto sea (seaX -104..-19); here that sea is a coast filling the whole SW corner.
const SEA_COAST_X := PORT.x - 14.0     # coastline (N-S) just west of the quay
const SEA_NORTH_Z := PORT.y - 70.0     # sea's north shore
## test 14 (boss: no square sea edge): the shore wiggles into bays and headlands away from the quays. The wiggle only
## moves the waterline seaward of the old straight lines, so the flat sea plane never shows through land.
static func shore_z(x: float) -> float:   # north shore (sea is south of it), straight along the harbour district quay
	var f := smoothstep(HarborDistrict.X0 - 10.0, HarborDistrict.X0 - 90.0, x)
	return SEA_NORTH_Z + f * (22.0 + 14.0 * sin(x * 0.012) + 8.0 * sin(x * 0.031 + 2.0))
static func coast_x(z: float) -> float:   # west coast (sea is west of it), straight along the old port + lighthouse
	var f := smoothstep(480.0, 560.0, z)
	return SEA_COAST_X - f * (20.0 + 14.0 * sin(z * 0.011) + 8.0 * sin(z * 0.027 + 1.0))
static func sea_mask(x: float, z: float) -> float:
	var cx := coast_x(z); var sz := shore_z(x)
	return (1.0 - smoothstep(cx - 8.0, cx, x)) * smoothstep(sz - 8.0, sz, z)
static func near_port(p: Vector2, pad := 0.0) -> bool:
	return p.distance_to(PORT) < 150.0 + pad or sea_mask(p.x, p.y) > 0.0 or (p.x < SEA_COAST_X + pad and p.y > SEA_NORTH_Z - 10.0 - pad)
const SHORE_YAW := PI
const HARBOR_Y := 0.25   # test 14: harbour district ground level
var harbor: Node3D
func _hi_terrain() -> void:
	var T := "res://assets/hi/terrain/"
	for i in 26:
		var a := i / 26.0 * TAU + rng.randf_range(-0.07, 0.07)
		var r := rng.randf_range(520, 640)
		var p := Vector2(cos(a), sin(a)) * r
		if _road_dist(p) < 70 or p.distance_to(Vector2(405, -402)) < 150: continue
		var k: String = ["peak_snow_hi", "peak_bare_hi", "peak_snow_hi", "peak_bare_hi"][i % 4]
		var sc := rng.randf_range(1.3, 2.0)
		var ry := rng.randf() * TAU; var sy := rng.randf_range(0.9, 1.2)
		if near_port(p, 60.0) or true: continue   # test 14: the hollow peak shells are gone (terrain mountains); rng draws kept
		_lod_instances(T + k, Transform3D(Basis(Vector3.UP, ry).scaled(Vector3(sc, sc * sy, sc)), Vector3(p.x, height(p.x, p.y) - 6.0, p.y)), true)
	_volcano_titan()
	for i in 18:
		var a2 := rng.randf() * TAU; var r2 := rng.randf_range(250, 460); var p2 := Vector2(cos(a2), sin(a2)) * r2
		if _road_dist(p2) < 30 or p2.distance_to(LAKE) < 70 or near_port(p2, 10.0) or p2.distance_to(VOLC) < 160.0: continue
		var k2: String = "boulder_strata_hi"
		var s2 := rng.randf_range(0.5, 1.0) if k2.begins_with("cliff") else rng.randf_range(0.8, 1.6)
		_lod_instances(T + k2, Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s2, s2, s2)), Vector3(p2.x, height(p2.x, p2.y) - 1.0, p2.y)), true)
	# lake with Beth's shore pieces, waterline at y=0
	var w := MeshInstance3D.new(); var pm := CylinderMesh.new(); pm.top_radius = 66; pm.bottom_radius = 66; pm.height = 0.2; pm.radial_segments = 64; pm.rings = 1
	pm.material = _water_mat(); w.mesh = pm; w.position = Vector3(LAKE.x, -0.1, LAKE.y); add_child(w)
	# SW-corner sea (test 10): one big water quad from the coast to the world edge
	var sw := MeshInstance3D.new(); var sp := PlaneMesh.new(); var x0 := -4000.0; var z1 := 4000.0   # test 14: sea to the horizon
	sp.size = Vector2(SEA_COAST_X - 1.0 - x0, z1 - (SEA_NORTH_Z - 2.0)); sp.material = _water_mat(); sw.mesh = sp; sw.name = "Sea"
	sw.position = Vector3((x0 + SEA_COAST_X - 1.0) * 0.5, 0.0, (SEA_NORTH_Z - 2.0 + z1) * 0.5); sw.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(sw)
	# the boss's Tripo lighthouse: rock island + tower share one origin (Beth). LOD1/LOD2 only.
	var lh := Node3D.new(); lh.name = "Lighthouse"; lh.position = Vector3(SEA_COAST_X - 2.0, -0.6, PORT.y + 62.0); lh.rotation.y = 1.34; add_child(lh)   # test 11: on the SW coast; island turned so its stair foot (model ~(3, 0.5, 13)) lands on the dry shore to the east
	for part in ["lighthouse_rock_island", "lighthouse_tower"]:
		for k in 2:
			var v: Node3D = load("res://assets/card2/tripo/bld_%s_tripo%s.glb" % [part, ["_lod1", "_lod2"][k]]).instantiate(); lh.add_child(v)
			for mi in _meshes(v, []):
				mi.visibility_range_begin = [0.0, 160.0][k]; mi.visibility_range_end = [160.0, 0.0][k]
		# test 11: island col with the stair corridor carved out (assets/lighthouse_fix, from Beth's col); ramp below
		var cp := "res://assets/lighthouse_fix/lighthouse_rock_island_col_stairs.glb" if part == "lighthouse_rock_island" else "res://assets/card2/tripo/bld_%s_tripo_col.glb" % part
		_add_col(cp, lh.position, lh.rotation.y)
	# test 11: the Tripo stair treads are too tall/ragged for the capsule to climb; an invisible ramp under the stairs
	# (island model space, ground -> plateau, ~35 deg) makes them walkable. The visible steps are unchanged.
	var ra := Vector3(3.6, 0.6, 15.5); var rb := Vector3(0.8, 9.0, 3.0); var rd := rb - ra
	var ramp := StaticBody3D.new(); ramp.name = "LighthouseStairRamp"; lh.add_child(ramp)
	var rcs := CollisionShape3D.new(); var rbx := BoxShape3D.new(); rbx.size = Vector3(2.4, 0.3, rd.length()); rcs.shape = rbx
	rcs.transform = Transform3D(Basis.looking_at(rd.normalized(), Vector3.UP), (ra + rb) * 0.5 - Vector3(0, 0.15, 0)); ramp.add_child(rcs)
	for i in 12:
		var a3 := i / 12.0 * TAU
		var p3 := LAKE + Vector2(cos(a3), sin(a3)) * 60.0
		var b3 := Basis(Vector3.UP, atan2(p3.x - LAKE.x, p3.y - LAKE.y) + SHORE_YAW)
		_lod_instances(T + "shore_edge_hi", Transform3D(b3, Vector3(p3.x, 0, p3.y)), false)

func _mountains_old() -> void:
	var kinds := ["mountain_peak_snow", "mountain_peak_bare", "mountain_peak_snow", "mountain_peak_bare", "cliff_ridge_60m"]
	var placed := []
	for i in 30:
		var a := i / 30.0 * TAU + rng.randf_range(-0.08, 0.08)
		var r := rng.randf_range(470, 620)
		var p := Vector2(cos(a), sin(a)) * r
		if _road_dist(p) < 45: continue
		placed.append([kinds[i % kinds.size()], p, rng.randf_range(1.6, 3.2)])
	placed.append(["volcano_cone_flank", Vector2(405, -402), 2.6])
	for i in 14:
		var a2 := rng.randf() * TAU; var r2 := rng.randf_range(250, 420); var p2 := Vector2(cos(a2), sin(a2)) * r2
		if _road_dist(p2) < 25: continue
		placed.append([["grass_mound", "scree_slope", "rock_arch", "cliff_ridge_60m"][i % 4], p2, rng.randf_range(0.9, 1.5)])
	var by := {}
	for m in placed:
		var p: Vector2 = m[1]; var s: float = m[2]
		var t := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.9, 1.3), s)), Vector3(p.x, height(p.x, p.y) - 2.0, p.y))
		if not by.has(m[0]): by[m[0]] = []
		by[m[0]].append(t)
	for k in by:
		for lod in 3:
			var path: String = "res://assets/terrain/%s%s.glb" % [k, ["", "_lod1", "_lod2"][lod]]
			if not ResourceLoader.exists(path):
				if lod == 2: path = "res://assets/terrain/%s_lod1.glb" % k
				else: continue
			for mmi in _multimesh(path, by[k], lod == 0):
				terrain_lods.append([mmi, lod])

# ---------- foliage ----------
func _in_gate_path(p: Vector2, pad := 0.0) -> bool:
	# 12 m-wide corridor from 30 m inside to 35 m outside each gate
	if abs(p.x) < 6 + pad and abs(p.y) > CITY_HALF - 30 and abs(p.y) < CITY_HALF + 35: return true
	if abs(p.y) < 6 + pad and abs(p.x) > CITY_HALF - 30 and abs(p.x) < CITY_HALF + 35: return true
	return false

func _ok_spot(p: Vector2, pad: float) -> bool:
	if abs(p.x) < 7 + pad and p.y > -215 and p.y < 215: return false   # N-S avenue through both gates
	if abs(p.y) < 7 + pad and abs(p.x) < 215: return false             # E-W avenue through both gates
	if _in_gate_path(p, pad): return false
	if p.length() < 40 + pad: return false
	if abs(p.length() - 194.0) < 7 + pad: return false
	if street_edge_dist(p) < 1.5 + pad: return false
	if _in_building(p, 1.0 + pad): return false
	for sp in spurs:
		if Geometry2D.get_closest_point_to_segment(p, sp[0], sp[1]).distance_to(p) < sp[2] + 0.5 + pad: return false
	if abs(p.x) > CITY_HALF - 4 and abs(p.x) < CITY_HALF + 4: return false
	if abs(p.y) > CITY_HALF - 4 and abs(p.y) < CITY_HALF + 4: return false
	for b in blockers:
		if p.distance_to(b[0]) < b[1] + pad: return false
	if p.length() > 200 and _road_dist(p) < 8 + pad: return false
	return true

func _wind_mat_for(mesh: Mesh, sway: float) -> Mesh:
	# duplicate the mesh and give every surface its own wind material (fixes shared-override bug)
	var m2: Mesh = mesh.duplicate()
	for i in m2.get_surface_count():
		var src = m2.surface_get_material(i)
		var m := ShaderMaterial.new(); m.shader = load("res://scripts/wind.gdshader")
		if src is BaseMaterial3D:
			m.set_shader_parameter("albedo_tex", src.albedo_texture)
			m.set_shader_parameter("tint", src.albedo_color)
		m.set_shader_parameter("sway", sway)
		m2.surface_set_material(i, m)
	return m2

func _scatter(path: String, count: int, area: float, minr: float, sway: float, smin: float, smax: float, shadow: bool, collide := false) -> Array:
	var xf := []
	var tries := 0
	while xf.size() < count and tries < count * 40:
		tries += 1
		var p := Vector2(rng.randf_range(-area, area), rng.randf_range(-area, area))
		if p.length() < minr or not _ok_spot(p, 2.0): continue
		var s := rng.randf_range(smin, smax); var ry := rng.randf() * TAU
		if near_port(p, 2.0): continue   # SW-corner port/sea (test 10), after the draws so the rest is unchanged
		xf.append(Transform3D(Basis(Vector3.UP, ry).scaled(Vector3(s, s, s)), Vector3(p.x, height(p.x, p.y) - 0.05, p.y)))
	for part in _mesh_parts(path):
		var mesh: Mesh = part[0] if sway == 0.0 else _wind_mat_for(part[0], sway)
		var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = mesh; mm.instance_count = xf.size()
		for i in xf.size(): mm.set_instance_transform(i, xf[i] * part[1])
		var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mmi.visibility_range_end = 450.0 if shadow else 120.0
		add_child(mmi)
		if shadow: tree_mmis.append(mmi)
	if collide:
		for t in xf:
			if t.origin.length() < CITY_HALF: _static_box(t.origin + Vector3(0, 1.5, 0), Vector3(0.7, 3, 0.7))
	return xf

var blossom_xf := []
func _pick(count: int, area: float, minr: float, smin: float, smax: float, maxr := 1e9) -> Array:
	var xf := []; var tries := 0
	while xf.size() < count and tries < count * 40:
		tries += 1
		var p := Vector2(rng.randf_range(-area, area), rng.randf_range(-area, area))
		if p.length() < minr or p.length() > maxr or not _ok_spot(p, 2.0) or p.distance_to(LAKE) < 62: continue
		var s := rng.randf_range(smin, smax); var ry := rng.randf() * TAU
		if near_port(p, 2.0): continue   # test 10 SW port/sea, after the draws so the rest is unchanged
		xf.append(Transform3D(Basis(Vector3.UP, ry).scaled(Vector3(s, s, s)), Vector3(p.x, height(p.x, p.y) - 0.05, p.y)))
	return xf

func _trees_hi(kind: String, xf: Array, sway: float, collide: bool, chunk := 140.0) -> void:
	var chunks := {}
	for t in xf:
		var key := Vector2i(floori(t.origin.x / chunk), floori(t.origin.z / chunk))
		if not chunks.has(key): chunks[key] = []
		chunks[key].append(t)
	for lod in 3:
		var path := "res://assets/hi/trees/%s_hi%s.glb" % [kind, ["", "_lod1", "_lod2"][lod]]
		if not ResourceLoader.exists(path): continue
		for part in _mesh_parts(path):
			var mesh := _wind_mat_for(part[0], sway if lod < 2 else 0.0)
			for key in chunks:
				var arr: Array = chunks[key]
				var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = mesh; mm.instance_count = arr.size()
				for i in arr.size(): mm.set_instance_transform(i, arr[i] * part[1])
				var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm
				mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if lod < 2 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				add_child(mmi); tree_lods.append([mmi, lod])
	if collide:
		for t in xf:
			if t.origin.length() < CITY_HALF: _static_box(t.origin + Vector3(0, 1.5, 0), Vector3(0.7, 3, 0.7))

func _foliage() -> void:
	_trees_hi("oak", _pick(150, 180, 0, 0.9, 1.25), 0.04, true)
	_trees_hi("birch", _pick(60, 180, 0, 0.9, 1.2), 0.06, true)
	blossom_xf = _pick(40, 130, 0, 0.9, 1.1)
	_trees_hi("blossom", blossom_xf, 0.04, true)
	_trees_hi("oak_autumn", _pick(45, 180, 0, 0.9, 1.25), 0.04, true)
	_trees_hi("oak_deep", _pick(30, 180, 0, 0.9, 1.25), 0.04, true)
	_trees_hi("pine", _pick(650, 600, 205, 1.0, 1.6), 0.02, false, 180.0)
	_trees_hi("pine_snow", _pick(120, 650, 480, 1.1, 1.7), 0.02, false, 180.0)
	_trees_hi("oak", _pick(150, 420, 205, 1.0, 1.4, 420), 0.03, false, 180.0)
	_trees_hi("bush", _pick(200, 180, 0, 0.8, 1.3), 0.1, false)
	_trees_hi("bush_autumn", _pick(90, 180, 0, 0.8, 1.3), 0.1, false)
	for f in ["flowers_red", "flowers_yellow", "flowers_white", "flowers_purple"]:
		_scatter("res://assets/veg/%s.glb" % f, 160, 170, 0, 0.25, 0.8, 1.2, false)
	_scatter("res://assets/rocks/rock_mossy.glb", 60, 450, 205, 0.0, 1.0, 2.5, true)
	_scatter("res://assets/rocks/boulder.glb", 40, 450, 205, 0.0, 1.0, 2.0, true)

func _showcase() -> void:
	# one of every tree kind in a row west of the plaza, for close-up checks
	var kinds := ["blossom", "oak", "birch", "oak_autumn", "oak_deep", "pine", "pine_snow", "bush", "bush_autumn"]
	for i in kinds.size():
		var p := Vector3(-150 + i * 9.0, 0, 158)
		_trees_hi(kinds[i], [Transform3D(Basis(), p)], 0.04, false)
		blockers.append([Vector2(p.x, p.z), 3.0])
		_static_box(p + Vector3(0, 1.5, 0), Vector3(0.7, 3, 0.7))

func _grass() -> void:
	# one crossed-quad blade clump; chunked so frustum culling + visibility range keep it cheap
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for k in 3:
		var a := k * PI / 3.0; var dx := cos(a) * 0.09; var dz := sin(a) * 0.09
		var v := [Vector3(-dx, 0, -dz), Vector3(dx, 0, dz), Vector3(dx * 0.15, 0.42, dz * 0.15), Vector3(-dx * 0.15, 0.42, -dz * 0.15)]
		var uv := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)]
		for idx in [0, 1, 2, 0, 2, 3]: st.set_uv(uv[idx]); st.add_vertex(v[idx])
	var blade := st.commit()
	var gm := ShaderMaterial.new(); gm.shader = load("res://scripts/grass.gdshader"); blade.surface_set_material(0, gm)
	var C := 30.0
	for cx in range(-7, 7):
		for cz in range(-7, 7):
			var xf := []
			for i in 1600:
				var p := Vector2((cx + rng.randf()) * C, (cz + rng.randf()) * C)
				if p.length() > 400 or not _ok_spot(p, 0.5): continue
				var s := rng.randf_range(0.7, 1.4)
				xf.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.8, 1.5), s)), Vector3(p.x, height(p.x, p.y), p.y)))
			if xf.is_empty(): continue
			var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = blade; mm.instance_count = xf.size()
			for i in xf.size(): mm.set_instance_transform(i, xf[i])
			var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm; mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mmi.visibility_range_end = 110.0; mmi.visibility_range_end_margin = 10.0
			add_child(mmi); grass_chunks.append(mmi)

# ---------- particles ----------
func _soft_quad(c: Color, size: float, additive: bool) -> QuadMesh:
	var q := QuadMesh.new(); q.size = Vector2(size, size)
	var m := StandardMaterial3D.new()
	if additive: m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES; m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = c; m.vertex_color_use_as_albedo = true
	var g := GradientTexture2D.new(); var gr := Gradient.new(); gr.set_color(0, Color(1, 1, 1, 1)); gr.set_color(1, Color(1, 1, 1, 0))
	g.gradient = gr; g.fill = GradientTexture2D.FILL_RADIAL; g.fill_from = Vector2(0.5, 0.5); g.fill_to = Vector2(1.0, 0.5); g.width = 64; g.height = 64
	m.albedo_texture = g
	if additive: m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD; m.emission_enabled = true; m.emission = c; m.emission_energy_multiplier = 3.0
	q.material = m
	return q

func _particles(amount: int, life: float, mesh: Mesh, _t: int) -> GPUParticles3D:
	var p := GPUParticles3D.new(); p.amount = amount; p.lifetime = life; p.draw_pass_1 = mesh
	p.process_material = ParticleProcessMaterial.new(); p.visibility_aabb = AABB(Vector3(-40, -10, -40), Vector3(80, 40, 80))
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return p

func _fx() -> void:
	# chimney smoke
	for b in buildings:
		if not CHIMNEYS.has(b.id): continue
		var a: AABB = b.aabb
		var p := _particles(40, 6.0, _soft_quad(Color(0.75, 0.75, 0.78, 0.35), 1.6, false), 0)
		var pm: ParticleProcessMaterial = p.process_material
		pm.direction = Vector3(0.3, 1, 0); pm.spread = 12; pm.initial_velocity_min = 0.8; pm.initial_velocity_max = 1.3; pm.gravity = Vector3(0.25, 0.15, 0)
		pm.scale_min = 0.6; pm.scale_max = 1.2
		var sc := Curve.new(); sc.add_point(Vector2(0, 0.4)); sc.add_point(Vector2(1, 2.5)); var sct := CurveTexture.new(); sct.curve = sc; pm.scale_curve = sct
		var cr := Gradient.new(); cr.set_color(0, Color(1, 1, 1, 0.7)); cr.set_color(1, Color(1, 1, 1, 0)); var crt := GradientTexture1D.new(); crt.gradient = cr; pm.color_ramp = crt
		p.position = b.node.global_transform * Vector3(a.position.x * 0.5, a.end.y - 0.5, a.position.z * 0.4)
		add_child(p); fx_any.append([p, 2])
	# falling petals around cherry trees
	var petal := _soft_quad(Color(1.0, 0.72, 0.85, 1.0), 0.09, false)
	for i in blossom_xf.size():
		var t: Transform3D = blossom_xf[i]
		var p := _particles(60, 7.0, petal, 0)
		var pm: ParticleProcessMaterial = p.process_material
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE; pm.emission_sphere_radius = 2.0
		pm.gravity = Vector3(0.3, -0.35, 0.1); pm.initial_velocity_min = 0.1; pm.initial_velocity_max = 0.4
		pm.turbulence_enabled = true; pm.turbulence_noise_strength = 0.6; pm.turbulence_influence_min = 0.05; pm.turbulence_influence_max = 0.15
		p.position = t.origin + Vector3(0, 4.0, 0); p.visibility_range_end = 70.0
		add_child(p); fx_any.append([p, 3])
	# fireflies (night)
	for c in [Vector3(-110, 1.2, 110), Vector3(0, 1.2, 0), Vector3(-60, 1.2, 60), Vector3(60, 1.2, -90), Vector3(-25, 1.2, 40), Vector3(80, 1.2, 80)]:
		var p := _particles(70, 5.0, _soft_quad(Color(0.75, 1.0, 0.35, 1.0), 0.12, true), 0)
		var pm: ParticleProcessMaterial = p.process_material
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX; pm.emission_box_extents = Vector3(22, 1.5, 22)
		pm.gravity = Vector3.ZERO; pm.turbulence_enabled = true; pm.turbulence_noise_strength = 1.5; pm.turbulence_influence_min = 0.2; pm.turbulence_influence_max = 0.4
		var cr := Gradient.new(); cr.offsets = PackedFloat32Array([0, 0.3, 0.7, 1]); cr.colors = PackedColorArray([Color(1,1,1,0), Color(1,1,1,1), Color(1,1,1,1), Color(1,1,1,0)])
		var crt := GradientTexture1D.new(); crt.gradient = cr; pm.color_ramp = crt
		p.position = c; add_child(p); fx_night.append([p, 1])
	# sunlit dust motes around the hero (day)
	var dust := _particles(260, 6.0, _soft_quad(Color(1.0, 0.95, 0.8, 0.5), 0.04, true), 0)
	var dm: ParticleProcessMaterial = dust.process_material
	dm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX; dm.emission_box_extents = Vector3(16, 4, 16)
	dm.gravity = Vector3(0.05, -0.02, 0); dm.turbulence_enabled = true; dm.turbulence_noise_strength = 0.4
	dust.position = Vector3(0, 2, 0); dust.local_coords = false; hero_vis.get_parent().add_child(dust); fx_day.append([dust, 3])

# ---------- hero + Pip ----------
func _limb(parent: Node3D, mesh: Mesh, mat: Material, pos: Vector3) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); mi.mesh = mesh; mi.material_override = mat; mi.position = pos; parent.add_child(mi); return mi

func _hero() -> void:
	hero = CharacterBody3D.new(); hero.position = Vector3(-6, 0.1, 26)
	var cs := CollisionShape3D.new(); var cap := CapsuleShape3D.new(); cap.height = 1.905; cap.radius = 0.32; cs.shape = cap; cs.position.y = 1.905 / 2
	hero.add_child(cs); add_child(hero)
	hero_vis = Node3D.new(); hero.add_child(hero_vis)
	var skin := _mat(Color(0.86, 0.68, 0.55), 0.6); var tunic := _mat(Color(0.45, 0.12, 0.14), 0.7); var dark := _mat(Color(0.15, 0.13, 0.12)); var gold := _mat(Color(0.85, 0.65, 0.2), 0.3)
	gold.metallic = 0.8
	var leg := CapsuleMesh.new(); leg.radius = 0.11; leg.height = 0.95
	var arm := CapsuleMesh.new(); arm.radius = 0.08; arm.height = 0.72
	var torso := CapsuleMesh.new(); torso.radius = 0.24; torso.height = 0.72
	var head := SphereMesh.new(); head.radius = 0.13; head.height = 0.27
	for s in [-1, 1]:
		var hip := Node3D.new(); hip.position = Vector3(s * 0.12, 0.95, 0); hero_vis.add_child(hip)
		_limb(hip, leg, dark, Vector3(0, -0.475, 0)); limbs.append([hip, s])
		var sh := Node3D.new(); sh.position = Vector3(s * 0.31, 1.48, 0); hero_vis.add_child(sh)
		_limb(sh, arm, tunic, Vector3(0, -0.34, 0)); limbs.append([sh, -s])
	_limb(hero_vis, torso, tunic, Vector3(0, 1.27, 0))
	_limb(hero_vis, head, skin, Vector3(0, 1.775, 0))
	var crown := CylinderMesh.new(); crown.top_radius = 0.12; crown.bottom_radius = 0.13; crown.height = 0.05
	_limb(hero_vis, crown, gold, Vector3(0, 1.88, 0))
	var cape := BoxMesh.new(); cape.size = Vector3(0.5, 0.9, 0.04)
	_limb(hero_vis, cape, _mat(Color(0.1, 0.15, 0.35)), Vector3(0, 1.1, 0.26))
	pip = Node3D.new(); pip.position = hero.position + Vector3(1.2, 0, 1.2); add_child(pip)
	var fur := _mat(Color(0.95, 0.78, 0.25), 0.8)
	var pb := SphereMesh.new(); pb.radius = 0.17; pb.height = 0.3; _limb(pip, pb, fur, Vector3(0, 0.2, 0))
	var ph := SphereMesh.new(); ph.radius = 0.12; ph.height = 0.22; _limb(pip, ph, fur, Vector3(0, 0.38, -0.04))
	var ear := PrismMesh.new(); ear.size = Vector3(0.05, 0.13, 0.03)
	_limb(pip, ear, dark, Vector3(-0.07, 0.455, -0.04)); _limb(pip, ear, dark, Vector3(0.07, 0.455, -0.04))
	cam_pivot = Node3D.new(); add_child(cam_pivot)
	cam_arm = SpringArm3D.new(); cam_arm.spring_length = 6.0; cam_arm.margin = 0.3
	var sph := SphereShape3D.new(); sph.radius = 0.25; cam_arm.shape = sph
	cam_arm.add_excluded_object(hero.get_rid())
	cam_pivot.add_child(cam_arm)
	cam = Camera3D.new(); cam.fov = 62; cam.far = 2200; cam_arm.add_child(cam); cam.current = true

func _hud() -> void:
	var cl := CanvasLayer.new(); add_child(cl)
	hud_label = Label.new(); hud_label.position = Vector2(12, 64); hud_label.add_theme_font_size_override("font_size", 16)
	hud_label.add_theme_color_override("font_outline_color", Color.BLACK); hud_label.add_theme_constant_override("outline_size", 6); cl.add_child(hud_label)
	where_label = Label.new(); where_label.position = Vector2(500, 44); where_label.add_theme_font_size_override("font_size", 30)
	where_label.add_theme_color_override("font_outline_color", Color.BLACK); where_label.add_theme_constant_override("outline_size", 8); cl.add_child(where_label)
	bench_label = Label.new(); bench_label.position = Vector2(40, 110); bench_label.add_theme_font_size_override("font_size", 18)
	bench_label.add_theme_color_override("font_outline_color", Color.BLACK); bench_label.add_theme_constant_override("outline_size", 8); cl.add_child(bench_label)
	_apply_time_mode()
	joy_base = Panel.new(); joy_base.size = Vector2(220, 220); joy_base.position = Vector2(60, 460)
	var sb := StyleBoxFlat.new(); sb.bg_color = Color(1, 1, 1, 0.15); sb.set_corner_radius_all(110); sb.border_color = Color(1, 1, 1, 0.5); sb.set_border_width_all(3)
	joy_base.add_theme_stylebox_override("panel", sb); joy_base.mouse_filter = Control.MOUSE_FILTER_IGNORE; cl.add_child(joy_base)
	joy_knob = Panel.new(); joy_knob.size = Vector2(90, 90)
	var kb := StyleBoxFlat.new(); kb.bg_color = Color(1, 1, 1, 0.55); kb.set_corner_radius_all(45)
	joy_knob.add_theme_stylebox_override("panel", kb); joy_knob.mouse_filter = Control.MOUSE_FILTER_IGNORE; joy_base.add_child(joy_knob)
	joy_knob.position = Vector2(65, 65)
	joy_center = joy_base.position + Vector2(110, 110)

func _btn(cl: CanvasLayer, pos: Vector2, cb: Callable) -> Button:
	var b := Button.new(); b.position = pos; b.size = Vector2(225, 56); b.add_theme_font_size_override("font_size", 22)
	b.focus_mode = Control.FOCUS_NONE; b.pressed.connect(cb); cl.add_child(b); return b

func _apply_time_mode() -> void:
	_set_time(TIME_PRESETS[time_mode][1])

func _input_blocked() -> bool:
	return menu_open or (VUI.title != null and VUI.title.visible)

func _unhandled_input(e: InputEvent) -> void:
	if _input_blocked():
		joy_touch = -1; cam_touch = -1; joy_vec = Vector2.ZERO
		return
	var vw := get_viewport().get_visible_rect().size
	if e is InputEventScreenTouch:
		if e.pressed:
			if e.position.x < vw.x * 0.45 and joy_touch == -1:
				joy_touch = e.index; joy_center = e.position
				joy_base.position = joy_center - Vector2(110, 110); _joy(e.position)
			elif cam_touch == -1: cam_touch = e.index
		else:
			if e.index == joy_touch: joy_touch = -1; joy_vec = Vector2.ZERO; joy_knob.position = Vector2(65, 65)
			if e.index == cam_touch: cam_touch = -1
	elif e is InputEventScreenDrag:
		if e.index == joy_touch: _joy(e.position)
		elif e.index == cam_touch:
			var ls := float(VPrefs.prefs.get("lookSens", 1.0))
			yaw -= e.relative.x * 0.006 * ls; pitch = clamp(pitch - e.relative.y * 0.004 * ls, -1.2, 0.35)
	elif e is InputEventMagnifyGesture:
		_zoom_by(1.0 / e.factor)
	elif e is InputEventMouseButton and e.pressed and e.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
		_zoom_by(0.9 if e.button_index == MOUSE_BUTTON_WHEEL_UP else 1.1)

func _zoom_by(f: float) -> void:
	var zs := float(VPrefs.prefs.get("zoomSens", 1.0))
	var z := clampf(float(VPrefs.prefs.get("zoom", 1.0)) * pow(f, zs), 0.5, 2.0)
	VPrefs.prefs["zoom"] = z   # live; persisted on next set_pref/save

func _joy(p: Vector2) -> void:
	var d := (p - joy_center).limit_length(100.0)
	joy_vec = d / 100.0; joy_knob.position = Vector2(65, 65) + d

func _physics_process(dt: float) -> void:
	if hero == null: return
	var inp := joy_vec if not _input_blocked() else Vector2.ZERO
	var k := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if k.length() > 0.1: inp = k
	if sea and sea.active: sea.drive(inp, dt); return   # test 32: sailing / diving in the Tidewrack Sea
	var fwd := Vector3(-sin(yaw), 0, -cos(yaw)); var right := Vector3(cos(yaw), 0, -sin(yaw))
	var dir := right * inp.x + fwd * -inp.y
	var speed: float = (move_speed * float(cheat.speed)) * clamp(inp.length(), 0.0, 1.0)
	if flying_now() and fly_alt > 40.0: speed *= minf(1.0 + (fly_alt - 40.0) / 30.0, 120.0)   # test 16: fly faster up high (~100x at 3 km)
	if dir.length() > 0.05: dir = dir.normalized()
	hero.velocity.x = dir.x * speed; hero.velocity.z = dir.z * speed
	hero.velocity.y = -1.0 if hero.is_on_floor() else hero.velocity.y - 20.0 * dt
	# test 13 Jump: ~1.2 m apex (v = sqrt(2 g h), g 20), only from the floor -> no double jump
	if jump_req and hero.is_on_floor() and not flying_now():
		hero.velocity.y = JUMP_V; jump_count += 1
		if party and party.get("rig") and party.rig.clips.has("jump"): party.rig.play_attack("jump", 1.0)
	jump_req = false
	if flying_now(): hero.velocity.y = (height(hero.position.x, hero.position.z) + fly_alt - hero.position.y) * 2.0
	elif in_sea(hero.position) and hero.position.y < -0.05: hero.velocity.y = (0.0 - hero.position.y) * 4.0   # test 26: float at the sea surface (swim)
	elif landing and not hero.is_on_floor(): hero.velocity.y = maxf(hero.velocity.y, -7.0)   # fly turned off mid-air: soft landing
	elif landing: landing = false
	_altitude_view()
	if cheats and cheats.flags.bump and party:   # Bumps: enemies' bodies push the hero; off = walk through them
		for e in party.director.living():
			var dv := Vector2(hero.position.x - e.global_position.x, hero.position.z - e.global_position.z)
			var mind: float = e.bump_r() + 0.4
			if dv.length() < mind and dv.length() > 0.001:
				var push := dv.normalized() * (mind - dv.length()); hero.position.x += push.x; hero.position.z += push.y
	if interiors: interiors.climb(hero, dir, dt)   # ladders: only while pushing into them
	hero.floor_snap_length = 0.6
	hero.move_and_slide()
	if speed > 0.1:
		hero_vis.rotation.y = lerp_angle(hero_vis.rotation.y, atan2(-dir.x, -dir.z), 10 * dt)
		walk_t += dt * speed * 1.6
	else: walk_t = lerp(walk_t, round(walk_t / PI) * PI, 8 * dt)
	for l in limbs: l[0].rotation.x = sin(walk_t) * 0.6 * l[1]
	var tgt := hero.position + hero_vis.global_transform.basis.z * 1.3 + hero_vis.global_transform.basis.x * 0.7
	var dp := tgt - pip.position; dp.y = 0
	var gy := height(pip.position.x, pip.position.z) if not (interiors and interiors.active()) else hero.position.y
	if dp.length() > 0.3:
		pip.position += dp * min(1.0, 4.0 * dt)
		pip.rotation.y = lerp_angle(pip.rotation.y, atan2(-dp.x, -dp.z), 8 * dt)
		pip.position.y = gy + abs(sin(Time.get_ticks_msec() * 0.012)) * 0.12
	else: pip.position.y = gy

var _tacc := 0.0
func _process(dt: float) -> void:
	for lm in lava_mats: lm.uv1_offset.x = fmod(lm.uv1_offset.x + dt * 0.02, 1.0); lm.uv1_offset.y = fmod(lm.uv1_offset.y + dt * 0.013, 1.0)
	if fly_controls: fly_controls.visible = VUI.hud != null and VUI.hud.visible and not (VUI.title and VUI.title.visible) and not (sea and sea.active and not (cheats and cheats.flags.fly and not sea.diving))   # test 33: fly buttons at sea only with the fly cheat on
	if Input.is_key_pressed(KEY_SPACE) and hero and hero.is_on_floor(): request_jump()
	_bob_ships(dt)
	if hero == null: return
	if titan_quest == null and party and party.director and volc_base != Vector3.ZERO:
		titan_quest = load("res://scripts/titan_quest.gd").new(); add_child(titan_quest); titan_quest.setup(self)
	_update_door_lights(dt)
	if not bench and not bench_running:
		_tacc += dt
		if _tacc > 0.2: _set_time(tod + _tacc * speed_x * 24.0 / DAY_SECONDS); _tacc = 0.0
	cam_pivot.position = hero.position + Vector3(0, cam_h, 0)
	# test 12 (boss: can't see the Arcane Academy stairs): in walk-in interiors the camera rides high over the walls
	# (floors above are hidden) instead of colliding with them and jamming into the hero's face
	var in_int: bool = interiors != null and interiors.active()
	cam_arm.collision_mask = 0 if in_int else 1
	cam_pivot.rotation = Vector3(minf(pitch, -0.95) if in_int and P_view_third() else pitch, yaw, 0)
	for bl in windmill_blades:
		if bl: bl.rotate_object_local(Vector3(0, 0, 1), dt * 0.8)
	var inside := ""
	for b in buildings:
		var lp: Vector3 = b.node.global_transform.affine_inverse() * hero.global_position
		var a: AABB = b.aabb.grow(-0.6)
		# test 17 (boss: roof missing while flying): only "inside" when the hero is also BELOW the roof line; the footprint-only
		# test hid the Stables roof for a hero flying over it at any height
		var ins: bool = lp.x > a.position.x and lp.x < a.end.x and lp.z > a.position.z and lp.z < a.end.z and lp.y < b.aabb.end.y - 1.0 and not flying_now()
		for rf in b.roofs: rf.visible = not ins
		if ins: inside = b.name
	if interiors and interiors.active(): inside = interiors.current_name()
	_camera_prefs(inside != "", dt)
	_camera_occlusion()
	if VUI.hud and VUI.hud.minimap: VUI.hud.minimap.set_player(Vector2(hero.position.x, hero.position.z), hero_vis.rotation.y)
	if world_map: world_map.tick(dt)   # test 33: fog of war + full map
	VUI.set_fps(Engine.get_frames_per_second())
	lamp_shadow_t -= dt
	if lamp_shadow_t <= 0.0: lamp_shadow_t = 0.5; _update_lamp_shadows()
	_net_tick(dt)
	_where_update(inside, dt)
	ft_acc += dt; ft_n += 1; ft_max = max(ft_max, dt)
	if ft_acc >= 0.5:
		ft_txt = "%.1f ms avg / %.1f ms worst" % [ft_acc / ft_n * 1000.0, ft_max * 1000.0]
		ft_acc = 0.0; ft_n = 0; ft_max = 0.0
	hud_label.visible = bool(VPrefs.prefs.get("showFps", false)) or bench_running
	hud_label.text = "test %s | %s | FPS %d | %s | dc %d | %dk tris | %02d:%02d" % [VERSION, TIERS[tier], Engine.get_frames_per_second(), ft_txt,
		Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000), int(tod), int(fmod(tod, 1.0) * 60)]

## test 25 (boss: the Arcane Academy title stayed up while he flew far outside): a place/interior title shows when
## the hero arrives somewhere new and hides after WHERE_SECS, on leaving, on any door or teleport, and while flying.
const WHERE_SECS := 4.0
var _where_name := ""
var _where_t := 0.0
func _where_update(inside: String, dt: float) -> void:
	if flight or flying_now(): inside = ""
	if inside != _where_name:
		_where_name = inside; _where_t = WHERE_SECS if inside != "" else 0.0
	_where_t = maxf(0.0, _where_t - dt)
	where_label.text = _where_name
	where_label.visible = _where_t > 0.0 and _where_name != ""

func hide_where() -> void:
	_where_t = 0.0
	if where_label: where_label.visible = false

# ---------- in-app benchmark: 10 s fly-through per tier ----------
const FLY := [Vector3(-6, 0, 30), Vector3(0, 0, 44), Vector3(-20, 0, 60), Vector3(0, 0, 120), Vector3(0, 0, 175), Vector3(-30, 0, 90), Vector3(-60, 0, 10), Vector3(-6, 0, 30)]
## test 20 (boss benchmark: Low avg 111 with "cap 60"; mins 12-30): the run now honours the FPS cap, reports a
## 1% low next to the single worst frame, and logs every spike (> 2.5x the median frame and > 25 ms) with what
## happened that frame: pipeline compiles (draw-time = blocking), draw-call / object jumps, script time, lamp-shadow
## re-picks, memory growth. Written to user://benchmark.txt and printed as FLY / SPIKE lines.
var _bench_spikes: Array = []
func _pc() -> Array:
	return [Performance.get_monitor(Performance.PIPELINE_COMPILATIONS_DRAW), Performance.get_monitor(Performance.PIPELINE_COMPILATIONS_SPECIALIZATION),
		Performance.get_monitor(Performance.PIPELINE_COMPILATIONS_SURFACE), Performance.get_monitor(Performance.PIPELINE_COMPILATIONS_MESH)]
func _flythrough(seconds := 10.0) -> Array:
	var t := 0.0; var frames := 0; var worst := 0.0; var warm := 0.5
	var dts: PackedFloat32Array = []; var rows: Array = []
	var pc0 := _pc(); var dc0 := 0.0; var ob0 := 0.0; var mem0 := Performance.get_monitor(Performance.MEMORY_STATIC)
	var lamp0 := lamp_shadow_t
	while t < seconds + warm:
		await get_tree().process_frame
		var dt := get_process_delta_time()
		t += dt
		var u: float = clamp(t / (seconds + warm), 0.0, 0.999) * (FLY.size() - 1)
		var i := int(u); var f := u - i
		var p: Vector3 = FLY[i].lerp(FLY[i + 1], f)
		var d: Vector3 = FLY[i + 1] - FLY[i]
		hero.position = Vector3(p.x, height(p.x, p.z) + 0.1, p.z)
		if d.length() > 0.1: yaw = lerp_angle(yaw, atan2(-d.x, -d.z), 0.08); hero_vis.rotation.y = yaw
		var pc := _pc(); var dc := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME); var ob := Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)
		var mem := Performance.get_monitor(Performance.MEMORY_STATIC)
		if t > warm:
			frames += 1; worst = max(worst, dt); dts.append(dt)
			rows.append([t - warm, dt, i, pc[0] - pc0[0], pc[1] - pc0[1], pc[2] - pc0[2] + pc[3] - pc0[3], dc - dc0, ob - ob0,
				Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0, lamp_shadow_t > lamp0, (mem - mem0) / 1048576.0])
		pc0 = pc; dc0 = dc; ob0 = ob; mem0 = mem; lamp0 = lamp_shadow_t
	var tot := [0, 0, 0]
	for r in rows: tot[0] += r[3]; tot[1] += r[4]; tot[2] += r[5]
	if OS.get_environment("BENCH_COMPLOG") != "":
		for r in rows: if r[3] > 0 or r[4] > 0: print("COMPLOG %s t=%.2f leg %d draw %d spec %d dobj %+d ddc %+d" % [TIERS[tier], r[0], r[2], r[3], r[4], r[7], r[6]])
	_bench_spikes.append("  COMPILES %s during run: draw-time %d, specialization %d, surface/mesh %d" % [TIERS[tier], tot[0], tot[1], tot[2]])
	var sorted := dts.duplicate(); sorted.sort()
	var med: float = sorted[sorted.size() / 2] if sorted.size() > 0 else 0.016
	var p99: float = sorted[int(sorted.size() * 0.99)] if sorted.size() > 0 else 0.016
	for r in rows:
		if r[1] > maxf(med * 2.5, 0.025):
			var why := []
			if r[3] > 0: why.append("%d draw-time pipeline compile(s)" % r[3])
			if r[4] > 0: why.append("%d specialization compile(s)" % r[4])
			if r[5] > 0: why.append("%d surface/mesh pipeline(s)" % r[5])
			if absf(r[6]) > 40: why.append("draw calls %+d" % r[6])
			if absf(r[7]) > 40: why.append("objects %+d" % r[7])
			if r[9] and tier == 3: why.append("lamp shadow re-pick")
			if r[10] > 2.0: why.append("+%.1f MB static mem" % r[10])
			if why.is_empty(): why.append("unknown (GPU/driver, shadow cascade or streaming)")
			_bench_spikes.append("  SPIKE %s t=%.2fs leg %d: %.1f ms - %s" % [TIERS[tier], r[0], r[2], r[1] * 1000.0, ", ".join(why)])
	return [frames / seconds, 1.0 / max(worst, 0.0001), 1.0 / max(p99, 0.0001), med * 1000.0]

func _flythrough_all() -> void:
	bench_running = true
	_bench_spikes = []
	var saved := tier; var lines := ["Benchmark (10 s fly-through each, cap %s)" % (str(fps_cap) if fps_cap > 0 else "off")]
	var order := [0, 1, 2, 3]
	if OS.get_environment("BENCH_TIERS") != "": order = Array(OS.get_environment("BENCH_TIERS").split(",")).map(func(x): return int(x))
	for q in order:
		if OS.get_environment("BENCH_NOAPPLY") == "" or tier != q or order.find(q) == order.rfind(q): tier = q; apply_quality()
		else: tier = q
		if OS.get_environment("BENCH_NOWARM") == "": await _warm_views(); await _warm_interiors(); await _warm_voxel()   # same per-tier warm-up the game does at load (+ voxel-heroes)
		Engine.max_fps = fps_cap   # test 20: the cap used to be switched off (Low read avg 111 under "cap 60")
		bench_label.text = "\n".join(lines) + "\nRunning %s..." % TIERS[q]
		var r: Array = await _flythrough()
		lines.append("%s: avg %.0f FPS, 1%% low %.0f FPS, worst frame %.0f FPS (median %.1f ms)" % [TIERS[q], r[0], r[2], r[1], r[3]])
		bench_label.text = "\n".join(lines)
	tier = saved; apply_quality()
	var top := _bench_spikes.slice(0, 40)
	lines.append("Spikes (%d):" % _bench_spikes.size()); lines.append_array(top)
	# test 20: user://benchmark.txt is app-private on Android (/data/data/com.varnethryl.godottest/files/), so also
	# copy the full report to the clipboard and show the worst spikes on screen.
	DisplayServer.clipboard_set("\n".join(lines))
	var worst := _bench_spikes.filter(func(x): return x.contains("SPIKE"))
	bench_label.text = "\n".join(lines.slice(0, 5)) + "\nSpikes: %d - full report copied to clipboard (paste it in chat)\n%s" % [worst.size(), "\n".join(worst.slice(0, 6))]
	var f := FileAccess.open("user://benchmark.txt", FileAccess.WRITE); f.store_string("\n".join(lines)); f.close()
	print("FLY ", " | ".join(lines.slice(0, 5)))
	for l in top: print(l)
	bench_running = false

# ---------- headless bench / screenshots ----------
func _shot(name: String, pos: Vector3, yw: float, pt: float, hour: float, q: int, frames := 25) -> void:
	tier = q; apply_quality(); _set_time(hour)
	hero.position = pos; hero.position.y = ground_y(pos.x, pos.z) + 0.1; yaw = yw; pitch = pt
	hero_vis.rotation.y = yw
	pip.position = hero.position + Vector3(1, 0, 1)
	for i in frames: await get_tree().process_frame
	var n := 6; var dc := 0.0
	for i in n:
		await get_tree().process_frame
		dc += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	print("BENCH %s tier=%s draw_calls=%d prims=%d objects=%d" % [name, TIERS[q], int(dc / n),
		Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)])
	if not name.begins_with("dc_"):
		get_viewport().get_texture().get_image().save_png("user://shot_%s.png" % name)

func _run_bench() -> void:
	await get_tree().create_timer(0.5).timeout
	var views := [["plaza", Vector3(-6, 0, 30), 0.25, -0.28], ["houses", Vector3(0, 0, 44), PI * 0.82, -0.22],
		["inside", Vector3(-25.2, 0, 52), PI * 0.1, -0.55], ["gate", Vector3(0, 0, 165), 0.0, -0.12],
		["outside", Vector3(30, 0, 240), PI * 0.85, -0.05], ["keep", Vector3(0, 0, -95), 0.0, -0.1]]
	var only := OS.get_environment("BENCH_ONLY")
	if only == "flywarm":   # test 20: boot warm-up as on device, then the in-app benchmark (prints FLY / SPIKE lines)
		_warm_up()
		while not warmed: await get_tree().process_frame
		fps_cap = 60
		await _flythrough_all()
		get_tree().quit(); return
	if only == "" or only == "dc":
		for q in 4:
			for v in views: await _shot("dc_%s_%s" % [v[0], TIERS[q]], v[1], v[2], v[3], 11.0, q, 8)
		for q in 4: await _shot("dc_night_plaza_%s" % TIERS[q], views[0][1], views[0][2], views[0][3], 22.5, q, 8)
	var ST := int(OS.get_environment("SHOT_TIER")) if OS.get_environment("SHOT_TIER") != "" else 2
	var pre: String = String(TIERS[ST]).to_lower() + "_"
	if only == "night":
		await _shot("high_u6_night_plaza", Vector3(-6, 0, 30), 0.25, -0.25, 22.5, 2, 40)
		await _shot("high_u7_night_street", Vector3(0, 0, -20), PI, -0.15, 22.5, 2, 40)
	if only == "gates":
		var fails := 0
		for gd in GATES:
			var d := Vector3(gd[0].x, 0, gd[0].y)
			for leg in [["out", 1.0], ["in", -1.0]]:
				var start: Vector3 = d * (CITY_HALF - 25.0 if leg[1] > 0 else CITY_HALF + 25.0)
				var dir: Vector3 = d * leg[1]
				_teleport(start, atan2(-dir.x, -dir.z)); joy_vec = Vector2(0, -1)
				var t := 0.0; var stuck := 0.0; var last := hero.position
				while t < 14.0:
					await get_tree().physics_frame; t += 1.0 / Engine.physics_ticks_per_second
					yaw = atan2(-dir.x, -dir.z)
					if hero.position.distance_to(last) < 0.02: stuck += 1.0 / Engine.physics_ticks_per_second
					last = hero.position
					var r: float = hero.position.dot(d)
					if (leg[1] > 0 and r > CITY_HALF + 20.0) or (leg[1] < 0 and r < CITY_HALF - 20.0): break
				var r2: float = hero.position.dot(d)
				var ok: bool = (r2 > CITY_HALF + 20.0) if leg[1] > 0 else (r2 < CITY_HALF - 20.0)
				var lateral: float = absf(hero.position.dot(Vector3(d.z, 0, -d.x)))
				ok = ok and lateral < 1.5 and stuck < 0.5
				if not ok: fails += 1
				print("GATE %s %s %s t=%.1fs pos=(%.1f,%.1f,%.1f) lateral=%.2f stuck=%.2fs" % [gd[2], leg[0], "PASS" if ok else "FAIL", t, hero.position.x, hero.position.y, hero.position.z, lateral, stuck])
		joy_vec = Vector2.ZERO
		print("GATES RESULT: %s (%d failures)" % ["ALL PASS" if fails == 0 else "FAIL", fails])
		for gd in GATES:
			var d2 := Vector3(gd[0].x, 0, gd[0].y)
			var pos: Vector3 = d2 * (CITY_HALF + 30.0)
			await _shot("t5_gate_" + String(gd[2]).to_lower().replace(" ", "_"), pos, atan2(d2.x, d2.z), -0.12, 11.0, 2, 30)
		get_tree().quit(1 if fails > 0 else 0)
		return
	if only == "cape":
		var tag := OS.get_environment("CAPE_TAG")
		VUI._enter("solo"); tier = 2; apply_quality(); _set_time(11.0); bench = false
		var cl = get_tree().root.get_node("VUI").hud; cl.visible = false
		VPrefs.prefs["zoom"] = 0.55; VPrefs.prefs["camMode"] = "free"; party.hud.visible = false
		for v in [["back", 0.0], ["side", PI / 2], ["q34", PI / 4]]:
			# idle: hero faces -Z (yaw 0); camera orbits around it
			_teleport(Vector3(-6, 0, 60), 0.0); joy_vec = Vector2.ZERO; cam_arm.spring_length = 3.2
			for i in 240: await get_tree().physics_frame
			yaw = v[1]; pitch = -0.15
			for i in 6: await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png("user://shot_cape_%s_idle_%s.png" % [tag, v[0]])
			# running forward along -Z for 1.2 s; camera keeps the same relative angle
			_teleport(Vector3(-6, 0, 60), 0.0)
			yaw = 0.0
			for i in 72:
				joy_vec = Vector2(0, -1); yaw = 0.0
				await get_tree().physics_frame
			yaw = v[1]
			for i in 3:
				joy_vec = Vector2(0, -1); await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png("user://shot_cape_%s_run_%s.png" % [tag, v[0]])
			joy_vec = Vector2.ZERO
		get_tree().quit()
		return
	if only == "t13":
		VUI._enter("solo"); bench = true
		cheats.role_provider = func() -> String: return "owner"
		for i in 30: await get_tree().process_frame
		var q = titan_quest; var C := VolcanoTitan.CENTER; var B: Vector3 = volc_base
		_set_time(12.0)
		# HUD with Jump (+ Fly unlocked by the menu cheat)
		cheats.request("fly", true)
		await _shot("t13_hud", Vector3(-6, 0, 60), PI / 2, -0.12, 11.0, 2, 30)
		cheats.request("fly", false)
		# boss-like view: high over the rim looking down into the crater (white blob check)
		var vc := Camera3D.new(); vc.far = 1500; add_child(vc)
		vc.look_at_from_position(C + Vector3(-30, 70, 34), C + Vector3(0, 39, 0)); vc.current = true
		await _shot_here("t13_crater_top")
		vc.current = false; cam.current = true
		# intro: hero on a plate facing the pool
		var plate := C + Vector3(20, 0, 8)
		for r in range(14, 30, 2):
			var y: float = ground_y(C.x + r, C.z + 6)
			if y > B.y + 38.9 and y < B.y + 39.4: plate = Vector3(C.x + r, y, C.z + 6); break
		hero.global_position = plate + Vector3(0, 0.5, 0)
		q.accept(); q.start_intro()
		for tt in [0.6, 2.0, 3.6, 4.8, 6.6, 8.4]:
			while q.t_intro < tt: await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png("user://shot_t13_intro_%02d.png" % int(tt * 10)); print("BENCH intro ", tt)
		while q.state != "fight": await get_tree().process_frame
		var gp := plate + Vector3(0, 0.5, 0); hero.global_position = gp
		var yaw2 := atan2(-(C.x - gp.x), -(C.z - gp.z))
		for st in [1, 2, 3]:
			if st > 1:
				q.titan.hp = q.titan.max_hp * (0.6 if st == 2 else 0.3)
				for i in 150: await get_tree().physics_frame
			hero.global_position = gp; party.combat.hp = party.combat.max_hp
			await _shot("t13_stage%d" % st, gp, yaw2, -0.22, 16.0, 2, 40)
			vc.look_at_from_position(C + Vector3(26, 64, 22), C + Vector3(0, 42, 0)); vc.current = true
			await _shot_here("t13_stage%d_wide" % st)
			# test 14: close on the lava veins (chest height, in front of him)
			var tp: Vector3 = q.titan.global_position; var fw: Vector3 = Vector3(gp.x - tp.x, 0, gp.z - tp.z).normalized()
			vc.look_at_from_position(tp + fw * 20.0 + Vector3(0, 22, 0) + fw.cross(Vector3.UP) * 5.0, tp + Vector3(0, 19, 0)); vc.current = true
			await _shot_here("t14_titan_close_stage%d" % st)
			print("T14 stage %d veins=%s glow=%.2f drips=%d prims=%d draws=%d fps=%d" % [st, "shader" if q.titan.lava_hq else "fallback", q.titan.glow_strength,
				q.titan.drips.filter(func(d): return d.emitting).size(), RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME), Engine.get_frames_per_second()])
			vc.current = false; cam.current = true
		q.titan.take_damage(int(q.titan.hp) + 1, C)
		for i in 300: await get_tree().physics_frame
		vc.look_at_from_position(C + Vector3(26, 64, 22), C + Vector3(0, 42, 0)); vc.current = true
		await _shot_here("t13_win")
		print("T13 state=%s stage=%d" % [q.state, q.stage])
		get_tree().quit()
		return
	if only == "t14":
		VUI._enter("solo"); bench = true
		var tag := OS.get_environment("T14_TAG"); if tag == "": tag = "after"
		var hc := Camera3D.new(); hc.far = 3000; add_child(hc)
		_set_time(11.0); tier = 2; apply_quality()
		var tv := [["pond_close", Vector3(-110 + 24, 7, 110 + 16), Vector3(-110, 0, 110)], ["pond_top", Vector3(-109.5, 70, 110.5), Vector3(-110, 0, 110)],
			["wide_n", Vector3(0, 40, -150), Vector3(0, 60, -900)], ["wide_e", Vector3(150, 40, 0), Vector3(900, 60, 0)],
			["wide_s", Vector3(0, 40, 150), Vector3(0, 60, 900)], ["wide_w", Vector3(-150, 40, 0), Vector3(-900, 60, 0)],
			["aerial", Vector3(-300, 520, 700), Vector3(80, 0, -150)], ["volcano_view", Vector3(200, 40, -150), Vector3(405, 60, -402)],
			["port_wide", Vector3(-250, 90, 250), Vector3(-500, 0, 450)],
			["harbor_aerial", Vector3(-380, 140, 470), Vector3(-490, 0, 320)], ["harbor_quay", Vector3(-455, 4, 330), Vector3(-540, 2, 320)],
			["harbor_street", Vector3(-400, 3, 318), Vector3(-470, 4, 296)], ["harbor_cranes", Vector3(-500, 6, 372), Vector3(-530, 6, 322)],
			["coast_w", Vector3(-700, 60, 300), Vector3(-700, 0, 520)],
			["gate_n_aerial", Vector3(25, 45, -160), Vector3(0, 12, -185)], ["gate_e_ground", Vector3(170, 2, 20), Vector3(185, 12, 0)],
			["farm_aerial", Vector3(-250, 60, -250), Vector3(-290, 0, -288)], ["farm_ground", Vector3(-325, 3, -300), Vector3(-290, 6, -288)],
			["obs_aerial", Vector3(100, 70, -100), Vector3(130, 0, -149)], ["obs_ground", Vector3(130, 2, -124), Vector3(130, 10, -149)],
			["street_n", Vector3(-110, 3, -66), Vector3(-30, 4, -66)], ["street_e", Vector3(78, 3, 100), Vector3(78, 4, 20)]]
		if OS.get_environment("T14_TOP_ONLY") != "": tv = []
		for v in tv:
			var a0: Vector3 = v[1]; var t0: Vector3 = v[2]
			a0.y += height(a0.x, a0.z); t0.y += maxf(0.0, height(t0.x, t0.z)) * 0.0
			hc.look_at_from_position(a0, t0, Vector3.UP if absf(a0.x - t0.x) + absf(a0.z - t0.z) > 0.1 else Vector3(0, 0, -1)); hc.current = true
			for i in 40: await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png("user://shot_t14_%s_%s.png" % [tag, v[0]]); print("BENCH ", v[0])
		var oc := hc; oc.projection = Camera3D.PROJECTION_ORTHOGONAL; oc.size = 390.0; oc.position = Vector3(0, 420, 0); oc.rotation = Vector3(-PI / 2, 0, 0)
		env.fog_enabled = false; get_viewport().canvas_cull_mask = 0
		for f in fillers:   # top-down ortho camera is 420 m up: lift the filler LOD visibility ranges for this shot only
			for mi in (f.node as Node).find_children("*", "GeometryInstance3D", true, false): 
				var gi := mi as GeometryInstance3D
				if gi.visibility_range_begin > 0.0: gi.visible = false
				else: gi.visibility_range_end = 0.0
		for i in 40: await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png("user://shot_t14_%s_city_top.png" % tag)
		get_viewport().canvas_cull_mask = 0xFFFFFFFF; env.fog_enabled = true; oc.projection = Camera3D.PROJECTION_PERSPECTIVE
		hc.current = false; cam.current = true
		cheats.role_provider = func() -> String: return "owner"
		cheats.request("fly", true)
		await _shot("t14_%s_hud_ground" % tag, Vector3(-6, 0, 60), PI / 2, -0.12, 11.0, 2, 30)
		set_flight(true)
		await _shot("t14_%s_hud_flying" % tag, Vector3(-6, 0, 60), PI / 2, -0.12, 11.0, 2, 30)
		get_tree().quit()
		return
	if only == "t13city":
		VUI._enter("solo"); bench = true
		var hc := Camera3D.new(); hc.far = 1500; add_child(hc)
		_set_time(11.0); tier = 2; apply_quality()
		var cviews := [["fountain_close", Vector3(14, 5, 14), Vector3(0, 2, 0)], ["fountain_top", Vector3(0.5, 60, 0.5), Vector3(0, 0, 0)]]
		for b in buildings:
			if b.id == "mage" or b.id == "farmhouse":
				var f: Vector3 = b.node.global_transform.basis.z; var c: Vector3 = b.node.global_position
				var r := 26.0 if b.id == "farmhouse" else 22.0
				for k in 4:
					var dir := f.rotated(Vector3.UP, k * PI / 2)
					cviews.append(["%s_side%d" % [b.id, k], c + dir * r + Vector3(0, 2.2, 0), c + Vector3(0, 3.0, 0)])
		for gd in GATES:
			var out := Vector3(gd[0].x, 0, gd[0].y)
			cviews.append(["gate_%d_%d_out" % [int(out.x), int(out.z)], out * (CITY_HALF + 22) + Vector3(0, 4, 0), out * CITY_HALF + Vector3(0, 4, 0)])
			cviews.append(["gate_%d_%d_in" % [int(out.x), int(out.z)], out * (CITY_HALF - 18) + Vector3(0, 2.2, 0), out * CITY_HALF + Vector3(0, 1, 0)])
		cviews.append(["crossroads", Vector3(75 - 12, 7, 70 + 12), Vector3(75, 0, 70)])
		cviews.append(["crossroads2", Vector3(-75 + 12, 7, -70 - 12), Vector3(-75, 0, -70)])
		for v in cviews:
			var a: Vector3 = v[1]; var t: Vector3 = v[2]
			a.y += height(a.x, a.z); t.y += height(t.x, t.z)
			hc.look_at_from_position(a, t, Vector3.UP if absf(a.x - t.x) + absf(a.z - t.z) > 0.1 else Vector3(0, 0, -1)); hc.current = true
			for i in 30: await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png("user://shot_t13c_%s.png" % v[0]); print("BENCH ", v[0])
		get_tree().quit()
		return
	if only == "t11fly":
		VUI._enter("solo"); bench = true
		cheats.role_provider = func() -> String: return "owner"
		cheats.request("fly", true)   # test 13: the menu cheat unlocks the HUD button
		await _shot("t11_hud_ground", Vector3(-6, 0, 60), PI / 2, -0.12, 11.0, 2, 30)
		fly_controls.fly_btn.button_pressed = true
		fly_controls.up_btn.button_down.emit()
		for i in 20: await get_tree().process_frame
		fly_controls.up_btn.button_up.emit()
		await _shot("t11_hud_flying", hero.position, PI / 2, -0.12, 11.0, 2, 60)
		print("FLY on=%s alt=%.1f hero_y=%.1f ground=%.1f" % [cheats.flags.fly, fly_alt, hero.position.y, height(hero.position.x, hero.position.z)])
		get_tree().quit()
		return
	if only == "t11city":
		VUI._enter("solo"); bench = true
		var tag := OS.get_environment("CITY_TAG")
		var oc := Camera3D.new(); oc.projection = Camera3D.PROJECTION_ORTHOGONAL; oc.size = 400.0; oc.far = 1500; add_child(oc)
		oc.position = Vector3(0, 420, 0); oc.rotation = Vector3(-PI / 2, 0, 0); oc.current = true; oc.size = 390.0
		env.fog_enabled = false; env.volumetric_fog_enabled = false; _set_time(12.0)
		get_viewport().canvas_cull_mask = 0   # no HUD in the overview
		hero.position = Vector3(0, height(0, 120) + 0.2, 120)
		await _shot_here("t12_city_%s_top" % tag)
		get_viewport().canvas_cull_mask = 0xFFFFFFFF
		oc.projection = Camera3D.PROJECTION_PERSPECTIVE; oc.fov = 60
		oc.look_at_from_position(Vector3(0, 45, 120), Vector3(0, 0, 185)); await _shot_here("t12_city_%s_southgate" % tag)
		oc.look_at_from_position(Vector3(0, 45, -120), Vector3(0, 0, -185)); await _shot_here("t12_city_%s_northgate" % tag)
		oc.current = false; cam.current = true
		get_tree().quit()
		return
	if only == "t12volcano":
		VUI._enter("solo"); bench = true; _set_time(12.0)
		var vt0 := VolcanoTitan.new(); party.director.add_child(vt0); vt0.setup_volcano(Callable(self, "ground_y"))
		for i in 10: await get_tree().physics_frame
		var vc := Camera3D.new(); vc.far = 2500; add_child(vc); vc.current = true
		var aj: Array = volc_vj.arena.center; var ar := volc_base + Vector3(aj[0], aj[1], aj[2])
		vc.look_at_from_position(volc_base + Vector3(-330, 60, 260), volc_base + Vector3(0, 30, 0)); await _shot_here("t12_volcano_far")
		vc.look_at_from_position(ar + Vector3(-60, 60, 70), ar); await _shot_here("t12_volcano_caldera")
		var ps: Array = volc_vj.path.start
		vc.look_at_from_position(volc_base + Vector3(ps[0] - 30, ps[1] + 14, ps[2] + 30), volc_base + Vector3(ps[0] + 20, ps[1] + 8, ps[2] - 10)); await _shot_here("t12_volcano_path_foot")
		var titan: Node3D = null
		titan = vt0
		if titan: vc.look_at_from_position(titan.global_position + Vector3(-35, 25, 35), titan.global_position + Vector3(0, 10, 0)); await _shot_here("t12_volcano_titan")
		print("TITAN at %s (arena %s, ground %.1f)" % [titan.global_position if titan else null, ar, ground_y(ar.x, ar.z)])
		# walk the path from the foot: the hero must climb it on the collision
		vc.current = false; cam.current = true
		var cl: Array = volc_vj.path.centerline; var w0: Array = cl[0]
		hero.global_position = volc_base + Vector3(w0[0], w0[1] + 1.0, w0[2])
		var best := 0.0; var wi := 1; var stuck := 0
		for i in 9000:
			if wi >= cl.size(): break
			var wp: Array = cl[wi]; var tg := volc_base + Vector3(wp[0], wp[1], wp[2])
			var d := Vector3(tg.x - hero.global_position.x, 0, tg.z - hero.global_position.z)
			if d.length() < 2.0: wi += 1; continue
			yaw = atan2(-d.x, -d.z); joy_vec = Vector2(0, -1)
			await get_tree().physics_frame
			best = maxf(best, hero.global_position.y - volc_base.y)
		joy_vec = Vector2.ZERO
		print("VOLCANO_PATH reached %d/%d waypoints, max height %.1f m above the base, end %s" % [wi, cl.size(), best, hero.global_position - volc_base])
		await _shot("t12_volcano_hero_arena", hero.global_position, yaw, -0.3, 11.0, 2, 10)
		get_tree().quit()
		return
	if only == "t11mage":
		VUI._enter("solo"); bench = true
		for b in buildings: if b.id == "mage": interiors.enter(b)
		for i in 30: await get_tree().physics_frame
		var info: Dictionary = interiors.cur
		var k := 0
		for st in info.stairs:
			var foot: Vector3 = (info.node as Node3D).to_global(st.base + st.dir * (st.run * 0.5) + Vector3(0, st.rise * 0.5, 0))
			hero.global_position = foot + Vector3(0, 0.1, 0); hero.velocity = Vector3.ZERO
			yaw = atan2(st.dir.x, st.dir.z)
			for i in 30: await get_tree().physics_frame
			# detached view (the follow cam hugs the hero in the narrow tower): from the stair top, back toward the hero
			await _shot_here("t12_mage_stair%d_gamecam" % k)
			var vc := Camera3D.new(); vc.fov = 80; add_child(vc)
			var ntop: Vector3 = (info.node as Node3D).to_global(st.base + st.dir * (st.run + 0.6) + Vector3(0, st.rise + 1.7, 0))
			vc.look_at_from_position(ntop, hero.global_position + Vector3(0, 0.6, 0)); vc.current = true
			await _shot_here("t11_mage_stair%d" % k); k += 1
			vc.current = false; cam.current = true; vc.queue_free()
		get_tree().quit()
		return
	if only == "t11stairs":
		VUI._enter("solo"); bench = true
		# walk the hero from the dry shore east of the lighthouse up its stairs: waypoints in the island's model space
		var lh := get_node("Lighthouse") as Node3D
		var wps := [Vector3(3.5, 0, 19.0), Vector3(3.2, 0, 13.0), Vector3(2.5, 0, 9.0), Vector3(2.0, 0, 6.0), Vector3(0.5, 0, 2.0)]
		var w0: Vector3 = lh.to_global(wps[0])
		await _shot("t11_lighthouse_shore", Vector3(w0.x + 6.0, 0, w0.z), PI / 2, -0.15, 13.0, 2, 30)
		hero.position = Vector3(w0.x, height(w0.x, w0.z) + 0.3, w0.z)
		var best := -99.0; var wi := 1
		for i in 900:
			if wi >= wps.size(): break
			var tgt: Vector3 = lh.to_global(wps[wi])
			var d := Vector3(tgt.x - hero.position.x, 0, tgt.z - hero.position.z)
			if d.length() < 0.8: wi += 1; continue
			yaw = atan2(-d.x, -d.z); joy_vec = Vector2(0, -1)
			await get_tree().physics_frame
			best = maxf(best, hero.position.y)
		joy_vec = Vector2.ZERO
		print("STAIRS start_y=%.2f max_y=%.2f reached_wp=%d/%d end=%s" % [height(w0.x, w0.z), best, wi, wps.size(), hero.position])
		var lc := Camera3D.new(); lc.far = 800; add_child(lc)
		lc.look_at_from_position(lh.to_global(Vector3(14, 16, 22)), hero.position + Vector3(0, 1, 0)); lc.current = true
		for i in 20: await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png("user://shot_t11_lighthouse_top.png")
		lc.current = false; cam.current = true; lc.queue_free()
		get_tree().quit()
		return
	if only == "t10":
		VUI._enter("solo"); bench = true
		var hs := harbour_spot(); var hb: Vector2 = hs[0]
		# close: on the quay road east of the shops, looking west across the harbour to the sea
		await _shot("t10_harbour_close", Vector3(hb.x + 40, 0, hb.y - 4), PI / 2, -0.08, 14.0, 2, 40)
		await _shot("t10_harbour_close_lowtier", Vector3(hb.x + 40, 0, hb.y - 4), PI / 2, -0.08, 14.0, 0, 30)
		var hc := Camera3D.new(); hc.far = 1500; add_child(hc)
		for v in [["overview", Vector3(PORT.x + 130, 70, PORT.y - 110), Vector3(PORT.x - 20, 0, PORT.y + 10)],
				["docks", Vector3(hb.x - 45, 12, hb.y - 40), Vector3(hb.x - 6, 1, hb.y)],
				["lighthouse", Vector3(SEA_COAST_X + 50, 18, PORT.y + 30), Vector3(SEA_COAST_X - 4, 4, PORT.y + 62)],
				["from_road", Vector3(-387, 6, 322), Vector3(hb.x, 2, hb.y)],
				["corner_map", Vector3(-200, 420, 200), Vector3(-430, 0, 400)],
				["ships_moored", Vector3(hb.x - 30, 9, hb.y - 38), Vector3(hb.x - 25, 2, hb.y + 3)],
				["ships_sea", Vector3(hb.x - 20, 14, hb.y + 70), Vector3(hb.x - 120, 2, hb.y)],
				["ship_close", Vector3(hb.x - 18 + 16, 7, hb.y - 23 - 20), Vector3(hb.x - 18, 4, hb.y - 23)],
				["ship_waterline", Vector3(hb.x - 18 + 14, 1.2, hb.y - 23 - 4), Vector3(hb.x - 18, 0.5, hb.y - 23)],
				["road_hairpin", Vector3(330, height(330, 330) + 30, 330), Vector3(304, height(304, 356), 356)],
				["road_hairpin_low", Vector3(318, height(318, 340) + 3, 340), Vector3(304, height(304, 356), 356)],
				["road_north_gate", Vector3(0, height(0, -230) + 14, -230), Vector3(0, height(0, -180), -180)],
				["farmstead", Vector3(-92, 22, 78), Vector3(-134, 3, 46)],
				["boats_close", Vector3(hb.x - 2, 4, hb.y + 12), Vector3(hb.x - 10, 1, hb.y + 12)],
				["castle_" + OS.get_environment("CASTLE_TAG"), Vector3(395, height(395, -40) + 4, -40), Vector3(480, 25, -110)]]:
			hc.look_at_from_position(v[1], v[2]); hc.current = true
			for i in 40: await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png("user://shot_t10_%s.png" % v[0])
		hc.current = false; cam.current = true; hc.queue_free()
		get_tree().quit()
		return
	if only == "t9":
		VUI._enter("solo"); bench = true
		# camera fade: a frost troll parked between the camera and the hero (camera sits behind the hero, +Z at yaw 0)
		var hp := Vector3(30, 0, 120)
		var tr: Enemy = party.director.spawn("frosttroll_a", hp + Vector3(0, 0, 9), hero)
		tr.set_process(false); tr.set_physics_process(false)
		tr.global_position = Vector3(hp.x + 0.6, height(hp.x, hp.z + 3.2), hp.z + 3.2)
		await _shot("t9_camera_fade_troll", hp, 0.0, -0.12, 11.0, 2, 30)
		print("FADE faded=%d arm=%.2f cam=%s hero=%s troll=%s" % [_faded.size(), cam_arm.spring_length, cam.global_position, hero.global_position, tr.global_position])
		tr.queue_free()
		# backdrop castle seen from the east gate road (temporary camera aimed at it)
		_set_time(16.0)
		var c := Camera3D.new(); c.far = 1500; add_child(c)
		c.global_position = Vector3(200, 14, -20); c.look_at(Vector3(480, height(480, -110) + 30, -110)); c.current = true
		for i in 30: await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png("user://shot_t9_backdrop_castle.png")
		c.current = false; cam.current = true; c.queue_free()
		# harbour on the lake + night door lights
		var hs := harbour_spot(); var hb: Vector2 = hs[0]
		var tv := (Vector2.ZERO - hb).normalized()   # look at the harbour from the town side
		var hp2 := hb + tv * 45.0
		await _shot("t9_harbour_day", Vector3(hp2.x, 0, hp2.y), atan2(tv.x, tv.y), -0.05, 14.0, 2, 40)
		# overview from the shore side-on (lake on the right): quay, piers and boats should face the water
		var hin: Vector2 = hs[1]; var side := Vector2(-hin.y, hin.x)
		var hc := Camera3D.new(); hc.far = 800; add_child(hc)
		var eye := hb + side * 55.0 + hin * 25.0
		hc.look_at_from_position(Vector3(eye.x, 22, eye.y), Vector3(hb.x + hin.x * 6.0, 1, hb.y + hin.y * 6.0)); hc.current = true
		for i in 30: await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png("user://shot_t9_harbour_overview.png")
		hc.current = false; cam.current = true; hc.queue_free()
		await _shot("t9_door_lights_night", Vector3(0, 0, 38), PI * 0.85, -0.12, 22.5, 2, 40)
		print("DOORLIGHTS on=%d total=%d" % [active_door_lights(), door_lights.size()])
		for q in 4:
			await _shot("dc_t9_town_night_q%d" % q, Vector3(0, 0, 38), PI * 0.85, -0.12, 22.5, q, 20)
			print("DOORLIGHTS tier=%d on=%d" % [q, active_door_lights()])
		get_tree().quit()
		return
	if only == "t8":
		VUI._enter("solo"); bench = true
		var part := OS.get_environment("T8_PART")
		if part == "" or part == "a":
			VPrefs.prefs["zoom"] = 0.5
			await _shot("t8_pip_owner", Vector3(-6, 0, 60), PI / 2, -0.12, 11.0, 2, 40)
			VPrefs.prefs["zoom"] = 1.0
			await _shot("t8_camera_troll_behind", Vector3(52, 0, 241), 0.0, -0.15, 11.0, 2, 40)
			await _shot("t8_night_plaza", Vector3(0, 0, -20), PI, -0.12, 22.5, 2, 40)
			await _shot("t8_night_street", Vector3(0, 0, 38), PI * 0.85, -0.12, 22.5, 2, 40)
			await _shot("t8_street_kit_day", Vector3(42, 0, 0), -PI / 2, -0.1, 11.0, 2, 30)
			await _shot("t8_backdrop_castle", Vector3(150, 0, 0), -PI / 2, 0.04, 17.0, 2, 40)
		if part == "c":
			await _shot("t8_backdrop_castle", Vector3(150, 0, 0), -PI / 2, 0.04, 17.0, 2, 40)
		if part == "" or part == "b":
			for id in ["inn", "library", "farmhouse", "colosseum", "house2"]:
				for b in buildings:
					if b.id != id: continue
					_set_time(11.0); interiors.enter(b)
					for i in 40: await get_tree().process_frame
					get_viewport().get_texture().get_image().save_png("user://shot_t8_interior_%s.png" % id)
					interiors.exit()
					for i in 5: await get_tree().process_frame
		get_tree().quit()
		return
	if only == "t6":
		VUI._enter("solo"); bench = true
		var part := OS.get_environment("T6_PART")
		if part != "enemies":
			await _shot("t6_houses", Vector3(0, 0, 38), PI * 0.85, -0.12, 11.0, 2, 30)
			await _shot("t6_inn_smithy", Vector3(42, 0, 0), -PI / 2, -0.1, 11.0, 2, 30)
			await _shot("t6_apothecary_bakery", Vector3(-42, 0, 42), PI / 2 + 0.3, -0.1, 11.0, 2, 30)
			await _shot("t6_guildhall", Vector3(0, 0, -28), 0.0, -0.05, 11.0, 2, 30)
			await _shot("t6_party_plaza", Vector3(-6, 0, 30), 0.25, -0.28, 11.0, 2, 10)
			for c in party.companions: c.node.global_position = hero.global_position + Vector3(1.6, 0, -2.0) * (1 + party.companions.find(c))
			pitch = -0.2
			for i in 20: await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png("user://shot_t6_party_plaza.png")
		if part == "buildings": get_tree().quit(); return
		for sp in EnemyDirector.SPAWNS: party.director.spawn(sp[0], sp[1], hero)
		for e in party.director.living(): e.set_process(false); e.set_physics_process(false)   # pose them for the photo
		await _shot("t6_wolves", Vector3(-216, 0, 24), PI / 2, -0.2, 11.0, 2, 40)
		await _shot("t6_frost_trolls", Vector3(46, 0, 218), PI, -0.05, 11.0, 2, 40)
		await _shot("t6_ashen_titan", Vector3(-70, 0, 236), PI, 0.15, 11.0, 2, 40)
		bench = false
		_teleport(Vector3(-218, 0, 24), PI / 2); pitch = -0.2
		for i in 30: await get_tree().process_frame
		party.combat.use(1)
		for i in 10: await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png("user://shot_t6_combat_hud.png")
		get_tree().quit()
		return
	if only == "t5":
		var sv := func(n: String, fr := 12):
			for i in fr: await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png("user://shot_%s.png" % n)
		tier = 2; apply_quality(); _set_time(10.5)
		VUI._enter("solo"); _teleport(Vector3(-6, 0, 30), 0.25); pitch = -0.28
		bench = false
		_warm_up(); await sv.call("t5_boot_label", 3)
		while not warmed: await get_tree().process_frame
		cheats.role_provider = func() -> String: return "owner"   # bench-only stand-in for the unlocked owner gate
		_teleport(Vector3(0, 0, 60), 0.0); pitch = -0.2
		party.director.spawn("frosttroll_a", Vector3(0, 0, 50), hero)
		for i in 30: await get_tree().process_frame
		party.combat.use(0); await sv.call("t5_combat", 8)
		party.combat.use(1); await sv.call("t5_combat_skill", 10)
		VUI._set_owner(true); VUI.open_settings(true)
		var sc: ScrollContainer = VUI.settings.find_children("*", "ScrollContainer", true, false)[0]
		for i in 8:
			await sv.call("t5_owner_panel_%d" % i, 8)
			var bar := sc.get_v_scroll_bar()
			if sc.scroll_vertical >= bar.max_value - sc.size.y - 2: break
			sc.scroll_vertical += int(sc.size.y * 0.85)
		VUI.settings.hide(); VUI._set_owner(false)
		cheats.role_provider = func() -> String: return "coowner"
		VUI.open_settings(true)
		sc = VUI.settings.find_children("*", "ScrollContainer", true, false)[0]
		for i in 4:
			await sv.call("t5_coowner_panel_%d" % i, 8)
			var bar2 := sc.get_v_scroll_bar()
			if sc.scroll_vertical >= bar2.max_value - sc.size.y - 2: break
			sc.scroll_vertical += int(sc.size.y * 0.85)
		get_tree().quit()
		return
	if only == "ui":
		var sv := func(n: String):
			for i in 20: await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png("user://shot_%s.png" % n)
		tier = 3; apply_quality(); _set_time(10.5); _teleport(Vector3(-6, 0, 30), 0.25); pitch = -0.28
		VUI.show_title(); await sv.call("t4_title")
		VUI._enter("solo"); VUI.play_solo.emit(); _teleport(Vector3(-6, 0, 30), 0.25); VPrefs.prefs["showFps"] = true
		await sv.call("t4_hud_minimap")
		VUI.open_settings(); await sv.call("t4_settings")
		VUI.settings.hide(); VUI.open_settings(true); await sv.call("t4_settings_dev")
		VUI.settings.hide()
		bench = false
		await _shot("t4_ultra_day", Vector3(-6, 0, 30), 0.25, -0.28, 10.5, 3, 30)
		await _shot("t4_ultra_day_cherry", Vector3(-114, 0, 176), 0.0, -0.05, 12.0, 3, 30)
		await _shot("t4_ultra_night", Vector3(-6, 0, 30), 0.25, -0.25, 22.5, 3, 40)
		await _shot("t4_ultra_night_street", Vector3(0, 0, -20), PI, -0.15, 22.5, 3, 40)
	if only == "fly":
		await _flythrough_all()
	if only == "" or only == "shots":
		await _shot(pre + "u1_day_plaza", Vector3(-6, 0, 30), 0.25, -0.28, 10.5, ST, 30)
		await _shot(pre + "u2_houses", Vector3(0, 0, 44), PI * 0.82, -0.22, 14.0, ST)
		await _shot(pre + "u3_cherry_closeup", Vector3(-150, 0, 165.5), 0.0, 0.3, 12.0, ST)
		await _shot(pre + "u3b_tree_row", Vector3(-114, 0, 176), 0.0, -0.05, 12.0, ST)
		await _shot(pre + "u4_sunset_gate", Vector3(0, 0, 150), 0.0, -0.05, 18.2, ST)
		await _shot(pre + "u5_sunset_outside", Vector3(30, 0, 240), PI * 0.85, -0.02, 17.6, ST)
		await _shot(pre + "u10_lake", Vector3(250, 0, -120), 0.0, -0.25, 15.0, ST)
		await _shot(pre + "u9_noon_mountains", Vector3(-20, 0, 250), PI * 1.15, 0.05, 12.0, ST)
		await _shot(pre + "u6_night_plaza", Vector3(-6, 0, 30), 0.25, -0.25, 22.5, ST, 40)
		await _shot(pre + "u7_night_street", Vector3(0, 0, -20), PI, -0.15, 22.5, ST, 40)
		await _shot(pre + "u8_inside", Vector3(-25.2, 0, 52), PI * 0.1, -0.55, 12.0, ST)
		await _shot("low_day_plaza", Vector3(-6, 0, 30), 0.25, -0.28, 10.5, 0)
	get_tree().quit()


# ---------- test 4: UI / prefs / save / net hooks ----------
func _hook_ui() -> void:
	VPrefs.changed.connect(func(_p):
		if bench_running: return
		var t := VPrefs.tier()
		var changed := t != tier
		if changed: tier = t
		apply_quality()
		if changed: _warm_veiled())
	VUI.menu_toggled.connect(func(o): menu_open = o)
	VUI.get_snapshot = func() -> Dictionary:
		return {"x": hero.position.x, "z": hero.position.z, "yaw": yaw, "zone": "village", "hero": int(VSave.state.get("active", 0))}
	VUI.play_solo.connect(_on_play_solo)
	VUI.multiplayer_requested.connect(_on_multiplayer)
	VUI.travel_requested.connect(_on_travel)
	VUI.returned_to_title.connect(func(): Net.leave(); _clear_remotes(); menu_open = false)
	VUI.dev_action.connect(_on_dev_action)
	cheats = Cheats.new(); cheats.name = "Cheats"; add_child(cheats); cheats.setup(self, party)
	cheats.role_provider = func() -> String:
		if VUI.gate and VUI.gate.is_owner(): return "owner"
		if cheats.coowner_ok and Net.is_online(): return "coowner"
		return ""
	cheats.said.connect(_toast)
	VUI.cheat_api = cheats
	# test 11: on-screen Fly / ▲ / ▼ for the Owner and CoOwner (ui/fly_controls.gd), menu toggle kept in sync
	var fl := CanvasLayer.new(); fl.layer = 5; fl.name = "FlyLayer"; add_child(fl)
	fly_controls = FlyControls.new(); fly_controls.cheats = cheats; fly_controls.main = self; fl.add_child(fly_controls)
	cheats.changed.connect(func(k, _v): if k == "fly" and VUI.settings and VUI.settings.visible: VUI.settings.build())
	if cheats.role() == "owner" and not bench: cheats.request("god", true)   # JS: god starts ON for the owner
	VUI.owner_cheat.connect(func(k, v):
		var key: String = {"titan": "titan", "remax": "remax", "nocd": "nocd"}.get(k, k)
		if key == "lock": return
		cheats.request(key, v))
	Net.coowner_event.connect(func(m):
		match str(m.get("type", "")):
			"coowner-auth": cheats.coowner_ok = m.get("ok") == true
			"coowner-locked": cheats.coowner_ok = false
		if VUI.settings.visible: VUI.settings.build())
	Net.disconnected.connect(func(_c, _r): cheats.coowner_ok = false)
	VUI.hero_selected.connect(func(id: int):
		var hid := _roster_id(id)
		if hid != "" and party.hero_id != hid: party.set_hero(hid))
	var act_id := _roster_id(int(VSave.state.get("active", 0)))
	# the boss plays as the Owner: an unlocked owner gate always starts on the Owner hero (HUD said "Hero: Aldric")
	if VUI.gate and VUI.gate.is_owner(): party.set_hero("owner")
	elif act_id != "" and not bench: party.set_hero(act_id)
	VUI.owner_set.connect(func(on: bool): if on and not bench and party.hero_id != "owner": party.set_hero("owner"))
	Net.state_provider = func() -> Dictionary:
		var st: Dictionary = party.net_state(); st.erase("position"); st.erase("heading")
		for k in ["x", "y", "z"]: st[k] = float(st[k]) * JS_UNITS
		return st
	# RemotePlayer.bind expects Net-like signals: feed it a proxy that converts JS world units -> metres
	net_proxy = load("res://net/net_unit_proxy.gd").new(); net_proxy.name = "NetUnitProxy"; add_child(net_proxy)
	var conv := func(p: Dictionary) -> Dictionary:
		var q := p.duplicate()
		for k in ["x", "y", "z"]: if q.has(k): q[k] = float(q[k]) / JS_UNITS
		if (q.has("zone") and str(q.zone) != "village" and str(q.zone) != "town"): q["x"] = 0.0; q["z"] = -10000.0   # other zone: park far away
		return q
	Net.peer_joined.connect(func(p): if str(p.get("id", "")) != Net.self_id: net_proxy.emit_signal("peer_joined", conv.call(p)))
	Net.peer_state.connect(func(p): if str(p.get("id", "")) != Net.self_id: net_proxy.emit_signal("peer_state", conv.call(p)))
	Net.peer_left.connect(func(i): net_proxy.emit_signal("peer_left", str(i)))
	remotes = RemotePlayer.bind(net_proxy, self)
	Net.welcomed.connect(func(info):
		for pl in info.get("players", []): if str(pl.get("id", "")) != Net.self_id: net_proxy.emit_signal("peer_joined", conv.call(pl))
		var sp = info.get("spawn")
		if typeof(sp) == TYPE_DICTIONARY and sp.has("x"): _teleport(Vector3(float(sp.x) / JS_UNITS, 0, float(sp.get("z", 0)) / JS_UNITS), float(sp.get("yaw", yaw))))
	Net.disconnected.connect(func(_c, _r): _clear_remotes())
	_build_minimap()
	world_map = WorldMap.new().setup(self)   # test 33: tap the minimap -> whole-world map with fog of war
	var wl := CanvasLayer.new(); wl.layer = 50; add_child(wl); wl.add_child(world_map)
	if VUI.hud and VUI.hud.minimap: VUI.hud.minimap.tapped.connect(world_map.toggle)

func _teleport(p: Vector3, yw: float) -> void:
	hide_where()   # test 25
	hero.position = Vector3(p.x, height(p.x, p.z) + 0.2, p.z); hero.velocity = Vector3.ZERO
	yaw = yw; hero_vis.rotation.y = yw; pip.position = hero.position + Vector3(1, 0, 1)
	if party and party.rig and party.rig.cloth: party.rig.cloth.call_deferred("reset")   # no cape fling on teleport

func _on_play_solo() -> void:
	Net.leave(); _clear_remotes()
	var pos = VSave.read_pos(VSave.read_save().get("state"), CITY_HALF * 3.0)
	if pos != null: _teleport(Vector3(pos.x, 0, pos.z), pos.yaw)

func _on_multiplayer(world: String) -> void:
	var w := world if world != "" else "Liongate-1"
	w = {"Liongate-1": "WORLD1", "Liongate-2": "WORLD2", "Ashen-Ruins": "WORLD3"}.get(w, w)  # server codes: ^[A-Z0-9]{4,12}$
	var nick := str(VSave.state.get("nickname", VSave.state.get("name", "Hero")))
	if nick.length() < 2: nick = "Hero"
	Net.join(w, nick)

func _on_travel(dest: String) -> void:
	match dest:
		"town": _teleport(Vector3(-6, 0, 26), 0.0)
		"sail":  # test 32: the Tidewrack Sea
			if sea and not sea.active: sea.ui.fade(func(): sea.enter())
		"hydra":  # TODO(port-zones): hydra arena
			_teleport(Vector3(0, 0, 175), PI); _toast("Hydra lair is coming in a later build.")
		_: _toast("Unknown destination: " + dest)

func _toast(t: String) -> void:
	bench_label.text = t
	get_tree().create_timer(3.0).timeout.connect(func(): if bench_label.text == t: bench_label.text = "")

func _on_dev_action(k: String) -> void:
	if not cheats.allowed("dev"): _toast("Developer tools are Owner-only."); return
	match k:
		"time": time_mode = (time_mode + 1) % 4; _save_settings(); _apply_time_mode(); _toast("Time: " + TIME_PRESETS[time_mode][0])
		"speed": speed_x = 10.0 if speed_x == 1.0 else 1.0; _toast("Day speed: %dx" % int(speed_x))
		"fps_cap": fps_cap = 120 if fps_cap == 60 else 60; _save_settings(); apply_quality(); _toast("FPS cap: %d" % fps_cap)
		"benchmark":
			if not bench_running:
				VUI.settings.hide(); VUI.toggle_menu(false); _flythrough_all()
		_: _toast("Dev action '%s' lands with a later branch." % k)

func P_view_third() -> bool: return VPrefs.prefs.get("view", "third") != "first"

func _camera_prefs(inside: bool, dt: float) -> void:
	var P: Dictionary = VPrefs.prefs
	var first: bool = P.get("view", "third") == "first"
	var base := 6.0 * float(P.get("zoom", 1.0))
	var want: float = 0.0 if first else (min(3.5, base) if inside else base)
	if interiors and interiors.active() and not first: want = clampf(base, 5.0, 6.5)   # high over-the-walls view
	if sea and sea.active and not sea.diving: want = sea.cam_dist()   # test 32: deck camera rides high behind the ship
	cam_arm.spring_length = lerpf(cam_arm.spring_length, want, min(1.0, 10.0 * dt))
	hero_vis.visible = not first or bench_running
	# follow mode: drift yaw behind the hero while walking (unless the player is dragging the camera)
	if P.get("camMode", "follow") == "follow" and not first and cam_touch == -1 and joy_vec.length() > 0.2 and not bench_running:
		yaw = lerp_angle(yaw, hero_vis.rotation.y, min(1.0, 1.5 * dt))

var _lamp_shadow_on := {}
func _update_lamp_shadows() -> void:
	# Ultra only: the 3 nearest lit lamps within 28 m cast shadows (Mobile renderer handles a few omni shadows fine).
	if tier != 3:
		return
	var lit := []
	for l in lamp_lights:
		var n: OmniLight3D = l[0]
		if n.visible: lit.append([n.global_position.distance_squared_to(hero.global_position), n])
	lit.sort_custom(func(a, b): return a[0] < b[0])
	for i in lit.size():
		var on: bool = i < 3 and lit[i][0] < 28.0 * 28.0
		if _lamp_shadow_on.get(lit[i][1], null) == on: continue   # test 20: no per-0.5 s re-set of unchanged lights
		_lamp_shadow_on[lit[i][1]] = on
		if on: lit[i][1].shadow_bias = 0.05; lit[i][1].omni_shadow_mode = OmniLight3D.SHADOW_DUAL_PARABOLOID
		lit[i][1].shadow_enabled = on

func _clear_remotes() -> void:
	for id in remotes.keys():
		if is_instance_valid(remotes[id]): remotes[id].queue_free()
		remotes.erase(id)

func _net_tick(dt: float) -> void:
	if Net.is_online():
		net_send_t -= dt
		if net_send_t <= 0.0: net_send_t = 0.1; Net.send_state(Net.state_provider.call())

# --- minimap texture from the town layout ---
func _build_minimap() -> void:
	var N := 256
	var img := Image.create(N, N, false, Image.FORMAT_RGBA8)
	var px := MAP_RECT.size.x / N
	for y in N:
		for x in N:
			var w := MAP_RECT.position + Vector2(x + 0.5, y + 0.5) * px
			var c := Color(0.30, 0.42, 0.22).lerp(Color(0.36, 0.48, 0.26), noise.get_noise_2d(w.x, w.y) * 0.5 + 0.5)
			if w.distance_to(LAKE) < 60.0 or sea_mask(w.x, w.y) > 0.5: c = Color(0.22, 0.42, 0.6)
			var inside_wall := absf(w.x) < CITY_HALF and absf(w.y) < CITY_HALF
			if inside_wall: c = c.lerp(Color(0.45, 0.43, 0.36), 0.35)
			if absf(maxf(absf(w.x), absf(w.y)) - CITY_HALF) < 2.5: c = Color(0.55, 0.52, 0.47)
			if _road_dist(w) < 4.4: c = Color(0.62, 0.55, 0.42)
			if w.distance_to(Vector2(0, 0)) < 18.0: c = Color(0.68, 0.64, 0.56)
			if w.distance_to(Vector2(0, 0)) < 5.0: c = Color(0.35, 0.6, 0.8)
			img.set_pixel(x, y, c)
	for b in buildings:
		var a: AABB = b.aabb; var xf: Transform3D = b.node.global_transform
		var pts := []
		for cx in [a.position.x, a.end.x]:
			for cz in [a.position.z, a.end.z]: var g := xf * Vector3(cx, 0, cz); pts.append(Vector2(g.x, g.z))
		var mn: Vector2 = pts[0]; var mx: Vector2 = pts[0]
		for q in pts: mn = mn.min(q); mx = mx.max(q)
		var r0 := ((mn - MAP_RECT.position) / px).floor(); var r1 := ((mx - MAP_RECT.position) / px).ceil()
		for y in range(maxi(0, int(r0.y)), mini(N, int(r1.y))):
			for x in range(maxi(0, int(r0.x)), mini(N, int(r1.x))):
				var edge: bool = x == int(r0.x) or y == int(r0.y) or x == int(r1.x) - 1 or y == int(r1.y) - 1
				img.set_pixel(x, y, Color(0.32, 0.2, 0.14) if edge else Color(0.62, 0.32, 0.22))
	var tex := ImageTexture.create_from_image(img)
	if VUI.hud and VUI.hud.minimap:
		VUI.hud.minimap.set_map_texture(tex, MAP_RECT)
		var mk := [{"pos": Vector2(0, 0), "color": Color(0.5, 0.8, 1.0), "label": "Plaza"}]
		for gd in GATES: mk.append({"pos": gd[0] * CITY_HALF, "color": Color(1, 0.85, 0.3), "label": gd[2]})
		VUI.hud.minimap.set_markers(mk)

# --- shader warm-up: draw every LOD / tier variant once behind the title screen ---
const WARM_VIEWS := [
	[Vector3(-6, 8, 30), Vector3(-6, 6, -20)], [Vector3(-6, 8, 30), Vector3(44, 6, 30)], [Vector3(-6, 8, 30), Vector3(-6, 6, 80)],
	[Vector3(-6, 8, 30), Vector3(-56, 6, 30)], [Vector3(-6, 60, 30), Vector3(-6, 0, 31)],
	[Vector3(0, 4, 120), Vector3(0, 4, 175)], [Vector3(0, 4, 175), Vector3(0, 10, 260)], [Vector3(-60, 4, 10), Vector3(-6, 4, 30)],
	[Vector3(0, 40, 0), Vector3(250, 0, -120)], [Vector3(0, 40, 0), Vector3(-20, 30, 300)]]
## Draw every LOD band, fx, lamp and the town/bench-path views once at the current tier for day and night.
func _warm_views() -> void:
	var wcam := Camera3D.new(); wcam.fov = 90; wcam.far = 4000; add_child(wcam); wcam.current = true
	var saved_t := tod
	for h in [12.0, 22.5]:
		_set_time(h)
		for t in tree_lods + hi_terrain: t[0].visibility_range_begin = 0; t[0].visibility_range_end = 0; t[0].visible = true
		for b in buildings: for m in _meshes(b.node, []): m.visibility_range_begin = 0; m.visibility_range_end = 0
		for f in fx_any + fx_day + fx_night: f[0].visible = true; f[0].emitting = true
		for l in lamp_lights: l[0].visible = true; l[0].shadow_enabled = tier == 3
		for vp in WARM_VIEWS:
			wcam.look_at_from_position(vp[0], vp[1], Vector3.UP)
			await get_tree().process_frame
		# test 23: wildflowers (both lods), far grass, scatter rocks/bushes/pebbles, ground2 near detail: eye-level views
		for tv in TERRAIN_WARM:
			var e: Vector3 = tv[0]; e.y = height(e.x, e.z) + 1.7
			var lk: Vector3 = tv[1]; lk.y = height(lk.x, lk.z) + 0.5
			wcam.look_at_from_position(e, lk, Vector3.UP)
			await get_tree().process_frame; await get_tree().process_frame
		await get_tree().process_frame
	_set_time(saved_t); apply_quality(); _apply_time_mode()
	cam.current = true; wcam.queue_free()
	for l in lamp_lights: _lamp_shadow_on[l[0]] = l[0].shadow_enabled

func _veil() -> CanvasLayer:
	var veil := ColorRect.new(); veil.color = Color(0.05, 0.04, 0.06); veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	var cl := CanvasLayer.new(); cl.layer = 100; add_child(cl); cl.add_child(veil)
	var lbl := VStyle.label("Preparing shaders…", 22, Color(0.9, 0.85, 0.7))
	lbl.autowrap_mode = TextServer.AUTOWRAP_OFF   # phone bug (test 4): autowrap + zero width = one letter per line
	lbl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	cl.add_child(lbl)
	return cl

## test 20: a graphics-quality change in game changes the global shadow settings (drops compiled pipelines),
## so re-warm the new tier behind the same "Preparing shaders" veil instead of stuttering while walking.
var _rewarming := false
func _warm_veiled() -> void:
	if _rewarming or not warmed: return
	_rewarming = true
	var cl := _veil(); var cam_far := cam.far
	await _warm_views(); await _warm_interiors()   # test 21
	cam.far = cam_far; cl.queue_free(); _rewarming = false

## test 22 (boss: "a lot of places look like this on the inside" - bare stone shell, no props/ceiling, dark window bars):
## the 212 town fillers and the harbour's Harbour Master / Fish Market / Salty Anchor reuse Beth's card2 models, whose
## -colonly collision keeps the door opening walkable, but they had no door trigger - the hero walked into the hollow
## exterior shell. Each now leads to the dressed interior of its model (house1-4, bakery, apothecary, smithy, market, inn).
static var _shell_aabb := {}
func _shell_entry(model: String, label: String, n: Node3D) -> Dictionary:
	if not _shell_aabb.has(model):
		var ab := AABB(); var first := true
		var v: Node3D = load(_card2_path(model, "_lod1")).instantiate()
		for mi in _meshes(v, []):
			var xf := Transform3D(); var q: Node = mi
			while q != v: xf = (q as Node3D).transform * xf; q = q.get_parent()
			var a: AABB = xf * mi.get_aabb()
			if first: ab = a; first = false
			else: ab = ab.merge(a)
		v.free(); _shell_aabb[model] = ab
	return {"id": model, "name": label, "node": n, "aabb": _shell_aabb[model], "rect": Rect2(), "shell": true}

func _register_shell_doors() -> void:
	if interiors == null: return
	for f in fillers:
		if interiors.has_interior(f.model): extra_doors.append(_shell_entry(f.model, String(f.node.get_meta("filler_id", f.id)), f.node))
	if harbor:
		for hb in [["house4", "Harbour Master"], ["market", "Fish Market"], ["inn", "The Salty Anchor (Tavern)"]]:
			var n := harbor.get_node_or_null(NodePath(hb[1]))
			if n and interiors.has_interior(hb[0]): extra_doors.append(_shell_entry(hb[0], hb[1], n))

const TERRAIN_WARM := [[Vector3(40, 0, 262), Vector3(30, 0, 230)], [Vector3(-245, 0, -245), Vector3(-225, 0, -265)], [Vector3(-60, 0, -440), Vector3(-80, 0, -470)], [Vector3(-262, 0, 14), Vector3(-280, 0, 10)]]
## test 21: Beth's interior pass tier (textures + torch lights). InteriorManager caches built interiors, so a tier
## change drops every cached one except the room the hero stands in (that one rebuilds on its next entry).
func _pass_tier_set(t: String) -> void:
	if InteriorManager.pass_tier == t: return
	InteriorManager.pass_tier = t
	if interiors == null: return
	for id in interiors.built.keys():
		if not interiors.cur.is_empty() and interiors.cur == interiors.built[id]: continue
		interiors.built[id].node.queue_free(); interiors.built.erase(id)

## test 21: render a dressed interior (indoor env, sun off, torches) so the pass materials compile behind the veil
const WARM_INTERIORS := ["keep", "temple"]
func _warm_interiors() -> void:
	if interiors == null: return
	var wcam := Camera3D.new(); wcam.fov = 90; add_child(wcam); wcam.current = true
	var sun_v := sun.visible; sun.visible = false; interiors._env_inside(true)
	for id in WARM_INTERIORS:
		if not InteriorDefs.D.has(id): continue
		var info: Dictionary = interiors.get_info(id, Vector3(20, 10, 20))
		var n: Node3D = info.node
		for v in [[Vector3(info.W * 0.18, 1.7, info.D / 2 - 1.2), Vector3(-info.W * 0.25, 2.6, -info.D * 0.2)], [Vector3(-info.W * 0.3, 1.6, info.D * 0.25), Vector3(info.W * 0.45, 3.4, -info.D * 0.3)]]:
			wcam.look_at_from_position(n.to_global(v[0]), n.to_global(v[1]), Vector3.UP)
			await get_tree().process_frame; await get_tree().process_frame
	interiors._env_inside(false); sun.visible = sun_v
	cam.current = true; wcam.queue_free()

## voxel-heroes: show one of each voxel model (heroes, guard, villain) to a warm camera, normal and faded
## (camera-occlusion alpha-hash copy), so their skinned materials compile behind the veil, not mid-walk.
func _warm_voxel() -> void:
	var wcam := Camera3D.new(); wcam.fov = 70; add_child(wcam)
	var root := Node3D.new(); add_child(root); root.global_position = hero.global_position + Vector3(0, 200, 0)
	var paths := HeroRoster.VOXEL.values() + [TownGuards.MODEL, Enemy.TYPES.holyknight_villain.model]
	for i in paths.size():
		var r := CharacterRig.new().setup(paths[i], 1.905); root.add_child(r); r.position = Vector3((i - 2) * 1.2, 0, 0)
	wcam.look_at_from_position(root.global_position + Vector3(0, 1.2, 5.5), root.global_position + Vector3(0, 1.0, 0), Vector3.UP); wcam.current = true
	await get_tree().process_frame; await get_tree().process_frame
	_set_fade(root, true)
	await get_tree().process_frame; await get_tree().process_frame
	root.queue_free(); cam.current = true; wcam.queue_free()

func _warm_up() -> void:
	var saved := tier; var saved_t := tod
	var cl := _veil()
	var cam_far := cam.far
	# test 20: the soft-shadow quality / atlas size are global and changing them drops every compiled pipeline, so
	# warming other tiers first only helped if the player stayed on the last one. Warm the player's own tier LAST.
	var order := [3, 0, 1, 2]; order.erase(saved); order.append(saved)
	for q in order:
		tier = q; apply_quality()
		await _warm_views()
		await _warm_interiors()   # test 21
		await _warm_voxel()   # voxel-heroes
	cam.far = cam_far; tier = saved; _set_time(saved_t); apply_quality(); _apply_time_mode()
	for l in lamp_lights: _lamp_shadow_on[l[0]] = l[0].shadow_enabled
	warmed = true
	cl.queue_free()

func _roster_id(vid: int) -> String:
	if vid < 0 or vid >= VHeroData.RAW.size(): return ""
	for w in String(VHeroData.RAW[vid][0]).to_lower().split(" "):
		if HeroRoster.ORDER.has(w): return w
	return ""

func cheat_tp_place(id: String) -> bool:
	for b in buildings:
		if b.id == id or b.name == id:
			var p: Vector3 = b.node.global_position; _teleport(p + Vector3(0, 0, 6), 0.0); return true
	return false

func cheat_tp_zone(z: String) -> bool:
	match z:
		"village": _teleport(Vector3(-6, 0, 26), 0.0); return true
		"sailing": _on_travel("sail"); return true
		"hydra": _on_travel("hydra"); return true
	_toast("%s is not ported yet." % z); return false


# ---------- test 7: camera vs big characters / companions ----------
## Anything (companions, enemies, remote players) between the camera and the hero fades out; if the camera
## would sit inside a big creature, the arm pulls in in front of it.
var _faded := {}
func _occluders() -> Array:
	var out := []
	if party:
		for c in party.companions: out.append([c.node, c.rig, 0.45])
		for e in party.director.living(): out.append([e, e.rig, float(e.radius)])
	if guards:   # test 25: a gate guard right behind the hero filled the boss's screen; fade it like companions
		for g in guards.guards:
			if (g.node as Node3D).visible: out.append([g.node, g.rig, 0.5])
	for id in remotes:
		var rp = remotes[id]
		if is_instance_valid(rp) and rp.rig: out.append([rp, rp.rig, 0.5])
	return out

func _camera_occlusion() -> void:
	if cam == null or hero == null: return
	var head := hero.global_position + Vector3(0, cam_h, 0)
	var cp := cam.global_position
	var seg := cp - head; var L := seg.length()
	if L < 0.01: return
	var dir := seg / L
	var pull := L
	var now := {}
	for o in _occluders():
		var n: Node3D = o[0]; var rig: CharacterRig = o[1]; var r: float = o[2]
		if not is_instance_valid(n) or rig == null: continue
		var h: float = maxf(rig.target_height, 0.3)
		var base := n.global_position
		# closest point on the camera ray to the creature's vertical axis (cylinder r, height h)
		var t := clampf((base - head).dot(dir), 0.0, L)
		var p := head + dir * t
		var flat := Vector2(p.x - base.x, p.z - base.z).length()
		var inside_h := p.y > base.y - 0.2 and p.y < base.y + h + 0.3
		# camera itself inside the creature's cylinder also counts (after a pull-in the ray can be shorter than it)
		var cam_in := Vector2(cp.x - base.x, cp.z - base.z).length() < r + 0.6 and cp.y > base.y - 0.2 and cp.y < base.y + h + 0.3
		if (flat < r + 0.35 and inside_h and t > 0.2) or cam_in:
			now[n.get_instance_id()] = n
			# big creature behind the hero: pull the arm in front of it only if that leaves the camera clear of it;
			# otherwise keep the arm and just fade the creature (pulling into its body showed only its mesh)
			if r > 1.0 and t - r - 0.6 >= 1.5: pull = minf(pull, t - r - 0.6)
	for k in now:
		if not _faded.has(k): _set_fade(now[k], true)
	for k in _faded:
		if not now.has(k) and is_instance_valid(_faded[k]): _set_fade(_faded[k], false)
	_faded = now
	if pull < L - 0.05:
		cam_arm.spring_length = minf(cam_arm.spring_length, pull)

## Fade to ~30% visible with an alpha-hash dither (works on Mobile, keeps depth sorting sane): duplicate each
## surface's material once with transparency ALPHA_HASH and albedo alpha 0.3; restore the originals on unfade.
const FADE_ALPHA := 0.3
func _set_fade(node: Node, on: bool) -> void:
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh == null: continue
		if on:
			if m.has_meta("fade_orig"): continue
			var orig := []
			for i in m.mesh.get_surface_count():
				orig.append(m.get_surface_override_material(i))
				var src: Material = m.get_active_material(i)
				if src is BaseMaterial3D:
					var d := (src as BaseMaterial3D).duplicate() as BaseMaterial3D
					d.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; d.cull_mode = BaseMaterial3D.CULL_BACK
					d.albedo_color.a = FADE_ALPHA; m.set_surface_override_material(i, d)
			m.set_meta("fade_orig", orig)
			if not (m.get_active_material(0) is BaseMaterial3D): m.transparency = 1.0 - FADE_ALPHA
		elif m.has_meta("fade_orig"):
			var orig: Array = m.get_meta("fade_orig")
			for i in orig.size(): m.set_surface_override_material(i, orig[i])
			m.remove_meta("fade_orig"); m.transparency = 0.0

# ---------- worldboss-test: world-boss Ashen Titan (scripts/world_boss.gd) ----------
var world_boss: WorldBoss
const STORY_CFG := "user://story.cfg"
func volcano_quest_done() -> bool:
	var cf := ConfigFile.new()
	return cf.load(STORY_CFG) == OK and bool(cf.get_value("story", "volcano_done", false))
## called by TitanQuest._win: persist the story flag, then the world boss rises on the outskirts
func on_volcano_quest_done() -> void:
	var cf := ConfigFile.new(); cf.load(STORY_CFG); cf.set_value("story", "volcano_done", true); cf.save(STORY_CFG)
	if OS.get_cmdline_user_args().has("--bench") or bench_running or world_boss != null: return
	get_tree().create_timer(8.0).timeout.connect(func():
		spawn_world_boss(false)
		if has_method("_toast"): _toast("The Ashen Titan stirs beyond the walls..."))
func spawn_world_boss(near_hero := true) -> bool:
	if world_boss == null:
		world_boss = WorldBoss.new(); add_child(world_boss); world_boss.setup(self)
		if party and party.combat: party.combat.used.connect(func(slot, sk): get_tree().create_timer(0.12).timeout.connect(func(): world_boss.on_hero_used(slot, sk, party.hero_id)))
	if near_hero and hero: world_boss.spawn_near(hero.global_position)
	return true

# ---------- test 16: high-altitude flight view (owner can fly far above the map) ----------
var _alt_base := {}
func _altitude_view() -> void:
	if cam == null or env == null: return
	var alt := fly_alt if flying_now() else 0.0
	if alt < 150.0:
		if not _alt_base.is_empty():
			cam.far = _alt_base.far; env.fog_density = _alt_base.fog; env.fog_aerial_perspective = _alt_base.ap; env.fog_sky_affect = _alt_base.sa; _alt_base = {}
		return
	if _alt_base.is_empty(): _alt_base = {"far": cam.far, "fog": env.fog_density, "ap": env.fog_aerial_perspective, "sa": env.fog_sky_affect}
	var y := hero.position.y
	cam.far = maxf(float(_alt_base.far), y * 2.2 + 4500.0)            # whole map + sea stay inside the far plane from any height
	var k := clampf((y - 150.0) / 350.0, 0.0, 1.0)
	env.fog_density = float(_alt_base.fog) * lerpf(1.0, 0.03, k)   # thin the fog with height so the ground is not a white sheet
	env.fog_aerial_perspective = lerpf(float(_alt_base.ap), 0.0, k); env.fog_sky_affect = lerpf(float(_alt_base.sa), 0.0, k)


# test 23: boulder colliders found blocking by tests/boulder_check.gd (1 on a placement/blocker zone, 5 on the volcano quest pad).
const BOULDER_DROP := [Vector2(-873.1,-186.4), Vector2(617.6,-315.9), Vector2(621.2,-325.8), Vector2(213.7,-258.1), Vector2(337.8,-177.6), Vector2(326.2,-198.4)]
func _drop_blocking_boulders() -> void:
	var bc: Node = TerrainScatter.root.get_node_or_null("BoulderCollision") if TerrainScatter.root else null
	if bc == null: return
	for cs in bc.get_children():
		var p: Vector3 = (cs as Node3D).global_position if cs.is_inside_tree() else (cs as Node3D).position
		for d: Vector2 in BOULDER_DROP:
			if Vector2(p.x, p.z).distance_to(d) < 0.3: cs.queue_free(); break
