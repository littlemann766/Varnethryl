# Voxel NPC clips + crowd LODs v3 (2026-10-29), based on capes_v2 (3f335f5)
New clips (Quaternius Universal Animation Library, CC0, retargeted with tools/voxel_v3/rt2.py, contact foot lock, cape re-baked with capes.py):
- selene_voxel.glb: attack1 (Spell_Simple_Shoot, 0.5 s), attack2 (Punch_Cross, 1.0 s), hit (Hit_Chest, 0.33 s), death (Death01, 2.4 s). 14 clips total.
- holyknight_villain_voxel.glb: death (Death01, 2.4 s). 6 clips total.
Fixes on the new clips: death upper-arm abduction on frames 20-30 (fixarm.py, 45 deg) to keep the arms/staff out of the legs; gclamp.py lifts the hips so nothing goes below the ground in hit/death (lowest point within -6 cm of the rest sole).
Checks (check1.py, EVERY frame, counts over the rest baseline): selene all 14 clips arm-in-leg 0 and cape-in-body 0. Villain death 0/0.
Known: villain attack/hit from earlier work still show staff/fingers in the leg cells (attack 1861, hit 3369 verts); not changed here.
Crowd LODs (lod.py: re-voxelize on a coarser grid, 1.5x and 2.3x cube size, rigid 1-bone cubes, same rig/clips/material):
- town_guard: LOD0 129,468 tris; LOD1 36,164 (27.9%); LOD2 13,596 (10.5%). 8 guards: 1.04M / 289k / 109k.
- holyknight_villain: LOD0 181,424; LOD1 50,052 (27.6%); LOD2 18,320 (10.1%).
LOD meshes are coarser so the 1.8 cm check grid reports small overlaps (see *_lod*.cape_checks.json); intended for distance use.
town_guard_voxel.glb is unchanged from capes_v2. Godot 4.7.2 headless import: 0 errors (7 GLBs). Blender 30 fps.
