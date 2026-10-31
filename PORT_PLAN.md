# Varnethryl → Godot 4 port plan

Source: Varnethryl repo main 659b86e (local copy /workspace/sc), www/ + www/proto3d (≈13.3k lines of game JS in proto3d, plus www/core, www/data.js, www/quest.js and multiplayer/server.mjs).
Target: this repo (Godot 4.7.2, Mobile renderer, GDScript). The town, terrain, day/night, quality tiers, touch controls and benchmark already exist (tests 1–3).
Effort is in focused dev-days for one developer working with Beth on art. "Carries over" means used without rewriting.

## What carries over as-is
- **Character GLBs:** 21 roster heroes (proto3d/models), 27 Beth creatures/companions/bosses (models-beth), and the smooth, cloth and arms variants in models-new.
  - Rigs and skeletons import natively.
  - `*.cloth.json` spring/cloth data stays as data; the spring-bone code is rewritten.
- **Beth's world art:** r2/r3/r4 buildings, terrain, trees, dressing, decals and placement JSON. All of it is already in Godot.
- **Data tables:** move them to JSON or .tres with a one-off script (no hand retyping).
  - charscale.js height table (Pip 0.52, Phoenix 0.756, Wren 1.35, Owner 1.905, Titan 6x, trolls 3x, Vaelthryx about 19 m).
  - combat/data.js: TUNING, BOSS_PATTERNS, enemy table E(...), herokits.
  - www/data.js and core/items.js.
  - quest.js quest and NPC text.
  - buildings.js BUILDING_DEFS and townlands TOWN_MAP_ROADS.
  - bossregions.js centres.
- **Brand assets:** icons, adaptive icon, splash, poster and banner. Already used in test 3.
- **Not reused:** HUD sprites and icons in www/assets/hud and sprites are reused as textures, but all the HUD and UI layout code is rewritten.
- **Audio:** the current game synthesises sound with WebAudio (fight.js grunts); there are no audio files. Rebuild it as AudioStreamGenerator or record proper SFX. There's nothing to carry over.
- **Backend:** multiplayer/server.mjs (Railway) stays as it is. The Godot client talks to it over WebSocket (WebSocketPeer) using the same message protocol.

## Port order and effort

