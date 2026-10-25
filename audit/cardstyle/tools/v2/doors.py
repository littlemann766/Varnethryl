# record door() calls per card2 building (Q=0 geometry), propagate through Mesh.merge + front_gable rot
import json,sys,numpy as np, geo, house
_door=house.door
def door(c,face,a,w=1.5,h=2.7):
    p,t,n=house.facepos(c,face,a,0.0)
    c['m'].__dict__.setdefault('doors',[]).append(dict(p=np.array(p,float),n=np.array(n,float),w=w,h=h))
    return _door(c,face,a,w,h)
_merge=geo.Mesh.merge
def merge(s,o,off=(0,0,0),rot=0):
    r=np.radians(rot); R=np.array([[np.cos(r),0,np.sin(r)],[0,1,0],[-np.sin(r),0,np.cos(r)]])
    for d in getattr(o,'doors',[]): s.__dict__.setdefault('doors',[]).append(dict(p=R@d['p']+np.asarray(off,float),n=R@d['n'],w=d['w'],h=d['h']))
    return _merge(s,o,off,rot)
geo.Mesh.merge=merge; house.door=door
import kit2,kit3,bld4; bld4.door=door
import build
for mod in (build,kit3): mod.door=door
out={}
for name in sys.argv[1:]:
    kit2.Q=0; c=build.SPECS[name](); ds=getattr(c['m'],'doors',[])
    R=np.array([[0,0,-1],[0,1,0],[1,0,0]],float)
    L=[]
    for d in ds:
        p,n=d['p'],d['n']
        if c.get('front_gable'): p,n=R@p,R@n
        L.append(dict(pos=[round(float(v),3) for v in p],normal=[round(float(v),3) for v in n],yaw_deg=round(float(np.degrees(np.arctan2(n[0],n[2]))),1),width=d['w'],height=d['h']))
    out[name]=L
print(json.dumps(out))
