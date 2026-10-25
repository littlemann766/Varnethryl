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
- Intro: when the player crosses the rim cut (path_end region, or the index `path.breach` point), the camera pulls wide over the crater. The Titan rises from the lava at `titan_spawn` (starts at y about 20, tweens to 39.05 over about 3 s, with smoke and embers), plays `volcano_roar` and shows the name card "ASHEN TITAN". Then show the boss HP bar (top centre, with stage notches at 66% and 33%).

## Budgets
Mountain High 291k / lod1 95k / lod2 40k. Stage 1 High 27k / lod1 12k / lod2 2.6k (stages 2 and 3 are smaller).
