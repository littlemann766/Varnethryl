# Varnethryl v1.5.33 — approved map, Balthrix world timer and boss tools

Source of truth: marked-up top-down map supplied 24 October 2026. **Blue = Balthrix's perimeter route. Dark brown = new walkable roads.** The 3D path and minimap both use the game's real world coordinates, not pixel positions from the photo.

## New source work
- New perimeter spline for Balthrix. Harbor center is approximately 195 world units from the route, and a 500-point sampled route check enforces more than 165 units clearance throughout the curve.
- Balthrix has one **6-minute active encounter window every 15 minutes**, determined by the real-world clock rather than the player's proximity. One natural summon per client/session/15-minute slot, and it must never restart simply because someone walks past. His world timer applies to Town map combat; multiplayer boss damage/health is not yet synchronized across devices.
- Balthrix's physical worn corridor is ~30 units across, with sloped raised earthen shoulders, a scuffed central lane, fallen trees, crushed branches, boulders pushed toward the outer sides, and a patrol leash keeping his combat behavior outside the port and town.
- The brown route drawing was converted into **eight named terrain-following carriageways**, including the road into Tidewrack, spiraling frost-cave approach, Broken Seal connector, west/east main roads, Wilds spur, eastern meadow loop and southern road. Existing minimap roads were made smoothly curved.
- The old extraneous southwest harbor ridge was removed and the port terrain flattened over a wider safe zone; the distant fake cone mountain behind the harbor is excluded. Harbor scenery's random rocks and trees are cleared more broadly, as are the new road and patrol centerlines.
- Owner panel has six boss selections: Ashen Titan, Giant Ashen Titan, Balthrix, Frost Troll A, Frost Troll B and Hydra.
- CoOwner panel has the same six **test summon** selections, authorized by the **live multiplayer server** and whitelisted/rate-limited there. No Owner password or CoOwner secret is embedded in the code. Requests never grant all Owner privileges.
- Only one active boss or pending boss load per device. Balthrix summons are routed onto his actual mapped perimeter trail, never beside the harbor. Hydra needs the Hydra Mire map to show its real model, and Balthrix needs Town. Server-authenticated CoOwner boss summons are local combat tests only until combat replication is implemented.
- New asset `www/proto3d/balthrix-corridor.js` is included in the service-worker offline precache.
- CI smoke test: `node tools/check_owner_map_routes.mjs`, plus all existing overhaul, movement, multiplayer, Owner, and Android checks.

## Phone test plan
1. Back up saves, install the **newest successful** v1.5.33 APK over the existing app without clearing data.
2. Go to Tidewrack Harbor. Check the giant triangular mountain/cliff is gone, rocks no longer block the ship or harbor entrance, and Balthrix cannot be found in the port. Walk and sail the docks as before.
3. Follow each new road on foot; verify roads touch the ground and don't lead through walls or massive obstacles. Check the top-down minimap matches their curves.
4. Find Balthrix's worn perimeter trail and confirm visible raised sides, crushed branches, uprooted logs, scattered debris and displaced rocks without an impassable blockade. Check his long snaking body remains on it while roaming.
5. Balthrix must **not** appear merely because you enter the trail or re-enter the port. During his scheduled six-minute window, he can naturally appear, then retire after the window unless you are in an active close-range boss fight. Since the schedule is shared wall-clock time, the wait to next window varies.
6. Open Owner tools, choose each boss from the Summon bosses selector and verify the approved model actually loads; only one active boss at a time. Check Balthrix is summoned *on the perimeter path*, not in Town or Tidewrack docks.
7. Join a multiplayer world, unlock CoOwner through server verification, then use its new Summon boss tools. Expect the requested model to appear on **your own testing device**, not all players' devices. Check attempts from an ordinary/unverified player fail.
8. Leave the world, re-enter and verify stable saves, joystick+skills+Jump and general FPS. The existing ship and ocean assets must still work.
9. If any item fails, share zone, approximate map position, phone model, repro steps, and a screenshot/video. **Never include passwords/tokens** in a shared issue.

## Status and limits
Static source/syntax and route assertions are testable here. Full Android APK compilation, physical graphics/collisions, WebView frame rate, and synchronized multiplayer boss combat **have not been independently verified**. Balthrix's timer is a world-clock schedule evaluated by the client combat system; there is not yet an authoritative cross-device boss simulation.
