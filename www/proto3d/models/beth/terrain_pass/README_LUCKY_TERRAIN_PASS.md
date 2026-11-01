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

## Fix 5: sea edge (dark rectangle past the 1,600 m water grid)
**New:** `tidewrack_sea/stage1/meshes/ocean_far_ring.glb` and `stage1/shaders/ocean_far.gdshader`.
- The ring is 768 tris, 1 draw call: an annulus from r 700 m to 9 km at y −0.25, sitting under the grid's edge so it can't z-fight.
- The shader uses the region's deep colour, fading into `horizon` between `fade_start` 900 m and `fade_end` 6,500 m.
**Lucky (tw_sea.gd):**
1. In `_make_water()`, after `add_child(water)`:
   `var ring: Node3D = load(R + "stage1/meshes/ocean_far_ring.glb").instantiate(); water.add_child(ring)`.
   Give its MeshInstance3D a `ShaderMaterial` with `stage1/shaders/ocean_far.gdshader`, and turn shadows off. Being a child of `water`, it follows the camera with the existing snap.
2. Per region, set `deep` from the same deep colour you pass to the water.
3. Each frame (or in `_set_time`), set `horizon` to `m.env.fog_light_color`, or to the sky horizon if FogV2 isn't in yet.
4. Keep `cam.far` ≥ 7,000 m at sea, or lower `fade_end` to about 0.85 × cam.far, so the ring finishes fading before the far clip.

## Fix 6 - high cliff landings: built stone stairs instead of the generated board

vent, aurora_arch, hot_spring and obsidian_arch sit on 13-17 m sheer cliffs, so the generated board was a long 18-19 deg plank.
Beth built a stone landing for each one: a bridge over the cliff lip, a stepped 19 deg stair on piers with parapets, a 9 m timber
jetty at y 1.4 over water 8-16 m deep, and lanterns.
Files are in `tidewrack_sea/stage4/meshes/`: `ash_landing_{vent,hot_spring,obsidian_arch}` and `frost_landing_aurora_arch`, each with `.glb`, `_lod1` (45-47%) and `_col`.
They are named with the region prefix, so `tw_sea` auto-loads them from stage4/meshes. There is no code change.

**Lucky: copy the 12 glbs into `tidewrack/stage4/meshes/`, then merge these keys into `tidewrack/landings.json`.**
`shore` and `inland` stay as they are. The `"jetty"` key turns off the generated board.
```json
{
 "vent": {
  "jetty": "ash_landing_vent",
  "moor": [
   -485.73,
   0.0,
   1811.48
  ],
  "spawn": [
   -485.73,
   1.5,
   1817.98
  ],
  "pier_m": 61.9,
  "inland_target": [
   -485.73,
   17.22,
   1883.42
  ],
  "inland_route": [
   [
    -485.73,
    1.5,
    1817.98
   ],
   [
    -485.73,
    1.5,
    1825.48
   ],
   [
    -485.73,
    16.58,
    1869.42
   ],
   [
    -485.73,
    17.27,
    1883.42
   ]
  ]
 },
 "aurora_arch": {
  "jetty": "frost_landing_aurora_arch",
  "moor": [
   26.6,
   0.0,
   -2391.6
  ],
  "spawn": [
   29.09,
   1.5,
   -2397.6
  ],
  "pier_m": 62.3,
  "inland_target": [
   54.28,
   16.02,
   -2458.4
  ],
  "inland_route": [
   [
    29.09,
    1.5,
    -2397.6
   ],
   [
    31.96,
    1.5,
    -2404.53
   ],
   [
    49.11,
    16.88,
    -2445.93
   ],
   [
    54.28,
    16.07,
    -2458.4
   ]
  ]
 },
 "hot_spring": {
  "jetty": "ash_landing_hot_spring",
  "moor": [
   1075.54,
   0.0,
   2015.39
  ],
  "spawn": [
   1082.04,
   1.5,
   2015.39
  ],
  "pier_m": 66.7,
  "inland_target": [
   1155.29,
   14.52,
   2015.39
  ],
  "inland_route": [
   [
    1082.04,
    1.5,
    2015.39
   ],
   [
    1089.54,
    1.5,
    2015.39
   ],
   [
    1139.29,
    18.58,
    2015.39
   ],
   [
    1155.29,
    14.57,
    2015.39
   ]
  ]
 },
 "obsidian_arch": {
  "jetty": "ash_landing_obsidian_arch",
  "moor": [
   511.65,
   0.0,
   2656.65
  ],
  "spawn": [
   505.64,
   1.5,
   2659.14
  ],
  "pier_m": 57.2,
  "inland_target": [
   449.59,
   16.12,
   2682.36
  ],
  "inland_route": [
   [
    505.64,
    1.5,
    2659.14
   ],
   [
    498.71,
    1.5,
    2662.01
   ],
   [
    461.6,
    15.28,
    2677.38
   ],
   [
    449.59,
    16.17,
    2682.36
   ]
  ]
 }
}
```
Walk test: `stage4/tools/walk_stairs.gd`, using a capsule of r 0.35 / h 1.8, floor_max_angle 40, at 4 m/s.
All 8 legs (up and down) pass in 15-20 s each, so the walk is about 1 s longer than the board.
Rebuild: `python3 stage4/tools/build_landing_stairs.py landings.json stage4/meshes`. The cliff-top profiles are in `landing_rim_profiles.json`, from `tools/probe_land.gd`.

