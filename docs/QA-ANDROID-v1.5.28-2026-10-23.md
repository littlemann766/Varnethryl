# Varnethryl Android device test — v1.5.28 (2026-10-23)

This test pass packages the current `main` game into an installable Android APK via GitHub Actions. No game data should be reset. The Android workflow runs automatically on pushes to `main` and uploads `Varnethryl-RPG-debug-APK` and `Varnethryl-RPG-release-APK` if validation, signing, and Gradle succeed.

## Install and smoke test
- Before installing, **export a JSON save backup** from the game; do not uninstall the existing app.
- Download the latest successful artifact from **Actions → Build Varnethryl Android APK**. Use the release APK to update an existing release-signed installation. A debug APK may use a different signing key and require a separate install.
- Launch the 3D game, move/turn the hero, open the character selector, enter combat, and check all five HUD abilities, including current skill focus.
- Exit/reopen the app and verify active hero, position, XP, and available save data persist.

## Open field tests (real Android hardware)
1. **Tidewrack/ocean:** enter the harbor/sea, confirm water and the supplied 3D ship render; sail, turn and return ashore. Look for missing models or a rectangular wake.
2. **Multiplayer orientation:** use *two devices* in one world; rotate each hero in place, walk/run in a circle, and confirm the other device receives facing direction as well as movement.
3. **Multiplayer chat:** send from both devices; both clients should show sender, timestamp and actual message body, once per message. Test after reconnect.
4. **Portals and teleport:** travel through portals and use available permissioned teleport controls. Verify you land in the correct zone, not off terrain, and failures are reported.
5. **Owner controls:** test the intended cheats one by one in a safe local save: XP, levels, heal, fly, speed, noclip, enemy spawn, zone travel. The quest-skip button is intentionally disabled until a 3D quest API exists.
6. **CoOwner controls:** confirm its separate server-verified role unlock, online player list, permission-limited teleport and lock. Do not place passwords in chat, screenshots, logs or this repository.
7. **General:** combat, minimap for each visited zone, collision, ship movement, and hot reload after closing/reopening.

## Reporting
For each failed check, capture the **version (v1.5.28)**, map/zone, device model, steps to reproduce, expected and actual behavior, and a screenshot or short recording if possible.

Note: repository code tests are not proof of correct behavior on a physical phone or a two-device multiplayer session.
