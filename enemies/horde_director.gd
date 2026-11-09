class_name HordeDirector
extends Node
## One bounded crowd outside the walled town. Not a replacement for wolves, trolls, or the titan.
## Alive count and corpses are capped. Nothing here is written into the save.

const CAP := 16
const HARD_CAP := 24
const CORPSE_CAP := 6
const CORPSE_SEC := 8.0
const REFILL_SEC := 7.0
## Packs stand in the gate openings, past the guard apron, so a player looking out a gate
## sees a crowd. The old ring pressed the wall beside the gates, and the opening showed one body.
## "out" is metres past the outer face. "along" is metres across that gate. The northeast
## wedge is not a gate, so none of these packs sit in it.
const ROSTER := [
	{"id": "shambler", "gate": "south", "along": -4.8, "out": 18.0},
	{"id": "shambler", "gate": "south", "along": -1.6, "out": 18.0},
	{"id": "shambler", "gate": "south", "along": 1.6, "out": 18.0},
	{"id": "shambler", "gate": "south", "along": 4.8, "out": 18.0},
	{"id": "shambler", "gate": "south", "along": -3.2, "out": 23.0},
	{"id": "shambler", "gate": "south", "along": 3.2, "out": 23.0},
	{"id": "runner", "gate": "south", "along": -4.2, "out": 28.0},
	{"id": "runner", "gate": "south", "along": 4.2, "out": 28.0},
	{"id": "undead_knight", "gate": "north", "along": -2.2, "out": 18.0},
	{"id": "undead_knight", "gate": "north", "along": 2.2, "out": 18.0},
	{"id": "shambler", "gate": "north", "along": 0.0, "out": 23.0},
	{"id": "undead_sailor", "gate": "east", "along": -2.2, "out": 18.0},
	{"id": "undead_sailor", "gate": "east", "along": 2.2, "out": 18.0},
	{"id": "runner", "gate": "east", "along": 0.0, "out": 24.0},
	{"id": "shambler", "gate": "west", "along": 0.0, "out": 18.0},
	{"id": "runner", "gate": "west", "along": 0.0, "out": 24.0},
]

var main: Node
var slots: Array = []
var noise_at := Vector2.ZERO
var noise_r := 0.0
var noise_t := 0.0
var refill_t := REFILL_SEC
var spawned := 0
var culled := 0

func setup(m: Node) -> void:
	main = m
	name = "Horde"
	for spec in ROSTER:
		var pos := spawn_pos(spec)
		var z := _spawn_slot(spec, pos)
		slots.append({"spec": spec, "node": z})
	var combat = m.party.combat if m.get("party") else null
	if combat and not combat.used.is_connected(_on_combat):
		combat.used.connect(_on_combat)

static func _gate_dir(gate: String) -> Vector2:
	match gate:
		"north": return Vector2(0, -1)
		"east": return Vector2(1, 0)
		"west": return Vector2(-1, 0)
		_: return Vector2(0, 1)

static func spawn_pos(spec: Dictionary) -> Vector3:
	if spec.has("gate"):
		var dir := _gate_dir(str(spec.gate))
		var along := Vector2(-dir.y, dir.x)
		var p := dir * (TownHaven.outer_limit() + float(spec.out)) + along * float(spec.along)
		return Vector3(p.x, 0.0, p.y)
	var a := deg_to_rad(float(spec.ang))
	var legacy := Vector2(sin(a), cos(a))
	var q := legacy * (TownHaven.outer_limit() + float(spec.dist))
	return Vector3(q.x, 0.0, q.y)

static func pressure_pos(spec: Dictionary) -> Vector2:
	# Gate packs hold the gathering. They do not walk into the guard apron.
	if spec.has("gate"):
		var p := spawn_pos(spec)
		return Vector2(p.x, p.z)
	var a := deg_to_rad(float(spec.ang))
	var dir := Vector2(sin(a), cos(a))
	return dir * (TownHaven.stand_off(HordeZombie.BODY_R) + 0.45)

