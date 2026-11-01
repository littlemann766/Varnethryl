# README for Lucky — Equipment & Loot v1.0 (code plan)

Spec: boss package `Varnethryl_Equipment_Loot_Design_v1.0` (DESIGN_SPEC, ITEM_DATA_SCHEMA, LOOT_AND_ECONOMY_RULES, ARMOR_3D_PIPELINE, IMPLEMENTATION_PLAN, QA_CHECKLIST).
Mapping to the current game: `MAPPING.md` (read first). Everything here is art + data on `beth-world-art`; all code is yours. Nothing is wired into main.

Mount: copy/merge `www/proto3d/models/beth/equipment/` to `res://equipment/` (and keep `loot/` at `res://loot/` from phase 2). All paths in the JSON are `res://equipment/...` / `res://loot/...`.

## What's in the box
| Path | What |
|---|---|
| `data/item_definitions.json` | 594 definitions, each validated against ITEM_DATA_SCHEMA `itemDefinition` (jsonschema). Definitions only; instances live in the save. |
| `data/instances_example.json` | 4 schema-valid `itemInstance` examples (enhancement, ascension, substats, sockets, boundTo). |
| `data/rarity.json` | 6 rarities (gray Uncommon is lowest → red Masterwork), item level, stat mult, substat count, sockets, drop baseline, loot beam (colour/height/pulse/sound key), look name. |
| `data/substats.json` | 12 substats with per-rarity [min,max], per-substat cap (+10 enhancement), total caps (VIT 28 = the live +28% HP cap), family roll weights. |
| `data/affixes.json` | 19 prefix affixes with bounded per-rarity ranges; 8 elements + counter table, resist cap 60%, no multiplicative stacking. |
| `data/sets.json` | 18 active sets (3 per family: epic/legendary/masterwork), 6 pieces each, 2/4/6 milestones; 9 more spec concepts listed. |
| `data/enhancement.json` | +15 cap, substat +10, milestones 3/6/9/12/15, Legendary@12, Masterwork@15. **`active_track: ascension_track_v0_live`** = today's items.js rules, verbatim. `ascension_track_v1_spec` ships beside it; switching needs the boss's yes. Per-level cost table (gold/shards/material/success%, no destroy on fail). |
| `data/gems_runes.json` | 12 gems x 7 qualities, 3→1 combine with cost/success/fail rule, sockets by rarity, 8 runes. |
| `data/crafting.json` | 6 professions + Mystic Forge, facility→building map, 265 recipes, forge ops (reroll, replace-one, unlock socket, transfer cap), boss recipes (Voidfang disabled). |
| `data/boss_loot.json` | Ashen Titan, Frost Troll Brothers, Balthrix, Hydrella enabled; Cinder (not in Godot yet) and **Sslythar disabled**. Exclusive roll separate from rarity roll, pity, first-clear guarantee. Godot ids per boss. |
| `data/loot_rules.json` | Ordinary baseline 55/25/14/5/0.9/0.1, elite/boss/chest tables, rarity pity, Need/Greed/Pass, participation, binding, trade safety, hidden list. |
| `data/weapon_types.json` | 14 weapon types that have animations today → hero list, hands, occupancy. Spec types without animations are listed and must stay out of loot. |
| `data/migration_v0_to_v1.json` | Old save → `state.equipment`: slot map, tier/rarity map, stat map, backup key, rollback. |
| `appearances.json` | appearanceId → meshes/parts/lod1/icon/border/hide rule. |
| `meshes/<family>/` | 324 wearable part meshes + lod1 (8 slots x 6 families x 6 rarities; R parts mirror the L mesh). `meshes/companion/collar_<rarity>`. |
| `fit/armor_attach.json` | Per hero (22 playable), 14 parts: bone + bone-local transform; hide rules. `fit/companion_attach.json`: Pip, Phoenix. |
| `icons/` | 128 px icons, transparent, no frame baked in (draw `ui/tile_bg_<r>` + icon + `ui/border_<r>`). |
| `ui/` | Rarity borders, tile backgrounds, loot-beam strips, 14 slot frames with silhouettes, equipment panel, tooltip frame, `ui_theme.json` (9-slice margins, paper-doll layout). |
| `FIT_AND_HIDE.md` | Fit + hide rule details, baked-weapon list for Lucian, fixed old issues. |
| `tools/` | Generators (data, meshes, fit, icons) + `tools/godot/dress.gd`: reference equip/hide harness used for the clip checks. |

