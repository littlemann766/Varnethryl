# Locomotion v1 from a licensed animation library — REVIEW ONLY, do not install

The boss reviews `/workspace/hero-motion/mocap_locomotion_v1.mp4` first. Nothing here goes to Lucky or into the build until he approves.

## Source and license
- **Quaternius Universal Animation Library 1 [Standard]**, the free tier (https://quaternius.itch.io/universal-animation-library), downloaded anonymously with no sign-in on 2026-10-29. The zip sha256 is `cc73fc4e495b82958207316596317a3f40b9fa38065bde1027937452da537724`.
- **License:** CC0 1.0 Universal (public domain), which is free for commercial use with no attribution required. The license text is in `tools/mocap/src/LICENSE_UAL1_CC0.txt` and the source GLB is `tools/mocap/src/UAL1_Standard.glb`.
- The UAL2 pack (also CC0, sha256 `4008ea20…2a68`) was downloaded for the attack proposals. It isn't used yet.
- **Note:** Quaternius clips are animated by a professional animator on a humanoid rig. Quaternius doesn't describe them as raw motion capture. No Mixamo, and nothing that needs a sign-in.

## Clips (30 fps, in place, loop at import)

| clip | UAL1 source | frames |
|---|---|---|
| walk | Walk_Loop | 40 (1.33 s) |
| run | Jog_Fwd_Loop | 28 (0.93 s) |
| idle | Idle_Loop | 75 (2.5 s) |

The other clips in each file (attack, fly, etc.) are unchanged from voxel v2. The town guard gains a `run`.

## Retarget method (`tools/mocap/retarget.py`, Blender 4.2, scene at 30 fps before import)
- **Rotations:** each source bone's world-space rotation change is transferred to the target, with a per-bone correction so each target bone points the way the source bone does. Bone lengths are never changed, so there is no stretch: every voxel cube is 100%-weighted to one bone, so the 99th-percentile edge stretch is 0%.
- **Hips:** height is scaled by the hip-height ratio. Root and hips have no horizontal travel, so the clips stay in place.
- **Foot IK:** the ball of the foot is locked while it is on the ground, moving backward at exactly the root speed. Heel and ankle roll around it (heel-to-toe), with 4–6 frame blends at contact start and end and analytic 2-bone leg IK. In idle the feet are planted.
- **Measured foot slide** with the root moving at the listed speed: 0 mm per frame for every character and clip. The worst is the Owner's walk at 1.3 mm per frame. Details are in `<name>.slide.txt`.
- **Capes** follow the chest rigidly. In-game root speed must match: speeds in m/s are in `<name>.speeds.json`.

| character | walk m/s | run m/s | arm offset (walk/run, idle) | weapon hand |
|---|---|---|---|---|
| owner | 1.12 | 6.98 | 0 | mocap |
| selene | 0.96 | 5.55 | 0 | mocap |
| darius | 1.02 | 5.85 | 14°, 18° | right hand keeps its rest orientation (sword hangs clear) |
| town_guard | 1.04 | 6.11 | 20°, 20° | right forearm and hand keep their rest orientation (hammer) |
| holyknight_villain | 1.19 | 7.10 | 26°, 18° | both hands keep their rest orientation |

The run source is a fast jog of about 5–7 m/s. If gameplay wants a slower run, play it at a TimeScale of 0.75 and scale the root speed the same way.

## Clearance checks (`<name>.checks.json`, every 2nd frame, counted above the rest pose)
- Cape into body or legs: 0 for the Owner, Selene and Darius in walk, run and idle.
- Arms into legs: 0 for the three heroes.
- **Town guard walk:** 5 frames with up to 50 hammer vertices touching the leg (about 2 cubes).
- **Villain walk:** 8 frames with up to 116 hand/staff vertices touching the leg.
- Run and idle: 0 for both NPCs.

The headless Godot 4.7.2 import loads all 5 with 0 errors. Each has walk 1.333 s, run 0.933 s, idle 2.5 s and 1 mesh.
