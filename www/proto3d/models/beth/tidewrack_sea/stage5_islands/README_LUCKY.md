# Tidewrack Sea - Stage 5: island interiors behind the 13 landings (Lucky test 35)

Each landing in `landings_v1.json` (copied from /workspace/shots/t34/dock) gets a real interior inland of its pier head:
shaped hills and outcrops, region ground (temperate A, saltglass B, frost, ash), paths from the pier head to every point of
interest, scatter (rocks + pines/bushes, salt crystals, ice spires/snow pines, basalt columns/sulphur), and 2-4 POIs.

## How to drop it in (no code change needed)
`tw_sea.gd` already loads every `{pre}*.glb` in a region's mesh dir. Copy the files of each island into that region dir:
- `{pre}isl_<id>.glb` / `_lod1.glb` - terrain + POIs + scatter, one vertex-colour surface (gets `vc_lit.tres`; ash ones get the basalt mat).
- `{pre}isl_<id>_glow.glb` - lanterns, lava, crystals, spring water (name ends `_glow` -> glow_vc, no shadow). No lod1 (tiny).
- `{pre}isl_<id>_col.glb` - walk collider (name ends `_col` -> trimesh StaticBody, never drawn): simplified patch + solid POI parts
  (tower/wall blocks, shrine pillars, hull, tent, chest, big rocks, tree trunks, bridge decks + rails).
POI positions, names, radii and suggested OmniLights per island are in `stage5_manifest.json` (`islands.<id>.pois`), plus the
bridge endpoints and the camera spots used for the renders.

## What it does to the existing art (nothing is edited)
- The patch is sampled from the stage 1/2/4 terrain and sits **+0.08 m above it**; its rim tucks 0.25 m under the original
  ground so there is no visible seam. Hills only ever ADD height (paths are filled benches, never cut).
- **Docks/landings untouched:** no patch within 6 m of the pier head, and the ground is exactly the original height out to
  14 m (blending in by 22 m), so `pier_head()` / `pier_foot()`, the boards Lucky places and the 20 m inland check still hold.
- **Existing props are cut out:** every vertex of Gullhaven port, Saltglass Landing, Saltwatch Keep, Lantern Rock, Coil arena,
  harbours, wrecks, arches, crystals, vents... standing on that land makes a hole in the patch (+ a 30 m falloff of the hills).
- **Original sea cliffs keep their own look:** steep original faces are not covered unless the hills raise them.
- Existing `_col` colliders stay; the new `_col` sits on top, so the hero walks on the new surface.

## Walkability
- Paths are routed with a direction-aware grade cost (switchbacks), then filled into a level bench (<=2.5 m fill).
- POIs are only placed on ground reachable from the pier head with steps <= 35 deg (hero floor_max_angle is 50).
- Max path grade per island is in the table (most p95 10-25 deg).

## Islet landings: causeways
Frostreach, Beached Wreck and Ember Wreck landings sit on small islets/shelves separated from the main land, so the builder
adds a causeway (ice / plank / basalt deck 3 m wide with rails, collider included) to the nearest big land:
Frostreach 58 m, Beached Wreck 39 m, Ember Wreck 16 m. Endpoints in the manifest. **Check ship clearance** there - decks sit
~0.3 m above the land ends (low over water); if a sailing lane crosses one, drop that bridge file part or tell me to arch it.

