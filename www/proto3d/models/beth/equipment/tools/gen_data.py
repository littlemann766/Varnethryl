import json,os,sys,math,copy
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from edata import *
SPEC="/workspace/specs/Varnethryl_Equipment_Loot_Design_v1.0"; O="/tmp/l3/www/proto3d/models/beth/equipment/data"; os.makedirs(O,exist_ok=True)
SAMPLE=json.load(open(SPEC+"/SAMPLE_CONTENT.json")); SCHEMA=json.load(open(SPEC+"/ITEM_DATA_SCHEMA.json"))
OLD="/tmp/l3/www/proto3d/models/beth/loot"; GEAR=json.load(open(OLD+"/gear/gear.json"))["items"]; ITEMS=json.load(open(OLD+"/items.json"))["items"]
defs=[]; apps={}
def D(itemId,name,category,rarity,appearanceId,slot=None,family=None,ilvl=None,setId=None,base=None,affixes=None,effect=None,bind=None,trade=None,tags=None):
    if bind is None: bind={"uncommon":"unbound","common":"unbound","rare":"unbound","epic":"bind_on_equip","legendary":"bind_on_equip","masterwork":"bind_on_pickup"}[rarity]
    if trade is None: trade=bind in("unbound","bind_on_equip")
    d={"schemaVersion":1,"itemId":itemId,"name":name,"category":category,"slot":slot,"armorFamily":family,"rarity":rarity,"itemLevel":ilvl or ILVL[rarity],
       "appearanceId":appearanceId,"setId":setId,"baseStats":base or {},"possibleAffixes":affixes or [],"specialEffectId":effect,"bindingRule":bind,"tradeable":trade,"sourceTags":tags or []}
    defs.append(d); return d
# ---------------- substats (bounded) ----------------
STATS=["STR","DEF","AGI","MAG","VIT","CRIT","HASTE","RES","LIFESTEAL","REGEN","STAMINA","COOLDOWN"]
SUB_BASE={"STR":(4,10,"flat",120),"DEF":(5,12,"flat",150),"AGI":(4,10,"flat",120),"MAG":(4,10,"flat",120),"VIT":(1.0,3.0,"pct",28),"CRIT":(0.7,2.0,"pct",25),
 "HASTE":(1.0,2.5,"pct",20),"RES":(1.0,3.0,"pct",40),"LIFESTEAL":(0.2,0.8,"pct",6),"REGEN":(0.3,1.0,"flat_per_s",15),"STAMINA":(2,6,"flat",60),"COOLDOWN":(0.5,1.5,"pct",20)}
substats={"_note":"Bounded random substats. Roll value uniformly in [min,max] for the item's rarity (scaled by itemLevel/50 for flat stats, min 0.3x). Each substat has its own enhancement 0..10; each +1 adds `step` of the rolled max. `cap` is the total cap across ALL equipped gear (diminishing above 70% of cap: x0.5). VIT cap 28 = existing +28% max-HP equipment cap.",
 "count_by_rarity":{"uncommon":1,"common":2,"rare":3,"epic":4,"legendary":5,"masterwork":5},"substat_enhancement_cap":10,
 "stats":{}}
for s,(mn,mx,kind,cap) in SUB_BASE.items():
    substats["stats"][s]={"kind":kind,"cap_total":cap,"step_pct_of_max":8,"ranges":{r:[round(mn*RMULT[r],2),round(mx*RMULT[r],2)] for r in RARITIES}}
substats["family_weights"]={"plate":{"DEF":3,"VIT":3,"STR":2,"RES":1,"STAMINA":2},"chain":{"DEF":2,"STR":2,"AGI":2,"VIT":2,"HASTE":1},"leather":{"AGI":3,"CRIT":3,"HASTE":2,"LIFESTEAL":1},
 "scale":{"DEF":2,"RES":3,"VIT":2,"STR":1},"cloth":{"MAG":3,"COOLDOWN":3,"REGEN":2,"RES":1},"mystic":{"MAG":3,"RES":2,"LIFESTEAL":1,"REGEN":2,"COOLDOWN":1},"*":{s:1 for s in STATS}}
