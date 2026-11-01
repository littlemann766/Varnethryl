# Snap the Frostreach and Vent Harbour stalls onto walkable ground (stage4 collision + harbour meshes, read-only).
import sys,json,numpy as np; sys.path.insert(0,'.'); from gl import load
M="/workspace/vmain/tidewrack/stage4/meshes/"
def tris(f):
    j,acc=load(M+f+".glb"); out=[]
    for m in j['meshes']:
        for p in m['primitives']:
            P=acc(p['attributes']['POSITION']); I=acc(p['indices']).astype(int).reshape(-1,3) if 'indices' in p else np.arange(len(P)).reshape(-1,3)
            out.append(P[I])
    return np.vstack(out)
def ray(T,x,z):
    a,b,c=T[:,0],T[:,1],T[:,2]
    v0=c[:,[0,2]]-a[:,[0,2]]; v1=b[:,[0,2]]-a[:,[0,2]]; v2=np.array([x,z])-a[:,[0,2]]
    d00=(v0*v0).sum(1); d01=(v0*v1).sum(1); d11=(v1*v1).sum(1); d20=(v2*v0).sum(1); d21=(v2*v1).sum(1); den=d00*d11-d01*d01
    with np.errstate(all='ignore'):
        u=(d11*d20-d01*d21)/den; v=(d00*d21-d01*d20)/den
    k=(u>=0)&(v>=0)&(u+v<=1)&(np.abs(den)>1e-12)
    if not k.any(): return None,None
    y=a[k,1]+u[k]*(c[k,1]-a[k,1])+v[k]*(b[k,1]-a[k,1]); i=np.argmax(y)
    n=np.cross(b[k][i]-a[k][i],c[k][i]-a[k][i]); n=n/np.linalg.norm(n); return float(y[i]),abs(float(n[1]))
def snap(T,x0,z0,yaw,R=8.0):
    T=T[(np.abs(T[:,:,0].mean(1)-x0)<R+6)&(np.abs(T[:,:,2].mean(1)-z0)<R+6)]
    best=None; c,s=np.cos(yaw),np.sin(yaw)
    for dx in np.arange(-R,R+0.01,0.5):
        for dz in np.arange(-R,R+0.01,0.5):
            if dx*dx+dz*dz>R*R: continue
            x,z=x0+dx,z0+dz; ys=[]
            ok=True
            for lx,lz in [(0,0),(-1.3,-1),(1.3,-1),(-1.3,1.4),(1.3,1.4)]:   # stall footprint + merchant spot
                px=x+lx*c+lz*s; pz=z-lx*s+lz*c; y,ny=ray(T,px,pz)
                if y is None or ny<0.85 or y<0.4: ok=False; break
                ys.append(y)
            if not ok or max(ys)-min(ys)>0.3: continue
            d=dx*dx+dz*dz
            if best is None or d<best[0]: best=(d,x,float(np.median(ys)),z)
    return best
pl=json.load(open(sys.argv[1]))
for it in pl["items"]:
    if it["shop"] not in("frostreach_trader","vent_harbour_apothecary"): continue
    pre="frost" if "frost" in it["shop"] else "ash"
    T=np.vstack([tris(pre+"_terrain_col"),tris(pre+"_harbour")]); x0,_,z0=it["position"]
    b=snap(T,x0,z0,it["yaw"]) or snap(T,x0,z0,it["yaw"],16.0) or snap(T,x0,z0,it["yaw"],30.0)
    print(it["shop"],it["position"],"->",b)
    if b:
        it["position_v0"]=it["position"]; it["position"]=[round(b[1],2),round(b[2],2),round(b[3],2)]
        it["frame"]+=f"; SNAPPED (Equipment v1 step 3) by raycast vs stage4 {pre}_terrain_col+{pre}_harbour: flat (|n.y|>=0.85, height spread <=0.3 m over stall footprint), {round(b[0]**0.5,2)} m from the old point"
json.dump(pl,open(sys.argv[1],"w"),indent=1)
