# Land4 terrain review — textured ground

Grass and snow roughness from the CC0 photos is smooth (grass median about 0.25). Used raw, and worse if the JPEG is read as sRGB, that is a broad specular blob, the polished-carpet look. The shader keeps the photo's variation but places grass and earth in 0.88–0.98, snow in 0.93–0.99, dry sand in 0.84–0.94, rock in 0.80–0.92. Wet sand is the only surface allowed down to about 0.58. Specular is capped. Normal strength is about half of the first textured pass, so the grain stays in the albedo.

The repeat is broken without a third tap. Grass, soil, sand and snow keep the metre-scale photo and mix in a rotated copy at about three times the size, weight about 0.12–0.34, with a mild bend in the UV. Rock, which was showing straight columns on cliffs, mixes more widely (about 0.18–0.74) and the bend follows the cliff, including height. The third rock tap is gone. A small-scale mask that drew diamonds is still not used.

What is still visible, and is not claimed fixed: distant frost faces still show the terrain mesh's large triangles. Rock still has the photograph's own grain, and a close frost cliff can still show a faint column. This is a GL Compatibility preview, not a phone capture. 15 samplers, 26 texture reads per fragment (was 29).

The ground is the subject. Scatter is still in the drop-in meshes and is not what these stills are for. `renders/terrain/*.jpg` is land3 on the left and land4 on the right, same camera, no scatter loaded. Godot 4.4.1 GL Compatibility on llvmpipe. That is a preview, not a Galaxy S26 Vulkan capture.

Shader compile on this 50-shot set: 0 errors. Median pixels changed by more than 12 levels: **0.48** (`renders/terrain/pixel_diff.json`).

## What the ground is now

`shaders/vc_terrain.gdshader` samples five CC0 surface sets (albedo, normal, roughness). The photographs and the license are in `textures/TEXTURES.md`. Tile size is in metres: grass and soil 2 m, sand 2.4 m, snow 3.2 m, rock 1.8 m on a triplanar blend so a cliff does not stretch. A second, larger copy of the same photo is mixed at 22% everywhere. An earlier spatial blend-mask made diamond cells at eye height, so that mask is gone.

Baked vertex colour still chooses the biome (grass, sand, snow, slope rock). The photo is what you see. Grass is darkened and pulled toward olive so it is not the land3 neon. Snow is darkened and its roughness is held at 0.82 or above so the flake texture is not a white specular disk. Ash flats are the cliff rock cooled and darkened, mixed with the soil set. That is basalt-coloured stone, not a separate vesicular basalt scan (Rock035 was reviewed and left out to stay at 15 samplers).

Placed props (vertex alpha under 0.5) stay vertex colour. `hero_cut` is unchanged. The random near-fade that dithered the foreground is gone. Only fragments closer than 0.2 m are discarded.

## Budgets

Terrain and scatter triangle counts are unchanged from the smooth pass:

| region | terrain before | terrain high | lod1 | scatter instances | scatter high |
|---|---:|---:|---:|---:|---:|
| A Archipelago | 251k | 386k | 154k (40%) | 2600 | 176k |
| B Saltglass | 475k | 794k | 318k (40%) | 2467 | 108k |
| frost | 572k | 942k | 377k (40%) | 3418 | 160k |
| ash | 242k | 378k | 151k (40%) | 2893 | 135k |

Texture set on disk is about 21 MB of 1024 JPEG (15 files). In the preview they are uploaded with mipmaps. The shader binds **2 `sampler2DArray`s** (albedo, and normal-with-roughness-in-B). Layers are grass, earth, sand, rock, snow. It still takes about 26 texture reads per fragment. Godot 4.7 Forward Mobile on lavapipe linked it. That is not a phone. `detail` only scales normal strength. It does not drop taps.

## Frames to look at

| shot | what is in the frame |
|---|---|
| `gullhaven_ground` | Eye height. Left is the streaked neon grass. Right is the grass photograph, soil in the wear, sand at the bottom of the frame. |
| `B_ground` | Saltgrass flat in front, sandstone hills behind. |
| `saltglass_ground` | On the island, about 86 m inland of the port, so the frame is the slope and not the quay wall. |
| `gullhaven_coast` | Sand photograph on the bank, rock on the offshore stacks. |
| `frost_ground` | Cold white and blue-grey snow on the slope. Grass and earth are not mixed in. |
| `frost_skyline` | Snow on the gentler shoulder, darker blue-grey rock where the face is actually steep. |
| `ash_skyline` | The cone against the sky, from offshore. The earlier black frame was the camera inside the mesh. This one is not. Most of the frame is sky and sea, so the pixel delta is only 0.07. Judge the mountain, not the percentage. |
| `ash_ground` | Dark soil and rock at eye height. |

## Frames that are weak

- `hot_spring_coast` looks down a dark face. The after frame is mostly black. Use `ash_coast` and `hot_spring_ground` instead.
- `hot_spring_skyline` is the bridge and the crystal props. The terrain change is small (pixel delta 0.08) because the props dominate.
- Distant cliff faces can still show a faint tile or the mesh facets. Mipmaps hide the fine photo; they do not hide a large triangle.
- Frost stays on the cold palette: snow on gentle faces, darker blue-grey rock on steep faces and at the waterline, no grass. The triangle edges are still the mesh. A trial that split long edges and slid only the new vertices rounded the crests and also opened dark cuts in the gullies once the slide was large enough to read offshore. Tile borders were held on the old edge and the cuts still appeared, so the trial was not kept. No terrain vertex in this commit moved. A gentle snow slope can still read as large facets.
- Grass, sand and rock meet over a wider, noisier band. Skerries use this same shader. The photographs and the matte roughness ranges are unchanged.
- The shader is 15 samplers and 26 texture reads. It has not been timed on a phone. Mainland collision is still the separate blocker; these glbs do not replace it.
- Specular on snow and on some grass slopes is still hot where the camera faces the sun. Roughness is floored on snow. It is not a measured phone exposure.

## Every island

All 13 playable islands have `*_ground`, `*_coast`, and `*_skyline` when the mesh rises past 14 m. The same shader runs on every terrain mesh in the four regions, including islets and skerries. A skerry marked `bare_rock` or `bare_unplaceable` in `COVERAGE.md` has no trees on purpose. It still gets the rock and shore materials.

Cameras were placed on the land3 surface (highest triangle at that xz), with the eye 1.6–1.7 m up on ground shots and at least 6 m up on slopes. Offshore skylines sit at 8 m above the sea when the sample is water, so they are not under the water plane and not inside the body. A few coast frames are still awkward. They are named above.

## Not changed

- Routes. No terrain vertex was moved. The facet trial was discarded before this commit.
- Collision glbs. Not replaced.
- Saltglass stair, harbour, lift, toll. Not redesigned.
- Mainland. `main.gd` is not on this branch. The gully term would change height for r ≳ 800 m and therefore collision. It was not applied. See `terrain_pass/mainland_land4/REMAINING_GULLY.md`. No mainland render.
- Knight rig, armor, `vertex_color_is_srgb`. Not touched.
- The game does not load this shader yet. `preview/render.gd` is what binds the textures. Copying the shader into the game without those 15 uniforms will not show this ground.