# ---------------- affixes ----------------
AFF=[("titans","Titan's","STR"),("guardians","Guardian's","DEF"),("swift","Swift","AGI"),("arcane","Arcane","MAG"),("vital","Vital","VIT"),("vampiric","Vampiric","LIFESTEAL"),
 ("unbreakable","Unbreakable","damage_reduction_pct"),("precise","Precise","CRIT"),("eternal","Eternal","REGEN"),("cursed","Cursed","power_with_drawback"),("dragonforged","Dragonforged","fire_damage_pct"),
 ("frostbound","Frostbound","frost_res_pct"),("stormcharged","Stormcharged","storm_damage_pct"),("shadowwoven","Shadowwoven","evasion_pct"),("blessed","Blessed","healing_pct"),
 ("berserkers","Berserker's","low_hp_damage_pct"),("wardens","Warden's","ally_protection_pct"),("soulbound","Soulbound","mana_regen_pct"),("executioners","Executioner's","weakened_target_damage_pct")]
affixes={"_note":"Prefix affixes (one per item, rolled from possibleAffixes). Values bounded per rarity; 'cursed' adds +X% damage and -X/2% max HP.","elements":SAMPLE["elements"],
 "affixes":{a:{"label":l,"effect":e,"range_by_rarity":{r:[round(1.5*RMULT[r],1),round(4*RMULT[r],1)] for r in RARITIES},"stack_rule":"additive_capped"} for a,l,e in AFF},
 "element_rules":{"counters":{"fire":"frost","frost":"storm","storm":"fire","shadow":"holy","holy":"unholy","unholy":"nature","nature":"shadow","arcane":"arcane"},"counter_bonus_pct":15,"resist_cap_pct":60,"no_multiplicative_stacking":True}}
FAFF={"plate":["titans","guardians","unbreakable","vital","wardens","frostbound","dragonforged"],"chain":["titans","guardians","swift","vital","stormcharged","berserkers"],
 "leather":["swift","precise","shadowwoven","vampiric","berserkers","executioners"],"scale":["guardians","frostbound","dragonforged","stormcharged","vital","unbreakable"],
 "cloth":["arcane","soulbound","blessed","eternal","stormcharged"],"mystic":["arcane","eternal","soulbound","cursed","shadowwoven","vampiric"]}
# ---------------- armor ----------------
SLOTW={"helmet":.12,"chest":.25,"shoulders":.12,"gloves":.08,"legs":.18,"boots":.10,"belt":.06,"cloak":.09}
FAM={"plate":dict(DEF=1.3,STR=.3),"chain":dict(DEF=1.0,STR=.2,AGI=.2),"leather":dict(DEF=.7,AGI=.4,CRIT=.04),"scale":dict(DEF=1.15,RES=.06),"cloth":dict(DEF=.45,MAG=.45,COOLDOWN=.03),"mystic":dict(DEF=.55,MAG=.4,RES=.04)}
def armor_base(fam,slot,r):
    L=ILVL[r]; B=10*L*RMULT[r]*SLOTW[slot]; out={}
    for k,m in FAM[fam].items(): out[k]=round(B*m,1) if k in("DEF","STR","AGI","MAG") else round(m*100*SLOTW[slot]*RMULT[r],1)
    if slot=="cloak": out["RES"]=round(out.get("RES",0)+1.5*RMULT[r],1)
    if slot=="belt": out["STAMINA"]=round(4*RMULT[r],1)
    return out