## Islands
| Landing | Region / ground | Files | POIs | tris High / lod1 / col | path max deg | causeway |
|---|---|---|---|---|---|---|
| Gullhaven | A / temperate | `meshes/A/arch_isl_gullhaven*` -> `tidewrack/stage1/meshes/` | Gull Watchtower ruin (watchtower), Gull Shrine (shrine), Founders' Stone (lore), Harbourmaster's Cache (chest) | 51348 / 23105 / 19816 | 39.4 | - |
| Saltglass Landing | B / saltglass | `meshes/B/coast_isl_saltglass*` -> `tidewrack/stage2/meshes/` | Saltglass Shrine (crystal_shrine), Singing Shards (crystal_grove), Glass-diver's Chest (chest), Salt-crusted Tablet (lore) | 44182 / 19880 / 18188 | 56.1 | - |
| Frostreach Ice Dock | frost / frost | `meshes/frost/frost_isl_frostreach*` -> `tidewrack/stage4/meshes/` | Rimehollow Ice Cave (ice_cave), Frostreach Cairn (frost_shrine), Iced Chest (chest), Frozen Waystone (lore) | 38150 / 17167 / 16521 | 11.0 | 58.1 m |
| Vent Harbour | ash / ash | `meshes/ash/ash_isl_vent*` -> `tidewrack/stage4/meshes/` | Ventmouth (lava_vent), Steam Pools (hot_pool), Ember Shrine (obsidian_shrine), Ash-buried Chest (chest) | 51704 / 23265 / 20827 | 50.7 | - |
| Lantern Rock | A / temperate | `meshes/A/arch_isl_lantern_rock*` -> `tidewrack/stage1/meshes/` | Old Lantern ruin (lighthouse), Keeper's Hut (hut_ruin), Keeper's Strongbox (chest), Lamp-oil Logbook (lore) | 37586 / 16913 / 15408 | 21.9 | - |
| Saltwatch Keep | A / temperate | `meshes/A/arch_isl_saltwatch_keep*` -> `tidewrack/stage1/meshes/` | Outer Wall ruin (keep_ruin), Watch Shrine (shrine), Garrison Chest (chest) | 8116 / 3651 / 3369 | 13.8 | - |
| Coil Isle | A / temperate | `meshes/A/arch_isl_coil_isle*` -> `tidewrack/stage1/meshes/` | Coil Bones (bones), Serpent Shrine (shrine), Drowned Offering (chest) | 40286 / 18127 / 14826 | 10.6 | - |
| Beached Wreck | B / saltglass | `meshes/B/coast_isl_beached_wreck*` -> `tidewrack/stage2/meshes/` | Castaway Camp (wreck_camp), Salvage Chest (chest), Captain's Last Log (lore) | 10928 / 4916 / 3916 | 33.7 | 39.4 m |
| Frozen Wreck | frost / frost | `meshes/frost/frost_isl_frozen_wreck*` -> `tidewrack/stage4/meshes/` | Frozen Camp (wreck_camp), Bergcleft Cave (ice_cave), Frostbitten Chest (chest) | 31782 / 14301 / 12467 | 22.9 | - |
| Aurora Arch | frost / frost | `meshes/frost/frost_isl_aurora_arch*` -> `tidewrack/stage4/meshes/` | Aurora Shrine (frost_shrine), Skyglass Hollow (ice_cave), Starwatcher's Stone (lore) | 33008 / 14852 / 14229 | 39.8 | - |
| Ember Wreck | ash / ash | `meshes/ash/ash_isl_ember_wreck*` -> `tidewrack/stage4/meshes/` | Cinder Camp (wreck_camp), Ember Vent (lava_vent), Scorched Chest (chest) | 22994 / 10346 / 10011 | 24.8 | 16.0 m |
| Hot Spring Grotto | ash / ash | `meshes/ash/ash_isl_hot_spring*` -> `tidewrack/stage4/meshes/` | Upper Spring (hot_pool), Lower Spring (hot_pool), Bathers' Shrine (shrine), Bather's Bundle (chest) | 14602 / 6569 / 5628 | 11.3 | - |
| Obsidian Arch | ash / ash | `meshes/ash/ash_isl_obsidian_arch*` -> `tidewrack/stage4/meshes/` | Glassfire Shrine (obsidian_shrine), Arch Vent (lava_vent), Obsidian Mirror (lore) | 40034 / 18014 / 16614 | 10.2 | - |

Budgets: High <= ~52k tris per island (terrain capped at 36k), lod1 = 45 % of High, colliders 1-21k tris; 1 vc draw call + 1 glow.

## Known limits
- **Saltglass**: the landing sits under a 50 m cliff (original stage 2 terrain). Only the lower ground is reachable, so its
  4 POIs are down there (shrine on the lower shelf; grove, chest and tablet in the gullies). The plateau above is shaped but
  not reachable on foot - it needs a stair/ramp structure (next step if you want it).
- **Saltwatch Keep / Hot Spring** are small islands: small patches (8-15k tris), 3-4 POIs close together.
- Renders are lit by a simple test rig (no shadows: Mobile PSSM striped on these broad slopes); the game lights them itself.

Renders: `renders/small/<id>_before_after_High.jpg` (inland view from the pier head + overview, before/after),
`<id>_before_after_Low.jpg`, `<id>_pois_High.jpg` (each POI), `S5_contact_inland_after.jpg`.
Tools: `tools/build_stage5.py [id ...]` (deterministic per id), `tools/render5.gd`.

## Stage 6 - Saltglass stair, causeway check, walk test

