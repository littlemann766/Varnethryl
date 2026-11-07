extends Node
## Port of www/core/save.js + www/proto3d/save3d.js + the active-session part of varn-menu.js.
## Same keys and field names as the JS save so a later localStorage import is a straight copy:
##   user://guildbound_rpg_save_v1.json   (SAVE_KEY, version 1)   -- JS core/save.js
##   user://vn.active3d.v1.json           (ACTIVE)                -- JS varn-menu.js
## Version 1 files may omit keys added after the JS port (story, sea, fog). Missing keys keep
## fresh_state defaults. A file that is not version 1, or not JSON, is left untouched by autosave.
signal saved(state: Dictionary)

const SAVE_KEY := "guildbound_rpg_save_v1"
const ACTIVE_KEY := "vn.active3d.v1"
const P3D_KEY := "p3d"
const P3D_ZONES := ["village"]
const MAX_AGE_MS := 30 * 24 * 60 * 60 * 1000
## Mainland terrain is 2400 m across (scripts/main.gd _terrain, half 1200). The old resume box
## was CITY_HALF * 3 (553.5 m), which dropped mountain, outer-pad and any sailing coordinate.
const MAINLAND_HALF := 1200.0
## Tidewrack local coordinates. The sea node sits at world z = SEA_WORLD_Z, so a hero on a ship
## used to be saved at z ≈ 20000 and then rejected, which dropped them in town.
const SEA_HALF := 4000.0
const SEA_WORLD_Z := 20000.0
## Interiors are built at this stable offset (interiors/interior_manager.gd FAR / STEP), outside the mainland.
const INTERIOR_FAR_X := 4000.0
const INTERIOR_FAR_Z := 4000.0
const INTERIOR_STEP := 160.0
const VOLCANO_STATES := ["none", "active", "fight", "won"]
const _INT_FIELDS := ["gold", "shards", "accountLevel", "accountXp", "partyCap", "guildLevel", "forgeLevel", "kills", "bossKills", "questStep", "secondsPlayed"]

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

## Version 1 object. gear/party/unlocked may be missing; adopt() fills them. A future version is not readable.
static func is_valid_save(s) -> bool:
	if typeof(s) != TYPE_DICTIONARY: return false
	var v = s.get("version", null)
	if typeof(v) != TYPE_INT and typeof(v) != TYPE_FLOAT: return false
	return is_finite(float(v)) and int(v) == 1

static func _num(v) -> bool:
	return (typeof(v) == TYPE_INT or typeof(v) == TYPE_FLOAT) and is_finite(float(v))

static func sanitize_party(s: Dictionary) -> Dictionary:
	# Minimal port of core/party.js: party ⊆ unlocked, unique, ≤ partyCap, active ∈ party.
	var cap := maxi(1, int(s.get("partyCap", 3)))
	var unl: Array = []
	var unlocked = s.get("unlocked", [])
	if unlocked is Array:
		for i in unlocked:
			if _num(i) and int(i) >= 0 and int(i) < 20 and not unl.has(int(i)): unl.append(int(i))
	if unl.is_empty(): unl = [0]
	var p: Array = []
	var party = s.get("party", [])
	if party is Array:
		for i in party:
			if _num(i) and unl.has(int(i)) and not p.has(int(i)) and p.size() < cap: p.append(int(i))
	if p.is_empty(): p = [unl[0]]
	s.unlocked = unl; s.party = p
	var active_ok := _num(s.get("active")) and p.has(int(s.active))
	s.active = int(s.active) if active_ok else p[0]
	return s

