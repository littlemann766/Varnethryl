# Loot kit for Lucky (Beth, loot plan v1)

Everything here is **proposed values** from the Loot Plan Page. Copy this folder to `res://loot/` (the icon and pickup paths in `items.json` assume that). The boss approved the plan; nothing touches main, and none of your or Lucian's files were edited.

## Files
| Path | What |
|---|---|
| `items.json` | 51 items: id, name, slot, kind, rarity, stats, buy, sell, stack, icon, pickup. Also `starting_gold` = **100**, `shop_buyback_pct` = 25, rarity colours and weights, shop stock lists, and the existing ship tier costs (unchanged). |
| `drop_tables.json` | Per enemy, keyed by `combat_data.json` ENEMIES ids / `Enemy.type_id`: gold range, `drops` (chance %, count), `first_kill`, `repeat`, `choice_of`. |
| `chest_loot.json` | 16 chests: name and region (these match the stage5 POI names), gold, fixed first-open items, `one_of`, `requires_item`, `chest_type` (which mesh to use), `weekly_refill`. |
| `icons/<id>.png` | 59 icons, 256 px, with the rarity frame baked in: 51 items plus gold_coins, gold_pouch, forge_shards, ship_t1..t3, drop_bag and material_bundle. `_frame_<rarity>.png` are the empty frames. |
| `pickups/*.glb` (+`_lod1`) | World drops: gold_pouch, gold_pile, drop_bag, material_bundle, potion, and one per material (driftwood, coil_scale, saltglass, stormsilk_bolt, glasswyrm_shard, wolf_pelt, iron_ore, hob_tusk, troll_hide, rime_shard, ash_ember, titan_magma_core). About 0.4 m, origin at the base. |
| `chests/<type>.glb` (+`_lod1`) | sea_chest, iron_strongbox, frozen_chest, scorched_chest, crate. Each has two nodes (base and lid) and one animation, **`open`** (0.73 s, lid swings to 110° with a small overshoot). The front faces +Z, and the inside has an emissive gold heap. About 1.0 x 0.6 x 0.64 m. |
| `ship_addons/upg_<ship>_<addon>.glb` (+`_lod1`) | galleon: copper_hull, ram_prow, lantern. skiff: copper_hull, ram_prow, lantern, oar_bank. |

Materials use vertex colours (COLOR_0, linear) with one emissive material for the glowing voxels.

## LOD (lod1 / High tris, all at or under 50%)
| `sea_chest.glb` | 6080 | 1628 | 26% |
| `iron_strongbox.glb` | 6080 | 1628 | 26% |
| `frozen_chest.glb` | 6080 | 1628 | 26% |
| `scorched_chest.glb` | 6080 | 1628 | 26% |
| `crate.glb` | 4920 | 1336 | 27% |
| `upg_galleon_copper_hull.glb` | 3392 | 1024 | 30% |
| `upg_galleon_ram_prow.glb` | 2144 | 608 | 28% |
| `upg_galleon_lantern.glb` | 1416 | 320 | 22% |
| `upg_skiff_copper_hull.glb` | 6960 | 1896 | 27% |
| `upg_skiff_ram_prow.glb` | 2144 | 608 | 28% |
| `upg_skiff_lantern.glb` | 1416 | 320 | 22% |
| `upg_skiff_oar_bank.glb` | 2364 | 996 | 42% |
| `pickups/ash_ember.glb` | 1336 | 380 | 28% |
| `pickups/coil_scale.glb` | 820 | 232 | 28% |
| `pickups/driftwood.glb` | 784 | 248 | 31% |
| `pickups/drop_bag.glb` | 1856 | 544 | 29% |
| `pickups/glasswyrm_shard.glb` | 1240 | 384 | 31% |
| `pickups/gold_pile.glb` | 1464 | 408 | 27% |
| `pickups/gold_pouch.glb` | 1588 | 456 | 28% |
| `pickups/hob_tusk.glb` | 644 | 204 | 31% |
| `pickups/iron_ore.glb` | 1524 | 428 | 28% |
| `pickups/material_bundle.glb` | 1280 | 392 | 30% |
| `pickups/potion.glb` | 1528 | 432 | 28% |
| `pickups/rime_shard.glb` | 1240 | 384 | 31% |
| `pickups/saltglass.glb` | 1240 | 384 | 31% |
| `pickups/stormsilk_bolt.glb` | 1744 | 492 | 28% |
| `pickups/titan_magma_core.glb` | 2400 | 688 | 28% |
| `pickups/troll_hide.glb` | 1288 | 424 | 32% |
| `pickups/wolf_pelt.glb` | 1304 | 392 | 30% |

