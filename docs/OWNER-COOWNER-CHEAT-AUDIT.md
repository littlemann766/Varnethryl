# Varnethryl Owner / CoOwner control audit — v1.5.25

The Owner and CoOwner are **separate roles**. Only the Owner can use full gameplay cheats; CoOwner permissions are verified by the Varnethryl WebSocket server. A nickname, local boolean, or saved skin is not proof of rank. Both remain unlocked until their manual Lock action.

## Owner panel

| Control | Actual operation | Validation / limitations |
| --- | --- | --- |
| God | Flag + damage mitigation | Verified by `tools/owner_cheats_test.mjs` |
| Fly / fly arrows | Owner altitude flags and per-frame fly controls | Unit-tested; available outside vehicle mode |
| Noclip | Collision bypass | Unit-tested |
| Bumps | Bump collision switch | Unit-tested |
| Speed | Live movement multiplier, 0.25–10 | Unit-tested |
| Unlimited MP/SP | Combat resource flag | Wired and persisted |
| No cooldowns | Combat cooldown override | Wired and persisted |
| Infinite / +1M gold | Shared profile save mutations | Save state verified; **not** equivalent to 3D Armory wallet |
| +1k / +50k XP | Shared profile XP and levels | Save state verified; 3D combat uses a **separate** per-hero XP store |
| Active / party level | Shared profile levels | Save state verified; 3D combat progression is separate |
| Spawn gear | Shared profile inventory | Item verified by unit tests; **3D Armory is a distinct equipment store** |
| Heal | Actual 3D CombatController restore | Initializes fight controller when needed; unavailable at sea |
| Kill enemies | Defeats live 3D fight targets | Reports failure if no live enemies |
| Quest skip | **Disabled** until a 3D quest advance API exists | No false success |
| Spawn enemy / Ashen Titan | Actual 3D fighter spawn result | Awaits controller readiness; unavailable at sea; may be refused by boss cap |
| Start / stop fight | Awaits actual combat transition | Reports false where prohibited (e.g. ship) |
| Town / Wilds / Frost / Hydra / Tidewrack travel | Uses the same queued zone-changing implementation as portals | **Awaits** model loading and reports failure; never silently claims the ship loaded |
| Buildings | Travels via town and validates collision | Awaits transition and reports failure |
| Teleport beside player | Varnethryl relay validates Owner role, world and online target | Existing live player never moved; two-device QA needed |
| Reset cheats | Clears active flags and preference toggles | Does **not** clear the sticky save-cheated marker |
| Lock Owner | Clears local Owner gate and revokes online bearer | Manual only; no inactivity timeout |

## CoOwner

- **Unlock:** masked password input and Railway-only server verifier. Never public GitHub code or game chat.
- **Player list / refresh:** requires server-verified CoOwner token.
- **Teleport:** server-authorized, moves only the CoOwner across world instances and map zones; does not grant Owner cheats.
- **Lock CoOwner:** revokes server token. Brief disconnect/reconnect uses a random bearer token; no plaintext password is retained by the client.
- **Chat:** ordinary world/private chat; CoOwner role labels are assigned by the relay rather than nicknames.

## Ocean fallback

At build time, `tools/prepare_marine_assets.py` decompresses the **approved original** Tidewrack and Hydra `.glb.gz` files into raw `.glb` copies inside the web app. `glbFromGzip` checks the scene-relative URL and prefers the raw copy when `DecompressionStream` is unavailable. Both assets are included in Android and GitHub Pages workflows. No substitute ship is introduced.

## Regression suite

- `node tools/check_overhaul.mjs`
- `node tools/owner_cheats_test.mjs`
- `node tools/owner_async_cheats_test.mjs`
- `cd multiplayer && npm test`
- `python tools/marine_browser_test.py` — mobile WebView emulation with `DecompressionStream` unavailable and desktop sailing.

These tests do not substitute for confirming the APK on the actual Android model, especially Ocean loading and two-device multiplayer.