## Phase plan (follows IMPLEMENTATION_PLAN)

### Phase 0 — audit (done on the art side, check it)
- MAPPING.md covers: existing `varn-core/www/core/items.js` + `data.js` enhancement (tier from floor(level/3), SUBSTAT_POOL, boost ≤10, costs), Godot save `core/save/save_system.gd` (`guildbound_rpg_save_v1`, `gear[]`, `loadouts[heroIdx]={weapon,armor,charm}`, `relicLevels`), hero rigs `heroes/roster.gd` VOXEL map.
- **Accept:** you agree with MAPPING.md and `migration_v0_to_v1.json`, or tell me what to change.

### Phase 1 — core equipment foundation
1. **Item DB autoload** (`Equip`, new file of yours): load `data/*.json` + `appearances.json` once; index definitions by `itemId`.
2. **Instances + save.** New key `state.equipment = {schemaVersion:1, instances:{instanceId:inst}, equipped:{hero_id:{slot:instanceId}}, inventory:[instanceId], locks:[...] }`. Run `migration_v0_to_v1.json` once in `save_system.gd` `load_state()` after writing the backup key; idempotent; rollback = restore backup.
3. **Slots + rules.** 14 slots from `edata`/MAPPING: helmet, chest, shoulders, gloves, legs, boots, belt, cloak, amulet, ring1, ring2, main_hand, off_hand, class_item (+2 artifact slots). A definition with `slot:"ring"` goes into ring1 or ring2. Two-handed types (`weapon_types.json` hands=2, and dual_blades/fist_weapon) occupy main_hand+off_hand. Any hero can wear any armor family at efficiency 0.85 (own family 1.0, MAPPING table).
4. **Stats once.** `final = base_hero_stats (unchanged) + Σ gear (base x rarity mult x enhancement + substats) + set bonuses`, capped by `substats.json` cap_total. Recompute on every equip change; never write into base stats.
5. **3D swapping.** For each equipped wearable: for every part in `appearances[appId].parts` add `BoneAttachment3D(bone)` + mesh instance with the transform from `fit/armor_attach.json[hero].parts[attach_part]`. Apply hide rules (`FIT_AND_HIDE.md`, reference `tools/godot/dress.gd hide_verts()`): build the filtered index array once per hero+equip set; restore the original ArrayMesh on unequip. Use lod1 past ~25 m. Material: vertex colour albedo, linear, surface 1 emissive.
6. **Baked weapons.** Heroes in FIT_AND_HIDE.md's list get `hide.baked_weapon` applied while a main_hand/off_hand item is equipped.
7. **Inventory UI** with `ui/` art: grid of `tile_bg + icon + border`, paper doll from `ui_theme.json`, compare tooltip with deltas, lock toggle, sort/filter by slot/rarity/family/level, 4-column 72 px tiles on phones.
- **Accept (plan §Phase 1 1–10):** every slot visibly swaps, unequip restores, no severe clipping (see clip-check shots), stats once, base stats unchanged, relaunch/reconnect keep gear, 2H reserves both, locked items protected, mobile usable, nothing else regresses.

### Phase 2 — loot generation
- Server rolls: rarity from `loot_rules.tables[table]`, then (bosses) the separate exclusive roll from `boss_loot.json` with pity per player per boss; first-clear guarantee once.
- Instance creation: roll `substats.count_by_rarity[r]` substats from `family_weights` (no duplicate stat), value uniform in range; sockets by rarity; `boundTo` by `bindingRule`.
- Shared boss pool + Need/Greed/Pass per `loot_rules.need_greed_pass` (60 s, need before greed, sha256 tie-break, no leader override, mail/disenchant after 72 h, participation thresholds). Log every award.
- Loot beam: `rarity.json lootBeam` + `ui/beam_<r>.png` (additive billboard); rare+ only; legendary/masterwork pulse; sound key.
- **Never** roll anything tagged `hidden` (Sslythar list in `loot_rules.hidden_content`).
- **Accept:** server-side only, rates match tables over 100k sim rolls (±0.1% abs), exclusives only from their boss, no dupes on reconnect, expiry works, logs exist.