for fam in FAMILIES:
    for si,slot in enumerate(ARMOR_SLOTS):
        for r in RARITIES:
            sid=SETS_BY.get((fam,r)) if slot in SET_SLOTS else None
            noun=NOUN[fam][si]
            if sid: name=f"{SETNAME(sid)} {noun}"
            elif r in PREF: name=f"{PREF[r]} {noun}"
            else: name={"epic":"Gilded","legendary":"Runeforged","masterwork":"Masterwork"}[r]+" "+noun
            iid=f"{fam}_{slot}_{r}"
            eff=f"set_{sid}" if sid else (f"{fam}_{slot}_{r}_special" if r in("legendary","masterwork") else None)
            tags=["drop","chest"]+(["craft"] if r in("uncommon","common","rare","epic") else [])+(["boss"] if r in("legendary","masterwork") else [])
            D(iid,name,"armor",r,f"app_{fam}_{slot}_{r}",slot=slot,family=fam,setId=sid,base=armor_base(fam,slot,r),affixes=FAFF[fam],effect=eff,tags=tags)
# ---------------- weapons ----------------
WBASE={"longsword":1.0,"short_sword":.9,"greatsword":1.45,"dual_blades":.75,"battle_axe":1.15,"mace":1.1,"spear":1.25,"two_handed_staff":1.1,"scythe":1.35,"longbow":1.2,"crossbow":1.3,"instrument":.85,"whip":.9,"fist_weapon":.8}
weapon_types={}
for fam,(wt,hands,heroes) in WEAPONS.items():
    weapon_types[wt]={"game_family":fam,"hands":hands,"dual_wield":wt in("dual_blades","fist_weapon"),"occupies":["main_hand","off_hand"] if hands==2 else (["main_hand","off_hand"] if wt in("dual_blades","fist_weapon") else ["main_hand"]),
       "animation_supported":True,"heroes":heroes,"stat":"MAG" if wt in("two_handed_staff","instrument") else "STR"}
    for r in RARITIES:
        st="MAG" if wt in("two_handed_staff","instrument") else "STR"; v=round(22*ILVL[r]/5**0.5*0+ (6+ILVL[r]*1.6)*RMULT[r]*WBASE[wt],1)
        D(f"{wt}_{r}",f"{WPRE[r]} {WNOUN[fam]}","weapon",r,f"app_w_{fam}_{r}",slot="main_hand",base={st:v,"CRIT":round(1+ (2 if wt in('dual_blades','short_sword','longbow') else 0)*RMULT[r],1)},
          affixes=["titans","precise","vampiric","berserkers","executioners","dragonforged","frostbound","stormcharged"] if st=="STR" else ["arcane","soulbound","blessed","eternal","stormcharged","dragonforged"],
          effect=(f"{wt}_{r}_special" if r in("legendary","masterwork") else None),tags=["drop","chest","shop"] if r in("uncommon","common") else ["drop","chest"]+(["craft"] if r!="masterwork" else []))
for iid,nm,fam,src,eff,r,hid in NAMED:
    wt=WEAPONS[fam][0]; st="MAG" if wt in("two_handed_staff","instrument") else "STR"
    D(iid,nm,"weapon","legendary",f"app_named_{iid}",slot="main_hand",ilvl=55,base={st:round((6+55*1.6)*RMULT['legendary']*WBASE[wt]*1.08,1),"CRIT":3.0},
      affixes=[],effect=eff,bind="bind_on_pickup",trade=False,tags=["named","boss",src]+(["hidden"] if hid else []))
# ---------------- off-hand ----------------
for kind,names in OFFHAND.items():
    for r,nm in zip(RARITIES,names):
        D(f"{kind}_{r}",nm,"shield" if kind=="shield" else "weapon",r,f"app_{kind}_{r}",slot="off_hand",
          base=({"DEF":round(ILVL[r]*1.4*RMULT[r],1),"block_pct":round(8+5*RARITIES.index(r),1)} if kind=="shield" else {"MAG":round(ILVL[r]*0.9*RMULT[r],1),"COOLDOWN":round(1+RARITIES.index(r)*0.6,1)}),
          affixes=FAFF["plate"] if kind=="shield" else FAFF["cloth"],effect=(f"{kind}_{r}_special" if r in("legendary","masterwork") else None),
          tags=(["drop","chest","shop"] if kind=="shield" else ["concept_disabled_until_1h_caster_weapon"]))
