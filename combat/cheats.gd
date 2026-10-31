class_name Cheats
extends Node
## Owner + CoOwner cheats (ports www/proto3d/cheats.js, cheatpanel.js, ownermax.js, coowner-panel.js).
## SECURITY: the role is NEVER taken from the caller. role_provider reads the gates:
##   owner   = local owner gate unlocked (ui/owner_gate.gd, PBKDF2 check unchanged)
##   coowner = server confirmed {"type":"coowner-auth","ok":true} on Net (password is checked by the
##             server only; this client never sees or stores the co-owner hash/salt).
## Every action goes through request(), which rejects keys outside the caller's role list.
signal changed(key: String, value)
signal said(text: String)

const MAX_LEVEL := 80
const MAX_ITEM_LEVEL := 15
const GOLD_CAP := 999999999
const ITEM_KINDS := ["weapon", "armor", "charm"]
const FOES := ["frosttroll_a", "frosttroll_b"]
const BOSSES := [["titan", "Ashen Titan"], ["frosttroll_a", "Frost Troll — Krag"], ["frosttroll_b", "Frost Troll — Mog"]]
const ZONES := [["village", "Kingdom / Main Overworld"], ["hydra", "Hydra Mire"], ["sailing", "Tidewrack Ocean"], ["frost", "Frost Troll Ice Cave"]]

## Self-only play cheats. These affect only the caller's own hero, on their own device.
const SELF_ONLY := ["god", "fly", "noclip", "bump", "speed", "unlimited", "nocd", "heal", "titan_form", "tp_place", "fly_up", "fly_down"]
## Owner gets everything: self-only cheats plus world/save/economy/server tools.
const OWNER := SELF_ONLY + ["bamboo", "inf_gold", "gold", "xp", "xp_big", "level_active", "level_party", "remax", "item",
	"kill", "spawn_enemy", "titan", "spawn_boss", "spawn_worldboss", "fight_test", "tp_zone", "online_list", "online_jump", "lock", "panel", "dev"]
## CoOwner: self-only cheats, plus the server-verified jump-beside-player (it moves only her own hero).
## test 33: + ship_upgrade = free tier upgrades for HER OWN ship only (checked in TidewrackSea.free_upgrade()).
const COOWNER := SELF_ONLY + ["coowner_jump", "coowner_lock", "ship_upgrade"]

var flags := {"god": false, "fly": false, "noclip": false, "bump": true, "speed": 1.0, "unlimited": false, "nocd": false,
	"bamboo": false, "inf_gold": false, "titan_form": false}
var main: Node
var party: Node
var role_provider: Callable = func() -> String: return ""
var coowner_ok := false
var _bamboo_saved = null

func _vs() -> Node: return get_tree().root.get_node("VSave")
func _net() -> Node: return get_tree().root.get_node("Net")

func setup(m: Node, p: Node) -> void:
	main = m; party = p

func role() -> String: return str(role_provider.call())

## test 16 (boss: "fly even higher than the map as the owner"): owner has no practical ceiling; co-owner/others keep 60 m.
const FLY_CAP := 60.0
const OWNER_FLY_CAP := 100000.0
func fly_cap() -> float: return OWNER_FLY_CAP if role() == "owner" else FLY_CAP

func allowed(key: String, r := "") -> bool:
	if r == "": r = role()
	if r == "owner": return OWNER.has(key)
	if r == "coowner": return COOWNER.has(key)
	return false

## The only entry point. Returns true if the action ran.
func request(key: String, value = true) -> bool:
	var r := role()
	if not allowed(key, r):
		said.emit("Not allowed for %s: %s" % [r if r != "" else "player", key])
		return false
	if r == "owner" and not SELF_ONLY.has(key) and key != "lock" and key != "panel": _mark_cheated()
	var ok := _apply(key, value)
	changed.emit(key, value)
	return ok

func _mark_cheated() -> void:
	if _vs().state.get("cheated") != true: _vs().state["cheated"] = true; _vs().state["cheatedAt"] = int(Time.get_unix_time_from_system() * 1000)
	_vs().state["cheatCount"] = int(_vs().state.get("cheatCount", 0)) + 1

func _combat(): return party.combat if party else null

