# Varnethryl 3D prototype

Standalone test of whether a 3D version of Varnethryl is practical on phones.
It does not touch the 2D game. Open `proto3d.html` (or `/proto3d/`) on the deployed site, or locally:
`npx http-server www -p 8080` then `http://localhost:8080/proto3d.html`.

## What it is
- One small Liongate-style village: ground, cobbled plaza and roads, fountain, 7 buildings, 2 gate towers, a keep tower, crenellated walls, ~56 trees, crates.
- One procedural low-poly knight (built from boxes/spheres/cones in code, with sword, shield, cape, plume) with idle (breathing, head turn) and walk (leg/arm swing, bob, cape) animation.
- Controls: virtual joystick (bottom left), tap-to-move on the ground, drag on empty screen to rotate the camera, WASD/arrows on desktop.
- Collision: hero is a circle against axis-aligned boxes (buildings, walls, crates) and circles (fountain, towers, trees). Hero slides along walls.
- Third-person follow camera, different distance/FOV in portrait and landscape.

## Update: three hero models and walk-in buildings
- Heroes (switch with the buttons at bottom right, or `?hero=0|1|2`): Sir Aldric, Darius Umbral, Selene Frostveil. Each is a detailed low-poly build (about 100 primitives, 8k to 10k triangles) made in code to match the boss's character sheets. Gold lion/fleur-de-lis (Aldric) comes from the sheet itself (colour-keyed from a crop, `tex/shield.jpg`); cloth tiles for the purple and blue/white fabric and fur are crops from the Umbral and Selene sheets (`tex/u-purple.jpg`, `s-fur.jpg`, `s-blue.jpg`). Umbral's cross and Selene's snowflakes are drawn procedurally. All animated: idle breathing/head turn, walk cycle, cape sway (CPU-deformed cloth), Selene's hair sway, Umbral's pulsing sword glow.
- Buildings: inn, smithy, guild hall and one house now have a real open door, hollow walls, furniture (bar, tables, hearth, forge, anvil, long table, bed, shelves) and collision. When the hero is inside, the roof and door frame hide and the walls turn see-through (cutaway). The other three houses are still solid.
- Sheet-vs-model fidelity: silhouettes, colour palette, main gear (shield, sword, staff, cloaks, spiked pauldrons, fur collar) are recognisable. Painted detail (filigree, chainmail, weathering, faces, flowing wavy hair) is only approximated. Think "toy version of the concept art", not a match.

## Files
- `www/proto3d.html`: page and touch UI. `www/proto3d/main.js`: whole prototype (~450 lines). `www/proto3d/index.html`: redirect.
- `www/proto3d/vendor/three.module.js`, `three.core.js`: Three.js r186, vendored unmodified (MIT, `THREE-LICENSE.txt`). No CDN.
- `tools/proto3d_test.py`: Playwright test (loads, no console errors, joystick moves, tap moves, building and fountain block the hero, FPS sample, screenshots).

## Licensing / assets
No external models or textures. The hero, buildings and textures are generated in code, so there is nothing to attribute besides Three.js (MIT). If we later use CC0 packs (Quaternius, Kenney) note them here.

## Performance choices
- Pixel ratio capped at 1.5. One shadow-casting directional light, 1024x1024 shadow map, PCF (not soft/VSM), shadow frustum +-15 units that follows the hero.
- Lambert materials only (no PBR), no post-processing, no environment maps, linear fog.
- All static world meshes are merged into one mesh per material at load; trees are 3 InstancedMeshes. Result: ~85 draw calls including the shadow pass, ~14k triangles.
- Hero is ~40 small meshes (not skinned), cheap on CPU.

## Honest assessment
Look: clean "toy diorama" low-poly style. It reads well and the lighting/shadows give real depth, but it is blocky and generic. It does not look like the painted Varnethryl heroes. To match the painted art we would need stylized hand-made models and textures, not primitives.
Phone performance: the scene is tiny by 3D standards (14k triangles, 85 calls, one 1024 shadow map), which a mid-range phone's GPU handles at 60fps in principle. This was not tested on a real phone. Headless numbers are from software rendering and say nothing about phone speed. The real risks come later: skinned characters (20 heroes, enemies), many simultaneous effects, bigger maps, and WebView overhead in Capacitor.

# What a full 3D conversion would need

