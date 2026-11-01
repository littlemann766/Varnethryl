# quests-test progress notes (resume here)
Worktree: /workspace/godot-quests (branch quests-test from voxel-heroes bc917c6; Lucky's /workspace/godot-voxel had uncommitted
tests/docking_test.gd + tidewrack/tw_sea.gd changes, left untouched). Story: varn-core design/story_crew_pilgrim.md @1ef8e2a, beats 1-3.

## Done
- [x] quests/quests.json (steps: talk/collect/interact/travel/kill; crew; npcs; points; pickups; spawns)
- [x] quests/quest_manager.gd autoload `Quests` (VSave.state.story; questStep untouched; old saves OK)
- [x] quests/quest_world.gd (spawns on POI walk routes from stage5_manifest; prompts; knight's men via EnemyDirector)
- [x] quests/quest_ui.gd (tracker, Journal, dialogue box)
- [x] tw_sea.gd hooks: went_ashore/left_shore signals, quest_prompt, unlock_B story flag; enemy.gd knight_man type
- [x] headless import: 0 errors
- [x] tests/quest_playthrough_test.gd: `VARN_LITE=1 godot --headless --path . --fixed-fps 60 -- --questrun` -> QT RESULT pass=75 fail=0,
      0 SCRIPT ERRORs (~70 s). Walks Beth's stage-5 POI routes on foot to every NPC/point/pickup/enemy.
- [x] TitanQuest: tests/titan_quest_test.gd headless gives the identical PASS/FAIL list to untouched bc917c6 (21 FAILs are
      display-only checks that need xvfb, same on base); tests/run_tests.gd exit 0.
- [x] debug APK: build/varnethryl-quests-test.apk (export preset "Android", version untouched; quests.json is in the APK)

## Round 2 (boss: fix rough spots) - done
- [x] Saltglass pier stair walkable (e9478a4, d45fd29): the stair was fine; a hero coming off the pier head wedged in the V
      between the stair's west cheek and the island face. tw_sea.gd ACCESS_PATCHES "guide" slabs funnel onto the flight.
- [x] Glass-diver's Chest path (e9478a4, d45fd29): invisible "deck" planks over the rock seams (route idx 108-117);
      _step_up() in _walk climbs lips <= 0.55 m and unsticks a capsule sunk into a sloped seam. Brynn back at the chest.
- [x] Night sailing (d45fd29, 10819c4): at night without Wren the ship crawls (3 m/s) and Charts refuse; the story night
      sail to Lantern Rock is allowed; arriving at Lantern Rock by day doesn't count ("only shows by night"). With Wren:
      Night/Day button at sea, full speed at night.
- [x] Cave diving (d45fd29): the skiff can't enter any sea cave until Brynn joins ("Only a diver knows the way...").
      Owner (unlock_all) and direct _cave_enter calls (tidewrack_test) bypass.
- [x] party_hook (10819c4): recruits join party.gd companions (follow + _companion_fight), max FOLLOW_GAP.size(), crew
      first, missing model -> warning + skip, crew re-applied when a save loads.
- [x] Playthrough with no assists (8f513bf): QT RESULT pass=93 fail=0, 0 SCRIPT ERRORs, 0 ASHORE resets.
- [x] TitanQuest test and tidewrack_test: identical PASS/FAIL to untouched bc917c6 (tq 25/21 display-only fails, tw 83/1).
- [x] Headless import 0 errors; debug APK rebuilt: build/varnethryl-quests-test.apk.
## Round 3 (boss Oct 31: "allow the owner to have it already but all other characters dont")
- [x] Owner as active hero (party.gd hero_id == "owner") has night sailing from the start: full night speed, Charts at
      night, Night/Day button. tw_sea.owner_active()/has_night_sailing(). Others keep the gate until Wren.
- [x] Playthrough 96/0 (new: Owner full speed + button before Wren, Aldric capped before Wren), 0 script errors.
- [x] titan_quest_test and tidewrack_test identical to bc917c6; import 0 errors; APK rebuilt 23:37 ET.

## Merge notes for Lucky
- tw_sea.gd: new ACCESS_PATCHES + _access_patches() (one call after _place_landings), _step_up/_shape_free (one call
  after move_and_slide in _walk), night/cave helpers + _night_cap (one call after ship.drive), cave gate inside the
  _contexts cave loop, chart_travel night line. No overlap with his uncommitted _place_landings pier-board edit
  (different lines; his edit sits in the same function as the call site, should auto-merge).
- tw_ui.gd: night_b button at (-700,-470).

## Known issues
- Players who chose the "Night" time preset crawl at sea until Wren joins (intended gate, but worth a boss OK).
- The access patches are invisible colliders: Beth should fix the island collider (stair-foot corner, plateau seams).
- godot-voxel moved on to 41a3b33 since this branch was cut from bc917c6; rebase/merge needed.

## Round 4 (Nov 1, 2026, ~1:00 AM ET): floating galleon / Night button
- Floating ship + Fly buttons: NOT quest code. Reproduced identically on base bc917c6: with the Owner Fly cheat flag on (cheats.request("fly", true), set only from the Owner cheat menu), tw_sea `_fly_step` treats the ship as flying without the Fly toggle being pressed; it rises to ~13-14 m on setting sail, hovers over land (shore 0 m), Fly UI shows, "Go ashore" hidden. With the flag off the ship stays at alt 0 on both. No quest code sets the fly flag (grep).
- Night/Day button moved from screen centre (580,250) to the right-hand sea row (990,250) in tw_ui.gd.
- Playthrough checks added: ship alt/Y stays 0 at sea, never over land (min shore >= 1 m), Fly UI never shown, Night button outside centre, HUD overlap clean at sea.
- Results: playthrough 101/0; titan_quest 25/21 and tidewrack 83/1 (same as base); import 0 errors; APK rebuilt 01:00 AM ET.

## Round 5 (Nov 1, 2026, ~1:35 AM ET): cherry-pick of Lucky's 49c6b4d (fly only after tapping Fly)
- Cherry-picked 49c6b4d cleanly (no conflicts) as 736be72 (main.gd, tw_sea.gd, ship_fly_test.gd, tidewrack_test.gd).
- Night button kept at right-hand sea row (-290,-470 -> screen 990,250, 130x64): clear of Charts (-560..-430) and Gust (-420..-290); Fly column is x -404..-320 at y -312..-32, so no vertical overlap.
- ship_fly_test 20/0; quest playthrough 101/0 (0 script errors); import 0 errors.
- titan_quest 25/21, same as base 49c6b4d.
- tidewrack 85/1 vs base 49c6b4d 86/0: only difference is "ash basalt ... materials" — that check was changed by voxel-heroes 2d96a78/ee93d25 (basalt on vc_flat), which quests-test (based on bc917c6) does not include; it already failed identically on bc917c6. Not from quest code.
- APK rebuilt 01:31 AM ET.

## Round 6 — QUESTS TEST 2 (boss on S26: no tracker / Journal in town)
- Cause: QuestUi was only created inside the Quests autoload's sea hook (current_scene with `sea` → QuestWorld.setup → then QuestUi). Anything that stops/delays that one chain on device (world hook failing, scene without `sea`) leaves no tracker and no Journal. Not reproducible on desktop (headless normal launch and xvfb both show it), so the UI is now independent of it.
- Fix: QuestUi on the tree root as soon as VUI exists; tracker + Journal shown whenever the title is not up (land and sea); auto-start re-checked every 1 s (save swapped later still gets the quest); fallback "Sail to Gullhaven" text; one-time hint after the shader veil: "Head to the harbour, board your ship and set sail for Gullhaven."
- Badge: config/test_build="QUESTS TEST 2" (named builds show as-is; tests/run_tests.gd's numeric test_build==version/code-1 check will fail on this branch by design).
- Checks: import 0 errors; questrun 101/0; xvfb shots checks/quests_test2_land_tracker*.png. APK rebuilt build/varnethryl-quests-test.apk (debug, unsigned by Lucky).
