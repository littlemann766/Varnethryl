# On-hero fit review (not gameplay, not finished)

The armor was checked on the real voxel heroes. This folder is a review record. `tools/knight_rig/review_on_hero.py` is the only scene. It is not autoloaded and it is not referenced by the game.

Hero files were read from git and not copied onto this branch:

| Body | Ref | Clips that actually move |
|---|---|---|
| Darius, weaponless (male the armor was fitted to) | `origin/weaponless-rigs:voxel/darius_voxel_noweapon.glb` | idle, walk, run, attack, attack2, hit, death, fly_* |
| Talia | `origin/main:voxel/talia_voxel.glb` (same clips on `origin/weaponless-rigs`) | idle, walk, run, attack1, attack2, attack3, skill, hit, death, fly_* |
| Rook (taller male, different build) | `origin/main:voxel/rook_voxel.glb` | idle, walk, run, attack1, attack2, attack3, skill, hit, death, fly_* |

No jump clip is in those three GLBs. `tests/jump_test.gd` on main is a code test, not a character animation. `knight_female.glb` lists `jump`, `jump_hang`, `jump_land`, `jump_start`, `swim_stroke`, and `swim_tread`, but every channel in that file is two identical keys. A real jump comparison needs a hero GLB that contains a jump clip.

## How the review pose is built

Anatomical rotations are copied off the hero clip. Bones whose rest direction differs (Darius arms: 8.9° upper arm, 23.7° forearm, the same figures as `retarget_fix.py`) get that correction. Hips location is copied too, because the clips move the hips (attack up to 20 cm). Plate helpers exist only on the review armature: pauldron 0.45, elbow and knee 0.5, tasset 0.85, tabard on thigh X, forearm twist 0.5. The hero angles are not soft-limited.

Talia and Rook do not share Darius’s rest. Their hips were translated onto the armor hips for the overlay. The armor was not scaled. Talia has no `spine2` or `upperChest`. Her mesh rests with the arms out; the female armor rests with the arms down. Rook’s hips sit about 15 cm off the male armor before that translation, and his mesh is about 1.93 m tall against the armor’s 1.85 m.

## What the pictures show

Renders are 1400×1860, neutral sun and fill, from the actual GLBs.

Darius and the male armor share hips, spine, and leg bones exactly, so they can occupy the same figure. The voxel coat, shoulders, head, and hands are larger than the plates. On idle, walk, run, and attack the body shows outside the armor, and the knee and elbow still open into hollow gaps. Reseat versus the previous binding, same frames, pixels that differ by more than 40 levels: idle front 728, walk front 2292, run front 2375, attack front 4794, out of 2,604,000. That does not close the gaps.

Talia’s attack1 before/after differs in about 338,000 pixels, but both frames show the same problem: her arms stay out in the robe and the armor does not sit on them. Joint reseat cannot fix a rest pose the sculpt does not share. Rook’s run and attack, with the male armor unscaled, leave the plates inside the larger body.

Further reseating was not applied. The remaining misses are missing under-geometry and bodies that are not the armor’s rest shape. New plates, a global scale, or stiffer clips would violate the review limits, and they would not be an honest fix.

Numbers: `metrics.json`. Sheet: `contact_on_hero.jpg`.