# ---------------- jewelry ----------------
JN={"amulet":["Pewter Badge","Garnet Pendant","Blackened Torc","Gilded Pendant","Runeforged Locket","Masterwork Heart-Locket"],
    "ring":["Iron Band","Copper Signet","Garnet Signet","Gilded Seal Ring","Runeforged Ring","Masterwork Signet"]}
for kind,names in JN.items():
    for r,nm in zip(RARITIES,names):
        D(f"{kind}_{r}",nm,"jewelry",r,f"app_{kind}_{r}",slot="amulet" if kind=="amulet" else "ring",base={"VIT" if kind=="amulet" else "CRIT":round((0.8 if kind=="ring" else 1.2)*RMULT[r]*(1+RARITIES.index(r)),1)},
          affixes=["vital","precise","eternal","soulbound","vampiric","arcane"],effect=(f"{kind}_{r}_special" if r in("legendary","masterwork") else None),tags=["drop","chest","craft"])
# ---------------- class items (one per playable hero; existing relicLevels +10 rule) ----------------
CLASSN={"aldric":"Lion Sigil","seraphine":"Dawn Reliquary","darius":"Oath Brand","owner":"Crown Seal","orin":"Spear-Captain's Token","garruk":"War-Totem","rook":"Hunter's Trophy",
 "finn":"Duelist's Favor","vesper":"Bolt Quiver","brynn":"Repeater Gearbox","elira":"Fletcher's Quiver","morwen":"Reaper's Lantern","nyx":"Shadow Charm","asha":"Prayer Beads",
 "wren":"Wren's Feather","cedric":"Songbook","rowan":"Ember Grimoire","thorne":"Light-Staff Crystal","talia":"Spark Coil","kael":"Rune Tablet","mirelle":"Thorn Seed","selene":"Frost Mirror"}
for h,nm in CLASSN.items():
    D(f"class_{h}",nm,"artifact","epic",f"app_class_{h}",slot="class_item",ilvl=1,base={},effect=f"class_{h}",bind="character_bound" if h!="owner" else "admin_only",trade=False,tags=["class_item",h,"relic_plus10"])
# ---------------- artifacts (2 active artifact slots, outside the 14) ----------------
ART=[("ancient_dragon_scale","Ancient Dragon Scale","legendary",["sslythar","hidden"]),("heart_of_the_titan","Heart of the Titan","legendary",["ashen_titan"]),("phoenix_feather","Phoenix Feather","epic",["cinder"]),
 ("eye_of_balthrix","Eye of Balthrix","legendary",["balthrix"]),("frost_troll_totem","Frost Troll Totem","epic",["frost_troll_brothers"]),("celestial_fragment","Celestial Fragment","epic",["exploration"]),
 ("voidstone","Voidstone","legendary",["sslythar","hidden"]),("kings_sigil","King's Sigil","masterwork",["quest"])]
for i,nm,r,t in ART: D(i,nm,"artifact",r,f"app_artifact_{i}",slot="artifact",effect=f"artifact_{i}",bind="bind_on_pickup",trade=False,tags=t)
# ---------------- gems & runes ----------------
GEMS=["ruby","sapphire","emerald","amethyst","diamond","garnet","obsidian","topaz","moonstone","bloodstone","frost_crystal","void_crystal"]
GSTAT={"ruby":"STR","sapphire":"MAG","emerald":"REGEN","amethyst":"COOLDOWN","diamond":"DEF","garnet":"VIT","obsidian":"RES","topaz":"HASTE","moonstone":"AGI","bloodstone":"LIFESTEAL","frost_crystal":"frost_res_pct","void_crystal":"CRIT"}
QUAL=["chipped","flawed","normal","fine","superior","perfect","pristine"]; QR=["uncommon","uncommon","common","rare","epic","legendary","masterwork"]
for g in GEMS:
    for qi,q in enumerate(QUAL):
        D(f"gem_{g}_{q}",f"{q.title()} {g.replace('_',' ').title()}","gem",QR[qi],f"app_gem_{g}",base={GSTAT[g]:round((qi+1)*1.5,1)},tags=["drop","craft"]+(["hidden"] if g=="void_crystal" and False else []))
