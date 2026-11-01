# Pricing sanity check (loot phase 2)

Scale anchor: the old Saltglass lift toll was **5 gold** a ride (150 for a season pass), bread and cheese is 4, a room at the inn 10. A labourer's day wage is set at **~10 gold**, so a toll is half a day's pay, like a medieval bridge or ferry toll.

| Item | Value (g) | = tolls (5 g) | = days' wages (10 g) |
|---|---|---|---|
| bread_cheese | 4 | 0.8 | 0.4 |
| minor_healing_draught | 15 | 3.0 | 1.5 |
| rusted_shortsword | 25 | 5.0 | 2.5 |
| iron_arming_sword | 60 | 12.0 | 6.0 |
| iron_cuirass | 90 | 18.0 | 9.0 |
| steel_knightly_sword | 420 | 84.0 | 42.0 |
| steel_breastplate | 650 | 130.0 | 65.0 |
| saltglass_longsword | 2400 | 480.0 | 240.0 |
| rimewarden_harness | 3200 | 640.0 | 320.0 |
| oar_bank | 600 | 120.0 | 60.0 |
| bronze_ram_prow | 2000 | 400.0 | 200.0 |

Historical check: a plain sword cost roughly a week of an ordinary worker's pay; a good steel blade or a breastplate a month or more; a fine named harness the better part of a year, which is why knights' kit came from lords, loot or inheritance. Tier 1 (6-9 days), Tier 2 (4-9 weeks) and Tier 3 (8-11 months, drop-only) follow that curve.

## Earning rate (drop_tables.json expected value per kill: gold + 30% resale of drops)

| Enemy | Tier | Gold | Exp. gold/kill | Kills for a T1 weapon (60) | Kills for a T2 weapon (420) |
|---|---|---|---|---|---|
| wolf | normal | 0-2 | 6.0 | 10.0 | 70.2 |
| raider | normal | 3-9 | 10.1 | 6.0 | 41.7 |
| holyknight_villain | normal | 8-18 | 19.5 | 3.1 | 21.5 |
| hob_enforcer | normal | 12-28 | 31.5 | 1.9 | 13.3 |
| wraith | normal | 4-12 | 11.9 | 5.0 | 35.2 |
| skeleton | normal | 12-30 | 45.5 | 1.3 | 9.2 |
| frosttroll | elite | 60-110 | 183.3 | 0.3 | 2.3 |
| stonetroll | elite | 60-110 | 171.7 | 0.3 | 2.4 |
| frosttroll_a | boss | 150-150 | 537.4 | 0.1 | 0.8 |
| frosttroll_b | boss | 150-150 | 537.4 | 0.1 | 0.8 |
| coil | boss | 400-400 | 775.0 | 0.1 | 0.5 |
| glasswyrm | boss | 600-600 | 1270.5 | 0.0 | 0.3 |
| vaelthryx | boss | 800-800 | 875.6 | 0.1 | 0.5 |
| hydra | boss | 800-800 | 893.6 | 0.1 | 0.5 |
| titan | boss | 1500-1500 | 1500.0 | 0.0 | 0.3 |

Starting gold 100 buys one T1 weapon plus potions. Selling at 25-40% means a T1 sword sold back returns 21 g (2 days), so farming the shop is never profitable; remote ports add 15-25% markup (carriage costs) and pay more for local materials (35-40%).