func _apply(key: String, v) -> bool:
	var c = _combat()
	match key:
		"god", "unlimited", "nocd", "inf_gold":
			flags[key] = bool(v)
			if key == "inf_gold" and v: _vs().state.gold = GOLD_CAP; _vs().write_state()
		"fly": flags.fly = bool(v); if main: main.cheat.fly = flags.fly
		"fly_up": if main: main.fly_alt = clampf(main.fly_alt + 3.0, 0.0, fly_cap())
		"fly_down": if main: main.fly_alt = clampf(main.fly_alt - 3.0, 0.0, fly_cap())
		"noclip":
			flags.noclip = bool(v)
			if main: main.hero.collision_mask = 0 if flags.noclip else 1
		"bump":   # JS "Bumps": enemies/props shove the hero. Off = enemy contact cannot push or stagger you.
			flags.bump = bool(v)
		"speed":
			flags.speed = clampf(float(v), 0.25, 10.0)
			if main: main.cheat.speed = flags.speed
		"titan_form":   # cosmetic, self only: hero model drawn 3x size (hitbox/damage unchanged)
			flags.titan_form = bool(v)
			if main: main.hero_vis.scale = Vector3.ONE * (3.0 if flags.titan_form else 1.0)
		"heal":   # own party only
			if c: c.hp = c.max_hp; c.st.mp = 100.0; c.st.sp = 100.0
		"tp_place":
			if main: return main.cheat_tp_place(str(v))
		"bamboo":
			flags.bamboo = bool(v)
			if c:
				if flags.bamboo: _bamboo_saved = c.kit.get("weapon"); c.kit["weapon"] = {"name": "Bamboo Stick", "dmgPct": 900.0}
				else: c.kit["weapon"] = _bamboo_saved
		"gold":
			_vs().state.gold = mini(GOLD_CAP, int(_vs().state.get("gold", 0)) + int(v if typeof(v) == TYPE_INT else 1000000)); _vs().write_state()
		"xp", "xp_big":
			var amt := 1000 if key == "xp" else 50000
			_vs().state.accountXp = int(_vs().state.get("accountXp", 0)) + amt
			var a := str(_vs().state.get("active", 0))
			_vs().state.heroXp[a] = int(_vs().state.heroXp.get(a, 0)) + amt; _vs().write_state()
		"level_active", "level_party", "remax":
			var lv := MAX_LEVEL if key == "remax" else clampi(int(v), 1, MAX_LEVEL)
			var ids: Array = [_vs().state.get("active", 0)] if key != "level_party" else _vs().state.party
			for i in ids: _vs().state.heroLevels[str(i)] = lv
			if key == "remax":
				for g in _vs().state.gear: if typeof(g) == TYPE_DICTIONARY: g.level = MAX_ITEM_LEVEL
				if c: c.hp = c.max_hp
			_vs().write_state()
		"item":
			var kind: String = str(v[0]) if v is Array else "weapon"
			var il: int = clampi(int(v[1]) if v is Array else MAX_ITEM_LEVEL, 0, MAX_ITEM_LEVEL)
			var it: Dictionary = _vs().base_item(kind, 0); it.id = "%s_owner_%d" % [kind, Time.get_ticks_msec()]; it.level = il
			_vs().state.gear.append(it); _vs().write_state()
		"kill":
			if party == null or party.director.living().is_empty(): said.emit("No active enemies."); return false
			for e in party.director.living(): e.take_damage(1 << 30, e.global_position)
		"spawn_enemy", "titan", "spawn_boss":
			if party == null: return false
			var tid := "titan" if key == "titan" else str(v)
			if key != "spawn_enemy":
				for e in party.director.living(): if e.is_boss(): said.emit("Only one boss at a time."); return false
			var hp: Vector3 = main.hero.global_position; var f: Vector3 = -main.hero_vis.global_transform.basis.z
			party.director.spawn(tid, hp + f * (14.0 if tid == "titan" else 8.0), main.hero)
		"spawn_worldboss":
			if main == null: return false
			said.emit("World Boss: the Ashen Titan roams nearby.")
			return main.spawn_world_boss(true)
		"fight_test":
			if party == null: return false
			var hp2: Vector3 = main.hero.global_position
			for i in 2: party.director.spawn(FOES[i], hp2 + Vector3(cos(i * PI) * 9.0, 0, sin(i * PI + 0.5) * 9.0), main.hero)
		"tp_zone":
			if main: return main.cheat_tp_zone(str(v))
		"online_list": return _net().owner_list()
		"online_jump": return _net().owner_jump(str(v))
		"coowner_jump": return _net().coowner_jump(str(v))
		"coowner_lock": coowner_ok = false; return _net().coowner_lock()
		"lock", "panel", "dev": pass
		_: return false
	return true

func _process(_dt: float) -> void:
	var c = _combat()
	if c == null: return
	# re-check role every frame: if a gate locks, the self cheats stop applying
	var r := role()
	if r == "": 
		if flags.god or flags.unlimited or flags.nocd or flags.fly or flags.noclip or flags.speed != 1.0 or flags.titan_form: _clear_all()
		return
	if flags.god: c.hp = c.max_hp
	if flags.unlimited: c.st.mp = 100.0; c.st.sp = 100.0
	if flags.nocd: for i in c.st.cd.size(): c.st.cd[i] = 0.0
	if flags.inf_gold and r == "owner" and int(_vs().state.get("gold", 0)) < GOLD_CAP: _vs().state.gold = GOLD_CAP

func _clear_all() -> void:
	for k in ["god", "unlimited", "nocd", "fly", "noclip", "titan_form", "inf_gold"]: flags[k] = false
	flags.speed = 1.0
	if main:
		main.cheat.fly = false; main.cheat.speed = 1.0; main.hero.collision_mask = 1; main.hero_vis.scale = Vector3.ONE
