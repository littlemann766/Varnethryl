# Equipment & Loot Design v1.0: mapping to what exists (Phase 0)

Beth (art and data). Source spec: `/workspace/specs/Varnethryl_Equipment_Loot_Design_v1.0/`. Everything here is data or art. Lucky owns all code.

## 1. What exists today
| Area | Where | State |
|---|---|---|
| Loot phase 1 items | `beth/loot/items.json` (51), `chest_loot.json`, `pickups/`, `chests/` (5 chest models with an `open` anim), `ship_addons/` | Proposed data. Not wired yet. |
| Hero gear (phase 2/2b) | `beth/loot/gear/gear.json` (72 items, tiers 1-3, T3 perks), `gear_attach.json` (bone, offset per hero), `meshes/`, `icons/` | Proposed. Helmet + chest + weapon + shield + ring + amulet + collar only. |
| Drops v2 | `beth/loot/drop_tables.json` (15 enemy ids + aliases, `gear_tier` rolls, pity) | Proposed. |
| Shops | `beth/loot/shops.json` (7 shops), `merchants/` (4 NPC + 4 stalls), `PLACEMENT_merchants.json` | Proposed. |
| Godot save | `vmain/core/save/save_system.gd`: `state.gear` (array of `{id, slot, base, level, affixes, perks}`), `state.loadouts[heroIdx] = {weapon, armor, charm}`, version 1, same keys as the JS save | **Live data. Must be migrated, never overwritten.** |
| Existing enhancement/ascension | JS `varn-core/www/core/items.js` + `data.js` TIERS: `tier = TIERS[floor(level/3)]`. +0 Uncommon (0 substats), +3 Rare (2), +6 Epic (3), +9 **Mythic** (4), +12 Legendary (5), +15 Masterwork (5). Substats from `SUBSTAT_POOL` (8 stats with min/max/step/cap). Each substat has `boost` (independent +10 cap). Ability unlocks at +3. Cost `100+level*120` gold + `2+floor(level*1.5)` shards. Equipment HP bonus capped at +28%. | Live in JS. The Godot port has only a stand-in `base_item()`. |
| Hero rigs | `vmain/voxel/<id>_voxel.glb` (+`_lod1`), Lucian's. Single skinned mesh. Bones `root,hips,spine,chest,neck,head,shoulder_*,upperArm_*,foreArm_*,hand_*,thigh_*,shin_*,foot_*` (+ cape/tail/hair chains). Embedded clips `idle, walk, run, attack1-3 / attack, skill, hit, death, fly_*` (pip: `jump, trot`). | Read only. |
| Enemies | `combat_data.json` ENEMIES + `enemy.gd` TYPES: wolf, raider, hob_enforcer, wraith, skeleton, frosttroll(+_a/_b), stonetroll, titan/titan40/titan_volcano, vaelthryx (= **Balthrix**), hydra (= **Hydrella**, the Five-Headed Hydra), holyknight_villain; sea bosses coil, glasswyrm (tw_sea) | Cinder (Phoenix boss) does not exist in Godot yet. |