### Phase 3 — crafting and enhancement
- Facilities: `crafting.facilities` (smithy, mage_academy first; interiors are yours).
- Recipes consume inputs atomically (single save write); preview cost before confirm.
- Enhancement: use `enhancement.json` with `active_track` = v0_live → the exact current behaviour. v1 track only after the boss says yes.
- Mystic Forge stage 1 (enhance, ascend), stage 2 (reroll, replace one, unlock socket), stage 3 later.
- **Accept:** +15 and +10 cannot be exceeded (clamp server-side), costs previewed, interrupted ops recover, existing rules unchanged.

### Phase 4 — builds
- Sets: count equipped pieces per `setId` after each change; mixed sets allowed.
- Gems/runes/artifacts per `gems_runes.json`; artifacts: 2 active slots, unique effects don't stack.
- Elements: counters + 60% resist cap; transmog via `cosmeticAppearanceId` (never stats).
- **Accept:** set bonuses update immediately, cosmetics never alter stats, effects have cooldowns/caps.

## QA checklist mapping
| QA item | Where it is covered |
|---|---|
| 14 slots equip/unequip | Phase 1.3; slots in MAPPING.md; paper doll layout `ui/ui_theme.json` |
| 2H reserve both | `weapon_types.json occupies` |
| Off-hand/shields | `off_hand` defs (shields live; foci disabled until a 1H caster weapon has animations) |
| Sort/filter/compare/lock/stack/capacity | Phase 1.7; `stack` for materials (consumables/materials are unbound + stackable) |
| Every armor slot changes mesh / unequip restores | Phase 1.5, `appearances.json`; shots `onhero_<family>_by_rarity.png` |
| Fit on all heroes, no severe clipping idle/walk/run/combat/skill | `fit/armor_attach.json`; shots `clipcheck_heroes_1/2.png` (22 heroes x idle/walk/run/attack/skill/hit/death, Godot 4.7). No `jump` clip in the hero rigs (Pip only); ultimate = `skill`. |
| Weapon/shield hand transforms | phase-2 `loot/gear/gear_attach.json` |
| Cloaks cheap | cloak skinned to the existing cape bones (skin_cloak), zero physics cost; shot polish/after_cloak_run.png |
| Helmet hair/face rules | `hide.helmet_full` / `helmet_open` |
| Rarity not only recolour | per-rank geometry (rivets/straps → brass bands + haute-pieces → spikes + flare + glow → filigree + horns/wings + gems → molten seams + forge spikes), see shots |
| Multiplayer perf | ~3.8k tris avg per part high, lod1 ≤50%; full 8-slot kit 22k–65k tris high, 6.7k–15k lod1; use lod1 for remote players |
| Base stats fixed / once only / caps | Phase 1.4, `substats.json` caps |
| +15 / +10 / milestones / Legendary 12 / Masterwork 15 | `enhancement.json` |
| PvP/PvE caps | `substats.cap_total`, `affixes.element_rules` (PvP multipliers are yours to add) |
| Server loot / rates / exclusives / first-time / pity / beams / atomic pickup | Phase 2, `loot_rules.json`, `boss_loot.json`, `rarity.json` |
| Shared boss loot | `loot_rules.need_greed_pass` |
| Crafting/trading atomic, previews, bound items | Phase 3, `crafting.json`, `loot_rules.trade` / `binding` |
| Persistence/migration/backup | `migration_v0_to_v1.json` |
| Sslythar hidden | `boss_loot` sslythar `enabled:false`, `hidden` tags, no meshes |

## Known gaps / next art
- Weapons use the phase-2 family meshes (T1/T2/T3) for 6 rarities; named weapons use the T3 mesh as a placeholder. Dedicated legendary/masterwork and named meshes are next.
- Cloak now binds to the cape bones (polish 2).
- Robed/tabard heroes: `hide.robe_hem` shortens the skirt at the knee when legs/boots are worn (polish 3).
- Class items, artifacts, gems, runes and materials have 2D icons only (no world mesh).