| # | System (JS source) | Godot approach | Effort | Carries over |
|---|---|---|---|---|
| 1 | Core loop, camera rig, touch and controls (main.js, camrig.js, controls.js, camprefs.js, terrain-follow.js) | CharacterBody3D, SpringArm camera and joystick (already prototyped). Camera prefs go into ConfigFile. | 4 | camera numbers |
| 2 | Heroes and roster, charscale (chars*.js, chars_core.js, heroes2.js, rework1–7.js, roster-preview.js, charscale.js) | One Hero scene and HeroDef resources. Height comes from the charscale table. AnimationTree per rig. | 8 | GLBs, height table |
| 3 | Animation and motion (classmotion.js, motion.js, serpent-locomotion.js, spring_bones*.js, aldric.js) | AnimationTree state machines, SkeletonModifier3D or a SpringBone add-on for cloth and tails, procedural serpent spine | 8 | clips in GLBs, cloth.json |
| 4 | Combat core (combat/controller.js, calc.js, systems.js, experience.js, grips.js, respawn.js, fight.js, core/combat.js) | Combat autoload, hitboxes as Area3D, cooldown timers, stamina/mana/fury, XP and levels | 10 | TUNING, enemy table |
| 5 | Skills and kits, cooldowns, owner ultimate (herokits.js, lightning.js, ownericons.js) | Skill resources with VFX scenes (GPUParticles) | 7 | skill numbers |
| 6 | Enemies and AI (combat/ai.js, guards.js, hobcamps.js) | NavigationRegion3D and agents, simple state machine, spawn caps (5 alive / 12 mobile) | 6 | stats, camp layouts |
| 7 | Bosses: Volcano Ashen Titan 11x, Hydra, frost trolls, Vaelthryx (boss-arena.js, BOSS_PATTERNS, boss-camera-focus.js, volcano-effects.js) | Pattern runner using telegraph decals (ring, cone, line), phase 2 enrage, boss camera | 9 | patterns verbatim, titan GLB and projectiles |
| 8 | Companions (combat/companions.js; Pip, Zephyr, Coral, Snowy …) | Follower AI with assist attacks (the Pip follower is already prototyped) | 3 | GLBs, stats |
| 9 | Buildings, interiors, stairs, ladders (buildings.js, bldkit.js, bldtex.js, interiors.js, ladders.js) | Beth's exteriors plus interior scenes per building: StaticBody stairs, Ladder Area3D with a climb state, roof-hide (done) | 10 | footprints, door data, stair routes |
| 10 | Maps, zones and gate travel (townlands.js, wilds.js, wilds-gateway.js, frostreach.js, frost-cave.js, water-realms.js, port-ships.js, balthrix-*.js, bossregions.js, zone-ambience.js) | One scene per zone, streamed with ResourceLoader.load_threaded. Gate portals use change-scene. Terrain via heightmaps. | 14 | road and region coordinates, Beth zone placements |
| 11 | NPCs and quests (quest.js, data.js) | Quest autoload driven by quest JSON, Dialogic or a custom dialogue box, quest markers | 6 | all quest and NPC text |
| 12 | Items, armory, gear (combat/armory.js, armoryui.js, core/items.js, weapons) | Inventory resources and an Armory UI | 5 | item tables, weapon GLBs |
| 13 | Title screen, menus, settings (varn-menu.js, settings3d.js, settingsboot.js; cleaned 3-tab version) | Control scenes: title with 3D preview; ☰ menu (Resume, Heroes, Travel, Multiplayer, Settings, Return to title); Settings tabs Graphics, Controls, Gameplay. Graphics maps onto the test-3 Low/Medium/High/Ultra tiers. | 5 | layout and option list |
| 14 | HUD, minimap, HUD layout editor (combat/hud.js, minimap.js, hud-layout-editor.js, hud-config.js) | CanvasLayer HUD, SubViewport top-down minimap fed from TOWN_MAP_ROADS, drag-to-place HUD editor saved to ConfigFile | 6 | HUD art, road data |
| 15 | Saves (save3d.js, core/save.js, P3D_KEY schema) | JSON in user://, same schema and version field, plus an importer for old saves (export code or cloud) | 3 | save schema |
| 16 | Cheats, Owner and co-owner gates, Owner & Dev tab (cheats.js, cheatflags.js, cheatpanel.js, cheatboot.js, ownergate.js, ownerboot.js, ownermax.js, coowner-panel.js) | Same gate logic (5 taps on the About version, tap cheats kept). Server-verified owner check goes through the backend; no secrets in the client. | 4 | rules and flags |
| 17 | Multiplayer and chat, Colosseum PvP (multiplayer-client.js, multiplayer-chat.js, coliseum-pvp.js, multiplayer/server.mjs) | WebSocketPeer client on the existing protocol, snapshot interpolation for remote players | 8 | server unchanged |
| 18 | Audio (fight.js WebAudio synth) | AudioStreamPlayer3D, buses, music. New SFX and music needed. | 4 | none (no files today) |
| 19 | FX (fx.js, volcano-effects.js, cinderflight.js, zone-ambience.js) | GPUParticles3D and shaders (fire, lava, frost, flight trails) | 5 | look references |
| 20 | 2D fallback and loader (index2d.html, loader.js, pwa.js) | Dropped: Godot ships native. The loader becomes the boot splash plus a threaded zone loader. | 1 | splash art |
| 21 | Platform: Play release, signing, version codes, Firebase/analytics if used | Godot Android export with a Gradle build for plugins, same package com.varnethryl.rpg and release key at cut-over | 3 | keystore, store listing |
| 22 | Performance and QA across tiers, real devices | Benchmark scene (exists), occlusion culling bake, shader prewarm | 6 | — |

**Total ≈ 135 dev-days, about 6–7 months for one developer, or about 3–4 months with Lucky, Lucian and Beth in parallel:**
- **Lucky:** world, buildings, zones and performance.
- **Lucian:** combat, bosses, backend and multiplayer.
- **Beth:** rigs, animation and VFX art.

## Milestones
1. **M1, vertical slice (~4 weeks):** town, one hero with full kit, 3 enemies, Pip, one quest, title, menu and settings, saves. Playable APK.
2. **M2, combat complete (~4 weeks):** all heroes and kits, companions, Hobgoblin camps, Ashen Titan boss.
3. **M3, world (~5 weeks):** all zones and gates, interiors, ladders, port, Frostreach, Wilds, remaining bosses.
4. **M4, online and polish (~3 weeks):** multiplayer and chat, PvP, cheats and owner tools, audio, QA. Then swap the package to com.varnethryl.rpg for the Play update (needs the boss's yes).

## Risks
- Rig and animation retargeting for the 48 character GLBs. Some rigs were made for three.js; check them in a Godot import pass first (1–2 days).
- Saves are in browser localStorage today, so players need a migration path (cloud or export code).
- Moving to com.varnethryl.rpg needs the same release key. The keystore must stay offline and never be printed.
- Phone performance: hold every zone to the test-3 High budget (60 FPS).
