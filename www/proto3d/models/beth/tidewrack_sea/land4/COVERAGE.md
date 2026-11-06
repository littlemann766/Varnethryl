# Land4 coverage — every landmass

Scatter on a `named_land` row can read 0 because those points are counted on the matching `named_island` row (pier neighbourhood). That is the same ground, not a missed island.

A skerry with scatter 0 had no gentle sample that cleared the path/prop keep-out. It is listed so it is not a silent omission. Those bare skerries still use the land4 terrain shader, so the surface is the rock and sand photographs, not a flat vertex colour.

## Playable islands (stage5 manifest, 13)

| id | region | name | scatter | trees-ish | close shot | silhouette | pixels changed |
|---|---|---|---:|---:|---|---|---:|
| lantern_rock | A | Lantern Rock | 453 | 148 | lantern_rock_close | lantern_rock_silhouette | 42.86 |
| gullhaven | A | Gullhaven | 343 | 110 | gullhaven_close | gullhaven_silhouette | 50.51 |
| saltwatch_keep | A | Saltwatch Keep | 16 | 3 | saltwatch_keep_close | saltwatch_keep_silhouette | 17.7 |
| coil_isle | A | Coil Isle | 289 | 75 | coil_isle_close | coil_isle_silhouette | 37.22 |
| saltglass | B | Saltglass Landing | 212 | 13 | saltglass_close | saltglass_silhouette | 1.14 |
| beached_wreck | B | Beached Wreck | 55 | 8 | beached_wreck_close | beached_wreck_silhouette | 9.23 |
| frostreach | frost | Frostreach Ice Dock | 67 | 14 | frostreach_close | frostreach_silhouette | 2.32 |
| frozen_wreck | frost | Frozen Wreck | 153 | 41 | frozen_wreck_close | frozen_wreck_silhouette | 7.91 |
| aurora_arch | frost | Aurora Arch | 186 | 38 | aurora_arch_close | aurora_arch_silhouette | 47.14 |
| vent | ash | Vent Harbour | 347 | 49 | vent_close | vent_silhouette | 5.29 |
| ember_wreck | ash | Ember Wreck | 194 | 17 | ember_wreck_close | ember_wreck_silhouette | 11.25 |
| hot_spring | ash | Hot Spring Grotto | 49 | 6 | hot_spring_close | hot_spring_silhouette | 7.53 |
| obsidian_arch | ash | Obsidian Arch | 315 | 27 | obsidian_arch_close | obsidian_arch_silhouette | 8.61 |

## Other land components

`main` is the largest landmass in the region (covered by the region mountain/shore/ground shots). `islet` is everything else above ~250 m². `named_land` is the component sitting under a playable island.

