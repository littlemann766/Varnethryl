import json,sys,os,numpy as np
sys.path.insert(0,os.path.dirname(__file__)); from colgen import build
D='/workspace/godot-art/buildings'; idx=json.load(open(D+'/index.json')); doors=json.load(open('/tmp/doors.json'))
def dp(pos,n,w,h,**k):
    n=np.array(n,float); n/=np.linalg.norm(n); d=dict(pos=[round(float(v),3) for v in pos],normal=[round(float(v),3) for v in n],yaw_deg=round(float(np.degrees(np.arctan2(n[0],n[2]))),1),width=w,height=h); d.update(k); return d
MAN={'keep':[dp((0,0,14.25),(0,0,1),3.6,4.6,depth=4.0,label='curtain gate'),dp((0,0,6.0),(0,0,1),3.0,4.2,label='keep door')],
 'treasury':[dp((0,0,4.0),(0,0,1),3.6,5.0)],'windmill':[dp((0,0,3.25),(0,0,1),1.3,2.4)],
 'gatehouse':[dp((0,0,3.0),(0,0,1),3.8,5.4,depth=6.6,label='gate passage (through)')],
 'colosseum':[dp((0,0,21.0),(0,0,1),3.0,4.0,depth=2.0,label='main arch')],
 'farmhouse_tripo':[dp((-1.9,0.9,10.9),(0,0,1),1.4,2.3,source='house door between the two lanterns, from geometry',label='house door'),dp((5.2,0.0,10.2),(0,0,1),4.0,5.0,source='barn opening, from geometry',label='barn doors')],
 'barn_stable_tripo':[dp((-1.9,0.9,10.9),(0,0,1),1.4,2.3,source='house door between the two lanterns, from geometry',label='house door'),dp((5.2,0.0,10.2),(0,0,1),4.0,5.0,source='barn opening, from geometry',label='barn doors')],
 'lighthouse_full_tripo':[dp((0.97,7.59,1.2),(0.75,0,0.66),1.0,2.2,source='measured from ortho render')],
 'lighthouse_tower_tripo':[dp((0.97,7.59,1.2),(0.75,0,0.66),1.0,2.2,source='measured from ortho render')],
 'lighthouse_rock_island_tripo':[]}
NODOOR={'fountain','wall_segment','walls_demo','watchtower'}
rep={}
for e in idx['buildings']+idx['tripo_buildings']:
    k=e['id']; ds=MAN.get(k, doors.get(k,[]))
    for d in ds: d.setdefault('source','generator door() call' if k in doors and doors[k] else d.get('source','generator geometry (manual)'))
    src=D+'/'+e['high']['file']; out=src[:-4]+'_col.glb'
    nb=build(src,ds,out); e['col']=os.path.relpath(out,D); e['door_points']=[{kk:v for kk,v in d.items() if kk!='depth'} for d in ds]
    for d in e['door_points']: d['opening']=[max(d['width'],1.4),max(d['height'],2.3)]
    rep[k]=dict(boxes=nb,doors=len(ds),kb=os.path.getsize(out)//1024); print(k,rep[k],flush=True)
idx['col_note']=("<id>_col.glb: collision only, nodes named colNNNN-colonly (Godot imports StaticBody3D + shape, no mesh). Same origin as the visual GLB. "
 "Built from a 0.5 m column grid (heights snapped to 0.25 m), roofed interiors solid, each door has a walk-in opening >=1.4 m wide x >=2.3 m tall "
 "(see door_points[].opening) cut ~1.5 m deep, with low steps in front removed. door_points: pos (door threshold, metres, building space), normal/yaw_deg = outward facing (yaw 0 = +Z).")
json.dump(idx,open(D+'/index.json','w'),indent=1)
