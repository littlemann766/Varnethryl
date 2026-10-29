# Voxel capes v1 (2026-10-29, review only - do NOT ship until the boss approves the video)
Cape cubes are re-rigged onto a capeV_c{col}_r{row} bone grid (10 rows x 5 cols; guard tabard 6x3), anchored at the chest/upperChest.
Each cube stays 100% on one bone (no stretch). Every clip is baked with procedural airflow: lag from body velocity + per-clip wind, travelling ripple, gravity hang, and capsule push-out from the torso and legs. Loops are seamless.
The check (cape cubes in body/leg cells, over the rest baseline) is 0 on every walk/run/idle/fly clip, with one exception: Darius fly_fast reaches 214 vertices on 5 frames.
Some attack/death clips still have contacts, e.g. death, where he lies on the cape. See *.cape_checks.json.
Godot 4.7.2 headless import: 0 errors.
Tools: tools/capes (capes.py name R C; spec.json per character).
