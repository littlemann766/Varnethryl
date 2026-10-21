# Varnethryl — Full 3D Overhaul Status

This is a **multi-phase game rebuild**, not a single APK patch. The current signed release on `main` is **1.2.6**. The next version, **1.2.7**, is **staged only** in a draft PR until its tests and device behavior are reviewed.

## Already on main (versions 1.2.4–1.2.5)

- Combat HUD activation for normal heroes; persistent character XP and gold/purple EXP meter.
- Purple crystal/gold medieval frames across menus and combat; expandable circular minimap.
- Freedom to look around with near-spherical third-person orbit.
- Frost Troll brothers' ice realm, cave tunnel and entry portal; region-specific boss spawns, aggro, telegraphs and retreats.
- Ashen Titan's region/lava effects and arena retreat; safer region transitions and async spawn guards.
- Tidewrack fallback 3D harbor ships (original approved ship asset **not yet integrated**).
- Balthrix's long patrol route, fallen trees and continuous position updates.
- Keep Sslythar hidden from standard gameplay, selections and older saves.
- Test workflows, Android APK build, and 1.2.4 rollback branch.

## In development: 1.2.7 rig/animation phase

- **Actual GLB rig audit**, covering Owner, two Balthrix rigs, Titan, Frost Troll A/B and two Sslythar rigs; logs and downloadable machine-readable report from GitHub Actions.
- First audit result: 10/10 structurally valid GLB files, **but valid does not mean visually correct**.
- Balthrix straight rig has 8 authored clips and 29 animated spine/tail-related joints. His dedicated `slither` and `slither_fast` animations are now explicitly preferred in the staged branch instead of generic walk/run.
- The newer Sslythar model has an animated skeleton; the older model is unskinned. **Both remain hidden** until in-game movement is tested and approved.
- **Ashen Titan volcanic pass (1.2.7 draft):** 42 batched basalt-rim formations, 128 low-cost drifting lava embers, two localized no-shadow lava lights, and subtle timed lava glow. Entire optional effect group culls automatically away from Titan territory. The original Titan boss GLB, cave summit, lava damage circles, fight arena and save coordinates remain untouched. Automated geometry/hazard tests plus an actual browser gameplay screenshot are required before release.
- **Frost Cave gameplay pass:** stronger local lighting at Krag and Mog's arenas and the return portal, large crystal clusters with collision, a guaranteed clear boss/portal travel corridor, and one low-cost animated airborne-ice particle batch. Cave glow pulses without adding shadow passes.
- **Browser regression:** checks actual cave color, both lit arenas, colliders and particles after the Frost portal, captures a mobile-size screenshot and checks both brothers still spawn.
- **Compatibility:** fixes inline CSS ornament URLs for GitHub Pages subpaths as well as Android; this keeps the repaired gold/purple HUD and original EXP fill visible on both.
- Varnethryl app, XP, HUD, and saved model slot ordering are otherwise retained.
- Latest CI and isolated Android side-by-side test build must pass before this work can be considered for release. Code checks alone are not a visual-animation quality guarantee.

## Remaining work — in zone-by-zone order

1. **Frost Troll cave:** Verify all walkable/collidable cave geometry, enemy attacks, low lighting, stable portal passage, battle stamina, weapon reach, model silhouettes and on-device rendering. Replace placeholders with approved original 3D assets where source files are available.
2. **Ashen Titan volcano:** Make lava terrain read properly at play height; proper heat light/shadows, giant-scale movement, attack collision and visual effects. Confirm no crossing into village.
3. **Tidewrack harbor:** Replace generated sailing ships with the approved source 3D ship GLB, tune scale/docking/water, and test on phone.
4. **Overworld / Balthrix:** Continue actual slither gait, turning and terrain-following spine movement, tree fallout collisions, foliage, slopes, dynamic shadows, distant castle, and player view freedom.
5. **Characters and companions:** Full skeletal skin/bone weight visual checks for Owner and all playable heroes, foot placement, idle/walk/run/sprint, companion AI and real attack hitboxes.
6. **Interfaces and world systems:** Complete consistent ornate HUD/menus, equipment, inventory, combat skill icons, quest interactions, loading video, audio and reliable save/restore.
7. **Sslythar:** Private animation playground only until body/tail/turns look right; do not spawn or reveal him in normal gameplay.
8. **Performance and release:** Browser and Android playthroughs for every zone, low/high graphics performance, textures/shadows, model load failure handling, no crashes, Android signature/versionCode preserved, backups and rollback instructions.

## Original artwork and models

GitHub contains playable-character and monster GLBs. The **approved original external environment GLBs** (especially the harbor ship and any terrain/lava/ice packs) need their source bytes made available in the repository before we can claim those particular assets are integrated. Do not substitute generated placeholder geometry while claiming the approved file has been used.

## Release discipline

1. Work in a branch, audit original models before editing skins, and stage changes zone-by-zone.
2. Run code + browser + Android test APK checks. Record which *specific* visual checks cannot be verified without a physical phone.
3. Keep the previous signed Android APK, ZIP, and backup GitHub branches. Do not break save slot ordering or change signing identity.
4. Only merge/ship a build after the specific phase is tested and clearly label what remains. **Do not mark the full overhaul finished merely because an automated build passes.**

**UI preservation:** Version 1.2.7 is based on the repaired, nine-sliced gold/purple border hotfix. Keep its mobile frame CSS and EXP bar unchanged.
