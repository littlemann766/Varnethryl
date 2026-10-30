# Voxel NPC clips v4 (2026-10-29) - supersedes capes_v3
- Sealed meshes (tools/voxel_v3/seal.py): faces between cubes bound to different bones are now kept, so joints/capes no longer open see-through holes ("speckled" look). Isolated single cubes removed. Opaque, backface-culled material.
- Arm/weapon-in-leg fixed (tools/voxel_v3/autofix.py, iterative upper-arm abduction <=15 deg): villain attack/hit/walk, guard attack/walk.
- Selene rebuilt from the committed capes_v3 GLB (re-imported at 30 fps; re-check: all 14 clips 0/0).
- check1 (every frame, frames over 24 verts vs rest): every clip on all 7 GLBs arm-leg 0 frames, cape-in-body 0 frames, EXCEPT selene attack1 cape 2 frames (max 64 verts).
- Tris: selene 142,416; villain 213,080 / LOD1 59,700 (28%) / LOD2 20,832 (9.8%); guard 139,948 / LOD1 38,628 (27.6%) / LOD2 13,604 (9.7%).
- Godot 4.7.2 headless import: 0 errors (7 GLBs). Blender 30 fps.

## v4.1 (2026-10-29 late)
- Added owner_voxel.glb (19 clips) and darius_voxel.glb (14 clips): sealed from capes_v2; arm-leg fixed with autofix.py (owner fly_fast; darius attack/attack2/death/fly*/hit/idle, <=40 deg on fly banks). All clips 0/0.
- selene_voxel.glb: attack1 cape re-baked (0). Death redone: body ground-snapped so she lies fully on the floor (chest/hips on the ground, resting on her cape ~4 cm), cape no longer props her up, cape drapes flat after landing (capes.py drape_death + dropfix.py shrinks patches that would go under the floor/body). Cape min -1 cm, 0 cape-in-body. Source is still Quaternius Death01 (UAL1/UAL2 contain no other death clip).
- holyknight_villain_voxel(+lod1/lod2): cape re-baked with stronger column constraint (lxtol 1.0, 20 iterations, final lateral pass) so it no longer splits into strips; seal.py CLEAN removes loose cape chunks (lone-bone cells re-bound, small detached cape components dropped) and cape cubes inflated 1.3x to close seams. All clips 0/0.
- Owner Pikachu: hood ears (black tips) and hobbit slippers read clearly; the hood has no Pikachu face or red cheeks in the source texture (not added).
- Godot 4.7.2 headless import: 0 errors.