## Fix 7a - Frost Troll Ice Cave (the cheats "frost" zone)
Files are in `terrain_pass/ice_cave/`:
- `ice_cave.glb` (19.4k tris) and `ice_cave_lod1.glb` (18%)
- `ice_cave_col.glb` and `ice_cave_glow.glb` (emissive crystals)
- `ice_cave.json` (spawn, exit trigger, arena, troll spawns and lights)
- `ice_cave_zone.gd` (class IceCaveZone: builds the cave, collision, lights, its own environment and the PLACEMENT_frost_realm floor dressing)

The cave is built in the legacy frost-realm local frame and placed at CAVE_ORIGIN (2250, -600, 0), well below the sea and off the mainland.
It is a 12 m entrance tunnel that winds into a 160 x 110 m troll arena.

**Lucky:**
1. Copy `ice_cave/*.glb` and `ice_cave.json` to `res://assets/ice_cave/`.
2. Copy `frost/*.glb` to `res://assets/frost/`.
3. Copy `PLACEMENT_frost_realm.json` to `res://assets/data/`.
4. Copy `ice_cave_zone.gd` to `res://scripts/`.
5. In `main.gd` `cheat_tp_zone`, add:
```gdscript
		"frost":
			if ice_cave == null: ice_cave = await IceCaveZone.new().build(self)
			_teleport(ice_cave.spawn_point(), 0.0)   # the cave has its own WorldEnvironment; hide/disable the overworld env + sky while inside
			party.director.spawn("frosttroll_a", ice_cave.troll_spawn("frosttroll_a"), hero); return true
```
   with `var ice_cave: IceCaveZone` declared at the top of main.gd.

**Snag:** enemy ground inside the cave must come from `ice_cave.floor_y(local x, z)` (a raycast), not `height()`. Branch on `ice_cave and pos.y < -300` wherever enemies are grounded (next to the VOLC branch near line 1239).
The exit trigger is at `ice_cave.json` `exit_trigger`, about 4 m inside the mouth. Teleport back to the village there.

Test: `ice_cave/tools/cave_test.gd`, using a capsule of r 0.35 / h 1.8 at 5 m/s from the spawn to the arena and both troll spawns.
It passes in both directions in 53 s each. 37 of the 80 frost_realm props land on the cave floor. The other 43 fall outside the footprint and are skipped (no floor hit).

## Fix 7b - Beth's unwired placement sets (frost town, volcano, hobcamps; port skipped)
`terrain_pass/placements/beth_placements.gd` (class BethPlacements) loads `PLACEMENT_frost_town.json`, `PLACEMENT_volcano.json` and `PLACEMENT_hobcamps.json`.
It applies the same filters as `_dressing()`: gate path, `_on_way`, `_in_building`, small blockers, water below y 0.6, and no hobcamp inside the walls. It also merges each file into a MultiMesh with `m._multimesh`.