| id | region | kind | ha | nearest named | m | scatter | shot |
|---|---|---|---:|---|---:|---:|---|
| A_islet_808_-333 | A | islet | 2.76 | lantern_rock | 873.6 | 83 | islet_808_-333 |
| A_islet_405_636 | A | islet | 2.72 | coil_isle | 568.6 | 67 | islet_405_636 |
| A_islet_-49_326 | A | islet | 0.52 | coil_isle | 372.5 | 0 | islet_-49_326 |
| A_islet_-509_637 | A | islet | 0.32 | saltwatch_keep | 244.2 | 14 | islet_-509_637 |
| A_islet_311_205 | A | islet | 0.28 | lantern_rock | 412.5 | 7 | islet_311_205 |
| A_islet_-241_-25 | A | islet | 0.24 | lantern_rock | 224.9 | 12 | islet_-241_-25 |
| A_islet_894_-487 | A | islet | 0.24 | lantern_rock | 1011.9 | 7 | islet_894_-487 |
| A_islet_188_558 | A | islet | 0.2 | coil_isle | 370.2 | 15 | islet_188_558 |
| A_islet_-1158_-277 | A | islet | 0.16 | gullhaven | 806.4 | 0 | checklist only |
| A_islet_-313_-31 | A | islet | 0.08 | gullhaven | 291.1 | 8 | checklist only |
| A_islet_-716_-554 | A | islet | 0.04 | gullhaven | 432.1 | 3 | skerry_-716_-554 |
| A_islet_-412_-802 | A | islet | 0.04 | gullhaven | 486.3 | 0 | checklist only |
| A_islet_-4_446 | A | islet | 0.04 | coil_isle | 283.3 | 0 | checklist only |
| A_islet_278_-425 | A | islet | 0.04 | lantern_rock | 479.7 | 0 | checklist only |
| A_main | A | main | 25.12 | lantern_rock | 97.9 | 441 | region shots |
| A_named_gullhaven | A | named_land | 20.92 | gullhaven | 142.0 | 509 | region shots |
| A_named_coil_isle | A | named_land | 8.6 | coil_isle | 118.3 | 49 | region shots |
| A_named_saltwatch_keep | A | named_land | 6.16 | saltwatch_keep | 79.1 | 190 | region shots |
| A_named_saltwatch_keep | A | named_land | 0.12 | saltwatch_keep | 125.2 | 0 | region shots |
| B_islet_-1710_179 | B | islet | 4.68 | saltglass | 638.5 | 74 | islet_-1710_179 |
| B_islet_-1474_-216 | B | islet | 1.24 | saltglass | 926.7 | 22 | islet_-1474_-216 |
| B_islet_-2100_1174 | B | islet | 0.96 | beached_wreck | 404.7 | 32 | islet_-2100_1174 |
| B_islet_-2077_-253 | B | islet | 0.08 | saltglass | 443.9 | 8 | checklist only |
| B_islet_-2413_773 | B | islet | 0.04 | beached_wreck | 183.1 | 0 | skerry_-2413_773 |
| B_islet_-1950_425 | B | islet | 0.04 | saltglass | 509.6 | 2 | checklist only |
| B_main | B | main | 138.76 | saltglass | 56.0 | 2039 | region shots |
| B_named_saltglass | B | named_land | 1.04 | saltglass | 142.8 | 0 | region shots |
| B_named_beached_wreck | B | named_land | 0.12 | beached_wreck | 5.2 | 0 | region shots |
| ash_islet_-533_2050 | ash | islet | 16.68 | vent | 182.7 | 404 | islet_-533_2050 |
| ash_islet_-1245_2382 | ash | islet | 12.52 | vent | 913.8 | 498 | islet_-1245_2382 |
| ash_islet_-753_2385 | ash | islet | 0.88 | vent | 577.0 | 21 | islet_-753_2385 |
| ash_islet_597_1983 | ash | islet | 0.16 | ember_wreck | 286.7 | 0 | checklist only |
| ash_islet_-54_2265 | ash | islet | 0.12 | vent | 582.5 | 0 | checklist only |
| ash_islet_-223_1995 | ash | islet | 0.08 | vent | 289.5 | 0 | skerry_-223_1995 |
| ash_islet_-73_2722 | ash | islet | 0.08 | obsidian_arch | 533.8 | 0 | checklist only |
| ash_main | ash | main | 48.8 | ember_wreck | 251.1 | 989 | region shots |
| ash_named_hot_spring | ash | named_land | 3.28 | hot_spring | 100.3 | 0 | region shots |
| frost_islet_-25_-2011 | frost | islet | 44.56 | aurora_arch | 445.0 | 468 | islet_-25_-2011 |
| frost_islet_478_-1960 | frost | islet | 7.32 | aurora_arch | 649.3 | 63 | islet_478_-1960 |
| frost_islet_-1223_-1804 | frost | islet | 6.76 | frostreach | 283.6 | 36 | islet_-1223_-1804 |
| frost_islet_-1383_-1886 | frost | islet | 0.56 | frostreach | 405.5 | 16 | islet_-1383_-1886 |
| frost_islet_-2195_-1700 | frost | islet | 0.2 | frostreach | 1238.2 | 0 | islet_-2195_-1700 |
| frost_islet_699_-2081 | frost | islet | 0.12 | aurora_arch | 746.0 | 0 | checklist only |
| frost_islet_-2078_-2344 | frost | islet | 0.04 | frostreach | 1161.7 | 0 | skerry_-2078_-2344 |
| frost_islet_1070_-2402 | frost | islet | 0.04 | aurora_arch | 1020.6 | 0 | checklist only |
| frost_main | frost | main | 210.88 | frozen_wreck | 362.9 | 2349 | region shots |
| frost_named_frostreach | frost | named_land | 0.04 | frostreach | 30.8 | 0 | region shots |

