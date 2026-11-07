# Flower depth and low-tier crowns — delta on top of `a3e69eba`

`a3e69eba` is unchanged. Review this commit on its own. Do not merge the pull request as a whole.

## What was wrong

Each flower was one card, so the head was a flat disk. The pink sprig read as a cutout. On the low graphics tier the pine crowns were separate little clumps with bare trunk between them. That tier is not a distance swap. `tw_sea.gd` loads `_lod1` whenever `high()` is false.

## What changed

Flower cards that were already in the scatter meshes are crossed faces of the same size, pitched so the head has thickness. The three flower cells are still a five-petal cup, a six-petal daisy, and a sprig of three blooms. The vein stroke is gone. Pine, leaf, bush, and grass pixels are unchanged. 2,949 heads.

Low-tier leaf cards in `*land_scatter*_lod1.glb` and `*canopy*_lod1.glb` are replaced inside the old crown box. A pine is six overlapping shells of the dense leaf photo, tapered, so the crown is one shape on the trunk. The sparse needle fan is what made the whiskers, so the low tier does not use it. High tree cards are not rewritten. 5,612 crowns.

Kept vertices match the `a3e69eba` position, normal, and color bytes. Trunks, ground, colliders, and the 14 colliderless visuals are untouched. No new solid. No `tw_sea` change. Still four samplers.

High scatter triangles 3,399,709 (was 3,393,785). The extra faces are the crossed flowers. Lod scatter 296,986 (was 608,530). Lod canopy 7,932 (was 33,756).

## Left alone

- High pine, broadleaf, and bush cards. The approved high trees stay.
- Ash chunks that had no flower cards.
- Terrain `86e61c6e`, gameplay, and armor.

Up close on the low tier the pine shells can still be told apart. At 32 m they read as one crown. Godot 4.7 Forward Mobile, llvmpipe. Not a phone.
