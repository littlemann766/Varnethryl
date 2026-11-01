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

---

# Loot phase 2 (Beth): gear, fuller drops, shops

New files (copy the whole `loot/` folder to `res://loot/` as before):

| Path | What |
|---|---|
| `gear/gear.json` | 72 equippable items: id, name, slot, family, tier (1 common / 2 rare / 3 epic), stats, value, sell (30%), icon, mesh, mesh_lod1, `heroes` (which heroes can wear it), tris, size. `hero_classes` maps each hero to weapon family, hand(s), armor weight and shield. |
| `gear/gear_attach.json` | Per hero, per slot: `bone`, `position`, `rotation` (quaternion xyzw), `scale`, all bone-local. Computed from each hero's skinned rest pose in `res://voxel/<id>_voxel.glb` (Lucian's rigs were not edited). |
| `gear/meshes/<id>.glb` + `_lod1` | One mesh per item. Origin = attach pivot: weapons at the grip (blade/shaft along +Y), helmets at the shell centre, chest pieces at 62% of torso height, shields at the handle, rings at the band centre, amulets at the top of the chain, collars at the ring centre. Front faces +Z. Vertex colours (COLOR_0) + one emissive material (`vox_glow`), same as phase 1. |
| `gear/icons/<id>.png` | 256 px icons with the rarity frame and tier pips baked in. |
| `drop_tables.json` | v2: replaces v1 (same keys, plus `holyknight_villain`). |
| `shops.json` | 7 shops: stock, buy/sell, restock rules, rotating stock, services. Replaces the `shops` block in `items.json` (leave that block unused). |
| `merchants/merchant_<type>.glb` + `_lod1` | smith, provisioner, shipwright, apothecary. Two nodes, `<type>_body` and `<type>_arm_R` (pivot at the shoulder). One looping animation, **`idle`** (smith hammers, 1.2 s; the others gesture, 3 s). About 1.8 m tall, front +Z. |
| `merchants/stall_<type>.glb` + `_lod1` | The matching stall (anvil and forge, canopy market stall, timber and rope yard, canopy and bottle shelves). About 3.2 x 2.0 m, counter at the front (+Z). |
| `merchants/PLACEMENT_merchants.json` | World positions and yaw for the 7 exterior stalls and their NPCs. |
| `PRICING_SANITY.md` | Prices against the 5-gold toll and a 10-gold day wage, plus kills needed per tier. |

## Gear wiring
1. **Load.** Add `gear.json` to the `Loot` autoload next to `items.json`. Each gear id is an inventory item (stack 1). Save the equipped set per hero: `state.equipped[hero_id] = {slot: gear_id}`, using the slots `weapon, weapon_offhand, head, chest, shield, ring, trinket, collar`.
2. **Who can equip what.** Only allow `item.heroes.has(hero_id)`. Dual-wielders (nyx daggers, asha cestus) put the same item in `weapon` and `weapon_offhand`. Wren uses a single dagger. Pip and Phoenix only take `collar`.
3. **Showing it on the model.** On equip, for each slot in `gear_attach.json.heroes[hero_id].slots` add a `BoneAttachment3D` (bone_name = `bone`) under the hero's Skeleton3D, with a child holding the mesh: `transform = Transform3D(Basis(Quaternion(rotation[0],rotation[1],rotation[2],rotation[3])) * Basis.from_scale(Vector3(scale)), Vector3(position))`. Use `mesh_lod1` on the Low tier, like `apply_quality()` does. `weapon_offhand` reuses the weapon mesh. The ring and trinket share the hand_R and chest bones.
   - Cedric's lute attaches to `chest` (slung on his back). Move it to `hand_R` with the weapon transform from the `weapon_offhand` math if you want it in hand while strumming.
   - Chest pieces are rigid shells on the `chest` bone with non-uniform scale fitted to each torso. Turn on cape_clamp or leave the cloth as is; capes stay outside them.
   - **Baked weapons.** Some voxel heroes already have a weapon in their mesh (Darius's sword shows in the sheets). While a gear weapon is equipped, either hide it (needs a weaponless variant from Lucian, which I didn't touch) or skip the gear weapon mesh for those heroes and only apply its stats.
