# Land pass 4 (Beth) — supersedes land3 for review. Nothing to main/live. None of Lucky's files edited.

Terrain evidence (ground, slopes, coasts, silhouettes, no scatter in the shot) is `TERRAIN.md` and `renders/terrain/`. Read that before the scatter notes. The mainland mountain gully is **not** applied.

Same drop-in shape as land3 (`../land3/README_LUCKY_LAND3.md`). Copy `land4/stageN/meshes/*` over the land3 (or game) terrain visuals of the same names. Do **not** replace `*_col.glb`, `*_terrain_col.glb`, stage5 harbour/path meshes, or anything under equipment/. The Saltglass stair, cove harbour, lift removal and toll are untouched.

Do **not** copy `shaders/vc_terrain.gdshader` over the game shader until the 15 texture uniforms are set. The review shader samples CC0 albedo, normal and roughness (`textures/TEXTURES.md`). `preview/render.gd` `bind_terrain()` is the binding. Without those textures the ground will not match these stills.

`_mat_for` stays the land3 snippet (`lift 0.1, ambient 1.25, spec 0.075` on ash). `detail` still scales the near grass for Low.

COLOR_0 is still uint8 normalized, the same encoding as land1–3. Leave `vertex_color_is_srgb` as the game already has it for these meshes. Knight rig `24fe4bc` was not touched.

## What changed, on every region (Archipelago, Saltglass, Frost, Ash) and the small landmasses

Priority was the silhouette and the waterline, then the ground and the scatter.

- **Silhouette.** Steep free faces are midpoint-split (waterline faces included) and Taubin-smoothed. The old ridged/strata displacement is what read as sawtooth crests and corrugated frost. Walkable ground, tile seams, route/POI/pier/bridge corridors, the Saltglass harbour footprint, glow decals, overhangs (arches) and edges longer than 18 m (pillars, rails) are pinned. Measured route-vertex motion is **0 m on every terrain mesh**. Peak heights stay within about 1 m (see `terrain_stats.json`).
- **Shore.** The shader's wet line follows a wandering height instead of a bathtub ring. A short visual apron is added only where a mesh boundary is actually the sea (several playable islets). Tile boundaries are the underwater cut, so they are not skirted; their waterline faces are the ones that got split and rounded.
- **Ground.** The review shader samples grass, soil, sand, rock and snow photographs (albedo, normal, roughness) at a fixed world scale, with slope rock on a triplanar map and a soft shore. Vertex colour still picks the biome. See `TERRAIN.md` and `textures/TEXTURES.md`. The old value-noise grass is what the left half of `renders/terrain/gullhaven_ground.jpg` shows.
- **Scatter.** More than one tree, bush and rock shape per region, plus shore wrack. Every one of the 13 playable islands has scatter (Saltwatch, the smallest, has 16). Islets down to a few hundred square metres are in `COVERAGE.md`. A few skerries have 0 instances: no gentle point cleared the keep-out. They are listed, not skipped. Ash spires and boulder clusters are spaced landmarks again (110), not a carpet.

## Budgets (High, whole region — the game streams tiles and 256 m chunks)

Terrain tris, land3 → land4 High, lod1 is 40% of the new High (the old lod1 was the sawtooth mesh, so it was not reused):

| region | terrain before | terrain high | lod1 | scatter instances | scatter high | scatter lod1 |
|---|---:|---:|---:|---:|---:|---:|
| A Archipelago | 251k | 386k | 154k (40%) | 2600 | 176k | 25% |
| B Saltglass coast | 475k | 794k | 318k (40%) | 2467 | 108k | 35% |
| frost | 572k | 942k | 377k (40%) | 3418 | 160k | 39% |
| ash | 242k | 378k | 151k (40%) | 2893 | 135k | 39% |

Scatter colliders are trunk/boulder boxes in `*_land_scatter_*_col.glb`, kept off routes. Terrain collision files are not in this folder.

## Mainland

The previously scoped mainland polish is already the land3 drop-ins: `terrain_pass/mainland_land3/ground5.gdshader`, `grass_land3.gdshader`, `far_grass.gdshader`, `terrain_flowers.gdshader`, plus the existing `fix02` / `fix09` patches. This pass does not edit `main.gd` and does not rebuild the mainland heightfield.

## Proof

`renders/*.jpg` is every still, same camera, land3 on the left and land4 on the right. `pixel_diff.json` is the per-shot fraction of pixels that moved by more than 12 levels (median about 28%). Stills were rendered in Godot 4.4 **GL Compatibility on llvmpipe**. That is a preview, not a Galaxy S26 Vulkan capture. Expect the phone to sit a little darker, which is the side land3 already aimed for.

Close-ups to look at before any integration: `gullhaven_close`, `lantern_rock_close`, `saltwatch_keep_close`, `coil_isle_close`, `saltglass_silhouette` (the fences and route are still there), `beached_wreck_close`, `frost_mountain` (the dashed frost corrugation is the clearest before/after), `frost_shore`, `frostreach_close`, `frozen_wreck_close`, `aurora_arch_close`, `ash_mountain`, `vent_close`, `ember_wreck_close`, `hot_spring_close`, `obsidian_arch_close`, and the `islet_*` frames.

## Honest limits

- Ash and some Saltglass slopes still show broad ridges. The smooth kills the short sawtooth (y-deviation in `terrain_stats.json`) and leaves the big landform. A wider smooth would move the routes.
- A few wide cameras sit on a wooded slope, so near trees cross the sky. The land3 frame of the same camera does it too. Judge seating on the close shots.
- `saltglass_close` and `frostreach_close` are mostly sea; the island is a thin band, so the pixel delta is small. Use the silhouette or ground shots for those.
- `A_islet_-49_326` (~0.5 ha) and thirteen smaller skerries have no scatter. See `COVERAGE.md`.
- Not tested inside a full game build, and not on the phone.
