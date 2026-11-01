extends AnimatableBody3D
## Beth stage 10: Saltglass dock lift, 20.4 -> 108.68 m (88.3 m) at 6 m/s (~15 s). Platform = sg_lift_platform.glb, origin = deck top centre.
## Collision (children): deck box 3.6x0.3x3.6 at y -0.15, rails 3.6x1.1x0.12 at z -1.74, 0.12x1.1x3.6 at x +-1.74 (door side +z open).
## sync_to_physics = true so the hero (CharacterBody3D) rides it.
## TOLL (stage 10, replaces the stage-9 unlock flag): a keeper in a booth at each stop. A ride costs `ride_price` coins, or is free
## with the season pass item `pass_item` (bought at either booth window for `pass_price`). Calling the lift to your stop is free.
## Coins/items go through the Wallet API (props/wallet_stub.gd; Lucky backs it with the real wallet). The shortcut gate is separate and free.
@export var bottom := Vector3(-2104.0, 20.4, -82.0)
@export var top := Vector3(-2104.0, 108.68, -82.0)
@export var speed := 6.0
@export var ride_price := 5
@export var pass_price := 150
@export var pass_item := "saltglass_lift_pass"
@export var window_bottom := Vector3(-2109.5, 20.4, -77.2)
@export var window_top := Vector3(-2109.5, 108.68, -77.2)
@export var reach := 2.4
@export var keeper_paths: Array[NodePath] = []   # the two SaltglassLiftKeeper nodes (they crank while the lift moves)
signal toast(text: String)   # Lucky: connect to ui.toast
var moving := false
func _ready() -> void:
	sync_to_physics = true; global_position = bottom
func at_top() -> bool: return global_position.distance_to(top) < 0.1
func on_platform(p: Vector3) -> bool: return Vector2(p.x - global_position.x, p.z - global_position.z).length() < 1.7 and absf(p.y - global_position.y) < 1.5
func prompt_for(hero_pos: Vector3) -> Array:
	if moving: return ["", Callable()]
	var dest := bottom if at_top() else top; var verb := "Ride down" if at_top() else "Ride up"
	if on_platform(hero_pos):
		if Wallet.has_item(pass_item): return ["%s (season pass)" % verb, func(): go(dest)]
		return ["%s - %d coins" % [verb, ride_price], func(): pay_and_go(dest)]
	var at_win := hero_pos.distance_to(window_bottom) < reach or hero_pos.distance_to(window_top) < reach
	if at_win and not Wallet.has_item(pass_item): return ["Buy season pass - %d coins" % pass_price, buy_pass]
	var near_bottom := hero_pos.distance_to(window_bottom) < 6.0 and absf(hero_pos.y - bottom.y) < 2.0
	var near_top := hero_pos.distance_to(window_top) < 6.0 and absf(hero_pos.y - top.y) < 2.0
	if near_bottom and at_top(): return ["Call lift", func(): go(bottom)]
	if near_top and not at_top(): return ["Call lift", func(): go(top)]
	return ["", Callable()]
func pay_and_go(dest: Vector3) -> void:
	if Wallet.pay(ride_price, "saltglass_lift_ride"): go(dest)
	else: toast.emit("Not enough coins - a ride costs %d (you have %d)." % [ride_price, Wallet.coins()])
func buy_pass() -> void:
	if Wallet.has_item(pass_item): return
	if Wallet.buy(pass_item): toast.emit("Season pass bought - ride the Saltglass lift free.")
	else: toast.emit("Not enough coins - the season pass costs %d (you have %d)." % [pass_price, Wallet.coins()])
func _keepers(on: bool) -> void:
	for p in keeper_paths:
		var k := get_node_or_null(p)
		if k and k.has_method("set_cranking"): k.set_cranking(on)
func go(to: Vector3) -> void:
	if moving: return
	moving = true; _keepers(true)
	var tw := create_tween(); tw.set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
	tw.tween_property(self, "global_position", to, global_position.distance_to(to) / speed).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.finished.connect(func(): moving = false; _keepers(false))
