HEROES={ # id: (weapon family, hand(s), armor weight, shield)
 "aldric":("sword","R","heavy",True),"elira":("bow","L","medium",False),"rowan":("staff","R","light",False),
 "thorne":("staff","R","light",False),"nyx":("dagger","RL","medium",False),"seraphine":("mace","R","heavy",True),
 "garruk":("axe","R","heavy",False),"mirelle":("staff","R","light",False),"cedric":("lute","R","medium",False),
 "morwen":("scythe","R","medium",False),"kael":("staff","R","light",False),"vesper":("crossbow","R","medium",False),
 "talia":("staff","R","light",False),"orin":("spear","R","heavy",False),"selene":("staff","R","light",False),
 "darius":("greatsword","R","heavy",False),"finn":("rapier","R","medium",False),"brynn":("crossbow","R","medium",False),
 "asha":("knuckles","RL","medium",False),"rook":("whip","R","heavy",False),"owner":("sword","R","heavy",True),
 "wren":("dagger","R","medium",False),"pip":(None,"","companion",False),"phoenix":(None,"","companion",False)}
TN={1:"common",2:"rare",3:"epic"}
WNAMES={"sword":("Iron Arming Sword","Steel Knightly Sword","Saltglass Longsword"),
 "rapier":("Iron Sidesword","Steel Rapier","Duelist's Swept-Hilt Rapier"),
 "greatsword":("Iron Two-Hander","Steel Greatsword","Rimeforged Zweihander"),
 "dagger":("Iron Dagger","Steel Rondel Dagger","Saltglass Misericorde"),
 "axe":("Iron Bearded Axe","Steel Dane Axe","Emberwrought Axe"),
 "mace":("Iron Mace","Steel Flanged Mace","Hallowed Flanged Mace"),
 "spear":("Ash Spear","Steel Winged Spear","Saltglass Partisan"),
 "staff":("Oak Quarterstaff","Bound Rowan Staff","Starglass Staff"),
 "scythe":("Field Scythe","Steel War-Scythe","Rime Reaper"),
 "bow":("Elm Longbow","Yew Longbow","Glasswyrm Recurve"),
 "crossbow":("Wooden Crossbow","Steel-Prod Crossbow","Stormsilk Arbalest"),
 "lute":("Pine Lute","Rosewood Lute","Court Lute of Gullhaven"),
 "whip":("Hide Whip","Braided Bullwhip","Coil-Scale Lash"),
 "knuckles":("Iron Knuckles","Steel Cestus","Ember Cestus")}
WSTAT={"sword":(1.0,0),"rapier":(0.9,8),"greatsword":(1.35,0),"dagger":(0.7,12),"axe":(1.15,3),"mace":(1.1,0),"spear":(1.1,5),
 "staff":(0.95,0),"scythe":(1.2,4),"bow":(1.0,6),"crossbow":(1.1,4),"lute":(0.75,0),"whip":(0.85,5),"knuckles":(0.8,10)}
