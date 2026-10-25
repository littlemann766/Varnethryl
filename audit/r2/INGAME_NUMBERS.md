# Round 2 in-game numbers (960x540, SwiftShader, Play Solo)
Before = clean 25f4fdc. After = 25f4fdc + round-1 preview + round-2 preview (audit/r2/preview-only-r2.diff). Single samples; streaming state adds roughly ±10 calls of noise.

| spot | calls before | calls after | tris before | tris after |
|---|---|---|---|---|
| bld_farmhouse_front | 279 | 273 | 344112 | 347846 |
| bld_farmhouse_34 | 249 | 237 | 344545 | 339350 |
| bld_barn_front | 278 | 254 | 364731 | 342858 |
| bld_barn_34 | 289 | 260 | 364816 | 341122 |
| bld_stables_front | 477 | 469 | 366473 | 356720 |
| bld_stables_34 | 335 | 322 | 367341 | 353120 |
| bld_windmill_front | 439 | 438 | 348285 | 331213 |
| bld_windmill_34 | 502 | 497 | 373702 | 356374 |
| bld_house1_front | 366 | 364 | 345590 | 348426 |
| bld_house1_34 | 416 | 454 | 362119 | 382250 |
| bld_house2_front | 339 | 335 | 373956 | 378902 |
| bld_house2_34 | 336 | 336 | 371301 | 376406 |
| bld_house3_front | 332 | 326 | 372179 | 372646 |
| bld_house3_34 | 347 | 343 | 369003 | 375764 |
| bld_house4_front | 330 | 328 | 373039 | 375916 |
| bld_house4_34 | 332 | 329 | 370011 | 372368 |
| bld_lighthouse_front | 293 | 205 | 319924 | 295186 |
| bld_lighthouse_34 | 393 | 261 | 230267 | 220354 |
| bld_thieves_front | 392 | 382 | 382000 | 374997 |
| bld_thieves_34 | 353 | 342 | 377783 | 368738 |
| bld_gate_towers_front | 195 | 181 | 338838 | 301408 |
| bld_gate_towers_34 | 208 | 193 | 336660 | 299938 |
| zone_frost_slope | 214 | 306 | 338138 | 357080 |
| zone_frost_slope2 | 248 | 297 | 341887 | 350022 |
| zone_volcano | 132 | 145 | 223802 | 244916 |
| zone_volcano2 | 271 | 202 | 216027 | 209280 |
| zone_port | 318 | 282 | 200310 | 212560 |
| zone_port2 | 459 | 364 | 240859 | 244932 |
| zone_hob_blackbriar | 280 | 286 | 217985 | 272272 |
| zone_hob_thornwatch | 328 | 331 | 231362 | 232300 |
| zone_hob_ironfang | 386 | 366 | 353935 | 336476 |
| zone_frost_realm | 137 | 148 | 144298 | 165578 |

## Rerun with zone chunk 200 m (frost/volcano) and one mesh for the frost realm — this is the setting in preview-only-r2.diff
| spot | calls before | calls after (chunk 200) | tris before | tris after |
|---|---|---|---|---|
| zone_frost_slope | 214 | 223 | 338138 | 345714 |
| zone_frost_slope2 | 248 | 205 | 341887 | 381904 |
| zone_volcano | 132 | 221 | 223802 | 308178 |
| zone_volcano2 | 271 | 132 | 216027 | 210488 |
| zone_frost_realm | 137 | 143 | 144298 | 171498 |

The volcano is mixed: one view is +89 calls and the other is -139. Treat it as unproven. Bucket the ring by angle (8 sectors) rather than by a square grid. See README_R2.
