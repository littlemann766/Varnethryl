# Tidewrack Sea: Stage 1 art (progress)
Built by Beth on 2026-10-29. Art-only drop-in for Lucky. No game project files were touched; renders were done in /tmp copies only, and those copies are deleted.

| Step | Status | Output |
|---|---|---|
| 1. Final world map v4 (label overlap fixed) | done | map/tidewrack_sea_world_map_v4.jpg, map/draw_combined_v4.py, land mask map/tidewrack_land_v4.npz |
| 2a. Archipelago islands from the v4 land mask | done | meshes/arch_islands (.glb, _lod1, _col) |
| 2b. Gullhaven, Lantern Rock, Wreck Reef (3 sunken galleon hulks), Saltwatch Keep + dive bell | done | meshes/arch_* |
| 2c. Water shader High (1 call, waves + crest/shore foam) and Low (flat) | done | shaders/ocean_water*.gdshader, shaders/arch_shore_dist.png/.json |
| 2d. Shore rocks, buoys, storm wall + fog bank | done | meshes/arch_shore_rocks, buoy_*, arch_storm_wall, arch_fog_bank |
| 2e. Brinecrown Coil (rest + hero) + sea-stack arena | done (mesh only; Lucian rigs) | meshes/brinecrown_coil_*, arch_coil_arena, BRINECROWN_COIL_NOTES.md |
| 3. Ship upgrades: 3 visible tiers x 2 ships (add-ons) + spec | done | meshes/upg_*, SHIP_UPGRADES.md |
| 4. Renders, before/after, hero sheet, upgrade contact sheet | done | renders/ |
| 5. Handoff notes | done | README_LUCKY.md |

## Next (not started)
- A sail-less galleon copy, for true sail swaps.
- A polish pass on the T1 figurehead and the skiff trim.
- Painted textures/UVs for the islands, props and the Coil (vertex colour only for now).
- Gullhaven interiors and NPC dressing.
- Stage 2: the Sunken Ward dive.

## Polish (2026-10-30)
- The galleon upgrade sails now use explicit mast positions (z -7.0 / -0.8 / 5.3), so all 3 masts are covered. Before this, the main mast was missed.
- The T1 figurehead is now a carved bust with a brass collar. Before, it read like a log.
- ship_upgrade_contact_sheet.jpg was re-rendered and checked by eye.

- Storm border v2, from Stage 2: arch_fog_layers / arch_storm_sky / arch_storm_sea / arch_storm_col with shaders fog_layers / storm_sky / storm_sea. These replace arch_storm_wall and arch_fog_bank in-game; the old files are kept only for the old renders. See ../ocean_stage2/README_LUCKY.md.