## Models
- 20 playable heroes: each a rigged, textured low-poly (3k-8k tris) character with class-specific gear (weapon, shield/staff/bow etc.). Shared humanoid skeleton so animations can be reused; per-hero variants for race/body (e.g. dwarf, beastkin) as needed. 20 heroes + 15 weapons (weapons already have concept art: `assets/weapons`, `assets/weapon-concepts`).
- Creatures/enemies: roughly 15 to 30 types for the current content (beasts, undead, bandits, constructs, bosses incl. Count Veyra and Mortimer, plus corrupted variants by recolor). Mix of humanoid-skeleton and custom-rig models.
- NPCs: 10 to 15 (innkeeper, smith, guild master, villagers, Count Veyra, Mortimer) reusing the humanoid rig with different meshes/outfits.
- Buildings/props per zone: Liongate (about 10 building types, gate, walls, towers, fountain), Dusk Hollow and other quest locations (ruins, chapel, mansion, cave, graveyard), forests (3 tree types, rocks, bushes), dungeon kit (floor/wall/door pieces). Plan on 60 to 100 modular pieces.
- Textures: shared atlas or small palette textures per zone (1024px max), hand-painted style to carry the Varnethryl look.
- Sources: commissioned 3D artist (best for style fit), CC0 packs (Quaternius, Kenney) as placeholders, or AI image-to-3D tools followed by manual cleanup and retopology (AI output is rarely animation ready).

## Animation sets
- Humanoid base: idle, walk, run, turn, hit-react, death, victory, interact/talk.
- Combat per class family (about 6: sword/shield, two-hand, dagger, bow, staff/caster, ranged/gun or thrown): basic attack x2, skill cast x2, ultimate, block/dodge.
- Creature sets: idle, move, attack x2, hit, death (about 5 per creature rig, 8 to 10 rigs).
- Delivered as glTF/GLB with embedded clips, played via Three.js AnimationMixer with cross-fades. Mixamo or a shared retargeted set can cover the humanoid base cheaply.

## Engine integration
- Keep game logic (`game.js`, `data.js`, `quest.js`, `settings.js`, saves) and replace the renderer layer: a `world3d` module that maps existing game state (party, enemies, NPCs, map zones, quest triggers) to 3D scene objects.
- Replace tile/2D map data with zone definitions (spawn points, collision volumes, triggers); replace the 2D sprite combat view with 3D combat staging (camera, targeting by tap raycast).
- Asset pipeline: GLB loading with GLTFLoader + Draco/meshopt compression, texture compression (KTX2) for memory, asset preloading and an offline precache list (the current service worker precaches all assets; 3D assets will make APK/PWA size grow, likely 50 to 150 MB, so consider lazy zone packs).
- Mobile performance: skinned meshes are the main cost, so cap on-screen skinned characters (~10 to 15), use LOD and distance culling, GPU instancing for repeated props, baked lighting or one cheap shadow, particle budget, adaptive pixel ratio with an FPS governor, and a low/medium/high graphics setting.
- UI stays HTML/CSS over the canvas (works as it does now). Settings screen gets graphics quality and camera options.
- Collision/navigation: replace circle/box test with a navmesh or grid for tap-to-move pathfinding around buildings (this prototype only goes straight and slides).
- Testing: Playwright smoke tests plus real-device FPS and memory checks on 2 to 3 phones (low, mid, high) with Android Studio profiler / Chrome remote debugging.

## Estimated phases (small team, rough)
1. Prototype validation (this): done. Next: test on real phones, pick the art direction, decide on sourcing.
2. Art pipeline and vertical slice (3 to 5 weeks): one real hero model with rig and 8 animations, one zone (Liongate) with modular buildings, GLB loading, quality settings, nav/pathfinding. Go/no-go on look and phone speed.
3. Core systems port (4 to 6 weeks): world/zone loader, party following, NPCs and dialogue, quest triggers, interactions, save compatibility, input polish.
4. Combat in 3D (4 to 6 weeks): combat staging, skills, effects, enemies with animation sets.
5. Content art production (8 to 16 weeks, parallel with 3 and 4): all 20 heroes, creatures, NPCs, remaining zones. This is the biggest cost and depends mostly on art sourcing.
6. Optimization, QA, device matrix, store build (3 to 4 weeks).
Total about 5 to 8 months with a dedicated 3D artist; much longer with AI-only art due to cleanup. A cheaper alternative worth considering: keep the 2D game and use 3D only for the world and 2.5D billboard painted heroes, which keeps the painted art and cuts the character modeling.