**Saltglass stair.** This is a switchback stair from the lower shelf (72.6 m) up to the plateau (108.3 m): 5 stone flights at 19.6°, rising 35.7 m.
- Landings span both flights, with a rail on the outer side only.
- The top walk is flat, then eases onto the plateau. The foot dips under the shelf so there is no lip.
- Slabs and rails are in `coast_isl_saltglass_col.glb`.
- Two new points of interest on top: **Saltglass Lookout** (watchtower) and **Clifftop Cache** (chest).
- Manifest: `islands.saltglass.ramp` = {decks, flights, deg, rise_m, bottom, top}.
- Renders: `renders/small/saltglass_stair_before_after_A.jpg` and `_B.jpg` (left before, right after).

**Sailing lanes vs causeways.** No stage 1-4 route or lane crosses the Frostreach (58 m), Beached Wreck (39 m) or Ember Wreck (16 m) causeways.
- The nearest are Rimefang Narrows, 309 m from Frostreach, and Cinder Gate, 631 m from Ember Wreck.
- So no arch was needed and the causeways stay low.
- Caveat: the water under the Frostreach deck is deep enough to sail, but no route uses it.

**Causeways.** The first and last span of each causeway is open (no rail) so you can step on at an angle. The decks are in the `_col`.

**Walk test.** Tool: `tools/walk5.gd`. It uses your ashore capsule: height 1.905, radius 0.32, speed 6, gravity 20, snap 0.6, 50° max floor, same resets as `_walk`. It walks from the pier head along every route in the manifest (`pois[].route`, world points) to each point of interest, both ways across each causeway, and up and down the stair. Results are in `walk_test_final.json`. Pier boards are excluded from this table and listed below.

| island | legs passed | still failing |
|---|---|---|
| gullhaven | 4/4 | - |
| frozen_wreck | 3/3 | - |
| frostreach | 6/6 | - |
| lantern_rock | 4/4 | - |
| obsidian_arch | 3/3 | - |
| vent | 3/4 | Ember Shrine (snag on a steep patch near the top) |
| hot_spring | 3/4 | Bathers' Shrine (snag at a pool edge) |
| coil_isle | 2/3 | Coil Bones (snag on a prop collider) |
| saltwatch_keep | 2/3 | Outer Wall ruin (snag on a wall block) |
| aurora_arch | 2/3 | Aurora Shrine (snag on a steep patch) |
| saltglass | 2/8 | stair up/down pass. All 6 lower-shelf points of interest fail: from the pier the shelf is up a ~50° cliff, so it needs a second stair from the pier |
| beached_wreck | 0/5 | causeway ends: the far islet bank is too steep where the deck lands |
| ember_wreck | 0/5 | causeway ends (same) + Cinder Camp snag |

**Total: 34/55 legs pass.**

**Your pier boards** (not stage 5): the sloped board fails the capsule on lantern_rock (48°), hot_spring (49°), vent (47°), saltglass (36°), aurora_arch (37°), obsidian_arch (31°) and ember_wreck (21°).

**Builder changes in stage 6:**
- Route heights come from the final mesh.
- The patch rides above the game's terrain collider.
- The patch collider is full resolution.
- Patch edges fade onto the game collider.
- Holes are cut only for standing props. Flat decals are re-laid onto the patch.
- Routes are re-planned on the finished surface.
- Terrain is kept out of stair headroom.

## Stage 7 — stairs, bank landings, snags
Walk test 53/57, with Lucky's pier boards left out. New built pieces are in the manifest: `ramp.pier_stair` (Saltglass), and `bridges[].bank_stairs` plus `bridges[].path` (Beached Wreck, Ember Wreck). Before/after renders are in renders/small/sheet_*_stair*.jpg. Results are in walk_test_final.json.

## Stage 9 — Saltglass dock lift + locked shortcut (stairs kept)
(Named Stage 9 because the 8a-8d fix commits already used "Stage 8".) Robert didn't want to climb ~11 flights every time, so Saltglass now has two faster ways from the dock to the plateau top. The old pier stair and plateau stair are unchanged.

**New files**
- `meshes/B/coast_isl_saltglass_lift.glb`, `_lod1` (49.9%), `_glow`, `_col`: the static parts. `tw_sea.gd` auto-loads them by the `coast_` prefix, so no code change is needed for these. 6,672 tris, collider 1,416 tris.
- `props/` (NOT auto-loaded; wire these in): `sg_lift.tscn` + `sg_lift.gd` + `sg_lift_platform.glb`, `sg_shortcut_gate.tscn` + `sg_shortcut_gate.gd` + `sg_shortcut_gate.glb` + `sg_lever.glb`, and `world_flags.gd`. The `.tscn` files expect the props at `res://tidewrack/stage2/props/`; change the paths if you put them elsewhere.
- Builder: `tools/build_stage9_saltglass.py`. It writes `islands.saltglass.stage9` into the manifest (positions, flags and walk routes).

