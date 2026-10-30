# Tidewrack Sea — Stage 3: sea-cave interiors + Sunken Ward underwater (Beth)

Godot 4.7.2, Mobile renderer. Each mesh = one vertex-coloured surface (+ `_lod1` at 45 %). No shadows from any of this.

## Caves (local cells: entrance at origin, cave runs into -Z; place each cell behind its coast mouth and fade/teleport at the mouth)
| cave | files | notes |
|---|---|---|
| Echo Grotto (190 m) | `cave_echo_grotto_{shell,glow,props,water,portal,col}.glb` | hanging saltglass ceiling, crystal hall, echo pool |
| Glasswyrm Cavern (170 m) | `cave_glasswyrm_cavern_*` | crystal spires, wyrm skeleton, boss arena r42 m (boss mesh not included) |
| Smugglers' Throat (230 m) | `cave_smugglers_throat_*` | 16 lanterns, rope bridge at y14, hidden jetty + stair + door |

Materials: shell/props = vertex-colour StandardMaterial (cull disabled); glow = `glow_vc.gdshader`; water = `cave_water.gdshader` (set `glow_tint`);
portal = `cave_portal.gdshader`. `_col` = trimesh collision (skiff). Light positions, skiff paths, widths/ceilings: `meshes/stage3_manifest.json`.
Lighting used in renders: dark BG, ambient (0.3,0.36,0.42) x5, ≤6 OmniLights per cave (energy 14, range 50, no shadows), exposure 1.5.

## Sunken Ward (world coords, centre (-1300, 400), seabed y -30)
`sw_seabed` (+`_col`), `sw_buildings`, `sw_landmarks` (copper dome hall, colonnade, towers, arcade, warden statues), `sw_rubble` -> `seabed_caustics.gdshader`;
`sw_kelp` -> `kelp_sway.gdshader` (COLOR.a = sway weight); `sw_light_shafts` -> `light_shaft.gdshader`; `sw_surface_under` -> `surface_under.gdshader`.
Underwater Environment when camera y < 0: BG + fog colour (0.08,0.32,0.36), fog density ~0.015, ambient (0.25,0.5,0.55). Streets run every 50 m on x/z = centre+50k.
Walk on `sw_seabed_col`; swimming = free volume above it (no extra collision needed).

## Budgets (stats_stage3.txt, 1280x720)
Caves High 11–31k prims, 4–6 draw calls; Low 5–15k. Sunken Ward High 87k, Low 39k prims, 7 draw calls.

## Known issues
- Interiors are separate cells, not stitched to the exterior heightfield: needs a fade/teleport at each mouth.
- Hanging saltglass reads a bit flat/blocky; Smugglers' jetty end shot is dim (add a lantern near the jetty door if needed).
- Light shafts are subtle; cave-mouth overhang slab is still somewhat boxy.
