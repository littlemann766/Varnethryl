# Terrain & map pass: fixes (Beth). Notes for Lucky
These follow `/workspace/shots/terrain_pass/FINDINGS.md`. I did not edit any of your files. Each section lists exactly what to change on your side.

## Fix 1: duplicate buildings (town fillers)
**New:** 22 filler variants in `hi/buildings_card2/`: `bld_<id>_card2{,_lod1,_lod2,_col}.glb`. Each one has an entry in `index.json` with `variant_of` and `collision`, and `index_v1_backup.json` is the old index.
- Every variant keeps the footprint, door position and front axis of the kit model it replaces, so `door` / `path_end` / `rect` / `interior` in fillers.json stay valid. `_col` is a copy of the base model's collider.
- Townhouses: `townhouse_a`–`townhouse_h`. They vary in roof (slate / oak shingle / stone tile), walls (plaster / weatherboard / ashlar / fieldstone), with or without timber framing, storeys and pitch.
- Trades: `tailor`, `weaver`, `butcher`, `candlemaker`, `farrier`, `cooper` and `carpenter` each have a hanging iron-bracket trade sign (scissors, spindle, cleaver, candle, horseshoe, barrel, saw). The butcher has an awning with hams.
- Plain shop-footprint dwellings: `merchant_house(_b)`, `guild_house(_b)`, `stone_hall(_b)`, plus `chapel` (bell turret and gable cross; at most 2 in town).
- lod1 is 28–43 % of high for every variant (≤ 50 %).
**New placement:** `town/fillers_v2.json` keeps the same 212 entries (same ids, pos, yaw, door, path_end, rect and interior). Only `model` changed, `label` changed for the trades, and `model_v1` records the old model. `town/fillers_v1_lucky.json` is the backup of yours.
- The smithy, bakery and apothecary landmarks are no longer used as fillers, so there is one of each shop per town.
- No two identical models stand within 40 m; the closest pair is 48 m (it was 82 pairs under 40 m before).
- The four kit houses (house1–4) still appear, but at least 52 m apart.
**Lucky:**
1. Copy `hi/buildings_card2/bld_{townhouse_*,tailor,weaver,butcher,candlemaker,farrier,cooper,carpenter,chapel,merchant_house*,guild_house*,stone_hall*}_card2*.glb` into `assets/card2/`.
2. Merge the new `index.json` entries.
3. Replace `assets/town/fillers.json` with `town/fillers_v2.json`.
4. In `town_fillers.gd`, `KIT` is only used by `solve()`. The runtime build already reads `f.model`, so nothing else is needed, as long as `_card2_path(model, suffix)` resolves the new ids from index.json. If `KIT` is used to validate models, add the new ids to it.
5. Collision: `_card2_path(f.model, "_col")` finds `bld_<variant>_card2_col.glb` (copies are shipped).