RUNES={"flame":"Burn chance on hit","swiftness":"+move speed after dodge","protection":"Shield on low HP (60 s cd)","rebirth":"Revive once per dungeon","destruction":"Ultimate +damage",
 "echoes":"Skill repeats at 30% power (rare)","hunt":"Bonus damage to marked target","guardian":"Redirect 10% of ally damage to you"}
for k,dsc in RUNES.items(): D(f"rune_{k}",f"Rune of {k.title()}","rune","rare",f"app_rune_{k}",effect=f"rune_{k}",tags=["drop","craft","enchanter"])
gems_runes={"gem_qualities":QUAL,"combine":{"rule":"3 of the same gem+quality -> 1 of the next quality","gold_cost_by_target_quality":{q:int(50*2.2**i) for i,q in enumerate(QUAL)},"success_pct_by_target_quality":{"flawed":100,"normal":100,"fine":95,"superior":85,"perfect":70,"pristine":50},"on_fail":"keep 2 of 3, lose 1"},
 "sockets":{"by_rarity":{"uncommon":0,"common":0,"rare":1,"epic":1,"legendary":2,"masterwork":3},"unlock_at_forge":True,"unlock_cost":"see crafting.mystic_forge.unlock_socket"},
 "gem_stats":GSTAT,"runes":{k:{"desc":v,"slots":["main_hand","off_hand","chest"],"one_per_item":True,"cooldown_s":30} for k,v in RUNES.items()}}
# ---------------- materials ----------------
MATS=SAMPLE["materials"]; mat_rows=[]
MR={"iron":"uncommon","steel":"common","silver":"common","gold":"rare","mithril":"rare","adamantite":"epic","darksteel":"epic","starsteel":"legendary","dragonsteel":"legendary","voidsteel":"masterwork"}
for fam,lst in MATS.items():
    for m in lst:
        r=MR.get(m,"rare" if fam=="magical" else "epic" if m in("dragon_scale","titan_core","demon_heart","phoenix_feather") else "rare")
        hid=m in("voidsteel",) and False
        D(f"mat_{m}",m.replace("_"," ").title(),"material",r,f"app_mat_{m}",bind="unbound",trade=True,tags=["material",fam]+(["hidden"] if m=="dragon_core" else []))
for m,r in [("molten_ore","epic"),("frozen_heart","epic"),("eternal_flame","legendary"),("hydra_heart","legendary"),("dragon_core","legendary"),("abyssal_scale","legendary"),("forge_shard","common")]:
    D(f"mat_{m}",m.replace("_"," ").title(),"material",r,f"app_mat_{m}",bind="unbound",trade=True,tags=["material","boss"]+(["sslythar","hidden"] if m in("dragon_core","abyssal_scale") else []))
# existing phase-1 materials and consumables (kept ids, prefixed)
OLDR={"common":"uncommon","uncommon":"common","rare":"rare","epic":"epic","legendary":"legendary","key":"rare"}
for it in ITEMS:
    if it["slot"] in("material","consumable","key"):
        cat={"material":"material","consumable":"consumable","key":"consumable"}[it["slot"]]
        D(f"legacy_{it['id']}",it["name"],cat,OLDR[it["rarity"]],f"app_legacy_{it['id']}",bind="bind_on_pickup" if it["slot"]=="key" else "unbound",trade=it["slot"]!="key",tags=["legacy_items_json",it["slot"]])