HNAMES={"light":("Wool Hood","Lined Coif","Warden's Silk Hood"),"medium":("Kettle Hat","Nasal Helm","Rimeguard Helm"),"heavy":("Iron Bascinet","Steel Barbute","Great Helm of the Vale")}
CNAMES={"light":("Quilted Robe","Bound Scholar's Robe","Starsilk Vestment"),"medium":("Leather Jerkin","Ring-Sewn Jack","Brigandine of the Watch"),"heavy":("Iron Cuirass","Steel Breastplate","Rimewarden Harness")}
SNAMES=("Round Buckler","Heater Shield","Gullhaven Kite Shield")
RNAMES=("Iron Band","Garnet Signet","Saltglass Seal Ring")
ANAMES=("Pewter Pilgrim Badge","Garnet Pendant","Glasswyrm Locket")
KNAMES=("Leather Collar","Brass-Studded Collar","Starsilk Collar")
# value in gold by tier (5-coin era: toll 5, bread 4, shortsword 25)
VAL={"weapon":(60,420,2400),"head":(40,280,1500),"chest":(90,650,3200),"shield":(50,320,1600),"ring":(80,450,2000),"trinket":(70,400,1800),"collar":(30,200,1100)}
ATK=(20,42,75); DEF={"heavy":(15,32,55),"medium":(11,23,40),"light":(7,15,26)}
def slug(s): return s.lower().replace("'s","s").replace("'","").replace("-","_").replace(" ","_")
PERKS={ # one unique named perk per T3 piece: id: {name, effect key, value, desc}
 "saltglass_longsword":{"name":"Brine-Edge","key":"lifesteal_pct","value":6,"desc":"Heal 6% of damage dealt."},
 "duelists_swept_hilt_rapier":{"name":"Riposte","key":"perfect_block_counter_pct","value":150,"desc":"After a perfect block, the next hit deals 150% and always crits."},
 "rimeforged_zweihander":{"name":"Glacier Cleave","key":"charged_frost_wave","value":1,"desc":"Fully charged swings send a frost wave that slows by 40% for 3 s."},
 "saltglass_misericorde":{"name":"Mercy Stroke","key":"execute_below_hp_pct","value":15,"desc":"Hits on non-boss enemies under 15% HP kill them outright; bosses take +30% instead."},
 "emberwrought_axe":{"name":"Ember Bite","key":"burn_on_hit_pct","value":25,"desc":"25% chance per hit to burn for 3 s (stacks 3x)."},
 "hallowed_flanged_mace":{"name":"Hallowed Ring","key":"stagger_heal_party_pct","value":3,"desc":"Staggering an enemy heals the party 3% max HP."},
 "saltglass_partisan":{"name":"Tidebreaker","key":"pierce_targets","value":3,"desc":"Thrusts pierce up to 3 enemies and ignore 20% defence."},
 "starglass_staff":{"name":"Starfall","key":"skill_cdr_pct","value":15,"desc":"Skill cooldowns -15%; every 5th skill cast is free."},
 "rime_reaper":{"name":"Winter Harvest","key":"kill_restores_sp_pct","value":20,"desc":"Kills restore 20% SP and chill nearby enemies."},
 "glasswyrm_recurve":{"name":"Wyrmglass Arrow","key":"crit_dmg_pct","value":40,"desc":"+40% crit damage; crits ricochet to a 2nd target."},
 "stormsilk_arbalest":{"name":"Stormbolt","key":"chain_lightning_targets","value":3,"desc":"Bolts chain lightning to 3 nearby enemies."},
 "court_lute_of_gullhaven":{"name":"Ballad of the Tide","key":"party_atk_pct","value":12,"desc":"Party +12% ATK while Cedric plays; nearby allies regen 1% HP/s."},
 "coil_scale_lash":{"name":"Coilbind","key":"snare_s","value":2.5,"desc":"Lash roots enemies for 2.5 s (bosses: 40% slow)."},
 "ember_cestus":{"name":"Furnace Fists","key":"combo_burn_ramp_pct","value":5,"desc":"Each hit in a combo adds +5% damage (max +50%) and the 10th hit explodes."},
 "wardens_silk_hood":{"name":"Warden's Sight","key":"crit_pct","value":12,"desc":"+12% crit and enemies' weak points glow."},
 "rimeguard_helm":{"name":"Rimeguard","key":"frost_immune","value":1,"desc":"Immune to frost slow and freeze; +30% frost resist."},
 "great_helm_of_the_vale":{"name":"Dread of the Vale","key":"fear_on_hit_taken_pct","value":10,"desc":"+25% poise; when hit, 10% chance to make the attacker cower for 1.5 s."},
 "starsilk_vestment":{"name":"Starsilk Ward","key":"spell_shield_pct_hp","value":20,"desc":"Every 20 s, a shield absorbs damage up to 20% max HP."},
 "brigandine_of_the_watch":{"name":"Watchman's Reflex","key":"dodge_heal_pct","value":4,"desc":"Perfect dodges heal 4% max HP and refund 15 SP."},
 "rimewarden_harness":{"name":"Thornplate","key":"thorns_pct","value":25,"desc":"Reflect 25% of melee damage taken; frost resist +30%."},
 "gullhaven_kite_shield":{"name":"Seawall","key":"block_reflect_pct","value":40,"desc":"Blocks reflect 40% of the blocked damage; can block boss slams."},
 "saltglass_seal_ring":{"name":"Seal of the Deep","key":"crit_heal_pct","value":2,"desc":"Crits heal 2% max HP."},
 "glasswyrm_locket":{"name":"Last Light","key":"revive_once_per_day","value":1,"desc":"Once per in-game day, survive a killing blow at 30% HP."},
 "starsilk_collar":{"name":"Bonded Spirit","key":"companion_shares_dmg_pct","value":20,"desc":"Companion takes 20% of the leader's damage and never despawns."},
}
def items():
    out=[]
    def add(i,**k): k["id"]=i; out.append(k)
    for fam,names in WNAMES.items():
        for t in (1,2,3):
            m,crit=WSTAT[fam]; st={"atk":round(ATK[t-1]*m)}
            if crit: st["crit_pct"]=crit+ (t-1)*2
            pass
            if fam=="staff": st["skill_pct"]=5*t
            if fam=="lute": st["aura_heal"]=t
            add(f"{slug(names[t-1])}",name=names[t-1],slot="weapon",family=fam,tier=t,stats=st)
    for w,names in HNAMES.items():
        for t in (1,2,3):
            st={"def":round(DEF[w][t-1]*0.45)}
            if w=="light": st["mp_pct"]=4*t
            if w=="heavy": st["poise"]=0.05*t
            if t==3: st[{"light":"fire_res_pct","medium":"frost_res_pct","heavy":"frost_res_pct"}[w]]=20
            add(slug(names[t-1]),name=names[t-1],slot="head",family=w,tier=t,stats=st)
    for w,names in CNAMES.items():
        for t in (1,2,3):
            st={"def":DEF[w][t-1]}
            if w=="heavy": st["speed_pct"]=-3
            if w=="medium": st["dodge_pct"]=2*t
            if w=="light": st["mp_regen_pct"]=10*t
            if t==3: st[{"light":"fire_res_pct","medium":"frost_res_pct","heavy":"frost_res_pct"}[w]]=30
            add(slug(names[t-1]),name=names[t-1],slot="chest",family=w,tier=t,stats=st)
    for t in (1,2,3): add(slug(SNAMES[t-1]),name=SNAMES[t-1],slot="shield",family="shield",tier=t,stats={"block_pct":(10,18,28)[t-1],"def":(4,8,14)[t-1]})
    for t in (1,2,3): add(slug(RNAMES[t-1]),name=RNAMES[t-1],slot="ring",family="ring",tier=t,stats={"crit_pct":(3,6,10)[t-1],**({"atk_pct":4} if t>=2 else {})})
    for t in (1,2,3): add(slug(ANAMES[t-1]),name=ANAMES[t-1],slot="trinket",family="amulet",tier=t,stats={"hp_regen":(1,3,6)[t-1],**({"max_hp_pct":5} if t>=2 else {})})
    for t in (1,2,3): add(slug(KNAMES[t-1]),name=KNAMES[t-1],slot="collar",family="collar",tier=t,stats={"companion_hp_pct":(10,25,45)[t-1],"companion_atk_pct":(5,12,22)[t-1]})
    for it in out:
        if it["tier"]==3 and it["id"] in PERKS: it["perk"]=PERKS[it["id"]]
        if it["tier"]==2 and it["slot"] in("weapon","head","chest","shield"): it["stats"]["poise" if it["slot"]!="weapon" else "atk_speed_pct"]=it["stats"].get("poise",0)+0.05 if it["slot"]!="weapon" else 5
        vs=VAL["weapon" if it["slot"]=="weapon" else it["slot"]][it["tier"]-1]
        if it["slot"] in("head","chest"): vs=int(vs*{"heavy":1.0,"medium":0.75,"light":0.6}[it["family"]])
        if it["slot"]=="weapon": vs=int(vs*{"lute":0.8,"knuckles":0.6,"dagger":0.6,"staff":0.7,"greatsword":1.4,"crossbow":1.2,"scythe":1.0}.get(it["family"],1.0))
        vs=int(round(vs/5)*5)
        it["rarity"]=TN[it["tier"]]; it["value"]=vs; it["sell"]=int(round(vs*0.3)); it["stack"]=1
        it["icon"]=f"res://loot/gear/icons/{it['id']}.png"; it["mesh"]=f"res://loot/gear/meshes/{it['id']}.glb"; it["mesh_lod1"]=f"res://loot/gear/meshes/{it['id']}_lod1.glb"
        it["heroes"]=[h for h,(f,hand,w,sh) in HEROES.items() if (it["slot"]=="weapon" and f==it["family"]) or (it["slot"] in("head","chest") and w==it["family"]) or (it["slot"]=="shield" and sh) or (it["slot"] in("ring","trinket") and w!="companion") or (it["slot"]=="collar" and w=="companion")]
    return out
if __name__=="__main__":
    I=items(); print(len(I)); import collections; print(collections.Counter(i["slot"] for i in I)); print(len(set(i["id"] for i in I)))
    for i in I[:5]: print(i)