**Layout (world m)**
- Dock walkway: runs from the pier head north along x -2124.6, then east along z -76 to the gate landing (y 20.4).
- **Shortcut ramp:** a switchback ramp tower in the water at x -2103.4..-2095.2, z -74..-46. It has 10 runs at **17.5°**, each 28 m long, with a turn landing after every run, rising 20.4 → 108.68 m. It has rails throughout and treads drawn on the ramps (the collider is a smooth slab).
- Top landing (y 108.68, z -76), then an **80.7 m skybridge** WNW onto the plateau at (-2172, 107.2, -22). That point is about 14 m from the Clifftop Cache. The skybridge pillars miss every POI route by 9 m or more, and the landing houses too.
- **Lift:** a shaft at (-2104, -82), right beside the ramp, running 20.4 → 108.68 (88.3 m) at 6 m/s, about 15 s per ride. Doors face north (+z) at both stops, with short connectors onto the gate landing and the top landing. It shares the top landing and skybridge with the ramp.

**Lock (Dark Souls style)**
- The **gate** is a portcullis at x -2100 across the gate landing, at the bottom of the ramp. It is locked from the dock side.
- The **lever** at (-2097.6, 20.4, -77.4) is on the ramp side, so the player can only reach it by first climbing the stairs to the plateau, crossing the skybridge and walking down the ramp.
- Pulling the lever raises the leaf 3.6 m into the gatehouse over 2.5 s and saves the flag **`saltglass_shortcut_open`**. On later loads the gate starts open.
- From the dock side the prompt reads "Locked from the other side".
- **Lift lock:** *replaced in Stage 10.* The lift no longer has an unlock flag; it is a paid ride run by a keeper (see Stage 10).
- Flags are stored by `WorldFlags` in `user://world_flags.cfg`. Point its two static funcs at your own save system if you have one.

**Wiring (tw_sea.gd, `_walk`)**
1. Instance both scenes under the B region root. The gate scene is already placed at (-2100, 20.4, -76). The lift places itself from its exports.
2. Add one branch to the prompt chain, before the final `else`:
   `var p: Array = lift.prompt_for(h.global_position); if p[0] == "": p = gate.prompt_for(h.global_position)`, then `ui.set_prompt(p[0], p[1])` when `p[0] != ""`.
3. Nothing else is needed. The lift is an `AnimatableBody3D` with `sync_to_physics`, and your ashore capsule rides it with no input. During the ride `_stuck_t` stays at 0 because spd is 0, and `_air_t` stays at 0 because the hero is on the floor.