func _spawn_slot(spec: Dictionary, pos: Vector3) -> HordeZombie:
	if alive_count() >= HARD_CAP: return null
	var d: EnemyDirector = main.party.director
	var z := d.spawn(str(spec.id), pos, main.hero)
	if z is HordeZombie:
		z.anchor = pressure_pos(spec)
		z.combat = main.party.combat
		spawned += 1
	return z

## The only respawn entry. Interior coordinates are pushed back outside before the node exists.
func respawn_at(tid: String, pos: Vector3) -> Enemy:
	if alive_count() >= HARD_CAP: return null
	var spec := {"id": tid, "ang": 0.0, "dist": 40.0}
	var placed := Vector2(pos.x, pos.z)
	if placed.length() > 1.0:
		spec.ang = rad_to_deg(atan2(placed.x, placed.y))
		spec.dist = maxf(8.0, placed.length() - TownHaven.outer_limit())
	var z := _spawn_slot(spec, pos)
	slots.append({"spec": spec, "node": z})
	return z

func debug_fill(n: int) -> int:
	var guard := 0
	while alive_count() < mini(n, HARD_CAP) and guard < HARD_CAP + 2:
		respawn_at("shambler", Vector3(6.0 + guard, 0.0, TownHaven.outer_limit() + 28.0))
		guard += 1
	return alive_count()

func alive_count() -> int:
	var n := 0
	var d = main.party.director if main and main.get("party") else null
	if d == null: return 0
	for e in d.enemies:
		if is_instance_valid(e) and e is HordeZombie and e.alive(): n += 1
	return n

func corpse_count() -> int:
	var n := 0
	var d = main.party.director if main and main.get("party") else null
	if d == null: return 0
	for e in d.enemies:
		if is_instance_valid(e) and e is HordeZombie and not e.alive(): n += 1
	return n

func hear(world: Vector3, radius: float) -> void:
	var p := Vector2(world.x, world.z)
	if TownHaven.inside_xz(p.x, p.y):
		p = TownHaven.nearest_outside(p, HordeZombie.BODY_R)
		radius = minf(radius, 22.0)
	if radius >= noise_r or noise_t <= 0.0:
		noise_at = p
		noise_r = radius
		noise_t = 1.8

func _on_combat(_slot: int, _sk: Dictionary) -> void:
	if main and main.hero: hear(main.hero.global_position, 40.0)

func _physics_process(dt: float) -> void:
	if main == null or main.hero == null: return
	if noise_t > 0.0:
		noise_t -= dt
		if noise_t <= 0.0: noise_r = 0.0
	var spd := Vector2(main.hero.velocity.x, main.hero.velocity.z).length()
	if spd > 4.8: hear(main.hero.global_position, 28.0)
	elif spd > 0.35: hear(main.hero.global_position, 10.0)
	_cull(dt)
	if OS.get_environment("VARN_NO_HORDE_REFILL") != "": return
	refill_t -= dt
	if refill_t > 0.0: return
	refill_t = REFILL_SEC
	_refill_one()

func _cull(dt: float) -> void:
	var corpses: Array = []
	for s in slots:
		var z = s.node
		if z != null and is_instance_valid(z) and not z.alive():
			z.dead_for += 0.0 # zombie already counts this
			corpses.append(s)
	corpses.sort_custom(func(a, b): return float(a.node.dead_for) > float(b.node.dead_for))
	while corpses.size() > CORPSE_CAP:
		_release(corpses[0])
		corpses.remove_at(0)
	for s in corpses:
		if is_instance_valid(s.node) and s.node.dead_for >= CORPSE_SEC: _release(s)

func _refill_one() -> void:
	if alive_count() >= CAP: return
	for s in slots:
		var z = s.node
		if z != null and is_instance_valid(z): continue
		var spec: Dictionary = s.spec
		if TownHaven.in_escape_wedge(_spec_xz(spec)): continue
		s.node = _spawn_slot(spec, spawn_pos(spec))
		return

func _spec_xz(spec: Dictionary) -> Vector2:
	var p := spawn_pos(spec)
	return Vector2(p.x, p.z)

func _release(s: Dictionary) -> void:
	var z = s.node
	s.node = null
	if z == null or not is_instance_valid(z): return
	var d = main.party.director if main and main.get("party") else null
	if d: d.enemies.erase(z)
	z.queue_free()
	culled += 1
