# Land4 ground textures

Photographic surfaces for the island terrain shader. The shader samples these in world metres (grass and soil 2 m, sand 2.4 m, snow 3.2 m, rock 1.8 m) and blends two rotated scales so a single repeat does not line up. Normals are OpenGL (+Y). Roughness is the CC0 roughness map, copied into RGB so the loader always has a red channel; the values are the published map.

No pixel grading was applied to the photographs. The shader darkens and desaturates them so the grass is not neon and the snow is not blown out.

## License

All five sets are **CC0 1.0** from [ambientCG](https://ambientcg.com). No purchase. Downloaded 2026-11-06 as the 1K JPG packs. Attribution is not required; the asset ids are recorded anyway.

| File prefix | ambientCG id | Use | Pack |
|---|---|---|---|
| `grass_` | [Grass004](https://ambientcg.com/view?id=Grass004) | meadow albedo, normal, roughness | Grass004_1K-JPG |
| `earth_` | [Ground048](https://ambientcg.com/view?id=Ground048) | forest soil mixed into grass and ash flats | Ground048_1K-JPG |
| `sand_` | [Ground054](https://ambientcg.com/view?id=Ground054) | shore and salt flats. Chosen over Ground080 because that one is rippled in one direction | Ground054_1K-JPG |
| `rock_` | [Rock023](https://ambientcg.com/view?id=Rock023) | cliff rock, triplanar. Ash multiplies this by a cool dark tint so the straits read as basalt | Rock023_1K-JPG |
| `snow_` | [Snow001](https://ambientcg.com/view?id=Snow001) | frost flats | Snow001_1K-JPG |

Repo `roads/textures/dirt_*` and `textures/realmed/fieldstone_*` were reviewed and not used. They are generated patterns (speckle dirt, polygonal stones), not a ground photograph.

## Not shipped, on purpose

[Rock035](https://ambientcg.com/view?id=Rock035) is a closer basalt photograph. A sixth set would be 18 samplers. The GL Compatibility shader stays at 15 (albedo, normal, roughness for the five sets above). Ash basalt is Rock023 with a dark blue-grey multiply, plus the soil set in the flats. It is stone detail, not a separate vesicular basalt scan.

## Where they are bound

`shaders/vc_terrain.gdshader` uniforms `grass_col/nrm/rgh`, `earth_*`, `sand_*`, `rock_*`, `snow_*`. `preview/render.gd` loads `../textures/<name>.jpg`, builds mipmaps, and sets those uniforms. The game does not load this shader yet. Nothing here is wired into `main.gd`.
