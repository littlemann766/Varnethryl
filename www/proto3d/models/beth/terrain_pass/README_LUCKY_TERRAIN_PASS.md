# Terrain & map pass: fixes (Beth). Notes for Lucky
These follow `/workspace/shots/terrain_pass/FINDINGS.md`. I did not edit any of your files. Each section lists exactly what to change on your side.

## Fix 1: duplicate buildings (town fillers)
**New:** 22 filler variants in `hi/buildings_card2/`: `bld_<id>_card2{,_lod1,_lod2,_col}.glb`. Each one has an entry in `index.json` with `variant_of` and `collision`, and `index_v1_backup.json` is the old index.
- Every variant keeps the footprint, door position and front axis of the kit model it replaces, so `door` / `path_end` / `rect` / `interior` in fillers.json stay valid. `_col` is a copy of the base model's collider.
- Townhouses: `townhouse_a`–`townhouse_h`. They vary in roof (slate / oak shingle / stone tile), walls (plaster / weatherboard / ashlar / fieldstone), with or without timber framing, storeys and pitch.
- Trades: `tailor`, `weaver`, `butcher`, `candlemaker`, `farrier`, `cooper` and `carpenter` each have a hanging iron-bracket trade sign (scissors, spindle, cleaver, candle, horseshoe, barrel, saw). The butcher has an awning with hams.
- Plain shop-footprint dwellings: `merchant_house(_b)`, `guild_house(_b)`, `stone_hall(_b)`, plus `chapel` (bell turret and gable cross; at most 2 in town).
- lod1 is 28–43 % of high for every variant (≤ 50 %).
**New placement:** `town/fillers_v2.json` keeps the same 212 entries (same ids, pos, yaw, door, path_end, rect and interior). Only `model` changed, `label` changed for the trades, and `model_v1` records the old model. `town/fillers_v1_lucky.json` is the backup of yours.
- The smithy, bakery and apothecary landmarks are no longer used as fillers, so there is one of each shop per town.
- No two identical models stand within 40 m; the closest pair is 48 m (it was 82 pairs under 40 m before).
- The four kit houses (house1–4) still appear, but at least 52 m apart.
**Lucky:**
1. Copy `hi/buildings_card2/bld_{townhouse_*,tailor,weaver,butcher,candlemaker,farrier,cooper,carpenter,chapel,merchant_house*,guild_house*,stone_hall*}_card2*.glb` into `assets/card2/`.
2. Merge the new `index.json` entries.
3. Replace `assets/town/fillers.json` with `town/fillers_v2.json`.
4. In `town_fillers.gd`, `KIT` is only used by `solve()`. The runtime build already reads `f.model`, so nothing else is needed, as long as `_card2_path(model, suffix)` resolves the new ids from index.json. If `KIT` is used to validate models, add the new ids to it.
5. Collision: `_card2_path(f.model, "_col")` finds `bld_<variant>_card2_col.glb` (copies are shipped).

## Fix 2: mountains (faceting + snow)
**New:** `terrain_pass/mainland/ground3.gdshader` replaces `terrain_fix2/ground/ground2.gdshader`; `ground2_v1_backup.gdshader` is the backup. Every uniform is the same, so it binds as-is.
- The regular `sin(wp.y)` strata stripes are replaced by low-contrast, noise-warped layers.
- The snow line is wider and warped at two scales, sits only on gentle ground (steep faces show rock), has a patchy edge, and is shaded by the normal, so it no longer reads as flat white paint.
- The rock band starts higher and blends more softly.
**Height change** (`fix02_main_gd.patch`, which also swaps the shader path): only inside `_height_raw`'s mountain term (`mr > 0`, r ≳ 800 m). The ridged crest `rg*rg` becomes a smooth knee, and the fine `rg2` spike term drops from 45 to 14 m. That removes the 10 m-grid needle peaks. Gameplay space (r < 800), the volcano pad and the farm are unchanged.
**New baked normals:** `terrain_n_v2.png` is baked from the patched `height()` (same format: RG = n.xz·0.5+0.5, 2 m/texel, ±1024 m, σ = 2 texel blur); `terrain_n_v1_backup.png` is the backup.
**Lucky:**
1. Copy `ground3.gdshader` to `terrain_fix2/ground/` and point `_terrain()` at it.
2. Apply the `_height_raw` hunk from `fix02_main_gd.patch`.
3. Replace `terrain_fix2/data/terrain_n.png` with `terrain_n_v2.png`.
The bake tool is `terrain_pass/mainland/tools/bake_n.gd`; its args are `script out.png`, then blur with σ 2.

## Fix 3: soft layered fog
**New:** `terrain_pass/mainland/fog_v2.gd` (`class_name FogV2`) sets up a thin distance haze (density 0.00042 instead of 0.0011, aerial perspective 0.78, so the distance fades into the sky colour) plus a low valley mist from height fog (fog_height 2 m, falloff 0.012). The fog colour is the horizon pulled 35 % toward cool blue-grey. The far ring keeps its silhouette, and the town is no longer a milky sheet.
**Lucky (main.gd):**
1. In `_env()`, replace the `env.fog_*` line with `FogV2.apply(env, Color(0.75, 0.82, 0.9))`.
2. At the end of `_set_time()`, replace `env.fog_light_color = sky_mat.sky_horizon_color` with `FogV2.apply(env, sky_mat.sky_horizon_color, nf)`.
3. In `apply_quality()`, replace the line `env.fog_enabled = true; env.fog_density = 0.0011` with `FogV2.apply(env, sky_mat.sky_horizon_color)`.
4. In the altitude fog code (lines ~2846–2853), take the base from `FogV2.DENSITY` and also thin `env.fog_height_density = FogV2.MIST_DENSITY * lerpf(1.0, 0.2, k)`.
Keep volumetric fog off on Mobile; this is plain exponential fog, so it costs nothing.

## Fix 4: floating and buried wildflowers and rocks
The cause: placement used the smooth `height()`, but the ground is drawn as the 10 m triangle grid, which is up to about 1.9 m off on hills.
**New:**
- `mainland/flowers_bake_v2.bin`: same format as `terrain_flowers/flowers_bake.bin`. Every one of the 230,540 instances is re-seated on the drawn triangle surface of the patched terrain, keeping its own baked offset. Floating >0.35 m went from 6,932 to 0, and buried >0.6 m from 3,093 to 0. (The audit's AABB metric counted 10.7k/4.4k; this is the per-instance origin metric.)
- Scatter (`terrain_fix2/scatter/terrain_scatter.scn`): `reseat.gd` checked all 12,418 instances, and every one is already within 0.35 m of the drawn ground by the origin metric. The audit's large numbers came from rock AABBs on slopes. **No change is needed**, so I removed the re-saved 59 MB scene from the repo again.
- Backups: `*_v1_backup.*`. Tool: `tools/reseat.gd` (args `old_main.gd new_main.gd outdir`). Re-run it whenever `height()` or the grid changes.
**Lucky:**
1. Copy `flowers_bake_v2.bin` → `terrain_flowers/flowers_bake.bin`.
3. For anything else placed with `height()` (trees, dressing), consider a `surface_y(x, z)` helper that returns the grid-triangle height. The `surf()` code in `reseat.gd` is the exact formula.
