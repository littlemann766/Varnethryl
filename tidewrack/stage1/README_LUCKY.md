# README_LUCKY: Tidewrack Sea Stage 1 art drop-in
Lucky, this is all art plus specs, and nothing in your project or Lucian's files was changed. Copy the folder in wherever suits you (for example res://art/ocean_stage1/).

## What's here
- map/: tidewrack_sea_world_map_v4.jpg (final map), draw_combined_v4.py, and tidewrack_land_v4.npz (the land mask the islands were built from).
- meshes/: every mesh is ONE vertex-coloured surface (1 draw call) with a _lod1 at 45-50% tris. stage1_manifest.json has the tri counts, prop positions, anchors, camera spots and ship mast data.
- shaders/:
  - ocean_water.gdshader (High) and ocean_water_low.gdshader (Low).
  - storm_wall.gdshader and fog_bank.gdshader.
  - vc_lit.tres: a vertex-colour material to put on all the meshes.
  - arch_shore_dist.png + .json: shore distance for region A, R channel = metres to land.
- tools/: build_stage1.py rebuilds all meshes, render_stage1.gd is the render harness, and make_sheets.py composes the sheets.
- Specs: SHIP_UPGRADES.md, BRINECROWN_COIL_NOTES.md, PROGRESS.md.
- renders/: before_after_archipelago.jpg, stage1_hero_sheet.jpg, ship_upgrade_contact_sheet.jpg, the individual shots, and drawcalls.txt.

## Placement
- World coordinates are map metres. The origin is the Archipelago centre, north is -Z, and the water is at y = 0.
- Every arch_* mesh is already in world position. Instance it at the origin and don't move it. Buoys are the exception: place them yourself.
- The ship add-ons sit at the ship root (see SHIP_UPGRADES.md).

## Import settings (important)
- Meshes > Generate LODs: OFF for every file here. We ship our own _lod1, and Godot's auto-LOD made slivers on the island mesh in testing.
  For the same reason, my harness sets viewport mesh_lod_threshold = 0.
- Use shaders/vc_lit.tres (vertex colour as albedo) as the material override. glTF COLOR_0 is stored linear, so colours come out right.
- Shadows: ships and add-ons are off. Islands, props and the arena are on, with a 60 m shadow distance at sea. Storm wall and fog are off.
- arch_islands_col.glb is a coarse collider (about 7% of the tris). Use it as a trimesh collider for land. For the Wreck Reef no-go zone, use a ring of radius 95 m around props.wreck_reef.pos.

## Water
- High: a camera-following grid of about 200x200 quads (I used PlaneMesh 1600 m, subdiv 200, snapped to 8 m), material ocean_water.gdshader, with arch_shore_dist.png set as `shore_dist`.
  Gerstner waves, crest foam and shore foam are all in 1 draw call. Waves calm in the shallows.
- Low: a flat 32x32 grid using ocean_water_low.gdshader. It has the same shore foam with no vertex waves. Ship bob comes from script.
- Ship bob on High: on the CPU, evaluate the same 3 Gerstner waves (L 38/17/7 m, A 0.55/0.25/0.08) with wind_dir.
- Storm wall: arch_storm_wall.glb with storm_wall.gdshader. Set the `flash` uniform from script for lightning, and `detail = 0` on Low. arch_fog_bank.glb uses fog_bank.gdshader.
  Both are ribbons 40-100 m inside the region box.

## Measured in my Mobile-renderer harness (1280x720, desktop GPU, not the phone)
| Shot | High draw calls / frame prims | Low draw calls / frame prims |
|---|---|---|
| Archipelago hero at Gullhaven (islands, port, T3 galleon, skiffs, buoys, water, walls) | 18 / ~529k | 10 / ~62k |
| Brinecrown Coil arena (+ Coil) | 31 / ~574k | 18 / ~77k |

- **Draw calls** are well under the 120 (High) and 60 (Low) BUILD_PLAN targets for region A.
- **Frame prims** include the shadow-cascade passes. Scene geometry itself on High is about 200k tris: islands 73k, water 80k, rocks 12k, props about 16k, galleon lod1 10k, add-on 4k.
  The 350k High target is met for geometry, but shadows roughly double what the frame counter shows. If the phone needs it, set the islands to shadow-only within 60 m, or use 2 cascades.
- **Low** uses every _lod1, no shadows and no glow.
- Please profile on the S26 Ultra. I have not run this on the device.

## Code you'll need (my suggestion for the order)
1. **Sailing port.** Port the old JS sailing controller to GDScript:
   - rudder and throttle with coasting;
   - crew deck slots;
   - the V wake (a particle trail or ribbon);
   - colliders against arch_islands_col plus the reef ring;
   - the water grid following the camera;
   - Gerstner bob on High, script bob on Low;
   - the stats table from SHIP_UPGRADES.md.
2. **Boarding.** The Tidewrack pier triggers the board prompt, which swaps the player to the deck camera; docking at Gullhaven and the Saltwatch pier does the same.
   The skiff launch happens at the white skiff buoys (buoy_skiff), and the dive prompt at buoy_dive near the Saltwatch dive bell (props.saltwatch_keep in the manifest). The dive itself is Stage 2.
3. **Streaming.**
   - Each region is its own scene (region A = this kit).
   - Threaded load (ResourceLoader.load_threaded_request) starts when the ship is within about 150 m of the region box edge.
   - Fade the far silhouettes in and out.
   - A locked region keeps its storm wall solid, shows a "the crew refuses" prompt and pushes the ship back.
4. **Upgrades.** Save fields, add-on swap, shipwright UI, the gust button, and Harbour Charts fast travel (all in SHIP_UPGRADES.md).
5. **Boss.** Once Lucian rigs brinecrown_coil_rest, the Coil fight is fought from the deck inside the arch_coil_arena ring.

## Known gaps (honest)
- Vertex colour only: no painted textures or UVs on the islands, props or Coil.
- The Gullhaven houses are simple blocks with roofs.
- Lantern Rock sits on its own sea rock just off a larger island.
- The Wreck Reef and Coil arena were moved into open water near their map marks, because the marks sat on land in the v4 mask. Positions are in the manifest.
- Upgrade sails overlay your baked sails. On the galleon's middle mast the original sails still show through; see SHIP_UPGRADES.md.
