# Equipment v1 catalogue (definitions). Shared by data generator, 3D builder and icon builder.
RARITIES=["uncommon","common","rare","epic","legendary","masterwork"]
RCOL={"uncommon":"#9a9a9a","common":"#4caf50","rare":"#3d7fe0","epic":"#9b4de0","legendary":"#e0a526","masterwork":"#d8312b"}
RNAME={"uncommon":"gray","common":"green","rare":"blue","epic":"purple","legendary":"gold","masterwork":"red"}
ILVL={"uncommon":5,"common":10,"rare":20,"epic":35,"legendary":50,"masterwork":60}
RMULT={"uncommon":1.0,"common":1.12,"rare":1.3,"epic":1.55,"legendary":1.85,"masterwork":2.1}
FAMILIES=["plate","chain","leather","scale","cloth","mystic"]
ARMOR_SLOTS=["helmet","chest","shoulders","gloves","legs","boots","belt","cloak"]
SET_SLOTS=["helmet","chest","shoulders","gloves","legs","boots"]
SLOTS14=["helmet","chest","shoulders","gloves","legs","boots","belt","cloak","amulet","ring1","ring2","main_hand","off_hand","class_item"]
HERO_FAMILY={"aldric":"plate","seraphine":"plate","darius":"plate","owner":"plate","orin":"plate","garruk":"scale","rook":"scale",
 "finn":"chain","vesper":"chain","brynn":"chain","elira":"chain","morwen":"chain","nyx":"leather","asha":"leather","wren":"leather","cedric":"leather",
 "rowan":"cloth","thorne":"cloth","talia":"cloth","kael":"cloth","mirelle":"mystic","selene":"mystic"}
COMPANIONS=["pip","phoenix"]
HIDDEN=["sslythar"]
NOUN={"plate":["Great Helm","Cuirass","Pauldrons","Gauntlets","Cuisses","Sabatons","War Belt","Fur Mantle"],
 "chain":["Mail Coif-Helm","Hauberk","Mail Spaulders","Mail Mitts","Chausses","Mail Boots","Buckled Belt","Riding Cloak"],
 "leather":["Cowl","Jerkin","Shoulderguards","Bracers","Leggings","Boots","Baldric Belt","Hooded Cloak"],
 "scale":["Crested Scale Helm","Scale Coat","Scale Spaulders","Scale Gauntlets","Scale Tassets","Scale Greaves","Scale Girdle","Scaled Cape"],
 "cloth":["Hood","Robe","Stole","Wraps","Trousers","Soft Boots","Sash","Travelling Cloak"],
 "mystic":["Runic Circlet","Vestment","Spirit Mantle","Runed Gloves","Leg Wraps","Warded Boots","Rune Cord","Shroud"]}
PREF={"uncommon":"Worn","common":"Sturdy","rare":"Blackened"}
SETS_BY={("plate","epic"):"iron_bastion",("plate","legendary"):"ashen_titan",("plate","masterwork"):"kingsguard",
 ("scale","epic"):"tidewarden",("scale","legendary"):"frostwarden",("scale","masterwork"):"dragonbane",
 ("chain","epic"):"bloodfang",("chain","legendary"):"stormcaller",("chain","masterwork"):"dwarven_kingsguard",
 ("leather","epic"):"wildheart",("leather","legendary"):"shadowveil",("leather","masterwork"):"voidstalker",
 ("cloth","epic"):"moonveil",("cloth","legendary"):"arcane_sovereign",("cloth","masterwork"):"celestial_watcher",
 ("mystic","epic"):"plaguekeeper",("mystic","legendary"):"soulreaper",("mystic","masterwork"):"astral_sovereign"}
SETNAME=lambda s:s.replace("_"," ").title().replace("Dwarven Kingsguard","Dwarven Kingsguard")
# weapons: game family -> (spec weaponType, hands, heroes)
WEAPONS={"sword":("longsword",1,["aldric","owner"]),"rapier":("short_sword",1,["finn"]),"greatsword":("greatsword",2,["darius"]),
 "dagger":("dual_blades",1,["nyx","wren"]),"axe":("battle_axe",1,["garruk"]),"mace":("mace",1,["seraphine"]),"spear":("spear",2,["orin"]),
 "staff":("two_handed_staff",2,["rowan","thorne","mirelle","kael","talia","selene"]),"scythe":("scythe",2,["morwen"]),"bow":("longbow",2,["elira"]),
 "crossbow":("crossbow",2,["vesper","brynn"]),"lute":("instrument",2,["cedric"]),"whip":("whip",1,["rook"]),"knuckles":("fist_weapon",1,["asha"])}
WNOUN={"sword":"Longsword","rapier":"Rapier","greatsword":"Greatsword","dagger":"Daggers","axe":"Battle Axe","mace":"Flanged Mace","spear":"Winged Spear",
 "staff":"Staff","scythe":"War-Scythe","bow":"Longbow","crossbow":"Crossbow","lute":"Lute","whip":"Bullwhip","knuckles":"Cestus"}
WPRE={"uncommon":"Worn Iron","common":"Iron","rare":"Blackened Steel","epic":"Gilded","legendary":"Runeforged","masterwork":"Masterwork"}
NAMED=[ # itemId, name, game family, source boss, effect, rarity, hidden
 ("worldbreaker","Worldbreaker","greatsword","ashen_titan","heavy_attacks_create_ground_eruption","legendary",False),
 ("winters_end","Winter's End","sword","frost_region","critical_hits_may_slow_or_freeze","legendary",False),
 ("soulrender","Soulrender","scythe","unholy_dungeon","bounded_damage_to_health_conversion","legendary",False),
 ("dawnbringer","Dawnbringer","sword","ancient_temple","healing_burst","legendary",False),
 ("voidfang","Voidfang","greatsword","sslythar","short_range_void_shockwave","legendary",True),
 ("serpents_kiss","Serpent's Kiss","dagger","balthrix","stacking_venom","legendary",False),
 ("eternal_cinder","Eternal Cinder","staff","cinder","periodic_fire_spell_empowerment","legendary",False)]
OFFHAND={"shield":["Round Buckler","Heater Shield","Blackened Kite Shield","Gilded Kite Shield","Runeforged Tower Shield","Masterwork Tower Shield"],
         "focus":["Glass Orb","Bound Crystal","Blackened Orb","Gilded Focus","Runeforged Grimoire","Masterwork Star-Orb"]}
OFFHAND_HEROES={"shield":["aldric","seraphine","owner","finn","rook","garruk"],"focus":[]}
