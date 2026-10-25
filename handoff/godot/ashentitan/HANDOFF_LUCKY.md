# Ashen Titan: intro + new attacks (for Lucky, Godot port)

Files (drop-in replacements for godot-proto/characters/, same mesh/materials/skeleton, clips added/replaced):
- `ashentitan_volcano_lod1.glb` (20.8 m volcano boss): new `intro`, `eruption_slam`, `magma_sweep`, `attack1-3`; original idle/walk/run/windup/boulder_hurl/volcano_roar/hit/death/skill untouched.
- `ashentitan_lod1.glb` (11.3 m): new `intro`, `attack1-3`.
- Web copy is already in `www/proto3d/models-new/ashentitan_cl_arms.glb` (`intro`, `attack`, `attack2`, `attack3`).
- lod2 was not in the source set: apply the same clips with `tools/rig_fix/bigattack/splice.py` if you need it.

## intro (10.0 s, 30 fps, plays once)
0-1.3 arms burst out of the lava · 2.05 both hands slam onto the rim · 2.3-4.0 two heavy hauls · 4.0-5.1 right foot onto the floor · 5.1-6.8 stands · 6.8-9.0 roar (jaw open) · 9.0-10.0 settles into idle stance.
Root motion is on the `root` bone (glTF axes, model faces +Z; volcano model):
- start: root (0, -22.46, -6.24) m = fully under the lava, 6.24 m outboard of the rim
- end: root (0, 0, +1.66) m = standing on the floor 1.66 m inside the rim; end rotation = identity.
(11 m titan: start (0,-12.25,-3.40), end (0,0,+0.91).)

### Hook-in
1. Pick the rim point R where he emerges: the arena edge at 33.5 m from the arena centre (lava ring 33.5-40 m), on the line from centre toward the spawn side.
2. Place the Titan node at R on the floor (y = 39), facing the arena centre, and play `intro` once with root motion OFF in the AnimationTree (just let the skeleton's `root` bone carry it; the mesh visibly rises from under the floor/lava). Hide nothing; his body is below the floor at t=0.
3. At t=10.0 his feet are at R + 1.66 m toward the centre. Then either
   - (suggested) bake that offset into the node position (node.position += forward*1.66, reset root) and **walk him in** with the normal `walk` (groundSpeedMps 5.47) to the spawn (0,39,-4), then start the AI; or
   - teleport to spawn after a fade.
4. Camera shake suggestions: hand slam at 2.05 s, foot plant ~4.7 s, roar 7.8-8.8 s.

## eruption_slam (2.967 s): aligned with the sidecar event
- `fist_impact` aoe t = 1.288 s: both fists are on the floor at exactly that frame (fist mesh bottom -0.5 m, i.e. sunk into the ground) and stay buried until 1.9 s.
- Fist centre is at glTF (+/-1.39, 0, **5.39**) m. The sidecar `center` is (0,0,5.89): 0.5 m further out, inside the 9 m radius. Optionally set `center` to [0,0,5.4] in ashentitan_volcano__ashentitan_volcano_11x.json.
- The eruption_ring/eruption_lava spawns at 1.338 s line up with the impact.
## magma_sweep (2.700 s): wind back 0-0.85 s, release at 0.976 s: hand_R is at glTF (-5.8, 13.1, 12.2) m (sidecar spawn offset (-4.77, 13.3, 12.58)).
## attack1 (1.9 s): right-fist hammer, contact 0.95 s at (−1.0, 0, 5.0) m. attack2 (1.93 s): left backhand sweep, waist-high. attack3 (2.2 s): left-foot stomp + double-fist slam, contact 1.05 s at (±2.3, 0, 4.8) m.
Note: character_rig.gd `play_attack("eruption_slam")` falls back to attack/attack2 unless the clip exists; it now exists in the volcano GLB.

All clips: per-frame check passed (no forearm/hand inside the torso hull on any frame).
