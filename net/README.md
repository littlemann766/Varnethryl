# res://net — Varnethryl multiplayer (Godot port)
Port of `www/proto3d/multiplayer-client.js` against `multiplayer/server.mjs` (Railway "Varnethryl-Multiplayer").
- `Net.gd` autoload: WebSocket JSON relay client (join/state/chat/owner/coowner, reconnect with `entry:"resume"`).
- `NetApi.gd`: HTTP `GET /rooms`, `GET /health`.
- Game hook: set `Net.state_provider = func(): return {zone,x,y,z,yaw,hero,skin,moving}`; Net then sends state every 100 ms. Render remote players from `peer_joined/peer_state/peer_left`.
- Test: `godot --headless --path . -s res://net/tests/net_test.gd` (live; set VARN_WS_URL/VARN_HTTP_URL for local `node multiplayer/server.mjs`). Uses a random private room.
- Passwords are never stored or logged; only opaque server tokens in `user://net_tokens.cfg`.
