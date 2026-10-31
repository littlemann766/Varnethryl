extends SceneTree
## Test 14 (boss: "keep every door that currently works WORKING"): every door that entered its interior before the
## test 14 moves (farmstead out of town, observatory to the NE corner, filler rows) must still do so. Walks the hero
## into each door through the real InteriorManager trigger, checks the interior, then exits.
## Baseline = the enterable doors in test 13 (b6dd896): every landmark with an interior + the barn doors.
const BASELINE := ["apothecary", "bakery", "barn", "colosseum", "crypt", "farmhouse", "guildhall", "house1", "house2", "house3",
	"house4", "inn", "keep", "library", "mage", "market", "observatory", "smithy", "stables", "temple", "thieves", "townhall",
	"training", "treasury", "windmill"]
func _initialize() -> void: _run.call_deferred()
var fails := 0
func ok(c: bool, m: String) -> void:
	print(("PASS " if c else "FAIL ") + m)
	if not c: fails += 1

func _run() -> void:
	var m = load("res://main.tscn").instantiate(); root.add_child(m)
	for i in 40: await process_frame
	var im = m.interiors
	var doors := {}
	for b in m.buildings + m.extra_doors: if im.has_interior(b.id): doors[b.id] = b
	for id in BASELINE: ok(doors.has(id), "%s door still registered with an interior" % id)
	for id in BASELINE:
		if not doors.has(id): continue
		var b: Dictionary = doors[id]
		var dw: Vector3 = im.door_world(b); var into: Vector3 = b.node.global_transform.basis * Vector3(0, 0, -1)
		var start := dw - into * 3.0; start.y = m.ground_y(start.x, start.z) + 0.3
		m.hero.global_position = start; m.hero.velocity = Vector3.ZERO
		await physics_frame
		var entered := false
		m.yaw = atan2(-into.x, -into.z); m.joy_vec = Vector2(0, -1)
		for f in 150:
			await physics_frame
			if im.active(): entered = true; break
		m.joy_vec = Vector2.ZERO
		ok(entered, "%s door enters its interior" % id)
		if entered:
			im.exit(); im.cooldown = 0.0
			for f in 5: await physics_frame
	print("DOORS %d failed" % fails); quit(1 if fails else 0)