## Fill defaults, keep unknown keys, and replace only fields whose types cannot be used.
static func adopt(saved) -> Dictionary:
	var m := fresh_state()
	if typeof(saved) == TYPE_DICTIONARY: m.merge(saved, true)
	var d := fresh_state()
	if not (m.get("gear") is Array): m.gear = d.gear
	else:
		var gear: Array = []
		var dropped := false
		for it in m.gear:
			if typeof(it) == TYPE_DICTIONARY: gear.append(it)
			else: dropped = true
		if dropped:
			m.gear = gear if not gear.is_empty() else d.gear
	if not (m.get("party") is Array): m.party = d.party
	if not (m.get("unlocked") is Array): m.unlocked = d.unlocked
	for k in _INT_FIELDS:
		if _num(m.get(k)): m[k] = int(m[k])
		else: m[k] = d[k]
	for k in ["heroLevels", "heroXp", "relicLevels", "loadouts", "zoneKills", "settings"]:
		if typeof(m.get(k)) != TYPE_DICTIONARY: m[k] = d[k]
	if typeof(m.get("logs")) != TYPE_ARRAY: m.logs = d.logs
	if m.get("sea") != null and typeof(m.sea) != TYPE_DICTIONARY: m.erase("sea")
	if m.get("story") != null and typeof(m.story) != TYPE_DICTIONARY: m.erase("story")
	if m.get("fog") != null and typeof(m.fog) != TYPE_STRING: m.erase("fog")
	if m.get(P3D_KEY) != null and typeof(m.get(P3D_KEY)) != TYPE_DICTIONARY: m.erase(P3D_KEY)
	m.version = 1
	return sanitize_party(m)

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
	f.store_string(JSON.stringify(v))
	f.close()
	if DirAccess.rename_absolute(tmp, p) == OK: return true
	# Some platforms refuse to rename over an existing file. Move the old one aside, then retry.
	var bak := p + ".replacing"
	if FileAccess.file_exists(bak): DirAccess.remove_absolute(bak)
	if FileAccess.file_exists(p) and DirAccess.rename_absolute(p, bak) != OK:
		DirAccess.remove_absolute(p)
	var err := DirAccess.rename_absolute(tmp, p)
	if FileAccess.file_exists(bak): DirAccess.remove_absolute(bak)
	return err == OK

## Copy a file we are about to replace when it is not a readable version-1 save.
func _quarantine(p: String) -> void:
	if not FileAccess.file_exists(p): return
	if is_valid_save(_read_json(p)): return
	var bytes := FileAccess.get_file_as_bytes(p)
	if bytes.is_empty(): return
	var dest := p + ".corrupt"
	if FileAccess.file_exists(dest):
		dest = "%s.corrupt-%d" % [p, int(Time.get_unix_time_from_system() * 1000.0)]
	var out := FileAccess.open(dest, FileAccess.WRITE)
	if out == null: return
	out.store_buffer(bytes)
	out.close()

## {status:'none'|'corrupt'|'ok', state}
func read_save() -> Dictionary:
	if not FileAccess.file_exists(save_path()): return {"status": "none", "state": null}
	var s = _read_json(save_path())
	if is_valid_save(s): return {"status": "ok", "state": adopt(s)}
	return {"status": "corrupt", "state": null}

func load_state() -> Dictionary:
	var r := read_save()
	return r.state if r.status == "ok" else fresh_state()

func write_state(s: Dictionary = state) -> bool:
	_quarantine(save_path())
	state = s
	var ok := _write_json(save_path(), s)
	if ok: saved.emit(s)
	return ok

## Autosave. Keeps the in-memory save (gold, sea upgrades, quest) and only patches position.
## A corrupt or other-version file is not replaced. A sailing position is stored on sea, not p3d,
## so it cannot erase the last mainland resume point. Coordinates the loader would reject are ignored.
func write_snapshot(snap: Dictionary) -> bool:
	if not _num(snap.get("x")) or not _num(snap.get("z")): return false
	var disk := read_save()
	if disk.status == "corrupt": return false
	var s: Dictionary = adopt(null)
	if is_valid_save(state): s = state
	elif disk.status == "ok": s = disk.state
	s = sanitize_party(s)
	_apply_hero_snap(s, snap)
	s = sanitize_party(s)
	var at_sea: bool = snap.get("at_sea") == true
	var at_interior: bool = snap.get("at_interior") == true
	if at_sea:
		var sx := float(snap.x); var sz := float(snap.z)
		if absf(sx) <= SEA_HALF and absf(sz) <= SEA_HALF:
			if typeof(s.get("sea")) != TYPE_DICTIONARY: s["sea"] = {}
			var kind := str(snap.get("ship", s.sea.get("ship", "galleon")))
			if kind not in ["galleon", "skiff"]: kind = "galleon"
			s.sea["aboard"] = true
			s.sea["ship"] = kind
			s.sea["x"] = snappedf(sx, 0.01)
			s.sea["z"] = snappedf(sz, 0.01)
			s.sea["yaw"] = snappedf(float(snap.yaw) if _num(snap.get("yaw")) else 0.0, 0.001)
			if typeof(s.get("interior")) == TYPE_DICTIONARY: s.interior["inside"] = false
	elif at_interior:
		var iid := str(snap.get("interior", ""))
		if iid != "" and _num(snap.get("x")) and _num(snap.get("z")) and absf(float(snap.x)) <= 80.0 and absf(float(snap.z)) <= 80.0:
			if typeof(s.get("interior")) != TYPE_DICTIONARY: s["interior"] = {}
			s.interior["inside"] = true
			s.interior["id"] = iid
			s.interior["x"] = snappedf(float(snap.x), 0.01)
			s.interior["z"] = snappedf(float(snap.z), 0.01)
			s.interior["y"] = snappedf(float(snap.iy) if _num(snap.get("iy")) else 0.0, 0.01)
			s.interior["yaw"] = snappedf(float(snap.yaw) if _num(snap.get("yaw")) else 0.0, 0.001)
			if typeof(s.get("sea")) == TYPE_DICTIONARY: s.sea["aboard"] = false
	else:
		var x := float(snap.x); var z := float(snap.z)
		var lim := MAINLAND_HALF - 1.5
		if absf(x) <= lim and z >= -lim and z <= lim:
			var zone := str(snap.get("zone", "village"))
			if zone not in P3D_ZONES: zone = "village"
			var yaw := float(snap.yaw) if _num(snap.get("yaw")) else 0.0
			s[P3D_KEY] = {"zone": zone, "x": snappedf(x, 0.01), "z": snappedf(z, 0.01), "yaw": snappedf(yaw, 0.001)}
			if typeof(s.get("sea")) == TYPE_DICTIONARY: s.sea["aboard"] = false
			if typeof(s.get("interior")) == TYPE_DICTIONARY: s.interior["inside"] = false
	_apply_quest_snap(s, snap)
	return write_state(s)

