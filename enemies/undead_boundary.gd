class_name UndeadBoundary
extends Node
## Runs after undead movement. Any undead that scripting, a shove, or a hitch left inside the
## town is put back on its last safe outside point before the next frame can hurt the hero.
## This does not move the hero and does not depend on guards.

var main: Node

func setup(m: Node) -> void:
	main = m
	name = "UndeadBoundary"
	process_physics_priority = 100

func sweep() -> int:
	var d = main.party.director if main and main.get("party") and main.party else null
	if d == null: return 0
	var kept: Array = []
	var expelled := 0
	for e in d.enemies:
		if not is_instance_valid(e): continue
		kept.append(e)
		if not TownHaven.is_undead_enemy(e): continue
		if e is HordeZombie: e.cancel_if_hero_safe()
		var r := float(e.radius) if e.get("radius") != null else HordeZombie.BODY_R
		var flat := Vector2(e.global_position.x, e.global_position.z)
		if not TownHaven.body_inside(flat, r) and not TownHaven.far_parking(flat): continue
		var back := Vector3.ZERO
		if e is HordeZombie:
			back = e.last_safe
		var back_flat := Vector2(back.x, back.z)
		if TownHaven.body_inside(back_flat, r) or TownHaven.far_parking(back_flat) or back == Vector3.ZERO:
			back = TownHaven.sanitize_spawn(e.global_position, r)
			if e is HordeZombie and (e as HordeZombie).height_fn.is_valid():
				back.y = float((e as HordeZombie).height_fn.call(back.x, back.z))
		e.global_position = back
		if e is HordeZombie:
			e.last_safe = e.global_position
			e.cancel_strike()
		expelled += 1
		TownHaven.note({"e": "expel", "id": str(e.type_id), "x": snappedf(back.x, 0.01), "z": snappedf(back.z, 0.01)})
	d.enemies = kept
	return expelled

func _physics_process(_dt: float) -> void:
	sweep()
