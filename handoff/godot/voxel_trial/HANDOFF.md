# Voxel trial (Owner, Selene, Darius) — REVIEW ONLY, do not install

The boss asked for a blockier, Minecraft-like voxel style. These are trial builds for his review. Nothing here goes into the game until he approves the video (`/workspace/hero-motion/voxel_trial_v1.mp4`).

Files: `owner_voxel.glb`, `selene_voxel.glb`, `darius_voxel.glb` (+ `*.stats.json`). Built by `tools/voxel/vox.py` (Blender 4.2, scene at 30 fps before import).

- **Source:** each hero's current height-baked rig `/workspace/rigged/<hero>_h.glb` plus the fly clips from `handoff/godot/heroes_fly/<hero>_fly.glb`. Skeleton and bone names are unchanged.
- **Method:** a surface shell of 4.5 cm cubes on a grid (the Owner is 1.905 m, about 42 cubes tall). Each cube has one flat colour sampled from the original texture and is bound 100% to one bone (the dominant weight at that spot), so cubes move rigidly and never stretch. Faces between neighbouring cubes on the same bone are culled. Colours come from a tiny palette texture with nearest filtering, so turn filtering off (Nearest) in Godot.
- **Owner:** Pikachu onesie in yellow with brown stripes (back, arms and legs), hobbit-feet slippers (skin-tone feet with brown hair tufts on top), and the purple cape with gold trim from the model.
- **Darius:** a gold cross painted on the purple tabard, and a voxel sword bound to `hand_R`.
- **Selene:** colours come straight from her model.

| hero | cubes | triangles | vertices | clips |
|---|---|---|---|---|
| owner | 3532 | 17176 | 34352 | 19 (walk/run/idle/attack/attack2/hit/death/saber set + 7 fly) |
| selene | 3222 | 15892 | 31784 | 10 (idle/walk/run + 7 fly; she has no attack clips on this rig) |
| darius | 3133 | 15212 | 30424 | 14 (walk/run/idle/attack/attack2/hit/death + 7 fly) |

The headless Godot 4.7.2 import loads all 3 with 0 errors, and each has 1 mesh and 1 Skeleton3D with the clips above. Turn on loop for the loop clips at import, the same as heroes_fly.

Known limits (v1): there are small gaps at bending joints because cubes are rigid per bone. Faces are only a few cubes wide. Selene's rig has 27 bones (one `cape` bone) and no attack clip. The Owner has no Pikachu ears or hood up because the model has none.
