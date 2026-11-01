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

## Known issues
- Saltglass pier stair (first ~13 route points, y 20 -> 69) can't be walked on test 37 head; docking_test DK_POI fails it
  too (Lucky's uncommitted pier-board change in godot-voxel targets this). The playthrough lifts the hero past it (QT WARN).
- Saltglass Glass-diver's Chest path snags ~16 m before the chest (route idx 111-113): Brynn stands at route_t 0.92 instead.
- Ship abilities (night_sailing, cave_diving) are flags only; nothing gates night sailing or caves yet.
- Crew -> party.gd fights: Quests.party_hook(id) is a stub.
