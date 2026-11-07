# Grass and flowers — delta on top of `c883b483`

`c883b483`, `6996eb80`, `05cd21c7`, and `86e61c6e` are unchanged. Review this commit on its own.

## What was wrong

Every flower was the same seven-petal head, painted three times and stacked. Grass was six copies of one blade card. The low tier used the same heads and fewer blades, so a tuft thinned when the graphics tier dropped.

Tidewrack does not swap foliage by distance. `tw_sea.gd` `_path` loads `_lod1` when `high()` is false (`tier < 2`). A region starts loading inside 150 m of its rectangle. Low and Medium show lod1 for the whole region. High and Ultra show the high mesh up close and at 32 m.

## What changed

Existing grass and flower cards in `*land_scatter*.glb` only. Trees, trunks, island ground, canopy files, and colliders are untouched. Kept vertices match the `c883b483` position, normal, and color bytes.

A tuft keeps its footprint. High uses five blade cards of mixed height. Lod uses three, and the tallest still reaches the old top so the clump does not vanish. A flower is one head on a short stem, seated in that tuft, not three stacked copies.

The three flower cells in `foliage_atlas.png` are different shapes now: a five-petal cup, a six-petal daisy, and a sprig of three small blooms. Pine, leaf, bush, and grass cells are the same pixels. Which shape a plant uses comes from its position, in half-metre steps, so a low-tier card that shifted a few centimetres keeps the same head. The old vertex color still tints it, so frost stays pale and the coast stays green.

7,278 tufts across 279 scatter files. High scatter triangles 3,393,785 (was 3,434,273). Lod 608,530 (was 610,850). No new collider. No `tw_sea` change.

## Left alone

- Crown lod. At 32 m the low tier still breaks a pine into separate clumps. That is the lod mesh from `05cd21c7`. Rebuilding it would restyle the trees. This commit does not.
- Ash scatter. Those chunks had no grass or flower cards in the foliage atlas, so they were not rewritten.
- The 14 scatter visuals with no collider. Ground meshes and the terrain shader.

Godot 4.7 Forward Mobile, llvmpipe. Not a phone.
