# Varnethryl v1.5.31 — Ladder-only navigation and free-climb device QA

## Implementation summary
- Perimeter Town wall's exterior staircase flights removed. Walkable battlements remain and vertical ladders connect street level to level 1.
- Shared multi-floor builder `stairs()` now registers ladder connectors instead of creating stair flight geometry. Existing `gallery()` and `fullUpper()` building layouts route through it, including towers, shops, residences, the keep and the temple. Hatches replace long stairwells.
- No Climb/Down prompt is created. Use the movement joystick or directional keyboard: walk toward the ladder, hold that direction to climb, release to pause, reverse to climb down.
- Ladder mesh rungs, rails and brackets use GPU instancing for Android performance.
- Normal characters receive 2 jumps per landing. Verified Owner and online server-verified CoOwner receive 4 jumps per landing. Combat HUD Jump and regular movement Jump share that behavior.
- Upper-floor and wall jumps preserve momentum and height; crossing a floor's edge while airborne begins a gravity-based descent.
- Permanent building rule: `docs/BUILDING-TRAVERSAL-RULES.md`.
- GitHub Actions checks: `node tools/check_ladders_jump.mjs`, existing overhaul and game tests, release cache checks and syntax checks.

## Phone tests
1. Save/backup game progress, install v1.5.31 over the existing signed Android app without uninstalling.
2. Town walls: walk to a visible wall ladder, keep joystick aimed toward the ladder to ascend automatically. No prompt should appear. Let go midway: character must pause on the rung, not fall. Reverse the joystick to descend. Climb fully onto the wall.
3. Walk on the battlements without jumping: edge collision should stop an accidental fall. Then **hold movement and press Jump**: character should clear the edge and drop to the ground rather than rubber-band to the wall or float.
4. At ground level, press Jump twice: no third jump until landing. Unlock verified Owner, test up to four jumps and verify the fifth is blocked until landing. Relock Owner and confirm two-jump maximum returns.
5. With two devices, test CoOwner four jumps **only after server confirms role**; an ordinary user or an invalid/offline CoOwner authorization must not receive four jumps.
6. Building interiors: try an Inn, Guild Hall, Temple gallery, Keep (multiple levels), Watchtower and Windmill or Lighthouse. Each ladder should have reachable ground and top anchor points, not cut through solid floors or block upper doors. Pause, reverse, and descend at every level.
7. Try jumping during normal walking/running and from combat mode. The movement joystick must remain responsive; combat skills must continue to work.
8. Open the minimap, change to Coliseum, return to Town. Town-only ladder collision/visuals must not show in other maps.
9. Save, exit, relaunch and check zone, hero, progress, controls and FPS.

## Remaining verification limits
Code and basic math/syntax checks are completed. No physical phone, Android APK build success, collision runtime simulation, live CoOwner device verification or complete artist-approved 3D visual pass has been confirmed in this session. Existing Coliseum terrain/spectator ramp is not a `Builder` staircase and remains unchanged pending separate navigation work.

Bug reports: share a screenshot/video, building/zone, device, and what button or joystick direction you used. Keep all Owner/CoOwner passwords and tokens private.
