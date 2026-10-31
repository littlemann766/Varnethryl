extends Node
## Port of www/core/save.js + www/proto3d/save3d.js + the active-session part of varn-menu.js.
## Same keys and field names as the JS save so a later localStorage import is a straight copy:
##   user://guildbound_rpg_save_v1.json   (SAVE_KEY, version 1)   -- JS core/save.js
##   user://vn.active3d.v1.json           (ACTIVE)                -- JS varn-menu.js
signal saved(state: Dictionary)

const SAVE_KEY := "guildbound_rpg_save_v1"
const ACTIVE_KEY := "vn.active3d.v1"
const P3D_KEY := "p3d"
const P3D_ZONES := ["village"]
const MAX_AGE_MS := 30 * 24 * 60 * 60 * 1000

var dir := "user://"
var state: Dictionary = {}

func _ready() -> void:
	state = load_state()

func save_path() -> String: return dir + SAVE_KEY + ".json"
func active_path() -> String: return dir + ACTIVE_KEY + ".json"

static func base_item(slot: String, idx: int) -> Dictionary:
	# Shape-compatible stand-in for core/items.js baseItem(); full item port comes with the inventory branch.
	return {"id": "%s_base_%d" % [slot, idx], "slot": slot, "base": idx, "level": 0, "affixes": [], "perks": []}

static func fresh_state() -> Dictionary:
	var inv := [base_item("weapon", 0), base_item("armor", 0), base_item("charm", 0), base_item("weapon", 1), base_item("weapon", 2)]
	return {"version": 1, "gold": 1250, "shards": 55, "accountLevel": 1, "accountXp": 0, "unlocked": [0, 1, 2], "party": [0, 1, 2], "partyCap": 3, "active": 0,
		"heroLevels": {"0": 1, "1": 1, "2": 1}, "heroXp": {}, "relicLevels": {}, "gear": inv,
		"loadouts": {"0": {"weapon": inv[0].id, "armor": inv[1].id, "charm": inv[2].id}, "1": {"weapon": inv[3].id}, "2": {"weapon": inv[4].id}},
		"guildLevel": 1, "forgeLevel": 1, "bossDifficulty": "standard", "zone": "village", "kills": 0, "zoneKills": {}, "bossKills": 0, "questStep": 0,
		"secondsPlayed": 0, "settings": {}, "veyra": null, "mirror": null, "logs": ["Welcome to Liongate. Your guild adventure begins!"]}

static func is_valid_save(s) -> bool:
	return typeof(s) == TYPE_DICTIONARY and int(s.get("version", 0)) == 1 and s.get("gear") is Array and s.get("party") is Array and s.get("unlocked") is Array

static func sanitize_party(s: Dictionary) -> Dictionary:
	# Minimal port of core/party.js: party ⊆ unlocked, unique, ≤ partyCap, active ∈ party.
	var cap := maxi(1, int(s.get("partyCap", 3)))
	var unl: Array = []
	for i in s.unlocked: if (typeof(i) == TYPE_FLOAT or typeof(i) == TYPE_INT) and int(i) >= 0 and int(i) < 20 and not unl.has(int(i)): unl.append(int(i))
	if unl.is_empty(): unl = [0]
	var p: Array = []
	for i in s.party: if unl.has(int(i)) and not p.has(int(i)) and p.size() < cap: p.append(int(i))
	if p.is_empty(): p = [unl[0]]
	s.unlocked = unl; s.party = p
	if not p.has(int(s.get("active", -1))): s.active = p[0]
	else: s.active = int(s.active)
	return s

func _read_json(p: String):
	if not FileAccess.file_exists(p): return null
	var f := FileAccess.open(p, FileAccess.READ)
	if f == null: return null
	var j := JSON.new()
	return j.data if j.parse(f.get_as_text()) == OK else null

func _write_json(p: String, v) -> bool:
	var tmp := p + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null: return false
	f.store_string(JSON.stringify(v)); f.close()
	return DirAccess.rename_absolute(tmp, p) == OK

## {status:'none'|'corrupt'|'ok', state}
func read_save() -> Dictionary:
	if not FileAccess.file_exists(save_path()): return {"status": "none", "state": null}
	var s = _read_json(save_path())
	if is_valid_save(s):
		var m := fresh_state(); m.merge(s, true)
		return {"status": "ok", "state": sanitize_party(m)}
	return {"status": "corrupt", "state": null}

func load_state() -> Dictionary:
	var r := read_save()
	return r.state if r.status == "ok" else fresh_state()

func write_state(s: Dictionary = state) -> bool:
	state = s
	var ok := _write_json(save_path(), s)
	if ok: saved.emit(s)
	return ok

## save3d.js writeSnapshot: writes p3d {zone,x,z,yaw} + active hero into the latest stored save. Never overwrites a corrupt file.
func write_snapshot(snap: Dictionary) -> bool:
	if not (snap.has("x") and snap.has("z")) or not is_finite(float(snap.x)) or not is_finite(float(snap.z)): return false
	var r := read_save()
	if r.status == "corrupt": return false
	var s: Dictionary = r.state if r.status == "ok" else sanitize_party(fresh_state())
	if snap.has("hero") and s.party.has(int(snap.hero)): s.active = int(snap.hero)
	s[P3D_KEY] = {"zone": str(snap.get("zone", "village")), "x": snappedf(float(snap.x), 0.01), "z": snappedf(float(snap.z), 0.01), "yaw": snappedf(float(snap.get("yaw", 0.0)), 0.001)}
	return write_state(s)

## save3d.js readPos
static func read_pos(s, world := 60.0):
	if typeof(s) != TYPE_DICTIONARY: return null
	var p = s.get(P3D_KEY)
	if typeof(p) != TYPE_DICTIONARY: return null
	if p.has("zone") and not P3D_ZONES.has(p.zone): return null
	if not (p.has("x") and p.has("z")): return null
	var lim := world - 1.5
	if absf(p.x) > lim or p.z < -lim or p.z > lim: return null
	return {"x": float(p.x), "z": float(p.z), "yaw": float(p.get("yaw", 0.0))}

# ---- active session (varn-menu.js) ----
func save_session(mode: String, world: String, nickname: String, snapshot: Dictionary) -> bool:
	return _write_json(active_path(), {"active": true, "time": int(Time.get_unix_time_from_system() * 1000), "mode": mode, "world": world, "nickname": nickname, "snapshot": snapshot})

func read_session():
	var v = _read_json(active_path())
	if typeof(v) != TYPE_DICTIONARY or v.get("active") != true: return null
	var age := int(Time.get_unix_time_from_system() * 1000) - int(v.get("time", 0))
	return v if age >= 0 and age < MAX_AGE_MS else null

func clear_session() -> void:
	if FileAccess.file_exists(active_path()): DirAccess.remove_absolute(active_path())

## JSON blob identical in shape to localStorage[guildbound_rpg_save_v1], for export/import.
func export_json() -> String: return JSON.stringify(state)
func import_json(txt: String) -> bool:
	var s = JSON.parse_string(txt)
	if not is_valid_save(s): return false
	var m := fresh_state(); m.merge(s, true)
	return write_state(sanitize_party(m))
