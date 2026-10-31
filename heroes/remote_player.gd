class_name RemotePlayer
extends Node3D
## Another player from Lucian's Net (port-net). Spawn on Net.peer_joined, update on peer_state,
## free on peer_left. Uses the same rigged hero models; `skin` picks the model (falls back to aldric).
## Usage:  var rp := RemotePlayer.spawn(world, player_dict)   rp.apply_state(dict)
var id := ""
var skin := ""
var rig: CharacterRig
var target_pos := Vector3.ZERO
var target_yaw := 0.0
var moving := false
var label: Label3D

static func spawn(parent: Node, p: Dictionary) -> RemotePlayer:
	var rp := RemotePlayer.new()
	rp.id = str(p.get("id", ""))
	parent.add_child(rp)
	rp.apply_state(p, true)
	return rp

static func skin_id(s: String) -> String:
	var k := s.trim_prefix("n:").get_slice("_", 0).to_lower()   # 'n:owner_pika1' -> 'owner'
	return k if HeroRoster.ORDER.has(k) else "aldric"

func apply_state(p: Dictionary, snap := false) -> void:
	var sk := skin_id(str(p.get("skin", "aldric")))
	if sk != skin:
		skin = sk
		if rig: rig.queue_free()
		rig = CharacterRig.new().setup(HeroRoster.model(sk, true), HeroRoster.height(sk)); add_child(rig)
	if label == null:
		label = Label3D.new(); label.billboard = BaseMaterial3D.BILLBOARD_ENABLED; label.font_size = 48; label.pixel_size = 0.004; add_child(label)
	label.text = str(p.get("name", p.get("hero", "")))
	label.position.y = HeroRoster.height(sk) + 0.25
	target_pos = Vector3(float(p.get("x", 0)), float(p.get("y", 0)), float(p.get("z", 0)))
	target_yaw = float(p.get("yaw", 0)); moving = p.get("moving", false) == true
	if snap: global_position = target_pos; rotation.y = target_yaw

func _process(dt: float) -> void:
	global_position = global_position.lerp(target_pos, min(1.0, 10.0 * dt))     # Net sends every 100 ms
	rotation.y = lerp_angle(rotation.y, target_yaw, min(1.0, 10.0 * dt))
	if rig: rig.set_locomotion(1.0 if moving else 0.0)

## Convenience: connect all three Net signals to a parent node.  RemotePlayer.bind(Net, world_node)
static func bind(net: Node, parent: Node) -> Dictionary:
	var peers := {}
	net.peer_joined.connect(func(p): if not peers.has(str(p.id)): peers[str(p.id)] = spawn(parent, p))
	net.peer_state.connect(func(p):
		var k := str(p.get("id", ""))
		if peers.has(k): peers[k].apply_state(p)
		else: peers[k] = spawn(parent, p))
	net.peer_left.connect(func(i):
		if peers.has(str(i)): peers[str(i)].queue_free(); peers.erase(str(i)))
	return peers
