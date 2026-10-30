# Voxel NPC clips v4 (2026-10-29) - supersedes capes_v3
- Sealed meshes (tools/voxel_v3/seal.py): faces between cubes bound to different bones are now kept, so joints/capes no longer open see-through holes ("speckled" look). Isolated single cubes removed. Opaque, backface-culled material.
- Arm/weapon-in-leg fixed (tools/voxel_v3/autofix.py, iterative upper-arm abduction <=15 deg): villain attack/hit/walk, guard attack/walk.
- Selene rebuilt from the committed capes_v3 GLB (re-imported at 30 fps; re-check: all 14 clips 0/0).
- check1 (every frame, frames over 24 verts vs rest): every clip on all 7 GLBs arm-leg 0 frames, cape-in-body 0 frames, EXCEPT selene attack1 cape 2 frames (max 64 verts).
- Tris: selene 142,416; villain 213,080 / LOD1 59,700 (28%) / LOD2 20,832 (9.8%); guard 139,948 / LOD1 38,628 (27.6%) / LOD2 13,604 (9.7%).
- Godot 4.7.2 headless import: 0 errors (7 GLBs). Blender 30 fps.
