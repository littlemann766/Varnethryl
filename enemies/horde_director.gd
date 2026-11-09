class_name HordeDirector
extends Node
## One bounded crowd outside the walled town. Not a replacement for wolves, trolls, or the titan.
## Alive count and corpses are capped. Nothing here is written into the save.

## Boot population. The scalable ceiling and the near-combat pool live on HordeCrowd.
const CAP := 1000
const HARD_CAP := 4096
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
var crowd: HordeCrowd
var noise_at := Vector2.ZERO
var noise_r := 0.0
var noise_t := 0.0
var refill_t := REFILL_SEC
var spawned := 0
var culled := 0

func setup(m: Node) -> void:
	main = m
	name = "Horde"
	crowd = HordeCrowd.new()
	crowd.name = "HordeCrowd"
	add_child(crowd)
	var n := HordeCrowd.SIM_DEFAULT
	var raw := OS.get_environment("VARN_HORDE_SIM")
	if raw.is_valid_int(): n = clampi(int(raw), 1, HordeCrowd.SIM_MAX)
	crowd.setup(self, n)
	spawned = crowd.alive_n
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

## Interior coordinates are pushed outside before a record exists.
func respawn_at(tid: String, pos: Vector3) -> Enemy:
	var placed := Vector2(pos.x, pos.z)
	if TownHaven.body_inside(placed, HordeZombie.BODY_R) or TownHaven.far_parking(placed):
		placed = TownHaven.nearest_outside(placed, HordeZombie.BODY_R)
	if crowd == null:
		return _spawn_loose(tid, Vector3(placed.x, pos.y, placed.y))
	if crowd.alive_n >= HordeCrowd.SIM_MAX: return null
	crowd._spawn_new(0, -1)
	return crowd.deploy_actor("shambler" if tid == "" else tid)

func _spawn_loose(tid: String, pos: Vector3) -> HordeZombie:
	var d: EnemyDirector = main.party.director
	var z := d.spawn(tid, pos, main.hero)
	if z is HordeZombie:
		z.anchor = Vector2(z.global_position.x, z.global_position.z)
		spawned += 1
	return z

func debug_fill(n: int) -> int:
	if crowd == null: return alive_count()
	return crowd.ensure_count(mini(n, HordeCrowd.SIM_MAX))

func alive_count() -> int:
	if crowd: return crowd.alive_n
	return 0

func near_count() -> int:
	if crowd: return crowd.near_n
	return 0

func rendered_count() -> int:
	if crowd: return crowd.rendered_n
	return 0

func corpse_count() -> int:
	if crowd: return crowd.corpse_n
	return 0

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
	if crowd: crowd.step(dt)
