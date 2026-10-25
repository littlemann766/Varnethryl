class_name InteriorDefs
## Per-building interior layouts, read off card_<name>.jpg floor plans (u,v in [-0.5,0.5]; +v = door wall).
## walls: [floor,u1,v1,u2,v2,[[t,width],...],mat]   stairs: [floor,u,v,ascent_deg(0 = toward back),width]
## ladders: [floor,u,v,deg]  props: [kit_name|_proc, floor,u,v,rot_deg,[extra]]  lights: [kind,floor,u,v,rot,energy,range,shadow]
## rooms: [label,floor,u,v] -> walk-test waypoints.   Kit props face +Z.
const CARD := {"inn": "card_inn.jpg", "guildhall": "card_guild_hall.png", "townhall": "card_town_hall.jpg",
	"smithy": "card_blacksmith.jpg", "bakery": "card_bakery.jpg", "temple": "card_temple.jpg"}

const D := {
# ---------------- INN: ground = entrance, common room, bar, kitchen, pantry, storage; upper = hall, bedrooms A-C, sitting (rumor) room, balcony
"inn": {"name": "Inn of Varnethryl",
	"floors": [{"h": 4.2, "mat": "flag", "wall": "stone", "win": 4.5}, {"h": 3.6, "mat": "oak", "wall": "plaster", "win": 4.5}],
	"walls": [
		[0, 0.0, -0.08, 0.5, -0.08, [[0.25, 2.2]]],          # kitchen behind bar
		[0, -0.5, -0.22, 0.0, -0.22, [[0.3, 1.6], [0.8, 1.6]]], # pantry/storage front wall
		[0, -0.25, -0.5, -0.25, -0.22, []],
		[0, 0.0, -0.5, 0.0, -0.08, [[0.6, 1.6]]],
		[1, -0.5, -0.12, 0.5, -0.12, [[0.17, 1.4], [0.5, 1.4], [0.83, 1.4]]],  # bedrooms A B C
		[1, -0.17, -0.5, -0.17, -0.12, []], [1, 0.17, -0.5, 0.17, -0.12, []],
		[1, -0.15, -0.12, -0.15, 0.5, [[0.4, 1.4]]],          # sitting room (rumor corner)
	],
	"stairs": [[0, 0.42, 0.42, 0, 2.0]],
	"rails": [[1, 0.36, 0.15, 90, 2]],
	"props": [
		["hearth", 0, -0.48, 0.12, 90], ["rug", 0, -0.33, 0.12, 90],
		["table", 0, -0.33, 0.3, 0], ["bench", 0, -0.33, 0.37, 180], ["bench", 0, -0.33, 0.23, 0],
		["table", 0, -0.14, 0.3, 0], ["chair", 0, -0.17, 0.38, 180], ["chair", 0, -0.11, 0.38, 180], ["chair", 0, -0.14, 0.22, 0],
		["table", 0, -0.22, 0.0, 90], ["chair", 0, -0.25, 0.0, 90], ["chair", 0, -0.19, 0.0, -90],
		["_round_table", 0, 0.12, 0.3, 0, [0.7, 4]],
		["bar_counter", 0, 0.12, 0.02, 0], ["bar_counter", 0, 0.24, 0.02, 0], ["stool", 0, 0.08, 0.08, 0], ["stool", 0, 0.13, 0.08, 0],
		["stool", 0, 0.19, 0.08, 0], ["stool", 0, 0.25, 0.08, 0], ["bottles", 0, 0.1, 0.02, 0, [1.42, false]], ["bottles", 0, 0.22, 0.02, 0, [1.42, false]],
		["apothecary_shelf", 0, 0.12, -0.065, 0], ["apothecary_shelf", 0, 0.22, -0.065, 0], ["keg", 0, 0.32, -0.03, 0], ["keg", 0, 0.35, -0.03, 0],
		["hearth", 0, 0.3, -0.48, 0], ["table", 0, 0.25, -0.3, 0], ["_pots", 0, 0.25, -0.3, 0, [1.4]], ["keg", 0, 0.45, -0.4, 0], ["chest", 0, 0.42, -0.2, -90],
		["keg", 0, -0.45, -0.45, 0], ["keg", 0, -0.4, -0.45, 0], ["chest", 0, -0.35, -0.44, 0], ["apothecary_shelf", 0, -0.12, -0.47, 0], ["chest", 0, -0.18, -0.3, 0],
		["lion_banner", 0, -0.05, 0.48, 180, [1.2, false]], ["lion_banner", 0, 0.05, -0.075, 0, [1.4, false]],
		["bed", 1, -0.33, -0.4, 0], ["wardrobe", 1, -0.22, -0.47, 0], ["chest", 1, -0.33, -0.22, 180],
		["bed", 1, 0.0, -0.4, 0], ["wardrobe", 1, 0.11, -0.47, 0], ["rug", 1, 0.0, -0.26, 0],
		["bed", 1, 0.33, -0.4, 0], ["wardrobe", 1, 0.44, -0.47, 0], ["chest", 1, 0.33, -0.22, 180],
		["_round_table", 1, -0.33, 0.22, 0, [0.6, 4]], ["lion_banner", 1, -0.49, 0.22, 90, [0.6, false]], ["quest_board", 1, -0.33, 0.48, 180],
		["bookshelf", 1, -0.17, 0.32, -90], ["rug", 1, -0.33, 0.22, 0], ["lion_banner", 1, 0.0, 0.48, 180, [0.6, false]],
		["bench", 1, 0.1, 0.45, 180],
	],
	"lights": [["chandelier", 0, -0.25, 0.18, 0, 3.0, 16.0, true], ["chandelier", 0, 0.15, 0.22, 0, 2.0, 12.0],
		["fire", 0, -0.46, 0.12, 0, 1.8, 7.0], ["lantern", 0, 0.18, -0.075, 0, 1.2, 7.0], ["lantern", 0, 0.25, -0.49, 0, 1.0, 7.0], ["lantern", 0, -0.35, -0.49, 0, 0.8, 6.0],
		["lantern", 1, -0.33, -0.12, 180, 0.9, 6.0], ["lantern", 1, 0.0, -0.12, 180, 0.9, 6.0], ["lantern", 1, 0.33, -0.12, 180, 0.9, 6.0],
		["chandelier", 1, -0.33, 0.22, 0, 1.6, 9.0, true], ["lantern", 1, 0.2, 0.49, 180, 1.0, 8.0]],
	"rooms": [["Common Room", 0, -0.3, 0.15], ["Bar", 0, 0.15, 0.15], ["Kitchen", 0, 0.25, -0.2], ["Pantry", 0, -0.38, -0.33], ["Storage", 0, -0.12, -0.38],
		["Hallway", 1, 0.0, 0.05], ["Bedroom A", 1, -0.33, -0.25], ["Bedroom B", 1, 0.0, -0.22], ["Bedroom C", 1, 0.33, -0.25], ["Rumor Corner", 1, -0.33, 0.1], ["Balcony", 1, 0.2, 0.4]]},

# ---------------- GUILD HALL: foyer, main hall w/ quest board, meeting table, stair & upper balcony overlooking hall
"guildhall": {"name": "Guild Hall of Varnethryl",
	"floors": [{"h": 6.0, "mat": "flag", "wall": "stone", "win": 4.0},
		{"h": 4.0, "mat": "oak", "wall": "plaster", "win": 4.0, "slab": [[-0.5, -0.5, -0.24, 0.5], [0.24, -0.5, 0.5, 0.5], [-0.24, 0.3, 0.24, 0.5]]}],
	"walls": [
		[0, -0.5, 0.3, 0.5, 0.3, [[0.5, 5.0, 4.5], [0.15, 2.0], [0.85, 2.0]]],   # foyer
		[0, -0.24, -0.5, -0.24, 0.3, [[0.55, 3.0]]], [0, 0.24, -0.5, 0.24, 0.3, [[0.55, 3.0]]],
		[1, -0.5, -0.1, -0.24, -0.1, [[0.5, 1.6]]], [1, 0.24, -0.1, 0.5, -0.1, [[0.5, 1.6]]],
	],
	"stairs": [[0, 0.37, 0.25, 0, 2.2]],
	"rails": [[1, -0.24, -0.45, 90, 6], [1, 0.24, -0.45, 90, 6], [1, -0.22, 0.3, 0, 4]],
	"props": [
		["_runner", 0, 0.0, 0.0, 0, [0.94, 2.4]], ["hearth", 0, 0.0, -0.48, 0], ["throne_dais", 0, 0.0, -0.36, 0],
		["lion_banner", 0, -0.1, -0.49, 0, [2.5, false]], ["lion_banner", 0, 0.1, -0.49, 0, [2.5, false]],
		["lion_banner", 0, -0.235, -0.2, 90, [2.8, false]], ["lion_banner", 0, 0.235, -0.2, -90, [2.8, false]],
		["bench", 0, -0.14, 0.0, 90], ["bench", 0, -0.14, 0.12, 90], ["bench", 0, 0.14, 0.0, -90], ["bench", 0, 0.14, 0.12, -90],
		["armor_stand", 0, -0.2, 0.43, 90], ["armor_stand", 0, 0.2, 0.43, -90], ["rug", 0, 0.0, 0.4, 0],
		["meeting_table", 0, -0.37, -0.2, 90], ["chair", 0, -0.33, -0.3, -90], ["chair", 0, -0.33, -0.2, -90], ["chair", 0, -0.33, -0.1, -90],
		["chair", 0, -0.41, -0.3, 90], ["chair", 0, -0.41, -0.2, 90], ["chair", 0, -0.41, -0.1, 90], ["bookshelf", 0, -0.49, -0.42, 90], ["lion_banner", 0, -0.37, -0.49, 0, [1.8, false]],
		["quest_board", 0, 0.37, -0.48, 0], ["quest_board", 0, 0.49, -0.3, -90], ["quest_board", 0, 0.49, -0.1, -90], ["table", 0, 0.37, -0.25, 0], ["chair", 0, 0.37, -0.2, 180], ["chest", 0, 0.28, -0.45, 0],
		["bookshelf", 1, -0.49, -0.35, 90], ["bookshelf", 1, -0.49, -0.25, 90], ["lectern", 1, -0.38, -0.3, 0], ["table", 1, -0.38, 0.15, 0], ["chair", 1, -0.38, 0.2, 180],
		["chest", 1, 0.4, -0.4, 0], ["chest", 1, 0.45, -0.3, -90], ["wardrobe", 1, 0.49, -0.2, -90], ["lion_banner", 1, 0.0, 0.48, 180, [0.8, false]],
	],
	"lights": [["chandelier", 0, 0.0, -0.15, 0, 4.0, 20.0, true], ["chandelier", 0, 0.0, 0.12, 0, 2.5, 14.0], ["fire", 0, 0.0, -0.46, 0, 2.0, 8.0],
		["chandelier", 0, -0.37, -0.2, 0, 2.0, 11.0], ["lantern", 0, 0.37, -0.49, 0, 1.4, 8.0], ["lantern", 0, -0.1, 0.31, 180, 1.0, 7.0], ["lantern", 0, 0.1, 0.31, 180, 1.0, 7.0],
		["lantern", 1, -0.4, -0.49, 0, 1.0, 8.0], ["lantern", 1, 0.4, -0.49, 0, 1.0, 8.0], ["lantern", 1, 0.0, 0.49, 180, 1.0, 8.0]],
	"rooms": [["Entrance Foyer", 0, 0.0, 0.4], ["Main Hall", 0, 0.0, -0.1], ["Meeting Table", 0, -0.37, 0.05], ["Quest Board", 0, 0.37, -0.15],
		["Upper Balcony", 1, 0.0, 0.4], ["Library Archive", 1, -0.37, 0.1], ["Storage", 1, 0.37, -0.3], ["Balcony Overlook", 1, -0.37, -0.3]]},

# ---------------- TOWN HALL: great court hall (checker floor), quest board area, tower stairs; upper: council room (round table), archives
"townhall": {"name": "Town Hall of Varnethryl",
	"floors": [{"h": 6.5, "mat": "checker", "wall": "palestone", "win": 3.5}, {"h": 4.5, "mat": "checker", "wall": "palestone", "win": 3.5}],
	"walls": [
		[0, -0.3, -0.5, -0.3, 0.5, [[0.35, 2.4], [0.75, 2.4]]], [0, 0.3, -0.5, 0.3, 0.5, [[0.35, 2.4], [0.75, 2.4]]],
		[1, -0.5, -0.05, 0.5, -0.05, [[0.15, 1.8], [0.5, 2.4], [0.85, 1.8]]],
		[1, -0.3, -0.5, -0.3, -0.05, []], [1, 0.3, -0.5, 0.3, -0.05, []],
	],
	"stairs": [[0, -0.45, 0.45, 0, 2.0], [0, 0.45, 0.45, 0, 2.0]],
	"props": [
		["_runner", 0, 0.0, 0.0, 0, [0.9, 2.6]], ["_area", 0, 0.0, -0.1, 0, [3.0, 3.0, "blue"]], ["throne_dais", 0, 0.0, -0.4, 0],
		["lion_banner", 0, 0.0, -0.49, 0, [2.8, false]], ["_glasswall", 0, -0.12, -0.49, 0, [1.6, 3.6, 2.2]], ["_glasswall", 0, 0.12, -0.49, 0, [1.6, 3.6, 2.2]],
		["lion_banner", 0, -0.29, -0.3, 90, [3.0, false]], ["lion_banner", 0, -0.29, 0.1, 90, [3.0, false]], ["lion_banner", 0, 0.29, -0.3, -90, [3.0, false]], ["lion_banner", 0, 0.29, 0.1, -90, [3.0, false]],
		["pew", 0, -0.15, 0.1, 0], ["pew", 0, 0.15, 0.1, 0], ["pew", 0, -0.15, 0.22, 0], ["pew", 0, 0.15, 0.22, 0], ["pew", 0, -0.15, -0.02, 0], ["pew", 0, 0.15, -0.02, 0],
		["quest_board", 0, -0.49, -0.2, 90], ["quest_board", 0, -0.4, -0.48, 0], ["table", 0, -0.4, -0.25, 90], ["chair", 0, -0.36, -0.25, -90], ["lectern", 0, -0.42, 0.05, 90],
		["bookshelf", 0, 0.49, -0.35, -90], ["bookshelf", 0, 0.49, -0.15, -90], ["table", 0, 0.4, -0.25, 90], ["chair", 0, 0.44, -0.25, 90], ["chest", 0, 0.4, 0.05, 0],
		["_round_table", 1, 0.0, -0.28, 0, [2.0, 10]], ["lion_banner", 1, 0.0, -0.49, 0, [1.0, false]], ["_area", 1, 0.0, -0.28, 0, [7.0, 6.0, "blue"]],
		["bookshelf", 1, -0.49, -0.4, 90], ["bookshelf", 1, -0.49, -0.22, 90], ["bookshelf", 1, -0.4, -0.48, 0], ["table", 1, -0.38, -0.25, 0], ["rug", 1, -0.38, -0.25, 0], ["ladder", 1, -0.32, -0.48, 0, [0.0, false]],
		["bookshelf", 1, 0.49, -0.4, -90], ["bookshelf", 1, 0.49, -0.22, -90], ["bookshelf", 1, 0.4, -0.48, 0], ["lectern", 1, 0.38, -0.25, 180],
		["lion_banner", 1, -0.25, 0.49, 180, [1.0, false]], ["lion_banner", 1, 0.25, 0.49, 180, [1.0, false]],
		["bench", 1, 0.0, 0.3, 180], ["rug", 1, 0.0, 0.2, 0],
	],
	"lights": [["chandelier", 0, 0.0, -0.1, 0, 4.0, 20.0, true], ["chandelier", 0, 0.0, 0.25, 0, 2.5, 14.0],
		["lantern", 0, -0.49, -0.35, 90, 1.2, 8.0], ["lantern", 0, 0.49, 0.0, -90, 1.2, 8.0], ["lantern", 0, -0.29, 0.45, -90, 1.0, 7.0], ["lantern", 0, 0.29, 0.45, 90, 1.0, 7.0],
		["chandelier", 1, 0.0, -0.3, 0, 3.0, 14.0, true], ["lantern", 1, -0.4, 0.49, 180, 1.0, 8.0], ["lantern", 1, 0.4, 0.49, 180, 1.0, 8.0], ["lantern", 1, 0.0, 0.49, 180, 1.0, 8.0]],
	"rooms": [["Great Court Hall", 0, 0.0, 0.3], ["Quest Board Area", 0, -0.4, -0.1], ["Records Office", 0, 0.4, -0.1],
		["Council Room", 1, 0.0, -0.15], ["Archives", 1, -0.4, -0.15], ["East Archives", 1, 0.4, -0.15], ["Upper Gallery", 1, 0.0, 0.3]]},

# ---------------- BLACKSMITH: forge room, armor display, weapon wall & workshop; upper floor storage loft via ladder
"smithy": {"name": "Blacksmith of Varnethryl",
	"floors": [{"h": 4.0, "mat": "stone", "wall": "stone", "win": 5.0, "stairmat": "darkoak"}, {"h": 3.0, "mat": "darkoak", "wall": "stone", "win": 0.0, "slab": [[-0.5, -0.5, 0.5, -0.05]]}],
	"ladders": [[0, -0.3, -0.05, 0]],
	"rails": [[1, -0.18, -0.05, 0, 4]],
	"props": [
		["forge", 0, 0.15, -0.44, 0], ["anvil", 0, 0.15, -0.22, 0], ["keg", 0, 0.32, -0.25, 0], ["weapon_rack", 0, 0.48, -0.25, -90], ["weapon_rack", 0, 0.48, 0.0, -90],
		["weapon_rack", 0, 0.48, 0.25, -90], ["table", 0, 0.3, 0.1, 90], ["table", 0, -0.05, -0.2, 0],
		["armor_stand", 0, -0.45, 0.1, 90], ["armor_stand", 0, -0.45, 0.25, 90], ["lion_banner", 0, -0.49, 0.18, 90, [1.2, false]], ["chest", 0, -0.35, 0.4, 0],
		["table", 0, -0.32, 0.25, 90], ["keg", 0, -0.45, -0.4, 0], ["chest", 0, -0.42, -0.25, 90],
		["chest", 1, -0.4, -0.4, 0], ["chest", 1, -0.25, -0.42, 0], ["keg", 1, 0.0, -0.42, 0], ["keg", 1, 0.06, -0.42, 0], ["wardrobe", 1, 0.3, -0.45, 0], ["weapon_rack", 1, 0.45, -0.25, -90],
	],
	"lights": [["fire", 0, 0.15, -0.4, 0, 4.0, 14.0, true], ["lantern", 0, -0.49, -0.1, 90, 1.2, 9.0], ["lantern", 0, 0.3, 0.49, 180, 1.0, 8.0], ["lantern", 1, 0.0, -0.49, 0, 1.0, 8.0]],
	"rooms": [["Forge Room", 0, 0.1, -0.1], ["Armor Display", 0, -0.3, 0.1], ["Weapon Wall", 0, 0.35, 0.3], ["Storage Loft", 1, 0.0, -0.3]]},

# ---------------- BAKERY: ground front shop (blue tile) + stairs; upper kitchen (oven), storage, seating area
"bakery": {"name": "Bakery of Varnethryl",
	"floors": [{"h": 3.8, "mat": "bluecheck", "wall": "plaster", "win": 4.0}, {"h": 3.4, "mat": "oak", "wall": "plaster", "win": 4.0}],
	"walls": [[0, 0.25, -0.5, 0.25, 0.5, [[0.85, 2.0]]],
		[1, -0.5, 0.0, 0.25, 0.0, [[0.3, 2.0]]], [1, 0.25, -0.5, 0.25, 0.5, [[0.85, 2.0]]]],
	"stairs": [[0, 0.38, 0.35, 0, 2.0]],
	"props": [
		["bread_rack", 0, -0.3, -0.47, 0], ["bread_rack", 0, -0.12, -0.47, 0], ["bread_rack", 0, -0.47, -0.25, 90], ["bread_rack", 0, -0.47, 0.0, 90],
		["_counter", 0, -0.2, -0.15, 0, [4.0, 1.0, 0.8]], ["_counter", 0, -0.47, 0.3, 90, [2.4, 0.9, 0.7]], ["_counter", 0, 0.05, 0.1, 90, [2.0, 0.9, 0.7]],
		["keg", 0, 0.15, -0.4, 0], ["chest", 0, 0.12, 0.35, 0], ["lion_banner", 0, -0.2, -0.49, 0, [1.0, false]],
		["apothecary_shelf", 0, 0.47, -0.35, -90], ["apothecary_shelf", 0, 0.47, -0.15, -90], ["keg", 0, 0.32, -0.45, 0],
		["bakery_oven", 1, -0.3, -0.42, 0], ["table", 1, -0.25, -0.15, 0], ["_pots", 1, -0.05, -0.2, 0, [1.6]], ["apothecary_shelf", 1, 0.0, -0.47, 0], ["keg", 1, -0.47, -0.1, 0],
		["apothecary_shelf", 1, 0.47, -0.4, -90], ["keg", 1, 0.32, -0.45, 0], ["keg", 1, 0.38, -0.45, 0], ["chest", 1, 0.45, -0.15, -90],
		["_round_table", 1, -0.25, 0.25, 0, [0.7, 4]], ["bench", 1, -0.47, 0.25, 90], ["bench", 1, -0.25, 0.47, 180], ["_round_table", 1, 0.05, 0.3, 0, [0.6, 3]],
	],
	"lights": [["lantern", 0, -0.2, -0.49, 0, 1.5, 9.0], ["chandelier", 0, -0.15, 0.1, 0, 2.6, 12.0, true], ["lantern", 0, 0.4, 0.0, -90, 1.0, 7.0],
		["fire", 1, -0.3, -0.35, 0, 2.5, 9.0, true], ["lantern", 1, -0.2, 0.49, 180, 1.2, 8.0], ["lantern", 1, 0.4, -0.2, -90, 0.9, 6.0]],
	"rooms": [["Front Shop", 0, -0.2, 0.25], ["Stair Hall", 0, 0.38, -0.2], ["Kitchen", 1, -0.25, -0.25], ["Seating Area", 1, -0.25, 0.1], ["Storage", 1, 0.38, -0.3]]},

# ---------------- TEMPLE: nave w/ pews + high altar, healing chambers (E, fountain), crypt-adjacent shrine (W), upper gallery overlooking nave
"temple": {"name": "Temple of Varnethryl", "scale": [0.82, 0.82],
	"floors": [{"h": 7.0, "mat": "palestone", "wall": "palestone", "win": 3.5},
		{"h": 5.0, "mat": "palestone", "wall": "palestone", "win": 3.5, "slab": [[-0.5, -0.5, -0.2, 0.5], [0.2, -0.5, 0.5, 0.5]]}],
	"walls": [[0, -0.2, -0.3, -0.2, 0.2, [[0.5, 3.0]]], [0, 0.2, -0.3, 0.2, 0.2, [[0.5, 3.0]]],
		[0, -0.5, -0.3, -0.2, -0.3, []], [0, 0.2, -0.3, 0.5, -0.3, []], [0, -0.5, 0.2, -0.2, 0.2, []], [0, 0.2, 0.2, 0.5, 0.2, []]],
	"stairs": [[0, -0.37, 0.47, 0, 2.2], [0, 0.37, 0.47, 0, 2.2]],
	"rails": [[1, -0.2, -0.47, 90, 9], [1, 0.2, -0.47, 90, 9]],
	"props": [
		["_runner", 0, 0.0, 0.03, 0, [0.88, 2.4]], ["altar", 0, 0.0, -0.43, 0], ["_area", 0, 0.0, -0.43, 0, [6.0, 4.0, "blue"]],
		["_glasswall", 0, 0.0, -0.495, 0, [3.0, 5.0, 1.8]], ["lion_banner", 0, -0.12, -0.49, 0, [2.5, false]], ["lion_banner", 0, 0.12, -0.49, 0, [2.5, false]],
		["pew", 0, -0.1, -0.2, 0], ["pew", 0, 0.1, -0.2, 0], ["pew", 0, -0.1, -0.12, 0], ["pew", 0, 0.1, -0.12, 0], ["pew", 0, -0.1, -0.04, 0], ["pew", 0, 0.1, -0.04, 0],
		["pew", 0, -0.1, 0.04, 0], ["pew", 0, 0.1, 0.04, 0], ["pew", 0, -0.1, 0.12, 0], ["pew", 0, 0.1, 0.12, 0], ["pew", 0, -0.1, 0.2, 0], ["pew", 0, 0.1, 0.2, 0],
		["_pillar", 0, -0.18, -0.38, 0, [7.0, 0.4]], ["_pillar", 0, 0.18, -0.38, 0, [7.0, 0.4]], ["_pillar", 0, -0.18, 0.3, 0, [7.0, 0.4]], ["_pillar", 0, 0.18, 0.3, 0, [7.0, 0.4]],
		["_fountain", 0, 0.35, -0.05, 0, [1.6]], ["_area", 0, 0.35, -0.05, 0, [5.0, 5.0, "blue"]], ["bench", 0, 0.47, -0.05, -90], ["bench", 0, 0.35, -0.27, 0], ["bench", 0, 0.35, 0.17, 180],
		["sarcophagus", 0, -0.35, -0.05, 0], ["altar", 0, -0.45, -0.05, 90], ["lion_banner", 0, -0.49, -0.2, 90, [2.0, false]], ["lion_banner", 0, -0.49, 0.1, 90, [2.0, false]],
		["lectern", 0, -0.3, 0.15, 180],
		["pew", 1, -0.35, -0.2, 90], ["pew", 1, 0.35, -0.2, -90], ["lion_banner", 1, -0.49, -0.1, 90, [1.0, false]], ["lion_banner", 1, 0.49, -0.1, -90, [1.0, false]],
		["bookshelf", 1, -0.49, 0.2, 90], ["bookshelf", 1, 0.49, 0.2, -90],
	],
	"lights": [["chandelier", 0, 0.0, -0.1, 0, 4.0, 22.0, true], ["chandelier", 0, 0.0, 0.2, 0, 2.5, 14.0], ["lantern", 0, 0.0, -0.4, 0, 2.0, 10.0],
		["chandelier", 0, 0.35, -0.05, 0, 2.2, 11.0], ["lantern", 0, -0.49, -0.05, 90, 1.5, 9.0], ["lantern", 0, -0.21, 0.4, -90, 1.0, 8.0], ["lantern", 0, 0.21, 0.4, 90, 1.0, 8.0],
		["lantern", 1, -0.49, -0.3, 90, 1.0, 9.0], ["lantern", 1, 0.49, -0.3, -90, 1.0, 9.0], ["lantern", 1, -0.49, 0.35, 90, 1.0, 9.0], ["lantern", 1, 0.49, 0.35, -90, 1.0, 9.0]],
	"rooms": [["Main Nave", 0, 0.0, 0.3], ["High Altar", 0, 0.0, -0.33], ["Healing Chambers", 0, 0.35, 0.1], ["Crypt-Adjacent Shrine", 0, -0.35, 0.1],
		["West Gallery", 1, -0.35, -0.3], ["East Gallery", 1, 0.35, -0.3]]},
}
