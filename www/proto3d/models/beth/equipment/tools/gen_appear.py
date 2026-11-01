import json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from edata import *; import armor3d as A
E_="/tmp/l3/www/proto3d/models/beth/equipment"; R="res://equipment"
defs=json.load(open(E_+"/data/item_definitions.json"))["definitions"]
G=json.load(open("/tmp/l3/www/proto3d/models/beth/loot/gear/gear.json"))["items"]
stats={}
import glob
for f in glob.glob("/tmp/l3w/armor_stats_*.json"): stats.update(json.load(open(f)))
RANKLOOK=["worn_iron","straps_rivets","blackened_steel_brass","gilt_flared_spiked_glow","filigree_crest_horns_runes","forge_scarred_molten_seams"]
apps={}
for d in defs:
    a=d["appearanceId"]
    if a in apps: continue
    e={"icon":f"{R}/icons/{d['itemId'] if not a.startswith('app_gem_') else a[4:]}.png","rarity_border":f"{R}/ui/border_{d['rarity']}.png"}
    if d["category"]=="armor":
        fam,slot,r=d["armorFamily"],d["slot"],d["rarity"]
        parts=[]
        for part,_,_ in A.PARTS[slot]:
            n=f"{fam}_{r}_{part}"
            sides=[part.replace("_L","_L"),part.replace("_L","_R")] if part.endswith("_L") else [part]
            for sp in sides: parts.append({"attach_part":sp,"mesh":f"{R}/meshes/{fam}/{n}.glb","lod1":f"{R}/meshes/{fam}/{n}_lod1.glb","mirror_x":sp.endswith("_R"),"tris":stats.get(n,[0,0])})
        e.update(kind="wearable",parts=parts,look=RANKLOOK[RARITIES.index(r)],hide_rules={"helmet":"helmet_full" if fam=="plate" else "helmet_open","cloak":"cloak","boots":"boots"}.get(slot))
    elif d["category"]=="weapon" and d["slot"]=="main_hand":
        fam=next((k for k,v in WEAPONS.items() if v[0]==d["itemId"].rsplit("_",1)[0]),None) or next((x[2] for x in NAMED if x[0]==d["itemId"]),None)
        t=[1,1,2,3,3,3][RARITIES.index(d["rarity"])]
        g=[i for i in G if i["slot"]=="weapon" and i["family"]==fam and i["tier"]==t]
        e.update(kind="held",attach_part="main_hand",mesh=g[0]["mesh"] if g else None,lod1=g[0]["mesh_lod1"] if g else None,
                 note="uses the phase-2 weapon mesh for this family/tier (legendary/masterwork re-use T3 until dedicated meshes); hide rule baked_weapon applies")
        if d["itemId"] in [x[0] for x in NAMED]: e["note"]="named weapon: T3 family mesh placeholder, dedicated model on the list"
    elif d["slot"]=="off_hand":
        g=[i for i in G if i["slot"]=="shield" and i["tier"]==[1,1,2,3,3,3][RARITIES.index(d["rarity"])]]
        e.update(kind="held",attach_part="shield",mesh=g[0]["mesh"] if g and "shield" in d["itemId"] else None)
    elif d["slot"]=="companion_collar":
        r=d["rarity"]; e.update(kind="companion",attach_part="collar",mesh=f"{R}/meshes/companion/collar_{r}.glb",lod1=f"{R}/meshes/companion/collar_{r}_lod1.glb",fit="fit/companion_attach.json")
    elif d["slot"] in("ring","amulet"):
        t=[1,1,2,3,3,3][RARITIES.index(d["rarity"])]; s={"ring":"ring","amulet":"trinket"}[d["slot"]]
        g=[i for i in G if i["slot"]==s and i["tier"]==t]; e.update(kind="held",attach_part=s,mesh=g[0]["mesh"] if g else None)
    else: e.update(kind="icon_only")
    apps[a]=e
json.dump({"_note":"appearanceId -> art. Definitions stay schema-strict; all paths are res:// under the Godot mount of www/proto3d/models/beth (equipment/, loot/). Right-side parts reuse the _L mesh with mirror_x (scale.x already negative in fit/armor_attach.json).","appearances":apps},open(E_+"/appearances.json","w"),indent=1)
print(len(apps))
