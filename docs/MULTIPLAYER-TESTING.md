# Varnethryl Multiplayer v1.5.17 — Solo & World Browser

On the 3D title screen choose **Play Solo** (no server connection) or **Multiplayer · Join World**. Multiplayer opens the in-game server browser with three discoverable public instances:

| World | Room code | Capacity |
|---|---|---|
| Kingdom One | WORLD1 | 12 |
| Kingdom Two | WORLD2 | 12 |
| Kingdom Three | WORLD3 | 12 |

These are room instances **on one dedicated Varnethryl World Server**, not different hosts and not any PayAviator service. The current number of connected players is retrieved from `GET /rooms`, with a Refresh control. If counts cannot be retrieved, the game says they are unavailable instead of inventing availability. An invite-only test session can still be created or joined with a private room code. These private codes are NOT published by `GET /rooms`.

A player joining from the **title screen** always enters the town (even if a local save last exited in another zone). A player already adventuring who chooses the in-game Multiplayer menu and connects to an *empty* world stays in their current map. When a second player joins, **only the arriving client** is placed in town, never the incumbent. Other players are visible by nickname when they enter the same zone.

The multiplayer controls remain in **Menu → Multiplayer · Worlds**, including switching public worlds, private world creation, leaving multiplayer, copying invite codes, and refreshing online counts. Each room has a 12-player limit. An instance is removed from server memory when its last member disconnects; public listings remain visible at 0 players.

## Deployment

The dedicated Varnethryl-Multiplayer Railway project hosts the `multiplayer/` Node.js server from the Varnethryl GitHub repository. Its production domain is `varnethryl-world-server-production.up.railway.app`. The game uses that public endpoint automatically. It should remain independent of the PayAviator-Backend/Postgres Railway project.

Server health: `GET /health`. Public worlds: `GET /rooms`. WebSocket room join: `wss://varnethryl-world-server-production.up.railway.app`.

Tests: `cd multiplayer && npm install && npm test`. CI runs the same tests on changes under `multiplayer/`.

## Current limits

This is opt-in shared-player **presence, positions, orientation and basic test-avatar movement**, not yet authoritative shared AI, synchronized monster health, player damage, shared loot, quests or authenticated accounts. Do not present it as fully functional multiplayer PvP. Rooms are ephemeral and online counts can briefly lag while devices reconnect.

## Two-device smoke test

1. A starts in the frost cave, opens **Menu → Multiplayer · Worlds**, and joins **Kingdom One**. A stays in the cave.
2. B selects **Multiplayer** from the title screen, chooses **Kingdom One**, and spawns in town. A remains in the cave.
3. A returns to town voluntarily (or B travels into the frost cave). Both see each other's test avatars and movement.
4. B leaves the world. A continues playing uninterrupted.
5. Both choose **Play Solo** to verify their local saves, quest progress, inventory, and controls remain intact.
6. Repeat with Kingdom Two and a private code to confirm separation.