# companion accessories
CN=["Leather Collar","Studded Collar","Blackened Collar","Gilded Collar","Runeforged Collar","Masterwork Collar"]
for r,nm in zip(RARITIES,CN): D(f"collar_{r}",nm,"companion_accessory",r,f"app_collar_{r}",slot="companion_collar",base={"companion_hp_pct":round(8*RMULT[r]*(1+RARITIES.index(r)*.5),1)},tags=["drop","chest","shop"])
D("luna_moon_charm","Luna's Moon Charm","companion_accessory","legendary","app_collar_legendary",slot="companion_collar",bind="bind_on_pickup",trade=False,tags=["quest","special_companion_luna"])
D("peaches_ribbon","Peaches' Ribbon","companion_accessory","legendary","app_collar_legendary",slot="companion_collar",bind="bind_on_pickup",trade=False,tags=["quest","special_companion_peaches"])
# ---------------- validate ----------------
import jsonschema
dsch=dict(SCHEMA["$defs"]["itemDefinition"]); dsch["$defs"]=SCHEMA["$defs"]; isch=dict(SCHEMA["$defs"]["itemInstance"]); isch["$defs"]=SCHEMA["$defs"]
for d in defs: jsonschema.validate(d,dsch)
ids=[d["itemId"] for d in defs]; assert len(ids)==len(set(ids)),"dup ids"
json.dump({"schemaVersion":1,"_note":"Item DEFINITIONS (ITEM_DATA_SCHEMA itemDefinition, validated). Instances live in the save (see instances_example.json). Art lookups by appearanceId in ../appearances.json.","definitions":defs},open(O+"/item_definitions.json","w"),indent=1)
json.dump(substats,open(O+"/substats.json","w"),indent=1); json.dump(affixes,open(O+"/affixes.json","w"),indent=1); json.dump(gems_runes,open(O+"/gems_runes.json","w"),indent=1)
json.dump({"weapon_types":weapon_types,"not_yet_supported_spec_types":["dual_axes","warhammer","morningstar","lance","halberd","polearm","flail","claws","executioner","two_handed_hammer","shortbow","heavy_crossbow","repeating_crossbow","throwing_knives","throwing_axes","javelins","magical_bow","wand","one_handed_staff","grimoire","spellbook","orb","crystal","totem","holy_relic","necromantic_catalyst"],"rule":"Do not add these to loot until attack animations exist (spec 10)."},open(O+"/weapon_types.json","w"),indent=1)
# example instances (validated)
import random; random.seed(3)
def inst(iid,owner,enh,n,asc=0):
    d=next(x for x in defs if x["itemId"]==iid); fam=d["armorFamily"] or "*"; pool=list(substats["family_weights"][fam].keys())
    subs=[{"stat":s,"value":round(random.uniform(*substats["stats"][s]["ranges"][d["rarity"]]),2),"enhancement":min(10,random.randint(0,enh))} for s in random.sample(pool,min(n,len(pool)))]
    return {"instanceId":f"inst-{iid}-{owner}-{enh}","itemId":iid,"ownerId":owner,"enhancement":enh,"ascension":asc,"substats":subs,"sockets":[None]*gems_runes["sockets"]["by_rarity"][d["rarity"]],"boundTo":owner if d["bindingRule"]=="bind_on_pickup" else None,"cosmeticAppearanceId":None,"createdAt":"2026-11-01T18:00:00Z"}
ex=[inst("plate_helmet_epic","player-1",9,4,3),inst("leather_gloves_legendary","player-1",12,5,4),inst("worldbreaker","player-2",15,5,5),inst("chain_chest_uncommon","player-1",0,1,0)]
for e in ex: jsonschema.validate(e,isch)
json.dump({"schemaVersion":1,"instances":ex},open(O+"/instances_example.json","w"),indent=1)
import collections
print(len(defs),collections.Counter(d["category"] for d in defs))
json.dump(defs,open("/tmp/l3w/defs.json","w"))
