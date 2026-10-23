# Varnethryl shared-world test rooms (v1.5.12)

## Scope and joining
This is the first **online presence and movement test**, available across the Kingdom, Wilds, Frost Cave, Hydra Mire, Tidewrack Ocean, and Coliseum, rather than PvP restricted to the Coliseum.

**The first person connecting creates the room without being moved** (even when already exploring a cave or fighting a boss). The next person who connects to the same server address and room code enters the kingdom's town. Joining, reconnecting, or leaving does **not** send commands to relocate anyone already connected. Players remain in the same online room while entering different zones. When two people are in the same zone they see each other's lightweight test character and name.

The user-facing menu is **Menu → Multiplayer · Test rooms**, with fields for nickname, room code, and server URL. Both players use the same server and room code. It currently allows up to 12 connected testers per room.

## Server
GitHub Pages alone cannot host live multiplayer. The relay is in `multiplayer/server.mjs` (Node.js, package in `multiplayer/package.json`).

To host on Railway, create a new Node service for this repository with **root directory `multiplayer`**. It uses the included `railway.json`, installs npm dependencies, and runs `npm start`. Generate a public hostname on the service. The game accepts its **`wss://hostname`** URL (not `https://`). The service provides `GET /health` for health checks. Optionally set `ALLOWED_ORIGINS` to the comma-separated URLs of your hosted game; set an allowlist for external testers. `PORT` is supplied by the host.

Do not confuse the health check with a room API. Room joins and position updates use a persistent WebSocket connection, which requires a host supporting WebSocket upgrades.

For local testing:

```bash
cd multiplayer
npm install
npm test
npm start
```

Connect game clients to `ws://localhost:3001` only when actually running on the same computer. Devices outside localhost need the publicly hosted secure `wss://` URL.

## Reliability and safety
- Room membership and positions live in memory and reset when the server restarts. Players can rejoin manually.
- Distinct room codes isolate different parties. Codes alone are not user authentication; avoid sensitive nicknames.
- The server rate-limits updates, validates zone/position values and only relays display data. It rejects damage, items, experience, gold and cheats.
- The game stores the last server address and room code as local preferences. Multiplayer is off unless the user explicitly presses Join.
- Existing single-player saves, inventory, XP, owner access, camera state and companions are not synchronized or reset.
- Other players currently appear as lightweight **test avatars**, not their finished 3D character model. Their names, positions, facing and basic walk motion are shown only on the same map.

## Not yet multiplayer
This does **not** synchronize boss health, damage, loot, NPC AI, quests, PvP hits, shared interiors, mounting someone else's boat, or accounts/identity. Those need authoritative world simulation and anti-cheat validation. The server never accepts a client assertion that another user has taken damage. These systems must be developed and tested before public multiplayer release.

## Live test checklist
1. Start service and verify `/health` returns `ok:true`.
2. On device A, enter a frost cave and then join room `FROST7`; device A must **stay inside the cave**, with its current health/gameplay untouched.
3. On device B, connect to the same server and `FROST7`; device B should spawn in town, while A remains in the cave.
4. Walk B to the same map (or have A return to town voluntarily). Both test avatars must appear on the same map and move.
5. Disconnect B; A must remain where it was, and multiplayer should continue.
6. Return both to solo play to verify that original quest/save data remains intact.
