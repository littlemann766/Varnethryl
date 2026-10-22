# Coliseum PvP preview (October 22, 2026)

## Test route
1. Open the existing 3D game. Visit the **mini coliseum** in town (world position approximately x=117.6, z=106.4).
2. Walk through the violet gateway by the mini coliseum's front entrance (x=117.6, z=126.4). Portal travel uses the game's usual short dwell/cooldown.
3. The new standalone **coliseum** zone starts outside the arena at (0,133). Walk inward to explore the fight floor, radial spectator terraces, colonnade, and outer access ramps. All use one continuous terrain-height function for the prototype.
4. Walk to the violet gateway at (0,145) to return to the mini coliseum in town.
5. Open the minimap: the new zone shows concentric arena/spectator bands and an exit marker.

## Scope
- New map is **procedural preview geometry**, not the high-detail refined GLB. No binary model uploaded to GitHub.
- The fighting area is tagged as radial distance below 59 on ground floor. Higher seating and outside paths are spectator-only; the game combat controller's current auto mode stops outside this boundary.
- Actual network multiplayer/PvP combat, matchmaking, spectator permissions, robust navigation/collision mesh, detailed ruins and statues, and model-based graphics are **not yet built**.
- Graphics/art can be replaced later by uploading the refined GLB and integrating it into the same map lifecycle.
- All other zones remain configured as before. This integration has not been browser- or APK-tested yet.

## Files
- `www/proto3d/coliseum-pvp.js`: map and gateways
- `www/proto3d/main.js`: zone lifecycle, physics, portal transition
- `www/proto3d/minimap.js`: map labeling and top-down rings
