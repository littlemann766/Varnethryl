import json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from edata import *
SPEC="/workspace/specs/Varnethryl_Equipment_Loot_Design_v1.0"; O="/tmp/l3/www/proto3d/models/beth/equipment/data"
S=json.load(open(SPEC+"/SAMPLE_CONTENT.json")); defs=json.load(open("/tmp/l3w/defs.json")); W=lambda n,o:json.dump(o,open(f"{O}/{n}","w"),indent=1)
W("rarity.json",{"order":RARITIES,"note":"Gray=Uncommon is the LOWEST rarity, Green=Common next (spec naming kept verbatim). Rarity looks add geometry per rank, not just colour (see ../appearances.json + MAPPING.md).",
 "rarities":{r:{"rank":i,"colorName":RNAME[r],"color":RCOL[r],"itemLevel":ILVL[r],"statMult":RMULT[r],"substats":[1,2,3,4,5,5][i],"sockets":[0,0,1,1,2,3][i],
   "dropBaselinePct":[55,25,14,5,0.9,0.1][i],"look":["worn_iron","straps_rivets","blackened_steel_brass","gilt_flared_spiked_glow","filigree_crest_horns_runes","forge_scarred_molten_seams"][i],
   "lootBeam":{"enabled":i>=2,"color":RCOL[r],"height_m":[0,0,2.5,4,6,8][i],"pulse":i>=4,"sound":[None,None,"drop_rare","drop_epic","drop_legendary","drop_masterwork"][i]}} for i,r in enumerate(RARITIES)},
 "legacy_tier_map":{"T1":"uncommon","T2":"rare","T3":"epic"}})
# sets
B={ "iron_bastion":[("damage_reduction_pct",4),("block_chance_pct",6),("bastion_wall_shield_on_block_pct_maxhp",10)],
 "ashen_titan":[("fire_damage_pct",8),("lava_resistance_pct",25),("molten_ground_burst_dmg_pct_atk",60)],
 "kingsguard":[("VIT_pct",5),("ally_damage_redirect_pct",8),("kings_rally_party_atk_pct_10s",12)],
 "tidewarden":[("RES_pct",6),("regen_in_water_pct_maxhp_s",1),("tidal_barrier_shield_pct_maxhp",15)],
 "frostwarden":[("frost_resistance_pct",8),("slow_on_frost_attack_chance_pct",15),("frostguard_shield_below_health_pct",25)],
 "dragonbane":[("damage_vs_dragons_pct",10),("dragon_resistance_pct",15),("dragon_hunter_mark_bonus_pct",20)],
 "bloodfang":[("LIFESTEAL_pct",1.5),("bleed_on_crit_chance_pct",12),("bloodfrenzy_haste_pct_below_50hp",15)],
 "stormcaller":[("storm_damage_pct",8),("chain_lightning_chance_pct",10),("stormcall_strike_every_s",12)],
 "dwarven_kingsguard":[("DEF_pct",6),("stagger_immunity_s_after_hit",2),("mountain_stance_dr_pct_while_still",20)],
 "wildheart":[("AGI_pct",5),("nature_damage_pct",8),("wild_surge_move_speed_pct_5s",20)],
 "shadowveil":[("evasion_pct",5),("stealth_or_shadow_bonus_pct",12),("shadowveil_vanish_on_dodge_cd_s",20)],
 "voidstalker":[("CRIT_pct",4),("damage_vs_marked_pct",12),("void_step_teleport_strike_cd_s",18)],
 "moonveil":[("MAG_pct",5),("REGEN_pct",8),("moonlit_heal_party_pct_maxhp_cd_s",[10,30])],
 "arcane_sovereign":[("arcane_damage_pct",8),("COOLDOWN_pct",5),("arcane_overflow_free_skill_chance_pct",10)],
 "celestial_watcher":[("holy_damage_pct",8),("healing_pct",8),("star_ward_revive_once_per_dungeon",1)],
 "plaguekeeper":[("unholy_damage_pct",8),("poison_duration_pct",20),("plague_burst_on_kill_dmg_pct_atk",40)],
 "soulreaper":[("soul_fragment_on_kill_heal_pct",2),("unholy_resist_pct",12),("reap_execute_below_hp_pct",8)],
 "astral_sovereign":[("MAG_pct",7),("all_resist_pct",6),("astral_convergence_skill_dmg_pct_10s",25)]}
sets=[]
for (fam,r),sid in SETS_BY.items():
    sets.append({"setId":sid,"name":SETNAME(sid),"armorFamily":fam,"rarity":r,"pieces":[f"{fam}_{s}_{r}" for s in SET_SLOTS],
     "bonuses":[{"pieces":p,"effect":e,"value":v,"tunable":True} for p,(e,v) in zip((2,4,6),B[sid])],"mix_rule":"pieces from different sets count toward each set separately"})
