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