## 2. Spec to existing
| Spec item | Maps to | Action (mine = data/art, Lucky = code) |
|---|---|---|
| 14 slots | Today: weapon/armor/charm (save), and gear.json weapon, weapon_offhand, head, chest, shield, ring, trinket, collar | New slot ids: `helmet, chest, shoulders, gloves, legs, boots, belt, cloak, amulet, ring1, ring2, main_hand, off_hand, class_item`. Old to new: head->helmet, chest->chest, weapon->main_hand, weapon_offhand/shield->off_hand, ring->ring1, trinket->amulet. Save `armor`->chest, `charm`->class_item (keeps the class relic `relicLevels` +10 rule). Companion collar is a `companion_accessory` (not one of the 14). |
| Item definition vs instance | gear.json/items.json are definitions only. Save `gear[]` entries are instances. | `equipment/item_definitions.json` (schema v1) + `instance_template` and `migration` in `equipment/migration_v0_to_v1.json` |
| 6 armor families | gear.json heavy/medium/light | heavy->plate (Aldric, Seraphine, Darius, Owner, Orin), heavy->**scale** (Garruk, Rook), medium->**chain** (Finn, Vesper, Brynn, Elira, Morwen), medium->leather (Nyx, Asha, Wren, Cedric), light->cloth (Rowan, Thorne, Talia, Kael), light->**mystic** (Mirelle, Selene). This is the hero's *proficient* family. Any hero can wear any family at `efficiency` 0.85 (spec: proficiency, not a lock). |
| 6 rarities + colours | gear.json tiers 1-3, items.json rarity common/uncommon/rare/epic/legendary | The spec keeps the current naming: **gray = Uncommon (lowest), green = Common**. Phase 1 `items.json` had these two swapped (common gray, uncommon green), so its colours are corrected in `rarity.json`. Old gear: T1->uncommon, T2->rare, T3->epic. Legendary/Masterwork models are new. |
| Rarity looks (not a recolour) | b9510d5 tier looks | uncommon = worn iron, plain; common = iron with leather/brass straps and rivets; rare = blackened steel, brass trim, raised edges; epic = dark steel, gilt, flared/spiked silhouette, faint glow; legendary = gilt and filigree, crest/horns/wings, glow runes; masterwork = blackened-red "forge-scarred" steel, molten glow seams, the largest silhouette (crown spikes, double pauldrons). Each step adds geometry, not just colours. |
| +15 / +10 / ascension | JS TIERS | **Conflict to confirm with the boss.** The spec's 6 rarities with milestones 3/6/9/12/15 (Legendary at +12, Masterwork at +15) fit the existing ascension track, but the JS track today is Uncommon, Rare, Epic, **Mythic**, Legendary, Masterwork. The spec list has **Common** and no Mythic. `enhancement.json` ships both: `ascension_track_v1_spec` (uncommon +0, common +3, rare +6, epic +9, legendary +12, masterwork +15) and `ascension_track_v0_live` (exactly the current JS). `active_track` defaults to **v0_live**, so nothing changes silently. Switching is one field once the boss confirms. Substat slots 0/2/3/4/5/5, the +10 per-substat cap and the +28% HP cap are kept in both. |
| Base STR/DEF/AGI/MAG fixed | combat_data KITS/PLAYER | Gear only adds modifiers (`baseStats` on definitions are gear stats, never hero base). |
| Drop-rate baseline + pity | drop_tables v2 `gear_tier`, `pity` | `equipment/loot_rules.json`: the rarity baseline 55/25/14/5/0.9/0.1 for ordinary loot, per-content-tier multipliers, a separate exclusive-item roll per boss, pity per exclusive (persisted server-side), first-clear guarantees. drop_tables v2 `gear_tier` 1/2/3 maps to rarity floors uncommon/rare/epic. |
| Need/Greed/Pass, trade/bind | none | `loot_rules.json` `shared_boss_loot` + `trade_rules`. `bindingRule` and `tradeable` are on every definition. |
| Sets, gems, runes, artifacts, crafting, materials, boss themes | items.json materials, shops services | `sets.json`, `gems_runes.json`, `artifacts` (in item_definitions), `crafting.json` (6 professions, facilities mapped to existing buildings), `materials` (in item_definitions), `boss_loot.json` |
| Shops | shops.json | Kept. Stock ids are remapped via `migration_v0_to_v1.json.id_map` (old gear ids -> new itemIds). |
| Inventory UI | none in Godot | `equipment/ui/` art (slot frames, rarity borders, panels) for Lucky |

## 3. Sslythar stays hidden: checked
- Godot (`vmain`): no Sslythar model, enemy, roster entry or spawn exists (grep: 0 hits). Nothing to hide.
- JS (`varn-core/www/proto3d/main.js:883`): the roster loop skips `ssylthar` ("remains an unreleased creature while the serpentine rig is refined"). It is still hidden.
- My data: `boss_loot.json.sslythar` has `"visibility": "hidden"` and `"enabled": false`. Voidfang, `dragon_core` and `abyssal_scale` carry `sourceTags: ["sslythar","hidden"]`. They appear in **no** drop table, chest, shop or crafting recipe, so normal gameplay cannot grant them. No Sslythar art was made. Note: varn-core calls Sslythar a basilisk, not a dragon, while the spec says "ancient dragon/void". I kept the spec's names and flagged it for the boss.
- Pip, Phoenix and the companions Luna and Peaches are special companions, not random drops (spec 16). Collars are companion accessories, and Luna/Peaches items are `bind_on_pickup` with source `quest` only.

## 4. Migration and rollback (save data)
- Never write to `guildbound_rpg_save_v1` in place. Lucky's migrator reads v1, writes `equipment_v1` into a **new** key `state.equipment` (inventory instances + `equipped[heroIdx][slot]`), keeps the old `gear`/`loadouts` untouched, and sets `state.equipmentSchema = 1`.
- Rollback: delete `state.equipment` and `equipmentSchema`, and the old fields still work. Before migrating, back up to `user://backup_pre_equipment_v1_<unix>.json`.
- Per old instance: `itemId = id_map[old.base_item]` or a generic `legacy_<slot>_<rarity>`. `enhancement = level`, rarity from the active ascension track at that level. `substats[] = {stat: id_map_stat[id], value, enhancement: boost}`. `ability` -> `specialEffectId`. `lock` is kept.
- Details are in `migration_v0_to_v1.json`.
