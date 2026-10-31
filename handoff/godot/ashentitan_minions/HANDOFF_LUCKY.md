# Ashen Titan minions (adds) — rigged + animated, branch heroes-motion-pass only

The Titan's adds are spawned by `scripts/world_boss.gd` `_spawn_adds()` (each broken weak point, and every 45 s
while he is not walking and a hero is within 200 m): 3 × `wb_ash_fiend_lod1` + 2 × `wb_ember_wisp_lod1`, max 12,
freed after 90 s. Today they are static meshes with no Skeleton/AnimationPlayer (audit rows: "static mesh with no
clips"); fiends stand still and wisps only bob/spin in `_update_adds()`. There is no minion AI, movement, damage or HP.

## Files (drop-in replacements for res://assets/volcano/worldboss/, same names, same +Z forward, scale 1)
| file | what |
|---|---|
| wb_ash_fiend.glb / _lod1.glb | 2.45 m fiend, rig `ash_fiend_Rig` (24 bones), clips idle, walk, run, attack, attack2, attack3, hit, death |
| wb_ember_wisp.glb / _lod1.glb | 1.3 m wisp, rig `ember_wisp_Rig` (15 bones; 7 shards each on its own rigid bone), clips idle, walk, run, attack, attack2, hit, death |
| minion_events.json | per clip: frames, loop, speeds, footsteps, attack windup/hit frames, hit point, reach, death ground-impact frame |
| checks.json | ground, single-frame step and arm-in-leg measurements |
| preview/ash_fiend_preview.mp4, preview/ember_wisp_preview.mp4 | every clip in order (walk/run move at their speed) |

Vertex colours (COLOR_0) are unchanged, so `wb_fiend_mat.tres` / `wb_wisp_mat.tres` as material_override still work
(skinning is applied before the shader's vertex flicker).

## Clips (30 fps, in place)
Fiend (Quaternius CC0 UAL1/UAL2 retargeted, foot-locked walk/run, feet locked in idle/attacks/hit):
- idle 2.50 s loop · walk 1.33 s loop @ 0.96 m/s · run 0.93 s loop @ 5.95 m/s
- attack `claw_rake` 1.97 s: windup 4→15, **hit f21 (0.70 s)**, right claws, reach 1.46 m
- attack2 `hook_haymaker` 1.30 s: windup 1→8, **hit f14 (0.47 s)**, reach 2.27 m (big telegraph)
- attack3 `quick_cross` 1.17 s: small windup, **hit f11 (0.37 s)**, reach 1.32 m
- hit 0.33 s · death 2.40 s (falls back, lands f26, lies on the ground)
Wisp (hand-keyed; no humanoid mocap fits a floating spirit):
- idle 2.0 s · walk 1.33 s (lean 14°, suggest 2.5 m/s) · run 0.80 s (lean 30°, tail streams, suggest 6 m/s)
- attack `ember_lash` 1.2 s: rear back 0–14, hold, lunge, **hit f20**, reach 1.3 m
- attack2 `shard_burst` 1.4 s: shards contract + spin up 0–18, burst out to 2.2 m **hit f21**, shards return
- hit 0.4 s · death 1.8 s: shudder, gravity fall from 2.0 m hover, lands f32, bounce, settles on the ground

Checks: Godot 4.7.2 headless import 0 errors/0 warnings; all 4 files load with their AnimationPlayer.
Largest frame-to-frame bone rotation ≤ 37° (fast strikes time-stretched so no frame jumps > 30°; run knee pop despiked).
Fiend arms never come within 19 cm of the legs in any clip. Feet on the ground (≤ 3.7 cm).

## What you need to wire up (I did not touch game code)
1. Copy the 4 GLBs over the ones in res://assets/volcano/worldboss/ and reimport. Set loop on idle/walk/run
   (`ap.get_animation("walk").loop_mode = Animation.LOOP_LINEAR` or in the import dock).
2. In `_update_adds()` replace the static/bob logic with a tiny state machine per add:
   chase the nearest hero (`_hero()`), snap feet to `_gy(x,z)` (wisp: +2.0 m), face it, play walk/run and move at
   the clip speed (scale `ap.speed_scale` = move speed / clip speed); in range (fiend reach 1.5–2.3 m, wisp 1.3 m or 2.2 m AoE)
   play an attack and apply damage once at its `hit_frame` from minion_events.json; cooldown ~2–3 s.
   Remove the wisp's code bob/spin when its clips play (the clips already bob and orbit the shards).
3. Give adds HP and a hit target: on damage play `hit`; at 0 HP play `death` (hold last frame), stop moving, free after ~4 s
   instead of the fixed 90 s lifetime.
4. Keep the existing cap of 12 adds; use the _lod1 files as now.

Tools: varn-core/tools/minions/ (rig_fiend.py → rt_fiend.py → post.py → export.py; rig_wisp.py; check.py, mind.py, pv.py, chk.gd).
