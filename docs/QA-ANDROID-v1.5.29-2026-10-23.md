# Varnethryl v1.5.29 — Android/Web QA (23 October 2026)

This is an **incremental stabilization pass**, not a declaration that all zones, PvP, or graphics have reached final quality. Source changes have been committed to `main`. Install a successful GitHub Actions APK artifact only after its workflow checks finish.

## Changes shipped in this pass
- Multiplayer character heading persists at the end of a movement when an older client sends a stale body yaw. Small intentional turns remain visible. Remote avatar position interpolation no longer allocates a fresh vector per peer each frame.
- Multiplayer chat ignores duplicate relay message IDs and flags unread **world** chat as well as private chat.
- If cross-world Owner/CoOwner teleport fails to load its destination, the client attempts to restore its previous map and reconnect to its previous room rather than silently remaining in the wrong room.
- The relay sends CoOwner teleport errors back to the **CoOwner** panel rather than accidentally sending Owner-only errors.
- Tidewrack's water remains renderable as a solid colored surface if a low-memory WebView cannot create its Canvas2D texture. Existing ship and wake logic are unchanged.
- The Coliseum adds 24 stylized spectator torch stands through two GPU instances. The arena floor remains the only PvP-designated zone, while the terraces remain spectator-only.
- New smoke checks run in Android and Pages workflows: `node tools/check_multiplayer_ocean_arena.mjs`.

## Test on a physical Android phone
1. Back up the current save with the game's JSON export before installing; do not uninstall or clear app data.
2. Launch, enter Town, and verify movement, character selection, minimap, camera, skill buttons and saved character remain functional.
3. Enter the Tidewrack map, check ocean texture or safe fallback, procedural 3D ship, steering, water and V-shaped wake. Return to Town.
4. Join the **same** multiplayer world on two phones. Have each player rotate while standing, turn while walking, and stop; both screens should show sensible facing, not snapping backward.
5. Send world and private chat in both directions. Each message should display sender, body and delivery state just once; unread indicator should appear if the panel is closed.
6. Try a valid Owner/CoOwner player teleport across zones, then a failed destination load (if reproducible) and confirm original world recovery. Confirm invalid CoOwner player selections show an error in CoOwner tools.
7. Enter Coliseum through the Town portal; walk the lower arena, exterior approach and upper spectator concourse. Confirm spectator tiers do not initiate combat.
8. Exit, reopen, and verify character, save and zone data remain consistent. Record fps, renderer calls, and device model for slowdowns.

**Not yet verified:** live Android APK build result, physical WebView performance, actual two-device movement/chat, live Railway relay redeployment, full multiplayer PvP, final custom ship/Coliseum art. These require build completion or hands-on testing, not just static source checks.

## Issue reporting
Include: **v1.5.29**, device, map/world, exact reproduction steps, expected and actual behavior, and screenshot/video if available. Never include Owner/CoOwner passwords, tokens or private world codes in shared issue reports.