func note_land_position(x: float, z: float, yaw: float) -> void:
	if not is_valid_save(state) or not _num(x) or not _num(z): return
	var lim := MAINLAND_HALF - 1.5
	if absf(x) > lim or z < -lim or z > lim: return
	var yw := yaw if _num(yaw) else 0.0
	state[P3D_KEY] = {"zone": "village", "x": snappedf(float(x), 0.01), "z": snappedf(float(z), 0.01), "yaw": snappedf(yw, 0.001)}

# ---- who you are (roster skin). Numeric `active` stays the JS hero index when one exists. ----
static func skin_for_index(idx: int) -> String:
	if idx < 0 or idx >= VHeroData.RAW.size(): return ""
	for w in str(VHeroData.RAW[idx][0]).to_lower().split(" "):
		if HeroRoster.ORDER.has(w): return w
	return ""

static func data_index_for_skin(skin: String) -> int:
	if skin == "" or not HeroRoster.ORDER.has(skin): return -1
	for i in VHeroData.RAW.size():
		if skin_for_index(i) == skin: return i
	return -1

## Puts the played character on the save. A skin with no JS index (owner, pip, phoenix, wren) is still stored.
static func remember_hero(s: Dictionary, skin: String) -> void:
	if skin == "" or not HeroRoster.ORDER.has(skin): return
	s["heroId"] = skin
	var idx := data_index_for_skin(skin)
	if idx < 0: return
	if not (s.get("unlocked") is Array): s["unlocked"] = []
	if not s.unlocked.has(idx): s.unlocked.append(idx)
	if not (s.get("party") is Array): s["party"] = []
	var cap := 3
	if _num(s.get("partyCap")): cap = maxi(1, int(s.partyCap))
	if not s.party.has(idx):
		if s.party.size() >= cap: s.party[s.party.size() - 1] = idx
		else: s.party.append(idx)
	s["active"] = idx

func _apply_hero_snap(s: Dictionary, snap: Dictionary) -> void:
	var skin := str(snap.get("heroId", ""))
	if HeroRoster.ORDER.has(skin):
		remember_hero(s, skin)
		return
	if snap.has("hero") and _num(snap.get("hero")) and s.get("party") is Array and s.party.has(int(snap.hero)):
		s.active = int(snap.hero)
		var from_idx := skin_for_index(int(snap.hero))
		if from_idx != "": s["heroId"] = from_idx

## Saved skin wins. An old file with no heroId still starts as Owner when the owner gate is unlocked.
static func resume_skin(s, owner_unlocked: bool) -> String:
	if typeof(s) != TYPE_DICTIONARY: return ""
	var skin := str(s.get("heroId", ""))
	if skin != "" and HeroRoster.ORDER.has(skin): return skin
	if owner_unlocked and not s.has("heroId"): return "owner"
	return ""

