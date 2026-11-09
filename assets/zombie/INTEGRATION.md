# Zombie model integration

Art only. `enemies/horde_zombie.gd` is unchanged. `MODEL_HOOK` is still empty, so test 59 still draws the capsule until someone points a hook at these scenes.

## What test 59 does today

`HordeZombie._build_visual` loads `MODEL_HOOK[role]` when that path exists. Every role is `""`, so the body is a capsule, a sphere, and a "PLACEHOLDER" label. The far crowd in `HordeCrowd._build_meshes` is one `MultiMesh` of capsules per role. Nothing on the horde plays an animation. Collision stays on `HordeZombie.BODY_R` (0.46 m). These meshes do not change it.

## Files

| Role | Scene | Tris (body + cloth) |
| --- | --- | --- |
| Female villager | `res://assets/zombie/zombie_female_villager.glb` | 9228 + 1584 = 10812 |
| Male villager | `res://assets/zombie/zombie_male_villager.glb` | 9504 + 788 = 10292 |
| Sailor | `res://assets/zombie/zombie_male_sailor.glb` | 9136 + 216 = 9352 |
| Knight | `res://assets/zombie/zombie_male_knight.glb` | 9724 + 788 = 10512 |
| Far LOD | `res://assets/zombie/zombie_far_lod.glb` | 212, no skin |
| Far card | `res://assets/zombie/zombie_far_impostor.glb` | 4, no skin |

Shared textures, next to the GLBs:

- `textures/zombie_albedo.png` — 2048² RGBA. Cloth hems and hair use alpha.
- `textures/zombie_normal.png` — 2048²
- `textures/zombie_orm.png` — 2048², R occlusion, G roughness, B metal
- `textures/zombie_far_albedo.png` — 256², the LOD only
- `textures/zombie_impostor.png` — 512×256 RGBA, cut from the Godot idle stills

Suggested hook paths, when the integration agent edits `MODEL_HOOK`:

- `shambler` → female or male villager
- `runner` → male villager (same mesh; play `run`)
- `undead_sailor` → male sailor
- `undead_knight` → male knight

## Skeleton

21 joints, in this order: `root`, `hips`, `spine`, `chest`, `cape`, `neck`, `head`, `shoulder_L`, `upperArm_L`, `foreArm_L`, `hand_L`, `shoulder_R`, `upperArm_R`, `foreArm_R`, `hand_R`, `thigh_L`, `shin_L`, `foot_L`, `thigh_R`, `shin_R`, `foot_R`.

Same names and the same rest translations as `characters/kael_lod1.glb`. No finger bones, no jaw, no toe bone. The `cape` joint is present so clip tracks have a target. Nothing is weighted to it. Each cloth polygon is weighted to one joint (`chest`, `hips`, or `head`) so a hem does not stretch between the hip and the thigh. Hair is weighted to `head`.

The glTF faces +Z, like the other character GLBs. `CharacterRig` turns hero models by 180° yaw. `HordeZombie._build_visual` does not. A drop-in under the horde needs that same yaw or the face points backward.

## Clips

Embedded on every combat GLB. Godot import on this machine listed:

`attack`, `attack1`, `attack2`, `attack3`, `death`, `hit`, `idle`, `run`, `walk`

Lengths and a useful frame (seconds):

| Clip | Length | Frame used in the stills |
| --- | --- | --- |
| idle | 2.50 | 1.25 |
| walk | 1.33 | 0.62 |
| run | 0.92 | 0.43 |
| attack1 | 1.00 | 0.45 |
| attack2 | 1.04 | 0.47 |
| attack3 | 1.67 | 0.75 |
| hit | 0.38 | 0.17 |
| death | 1.58 | 1.58 |

`attack` is `attack1`. There is no bite and no bite windup. The gameplay windup (0.28–0.50 s) is a timer on `HordeZombie`, not a clip. `attack2` is the closest swing: the hand stays about 0.44 m from the head.

Godot measured these joint lengths on the imported skeleton at every clip above. They do not change, except the thigh, which moves by 1 mm on the attack, hit, and death clips:

- shoulder to upper arm 0.144 m
- upper arm 0.203 m
- forearm 0.194 m
- thigh 0.417 m
- shin 0.397 m
- chest to neck 0.307 m
- neck 0.091 m

Bind-pose skinning error on the female mesh is 0 (the skinned vertices match the authored vertices).

## Budgets

Mobile renderer, up to 16 full bodies. One shared material pair (opaque body, alpha-scissor cloth), so a full horde is up to 32 surfaces if Godot does not batch the skinned draws.

- 16 × ~10.5k triangles ≈ 170k skinned triangles
- Textures are shared. At ASTC 6×6, three 2048² maps are about 5.6 MB of VRAM. At ASTC 4×4, about 12 MB. The PNG sources are smaller on disk (albedo 507 KB, normal 572 KB, ORM 108 KB) because they compress well; VRAM is the figure that matters.
- Far LOD: 212 triangles, one 256² albedo, no bones. One `MultiMesh` draw per role. This is the crowd mesh.
- Impostor: 4 triangles, one 512×256 card, alpha scissor, crossed quads, no bones. It is a still of the idle pose, not an animated billboard.

This was not measured on a phone. The stills were Godot 4.7 Forward Mobile on llvmpipe.

## Swap, when you want it

Do not do this in the art branch. For the combat body, set `MODEL_HOOK` to the scene path and turn the instance 180° on Y if the hook still does not. Hide the placeholder label with the mesh. For the far crowd, replace the `CapsuleMesh` in `HordeCrowd._build_meshes` with `zombie_far_lod.glb`. The impostor is optional and further out.

`assets/zombie/preview_render.gd` is a stills script. It is not the game. Run it with the lavapipe ICD and `xvfb-run` if you need to repeat the shots. It hides the title layer so the 3D view is visible.
