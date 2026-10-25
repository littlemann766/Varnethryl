# Prepare the user's supplied ship models for Godot: orient (bow +Z), real scale, waterline y=0, LODs, collision, index.
# Look is untouched: same geometry, UVs and texture; only transform, kit-sheet extraction (Tidewrack) and decimation.
import numpy as np, trimesh, json, os, gzip, shutil
from deci import decimate
SRC='/workspace/beth-world/www/proto3d'; OUT='/workspace/godot-art/ships'; os.makedirs(OUT,exist_ok=True)
def load(f):
    if f.endswith('.gz'):
        open('/tmp/_s.glb','wb').write(gzip.open(f).read()); f='/tmp/_s.glb'
    return trimesh.load(f,force='mesh',process=False)
def frame(m,flip,length,draft_frac,yaw=None):
    v=m.vertices; xz=v[:,[0,2]]-v[:,[0,2]].mean(0)
    if yaw is None:
        w,e=np.linalg.eigh(np.cov(xz.T)); a=e[:,-1]; yaw=np.arctan2(a[0],a[1])
    c,s=np.cos(yaw),np.sin(yaw); R=np.array([[c,0,-s],[0,1,0],[s,0,c]])
    if flip: R=np.diag([-1,1,-1])@R
    return R,yaw
def apply(m,R,sc,off):
    m=m.copy(); m.vertices=(m.vertices@R.T)*sc+off; return m
def colglb(m,deck_y,path):
    v=m.vertices; h=v[v[:,1]<=deck_y]
    hull=trimesh.convex.convex_hull(h); sc=trimesh.Scene(); sc.add_geometry(hull,node_name='hull-colonly',geom_name='hull-colonly'); sc.export(path)
SHIPS=[ # name, src high, existing lods or None, flip, target LOA (m) or None=keep, waterline as fraction of hull depth from keel, hull-top fraction of height
 dict(name='boat_sail',src='models/beth/tripo/boat_sail_game.glb',lods=['models/beth/tripo/boat_sail_game_lod1.glb','models/beth/tripo/boat_sail_game_lod2.glb'],flip=False,loa=None,deck=0.42,wl=0.35,desc='Tripo small sailing boat (user model)'),
 dict(name='boat_02',src='models/beth/tripo/boat_02_game.glb',lods=['models/beth/tripo/boat_02_game_lod1.glb','models/beth/tripo/boat_02_game_lod2.glb'],flip=False,loa=None,deck=0.42,wl=0.35,desc='Tripo small boat (user model)'),
 dict(name='tidewrack_sailing_ship',src='models-new/tidewrack_sailing_ship.glb.gz',lods=None,flip=False,loa=30.0,deck=0.30,wl=0.40,desc='Tidewrack sailing ship, extracted from the kit sheet (user model)'),
]
def run(only=None):
    idx={'units':'metres','waterline_y':0.0,'bow':'+Z','ships':{}}
    for S in SHIPS:
        if only and S['name'] not in only: continue
        m=load(f"{SRC}/{S['src']}")
        if S['name'].startswith('tidewrack'):
            fc=m.triangles_center; sel=(fc[:,0]<-0.12)&(fc[:,2]>-0.15)&(fc[:,1]<0.35)&(fc[:,0]+0.5<(fc[:,2]+0.15)*1.2+0.15)
            m=m.submesh([np.where(sel)[0]],append=True)
            # drop the stray kit piece floating off to one side: faces far off the hull centreline
            R0,_=frame(m,False,0,0); c=m.triangles_center@R0.T; L0=np.ptp(c[:,2]); keep=np.abs(c[:,0]-np.median(c[:,0]))<0.16*L0
            m=m.submesh([np.where(keep)[0]],append=True)
        R,yaw=frame(m,S['flip'],0,0)
        v=m.vertices@R.T; L=np.ptp(v[:,2]); sc=(S['loa']/L) if S['loa'] else 1.0; v=v*sc
        H=np.ptp(v[:,1]); y0=v[:,1].min(); deck=y0+S['deck']*H; wl=y0+S['wl']*(deck-y0)
        off=np.array([-(v[:,0].max()+v[:,0].min())/2,-wl,-(v[:,2].max()+v[:,2].min())/2])
        hi=apply(m,R,sc,off); hi.export(f"{OUT}/ship_{S['name']}.glb")
        n=len(hi.faces); tris=[n]
        if S['lods']:
            for k,f in enumerate(S['lods'],1):
                l=apply(load(f"{SRC}/{f}"),R,sc,off); l.export(f"{OUT}/ship_{S['name']}_lod{k}.glb"); tris.append(len(l.faces))
        else:
            P=hi.vertices[hi.faces].reshape(-1,3); UV=hi.visual.uv[hi.faces].reshape(-1,2); F=np.arange(len(P)).reshape(-1,3)
            for k,fr in ((1,0.5),(2,0.2)):
                P2,F2,UV2=decimate(P,F,UV,int(n*fr*0.97))
                l=trimesh.Trimesh(P2,F2,process=False,visual=trimesh.visual.TextureVisuals(uv=UV2,material=hi.visual.material))
                l.export(f"{OUT}/ship_{S['name']}_lod{k}.glb"); tris.append(len(F2))
        colglb(hi,deck-wl,f"{OUT}/ship_{S['name']}_col.glb")
        b=hi.bounds
        idx['ships'][S['name']]=dict(desc=S['desc'],source=S['src'],high=f"ship_{S['name']}.glb",lod1=f"ship_{S['name']}_lod1.glb",lod2=f"ship_{S['name']}_lod2.glb",col=f"ship_{S['name']}_col.glb",
            tris=dict(high=tris[0],lod1=tris[1],lod2=tris[2]),dims=dict(length_overall=round(float(np.ptp(b[:,2])),2),beam=round(float(np.ptp(b[:,0])),2),draft=round(float(-b[0,1]),2),height_over_waterline=round(float(b[1,1]),2),deck_y=round(float(deck-wl),2)),
            waterline_y=0.0,bow='+Z',phone_high_lod='high' if tris[0]<=8000 else 'lod1')
        print(S['name'],tris,idx['ships'][S['name']]['dims'])
    json.dump(idx,open(f'{OUT}/index.json','w'),indent=1)
if __name__=='__main__': run()