## Where a relaunch should put the player.
## kind "town" is only for a missing or unusable position (not finite, or outside the mainland,
## the Tidewrack Sea, and the interior block). A normal save does not use it.
static func resume_place(s) -> Dictionary:
	var nowhere := {"kind": "town"}
	if typeof(s) != TYPE_DICTIONARY: return nowhere
	var sea = read_sea_resume(s)
	if sea != null: return {"kind": "sea", "x": sea.x, "z": sea.z, "yaw": sea.yaw, "ship": sea.kind}
	var legacy_sea = _legacy_sea_world(s)
	if legacy_sea != null: return legacy_sea
	var inside = read_interior(s)
	if inside != null: return inside
	var legacy_in := legacy_interior_index(s)
	if legacy_in >= 0: return {"kind": "interior_legacy", "index": legacy_in}
	var pos = read_pos(s, MAINLAND_HALF)
	if pos != null: return {"kind": "land", "x": pos.x, "z": pos.z, "yaw": pos.yaw}
	return nowhere

static func read_interior(s):
	if typeof(s) != TYPE_DICTIONARY: return null
	var inn = s.get("interior")
	if typeof(inn) != TYPE_DICTIONARY or inn.get("inside") != true: return null
	var id := str(inn.get("id", ""))
	if id == "" or not _num(inn.get("x")) or not _num(inn.get("z")): return null
	var x := float(inn.x); var z := float(inn.z)
	if absf(x) > 80.0 or absf(z) > 80.0: return null
	var y := float(inn.y) if _num(inn.get("y")) else 0.0
	var yaw := float(inn.yaw) if _num(inn.get("yaw")) else 0.0
	return {"kind": "interior", "id": id, "x": x, "z": z, "y": y, "yaw": yaw}

## Old saves wrote the interior's world coordinates into p3d (around x=4000+i*160, z=4000).
static func legacy_interior_index(s) -> int:
	if typeof(s) != TYPE_DICTIONARY: return -1
	var p = s.get(P3D_KEY)
	if typeof(p) != TYPE_DICTIONARY or not _num(p.get("x")) or not _num(p.get("z")): return -1
	var x := float(p.x); var z := float(p.z)
	if absf(z - INTERIOR_FAR_Z) > 30.0 or x < INTERIOR_FAR_X - 20.0: return -1
	var i := int(round((x - INTERIOR_FAR_X) / INTERIOR_STEP))
	if i < 0 or i > 80: return -1
	return i

static func _legacy_sea_world(s):
	var p = s.get(P3D_KEY)
	if typeof(p) != TYPE_DICTIONARY or not _num(p.get("x")) or not _num(p.get("z")): return null
	var x := float(p.x); var z := float(p.z) - SEA_WORLD_Z
	if absf(float(p.z)) <= MAINLAND_HALF: return null
	if absf(x) > SEA_HALF or absf(z) > SEA_HALF: return null
	var yaw := float(p.yaw) if _num(p.get("yaw")) else 0.0
	return {"kind": "sea", "x": x, "z": z, "yaw": yaw, "ship": "galleon"}

## save3d.js readPos. `world` is the half-extent the coordinate must lie inside (default 60 matches the JS proto).
static func read_pos(s, world := 60.0):
	if typeof(s) != TYPE_DICTIONARY: return null
	var p = s.get(P3D_KEY)
	if typeof(p) != TYPE_DICTIONARY: return null
	if p.has("zone") and not P3D_ZONES.has(p.zone): return null
	if not _num(p.get("x")) or not _num(p.get("z")): return null
	var x := float(p.x); var z := float(p.z)
	var lim := float(world) - 1.5
	if absf(x) > lim or z < -lim or z > lim: return null
	var yaw := float(p.yaw) if _num(p.get("yaw")) else 0.0
	return {"x": x, "z": z, "yaw": yaw}

## Ship-local resume. Absent aboard flag (every save from before this field) stays on land.
static func read_sea_resume(s):
	if typeof(s) != TYPE_DICTIONARY: return null
	var sea = s.get("sea")
	if typeof(sea) != TYPE_DICTIONARY or sea.get("aboard") != true: return null
	if not _num(sea.get("x")) or not _num(sea.get("z")): return null
	var x := float(sea.x); var z := float(sea.z)
	if absf(x) > SEA_HALF or absf(z) > SEA_HALF: return null
	var kind := str(sea.get("ship", "galleon"))
	if kind not in ["galleon", "skiff"]: kind = "galleon"
	var yaw := float(sea.yaw) if _num(sea.get("yaw")) else 0.0
	return {"x": x, "z": z, "yaw": yaw, "kind": kind}

