# Land4 terrain review (this pass)

The ground is the subject. Scatter is still in the drop-in meshes, and it is not what these stills are for. `renders/terrain/*.jpg` is land3 on the left and land4 on the right, same camera, **no scatter loaded**. Godot 4.4 GL Compatibility on llvmpipe. Not a Galaxy S26 Vulkan capture.

## What was wrong, and what changed

- A terrain shader edit used `dirt` before it was declared. Godot dropped the shader and the ground drew as the white default. That is why Gullhaven looked like snow. It compiles now (`SHADER ERROR` count 0 on the 50-shot set).
- Near grass is two crossed high-frequency grains. The earlier domain-warp version drew closed contour lines; that is gone.
- Snow no longer self-lights into a flat sheet. Steep faces take a darker blue-grey rock, so a frost cliff has a cap and a face. Same camera, land3 is the blown-white cliff.
- Slopes steeper than about 25° pick up region rock. A sea cliff does too, down to about 8 m, so the lip is stone rather than grass.
- The wet line stays within about a metre of the water. It does not climb the hill.
- Long coastal faces and long ridge edges were split once more (`tools/refine_coast.py`). Walkable verts and the route/pier pin do not move. Extra motion on free verts is clamped to 0.7 m.

## Frames that show the terrain

Use these. Median pixels changed across the 50 shots is about 25%.

| shot | what you should see |
|---|---|
| `gullhaven_ground` | green Archipelago ground at eye height, hills behind, 64% of pixels changed |
| `A_ground`, `coil_isle_ground`, `lantern_rock_ground` | same, on other Archipelago ground |
| `frost_skyline` | ice cliff: pale cap, blue-grey face, 63% changed |
| `A_coast` | rock lip into the water, grass on the bank |
| `ash_ground` | dark basalt slope, ember cracks, the hill line |
| `B_skyline`, `saltglass_skyline` | Saltglass relief where the camera cleared the cliff |

## Frames that do not prove anything

- `ash_skyline` is inside the rock. The picture is black. Do not use it.
- `saltglass_ground` sits in the surface, so the near-fade dithers and the frame is mostly water. Do not use it.
- `hot_spring_coast` and `beached_wreck_coast` barely change (0–2%). The camera is on ground the pin held still.

## Every island

Playable islands each have a `*_ground` and a `*_coast` frame, and a `*_skyline` where the mesh rises past 14 m. Smaller land components, including skerries left as rock with no trees, are listed in `COVERAGE.md` and `grove_notes.json`. A skerry marked `bare_rock` or `bare_unplaceable` is bare on purpose: shore and rock material only, no trees.

## Mainland

Not done, and not claimed done. `main.gd` is not in this checkout. Fix 2 already rounded the crest and cut the 45 m spikes to 14 m (`terrain_pass/mainland/fix02_main_gd.patch`). The remaining land2 line, an erosion gully only for r ≳ 800 m, is written in `terrain_pass/mainland_land4/REMAINING_GULLY.md` and was **not** applied. Applying it moves mountain collision and needs a normal rebake plus a scatter reseat in the game. There is no in-engine mainland render in this pass.

## Paths

Route vertices were measured at 0 m of motion on the first smooth. This coast split only moves verts that are not on the route pin, and only up to 0.7 m. Collision glbs were not replaced. The Saltglass stair, harbour and toll were not redesigned.
