# Owner cheat panel (0.7.4)

Owner-only cheats for the 3D game (`proto3d.html`, the default entry). Nothing is visible, loaded or running for normal players.

## Opening it
- Desktop: press `` ` `` (backtick) or `Ctrl+Shift+G`.
- Phone: tap the small version label (`v0.7.4`, top-left under "Liongate prototype") **5 times** within 2.5 s.
- First time (or after "Lock owner"): a passphrase prompt appears. Enter the owner passphrase. The owner keeps the passphrase privately (not in the repo, not in any log). Once correct, the unlock is remembered in `localStorage` on that browser; the gesture then opens the panel directly.
- Wrong entries are throttled: 3 free tries, then a 30 s lock that doubles each failure, capped at 1 hour.

## What it does
| Cheat | Effect |
|---|---|
| God | `cheats.mitigate(dmg)` returns 0. **Attach point for combat**: wrap incoming damage with it. No combat exists in 3D yet. |
| Fly | Free altitude. Space/E up, Q/C/Shift down, or the on-screen ▲▼ buttons (touch). Above 2.5 m you also clear walls and buildings. |
| Noclip | Walk through walls, buildings, trees. World border still applies. |
| Speed | 0.5x to 8x (hard limits 0.25x to 10x). Followers keep up. |
| Infinite gold | Tops gold to 999,999,999 and `spendGold()` never deducts (attach point for shops). `+1M gold` adds gold. |
| XP / level | `+1k XP`, `+50k XP` use the shared `core/party.applyExperience`. Set level (1-80) for the active hero or the whole party. |
| Spawn items | Adds a weapon/armor/charm (level 0-15) to the shared save inventory. |
| Heal / Kill enemies / Skip quest | **Stubs**: they call `hooks.healParty / killEnemies / skipQuest` in `cheatEnv` (main.js, search `TODO(combat/quests)`) and report "not available yet" until those systems are wired. |
| Teleport | Zone list (only `village` exists in 3D) and every building (`BUILDING_DEFS`), landing on a free spot near the door. |
| Bumps | Turns the bump/stumble reaction off (`bumpSys.bumpOn`). Personal-space separation stays so nobody stacks. |

Cheats are off after every reload on purpose. "Reset cheats" turns them all off without a reload.

## The `cheated` flag
Any cheat use writes `cheated: true` (plus `cheatedAt` and a `cheatCount`) into the shared save `guildbound_rpg_save_v1`. It is **sticky**: reset and lock never clear it. It is an extra optional field, so the 2D/3D save schema (`version: 1`) is unchanged and both loaders keep it. When the backend exists it should refuse or flag any save with `cheated: true` and exclude it from leaderboards. If the stored save is unreadable the cheat is refused rather than overwriting it.

## Gating design (`www/proto3d/ownergate.js`)
- **Local mode (today):** PBKDF2-SHA256 (210,000 iterations, 16-byte random salt) over the passphrase, compared in constant time with the salted hash stored in the code. Only the salt and hash are in the repo. The persisted unlock token is a derived value, never the passphrase.
- **Server mode (later):** when Firebase auth lands (`sync.js`), call
  `getOwnerGate().setServerOwnerProvider(() => auth.currentUser.getIdTokenResult().then(r => r.claims))`.
  From that call on, only `ownerFromClaims(claims)` decides (custom claim `owner: true`, or the UID is in `OWNER_UID_ALLOWLIST`), the local passphrase and any stored unlock are ignored, and non-owners get no prompt at all. The backend must set that claim itself; never trust a client-sent flag.
- Rotating the passphrase: generate a new random salt and hash with `derive()` and replace `GATE` (old unlock tokens stop working automatically).

## Honest limits
Client-side gating **cannot stop a determined hacker**. Everything runs in the player's browser: someone can read the source, set `__p3d.cheat` flags from the console, edit `localStorage`, or patch the save. The passphrase gate only keeps casual players out and keeps the panel code from loading for them. Real protection has to live on the server: once the backend exists it must (1) verify the owner claim server-side, (2) reject or flag every save with `cheated: true`, and (3) validate saves (gold, levels, items) rather than trust them.

## Tests
- `node tools/owner_cheats_test.mjs` (gate: wrong/right passphrase, throttle, persistence, no plaintext leakage anywhere in the repo; every cheat's state effect; the 5-tap counter).
- `tools/owner_cheats_browser_test.py` (headless, 1920x1080 and 412x915: invisible by default, unlock, god/fly/noclip/speed, no console errors, draw calls unchanged).
