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
SKIP={'lighthouse','farmhouse','barn','stables'}   # replaced by the user's Tripo models (tripo/)
for k in SKIP:
    for suf in('','_lod1','_lod2'):
        p=f'{DST}/bld_{k}_card2{suf}.glb'
        if os.path.exists(p): os.remove(p)
old=json.load(open(DST+'/index.json')); OLD={e['id']:e for e in old.get('buildings',[])+old.get('tripo_buildings',[])}
B=[]
for k in sorted(set(CARDS)-SKIP):
    e=dict(id=k,card=CARDS[k])
    for lv,suf in(('high',''),('medium','_lod1'),('low','_lod2')):
        f=f'{SRC}/bld_{k}_card2{suf}.glb'; shutil.copy2(f,DST); e[lv]=info(f)
    for kk in('col','door_points'):
        if kk in OLD.get(k,{}): e[kk]=OLD[k][kk]
    e['phone_high_lod']='high' if e['high']['tris']<=20000 else 'lod1'
    B.append(e)
idx=json.load(open(DST+'/index.json')); idx['buildings']=B
idx['note']=("Beth card2 buildings. One shared material/atlas (atlas/card2_*.jpg, 2048) for ALL buildings; GLBs reference it by relative uri. "
 "Origin = footprint centre at ground, +Z = front, metres. LOD: no suffix=High, _lod1=Medium, _lod2=Low (Medium/Low are rebuilt with fewer "
 "segments/merlons/tower windows, not just culled). Atlas v4 adds cream ashlar, statue and rock strips: re-copy the atlas with these GLBs.")
TR=[]
for k,card,note in(('lighthouse_full','card_lighthouse_tidewrack.jpg','tower+rock island; x0.72 so door ~2.2 m'),('lighthouse_tower','card_lighthouse_tidewrack.jpg','stray railing posts removed; same origin as full/island'),
                   ('lighthouse_rock_island','card_lighthouse_tidewrack.jpg','x0.72'),('farmhouse','card_farmhouse_barn.jpg','cut face capped (+X side)'),('barn_stable','card_farmhouse_barn.jpg','barn/stables; cut face capped (-X side)')):
    e=dict(id=k+'_tripo',card=card,note=note,source='user Tripo upload, own 4096->2048 texture (not on card2 atlas)')
    for lv,suf in(('high',''),('medium','_lod1'),('low','_lod2')):
        import trimesh; f=f'{DST}/tripo/bld_{k}_tripo{suf}.glb'; m=trimesh.load(f,force='mesh')
        e[lv]=dict(file='tripo/'+os.path.basename(f),tris=len(m.faces),bbox_min=m.bounds[0].round(2).tolist(),bbox_max=m.bounds[1].round(2).tolist())
    for kk in('col','door_points','phone_high_lod'):
        if kk in OLD.get(e['id'],{}): e[kk]=OLD[e['id']][kk]
    TR.append(e)
idx['tripo_buildings']=TR
idx.update({k:v for k,v in old.items() if k not in('buildings','tripo_buildings','note','atlas')})
json.dump(idx,open(DST+'/index.json','w'),indent=1); print(len(B),'buildings')
