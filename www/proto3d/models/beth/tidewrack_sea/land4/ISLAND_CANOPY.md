# Island cone canopies — delta on top of `05cd21c7`

`05cd21c7` is unchanged. This commit only lifts closed decorative pine tiers out of island meshes and puts needle crowns in new files. Do not merge the whole pull request. Review this commit on its own, on a tree that already has terrain `86e61c6e` and foliage `05cd21c7`.

## What was separated

A component was removed only when it was a closed tier: 6 to 16 vertices, taller than 1 m, green or snow-dusted, and one level ring around an apex. Kept vertices are an exact subsequence of the original position, normal, and color bytes. 14 files, 0 mismatches.

| Island | Tiers removed | Trees | Canopy tris high / lod |
|---|---:|---:|---:|
| `arch_isl_gullhaven` | 81 | 27 | 34884 / 4860 |
| `arch_isl_coil_isle` | 81 | 27 | 34992 / 4860 |
| `arch_isl_lantern_rock` | 77 | 26 | 33372 / 4680 |
| `arch_isl_saltwatch_keep` | 9 | 3 | 3888 / 540 |
| `frost_isl_frostreach` | 66 | 37 | 33480 / 5040 |
| `frost_isl_frozen_wreck` | 60 | 34 | 33156 / 4950 |
| `frost_isl_aurora_arch` | 40 high, 24 lod | 23 / 18 | 20412 / 2130 |

High canopy triangles: 194,184. lod1: 27,060. Not all of that is on screen. The crowns reuse `foliage_atlas.png` (ambientCG Foliage001 needles). No new texture. No collider file. The 14 scatter visuals that have no collider are unchanged, and these canopies must not gain a box: a box around a crown would block a route.

Trunks that were separate vertices were not in these components, so they stay. Ground faces stay.

## Left alone

These had an apex-like vertex whose component is not a closed tier. They were not edited.

- `stage1/meshes/arch_islands.glb`: one apex sits in a component of 81,893 vertices (height 78 m). That is the terrain mesh. Cutting it would carve the ground.
- `stage1/meshes/arch_isl_lantern_rock.glb`: one component of 41 vertices, not a closed tier.
- `stage4/meshes/ash_isl_ember_wreck.glb`: one component of 42 vertices, height 1.54 m, not a closed tier.

Saltglass, the other ash isles, and `arch_islands_lod1.glb` had no such tier.

## Copy

For each row above, copy the high and `_lod1` island glb (cones removed) and the matching `*_canopy*.glb`. The canopy name replaces `_isl_` with `_canopy_`, so `arch_isl_gullhaven.glb` pairs with `arch_canopy_gullhaven.glb`. `_files` already skips `_lod1` on the high tier and swaps to it when the lod file exists. The canopy name does not contain `_isl_`, so `_land4_terrain` does not claim it.

`tw_sea_canopy_test54.patch` applies after `tw_sea_scatter_test54.patch`. It sends any mesh whose name contains `_canopy` to the existing `_scatter_mat()`. Same four textures. Do not point the terrain shader at these files.

Hashes of the kept vertices are in `island_cone_report.json`.
