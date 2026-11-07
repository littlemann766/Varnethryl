# Island scenery for test 54 — separate from the frozen terrain commit

Terrain shader, arrays, and terrain meshes stay at `86e61c6e`. Collider glbs were not rewritten. `trunk_bounds.json` is the manifest already sent to Lucky and was not rewritten.

Foliage is cutout cards in the old canopy patch. A tall piece is a cone of needle fans (Foliage001 blades). A wide piece is a cluster of photographed leaves (LeafSet001). Bushes sit on the old ground contact. Grass is blade cards. Flower heads are painted on those blades. Trunks and rocks keep their vertices. Trunks take a cylindrical UV into Bark012 (albedo and normal). Rocks sample the existing Rock023 photo. `trunk_bounds.json` was not rewritten.

Test 54 (`33ec05515fa2907c1d6958e39e884eed92955776`) has no `land_scatter` files. `tw_sea.gd` `_files` will load any `arch_` / `coast_` / `frost_` / `ash_` glb you copy into `res://tidewrack/stageN/meshes/`, and any name ending in `_col` becomes a trimesh static body. It is not drawn.

## What to copy

- `shaders/vc_scatter.gdshader` to `res://tidewrack/stage1/shaders/vc_scatter.gdshader`. Four samplers, separate from the terrain arrays: `bark_albedo.jpg`, `bark_normal.jpg`, `rock_albedo.jpg`, `foliage_atlas.png`.
- Those files from `textures/`. Provenance is in `textures/FOLIAGE.md`.
- Every `*land_scatter*.glb` and `*land_scatter*_lod1.glb` that has a matching `*land_scatter*_col.glb`. Copy the col file with it, unchanged. That is 168 chunks. The visual and the box were written from the same placement, so the trunk or rock sits on that box. Do not scale or move one without the other.
- Do not copy these 14 visuals. They have no collider. Several are tall enough to read as a trunk or spire, and a solid-looking prop with no body is a walk-through.

| File | Visual height span |
|---|---:|
| `stage2/meshes/coast_land_scatter_c13_21.glb` | 18.52 m |
| `stage4/meshes/ash_land_scatter_c25_28.glb` | 5.31 m |
| `stage1/meshes/arch_land_scatter_c21_21.glb` | 4.25 m |
| `stage4/meshes/frost_land_scatter_c16_08.glb` | 4.13 m |
| `stage2/meshes/coast_land_scatter_c12_17.glb` | 3.76 m |
| `stage2/meshes/coast_land_scatter_c13_19.glb` | 3.43 m |
| `stage1/meshes/arch_land_scatter_c19_23.glb` | 2.65 m |
| `stage4/meshes/ash_land_scatter_c15_30.glb` | 1.50 m |
| `stage4/meshes/frost_land_scatter_c21_13.glb` | 0.88 m |
| `stage4/meshes/ash_land_scatter_c16_29.glb` | 0.82 m |
| `stage2/meshes/coast_land_scatter_c11_14.glb` | 0.69 m |
| `stage1/meshes/arch_land_scatter_c16_20.glb` | 0.59 m |
| `stage4/meshes/frost_land_scatter_c20_08.glb` | 0.46 m |
| `stage1/meshes/arch_land_scatter_c20_21.glb` | 0.45 m |

The ones under about 1.5 m are tufts. They are soft and were intentionally given no box. The ones over 2.5 m need a collider before they are safe in normal play. Suggested box for a trunk: width 1.0 m, bottom at the placement y minus 0.15 m, height about 0.8 times the tree height (pines are about 7.5–12.5 m before the 0.82–1.22 scale). The current tree box, where one exists, is only 0.45 m wide and 2.6 m tall, centered 1.0 m above the placement. A sampled archipelago chunk (`arch_land_scatter_c18_16_col.glb`) has 5 boxes, median size 1.03 × 2.6 × 1.03 m, while the visual in that chunk spans 17.2 m vertically. The canopy is meant to be soft. The upper trunk is not covered. That is a Lucky collision pass, not an art move. These col files were not edited.

Grass, flowers, bushes, stones, driftwood, and crystals are class 0 and do not block. Routes were kept about 4 m clear when the scatter was placed, piers about 8 m. This commit does not move those points. One checked visual, `arch_land_scatter_c18_16.glb`, has max vertex motion 0 m versus `86e61c6e`.

## Counts

Instance counts are unchanged (Archipelago 2673, Saltglass 3231, Frost 4049, Ash 3754). High scatter triangles are 1.97 million across all four regions, lod1 444 thousand. The faceted-cone pass was 895 thousand high. The sphere pass was 2.73 million high. The original cones were 657 thousand high. Low tier still uses lod1. Cards are alpha-scissor, not blended, so they write depth. Not measured on a Galaxy S26.

What still shows: a card facing the camera is a flat clump, and a big oak is several of those clumps rather than one solid mass. Dead ash trees stay bare. Flower heads are painted, not photographed. Bark is the photograph on the old vertices, not a remodelled trunk.

## Patch

`tw_sea_scatter_test54.patch` sends `land_scatter` to `vc_scatter` and binds the four textures from `res://tidewrack/land4/textures/`. It applies to the tag by itself. `land_scatter` never takes the terrain arrays. Ash scatter is no longer forced through the basalt `StandardMaterial3D`.

## Check

Godot `4.7.stable.official.5b4e0cb0f`, `--rendering-method mobile`. Log: `Vulkan 1.4.318 - Forward Mobile` on lavapipe (software Vulkan, not a phone). No `SHADER ERROR`. Frames: Gullhaven ground and coast, Saltglass harbour, frost ground, ash ground. Audio still falls back to the dummy driver. That error is the missing sound card, not this shader.

Bare skerries that had no gentle ground off the route were left as rock. See `COVERAGE.md`.
