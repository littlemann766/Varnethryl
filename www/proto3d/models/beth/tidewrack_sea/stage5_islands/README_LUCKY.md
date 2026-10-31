# Tidewrack Sea - Stage 5: island interiors behind the 13 landings (Lucky test 35)

Each landing in `landings_v1.json` (copied from /workspace/shots/t34/dock) gets a real interior inland of its pier head:
shaped hills and outcrops, region ground (temperate A, saltglass B, frost, ash), paths from the pier head to every point of
interest, scatter (rocks + pines/bushes, salt crystals, ice spires/snow pines, basalt columns/sulphur), and 2-4 POIs.

## How to drop it in (no code change needed)
`tw_sea.gd` already loads every `{pre}*.glb` in a region's mesh dir. Copy the files of each island into that region dir:
- `{pre}isl_<id>.glb` / `_lod1.glb` - terrain + POIs + scatter, one vertex-colour surface (gets `vc_lit.tres`; ash ones get the basalt mat).
- `{pre}isl_<id>_glow.glb` - lanterns, lava, crystals, spring water (name ends `_glow` -> glow_vc, no shadow). No lod1 (tiny).
- `{pre}isl_<id>_col.glb` - walk collider (name ends `_col` -> trimesh StaticBody, never drawn): simplified patch + solid POI parts
  (tower/wall blocks, shrine pillars, hull, tent, chest, big rocks, tree trunks, bridge decks + rails).
POI positions, names, radii and suggested OmniLights per island are in `stage5_manifest.json` (`islands.<id>.pois`), plus the
bridge endpoints and the camera spots used for the renders.

## What it does to the existing art (nothing is edited)
- The patch is sampled from the stage 1/2/4 terrain and sits **+0.08 m above it**; its rim tucks 0.25 m under the original
  ground so there is no visible seam. Hills only ever ADD height (paths are filled benches, never cut).
- **Docks/landings untouched:** no patch within 6 m of the pier head, and the ground is exactly the original height out to
  14 m (blending in by 22 m), so `pier_head()` / `pier_foot()`, the boards Lucky places and the 20 m inland check still hold.
- **Existing props are cut out:** every vertex of Gullhaven port, Saltglass Landing, Saltwatch Keep, Lantern Rock, Coil arena,
  harbours, wrecks, arches, crystals, vents... standing on that land makes a hole in the patch (+ a 30 m falloff of the hills).
- **Original sea cliffs keep their own look:** steep original faces are not covered unless the hills raise them.
- Existing `_col` colliders stay; the new `_col` sits on top, so the hero walks on the new surface.

## Walkability
- Paths are routed with a direction-aware grade cost (switchbacks), then filled into a level bench (<=2.5 m fill).
- POIs are only placed on ground reachable from the pier head with steps <= 35 deg (hero floor_max_angle is 50).
- Max path grade per island is in the table (most p95 10-25 deg).

## Islet landings: causeways
Frostreach, Beached Wreck and Ember Wreck landings sit on small islets/shelves separated from the main land, so the builder
adds a causeway (ice / plank / basalt deck 3 m wide with rails, collider included) to the nearest big land:
Frostreach 58 m, Beached Wreck 39 m, Ember Wreck 16 m. Endpoints in the manifest. **Check ship clearance** there - decks sit
~0.3 m above the land ends (low over water); if a sailing lane crosses one, drop that bridge file part or tell me to arch it.

