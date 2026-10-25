# Hero fly clips (for Lucky)

The boss said "my character should fly not walk on the air". These are authored fly clips for 29 heroes, on each hero's existing rig at its HEIGHTS.md height (`/workspace/rigged/<name>_h.glb`, so the bone names are unchanged). They are generated in code (`tools/fly.py`, Blender 4.2) at 30 fps and checked with a headless Godot 4.7 import: all 29 load with 7 clips each.

Files: `<hero>_fly.glb`. Each holds the mesh and skeleton plus only the 7 fly clips. Copy the animations into the hero's existing AnimationLibrary, or load the file as a library. The skeleton and bone names match the hero's current GLB.

| clip | length | pose |
|---|---|---|
| fly_hover | 2.0 s | upright, ~8° lean, slow bob, legs relaxed with knees bent, arms loose |
| fly_forward | 1.6 s | body pitched ~64° (plus chest arch), legs trailing, arms swept back, cloth and hair streaming |
| fly_fast | 1.0 s | ~78°, flatter and streamlined, arms tight, legs together, faster flutter |
| fly_ascend | 1.6 s | ~14° lean, chest up, arms pushing down and back, legs trailing below |
| fly_descend | 1.6 s | leaning back, legs forward and braced, arms out for balance, cloth blown up |
| fly_bank_L / fly_bank_R | 1.6 s | the fly_forward pose rolled ±34° with ~8° yaw; inner arm out, inner knee tucked |

- **Loops:** every channel uses whole sine cycles over the clip, so the last key equals the first. Turn on loop in the import (no `_loop` suffix was added because of the name clash we hit before).
- **In place:** the `root` bone is never keyed. `hips` gets only a small vertical bob (≤2% of height) and the body rotation around the hips. There is no horizontal translation, so drive movement from code.
- **Facing:** the model faces +Z in glTF, the same as the other hero files.

## Blend tips
- Use a BlendSpace2D: x = lateral turn rate (fly_bank_L / fly_forward / fly_bank_R), y = speed (fly_hover → fly_forward → fly_fast). Put fly_ascend and fly_descend on a separate vertical-speed Blend3 (descend / [speed space] / ascend) driven by vertical velocity.
- Use crossfades of 0.25–0.35 s, and about 0.4 s between hover and forward (that blend carries a ~56° pitch change).
- Sync phase: the clip lengths are 2.0/1.6/1.0 s, so when blending forward and fast, scale fast's TimeScale by 1.6 or let the AnimationTree sync.
- From walk or run into flight, go to fly_ascend first, then fly_forward. For landing, fly_descend leads into idle.
- These clips have no wings. Ember, Zephyr and Cinder already have their own flap/glide/hover clips.

## Stretch check (99th percentile edge stretch, %, worst frame of any fly clip, compared with the hero's own walk clips)
The rigs' own walk clips already stretch a lot on the blocky originals (fused hands and cloth weights bleeding into the limbs). The target was to stay at or under each hero's walk. Cloth/hair secondary motion was auto-scaled (`seck` 0–1) to stay under that.

| hero | walk p99 | fly p99 max | seck | over walk |
|---|---|---|---|---|
| aldric | 265.6 | 243.6 | 1.0 |  |
| asha | 99.3 | 171.1 | 1.0 | yes |
| brynn | 202.4 | 63.6 | 1.0 |  |
| cedric | 405.9 | 257.1 | 1.0 |  |
| coral | 309.3 | 252.2 | 0.5 |  |
| darius | 56.8 | 36.7 | 0.5 |  |
| elira | 306.0 | 235.5 | 1.0 |  |
| finn | 278.0 | 234.5 | 1.0 |  |
| garruk | 29.2 | 26.4 | 1.0 |  |
| kael | 194.0 | 187.7 | 1.0 |  |
| lunara | 113.9 | 129.9 | 1.0 | yes |
| marella | 463.8 | 395.6 | 0.5 |  |
| mirelle | 255.1 | 190.0 | 1.0 |  |
| mortimer | 88.9 | 80.4 | 0.5 |  |
| morwen | 337.8 | 205.5 | 1.0 |  |
| nyx | 83.4 | 95.1 | 1.0 | yes |
| orin | 365.6 | 169.8 | 1.0 |  |
| owner | 60.6 | 42.0 | 1.0 |  |
| player_pikachu | 134.3 | 72.9 | 1.0 |  |
| rook | 199.5 | 231.8 | 1.0 | yes |
| rowan | 323.4 | 294.7 | 1.0 |  |
| selene | 135.7 | 104.8 | 1.0 |  |
| seraphine | 275.8 | 206.8 | 1.0 |  |
| snowy | 32.7 | 69.9 | 1.0 | yes |
| talia | 183.2 | 121.4 | 1.0 |  |
| thorne | 419.6 | 76.5 | 1.0 |  |
| thrain | 149.0 | 139.9 | 1.0 |  |
| vesper | 205.7 | 127.6 | 1.0 |  |
| wren | 20.2 | 49.4 | 1.0 | yes |

Over walk: asha, lunara, nyx, rook, snowy and wren. The cause is arm and leg weights shared with coat/cape bones on those rigs, and it stays over even with zero cloth motion. They are fine at game camera distance but should get a weight pass.

Skipped: Ember, Zephyr, Cinder (winged creatures that already have flight clips) and Pip (quadruped).
Preview: /workspace/hero-motion/heroes_fly_v1.mp4 (Owner, every clip side and 3/4, plus a lineup of all 29).