The volcano set predates the Titan (r 148), so all 150 of those items sat under it. The loader pushes each one out radially into a 152-212 m basalt, scree and ash band around the Titan, which also covers Fix 8's "hard cone/grass edge".

The test on Lucky's terrain, roads, walls and buildings (`placements/plc_test.gd`) kept 379 items and dropped 37 on roads and 12 in water.

**Lucky:**
1. Copy `hobcamp/`, `volcano/` (the props), `frost/`, `trees/tree_pine_snow.glb`, `clusters/cluster_volcano.glb` and `props/{barrel,crate}.glb` into `res://assets/`. Keep the same subpaths, and run `--import`.
2. Copy the 3 PLACEMENT jsons to `res://assets/data/`.
3. Copy the script to `res://scripts/`.
4. In `_ready()`, directly after `_dressing()`, add:
```gdscript
	if OS.get_environment("VARN_LITE") == "": BethPlacements.apply(self)   # terrain pass fix 7b
```
`PLACEMENT_port.json` is NOT wired. It is local to the old walled-harbour PORT_CENTER, and its 48 pier posts and 2 ships duplicate what HarborDistrict and `_ships()` already build. Leave it.

## Fix 8a - lod1 at or under 45%
These lod1 files were re-decimated from their base with gltfpack 1.3 (`-si 0.44 -noq -kn -km`; buildings use `-si 0.4 -sa -km`). The originals are kept as `*_lod1_v1_backup.glb`.
- Terrain tiles (coast_tile_x1z3/x1z1, frost_tile_x0z1/x1z0) are now 43%.
- Buildings (windmill, stables, barn, farmhouse, lighthouse variants) are 31-39%.
- tripo volcano_game is 36%.
- windmill_card is 47%.

- `tidewrack_sea/stage2/meshes/coast_tile_x1z3`_lod1.glb
- `tidewrack_sea/stage2/meshes/coast_tile_x1z1`_lod1.glb
- `tidewrack_sea/stage4/meshes/frost_tile_x0z1`_lod1.glb
- `tidewrack_sea/stage4/meshes/frost_tile_x1z0`_lod1.glb
- `hi/buildings/bld_windmill`_lod1.glb
- `hi/buildings_card2/bld_stables_card2`_lod1.glb
- `hi/buildings_card2/bld_barn_card2`_lod1.glb
- `hi/buildings_card2/bld_farmhouse_card2`_lod1.glb
- `hi/buildings_card2/bld_lighthouse_card2`_lod1.glb
- `hi/buildings/bld_lighthouse_card`_lod1.glb
- `hi/buildings/bld_lighthouse`_lod1.glb
- `hi/buildings/bld_windmill_card`_lod1.glb
- `tripo/volcano_game`_lod1.glb
**Lucky:** copy the 4 tile lod1s over `tidewrack/stage2|stage4/meshes/` and `hi/buildings/bld_windmill_lod1.glb` over your windmill lod1, then re-import.

## Fix 8b - frost strait blown out and blocky, ash strait flat grey
`tidewrack_sea/stage4/tools/regrade_frost_ash.py` regraded the vertex colours of all 28 `frost_tile_*` and `ash_tile_*` files (base and lod1). Geometry and collision are unchanged.
- Frost: snow is capped at 0.80, steep faces shade to glacier blue (0.42, 0.56, 0.70), with a soft noise breakup.
- Ash: the flats are warm ash sand, the slopes dark basalt, with sparse ember-red patches on low steep rock.

The originals are in `stage4/meshes_v1_backup/`. All `*_v1_backup` files were moved out of `meshes/` because `tw_sea` auto-loads every `frost_`/`ash_`/`coast_` glb in that folder.
**Lucky:** copy the 28 tile glbs over yours. Suggested (your code): in the frost region set the ambient to (0.55, 0.62, 0.75) and use the FogV2 values from Fix 3.