**Walk test** (`tools/walk5.gd`, your ashore capsule, test-36 piers): **66/66 legs pass.** That is the 57 earlier legs plus 9 new Saltglass legs:
- shortcut gate locked: the dock side is blocked by the gate, as it should be (counted as a pass when the walker can't get through)
- shortcut down to the lever with the gate locked
- shortcut up (unlocked) and shortcut down (unlocked), dock ↔ plateau
- lift: dock to platform, ride up, top to plateau, plateau back to the platform, ride down

The shortcut legs only run as passable after the test removes the gate collider (the unlocked state). Pier boards are still excluded; the same 6 fail as before (aurora, ember, hot_spring, obsidian, saltglass, vent). That is your board, not stage 9.

**Renders:** `renders/small/saltglass_lift_shortcut_before_after_A/B/C.jpg` (left before, right after). A is from the sea, B is from above with the skybridge, and C is a close-up of the gate, lever and lift door.

## Stage 10 — Saltglass lift keeper + toll (replaces the Stage 9 lift unlock flag)
The lift is now a paid ride. A **lift keeper** stands in a timber toll booth at each stop (dock and top). A ride costs **5 coins**, or the player can buy a **season pass for 150 coins** at either booth window, which makes every ride free. Calling the lift to your own stop is free. The shortcut ramp gate is unchanged: free for good once its lever is pulled (`saltglass_shortcut_open`). `saltglass_lift_unlocked` is gone; you can ignore it if a save already has it.

**New art**
- `meshes/B/coast_isl_saltglass_tollbooths{,_lod1,_glow,_col}.glb`: two timber booths (dock at (-2109.5, 20.4, -80.4), top at (-2109.5, 108.68, -80.4)). Each has a plank floor, a counter window facing the walkway, a pitched slate roof, a price sign ("RIDE 5" + coin, "PASS 150" + coin), a winch drum and a coin box. The dock booth stands on timber piles. The top booth is cantilevered off the lift shaft on iron struts, so no pillars come down through the dock booth. 4,240 tris, lod1 45%. Auto-loaded by the `coast_` prefix.
- `props/lift_keeper.glb` + `lift_keeper_lod1.glb`: a voxel NPC built on the same mixamo rig as `town_guard_voxel` (cape bones dropped). He's a weathered winch operator with a grey beard, teal wool cap, faded blue shirt with rolled sleeves, leather apron (shoulder straps, pocket, brass buckle), thick leather gloves with cuffs, work trousers and boots. 21,808 tris; lod1 9,520 (43.7%).
  - Clips: **`idle`** (2.5 s, the guard's idle) and **`crank`** (2.0 s = two turns, 1 rev/s: he leans in, both gloves on the grip, knees flex). Both are keyed at 24 fps with no retime.
  - Built by `tools/build_stage10_keeper_blender.py` (Blender 4.2: `blender -b -P tools/build_stage10_keeper_blender.py -- out.glb 0.02`; use 0.03 for the lod1).
- `props/sg_crank_handle.glb`: the winch handle. Origin = axle; it spins about local X. `props/sg_lift_keeper.tscn` + `.gd` put it at keeper-local (0, 1.12, 0.2), where his gloves are in the clip. The script loops `idle`, switches to `crank` while the lift moves, and spins the handle in step.
- Builder: `tools/build_stage10_tollbooths.py` → manifest `islands.saltglass.stage10` (booth, keeper, crank axle and window points; prices).

**Coin + inventory spec (Lucky owns the real systems; `props/wallet_stub.gd` is only a stand-in with these signatures)**
| API (static, `Wallet`) | does |
|---|---|
| `coins() -> int` | current coins |
| `add_coins(n: int, reason := "")` | add (or with n < 0, remove; never below 0) |
| `pay(amount: int, reason := "") -> bool` | takes `amount` if affordable and returns true; otherwise takes nothing and returns false |
| `has_item(id) -> bool`, `item_count(id) -> int`, `give_item(id, n := 1)` | inventory |
| `buy(id) -> bool` | pay `ITEMS[id].price` + give the item; false if unaffordable or the player already owns a stack-1 item |
- Item ids: **`saltglass_lift_pass`**: "Saltglass Lift Season Pass", price 150, stack 1, kind `key_item` (never consumed).
- Save keys (suggested for your save; the stub uses them in `user://wallet_stub.cfg`): **`wallet.coins`** (int) and **`inventory.items`** (Dictionary id → count).
- Reasons passed to `pay`: `saltglass_lift_ride` and `buy:saltglass_lift_pass`, in case you want them for a ledger.
- "Not enough coins" prompts come from `sg_lift.gd` via its `toast(text)` signal (connect it to `ui.toast`): "Not enough coins - a ride costs 5 (you have N)." and "Not enough coins - the season pass costs 150 (you have N)."

**`sg_lift.gd` (updated)**: exports `ride_price = 5`, `pass_price = 150`, `pass_item`, `window_bottom` / `window_top` (-2109.5, y, -77.2) and `keeper_paths` (the two `SaltglassLiftKeeper` nodes). Prompts from `prompt_for(hero_pos)`:
- on the platform: "Ride up - 5 coins" (calls `Wallet.pay`), or "Ride up (season pass)" if the player holds the pass
- at a booth window (no pass yet): "Buy season pass - 150 coins"
- within 6 m of a booth while the lift is at the other stop: "Call lift" (free)
I checked it headless: broke → toast, 12 coins → ride (7 left), keepers crank while moving and go back to idle on arrival, pass purchase fails at 7 coins and succeeds at 207 (57 left), then rides show "(season pass)" and the window prompt disappears.

**Wiring**: same `_walk` prompt hook as Stage 9. Instance `sg_lift_keeper.tscn` twice at `stage10.dock.keeper` and `stage10.top.keeper` (yaw 0, facing +z), set the lift's `keeper_paths` to them, connect `toast`, and replace `Wallet` with your wallet (or make `Wallet` forward to it).

**Walk test: 68/68** (66 earlier + "toll: dock to booth window" + "toll: top landing to booth window"). The booth colliders are loaded for every leg. Pier boards unchanged (same 6, your board).

**Renders**: `renders/small/saltglass_tollbooth_before_after_{dock,top,wide}.jpg` (left before, right after; the dock keeper is mid-crank) and `renders/small/saltglass_lift_keeper_idle_crank.jpg` (front/back, idle top row, crank bottom row).
