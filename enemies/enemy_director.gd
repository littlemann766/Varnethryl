class_name EnemyDirector
extends Node3D
## Spawns the enemy sets and routes their attacks into HeroCombat. Spawn points are test spots
## outside the town walls (zones/frost and the volcano come from the world owner later).
const SPAWNS := [
	["frosttroll_a", Vector3(40, 0, 235)],
	["frosttroll_b", Vector3(52, 0, 248)],
	["titan", Vector3(-70, 0, 262)],
	["stonetroll", Vector3(20, 0, 225)],   # test 7: Beth's stone troll at the approved 3x Owner (5.715 m)
	# test 6: Beth's rigged wolf, a pack outside the west gate
	["holyknight_villain", Vector3(232, 0, -18)],   # voxel-heroes: outside the east gate
	["wolf", Vector3(-232, 0, 18)], ["wolf", Vector3(-238, 0, 26)], ["wolf", Vector3(-229, 0, 31)],
]
var enemies: Array = []
var combat: HeroCombat
var ground: Callable

func setup(hero: Node3D, hc: HeroCombat, ground_fn: Callable, spawn_defaults := true) -> EnemyDirector:
	combat = hc; ground = ground_fn
	if spawn_defaults:
		for s in SPAWNS: spawn(s[0], s[1], hero)
		var vt := VolcanoTitan.new()
		add_child(vt); vt.setup_volcano(ground_fn); _wire(vt, hero)
		vt.aoe.connect(func(c, r, m): _aoe(vt, c, r, m))
	return self

func spawn(tid: String, pos: Vector3, hero: Node3D) -> Enemy:
	var e := Enemy.new()
	add_child(e)
	# never spawn on top of the player: keep (radius + 5 m) clear of the hero
	var r: float = float(Enemy.TYPES[tid].r) if Enemy.TYPES.has(tid) else 2.0
	var d := Vector2(pos.x - hero.global_position.x, pos.z - hero.global_position.z)
	if d.length() < r + 5.0:
		var dir2 := d.normalized() if d.length() > 0.01 else Vector2(0, -1)
		var np := Vector2(hero.global_position.x, hero.global_position.z) + dir2 * (r + 5.0)
		pos.x = np.x; pos.z = np.y
	if ground.is_valid(): pos.y = ground.call(pos.x, pos.z)
	e.setup(tid, pos, ground)
	_wire(e, hero)
	return e

func _wire(e: Enemy, hero: Node3D) -> void:
	e.target = hero
	enemies.append(e)
	e.attacked.connect(func(en, p): _on_attack(en, p))

func _on_attack(e: Enemy, p: Dictionary) -> void:
	if e is VolcanoTitan: return       # its damage comes from clip events (aoe)
	if combat and e.pattern_hits(p if not p.is_empty() else {"shape": "cone", "cos": 0.3}, combat.body.global_position):
		if _is_titan(e): combat.titan_hit(HeroCombat.TITAN_HIT * clampf(float(p.get("dmg", 1.0)), 0.5, 1.0))   # test 26
		else: combat.take_hit(float(e.def.atk), float(p.get("dmg", 1.0)))

func _aoe(e: Enemy, c: Vector3, r: float, mult: float) -> void:
	if combat and Vector2(c.x - combat.body.global_position.x, c.z - combat.body.global_position.z).length() <= r:
		if _is_titan(e): combat.titan_hit(HeroCombat.TITAN_HIT * clampf(mult, 0.5, 1.0))   # test 26
		else: combat.take_hit(float(e.def.atk), mult)

## a dormant volcano Titan (hidden in the lava until the quest intro) is not a living foe for cheats/AI
func living() -> Array: return enemies.filter(func(e): return is_instance_valid(e) and e.alive() and not (e is VolcanoTitan and not e.visible))

## test 26: Ashen Titan variants (6x roaming Titan, volcano Titan) hit for a capped share of HP, never a one-shot
static func _is_titan(e: Enemy) -> bool: return e is VolcanoTitan or e.type_id in ["titan", "titan_volcano"]
