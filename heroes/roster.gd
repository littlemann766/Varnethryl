class_name HeroRoster
## Playable roster. Heights in metres (foot to head). Approved by the boss: Pip 0.52, Phoenix 0.756,
## Wren 1.35, Owner 1.905. The rest come from charscale.js HERO_LORE_HEIGHTS (inches x 0.0254).
const HERO_M := 1.905
const APPROVED := {"owner": 1.905, "pip": 0.52, "phoenix": 0.756, "wren": 1.35}
const LORE_IN := {"aldric": 74, "darius": 74, "selene": 69, "elira": 68, "orin": 72, "seraphine": 70, "talia": 70,
	"finn": 69, "brynn": 64, "mirelle": 66, "nyx": 67, "vesper": 70, "thorne": 73, "rook": 75,
	"asha": 71, "rowan": 73, "kael": 71, "cedric": 72, "morwen": 69, "garruk": 82}
## Model sources (copied + dequantized into res://heroes/models/<id>.glb):
const SOURCES := {
	"owner": "rigged/owner_new5_fight_refined2.glb", "pip": "rigged/pip_new3_fight_refined2.glb",
	"phoenix": "rigged/phoenix_new3.glb", "wren": "rigged/wren_new6_fight_refined2.glb",
	"garruk": "rigged/garruk_new5_arms_fight_refined2.glb", "selene": "rigged/selene_new_arms_refined2.glb",
	"darius": "rigged/darius_new6_fight_refined2.glb", "asha": "rigged/asha_new3_arms_refined2.glb",
	"_other": "rigged/<id>_refined2.glb",
}
const ORDER := ["owner", "pip", "phoenix", "wren", "aldric", "elira", "rowan", "thorne", "nyx", "seraphine", "garruk",
	"mirelle", "cedric", "morwen", "kael", "vesper", "talia", "orin", "selene", "darius", "finn", "brynn", "asha", "rook"]

static func height(id: String) -> float:
	var c = CharacterRig.index().characters.get(id)
	if c: return float(c.height_m)
	if APPROVED.has(id): return APPROVED[id]
	if LORE_IN.has(id): return LORE_IN[id] * 0.0254
	return HERO_M

## Test 6: Beth's characters (res://characters, LOD1 = ~50% tris / 1024 tex, size baked on the armature root).
static func model(id: String, other := false) -> String:
	if not VOXEL.has(id): return CharacterRig.char_path(id)
	var lp: String = VOXEL[id].replace(".glb", "_lod1.glb")
	return lp if (lod1 or (other and comp_lod1)) and ResourceLoader.exists(lp) else VOXEL[id]
## test 27: companions / remote players use the voxel LOD1 on Low + Medium (your own hero is always LOD0)
static var comp_lod1 := false

## voxel-heroes (Lucian, varn-core heroes-motion-pass dcfc9b2 handoff/godot/voxel_trial/capes_v1): Owner, Selene and
## Darius use the voxel models (same skeleton/bone names, mocap idle/walk/run, cape cubes baked into every clip).
const VOXEL := {"owner": "res://voxel/owner_voxel.glb", "selene": "res://voxel/selene_voxel.glb", "darius": "res://voxel/darius_voxel.glb",
	# test 27: Beth voxel_cast batch 1 (fixed capes/boots/robe) + batch 2
	"aldric": "res://voxel/aldric_voxel.glb", "elira": "res://voxel/elira_voxel.glb", "rowan": "res://voxel/rowan_voxel.glb", "thorne": "res://voxel/thorne_voxel.glb", "nyx": "res://voxel/nyx_voxel.glb", "seraphine": "res://voxel/seraphine_voxel.glb", "garruk": "res://voxel/garruk_voxel.glb", "mirelle": "res://voxel/mirelle_voxel.glb", "cedric": "res://voxel/cedric_voxel.glb", "morwen": "res://voxel/morwen_voxel.glb", "kael": "res://voxel/kael_voxel.glb",
	# test 27: batch 3 (Pip/Phoenix keep their own walk/run clips: no ROOT_SPEED)
	"vesper": "res://voxel/vesper_voxel.glb", "talia": "res://voxel/talia_voxel.glb", "orin": "res://voxel/orin_voxel.glb", "finn": "res://voxel/finn_voxel.glb", "brynn": "res://voxel/brynn_voxel.glb", "asha": "res://voxel/asha_voxel.glb", "rook": "res://voxel/rook_voxel.glb", "wren": "res://voxel/wren_voxel.glb", "pip": "res://voxel/pip_voxel.glb", "phoenix": "res://voxel/phoenix_voxel.glb"}
## test 26: Low tier loads <id>_voxel_lod1.glb when it exists (Beth batch 1; ~33% tris). Set by main.apply_quality().
static var lod1 := false
## In-place walk/run clips: root speed (m/s) each clip was authored at, so playback is matched to real movement.
const ROOT_SPEED := {"owner": [1.12, 6.98], "selene": [0.96, 5.55], "darius": [1.02, 5.85],
	"town_guard": [1.04, 6.11],
	"aldric": [0.96, 5.15], "elira": [0.88, 4.72], "rowan": [0.94, 5.08], "thorne": [0.94, 5.07], "nyx": [0.87, 4.66], "holyknight_villain": [1.19, 7.10],
	"seraphine": [0.90, 4.87], "garruk": [1.13, 6.81], "mirelle": [0.85, 4.58], "cedric": [0.93, 5.01], "morwen": [0.90, 4.80], "kael": [0.92, 4.93],
	"vesper": [0.90, 4.85], "talia": [0.91, 4.87], "orin": [0.93, 4.99], "finn": [0.89, 4.79], "brynn": [0.82, 4.44], "asha": [0.95, 5.53], "rook": [0.97, 5.22], "wren": [0.77, 4.67]}

static func display_name(id: String) -> String: return id.capitalize()

## Movement speed (m/s): hero 6 m/s like the test build, small heroes a bit slower, never > 1.6x (SPEED_CAP).
static func speed(id: String) -> float:
	var h := height(id)
	return 6.0 * clamp(0.75 + 0.25 * h / HERO_M, 0.8, 1.6)

## Charscale conflicts with the approved values (reported, approved wins).
const CONFLICTS := [
	"pip/phoenix/wren: not in charscale.js CHARS, so JS falls back to DEFAULT 1.905 m; approved 0.52 / 0.756 / 1.35 m used",
	"n:frosttroll_a/b: charscale height 3.5 x HERO_M (6.67 m) and ENEMIES scale 3.5; approved 3x (5.715 m) used",
	"n:ashentitan_new: charscale height 10 x HERO_M (19.05 m); approved 6x (11.43 m) used (ENEMIES.titan.scale is 6, agrees)",
]
