import json,sys
sys.path.insert(0,'/workspace/godot-art/loot3_tools'); from edata import *
G=json.load(open('/tmp/l3/www/proto3d/models/beth/loot/gear/gear.json'))['items']
ATT=json.load(open('/tmp/l3/www/proto3d/models/beth/loot/gear/gear_attach.json'))['heroes']
ALL=["helmet","chest","shoulders","gloves","legs","boots","belt","cloak"]
def weap(h,r):
    t=[1,1,2,3,3,3][RARITIES.index(r)]; fam=ATT[h]['weapon_family']
    w=[i['id'] for i in G if i['slot']=='weapon' and i['family']==fam and i['tier']==t and h in i.get('heroes',[h])] or [i['id'] for i in G if i['slot']=='weapon' and i['family']==fam and i['tier']==t]
    s=[i['id'] for i in G if i['slot']=='shield' and i['tier']==t]
    return (w[0] if w else ""),(s[0] if s and 'shield' in ATT[h]['slots'] else "")
SHEETH={"plate":"darius","scale":"garruk","chain":"vesper","leather":"nyx","cloth":"rowan","mystic":"selene"}
J=[]
for fam,h in SHEETH.items():
    for r in RARITIES:
        w,s=weap(h,r)
        J.append({"hero":h,"family":fam,"rarity":r,"slots":ALL,"weapon":w,"weapon2":w,"shield":s,"shots":[{"clip":"idle","yaw":35,"t":0.3,"out":f"/tmp/l3w/c/{fam}_{r}_a.png"},{"clip":"idle","yaw":200,"t":0.3,"out":f"/tmp/l3w/c/{fam}_{r}_b.png"}]})
json.dump(J,open('/tmp/l3w/jc.json','w'))
CL=["idle","walk","run","attack1","attack","skill","hit","death"]
K=[]
for k,(h,fam) in enumerate(HERO_FAMILY.items()):
    r=RARITIES[k%6]; w,s=weap(h,r)
    K.append({"hero":h,"family":fam,"rarity":r,"slots":ALL,"weapon":w,"weapon2":w,"shield":s,"shots":[{"clip":c,"yaw":35,"t":0.5 if c!="death" else 0.6,"out":f"/tmp/l3w/k/{h}_{c}.png"} for c in CL]})
json.dump(K,open('/tmp/l3w/jk.json','w'))
print(len(J),len(K))
