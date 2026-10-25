extends RefCounted
class_name VHeroData
## Generated from www/data.js HEROES (same order = same ids as the JS save).
## [name, className, role, str, def, agi, mag, weapon, alternates, relic, skill, style]
const RAW := [
	["Sir Aldric","Knight","Tank",9,10,4,2,"Longsword","Broadsword, Mace, Warhammer","Lionheart Crest","Shieldbreaker","melee"],
	["Lady Elira","Ranger","Ranged DPS",4,5,10,3,"Longbow","Shortbow, Recurve Bow, Crossbow","Eagle-Eye Quiver","Piercing Volley","ranged"],
	["Brother Thorne","Cleric","Healer",3,6,4,9,"Holy Staff","Mace, Scepter, Wand","Sacred Reliquary","Divine Renewal","heal"],
	["Nyx Varrin","Rogue","Assassin",5,4,10,4,"Dual Daggers","Shortsword, Throwing Knives","Shadowfang Emblem","Shadow Flurry","melee"],
	["Rowan Firebrand","Mage","Spellcaster",2,3,5,10,"Fire Staff","Wand, Spellbook, Scepter","Emberheart Crystal","Meteor Burst","mage"],
	["Dame Seraphine","Paladin","Vanguard Support",8,9,4,6,"Holy Mace","Warhammer, Sword, Flail","Divine Sunstone","Radiant Aegis","tank"],
	["Garruk Stonefist","Berserker","Melee DPS",10,6,5,1,"Greataxe","Greatsword, Dual Axes, Maul","Bloodrage Totem","Bloodstorm","melee"],
	["Mirelle Thornroot","Druid","Summoner",3,5,6,10,"Nature Staff","Totem, Wand, Sickle","Heartwood Seed","Wildgrowth","heal"],
	["Cedric Vale","Bard","Buffer",4,4,7,8,"Enchanted Lute","Harp, Flute, Rapier","Harmonic Pendant","Battle Hymn","support"],
	["Morwen Blackveil","Necromancer","Debuffer",2,4,5,10,"Skull Staff","Scepter, Ritual Dagger, Tome","Soulbound Phylactery","Soul Reap","mage"],
	["Kael Runebinder","Runemaster","Arcane Utility",3,5,4,10,"Rune Staff","Runic Wand, Spellbook","Ancient Rune Core","Runic Cascade","mage"],
	["Vesper Crowe","Witch Hunter","Anti-Mage",5,5,8,2,"Crossbow","Daggers, Hand Crossbow, Sword","Witchbane Sigil","Witchbane Volley","ranged"],
	["Talia Stormcall","Shaman","Elemental Support",3,4,6,9,"Storm Staff","Totem, Ritual Mace","Spiritbound Charm","Thunder Totem","support"],
	["Orin Ashlance","Spearman","Reach Fighter",7,7,6,1,"Spear","Pike, Halberd, Javelin","Warlord’s Pennant","Impaling Charge","melee"],
	["Selene Frostveil","Cryomancer","Control Mage",2,4,5,10,"Ice Staff","Frost Wand, Scepter, Spellbook","Eternal Frost Crystal","Frozen Tempest","mage"],
	["Darius Umbral","Dark Knight","Bruiser Tank",9,8,4,4,"Dark Greatsword","Great Axe, Cursed Blade","Umbral Seal","Abyssal Cleave","tank"],
	["Finn Valecourt","Duelist","Precision DPS",5,4,9,2,"Rapier","Sabre, Estoc, Shortsword","Champion’s Insignia","Perfect Riposte","melee"],
	["Brynn Cogwright","Engineer","Trap Utility",4,6,6,5,"Mechanical Crossbow","Repeater, Hand Crossbow, Traps","Arcane Gear Core","Clockwork Blast","ranged"],
	["Asha Ironfist","Monk","Martial Striker",7,5,9,3,"Hand Wraps","Knuckles, Bo Staff, Claws","Iron Spirit Beads","Hundred Fists","melee"],
	["Rook Wildbane","Beastmaster","Companion Tactician",6,6,7,3,"Hunting Spear","Bow, Hunting Knife, Short Spear","Alpha Fang Charm","Wolfpack Rush","ranged"],
]

static func count() -> int: return RAW.size()
static func get_hero(id: int) -> Dictionary:
	var a: Array = RAW[id]
	return {"id": id, "name": a[0], "className": a[1], "role": a[2], "str": a[3], "def": a[4], "agi": a[5], "mag": a[6], "weapon": a[7], "alternates": a[8].split(", "), "relic": a[9], "skill": a[10], "style": a[11], "portrait": "res://ui/assets/heroes/%d.webp" % id}
static func all() -> Array:
	var o := []
	for i in RAW.size(): o.append(get_hero(i))
	return o