## Islands
| Landing | Region / ground | Files | POIs | tris High / lod1 / col | path max deg | causeway |
|---|---|---|---|---|---|---|
| Gullhaven | A / temperate | `meshes/A/arch_isl_gullhaven*` -> `tidewrack/stage1/meshes/` | Gull Watchtower ruin (watchtower), Gull Shrine (shrine), Founders' Stone (lore), Harbourmaster's Cache (chest) | 51348 / 23105 / 19816 | 39.4 | - |
| Saltglass Landing | B / saltglass | `meshes/B/coast_isl_saltglass*` -> `tidewrack/stage2/meshes/` | Saltglass Shrine (crystal_shrine), Singing Shards (crystal_grove), Glass-diver's Chest (chest), Salt-crusted Tablet (lore) | 44182 / 19880 / 18188 | 56.1 | - |
| Frostreach Ice Dock | frost / frost | `meshes/frost/frost_isl_frostreach*` -> `tidewrack/stage4/meshes/` | Rimehollow Ice Cave (ice_cave), Frostreach Cairn (frost_shrine), Iced Chest (chest), Frozen Waystone (lore) | 38150 / 17167 / 16521 | 11.0 | 58.1 m |
| Vent Harbour | ash / ash | `meshes/ash/ash_isl_vent*` -> `tidewrack/stage4/meshes/` | Ventmouth (lava_vent), Steam Pools (hot_pool), Ember Shrine (obsidian_shrine), Ash-buried Chest (chest) | 51704 / 23265 / 20827 | 50.7 | - |
| Lantern Rock | A / temperate | `meshes/A/arch_isl_lantern_rock*` -> `tidewrack/stage1/meshes/` | Old Lantern ruin (lighthouse), Keeper's Hut (hut_ruin), Keeper's Strongbox (chest), Lamp-oil Logbook (lore) | 37586 / 16913 / 15408 | 21.9 | - |
| Saltwatch Keep | A / temperate | `meshes/A/arch_isl_saltwatch_keep*` -> `tidewrack/stage1/meshes/` | Outer Wall ruin (keep_ruin), Watch Shrine (shrine), Garrison Chest (chest) | 8116 / 3651 / 3369 | 13.8 | - |
| Coil Isle | A / temperate | `meshes/A/arch_isl_coil_isle*` -> `tidewrack/stage1/meshes/` | Coil Bones (bones), Serpent Shrine (shrine), Drowned Offering (chest) | 40286 / 18127 / 14826 | 10.6 | - |
| Beached Wreck | B / saltglass | `meshes/B/coast_isl_beached_wreck*` -> `tidewrack/stage2/meshes/` | Castaway Camp (wreck_camp), Salvage Chest (chest), Captain's Last Log (lore) | 10928 / 4916 / 3916 | 33.7 | 39.4 m |
| Frozen Wreck | frost / frost | `meshes/frost/frost_isl_frozen_wreck*` -> `tidewrack/stage4/meshes/` | Frozen Camp (wreck_camp), Bergcleft Cave (ice_cave), Frostbitten Chest (chest) | 31782 / 14301 / 12467 | 22.9 | - |
| Aurora Arch | frost / frost | `meshes/frost/frost_isl_aurora_arch*` -> `tidewrack/stage4/meshes/` | Aurora Shrine (frost_shrine), Skyglass Hollow (ice_cave), Starwatcher's Stone (lore) | 33008 / 14852 / 14229 | 39.8 | - |
| Ember Wreck | ash / ash | `meshes/ash/ash_isl_ember_wreck*` -> `tidewrack/stage4/meshes/` | Cinder Camp (wreck_camp), Ember Vent (lava_vent), Scorched Chest (chest) | 22994 / 10346 / 10011 | 24.8 | 16.0 m |
| Hot Spring Grotto | ash / ash | `meshes/ash/ash_isl_hot_spring*` -> `tidewrack/stage4/meshes/` | Upper Spring (hot_pool), Lower Spring (hot_pool), Bathers' Shrine (shrine), Bather's Bundle (chest) | 14602 / 6569 / 5628 | 11.3 | - |
| Obsidian Arch | ash / ash | `meshes/ash/ash_isl_obsidian_arch*` -> `tidewrack/stage4/meshes/` | Glassfire Shrine (obsidian_shrine), Arch Vent (lava_vent), Obsidian Mirror (lore) | 40034 / 18014 / 16614 | 10.2 | - |

Budgets: High <= ~52k tris per island (terrain capped at 36k), lod1 = 45 % of High, colliders 1-21k tris; 1 vc draw call + 1 glow.

## Known limits
- **Saltglass**: the landing sits under a 50 m cliff (original stage 2 terrain). Only the lower ground is reachable, so its
  4 POIs are down there (shrine on the lower shelf; grove, chest and tablet in the gullies). The plateau above is shaped but
  not reachable on foot - it needs a stair/ramp structure (next step if you want it).
- **Saltwatch Keep / Hot Spring** are small islands: small patches (8-15k tris), 3-4 POIs close together.
- Renders are lit by a simple test rig (no shadows: Mobile PSSM striped on these broad slopes); the game lights them itself.

Renders: `renders/small/<id>_before_after_High.jpg` (inland view from the pier head + overview, before/after),
`<id>_before_after_Low.jpg`, `<id>_pois_High.jpg` (each POI), `S5_contact_inland_after.jpg`.
Tools: `tools/build_stage5.py [id ...]` (deterministic per id), `tools/render5.gd`.
