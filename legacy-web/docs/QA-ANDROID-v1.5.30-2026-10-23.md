# Varnethryl v1.5.30 — Coliseum and Owner control test pass

Release focus: keeping PvE test fights out of spectator stands and eliminating false "complete" messages when an Owner enemy model fails to load. Multiplayer, ocean and portal regression checks from v1.5.29 remain part of the build.

## Fixes to verify

1. **Coliseum spectator tier:** Enter through the Town mini-Coliseum portal and walk up the outer ramp. Using Fight in the spectator concourse must NOT arm combat. Walking off the arena floor must stop any fight before attacks can continue.
2. **Arena battle floor:** Walk back to the bottom arena (radius under 59 world units) and use the fight toggle. Combat HUD and skills should function without affecting the spectators. Enemies should spawn and stay on the lower floor.
3. **Owner spawning:** From a safe test save, unlock Owner and summon a normal enemy. The panel should only say complete after the model loads. A missing/failed GLB must say unavailable. Rapidly double-tap Spawn Titan: only one boss may begin loading.
4. **Ocean:** Confirm water, functioning procedural galleon and wake, then leave/return. The supplied original ship GLB is retained in the repository but is not currently used as the sailing hull because of previously reported disjointed meshes.
5. **Multiplayer:** Repeat two-device facing, chat, CoOwner error messages and cross-world teleport. Two-device verification remains outstanding until actually tested.
6. **Save safety:** Export a JSON backup before updating the existing app. Do not uninstall or clear Android app data. Verify character and game progress after launch.

## Expected implementation boundaries
- The Coliseum is still a **PvE combat-space preview**, NOT authoritative networked PvP. Upper tiers are protected now; real PvP health/damage and match rules remain future work.
- An Owner cheat action that loads a model is asynchronous; the UI must await an actual loaded enemy and may correctly report failure.
- Browser static tests and GitHub Actions do not substitute for an APK run on an Android device.

## Build
GitHub → Actions → **Build Varnethryl Android APK**. A successful workflow publishes debug/release APK artifacts. Choose the matching signing variant for your existing installation. A commit or an Actions run being queued does not mean the APK is ready.
