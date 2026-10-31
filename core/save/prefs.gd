extends Node
## Port of www/proto3d/camprefs.js. Same key/shape (vn_p3d_prefs_v1), stored as JSON in user://.
## Godot adds 'ultra' to QUALITIES (the JS game had no Ultra tier).
signal changed(prefs: Dictionary)

const PREF_KEY := "vn_p3d_prefs_v1"
const ZOOM_MIN := 0.4
const ZOOM_MAX := 1.7
const SENS_MIN := 0.4
const SENS_MAX := 2.5
const CAM_MODES := ["follow", "free"]
const VIEWS := ["third", "first"]
const QUALITIES := ["auto", "ultra", "high", "balanced", "low"]
## quality -> render tier index used by scripts/main.gd (0 Low,1 Medium,2 High,3 Ultra)
const QUALITY_TIER := {"auto": 2, "ultra": 3, "high": 2, "balanced": 1, "low": 0}
const DEFAULT_PREFS := {"view": "third", "zoom": 1.0, "zoomSens": 1.0, "lookSens": 1.0, "quality": "auto", "shadows": true,
	"showFps": false, "fpsSet": false, "combatSet": false, "combat": true, "camMode": "follow"}

var path := "user://%s.json" % PREF_KEY
var prefs: Dictionary = {}

func _ready() -> void:
	prefs = load_prefs()

static func _num(v, d: float) -> float:
	return float(v) if (typeof(v) == TYPE_FLOAT or typeof(v) == TYPE_INT) and is_finite(float(v)) else d

static func clamp_zoom(z) -> float:
	return clampf(_num(z, 1.0), ZOOM_MIN, ZOOM_MAX)

static func sanitize(p) -> Dictionary:
	var o: Dictionary = p if typeof(p) == TYPE_DICTIONARY else {}
	var d := DEFAULT_PREFS
	var fps_set: bool = o.get("fpsSet") == true
	var combat_set: bool = o.get("combatSet") == true
	return {
		"view": o.get("view") if o.get("view") in VIEWS else d.view,
		"zoom": clamp_zoom(o.get("zoom")),
		"zoomSens": clampf(_num(o.get("zoomSens"), 1.0), SENS_MIN, SENS_MAX),
		"lookSens": clampf(_num(o.get("lookSens"), 1.0), SENS_MIN, SENS_MAX),
		"quality": o.get("quality") if o.get("quality") in QUALITIES else d.quality,
		"shadows": o.get("shadows") != false,
		"fpsSet": fps_set, "showFps": fps_set and o.get("showFps") == true,
		"combatSet": combat_set, "combat": (o.get("combat") == true) if combat_set else true,
		"camMode": o.get("camMode") if o.get("camMode") in CAM_MODES else d.camMode,
	}

func load_prefs() -> Dictionary:
	if not FileAccess.file_exists(path): return sanitize(null)
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null: return sanitize(null)
	return sanitize(JSON.parse_string(f.get_as_text()))

func save_prefs() -> bool:
	prefs = sanitize(prefs)
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null: return false
	f.store_string(JSON.stringify(prefs))
	changed.emit(prefs)
	return true

func set_pref(k: String, v) -> void:
	prefs[k] = v
	save_prefs()

func restore_defaults() -> void:
	prefs = DEFAULT_PREFS.duplicate()
	save_prefs()

func tier() -> int:
	return QUALITY_TIER.get(prefs.get("quality", "auto"), 2)
