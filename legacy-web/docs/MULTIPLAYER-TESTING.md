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

## v1.5.21 — Actual remote 3D skins, world chat, private messages & friends

The game now advertises its **selected character skin ID** when joining, moving and changing skins. A peer resolves that ID strictly against the local `GLB_IDS` asset manifest and loads the actual existing `.glb` (including the currently selected Owner model). Arbitrary remote URLs and unreleased hidden Sslythar assets are not loaded. While a peer's GLB downloads, the older simple figure is only a temporary fallback. A loaded remote rig uses its own embedded idle/walk animation clips where available.

**Chat panel:** use **💬 Chat** within the world. The panel has World chat, Friends, a private-message area with contrasting purple styling **directly above the input**, a target selector and Send. Each message shows sender, time and text. The relay validates 1–280 characters, enforces a short per-player cooldown and broadcasts World chat only to the same world. A Private message is delivered only to the sender and intended recipient, including recipients across the three public worlds. Private-room participants do not appear in public-world chat rosters. HTML from other players is never rendered as markup.

**Friends:** add a player from the online directory or by their displayed Friend Code. Saved friends survive browser/app restarts on the same device, with online detection among users visible in your chat roster. They do not yet sync across devices. The Friend Code is **not account authentication**; it is a convenience test identifier and must never authorize Owner/CoOwner privileges or identify someone as a verified administrator. CoOwner ranks, permanent accounts, friend requests/approval, message history and offline messaging are later features.

**Testing:** two devices join WORLD1, select different GLB skins, meet in town, change one skin, and observe the remote 3D model update. Send a world message and a private message; verify only the intended player sees the private reply. Add another player as a friend, disconnect and reconnect, and verify the saved friend list. Repeat the private chat from WORLD1 to WORLD2, then ensure a private invite room is not exposed in the public chat roster.
