# www/core — shared, UI-free game logic (0.6.5)
Imported by `game.js` (2D) and importable from `proto3d/*` (3D). No DOM, no canvas, no Three.js.
- `util.js` clamp/rand/sample · `items.js` gear (baseItem/advanceItem/tier/makeRoll)
- `party.js` nLevel, xpNeed, sanitizeParty, applyExperience · `save.js` SAVE_KEY `guildbound_rpg_save_v1`, freshState, loadState, writeState
- `combat.js` hpTarget, baseHP, equipped, combinedStats(state,id,mods), rollHit, enemyHurt
Quest/Mirror stay in the 2D layer and are injected as `hooks` (defaults/ensure) and `mods` ({atk:[fn],def:[fn]}).
Tests: `node tools/core_test.mjs` (parity against `tools/legacy_core_snapshot.js`, the pre-0.6.5 code).
