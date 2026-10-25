# Volcano Titan arena: notes for Lucky (Beth, 2026-10-25 ET)
All coordinates are in index.json (Godot space, origin = cone centre at ground). Suggested placement: replace `volcano_flank_hi` at (405, height, -402), scale 1.

## Files
- `volcano_titan(.glb|_lod1|_lod2)`: the mountain. Phone uses lod1. `volcano_titan_col.glb` is the main collision (path, rim, basin floor).
- `volcano_arena_stage{1,2,3}(.glb|_lod1|_lod2)`: swappable arena floor. Show ONE stage at a time, plus its `_col.glb`.
- `volcano_arena_stage{N}_hazard.glb`: flat lava area at y 37.05 for that stage. Build an Area3D from it, or use `hazard_polys` in index.json. The moat ring (r 33.5-40) is lava in every stage.
- `titan/ashentitan_volcano_glow(_lod1).glb`: the Titan (20.955 m) with an emissive crack and eye map. Same rig and 12 clips as characters/.
- Markers inside the mountain GLB: `vent_*`, `smoke_plume`, `arena_center`, `titan_spawn`, `path_start`, `path_end`. Lights aren't in the GLB, so add orange OmniLight3Ds at the moat and vents.

## Staged fight (suggested)
| Stage | Titan HP | Floor | Titan emission_energy_multiplier | Attacks | FX |
|---|---|---|---|---|---|
| 1 | 100-66% | crust plates, thin glowing seams | 1.0 | rock throws (`boulder_hurl`), melee | light smoke at the vents, a few embers |
| 2 | 66-33% | wider cracks, about 25% of plates sunk to lava | 2.2 | + lava slam (ground AoE ring, `attack3`/`skill`) | more smoke, ember rate x2, vent bursts |
| 3 | 33-0% | 6 islands linked by stepping-stone plates | 4.0 | + falling-rock rain (random telegraphed circles), attack speed about +25% | heavy plume, ember rate x4, ash fall |

- Stage swap: camera shake (0.6 s), particle burst (embers + rock chunks) at the arena centre, `volcano_roar`. Then swap the floor mesh and its col and enable that stage's hazard Area3D. Plates near the spawn and the ramp landing are never removed.
- Hazard zones: lava deals damage over time (for example 15%/s max HP to players) and plays a burn VFX. Push players up if they're under y 38.
- Intro: when the player crosses the rim cut (path_end region, or the index `path.breach` point), the camera pulls wide over the crater. The Titan rises out of the central lava pool at (0, y, 0) (starts at y 10, tweens to 26.8 over 3.5 s, with smoke and embers), plays `volcano_roar` and shows the name card "ASHEN TITAN". Then show the boss HP bar (top centre, with stage notches at 66% and 33%).

## Budgets
Mountain High 291k / lod1 95k / lod2 40k. Stage 1 High 24.9k / lod1 10.7k / lod2 2.3k (stages 2 and 3 are smaller).

## Titan in the lava (2026-10-25 update)
- Scale the Titan by **1.3362** (20.955 m -> **28.0 m**). Place him at x 0, z 0, yaw 40 deg (faces the ramp landing). He stands IN a 20 m wide lava pool (r 10 m, surface y 38.0) cut from the centre of all 3 stages. The pool is hazard in every stage (it is in each `_hazard.glb` and `hazard_polys`). The old spawn plate is gone; the ramp-landing plate is kept in all stages.
- Root (feet) y per stage: **1: 26.8** (lava at mid-thigh), **2: 21.0** (waist), **3: 18.4** (lower chest). Head top 54.8 / 49.0 / 46.4; rim is 72-77 so he never pokes over it.
- Sink: during the stage swap, start 0.2 s into the 0.6 s shake and tween root y old -> new over 1.6 s (sine in-out). Disable root motion for walk/run; he never leaves the pool.
- `titan_lava_ring.glb` (48 tris): glowing collar at the waterline. Put it at (titan x, 38.03, titan z), scale xz 7 / 7 / 8 per stage, unshaded emissive, alpha blend, no depth write.
- Attack reach: his clips were authored standing on the ground, so slams land at his root height (under the lava). Hit-test from the hand bones (`hand_L`, `hand_R`) against players, and spawn ground-slam AoEs at plate height (y 39.05) under the hand's xz, not at the root. Reach is about 17 m horizontal: plates at r 10-17 are the danger ring. In stages 2-3 his idle hands hang in the lava, so the player hurtbox should be his body above y 38 (torso/head capsule), plus the arms when an attack brings them up.
- Shots: `shots/contact_titan_pool.jpg` (hero, player-on-plate and side view per stage).
