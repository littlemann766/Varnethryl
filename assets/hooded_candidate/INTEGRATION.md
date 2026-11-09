# Hooded candidate — integration contract

For one hooded mesh. The other two characters are not covered. `enemies/horde_zombie.gd` is unchanged. `MODEL_HOOK` is still empty. Nothing here is wired into the horde.

Files live in `assets/hooded_candidate/`. The isolated driver is `validation/hooded_male/hooded_presenter.gd`. Import check: `hooded_validate.gd`. Lit presentation: `hooded_delivery.gd`. Safety pass: `hooded_safety.gd`.

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

`attack2` is 1.04 s. It starts arms-out. The reaching hand then swings back (about −0.49 m along the face axis at 0.3 s) and only after that comes forward. The forward peak is about +0.55 m at 0.8 s, toward a marker placed in front of the nose. The other hand stays behind. That is an asymmetric bite, not a reach behind the face.

Shambler windup is 0.45 s and recover is 0.65 s. Runner windup is 0.28 s. Damage is applied at the end of windup, inside `HordeZombie._resolve`. At 0.45 s the reaching hand is still near the chest, not at the 0.8 s peak. The timers were not changed. Playing `attack2` at 1× from the start of windup finishes near the end of a shambler's recover. The hero is hit on the old timer, before the visual bite.

Blend 0.30 s from the current loop into `attack2`, `hit`, and `death`. The harness frames are `xfade_walk_to_attack2_05.png` (still the walk) and `xfade_walk_to_attack2_30.png` (one arm out, the other not yet). `mobile_attack2_arms_out.png` is the unblended first frame, kept so the arms-out pose is visible.

Facing: `HordeZombie._face_toward` uses `atan2(-to.x, -to.y)`, so yaw 0 looks down −Z. The presenter applies `rotation.y = PI` on the glTF node, the same turn `CharacterRig` uses. Root motion is already zero. Do not add it.

The distant crowd is not a skeleton and not `hooded_male_far.glb`. That 783-tri mesh is an optional fallback only. It is thinner, darker, and block-headed, and it hard-pops. Do not certify it as the crowd look.

The primary far crowd is `far_impostor/impostor_atlas_8dir_1024.png` on a Y-billboard quad (`validation/hooded_male/impostor_billboard.gdshader`), one MultiMesh, no AnimationPlayer. Instance custom.x is the face yaw in radians, 0 meaning the face points down −Z. The shader picks one of 8 atlas cells. `view_bias` is 4 so the cell in front of the nose is the baked front, not the cloak. Alpha below 0.5 is cut. A dither fades the card in from 8 m to 14 m while the mobile body fades out, and the same band runs backwards. Feet of the quad sit on y = 0. The card does not turn into a line from the side, because it billboards.

`HordeCrowd` in the game is still a capsule MultiMesh. Pointing it at this card is Lucky's wiring, not done here.

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

- No phone, no real GPU. The pictures in this pass are llvmpipe on X11. They are not a phone budget. See `SAFETY.md`.
- Damage still fires at the end of windup (shambler 0.45 s, runner 0.28 s), before the 0.8 s visual bite. Those timers were not changed.
- `hooded_male_far.glb` (783 tris) stays an optional fallback. It was not the crowd in the safety pass and it is not certified.
- `MODEL_HOOK` is still empty. This package was not sent onward.
- Soldier and female. Not started from this package.
