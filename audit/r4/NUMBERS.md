# Round 4 numbers

## Buildings (tris): High (2048) / Medium (1024) / Low (512); 2 meshes each (windmill 3), 1 material
| building | High | Medium | Low |
|---|---|---|---|
| house1 | 22616 | 5362 | 2542 |
| house2 | 25748 | 5972 | 2704 |
| house3 | 21704 | 5238 | 2458 |
| house4 | 26422 | 5982 | 2698 |
| farmhouse | 16136 | 7724 | 3464 |
| thieves | 27206 | 6760 | 2528 |
| barn | 19700 | 3570 | 2186 |
| stables | 24538 | 6868 | 2708 |
| windmill | 3906 | 2676 | 2308 |
| lighthouse | 5764 | 3932 | 3408 |
| gate_tower | 2766 | 1340 | 1204 |
| guildhall | 32034 | 6162 | 4766 |
| library | 34314 | 6696 | 5124 |
| townhall | 30662 | 7346 | 3486 |
| mage | 47626 | 9258 | 6102 |
| treasury | 27984 | 4504 | 2184 |
| crypt | 28376 | 4500 | 2180 |
| market | 28236 | 4732 | 3236 |
| apothecary | 26688 | 6292 | 2708 |
| bakery | 13032 | 6216 | 2680 |
| inn | 31656 | 8104 | 3912 |
| smithy | 25334 | 4474 | 2818 |
| training | 30532 | 5690 | 4090 |
| keep | 20104 | 7304 | 4544 |
| temple | 42240 | 8834 | 5022 |
| observatory | 4724 | 2218 | 1842 |
| colosseum | 19464 | 9004 | 7156 |

## Terrain (tris)
- hi/terrain/peak_snow_hi.glb: 57800 (2048)
- hi/terrain/peak_snow_hi_lod1.glb: 9800 (1024)
- hi/terrain/peak_snow_hi_lod2.glb: 1152 (512)
- hi/terrain/peak_bare_hi.glb: 24200 (2048)
- hi/terrain/peak_bare_hi_lod1.glb: 6272 (1024)
- hi/terrain/peak_bare_hi_lod2.glb: 968 (512)
- hi/terrain/volcano_flank_hi.glb: 54450 (2048)
- hi/terrain/volcano_flank_hi_lod1.glb: 9800 (1024)
- hi/terrain/volcano_flank_hi_lod2.glb: 1352 (512)
- hi/terrain/cliff_strata_hi.glb: 27500 (2048)
- hi/terrain/cliff_strata_hi_lod1.glb: 5958 (1024)
- hi/terrain/cliff_strata_hi_lod2.glb: 704 (512)
- hi/terrain/shore_edge_hi.glb: 16000 (2048)
- hi/terrain/shore_edge_hi_lod1.glb: 6400 (1024)
- hi/terrain/shore_edge_hi_lod2.glb: 608 (512)
- hi/terrain/boulder_strata_hi.glb: 6400 (2048)
- hi/terrain/boulder_strata_hi_lod1.glb: 1600 (1024)
- hi/terrain/boulder_strata_hi_lod2.glb: 400 (512)

## Trees/foliage (tris)
- hi/trees/oak_hi.glb: 2494 (2048)
- hi/trees/oak_hi_lod1.glb: 684 (1024)
- hi/trees/oak_hi_lod2.glb: 6 (512)
- hi/trees/oak_autumn_hi.glb: 2494 (2048)
- hi/trees/oak_autumn_hi_lod1.glb: 684 (1024)
- hi/trees/oak_autumn_hi_lod2.glb: 6 (512)
- hi/trees/oak_deep_hi.glb: 2494 (2048)
- hi/trees/oak_deep_hi_lod1.glb: 684 (1024)
- hi/trees/oak_deep_hi_lod2.glb: 6 (512)
- hi/trees/birch_hi.glb: 2494 (2048)
- hi/trees/birch_hi_lod1.glb: 684 (1024)
- hi/trees/birch_hi_lod2.glb: 6 (512)
- hi/trees/blossom_hi.glb: 2494 (2048)
- hi/trees/blossom_hi_lod1.glb: 684 (1024)
- hi/trees/blossom_hi_lod2.glb: 6 (512)
- hi/trees/pine_hi.glb: 2934 (2048)
- hi/trees/pine_hi_lod1.glb: 172 (1024)
- hi/trees/pine_hi_lod2.glb: 6 (512)
- hi/trees/pine_snow_hi.glb: 6174 (2048)
- hi/trees/pine_snow_hi_lod1.glb: 972 (1024)
- hi/trees/pine_snow_hi_lod2.glb: 6 (512)
- hi/trees/bush_hi.glb: 760 (2048)
- hi/trees/bush_hi_lod1.glb: 180 (1024)
- hi/trees/bush_autumn_hi.glb: 760 (2048)
- hi/trees/bush_autumn_hi_lod1.glb: 180 (1024)
- hi/trees/grass_clump_hi.glb: 440 (2048)
- hi/trees/grass_clump_hi_lod1.glb: 100 (1024)

## Godot test (copy at /tmp/gp4, Godot 4.7.2, llvmpipe CPU rasteriser in xvfb, 1280x720)
The scene has 27 buildings, 6 terrain pieces and 60 trees/foliage. Frame ms on llvmpipe is CPU software rendering and is NOT representative of the S26; use draw calls and primitives.

| shot | Ultra Forward+ calls/prims/ms | High Mobile | Medium Mobile | Low Mobile |
|---|---|---|---|---|
| cliff | 18/170678/100 | 10/170678/88 | 10/80130/37 | 10/13242/35 |
| closeup_inn | 122/1203846/261 | 99/1203846/203 | 99/333974/70 | 99/180930/54 |
| closeup_mage | 78/992992/202 | 57/992992/116 | 57/237282/49 | 57/128648/47 |
| closeup_temple | 115/1307870/271 | 80/1307870/224 | 80/338904/83 | 80/192582/66 |
| hero_colosseum_keep | 134/1481632/370 | 100/1481632/234 | 100/400396/85 | 100/229318/67 |
| hero_mage_temple | 129/1431552/387 | 101/1431552/223 | 101/381128/85 | 101/218478/63 |
| houses | 64/595858/218 | 40/595858/152 | 40/173088/47 | 40/68266/40 |
| night_closeup_inn | 122/1203846/246 | 99/1203846/203 | 99/333974/73 | 99/180930/59 |
| night_closeup_mage | 78/992992/198 | 57/992992/173 | 57/237282/53 | 57/128648/51 |
| night_town | 134/1481632/251 | 100/1481632/249 | 100/400396/85 | 100/229318/73 |
| night_volcano | 10/272260/89 | 4/272260/82 | 4/49010/28 | 4/6770/24 |
| peak_bare | 18/323308/87 | 8/323308/64 | 8/84954/25 | 8/14154/22 |
| row2 | 121/1239918/348 | 85/1239918/214 | 85/324494/68 | 85/169064/54 |
| shore | 25/216614/106 | 15/216614/81 | 15/97662/32 | 15/16388/32 |
| terrain | 20/263008/109 | 9/263008/73 | 9/113688/25 | 9/14714/22 |
| trees | 78/317272/242 | 53/317272/243 | 53/65422/71 | 53/6176/38 |
| volcano | 10/272260/101 | 4/272260/73 | 4/49010/27 | 4/6770/24 |
