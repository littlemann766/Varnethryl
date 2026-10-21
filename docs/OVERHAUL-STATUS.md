# Varnethryl — Staged 3D Overhaul

**Branch:** `overhaul-2026-10-20`  
**Status:** DRAFT, NOT RELEASED. Do not merge this branch into `main` or install over the user's signed app without browser, Android and save-compatibility verification.

## Implemented in the staged branch

1. Fix crash while creating the five-button CombatHUD: use the all-matches selector for ability buttons.
2. Activate regular combat on entering the 3D world without owner-only tools; trigger wilderness auto encounters for ordinary heroes.
3. Keep unreleased Sslythar hidden from normal roster, URLs and restored hero/companion slots. Preserve existing model files and stored save IDs.
4. Rebuild the frost brothers' realm as an enclosed dark icy cave with hanging icicles, floor spires and blue crystal lighting; preserve the brothers' arena and exit.
5. Replace the summit's decorative rock cluster with a traversable ice tunnel leading to the unchanged portal coordinates.
6. Replace the harbor's old geometric block boats with curved 3D sailing-ship fallback meshes, rigging and shaped sails.
7. Add 16 deterministic fallen trees, splintered stumps and debris along Balthrix's curved path, with real colliders and instanced rendering.
8. Advance Balthrix's patrol every frame rather than every ~220 ms, and drive serpent spine fallback on enemy animation updates.
9. Add full vertical pitch to the third-person camera orbit.
10. Simplify the combat settings label and correct the controls hint.
11. Repair outdated Balthrix scale/terrain test fixtures and refresh the offline precache list.

## Automated checks

- `node tools/check_overhaul.mjs`
- `node tools/check_boss_regions.mjs`
- `node tools/check_town_mountains.mjs`
- `node tools/check_balthrix_scale.mjs`
- `node tools/check_release_cache.mjs`
- Browser: `tools/town_expansion_browser_test.py` (GitHub Actions)
- Side-by-side installable debug APK: `.github/workflows/build-overhaul-test.yml` (no production signing secrets; separate `.overhaul` application ID).

**Passing automated checks are not proof of working Android combat or smooth imported GLB rig animations.** An actual Android playthrough still needs to validate input, frame rate, animation integrity, load time, portals, save/restore, and UI readability.

## Explicitly outstanding before release

- **Models:** replace procedural harbor ship with user's approved 3D ship GLB once the source file is actually imported. Import any additional lava/ice/creature GLBs only after file size, skeleton and texture audits. No existing binary has been deleted.
- **Sslythar:** remain hidden from normal gameplay; inspect full spine/tail bone weights, use the model viewer/isolated rig sandbox to build a terrain-following flight/slither gait.
- **Balthrix:** inspect authored serpent animations on a real device; the code-level fallback does not replace a sufficiently weighted, articulated skeleton.
- **Bosses/AI:** confirm Krag/Mog, Titan, nearby mobs, and companion attacks with direct gameplay recording, not only test assertions; tune pathing and combat hitboxes as needed.
- **Level art:** refine Frost tunnel roof/ice occlusion and lava terrain/harbor transitions using verified game screenshots.
- **Owner:** import final approved replacement Owner rig if different from `models-new/owner.glb`. Check hands, weapons, knees, run loop, cloak and attack animation weights.
- **UI and sound:** finish all menu/HUD screens and voice integration after input playtest; remove or implement any HUD edit controls that are misleading or inoperative.
- **Release:** confirm Android side-by-side debug build, memory and FPS, backup/restore compatibility. Only then selectively merge to `main` and create a separately signed release using existing keystore.

## How to test

1. Open the draft PR and check its status checks.
2. When `Build isolated Varnethryl overhaul test APK` completes successfully, download the `Varnethryl-Overhaul-Test-APK` artifact from that run.
3. **This debug edition installs alongside normal Varnethryl.** It has separate storage: importing an existing backup for testing is optional, but do not uninstall or overwrite the normal signed app.
4. Record any failures with zone name, hero selected, device model, and a short video if possible.

## Safety

No force pushes, no automatic main-branch merge, no live Play/App Store release, no save schema migration, no deletion of user GLB models, and no production signing keys in the test workflow.
