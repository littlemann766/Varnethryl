# Varnethryl v1.5.32 — two-thumb Jump and skill combat validation

## What changed
- **Circular JUMP button** near WALK. The icon and action have their own touch target in portrait/landscape.
- **Immediate Jump on pointerdown** rather than a touch-generated `click` after release. A tap with the right finger should work while the left finger is still controlling the joystick.
- **Independent pointer ownership:** joystick keeps its first pointer until that pointer releases/cancels; Jump and skills capture their own separate pointer IDs. The hero should not stop, steer off course or switch joystick pointers when a button is touched.
- **Five attack/skill buttons:** basic, skills 1–3 and Ultimate accept touch on pointerdown. Owner Holy/Unholy selection still supports long-press, and quick-release casts.
- **Short skill-input buffer:** presses made during another attack's active animation are queued briefly (up to 1.3 seconds) instead of silently discarded. Valid cooldowns, SP/MP costs and combat permissions remain intact.
- **No movement stop required** for jump or skill input. Existing double jump for normal characters and authenticated quadruple jump for Owner/CoOwner stay in place.
- Android and GitHub Pages workflow gates include `node tools/check_multitouch_controls.mjs` with independent pointer and skill tests.

## Test steps on Android
1. Back up game progress. Install newest **successful** v1.5.32 release APK over the existing signed app without uninstalling it.
2. Enter Town. Put **left thumb on the joystick and keep pushing forward continuously**. While holding it, use your right thumb to tap the **circular Jump** button. Hero should jump immediately without stopping. Keep steering while airborne and land naturally.
3. Repeat for second jump and for Owner/CoOwner third and fourth jumps. Verify ordinary players cannot jump five times without landing.
4. Repeat step 2 while holding **RUN** (toggle to running before testing), while moving diagonally and while moving along the wall battlements. Try jumping off the wall edge.
5. Enter an area where combat is active. Keep left thumb on the joystick throughout. With right thumb, press **Basic**, **Skill 1**, **Skill 2**, **Skill 3**, and **Ultimate**, individually. Character should keep moving as attacks launch.
6. Tap an ability before the preceding attack animation finishes. It should execute shortly afterward if still valid and affordable. No unexpected duplicate casts or ignored cooldowns.
7. Hold the Owner ultimate to open the Holy/Unholy picker; a quick press/release should cast the selected version, all without dropping the joystick.
8. Move the camera using a separate finger while walking (where room permits); buttons should not claim the joystick's pointer.
9. Repeat on an external Bluetooth mouse/keyboard if available; keyboard Jump via Space and accessibility click should activate once.
10. Exit/reopen and ensure character, UI placement and saves remain intact.

## If it still fails
Report which button, whether combat was active, which finger held the joystick, device model, OS/WebView version, and a 5–10s video. A screenshot alone cannot show whether multi-touch input was canceled.

## Limitations
Source syntax and static touch-control assertions can be checked without a device. Actual Android multi-touch, renderer responsiveness, release APK compilation and on-device skill execution **have not been physically verified in this development pass**.
