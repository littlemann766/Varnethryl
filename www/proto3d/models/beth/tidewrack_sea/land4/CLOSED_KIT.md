# Closed foliage kits — delta on top of `6996eb80`

`6996eb80` and `05cd21c7` are unchanged. Review `git diff 6996eb80` on its own.

## What changed

Some island meshes still held a copied foliage solid: 80 triangles, every edge shared by two faces, no vertex shared with the ground, mean color green (green above red, and green at least blue). Those became bush cards, or a needle crown when the piece is taller than it is wide. The cards go in the existing `*_canopy` files. A gap under the solid of at most 0.45 m is closed. Kept island vertices are an exact subsequence of the `6996eb80` position, normal, and color bytes. 11 files, 0 mismatches.

296 pieces. 283 bushes, 13 needle crowns. New triangles: 22,392 high and 6,696 lod. No new texture. No collider. The `_canopy` material rule from `6996eb80` already covers the new `coast_canopy_saltglass` and `coast_canopy_beached_wreck` files. No further `tw_sea` patch.

## Left alone

- `arch_islands.glb`: the apex at about (-12, 8.6, 288) is the tip of the terrain. Its ring connects down the slope. Removing it would open the ground.
- `ash_isl_ember_wreck.glb`: a closed 42-vertex spike, color about (0.44, 0.31, 0.05). It is an ember piece, not a green kit.
- Frost lumps whose blue is heavier than their green. Those read as ice, not shrubs.
- 17 green pieces whose tops sit under the surrounding surface. They stay buried rather than grow out of a cliff.
- One beached-wreck lod piece has fewer than 20 faces, so the low tier can still show that one small solid.

The 14 scatter visuals with no collider are unchanged. Ground meshes and the terrain shader are unchanged.
