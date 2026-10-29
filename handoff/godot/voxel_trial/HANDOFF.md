# Voxel trial v2 (heroes) + NPCs v1 — REVIEW ONLY, do not install

The boss reviews the videos first: `/workspace/hero-motion/voxel_trial_v2.mp4` and `/workspace/hero-motion/voxel_npcs_v1.mp4`. Nothing here goes into the game until he approves.

## Build (`tools/voxel/vox2.py`, Blender 4.2, scene at 30 fps before any import)
- **Cubes:** 1.8 cm on the body and 0.8 cm on the head and face (the region above the neck). Face colours are taken by ray-casting onto the outer surface, and eye, brow and beard contrast is boosted.
- **Skinning:** each cube is bound 100% to one bone, so cubes move rigidly and nothing stretches. Faces between neighbouring cubes on the same bone are culled. Colours come from a palette texture, so use Nearest filtering.
- **Heroes:** same rigs and bone names as before (`/workspace/rigged/<hero>_h.glb`, plus the fly clips from heroes_fly).
- **Owner:** Pikachu onesie with brown stripes, a Pikachu hood hanging down his back with ears (black tips) on the `hood` bone, and big hairy hobbit-feet slippers (toes in front, brown hair on top).
- **Darius:** a gold cross on the front of his purple tabard, and a sword on `hand_R`. A sword check over every 3rd frame of all 14 clips found 0 body hits and 0 frames below the floor.
- **NPCs:** the boss's models are in `source/` (`*_original.glb`). They keep their own fitted Mixamo skeleton (65 bones). They were scaled (guard 1.85 m, villain 1.95 m), and new in-place clips were authored in code (`tools/voxel/anim.py`). Cloth cubes that the auto-skin had on arm or leg bones (cape, tabard) were moved to the nearest torso bone so the cape doesn't swing with the arm.
  - `holyknight_villain_voxel.glb`: the white and red crusader with the long cape (enemy). Clips: idle, walk, run, attack, hit.
  - `town_guard_voxel.glb`: the blue and gold knight with a warhammer and shield (town guard). Clips: idle, walk, attack.

| model | cubes | triangles | vertices |
|---|---|---|---|
| owner | 36222 | 130296 | 260592 |
| selene | 26933 | 132064 | 264128 |
| darius | 30627 | 132584 | 265168 |
| town_guard | 27422 | 129468 | 258936 |
| holyknight_villain | 40323 | 181424 | 362848 |

The headless Godot 4.7.2 import loads all 5 with 0 errors, and each has 1 mesh and 1 Skeleton3D. Turn on loop at import for idle, walk and run.

**Phone estimate:** about 130k triangles per character is fine on a recent mid or high-end phone for 1–3 on screen. It is too heavy for crowds or low-end devices. Before shipping, a greedy-mesh pass (merging same-colour coplanar faces) should cut that 3–5x, plus a 3–4 cm LOD for distance. The GLBs are 15–21 MB because the cubes don't share vertices.