4. **Stats.** Weapon `atk` maps onto `base_item` atk (see Phase 2b below for the tier jumps and T3 perks). Head, chest and shield `def` add together. Extra keys: `crit_pct`, `on_hit` (bleed, burn_3s, frost_slow, stagger, pierce, shock, snare, riposte, mp_on_hit, party_atk_5pct), `skill_pct`, `aura_heal`, `mp_pct`, `mp_regen_pct`, `dodge_pct`, `speed_pct`, `poise`, `*_res_pct`, `block_pct`, `hp_regen`, `revive_once_per_day`, `atk_pct`, `companion_hp_pct`, `companion_atk_pct`. Anything you don't support yet can be ignored, because atk and def carry the balance.
5. **Legacy items.** The phase 1 weapons and armour in `items.json` (rusted_shortsword ... ashwalker_mail, iron_buckler) stay as loot. Treat them as "any hero" gear in the `weapon`/`chest`/`shield` slots that shows no mesh (stats only), or sell-only.

## Drop wiring (drop_tables.json v2)
- Entry types: `{item, chance_pct, count}` (from `items.json`), `{gear_tier, chance_pct, slot?, for_party}`, and `{rarity, chance_pct}`.
- For `gear_tier`, pick a random `gear.json` item of that tier (and slot, if one is given) whose `heroes` includes someone in the current party. Re-roll up to 3 times toward heroes the player owns.
- `choice_of` on bosses (vaelthryx, hydra, titan) now means 3 T3 gear pieces for the party, shown in the pick-1-of-3 panel.
- `first_kill`, `repeat` and `gold_repeat` work as before. Add the pity counters from `pity`: normal enemies guarantee a T1 gear drop after 40 kills without one, and elites guarantee a T2 after 15. Save them in `state.loot_pity`.
- `holyknight_villain` has its own entry. enemy.gd uses raider data for it, so key the drops by `type_id`.
- The gear pickup is `pickups/drop_bag.glb` with the rarity beam, like phase 1.

## Shop wiring (shops.json)
- **NPCs.** Spawn each exterior stall and NPC from `merchants/PLACEMENT_merchants.json`. A `y` of null means snap to the ground at (x, z). The NPC sits at `npc.local_offset` in the stall frame, plays `idle` on loop, and shows a "Trade" prompt within 2.5 m.
  - The town positions are the card2 building fronts from the DEFS in `main.gd`, plus about 2.5 m.
  - The Saltglass stall is on the west cove quay next to the harbormaster hut.
  - Gullhaven is 8 m inland of the pier head, where `tw_sea.gd` already opens the Shipwright. Put the NPC on that prompt.
  - Frostreach and Vent Harbour use their dock props. Snap them to walkable ground within 8 m, and check them in a shot, because I could not walk-test them.
- **Buy and sell.** The buy price is `stock[].buy`, already including the shop markup: 1.0 in town, 1.15 at Saltglass, 1.25 at Frostreach and Vent. When the player sells, the merchant pays `floor(value * sell_pct[slot or '*'] / 100)`, at least 1. That is 25-40% depending on the shop's trade. Key and legendary items can't be sold. T3 gear is never stocked but can be sold.
- **Restock.** `daily` refills to `qty` at in-game dawn, `weekly` every 7 in-game days, and `once` never refills. Each `rotating` block picks `slots` random ids from `pool` each period at the listed `prices`. Buyback: whatever the player sold stays buyable at the price they got until the next dawn.
- **Services.** The blacksmith repairs at 5% of value and forges at 50 x level + forge shards. Ship tiers stay in `tw_sea.gd` COST, unchanged.
- **Interiors (yours).** If you'd rather run the town shops inside, put the same merchant mesh behind the interior counter of smithy, market and apothecary, about 1.0 m behind the counter front and facing the door. Use the shop id from `shops.json` (`town_blacksmith`, `town_provisioner`, `town_apothecary`) and drop the matching exterior stall. I didn't touch any interior file.

## Phase 2 LOD (lod1 / High tris)
All 72 gear meshes are at or under 50% (range 24-43%). Merchants are 25-29%, and stalls 26-28%. Per-item figures are in `gear.json` (`tris`).

## Phase 2b: badass pass (look + stats)
- **Look:** helmets are the hero piece.
  - Heavy: T1 Iron Bascinet is now a flat-topped great helm with an eye slit and breaths. T2 Steel Barbute is a blackened houndskull visor bascinet with a mail aventail. T3 Great Helm of the Vale is a gilt great helm with horns, a crest and a glowing eye slit.
  - Medium: nasal helm, then a spectacle guard, then T3 with a crest and swept wings.
  - Light: shadowed hoods (the face is in darkness), a half-mask at T2, and a gilt spiked circlet at T3.
  - Chest pieces gain gorgets, flared layered pauldrons, fur mantles on heavy and cloth mantles or capes on medium and light, plus lames and a peascod ridge.
  - All metal has battle wear (dents, scratches, rust on T1).
  - Palettes: T1 worn iron, T2 blackened steel with brass, T3 dark steel with gilt and a glow accent.
  - **The attach pivots didn't change**, so `gear_attach.json` works as before.