## Boat add-on placement (bow = +Z, like TwShip)
- `upg_galleon_copper_hull`: Two copper sheathing strips at the waterline, centred on the hull; bow = +Z in Godot. Tune X width / Y offset to the hull.
- `upg_galleon_ram_prow`: Bronze ram; the point faces the bow (+Z in Godot). Place at the cutwater just above the waterline.
- `upg_galleon_lantern`: Stern lantern; the glow voxels are emissive. Add an OmniLight3D (range 12 m) at its centre for night sailing.
- `upg_skiff_copper_hull`: Two copper sheathing strips at the waterline, centred on the hull; bow = +Z in Godot. Tune X width / Y offset to the hull.
- `upg_skiff_ram_prow`: Bronze ram; the point faces the bow (+Z in Godot). Place at the cutwater just above the waterline.
- `upg_skiff_lantern`: Stern lantern; the glow voxels are emissive. Add an OmniLight3D (range 12 m) at its centre for night sailing.
- `upg_skiff_oar_bank`: Skiff oar bank: 3 oars per side across the hull, centred amidships. Animate a sweep (rotate about Z at the hull edge) during the burst.
Load them like `set_tier()` does, for example a `TwShip.addons` array attached under `vis` when the item is owned (`sea.items` / inventory).

## Code list
1. **Item DB and inventory.** Load `items.json` once (an autoload such as `Loot`). Keep gold in the existing `VSave.state.gold`. Set `fresh_state()` gold from 1250 to `starting_gold` (100); this is your file, so it's your change. Use one inventory dictionary `state.inventory` {id: count} that respects `stack`. Weapons, armor and charms should become gear entries so they fit the existing `gear`/`loadouts` (map `stats.atk`/`def` onto `base_item`). The archived Beth `wallet_stub.gd` API (`coins / add_coins / pay / give_item / buy`) is a fine interface shape.
2. **Gold sources.** Enemy kills (drop tables), chests, quest rewards (50-500 per quest step, your call per quest), selling at 25%, and the boss first-kill bonus. Show a "+N gold" HUD toast.
3. **Drop spawning.** On `Enemy.died`, look up `drop_tables.json` by `type_id`. `stonetroll` has its own entry even though enemy.gd uses frosttroll data, and `titan40` / `titan_volcano` map to `titan` through `aliases`. Roll gold once, and roll each drop by `chance_pct` and `count`. For `rarity` entries, pick a random item of that rarity. `first_kill` and `gold` apply on the first kill and `repeat` / `gold_repeat` after that (save `bossKills` per id). Spawn pickups at the corpse with a bob and spin plus a rarity-colour light beam (colour from `items.json` rarity). Collect them by walking over them or auto-collect within 2 m, and auto-collect after 60 s so nothing is lost. Bosses (`choice_of`) show a pick-1-of-3 panel.
4. **Chest opening.** Spawn `chests/<chest_type>.glb` at each POI chest from the stage5 manifest (match by name). On interact, check `requires_item`, play `open`, give gold and items, and set `state.chests_opened[id] = true`. If `weekly_refill` is not null, re-roll small loot every 7 in-game days. `one_of` means pick one list at random. The Sunken Ward vault also rolls one epic armor piece (`epic_armor_roll`). Interior chests are yours, so use the `interior_chest` entry.
5. **Shops.** Use the `shops` block in `items.json`: buy at `buy`, sell at `sell` (25%, so sell = round(buy/4) where buy exists), and key/legendary items can't be sold. Add vendor NPC interact points at the smithy, apothecary, inn, Gullhaven shipwright, the Saltglass harbormaster hut and Frostreach, plus a repair service (5% of price) and forge cost (50 x level gold + shards).
6. **Giving out boat materials.** Ship upgrades already read `sea.items` with display-name keys ("Driftwood", "Coil Scale", "Saltglass", "Stormsilk Bolt", "Glasswyrm Shard"). Every material item that feeds the Shipwright has `sea_item_key`. When one is picked up, also add it to `state.sea.items[sea_item_key]`, or switch `upgrade()` to read the shared inventory (only one source of truth, please). The **Brinecrown Coil** and **Glasswyrm** entries in `drop_tables.json` supply Coil Scale, Stormsilk Bolt and Glasswyrm Shard. Driftwood comes from chests, the Shipwright and beach pickups (`pickups/driftwood.glb`). Without these, T2 and T3 can't be reached.
7. **New ship add-ons** (`ship_addon` items): buy them at the Shipwright using `cost_items`. Copper Hull needs `requires_item` = the plans from the Scorched Chest. Effects are in `stats` (shallows damage -50%, ram damage, oar burst 20 s, lantern +50% night range).
8. **Inventory UI.** A grid using `icons/<id>.png` (frames are baked in), sorted by slot, showing count and sell value on tap. The phone layout needs a 4-column grid with 72 px tiles.