# ---- volcano quest (story.cfg remains the legacy completion flag) ----
static func volcano_progress(s) -> Dictionary:
	var none := {"state": "none", "stage": 1, "hp": 1.0}
	if typeof(s) != TYPE_DICTIONARY: return none
	var story = s.get("story")
	if typeof(story) != TYPE_DICTIONARY: return none
	var v = story.get("volcano")
	if typeof(v) != TYPE_DICTIONARY: return none
	var st := str(v.get("state", "none"))
	if st not in VOLCANO_STATES: return none
	if st == "won": return {"state": "won", "stage": 3, "hp": 0.0}
	if st == "none" or st == "active": return {"state": st, "stage": 1, "hp": 1.0}
	var stage := 1
	if _num(v.get("stage")): stage = clampi(int(v.stage), 1, 3)
	var hp := 1.0
	if _num(v.get("hp")): hp = clampf(float(v.hp), 0.0, 1.0)
	return {"state": "fight", "stage": stage, "hp": hp}

## Completion sticks. A legacy story.cfg flag completes the quest even when the JSON save has no story key.
static func volcano_resume(s, cfg_done: bool) -> Dictionary:
	var p := volcano_progress(s)
	if cfg_done or p.state == "won": return {"state": "won", "stage": 3, "hp": 0.0}
	return p

static func volcano_done_in_cfg_text(text: String) -> bool:
	for line in text.split("\n"):
		var t := line.strip_edges()
		if not t.begins_with("volcano_done"): continue
		var v := t.get_slice("=", 1).strip_edges().trim_prefix("\"").trim_suffix("\"")
		return v == "true"
	return false

func set_volcano_progress(st: String, stage: int, hp: float) -> void:
	if typeof(state.get("story")) != TYPE_DICTIONARY: state["story"] = {}
	var norm := "fight" if st == "intro" else st
	if norm not in VOLCANO_STATES: norm = "none"
	var rec := {"state": norm, "stage": clampi(stage, 1, 3), "hp": clampf(hp if _num(hp) else 1.0, 0.0, 1.0)}
	if norm == "won": rec = {"state": "won", "stage": 3, "hp": 0.0}
	elif norm == "none" or norm == "active": rec = {"state": norm, "stage": 1, "hp": 1.0}
	state["story"]["volcano"] = rec

func _apply_quest_snap(s: Dictionary, snap: Dictionary) -> void:
	if not snap.has("qstate"): return
	var st := str(snap.get("qstate", ""))
	if st == "intro": st = "fight"
	if st not in ["active", "fight", "won"]: return
	if typeof(s.get("story")) != TYPE_DICTIONARY: s["story"] = {}
	var stage := 1
	if _num(snap.get("qstage")): stage = clampi(int(snap.qstage), 1, 3)
	var hp := 1.0
	if _num(snap.get("qhp")): hp = clampf(float(snap.qhp), 0.0, 1.0)
	if st == "won":
		stage = 3; hp = 0.0
	elif st == "active":
		stage = 1; hp = 1.0
	s["story"]["volcano"] = {"state": st, "stage": stage, "hp": hp}

# ---- active session (varn-menu.js) ----
func save_session(mode: String, world: String, nickname: String, snapshot: Dictionary) -> bool:
	return _write_json(active_path(), {"active": true, "time": int(Time.get_unix_time_from_system() * 1000), "mode": mode, "world": world, "nickname": nickname, "snapshot": snapshot})

func read_session():
	var v = _read_json(active_path())
	if typeof(v) != TYPE_DICTIONARY or v.get("active") != true: return null
	if not _num(v.get("time")): return null
	var age := int(Time.get_unix_time_from_system() * 1000) - int(v.time)
	return v if age >= 0 and age < MAX_AGE_MS else null

func clear_session() -> void:
	if FileAccess.file_exists(active_path()): DirAccess.remove_absolute(active_path())

## JSON blob identical in shape to localStorage[guildbound_rpg_save_v1], for export/import.
func export_json() -> String: return JSON.stringify(state)
func import_json(txt: String) -> bool:
	var s = JSON.parse_string(txt)
	if not is_valid_save(s): return false
	return write_state(adopt(s))
