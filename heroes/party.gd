class_name Party
extends Node
## Hero controller glue: puts the real rigged hero on main.gd's CharacterBody3D, runs roster switching,
## companions that follow the hero's breadcrumb trail (so they climb the same stairs), combat and enemies.
## Hook (main.gd): party = Party.new(); add_child(party); party.setup(self)

signal hero_changed(id: String)

const TRAIL_STEP := 0.25
const FOLLOW_GAP := [1.6, 2.8, 4.0]
var main: Node
var hero_id := "owner"
var companion_ids: Array = ["pip"]
var rig: CharacterRig
var companions: Array = []        # [{id, node, rig}]
var trail: PackedVector3Array = []
var combat: HeroCombat
var director: EnemyDirector
var hud: Node
var zone := "town"

func setup(m: Node, spawn_enemies := true) -> void:
	main = m
	# remove the placeholder Owner limbs and hide the placeholder Pip
	m.limbs.clear()
	for c in m.hero_vis.get_children(): c.queue_free()
	if m.pip: m.pip.visible = false
	combat = HeroCombat.new(); combat.name = "HeroCombat"; add_child(combat)
	combat.body = m.hero; combat.facing = m.hero_vis
	director = EnemyDirector.new(); director.name = "Enemies"; m.add_child(director)
	director.setup(m.hero, combat, Callable(m, "ground_y") if m.has_method("ground_y") else Callable(m, "height"), spawn_enemies)
	combat.enemies = director.living
	set_hero(hero_id)
	_set_companions(companion_ids)
	hud = load("res://combat/combat_hud.gd").new(); add_child(hud); hud.setup(self)

func set_hero(id: String) -> void:
	if companion_ids.has(id):        # swap places with that companion
		companion_ids[companion_ids.find(id)] = hero_id
	hero_id = id
	if rig: rig.queue_free()
	rig = CharacterRig.new().setup(HeroRoster.model(id), HeroRoster.height(id))
	main.hero_vis.add_child(rig)
	if rig.voxel and HeroRoster.ROOT_SPEED.has(id): rig.set_root_speeds(HeroRoster.ROOT_SPEED[id][0], HeroRoster.ROOT_SPEED[id][1], HeroRoster.speed(id))
	var h := HeroRoster.height(id)
	var cs: CollisionShape3D = main.hero.get_child(0)
	var cap := CapsuleShape3D.new(); cap.radius = clamp(h * 0.17, 0.12, 0.53); cap.height = max(h, cap.radius * 2.0 + 0.01)
	cs.shape = cap; cs.position.y = cap.height / 2
	main.move_speed = HeroRoster.speed(id)
	main.cam_h = clamp(h * 0.9, 0.5, 2.0)
	combat.rig = rig; combat.set_hero(id)
	if companions.size(): _set_companions(companion_ids)
	hero_changed.emit(id)

func next_hero(step := 1) -> void:
	var i := HeroRoster.ORDER.find(hero_id)
	set_hero(HeroRoster.ORDER[(i + step + HeroRoster.ORDER.size()) % HeroRoster.ORDER.size()])

func _set_companions(ids: Array) -> void:
	for c in companions: c.node.queue_free()
	companions.clear()
	companion_ids = ids.filter(func(x): return x != hero_id)
	for i in companion_ids.size():
		var n := Node3D.new(); main.add_child(n)
		var r := CharacterRig.new().setup(HeroRoster.model(companion_ids[i], true), HeroRoster.height(companion_ids[i]))
		n.add_child(r)
		var cid: String = companion_ids[i]
		if r.voxel and HeroRoster.ROOT_SPEED.has(cid): r.set_root_speeds(HeroRoster.ROOT_SPEED[cid][0], HeroRoster.ROOT_SPEED[cid][1], HeroRoster.speed(cid) * 1.15)
		n.global_position = main.hero.global_position + Vector3(1.0 + i, 0, 1.0)
		companions.append({"id": companion_ids[i], "node": n, "rig": r, "swing": 0.0})

var _fly_last_yaw := 0.0
var riding := false   # test 33: true while sailing (set by TidewrackSea)
func _physics_process(dt: float) -> void:
	if main == null or main.hero == null: return
	var hp: Vector3 = main.hero.global_position
	var v: Vector3 = main.hero.velocity; v.y = 0
	var fly: bool = main.has_method("flying_now") and main.flying_now()
	var swim: bool = main.has_method("in_sea") and main.in_sea(hp)
	if swim:   # test 26: tread water / swim stroke (hover + forward flight clips) chest-deep at the sea surface
		var sl: Vector3 = rig.global_basis.inverse() * main.hero.velocity; sl.y = 0.0
		rig.set_flight(true, sl, 0.0, maxf(main.move_speed, 1.0))
	rig.swim_on = swim
	rig.position.y = lerpf(rig.position.y, -1.15 * rig.target_height / 1.905 if swim else 0.0, minf(1.0, dt * 6.0))
	if (fly or rig.fly_on) and not swim:   # test 16: flying state instead of walk/run on air
		var vv: Vector3 = main.hero.velocity
		var vl: Vector3 = rig.global_basis.inverse() * vv
		var yr: float = rig.global_rotation.y; var turn := wrapf(yr - _fly_last_yaw, -PI, PI) / maxf(dt, 0.001); _fly_last_yaw = yr
		rig.set_flight(fly, vl, turn, maxf(main.move_speed * 2.0, 8.0))
	rig.set_locomotion(v.length() / max(main.move_speed, 0.1) * 2.0)
	# breadcrumb trail (stairs/ramps included because points carry the hero's real y)
	if trail.is_empty() or trail[trail.size() - 1].distance_to(hp) > 8.0: trail = PackedVector3Array([hp])
	elif trail[trail.size() - 1].distance_to(hp) >= TRAIL_STEP:
		trail.append(hp)
		if trail.size() > 80: trail = trail.slice(trail.size() - 80)
	if riding: return   # test 33: at sea, companions sit on the deck (TidewrackSea.seat_crew), no follow / swim AI
	for i in companions.size():
		_follow(companions[i], FOLLOW_GAP[min(i, FOLLOW_GAP.size() - 1)], dt)

