# Model audit 2026-10-25

Geometry checks on every published High GLB: base height (sunk/floating), floating islands, LOD ratios (caps: lod1 <= 0.50, lod2 <= 0.20), and whether a collision file exists. A 3/4 render of each is in contact_buildings.jpg, contact_interiors.jpg and contact_props_ships.jpg.

| model | tris | min y | size m | lod1 | lod2 | col | floating | verdict |
|---|---|---|---|---|---|---|---|---|
| buildings/bld_apothecary_card2.glb | 18973 | -0.062 | 10.19x14.57x11.05 | 0.321 | 0.141 | y | 0 | OK |
| buildings/bld_bakery_card2.glb | 19087 | -0.055 | 11.96x16.71x13.11 | 0.363 | 0.132 | y | 1 | 1 tiny 4 cm bracket rod floats (not visible at game distance) |
| buildings/bld_crypt_card2.glb | 17442 | -0.3 | 13.51x15.31x18.19 | 0.441 | 0.194 | y | 0 | OK |
| buildings/bld_fountain_card2.glb | 6644 | -0.0 | 14.0x6.25x15.79 | 0.441 | 0.194 | y | 0 | OK |
| buildings/bld_gatehouse_card2.glb | 9758 | -0.034 | 24.0x24.73x8.81 | 0.351 | 0.169 | y | 0 | OK |
| buildings/bld_guildhall_card2.glb | 37251 | -0.056 | 16.16x24.28x16.26 | 0.409 | 0.142 | y | 0 | OK |
| buildings/bld_house1_card2.glb | 17443 | -0.062 | 9.99x15.28x10.48 | 0.299 | 0.102 | y | 0 | OK |
| buildings/bld_house2_card2.glb | 12716 | -0.058 | 9.37x14.88x11.04 | 0.275 | 0.122 | y | 0 | OK |
| buildings/bld_house3_card2.glb | 14779 | -0.045 | 9.85x14.91x11.69 | 0.273 | 0.108 | y | 0 | OK |
| buildings/bld_house4_card2.glb | 17034 | -0.062 | 9.56x17.74x8.98 | 0.281 | 0.097 | y | 0 | OK |
| buildings/bld_inn_card2.glb | 17782 | -0.06 | 14.27x20.46x15.4 | 0.425 | 0.187 | y | 2 | 2 tiny 4 cm bracket rods float 1-2 cm off the wall (not visible at game distance) |
| buildings/bld_keep_card2.glb | 46032 | -0.901 | 41.26x35.1x42.62 | 0.484 | 0.194 | y | 0 | rock base 0.9 m below grade by design |
| buildings/bld_library_card2.glb | 36686 | -0.3 | 18.6x21.36x18.93 | 0.364 | 0.194 | y | 0 | OK |
| buildings/bld_mage_academy_card2.glb | 63278 | -0.0 | 31.0x32.89x21.75 | 0.454 | 0.194 | y | 0 | OK |
| buildings/bld_market_card2.glb | 32632 | -0.034 | 13.8x16.5x21.42 | 0.485 | 0.194 | y | 0 | OK |
| buildings/bld_observatory_card2.glb | 19279 | -0.502 | 23.8x31.4x24.59 | 0.485 | 0.194 | y | 2 | crag 0.5 m below grade by design; 2 tiny bracket rods (4 cm) float 1-2 cm off |
| buildings/bld_port_card2.glb | 76222 | -2.5 | 36.95x22.51x37.27 | 0.471 | 0.194 | y | 0 | quay piles go 2.5 m below grade by design |
| buildings/bld_smithy_card2.glb | 11859 | -0.06 | 12.25x15.38x11.32 | 0.435 | 0.194 | y | 0 | OK |
| buildings/bld_temple_card2.glb | 37245 | -0.3 | 28.2x30.03x25.01 | 0.422 | 0.194 | y | 0 | OK |
| buildings/bld_thieves_den_card2.glb | 32294 | -0.056 | 23.22x20.9x11.9 | 0.317 | 0.164 | y | 0 | OK |
| buildings/bld_townhall_card2.glb | 18405 | -0.0 | 17.7x20.22x15.5 | 0.485 | 0.194 | y | 0 | OK |
| buildings/bld_training_hall_card2.glb | 17401 | -0.052 | 13.97x15.6x25.73 | 0.479 | 0.194 | y | 0 | OK |
| buildings/bld_treasury_card2.glb | 10890 | 0.0 | 17.36x24.6x17.5 | 0.358 | 0.194 | y | 0 | OK |
| buildings/bld_wall_segment_card2.glb | 816 | 0.0 | 12.2x8.4x3.9 | 0.482 | 0.194 | y | 0 | OK |
| buildings/bld_walls_demo_card2.glb | 3828 | 0.0 | 37.2x20.09x7.2 | 0.484 | 0.194 | y | 0 | OK |
| buildings/bld_watchtower_card2.glb | 1744 | 0.0 | 7.2x21.7x7.32 | 0.406 | 0.194 | y | 0 | OK |
| buildings/bld_windmill_card2.glb | 5011 | -0.034 | 14.16x18.94x11.52 | 0.452 | 0.194 | y | 0 | OK |
| buildings/tripo/bld_barn_stable_tripo.glb | 47678 | 0.0 | 34.32x14.55x24.36 | 0.485 | 0.194 | y | 0 | FIXED: was a cut barn carrying a slice of the house. Now a duplicate of the whole building, deprecated |
| buildings/tripo/bld_farmhouse_tripo.glb | 47678 | 0.0 | 34.32x14.55x24.36 | 0.485 | 0.194 | y | 0 | FIXED: now the whole farmhouse+barn, as on the card; walk-in doors 1.4x2.3 and 4x5 |
| buildings/tripo/bld_lighthouse_full_tripo.glb | 50853 | 0.0 | 23.83x25.91x25.33 | 0.49 | 0.196 | y | 0 | OK |
| buildings/tripo/bld_lighthouse_rock_island_tripo.glb | 43805 | 0.0 | 23.83x9.1x25.33 | 0.49 | 0.196 | y | 0 | OK |
| buildings/tripo/bld_lighthouse_tower_tripo.glb | 6760 | 4.404 | 7.51x18.33x7.53 | 0.49 | 0.194 | y | 0 | base at 4.4 m by design: shares an origin with the rock island |
| interiors/altar.glb | 4490 | 0.0 | 2.6x1.81x1.7 | 0.485 | 0.194 | - | 0 | OK |
| interiors/anvil.glb | 596 | 0.0 | 0.83x0.86x0.58 | 0.497 | 0.191 | - | 0 | OK |
| interiors/apothecary_shelf.glb | 5904 | 0.0 | 1.5x2.25x0.42 | 0.333 | 0.057 | - | 0 | OK |
| interiors/armchair.glb | 3063 | 0.0 | 0.96x1.24x0.96 | 0.456 | 0.14 | - | 0 | OK |
| interiors/armor_stand.glb | 3043 | 0.0 | 0.74x2.1x0.5 | 0.485 | 0.194 | - | 0 | OK |
| interiors/bakery_oven.glb | 1980 | 0.0 | 2.24x3.15x2.95 | 0.485 | 0.194 | - | 0 | OK |
| interiors/balcony_railing.glb | 752 | 0.0 | 2.14x1.22x0.13 | 0.484 | 0.191 | - | 0 | OK |
| interiors/bar_counter.glb | 5852 | 0.0 | 3.14x1.44x0.71 | 0.485 | 0.194 | - | 0 | OK |
| interiors/bed.glb | 4090 | 0.0 | 1.57x1.55x2.16 | 0.473 | 0.179 | - | 0 | OK |
| interiors/bench.glb | 344 | 0.0 | 1.6x0.47x0.34 | 0.326 | 0.14 | - | 0 | OK |
| interiors/bookshelf.glb | 3740 | 0.0 | 1.42x2.37x0.44 | 0.216 | 0.039 | - | 0 | OK |
| interiors/bottles.glb | 780 | 0.0 | 0.34x0.33x0.27 | 0.485 | 0.192 | - | 0 | OK |
| interiors/bread_rack.glb | 3224 | 0.0 | 1.25x1.81x0.45 | 0.484 | 0.114 | - | 0 | OK |
| interiors/chair.glb | 896 | 0.0 | 0.5x1.08x0.5 | 0.484 | 0.192 | - | 0 | OK |
| interiors/chest.glb | 776 | 0.0 | 0.96x0.7x0.61 | 0.482 | 0.193 | - | 0 | OK |
| interiors/crystal_orb.glb | 1808 | 0.0 | 0.6x1.37x0.6 | 0.485 | 0.194 | - | 0 | OK |
| interiors/forge.glb | 3172 | 0.0 | 3.12x3.5x1.6 | 0.5 | 0.194 | - | 0 | OK |
| interiors/gold_pile.glb | 3392 | 0.0 | 1.24x0.31x1.27 | 0.254 | 0.065 | - | 0 | OK |
| interiors/hearth.glb | 8678 | 0.0 | 2.71x2.97x1.22 | 0.485 | 0.194 | - | 0 | OK |
| interiors/iron_chandelier.glb | 8252 | 0.0 | 1.63x2.23x1.63 | 0.485 | 0.194 | - | 8 | 8 "floating" islands are candle flames/drips: intentional |
| interiors/keg.glb | 560 | 0.0 | 0.61x0.72x0.65 | 0.482 | 0.186 | - | 0 | OK |
| interiors/ladder.glb | 808 | 0.0 | 0.5x3.0x0.06 | 0.356 | 0.193 | - | 0 | OK |
| interiors/lectern.glb | 1307 | 0.0 | 0.6x1.23x0.51 | 0.445 | 0.19 | - | 0 | OK |
| interiors/lion_banner.glb | 2628 | 0.0 | 1.28x2.37x0.1 | 0.316 | 0.139 | - | 0 | OK |
| interiors/market_stall.glb | 2900 | 0.0 | 2.4x2.58x1.2 | 0.484 | 0.194 | - | 0 | OK |
| interiors/meeting_table.glb | 3264 | 0.0 | 3.6x1.16x1.1 | 0.485 | 0.194 | - | 0 | OK |
| interiors/pew.glb | 556 | 0.0 | 2.28x1.08x0.5 | 0.482 | 0.086 | - | 0 | OK |
| interiors/quest_board.glb | 2335 | 0.0 | 1.9x2.13x0.4 | 0.484 | 0.193 | - | 0 | OK |
| interiors/rug.glb | 1532 | 0.0 | 3.15x0.02x2.0 | 0.279 | 0.009 | - | 0 | OK |
| interiors/sarcophagus.glb | 6386 | 0.0 | 1.1x1.27x2.4 | 0.392 | 0.063 | - | 0 | OK |
| interiors/sofa.glb | 3839 | 0.0 | 2.06x1.09x0.98 | 0.446 | 0.116 | - | 0 | OK |
| interiors/stair_railing.glb | 504 | 0.0 | 3.14x2.98x0.13 | 0.484 | 0.19 | - | 0 | OK |
| interiors/stool.glb | 660 | 0.0 | 0.37x0.73x0.36 | 0.485 | 0.194 | - | 0 | OK |
| interiors/table.glb | 1536 | 0.0 | 1.4x0.95x0.85 | 0.484 | 0.193 | - | 0 | OK |
| interiors/telescope.glb | 724 | 0.0 | 0.71x1.83x1.03 | 0.483 | 0.193 | - | 0 | OK |
| interiors/throne_dais.glb | 6386 | 0.0 | 3.2x3.58x3.2 | 0.485 | 0.194 | - | 0 | OK |
| interiors/vault_door.glb | 4166 | 0.0 | 2.74x2.81x0.85 | 0.485 | 0.177 | - | 0 | OK |
| interiors/wall_lantern.glb | 668 | 0.0 | 0.2x0.48x0.41 | 0.482 | 0.192 | - | 0 | OK |
| interiors/wardrobe.glb | 1623 | 0.0 | 1.2x2.1x0.7 | 0.304 | 0.037 | - | 0 | OK |
| interiors/weapon_rack.glb | 2714 | 0.0 | 1.5x2.05x0.41 | 0.431 | 0.192 | - | 0 | OK |
| props_street/prop_barrel_group.glb | 517 | 0.0 | 1.56x0.95x1.48 | 0.453 | 0.193 | - | 0 | OK |
| props_street/prop_bench.glb | 364 | 0.0 | 1.82x1.06x0.55 | 0.484 | 0.192 | - | 0 | OK |
| props_street/prop_cobble_edge.glb | 96 | -0.04 | 3.96x0.24x0.32 | 0.479 | 0.188 | - | 0 | OK |
| props_street/prop_crate_stack.glb | 200 | 0.0 | 1.56x1.35x0.81 | 0.48 | 0.19 | - | 0 | OK |
| props_street/prop_fence.glb | 192 | 0.0 | 4.18x1.16x0.18 | 0.479 | 0.188 | - | 0 | OK |
| props_street/prop_flower_planter.glb | 180 | 0.0 | 1.28x0.86x0.68 | 0.483 | 0.189 | - | 0 | OK |
| props_street/prop_hay_bale.glb | 112 | -0.01 | 1.2x0.78x0.84 | 0.482 | 0.179 | - | 0 | OK |
| props_street/prop_lantern_post.glb | 1096 | 0.0 | 1.05x4.43x0.5 | 0.484 | 0.193 | - | 0 | OK |
| props_street/prop_market_cart.glb | 849 | -0.034 | 3.85x1.48x1.6 | 0.484 | 0.192 | - | 0 | OK |
| props_street/prop_signpost.glb | 228 | 0.0 | 2.38x4.09x1.02 | 0.478 | 0.189 | - | 0 | OK |
| props_street/prop_well.glb | 1006 | 0.0 | 2.8x3.2x2.33 | 0.483 | 0.193 | - | 0 | OK |
| ships/ship_boat_02.glb | 1175 | -0.856 | 2.41x5.82x6.4 | 0.5 | 0.2 | y | 0 | hull below waterline by design |
| ships/ship_boat_sail.glb | 1449 | -0.867 | 3.95x5.9x7.24 | 0.5 | 0.199 | y | 0 | hull below waterline by design |
| ships/ship_tidewrack_sailing_ship.glb | 21268 | -1.853 | 8.18x15.44x30.0 | 0.485 | 0.194 | y | 0 | hull below waterline by design |

Interiors: 27 props had LODs over the caps (e.g. chest lod1 was 0.85, wall_lantern 0.76/0.49). These were rebuilt by decimating the High mesh into the existing LOD GLBs, keeping their embedded lod-res atlas (tools/v2/fix_interior_lods.py). All are now <= 0.50/0.20.