- **Tier jumps:** weapon ATK is 20 / 42 / 75 (x family multiplier). Chest DEF is heavy 15/32/55, medium 11/23/40 and light 7/15/26, and helmets give 45% of that. Shield block is 12/22/34%. T2 weapons add `atk_speed_pct` 5, and T2 armour adds `poise` +0.05.
- **T3 perks:** every tier 3 item has a unique `perk` {name, key, value, desc} in `gear.json`. Show the name and desc in the tooltip. Implement them by `key`; anything not done yet can show as "(coming soon)".

| T3 item | Perk | Key | Effect |
|---|---|---|---|
| Saltglass Longsword | Brine-Edge | `lifesteal_pct` = 6 | Heal 6% of damage dealt. |
| Duelist's Swept-Hilt Rapier | Riposte | `perfect_block_counter_pct` = 150 | After a perfect block, the next hit deals 150% and always crits. |
| Rimeforged Zweihander | Glacier Cleave | `charged_frost_wave` = 1 | Fully charged swings send a frost wave that slows by 40% for 3 s. |
| Saltglass Misericorde | Mercy Stroke | `execute_below_hp_pct` = 15 | Hits on non-boss enemies under 15% HP kill them outright; bosses take +30% instead. |
| Emberwrought Axe | Ember Bite | `burn_on_hit_pct` = 25 | 25% chance per hit to burn for 3 s (stacks 3x). |
| Hallowed Flanged Mace | Hallowed Ring | `stagger_heal_party_pct` = 3 | Staggering an enemy heals the party 3% max HP. |
| Saltglass Partisan | Tidebreaker | `pierce_targets` = 3 | Thrusts pierce up to 3 enemies and ignore 20% defence. |
| Starglass Staff | Starfall | `skill_cdr_pct` = 15 | Skill cooldowns -15%; every 5th skill cast is free. |
| Rime Reaper | Winter Harvest | `kill_restores_sp_pct` = 20 | Kills restore 20% SP and chill nearby enemies. |
| Glasswyrm Recurve | Wyrmglass Arrow | `crit_dmg_pct` = 40 | +40% crit damage; crits ricochet to a 2nd target. |
| Stormsilk Arbalest | Stormbolt | `chain_lightning_targets` = 3 | Bolts chain lightning to 3 nearby enemies. |
| Court Lute of Gullhaven | Ballad of the Tide | `party_atk_pct` = 12 | Party +12% ATK while Cedric plays; nearby allies regen 1% HP/s. |
| Coil-Scale Lash | Coilbind | `snare_s` = 2.5 | Lash roots enemies for 2.5 s (bosses: 40% slow). |
| Ember Cestus | Furnace Fists | `combo_burn_ramp_pct` = 5 | Each hit in a combo adds +5% damage (max +50%) and the 10th hit explodes. |
| Warden's Silk Hood | Warden's Sight | `crit_pct` = 12 | +12% crit and enemies' weak points glow. |
| Rimeguard Helm | Rimeguard | `frost_immune` = 1 | Immune to frost slow and freeze; +30% frost resist. |
| Great Helm of the Vale | Dread of the Vale | `fear_on_hit_taken_pct` = 10 | +25% poise; when hit, 10% chance to make the attacker cower for 1.5 s. |
| Starsilk Vestment | Starsilk Ward | `spell_shield_pct_hp` = 20 | Every 20 s, a shield absorbs damage up to 20% max HP. |
| Brigandine of the Watch | Watchman's Reflex | `dodge_heal_pct` = 4 | Perfect dodges heal 4% max HP and refund 15 SP. |
| Rimewarden Harness | Thornplate | `thorns_pct` = 25 | Reflect 25% of melee damage taken; frost resist +30%. |
| Gullhaven Kite Shield | Seawall | `block_reflect_pct` = 40 | Blocks reflect 40% of the blocked damage; can block boss slams. |
| Saltglass Seal Ring | Seal of the Deep | `crit_heal_pct` = 2 | Crits heal 2% max HP. |
| Glasswyrm Locket | Last Light | `revive_once_per_day` = 1 | Once per in-game day, survive a killing blow at 30% HP. |
| Starsilk Collar | Bonded Spirit | `companion_shares_dmg_pct` = 20 | Companion takes 20% of the leader's damage and never despawns. |