## Walk `gap` metres back along the trail and move the companion there.
func trail_point(gap: float) -> Vector3:
	var acc := 0.0
	var p: Vector3 = main.hero.global_position
	for j in range(trail.size() - 1, -1, -1):
		var seg := p.distance_to(trail[j])
		if acc + seg >= gap: return p.lerp(trail[j], (gap - acc) / max(seg, 0.0001))
		acc += seg; p = trail[j]
	return p

## Test 7: companions walk BESIDE/behind the hero at ground level (never on the camera line behind him);
## flyers (phoenix) hover at shoulder height off to the side. Side alternates per companion slot.
const FLYERS := ["phoenix"]
const SIDE_M := 1.1
func follow_goal(c: Dictionary, gap: float) -> Vector3:
	var idx := companions.find(c)
	var goal := trail_point(gap)
	var fwd: Vector3 = -main.hero_vis.global_transform.basis.z; fwd.y = 0
	if fwd.length() < 0.01: fwd = Vector3(0, 0, -1)
	var side := fwd.normalized().cross(Vector3.UP) * (SIDE_M if idx % 2 == 0 else -SIDE_M)
	goal += side
	# stay out of the camera's line of sight: push sideways if the goal is near the camera->hero segment
	if main.cam:
		var a: Vector3 = main.cam.global_position; var b: Vector3 = main.hero.global_position + Vector3(0, 0.8, 0)
		var ab := b - a; var t := clampf((goal - a).dot(ab) / maxf(ab.length_squared(), 0.001), 0.0, 1.0)
		var near_pt := a + ab * t
		var off := Vector3(goal.x - near_pt.x, 0, goal.z - near_pt.z)
		if off.length() < 0.9: goal += (off.normalized() if off.length() > 0.01 else side.normalized()) * (0.9 - off.length())
	if FLYERS.has(c.id): goal.y += HeroRoster.height("owner") * 0.75   # shoulder height
	return goal

func _follow(c: Dictionary, gap: float, dt: float) -> void:
	var n: Node3D = c.node
	var goal := follow_goal(c, gap)
	var to := goal - n.global_position
	var flat := Vector2(to.x, to.z).length()
	var spd: float = HeroRoster.speed(c.id) * 1.15
	if to.length() > 12.0: n.global_position = goal; flat = 0.0      # lost: snap
	elif flat > 0.15:
		n.global_position += to.normalized() * min(to.length(), spd * dt * clamp(flat, 0.3, 1.5))
		n.rotation.y = lerp_angle(n.rotation.y, atan2(-to.x, -to.z), 10 * dt)
	n.global_position.y = lerp(n.global_position.y, goal.y, min(1.0, 12.0 * dt))
	var cr := c.rig as CharacterRig
	if cr.root_walk > 0.0: cr.set_move_mps(_comp_speed(c, n, dt))
	else: cr.set_locomotion(clamp(flat * 1.2, 0.0, 2.0))
	_companion_fight(c, dt)

## CompanionCombat (companions.js): modest damage 95-150, 1.1-1.5 s cadence, only near the hero.
func _companion_fight(c: Dictionary, dt: float) -> void:
	c.swing = max(0.0, c.swing - dt)
	if c.swing > 0.0: return
	var ranged := RegexHelper.ranged(c.id)
	var reach := (10.0 if ranged else 2.6) * CombatRules.UNIT_M
	for e in director.living():
		if e.global_position.distance_to(main.hero.global_position) > 12.0 * CombatRules.UNIT_M + e.radius: continue
		var d: float = e.global_position.distance_to(c.node.global_position) - e.radius
		if d <= reach:
			c.rig.play_attack("", 1.4)
			var v: Vector3 = e.global_position - c.node.global_position
			c.node.rotation.y = atan2(-v.x, -v.z)
			e.take_damage(randi_range(95, 150) / 10, c.node.global_position)   # companions are modest: ~1/10 of JS (enemy HP is retuned too)
			c.swing = randf_range(1.1, 1.5)
			return

## Net.state_provider hook: Net expects {zone,x,y,z,yaw,hero,skin,moving}; position/heading also given.
func net_state() -> Dictionary:
	var p: Vector3 = main.hero.global_position
	var yaw: float = main.hero_vis.rotation.y
	var v: Vector3 = main.hero.velocity; v.y = 0
	return {"zone": zone, "position": p, "heading": yaw, "x": p.x, "y": p.y, "z": p.z, "yaw": yaw,
		"hero": HeroRoster.display_name(hero_id), "skin": hero_id, "moving": v.length() > 0.2}

func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo:
		match e.keycode:
			KEY_J, KEY_SPACE: combat.use(0)
			KEY_1: combat.use(1)
			KEY_2: combat.use(2)
			KEY_3: combat.use(3)
			KEY_4: combat.use(4)
			KEY_5: combat.use(5)
			KEY_TAB: next_hero(-1 if e.shift_pressed else 1)

## voxel companions: measured horizontal speed (m/s), smoothed
func _comp_speed(c: Dictionary, n: Node3D, dt: float) -> float:
	var p := n.global_position
	var lp: Vector3 = c.get("lp", p); c.lp = p
	var v := Vector2(p.x - lp.x, p.z - lp.z).length() / maxf(dt, 0.001)
	c.sv = lerpf(float(c.get("sv", 0.0)), v, minf(1.0, dt * 8.0))
	return c.sv
