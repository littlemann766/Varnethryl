# port-heroes

Heroes, combat and enemies for the Godot port. Code lives in `res://heroes/`, `res://combat/` and `res://enemies/`.

## Hook points in `scripts/main.gd` (6 lines)
- `var party`, `var move_speed := 6.0`, `var cam_h := 1.7` (Party sets speed and camera height for each hero)
- `_ready()`: `party = load("res://heroes/party.gd").new(); add_child(party); party.setup(self, not bench)`
- `_physics_process`: `6.0` replaced with `move_speed`. `_process`: camera pivot height uses `cam_h`.
- Party clears `main.limbs`, removes the placeholder Owner meshes under `hero_vis` and hides the placeholder `pip`.

## Net (port-net)
- `Net.state_provider = party.net_state` returns `{zone, position, heading, hero, skin, moving}` plus `x,y,z,yaw`.
- `RemotePlayer.bind(Net, world_node)` connects peer_joined / peer_state / peer_left. You can also call `RemotePlayer.spawn(parent, dict)` and `apply_state(dict)` yourself.
- Positions are Godot metres. The JS server/clients send world units (metres x 1.4205), so a conversion is needed if they share a room with the JS client.

## Tests
`godot --headless -s res://tests/run_tests.gd` checks heights (skinned rest pose, every hero and enemy), the AnimationTree, and the combat rules. Exit code 0 means pass.
Screenshots: `VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json xvfb-run -a godot -s res://tests/shots.gd` writes them to `tests/shots/`.

## Controls
On screen: ATK, 3 skills, ult, and "Hero ▶" to switch heroes. Keys: J/Space attack, 1-4 skills, Tab next hero (Shift+Tab previous).
