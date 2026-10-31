class_name CombatData
## Combat data ported 1:1 from the JS game (www/proto3d/combat/data.js + herokits.js @ 659b86e),
## dumped to combat_data.json. Godot-side tuning that differs from JS lives in PORT below.
const JSON_PATH := "res://combat/combat_data.json"
static var _d: Dictionary = {}

## Port-only tuning (boss rules): basic attacks are spammable (fixed short interval, no stamina,
## no combo timing); skills keep JS cooldowns; enemies take several hits ("semi-slow");
## only the Owner is overpowered. HP here = average non-Owner basic hits to kill x avg hit (38).
const PORT := {
	"basic_interval": 0.3,          # = JS basic cd 0.5 x basicCdMul 0.6; no stamina, no timing window
	"hits_to_kill": {"wolf": 10, "raider": 12, "frosttroll": 45, "frosttroll_a": 60, "frosttroll_b": 60,
		"titan": 140, "titan_volcano": 220},
	"avg_hit": 38.0,
}

static func data() -> Dictionary:
	if _d.is_empty():
		_d = JSON.parse_string(FileAccess.get_file_as_string(JSON_PATH))
	return _d

static func kit(hero_id: String) -> Dictionary:
	var d := data()
	if hero_id == "owner":
		var sk := []
		# test 25: Holy Destruction gets its own button (slot 5)
		# test 27 (boss): Sovereign's Wrath removed; Unholy (slot 3) + Holy (slot 4) on the normal buttons, clear of Jump
		for k in ["royal", "chains", "unholy", "holy"]: sk.append(d.OWNER_SKILLS[k])
		return {"color": "#ffd700", "basic": "Saber slash", "skills": sk, "owner": true}
	if d.KITS.has(hero_id): return d.KITS[hero_id]
	# Pip / Phoenix / Wren have no kit in the JS game: generic kit from ABILITIES (heavy, secondary, class, ultimate), saber flag removed.
	var g := []
	for i in [1, 3, 2, 5]:
		var a: Dictionary = d.ABILITIES[i].duplicate(true); a.erase("saber"); a.id = hero_id + "." + a.id
		if i == 5: a.fury = 100
		g.append(a)
	return {"color": "#ffffff", "basic": "Basic attack", "skills": g, "generic": true}

static func enemy(key: String) -> Dictionary:
	var d := data()
	var src := "titan" if key == "titan_volcano" else key
	var e: Dictionary = d.ENEMIES[src].duplicate(true)
	e.js_hp = e.hp
	if PORT.hits_to_kill.has(key): e.hp = int(PORT.hits_to_kill[key] * PORT.avg_hit)
	if key == "titan_volcano": e.name = "Ashen Titan (Volcano)"
	return e

static func patterns(key: String) -> Array:
	var d := data()
	return d.BOSS_PATTERNS.get(key, [])
