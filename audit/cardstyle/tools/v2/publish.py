# copy card2 GLBs + shared atlas to /workspace/godot-art/buildings and rebuild index.json
import json,os,shutil,struct,glob
SRC='/workspace/beth-world/www/proto3d/models/beth/hi/buildings_card2'; DST='/workspace/godot-art/buildings'
CARDS=dict(apothecary='card_apothecary.jpg',bakery='card_bakery.jpg',fountain='card_fountain_monument.jpg',gatehouse='card_gatehouse.jpg',guildhall='card_guild_hall.png',
 house1='card_village_houses.jpg',house2='card_village_houses.jpg',house3='card_village_houses.jpg',house4='card_village_houses.jpg',inn='card_inn.jpg',keep='card_castle_keep.jpg',
 market='card_market_provisioner.png',port='card_port.jpg',smithy='card_blacksmith.jpg',temple='card_temple.jpg',townhall='card_town_hall.jpg',
 wall_segment='card_town_walls_watchtowers.jpg',walls_demo='card_town_walls_watchtowers.jpg',watchtower='card_town_walls_watchtowers.jpg',
 library='card_grand_library.png',mage_academy='card_mage_academy.jpg',observatory='card_observatory.jpg',treasury='card_treasury.jpg',crypt='card_crypt.jpg',
 lighthouse='card_lighthouse_tidewrack.jpg',windmill='card_windmill.jpg',stables='card_stables.jpg',farmhouse='card_farmhouse_barn.jpg',barn='card_farmhouse_barn.jpg',
 training_hall='card_training_hall.jpg',thieves_den='card_thieves_den.jpg',colosseum='card_colosseum.jpg')
def info(f):
    b=open(f,'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n])
    a=j['accessors'][0]; t=j['accessors'][3]['count']//3
    return dict(file=os.path.basename(f),tris=t,bbox_min=[round(v,2) for v in a['min']],bbox_max=[round(v,2) for v in a['max']])
os.makedirs(DST+'/atlas',exist_ok=True)
for f in glob.glob(SRC+'/atlas/card2_*.jpg'): shutil.copy2(f,DST+'/atlas/')
B=[]
for k in sorted(CARDS):
    e=dict(id=k,card=CARDS[k])
    for lv,suf in(('high',''),('medium','_lod1'),('low','_lod2')):
        f=f'{SRC}/bld_{k}_card2{suf}.glb'; shutil.copy2(f,DST); e[lv]=info(f)
    B.append(e)
idx=json.load(open(DST+'/index.json')); idx['buildings']=B
idx['note']=("Beth card2 buildings. One shared material/atlas (atlas/card2_*.jpg, 2048) for ALL buildings; GLBs reference it by relative uri. "
 "Origin = footprint centre at ground, +Z = front, metres. LOD: no suffix=High, _lod1=Medium, _lod2=Low (Medium/Low are rebuilt with fewer "
 "segments/merlons/tower windows, not just culled). Atlas v4 adds cream ashlar, statue and rock strips: re-copy the atlas with these GLBs.")
json.dump(idx,open(DST+'/index.json','w'),indent=1); print(len(B),'buildings')
