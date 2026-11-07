# Scatter bark and foliage

Photographic surfaces for the scatter shader only. The terrain shader is unchanged and does not sample these.

## License

CC0 1.0 from [ambientCG](https://ambientcg.com). No purchase. Downloaded 2026-11-07.

| File | ambientCG id | Use |
|---|---|---|
| `bark_albedo.jpg`, `bark_normal.jpg` | [Bark012](https://ambientcg.com/view?id=Bark012) 1K JPG, OpenGL normal | Trunks and limbs. Cylindrical UV on the existing vertices. |
| `foliage_atlas.png` needles and grass | [Foliage001](https://ambientcg.com/view?id=Foliage001) color + opacity | Needle fans and grass tufts, cut out and packed into the atlas. |
| `foliage_atlas.png` broad leaves and bushes | [LeafSet001](https://ambientcg.com/view?id=LeafSet001) color + opacity | Leaf clumps. |
| `rock_albedo.jpg` | [Rock023](https://ambientcg.com/view?id=Rock023) | Already in this folder for the terrain. Scatter rocks sample it triplanar. |

The three flower heads in the atlas (yellow, white, pink) are painted for this project. They are not an ambientCG photograph.

The atlas is 4 by 2 cells of 512. Each cell is bled on its own so a mip does not pull a flower into a leaf. Cards use alpha scissor.
