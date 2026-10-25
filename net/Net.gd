## Varnethryl multiplayer client (port of www/proto3d/multiplayer-client.js).
## Autoload name: Net. Talks JSON-over-WebSocket to the Railway relay
## (multiplayer/server.mjs). Presence/chat/rank only; no combat/loot sync.
## Never logs or persists passwords; only opaque server session tokens are
## kept in user://net_tokens.cfg (device-local, not in res://).
extends Node

signal connected
signal welcomed(info: Dictionary)          # {id, code, slot, first, spawn, players, maxPlayers}
signal join_failed(message: String)
signal disconnected(code: int, reason: String)
signal peer_joined(player: Dictionary)
signal peer_state(player: Dictionary)
signal peer_left(id: String)
signal role_changed(id: String, role: String)
signal chat_received(event: Dictionary)
signal chat_roster(players: Array)
signal chat_error(message: String)
signal owner_event(msg: Dictionary)        # owner-auth/players/error/locked/jump
signal coowner_event(msg: Dictionary)      # coowner-auth/players/error/locked/jump/boss-approved
signal message(msg: Dictionary)            # every decoded message (debug/tests)

const DEFAULT_WS := "wss://varnethryl-world-server-production.up.railway.app"
const DEFAULT_HTTP := "https://varnethryl-world-server-production.up.railway.app"
const ZONES := ["town", "wilds", "frost", "hydra", "sailing", "coliseum"]
const PUBLIC_WORLDS := [
	{"code": "WORLD1", "name": "Kingdom One"},
	{"code": "WORLD2", "name": "Kingdom Two"},
	{"code": "WORLD3", "name": "Kingdom Three"},
]
const MAX_PLAYERS := 12
const STATE_INTERVAL := 0.1   # server drops states < 80 ms apart
const TOKEN_FILE := "user://net_tokens.cfg"
const TOKEN_RE := "^[0-9a-f]{64}$"

var ws_url := DEFAULT_WS
var http_url := DEFAULT_HTTP
var auto_reconnect := true

var self_id := ""
var room := ""
var joined := false
var peers := {}  # id -> player Dictionary (last known)

var _ws: WebSocketPeer
var _last_state := 0.0
var _pending_join := {}
var _last_ws_state := WebSocketPeer.STATE_CLOSED
var _keep := false
var _retry_in := -1.0
var _retries := 0
var _token_re := RegEx.create_from_string(TOKEN_RE)

## Optional provider the game sets so Net can send the local hero's state.
## Must return {zone,x,y,z,yaw,hero,skin,moving}. (Hook: hero/world owner.)
var state_provider: Callable

func _ready() -> void:
	var env_url := OS.get_environment("VARN_WS_URL")
	if env_url != "": ws_url = env_url
	var env_http := OS.get_environment("VARN_HTTP_URL")
	if env_http != "": http_url = env_http

# ---------------- connection ----------------
## entry: "game" | "title" | "resume" (see server join rules).
func join(code: String, nickname: String, entry := "game", state := {}, friend_code := "") -> bool:
	var c := RegEx.create_from_string("[^A-Z0-9]").sub(_clean(code, 24).to_upper(), "", true).substr(0, 12)
	var n := _clean(nickname, 20)
	if c.length() < 4 or n.length() < 2:
		join_failed.emit("Enter a nickname (2+ letters) and a world code (4–12 characters).")
		return false
	leave()
	_pending_join = {"type": "join", "entry": entry, "code": c, "name": n, "friendCode": friend_code}
	if not state.is_empty(): _pending_join["state"] = state
	elif state_provider.is_valid(): _pending_join["state"] = state_provider.call()
	_keep = true
	return _open()

func leave() -> void:
	_keep = false
	_retry_in = -1.0
	if _ws and _ws.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		_ws.close(1000, "Leave world")
	_reset()

func is_online() -> bool:
	return joined and _ws != null and _ws.get_ready_state() == WebSocketPeer.STATE_OPEN

func _open() -> bool:
	_ws = WebSocketPeer.new()
	_ws.inbound_buffer_size = 1 << 16
	var err := _ws.connect_to_url(ws_url)
	if err != OK:
		join_failed.emit("Could not reach the Varnethryl world server.")
		return false
	_last_ws_state = WebSocketPeer.STATE_CONNECTING
	return true

func _reset() -> void:
	joined = false
	self_id = ""
	room = ""
	peers.clear()

func _process(delta: float) -> void:
	if _retry_in > 0.0:
		_retry_in -= delta
		if _retry_in <= 0.0 and _keep:
			_pending_join["entry"] = "resume"
			if state_provider.is_valid(): _pending_join["state"] = state_provider.call()
			_open()
	if _ws == null: return
	_ws.poll()
	var st := _ws.get_ready_state()
	if st == WebSocketPeer.STATE_OPEN:
		if _last_ws_state != WebSocketPeer.STATE_OPEN:
			connected.emit()
			_send(_pending_join)
		while _ws.get_available_packet_count() > 0:
			_handle(_ws.get_packet().get_string_from_utf8())
		if joined and state_provider.is_valid():
			_last_state += delta
			if _last_state >= STATE_INTERVAL:
				_last_state = 0.0
				send_state(state_provider.call())
	elif st == WebSocketPeer.STATE_CLOSED and _last_ws_state != WebSocketPeer.STATE_CLOSED:
		var code := _ws.get_close_code()
		var reason := _ws.get_close_reason()
		var was := joined
		_reset()
		disconnected.emit(code, reason)
		if _keep and auto_reconnect and was:
			_retries += 1
			_retry_in = min(30.0, 1.5 * pow(2.0, min(_retries, 5)))
	_last_ws_state = st

