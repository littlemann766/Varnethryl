# Tidewrack Sea: Stage 2, the Saltglass Coast (region B) + Sunken Ward dive spot
Art-only drop-in, made by Beth on 2026-10-30. It uses the same conventions as Stage 1 (see ../ocean_stage1/README_LUCKY.md):
- map metres, north is -Z, water at y = 0;
- one vertex-colour surface per mesh, with a _lod1 at 50% tris or less;
- glTF import with Generate LODs OFF;
- shaders/vc_lit.tres from Stage 1 as the material.

## Region
- B covers x -3000..-1200, z -1500..1700. It shares its east edge (x = -1200) with region A, so the sea is continuous and the Stage 1 islands start where these tiles stop.
- Water: the same ocean_water.gdshader as Stage 1, but with `shore_dist = shaders/coast_shore_dist.png` and `shore_rect = (-3000, -1500, 1800, 3200)`. Wind for this region is onshore from the west: wind_dir (1.0, 0.1).
- Storm wall and fog bank (`coast_storm_wall.glb` / `coast_fog_bank.glb`, using the Stage 1 shaders): keep them up until Brinecrown Coil is beaten, then fade them out.

## Meshes (all in world position: instance at the origin)
- **Terrain:** `coast_tile_x{0..2}z{0..3}(.glb/_lod1)`, 11 tiles of 600 x 800 m, about 174k tris High and 78k on lod1.
  - Tiles are split after simplifying, so there are no cracks between them, and each tile is culled on its own (camera and shadows).
  - The coast has cliffs on the exposed west, with strata bands and dark wet rock at the foot. There are beaches in the coves, river mouths and the long fjord inlet, uplands inland, and islets.
  - `coast_terrain_col.glb` is the land collider.
- `coast_saltglass_landing`: cliff port with two piers, a switchback stair cut up the cliff, a cargo lift, a clifftop warehouse, 14 houses and a pier-head beacon. The anchor point is in the manifest.
- **Skiff-only sea caves:** each one is a real cleft cut into the cliff terrain, with a rock arch, a rock roof going inland and a dark throat. Their interiors are Stage 3 sub-cells.
  - `coast_echo_grotto`: hanging saltglass.
  - `coast_glasswyrm_cavern`: big jagged mouth with glowing saltglass teeth and old ribs.
  - `coast_smugglers_throat`: narrow cleft with a rope bridge, lanterns and a hidden jetty.
- `coast_sunken_ward_surface`: the drowned district breaking the surface. It has broken column clusters, two drowned watch towers, a long arcade of arches, a copper dome just under the water, and a dive raft with a winch.
  Put Stage 1 `buoy_dive` in a ring of r = 30 m around `props.sunken_ward.dive_buoy`. That is where the Stage 2 dive starts (the dive interior isn't in this drop).
- `coast_saltglass_crystals`: pale cyan crystal clusters on the clifftops.
- `coast_offshore_rocks`: 300 rocks and sea stacks in the surf.
- `coast_beach_dressing`: driftwood plus one beached wreck in a cove.
- `stage2_manifest.json`: tri counts, tile list, prop positions, anchors and camera spots.

## Measured (my Mobile-renderer harness on desktop at 1280x720, not the phone)
- **High:** 18–41 draw calls (the Sunken Ward view is highest at 41), 270k–725k frame prims including shadow passes.
- **Low:** 17–36 draw calls, 91k–164k prims.
- That's under the BUILD_PLAN region B targets for draw calls (130 High / 65 Low). Tiling cut frame prims by about 2.4x compared with one big terrain mesh.
- Please profile on the S26 Ultra. If needed, drop the shadow distance to 40 m, or turn shadows off for the rocks and crystals.

## Code needed (beyond Stage 1)
- Region streaming: the A→B threaded load when you're within about 150 m of x = -1200, and storm-wall removal once the Coil is defeated.
- Skiff launch buoys outside each cave (use Stage 1 `buoy_skiff`), and a cave-entry trigger at each `props.coast_*.pos`.
- Docking at Saltglass Landing (`props.saltglass_landing.anchor`), which also adds it to Harbour Charts fast travel.
- Dive trigger at the Sunken Ward ring.