## Terrain meshes

| mesh | region | tris before | high | lod1 % | skirt tris | max move m | route dy m | ydev90 before→after | peak before→after |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| arch_isl_coil_isle | A | 40268 | 44166 | 40.0 | 1216 | 0.395 | 0.0 | 0.935→0.904 | 29.67→29.67 |
| arch_isl_gullhaven | A | 51126 | 70189 | 40.0 | 428 | 1.15 | 0.0 | 0.765→0.51 | 45.48→45.48 |
| arch_isl_lantern_rock | A | 37480 | 39819 | 40.0 | 0 | 0.408 | 0.0 | 0.796→0.755 | 76.8→76.8 |
| arch_isl_saltwatch_keep | A | 8086 | 8572 | 40.0 | 380 | 0.268 | 0.0 | 1.148→1.129 | 12.79→12.79 |
| arch_islands | A | 113938 | 222796 | 40.0 | 0 | 3.0 | 0.0 | 1.418→0.38 | 70.0→70.0 |
| ash_isl_ember_wreck | ash | 29610 | 36968 | 40.0 | 16 | 0.34 | 0.0 | 19.681→17.967 | 67.37→67.37 |
| ash_isl_hot_spring | ash | 15192 | 15322 | 40.0 | 124 | 0.199 | 0.0 | 1.133→1.124 | 17.23→17.23 |
| ash_isl_obsidian_arch | ash | 40238 | 42554 | 40.0 | 0 | 0.314 | 0.0 | 1.411→1.301 | 35.54→35.54 |
| ash_isl_vent | ash | 51400 | 59955 | 40.0 | 0 | 0.494 | 0.0 | 1.195→0.951 | 59.25→59.25 |
| ash_tile_x0z0 | ash | 4612 | 6251 | 40.0 | 0 | 0.872 | 0.0 | 8.806→0.77 | 37.16→37.16 |
| ash_tile_x0z1 | ash | 14384 | 25594 | 40.0 | 0 | 3.0 | 0.0 | 4.567→0.725 | 31.06→31.06 |
| ash_tile_x1z0 | ash | 31113 | 68311 | 40.0 | 0 | 2.828 | 0.0 | 3.603→0.509 | 119.52→118.56 |
| ash_tile_x1z1 | ash | 33416 | 74756 | 40.0 | 8 | 3.0 | 0.0 | 2.101→0.5 | 121.51→121.51 |
| ash_tile_x2z0 | ash | 8575 | 15030 | 40.0 | 0 | 3.0 | 0.0 | 4.775→1.418 | 79.58→79.58 |
| ash_tile_x2z1 | ash | 13298 | 33235 | 40.0 | 4 | 2.252 | 0.0 | 4.968→0.753 | 86.33→86.33 |
| coast_isl_beached_wreck | B | 14220 | 14781 | 40.0 | 0 | 0.127 | 0.0 | 26.471→26.327 | 45.16→45.16 |
| coast_isl_saltglass | B | 49658 | 84528 | 40.0 | 0 | 1.116 | 0.0 | 1.028→0.419 | 128.97→128.97 |
| coast_tile_x0z0 | B | 43190 | 86960 | 40.0 | 0 | 1.15 | 0.0 | 1.31→0.273 | 92.6→92.6 |
| coast_tile_x0z1 | B | 32502 | 86675 | 40.0 | 44 | 1.845 | 0.0 | 1.753→0.39 | 55.48→55.48 |
| coast_tile_x0z2 | B | 53104 | 69119 | 40.0 | 0 | 2.491 | 0.0 | 1.585→0.713 | 66.32→66.32 |
| coast_tile_x0z3 | B | 88344 | 103342 | 40.0 | 20 | 3.0 | 0.0 | 0.33→0.308 | 110.49→110.49 |
| coast_tile_x1z0 | B | 49308 | 67008 | 40.0 | 0 | 2.857 | 0.0 | 0.94→0.515 | 103.22→103.22 |
| coast_tile_x1z1 | B | 59992 | 83902 | 40.0 | 4 | 3.0 | 0.0 | 0.994→0.645 | 111.55→111.55 |
| coast_tile_x1z2 | B | 38868 | 104795 | 40.0 | 8 | 2.486 | 0.0 | 1.255→0.29 | 94.44→94.44 |
| coast_tile_x1z3 | B | 28658 | 62246 | 40.0 | 0 | 2.495 | 0.0 | 1.057→0.298 | 50.83→50.83 |
| coast_tile_x2z1 | B | 6879 | 9329 | 40.0 | 12 | 1.243 | 0.0 | 1.633→0.404 | 12.63→12.56 |
| coast_tile_x2z2 | B | 5231 | 16729 | 40.0 | 16 | 1.15 | 0.0 | 3.086→0.433 | 29.49→29.49 |
| coast_tile_x2z3 | B | 4586 | 4586 | 40.0 | 0 | 0.0 | 0.0 | 0.0→0.0 | -14.09→-14.09 |
| frost_isl_aurora_arch | frost | 32660 | 52414 | 40.0 | 0 | 0.545 | 0.0 | 1.592→0.689 | 48.74→48.74 |
| frost_isl_frostreach | frost | 38088 | 65691 | 40.0 | 340 | 2.808 | 0.0 | 1.64→0.624 | 61.93→61.93 |
| frost_isl_frozen_wreck | frost | 31906 | 37247 | 40.0 | 224 | 0.644 | 0.0 | 0.945→0.688 | 41.21→41.21 |
| frost_tile_x0z0 | frost | 75652 | 108189 | 40.0 | 0 | 2.51 | 0.0 | 0.51→0.27 | 60.0→60.0 |
| frost_tile_x0z1 | frost | 72324 | 103433 | 40.0 | 0 | 4.0 | 0.0 | 0.572→0.305 | 60.0→60.0 |
| frost_tile_x1z0 | frost | 100984 | 155589 | 40.0 | 0 | 3.063 | 0.0 | 0.531→0.31 | 60.04→60.04 |
| frost_tile_x1z1 | frost | 35956 | 103173 | 40.0 | 0 | 4.0 | 0.0 | 2.837→0.366 | 60.0→60.0 |
| frost_tile_x2z0 | frost | 69876 | 112701 | 40.0 | 0 | 4.0 | 0.0 | 0.905→0.405 | 56.16→55.05 |
| frost_tile_x2z1 | frost | 79856 | 124489 | 40.0 | 0 | 4.0 | 0.0 | 0.985→0.464 | 61.06→60.71 |
| frost_tile_x3z0 | frost | 31756 | 75329 | 40.0 | 0 | 1.303 | 0.0 | 0.869→0.195 | 52.64→52.64 |
| frost_tile_x3z1 | frost | 3326 | 3326 | 40.0 | 0 | 1.15 | 0.0 | 6.823→6.687 | 11.35→11.35 |

## Scatter budgets (High, one whole region, streamed in 256 m chunks)

| region | instances | tris high | lod1 % | col tris | chunks |
|---|---:|---:|---:|---:|---:|
| A | 2600 | 175855 | 25.4 | 12924 | 34 |
| B | 2467 | 107557 | 35.2 | 6648 | 41 |
| frost | 3418 | 160340 | 38.7 | 21696 | 74 |
| ash | 2893 | 134671 | 39.1 | 16968 | 30 |