func _send(obj: Dictionary) -> bool:
	if _ws == null or _ws.get_ready_state() != WebSocketPeer.STATE_OPEN: return false
	return _ws.send_text(JSON.stringify(obj)) == OK

# ---------------- outgoing ----------------
func send_state(s: Dictionary) -> bool:
	if not joined or not ZONES.has(str(s.get("zone", ""))): return false
	var m := {"type": "state", "zone": s.zone, "x": float(s.get("x", 0)), "y": float(s.get("y", 0)),
		"z": float(s.get("z", 0)), "yaw": float(s.get("yaw", 0)), "hero": str(s.get("hero", "Adventurer")),
		"skin": str(s.get("skin", "aldric")), "moving": s.get("moving", false) == true}
	return _send(m)

func send_chat(text: String, to := "") -> bool:
	if not joined: return false
	var m := {"type": "chat", "text": text}
	if to != "": m["to"] = to
	return _send(m)

# Owner rank (server verifies PBKDF2; pass is sent once over TLS, never stored).
func owner_login(passphrase: String) -> bool: return _send({"type": "owner-auth", "pass": passphrase})
func owner_resume() -> bool:
	var t := _get_token("owner")
	return t != "" and _send({"type": "owner-resume", "token": t})
func owner_lock() -> bool: return _send({"type": "owner-lock"})
func owner_list() -> bool: return _send({"type": "owner-list"})
func owner_jump(id: String) -> bool: return _send({"type": "owner-jump", "id": id})
# CoOwner rank (verifier lives only in Railway env).
func coowner_login(passphrase: String) -> bool: return _send({"type": "coowner-auth", "pass": passphrase})
func coowner_resume() -> bool:
	var t := _get_token("coowner")
	return t != "" and _send({"type": "coowner-resume", "token": t})
func coowner_lock() -> bool: return _send({"type": "coowner-lock"})
func coowner_list() -> bool: return _send({"type": "coowner-list"})
func coowner_jump(id: String) -> bool: return _send({"type": "coowner-jump", "id": id})
func coowner_boss(boss: String) -> bool: return _send({"type": "coowner-boss", "boss": boss})

# ---------------- incoming ----------------
func _handle(raw: String) -> void:
	var m = JSON.parse_string(raw)
	if typeof(m) != TYPE_DICTIONARY: return
	message.emit(m)
	var t := str(m.get("type", ""))
	match t:
		"welcome":
			self_id = str(m.id); room = str(m.code); joined = true; _retries = 0
			peers.clear()
			for p in m.get("players", []): peers[p.id] = p
			welcomed.emit(m)
			if _get_token("owner") != "": owner_resume()
			if _get_token("coowner") != "": coowner_resume()
		"error":
			_keep = false
			join_failed.emit(str(m.get("message", "cannot join")))
			_ws.close()
		"joined":
			peers[m.player.id] = m.player; peer_joined.emit(m.player)
		"state":
			peers[m.player.id] = m.player; peer_state.emit(m.player)
		"left":
			peers.erase(m.id); peer_left.emit(str(m.id))
		"role-state":
			if peers.has(m.id): peers[m.id]["role"] = m.role
			role_changed.emit(str(m.id), str(m.role))
		"chat": chat_received.emit(m)
		"chat-roster": chat_roster.emit(m.get("players", []))
		"chat-error": chat_error.emit(str(m.get("message", "")))
		"owner-auth", "owner-players", "owner-error", "owner-locked", "owner-jump":
			_track_token("owner", m)
			if t == "owner-jump": _apply_jump(m)
			owner_event.emit(m)
		"coowner-auth", "coowner-players", "coowner-error", "coowner-locked", "coowner-jump", "coowner-boss-approved":
			_track_token("coowner", m)
			if t == "coowner-jump": _apply_jump(m)
			coowner_event.emit(m)

func _apply_jump(m: Dictionary) -> void:
	room = str(m.get("world", room))
	peers.clear()
	for p in m.get("players", []): peers[p.id] = p

func _track_token(rank: String, m: Dictionary) -> void:
	var t := str(m.type)
	if t.ends_with("-auth"):
		if m.get("ok", false) and _token_re.search(str(m.get("token", ""))): _set_token(rank, str(m.token))
		elif m.get("resumed", false) and not m.get("ok", false): _set_token(rank, "")
	elif t.ends_with("-locked"):
		_set_token(rank, "")

func _get_token(rank: String) -> String:
	var cf := ConfigFile.new()
	if cf.load(TOKEN_FILE) != OK: return ""
	var t := str(cf.get_value("tokens", rank, ""))
	return t if _token_re.search(t) else ""

func _set_token(rank: String, value: String) -> void:
	var cf := ConfigFile.new()
	cf.load(TOKEN_FILE)
	cf.set_value("tokens", rank, value)
	cf.save(TOKEN_FILE)

static func _clean(v: String, max_len: int) -> String:
	var re := RegEx.create_from_string("[^\\p{L}\\p{N} _-]")
	return re.sub(v, "", true).strip_edges().substr(0, max_len)