active={s["setId"] for s in sets}
W("sets.json",{"_note":"18 active sets (3 per family). Remaining spec concepts listed for later.","sets":sets,
 "concepts_not_yet_built":[c for c in ["sunforged","gravewalker","bloodlord","wraithwalker","dreadlord","verdant_crown","arena_champion","elder_dragon_hunter","seraphim"]]})
# enhancement (preserve live v0)
R=lambda x:x
W("enhancement.json",{"_note":"Spec 6 says do not silently alter existing ascension. v0_live = current items.js behaviour (tier derived from floor(level/3)). v1_spec = rarity is fixed on the item, ascension is a separate counter granted at milestones. active_track stays v0_live until the boss approves switching.",
 "active_track":"ascension_track_v0_live","enhancement_cap":15,"substat_enhancement_cap":10,"milestones":[3,6,9,12,15],
 "ascension_track_v0_live":{"source":"varn-core/www/core/items.js","tier_by_level":{"0":"uncommon","3":"rare","6":"epic","9":"mythic","12":"legendary","15":"masterwork"},"substats_by_level":{"0":0,"3":2,"6":3,"9":4,"12":5,"15":5},"ability_unlock_level":3,
   "cost":{"gold":"100+level*120","shards":"2+floor(level*1.5)"},"hp_bonus_cap_pct":28,"note":"'mythic' has no v1 rarity; maps to epic+ascension 3 in migration"},
 "ascension_track_v1_spec":{"ascension_by_milestone":{"3":1,"6":2,"9":3,"12":4,"15":5},"on_milestone":"+1 substat enhancement token, +5% base stats; new substat if below rarity count",
   "rarity_milestones":{"legendary":{"at":12,"reward":"unlock legendary special effect tier 2"},"masterwork":{"at":15,"reward":"unlock masterwork signature + forge-scar glow"}},
   "max_enhancement_by_rarity":{"uncommon":9,"common":9,"rare":12,"epic":12,"legendary":15,"masterwork":15}},
 "levels":[{"level":l,"gold":100+l*120,"shards":2+int(l*1.5),"material":(["mat_iron","mat_steel","mat_mithril","mat_adamantite","mat_starsteel"][min(4,l//3)]),"material_qty":1+l//3,
   "success_pct":100 if l<=6 else max(55,100-(l-6)*5),"on_fail":"keep level, lose materials" ,"base_stat_bonus_pct":round(l*4,1)} for l in range(1,16)],
 "no_destroy_on_fail":True,"substat_enhance":{"cost_gold":"60*(n+1)","material":"mat_arcane_dust","qty":"1+n//3","cap":10}})
# crafting
FAC={"blacksmith":"smithy","leatherworker":"stables","tailor":"market","jeweler":"treasury","enchanter":"mage_academy","alchemist":"apothecary","mystic_forge":"mage_academy"}
PROF_SLOTS={"blacksmith":(["plate","chain","scale"],["main_hand","off_hand"]),"leatherworker":(["leather"],["belt"]),"tailor":(["cloth","mystic"],["cloak"]),"jeweler":([],["amulet","ring"])}
MET=["mat_iron","mat_steel","mat_mithril","mat_adamantite","mat_starsteel","mat_dragonsteel"]
HID=["legacy_wolf_pelt","legacy_wolf_pelt","mat_troll_hide","mat_troll_hide","mat_dragon_scale","mat_dragon_scale"]
CLO=["mat_arcane_dust","mat_arcane_dust","mat_enchanted_crystal","mat_soul_fragment","mat_celestial_essence","mat_celestial_essence"]
ids={d["itemId"] for d in defs}; rec=[]
for d in defs:
    if "craft" not in d["sourceTags"] or d["category"] not in("armor","weapon","shield","jewelry"): continue
    i=RARITIES.index(d["rarity"]); fam=d["armorFamily"]
    prof="blacksmith" if fam in("plate","chain","scale") or d["category"] in("weapon","shield") else "leatherworker" if fam=="leather" or d["slot"]=="belt" else "jeweler" if d["category"]=="jewelry" else "tailor"
    if d["slot"]=="main_hand" and any(w in d["itemId"] for w in("two_handed_staff","instrument","longbow")): prof="tailor" if "staff" in d["itemId"] else "leatherworker"
    m=(MET if prof=="blacksmith" else HID if prof=="leatherworker" else CLO)[i]
    if m not in ids: m={"legacy_wolf_pelt":"legacy_leather"}.get(m,m)
    ins=[{"itemId":m,"qty":3+i*2},{"itemId":"mat_forge_shard","qty":1+i}]
    if i>=3: ins.append({"itemId":"mat_arcane_dust","qty":2*i})
    rec.append({"recipeId":"r_"+d["itemId"],"output":d["itemId"],"profession":prof,"facility":FAC[prof],"skill_req":i*25,"gold":int(40*3**i),"inputs":ins,"time_s":30*(i+1)})
for g in ["ruby","sapphire","emerald","amethyst","diamond","garnet","obsidian","topaz","moonstone","bloodstone","frost_crystal"]:
    rec.append({"recipeId":f"r_cut_{g}","output":f"gem_{g}_chipped","profession":"jeweler","facility":"treasury","skill_req":0,"gold":30,"inputs":[{"itemId":"mat_forge_shard","qty":1}],"time_s":20})
for k in ["flame","swiftness","protection","rebirth","destruction","echoes","hunt","guardian"]:
    rec.append({"recipeId":f"r_rune_{k}","output":f"rune_{k}","profession":"enchanter","facility":"mage_academy","skill_req":75,"gold":900,"inputs":[{"itemId":"mat_ancient_rune","qty":2},{"itemId":"mat_arcane_dust","qty":5}],"time_s":120})
bad=[x["itemId"] for r in rec for x in r["inputs"] if x["itemId"] not in ids]
W("crafting.json",{"professions":S["professions"]+["mystic_forge"],"facilities":FAC,"facility_note":"Uses existing buildings; Blacksmith (smithy) and Mage Academy first per spec 12. Interiors belong to Lucky.",
 "mystic_forge":{"stage_1":["enhance","ascend"],"stage_2":["reroll_substats","replace_one_substat","unlock_socket"],"stage_3":["apply_element","cosmetic_upgrade","boss_recipes","transfer_enhancement"],
   "reroll_substats":{"gold":"500*(rank+1)","mat":"mat_soul_fragment","qty":"2+rank"},"replace_one_substat":{"gold":"1200*(rank+1)","lock_others":True,"max_per_item":3},
   "unlock_socket":{"gold":[0,0,800,2000,5000,12000],"mat":"mat_enchanted_crystal"},"transfer_enhancement":{"max_levels":9,"loss_pct":30,"same_slot_only":True},
   "apply_element":{"allowed_slots":["main_hand","off_hand","chest"],"one_element_per_item":True}},
 "boss_recipes":[{"recipeId":"r_worldbreaker","output":"worldbreaker","inputs":[{"itemId":"mat_titan_core","qty":3},{"itemId":"mat_molten_ore","qty":10},{"itemId":"greatsword_epic","qty":1}],"facility":"mage_academy","enabled":True},
   {"recipeId":"r_voidfang","output":"voidfang","inputs":[{"itemId":"mat_dragon_core","qty":1},{"itemId":"mat_abyssal_scale","qty":5}],"facility":"mage_academy","enabled":False,"hidden":"sslythar"}],
 "recipes":rec,"_missing_inputs":sorted(set(bad))})
print("recipes",len(rec),"missing",set(bad))
# boss loot
BL=[("ashen_titan",["titan","titan40","titan_volcano"],"ashen_titan","plate",["worldbreaker","heart_of_the_titan"],["mat_titan_core","mat_molten_ore"]),
 ("frost_troll_brothers",["frosttroll_a","frosttroll_b"],"frostwarden","scale",["winters_end","frost_troll_totem"],["mat_frozen_heart","mat_troll_hide"]),
 ("balthrix",["vaelthryx"],"bloodfang","chain",["serpents_kiss","eye_of_balthrix"],["mat_basilisk_scale","mat_serpent_venom"]),
 ("cinder",[],"celestial_watcher","cloth",["eternal_cinder","phoenix_feather"],["mat_phoenix_feather","mat_eternal_flame"]),
 ("hydrella",["hydra"],"tidewarden","scale",["soulrender"],["mat_hydra_fang","mat_hydra_heart"]),
 ("sslythar",[],"dragonbane","scale",["voidfang","voidstone","ancient_dragon_scale"],["mat_dragon_core","mat_abyssal_scale"])]
th={t["bossId"]:t for t in S["bossLootThemes"]}; bl=[]
for b,gids,st,fam,ex,mats in BL:
    for x in ex+mats: assert x in ids,(b,x)
    bl.append({"bossId":b,"godot_ids":gids,"enabled":b not in("sslythar","cinder"),"disabled_reason":{"sslythar":"keep_hidden_until_movement_animation_ready","cinder":"boss not in Godot yet"}.get(b),
      "theme":th[b]["theme"],"specialReward":th[b]["specialReward"],"themed_set":st,"exclusives":[{"itemId":x,"chance_pct":4.0 if x in ex[:1] else 6.0} for x in ex],
      "materials":[{"itemId":m,"qty":[1,3],"chance_pct":100 if i==0 else 60} for i,m in enumerate(mats)],
      "rarity_table":"boss_tier","pity":{"exclusive_bonus_pct_per_failed_clear":1.0,"cap_pct":30,"guarantee_after_clears":25,"reset_on":"exclusive_awarded","per":"player_per_boss"},
      "first_clear_guarantee":{"itemId":f"{fam}_chest_epic"},"shared_pool_size":[3,5]})
W("boss_loot.json",{"_note":"Exclusive roll is separate from the rarity roll. Sslythar fully disabled; its items/materials tagged hidden and appear in no enabled table.","bosses":bl})
W("loot_rules.json",{"rarity_baseline":{r["rarity"]:r["chancePercent"] for r in S["rarityBaseline"]},"baseline_scope":"ordinary loot only",
 "tables":{"ordinary":{"uncommon":55,"common":25,"rare":14,"epic":5,"legendary":0.9,"masterwork":0.1},"elite":{"uncommon":35,"common":30,"rare":22,"epic":10,"legendary":2.6,"masterwork":0.4},
   "boss_tier":{"uncommon":0,"common":25,"rare":40,"epic":27,"legendary":7,"masterwork":1},"chest_common":{"uncommon":60,"common":28,"rare":11,"epic":1,"legendary":0,"masterwork":0},
   "chest_vault":{"uncommon":10,"common":25,"rare":35,"epic":22,"legendary":7,"masterwork":1}},
 "pity":{"rarity_pity":{"epic_or_better_after_rolls":60,"legendary_or_better_after_rolls":400,"reset_on":"rarity_awarded_at_or_above","per":"player","visible_to_player":True},"exclusive_pity":"see boss_loot.json per boss"},
 "need_greed_pass":{"timer_s":60,"order":["need","greed"],"need_eligibility":"can_equip_family_or_weapon_type (any hero may wear any armor family -> need allowed if efficiency>=0.85 and slot matches a party hero)","roll":"1..100","tie_break":"sha256(encounterId+itemId+playerId) ascending","leader_override":False,
   "unclaimed":"mail_to_random_greed_or_disenchant","unclaimed_expiry_h":72,"participation":{"min_active_presence_pct":60,"credit":["damage","healing","mitigated_damage","objectives"],"late_join_cutoff_pct_encounter":50}},
 "binding":{"unbound":"tradeable","bind_on_equip":"tradeable until equipped","bind_on_pickup":"never tradeable","account_bound":"between own characters only","character_bound":"never moves","admin_only":"owner/co-owner gear, never tradeable"},
 "trade":{"two_step_confirm":True,"reset_confirm_on_change":True,"atomic":True,"server_validates":["ownership","capacity","binding","currency"],"rate_limit_per_min":6,"log":True,"market_later":{"listing_fee_pct":2,"sale_fee_pct":5,"excluded":["bind_on_pickup","character_bound","admin_only"]}},
 "hidden_content":{"sslythar":{"bosses":["sslythar"],"items":[d["itemId"] for d in defs if "hidden" in d["sourceTags"]],"rule":"never in an enabled table until reveal"}}})
# migration
W("migration_v0_to_v1.json",{"from":"guildbound_rpg_save_v1 version 1","to":"state.equipment schemaVersion 1","backup_key":"guildbound_rpg_save_v1_backup_pre_equipment",
 "slot_map":{"head":"helmet","weapon":"main_hand","shield":"off_hand","offhand":"off_hand","ring":"ring1","trinket":"amulet","armor":"chest","charm":"class_item"},
 "rarity_map_v0_tier":{"T1":"uncommon","T2":"rare","T3":"epic"},"rarity_map_items_js_level_tier":{"uncommon":"uncommon","rare":"rare","epic":"epic","mythic":"epic","legendary":"legendary","masterwork":"masterwork"},
 "enhancement":"copy level (0..15) verbatim; ascension=floor(level/3)","substats":"copy affixes -> substats {stat:map, value, enhancement=boost (clamped 0..10)}",
 "stat_map":{"hp":"VIT","crit":"CRIT","critDmg":"CRIT","speed":"HASTE","dodge":"AGI","lifesteal":"LIFESTEAL","reduction":"RES","cooldown":"COOLDOWN"},
 "id_map_rule":"gear.json base `<family>_<slot>_t<N>` -> `<family>_<newslot>_<rarity>`; weapons `<wfam>_t<N>` -> `<weaponType>_<rarity>`","rollback":"restore backup key; v1 data ignored by v0 code","idempotent":True})
print("ok")
