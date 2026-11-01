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
## Todo
- [ ] tests/quest_playthrough_test.gd (-- --questrun), headless run 0 errors
- [ ] TitanQuest test still passes
- [ ] debug APK build/varnethryl-quests-test.apk
