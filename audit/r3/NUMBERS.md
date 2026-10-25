# Round 3 numbers
Before numbers come from bldview (Lucky's current three.js builder; ext+roof groups). After numbers are the GLB nodes walls+roof, one shared material.

| building | before ext+roof meshes / tris | after meshes / tris |
|---|---|---|
| guildhall | 37+17 / 5566 | 2 / 5734 |
| library | 33+11 / 4056 | 2 / 6344 |
| townhall | 24+19 / 4820 | 2 / 7290 |
| mage | 24+12 / 4298 | 2 / 4174 |
| treasury | 22+3 / 2254 | 2 / 4504 |
| crypt | 22+11 / 2751 | 2 / 4500 |
| market | 32+16 / 4126 | 2 / 4732 |
| apothecary | 23+16 / 3146 | 2 / 6292 |
| bakery | 25+16 / 3134 | 2 / 6216 |
| inn | 26+14 / 4594 | 2 / 7888 |
| smithy | 22+10 / 2741 | 2 / 4134 |
| training | 24+11 / 3934 | 2 / 5690 |
| keep | 29+4 / 7351 | 2 / 5928 |
| temple | 17+10 / 6456 | 2 / 5398 |
| observatory | 19+5 / 2760 | 2 / 2218 |
| colosseum | 12+3 / 3626 | 2 / 4736 |

## Dressing and decals (tris)
- dressing/curb_2m.glb: 40
- dressing/cobble_edge_2m.glb: 54
- dressing/lantern_post.glb: 68
- dressing/wall_lantern.glb: 48
- dressing/signpost.glb: 84
- dressing/milestone.glb: 80
- dressing/well.glb: 244
- dressing/market_stall_red.glb: 276
- dressing/market_stall_blue.glb: 276
- dressing/market_stall_green.glb: 276
- dressing/banner_pole_blue.glb: 36
- dressing/banner_pole_red.glb: 36
- dressing/wall_cap_4m.glb: 44
- dressing/rubble.glb: 120
- dressing/bench.glb: 44
- dressing/flower_planter.glb: 132
- decals/decal_moss_wall.glb: 2
- decals/decal_moss_ground.glb: 2
- decals/decal_crack_wall.glb: 2
- decals/decal_crack_ground.glb: 2
- decals/decal_dirt_ground.glb: 2
- decals/decal_dirt_wall.glb: 2
- decals/decal_grime_wall.glb: 2
- decals/decal_leaves.glb: 2
- decals/decal_puddle.glb: 2
- decals/decal_soot_wall.glb: 2

## Terrain (tris, LOD0/1/2)
- terrain/mountain_peak_snow.glb: 2560
- terrain/mountain_peak_snow_lod1.glb: 640
- terrain/mountain_peak_snow_lod2.glb: 120
- terrain/mountain_peak_bare.glb: 2240
- terrain/mountain_peak_bare_lod1.glb: 560
- terrain/mountain_peak_bare_lod2.glb: 100
- terrain/volcano_cone_flank.glb: 2240
- terrain/volcano_cone_flank_lod1.glb: 560
- terrain/volcano_cone_flank_lod2.glb: 100
- terrain/cliff_ridge_60m.glb: 1600
- terrain/cliff_ridge_60m_lod1.glb: 400
- terrain/cliff_ridge_60m_lod2.glb: 100
- terrain/scree_slope.glb: 360
- terrain/scree_slope_lod1.glb: 140
- terrain/grass_mound.glb: 400
- terrain/grass_mound_lod1.glb: 160
- terrain/rock_arch.glb: 720
- terrain/rock_arch_lod1.glb: 180

## Placements
- PLACEMENT_dressing_town.json: 560 items
- PLACEMENT_decals.json: 314 items
- PLACEMENT_dressing_roads.json: 143 items

In merged batches that is one draw call per 128 m chunk per atlas: about 2 calls per visible town chunk, so roughly 8–12 extra calls in a town view. This was not measured in game.
