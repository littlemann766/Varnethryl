# Land4 terrain review (this pass)

The ground is the subject. Scatter is still in the drop-in meshes, and it is not what these stills are for. `renders/terrain/*.jpg` is land3 on the left and land4 on the right, same camera, **no scatter loaded**. Godot 4.4 GL Compatibility on llvmpipe. Not a Galaxy S26 Vulkan capture.

## Completed this round

- Ground detail is isotropic and world-scaled. Fine grain is about 15 cm and mid grain about 0.8–1.5 m, two frequencies that are not integer multiples. Fine grain is turned off when one pixel covers more than about 10 cm of ground, which is what stretched the old 4:1 blade noise into foreground streaks. Gullhaven at eye height no longer shows those streaks. The material is still procedural value noise, not a finished texture: a faint lattice can show when the camera looks straight down (`B_ground`). Do not call the grass finished.
- The hard horizontal frost band was the shader. Rock weight was multiplied by `smoothstep` on world height, so a sheer face changed colour on a level line. That term is gone. Rock follows slope only.
- The white and blue slivers above the frost cliff are not the terrain shader. They are `stage4/meshes/frost_icicles.glb` (23k tris, icicle fringes). In the cliff window, most of those verts sit metres above the surface directly below them because they hang off the lip. They are left as that prop. Terrain proof shots do not load them. The prop file was not edited.
- Shader compile on this 50-shot set: 0 errors.
- Long coast and ridge edges were split earlier. Routes stay pinned. Collision files were not replaced.

## Not done

- A photographed or tiled albedo set. There is no ground texture in this pass, only the procedural shader. Down-view lattice and grazing softness are the limit of that.
- `ash_skyline` is inside the mesh (black). `saltglass_ground` clips the surface and is mostly water. `hot_spring_coast` and `beached_wreck_coast` barely change. Do not use those four as proof.
- Mainland mountains. `scripts/main.gd` is on `origin/main` and not on this branch. Its `_height_raw` still has the old needle term (`230 * rg * rg` and `45 * rg2 * rg2`). The gully line would change height for r ≳ 800 m and therefore collision. It was not applied. See `terrain_pass/mainland_land4/REMAINING_GULLY.md`.

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
