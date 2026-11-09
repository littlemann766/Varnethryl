# Hooded candidate — integration contract

For one hooded mesh. The other two characters are not covered. `enemies/horde_zombie.gd` is unchanged. `MODEL_HOOK` is still empty. Nothing here is wired into the horde.

Files live in `assets/hooded_candidate/`. The isolated driver is `validation/hooded_male/hooded_presenter.gd`. The check that runs it is `validation/hooded_male/hooded_validate.gd`.

## Do not do these

- Do not play `voxel/kael_voxel.glb` clips on this skeleton. The rest pose, the twists, and the parents are not kael's. The clips inside the glb are already the retarget.
- Do not parent the thighs to `hips` or the shoulders to `chest`. In this file they are siblings of `hips`, under the armature root. `cloak_back` is the only new bone, and it is a child of `chest`.
- Do not send this through `CharacterRig` as it stands. That rig looks for a clip named `attack` before it will play a bite. This file has `attack2` only, so the bite would fall through to the procedural lunge. Its attack one-shot fades in over 0.05 s and it sets attack speed to 1.6. Both fight this clip. The 0.05 s fade is short enough to show the arms-out first frame.

## What HordeZombie actually does

Read from `enemies/horde_zombie.gd` on this branch. There is no AnimationPlayer call.

| Controller | Clip to use | Notes |
|---|---|---|
| `state == "approach"`, not moving | `idle` | Loop. Speed 1. |
| `approach`, shambler moving | `walk` | Authored foot speed about 0.91 m/s. Shambler `speed_mps` is 1.25. Play at `1.25 / 0.91` (about 1.37) or the feet slide. |
| `approach`, `runner == true` and moving | `run` | Authored about 2.0 m/s. Runner `speed_mps` is 3.35. Play at `3.35 / 2.0` (1.675). The harness measured that scale on a runner instance. |
| `windup` or `recover` | `attack2` | This is the bite, for `bite`, `grab`, and `lunge`. There is no second attack and no grab clip. |
| hp fell, still alive | `hit` | The controller never enters a hit state. `take_damage` only subtracts hp. The presenter infers the flinch from the hp drop. That inference is not in production code. |
| `state == "defeated"` | `death` | Play once. Hold the last frame. The controller only sets the state and changes the placeholder label. |

`attack2` is 1.04 s and starts arms-out. Shambler windup is 0.45 s and recover is 0.65 s (1.10 s together). Runner windup is 0.28 s. Damage is applied at the end of windup, inside `HordeZombie._resolve`, not at a frame of the clip. Playing `attack2` at 1× from the start of windup finishes near the end of a shambler's recover. The hit on the hero is still the old timer. It is not locked to the visual reach. Changing that would be a gameplay edit. It was not done.

Blend 0.30 s from the current loop into `attack2`, `hit`, and `death`. The harness frames are `xfade_walk_to_attack2_05.png` (still the walk) and `xfade_walk_to_attack2_30.png` (one arm out, the other not yet). `mobile_attack2_arms_out.png` is the unblended first frame, kept so the arms-out pose is visible.

Facing: `HordeZombie._face_toward` uses `atan2(-to.x, -to.y)`, so yaw 0 looks down −Z. The presenter applies `rotation.y = PI` on the glTF node, the same turn `CharacterRig` uses. Root motion is already zero. Do not add it.

The crowd of far bodies in `HordeCrowd` is a capsule MultiMesh, not this mesh. A far crowd of this character is a MultiMesh of `hooded_male_far.glb` in bind pose. It is not 72 skeletons. The card is a 2-triangle quad. It must be yawed toward the camera or it vanishes edge-on. Switching from the mobile body to the far mesh is a hard pop: the far mesh is darker, thinner, and the head is a block. There is no blend.

## How to turn it on later

Point `MODEL_HOOK["shambler"]` at a PackedScene whose root is `HoodedPresenter`, not at the raw glb. The raw glb would show the rest pose, facing +Z, and nothing would play, because `HordeZombie._build_visual` only instances the scene.

`HoodedPresenter._process` reads the parent when the parent is a `HordeZombie`. The harness built a shambler and a runner, turned physics off, and checked the clip:

- ready → idle
- after a step → walk
- windup and recover → attack2
- hp drop → hit
- defeated → death
- runner step → run at speed scale 1.675

That check does not spawn a fight and does not change the horde.

Mobile is the body to instance for the near ring (47,583 tris). Full (96,615) is the reference, not the crowd mesh. Far is 783 tris. The card is the impostor.

## Still open

- No phone, no real GPU. The llvmpipe timings are in `VALIDATION.md`. They are not a budget.
- Damage timing versus the reach.
- Card billboard and a fade into the far mesh.
- Soldier and female. Not started from this package.
