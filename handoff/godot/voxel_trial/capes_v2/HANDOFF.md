# Voxel capes v2 (2026-10-29) - replaces capes_v1 (dcfc9b2). Same file names, rigs, and clip names.
Fixes vs v1:
- Owner fly: the cape is now one connected sheet (columns move in phase on fly clips, with a stronger cross-column tie), not separate strips.
- Cape-in-body/legs check (cape cubes in body/leg cells, over the rest baseline) is 0 on EVERY clip for all 5 characters: attacks, death, saber, fly_fast included (see *.cape_checks.json). The fix keeps the cape's rest clearance from the lower back during torso bends and adds a larger push-out margin on non-loop clips.
- Villain: stray red cubes are no longer on the cape rig. Only the main connected cape component is rigged, so the loose bits stay on the body bones.
Godot 4.7.2 headless import: 0 errors. Animation counts: owner 19, selene 10, darius 14, villain 5, guard 4.
