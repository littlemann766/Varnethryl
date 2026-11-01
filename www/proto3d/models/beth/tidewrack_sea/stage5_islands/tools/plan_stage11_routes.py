import os  # Stage 11 path planner (Dijkstra on the 2 m heightfield, slope <= 0.36 = 19.8 deg). Uses POI positions from stage5_manifest.json.
import numpy as np, json, heapq
X,Z,H=np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data','stage11_H2.npz'))['H']; ST=2.0; ny,nx=H.shape; x0,z0=X[0,0],Z[0,0]
from scipy import ndimage
def ij(x,z): return int(round((z-z0)/ST)), int(round((x-x0)/ST))
mask=(H>0.3)&~((X>-2152)&(X<-2118)&(Z>26)&(Z<60))&~((X>-2135)&(X<-2105)&(Z>-120)&(Z<-84))   # skip plateau stair + old pier tower footprints
sl=np.hypot(*np.gradient(H,ST))
def dij(src,tmax):
    Dd=np.full(H.shape,np.inf); P=-np.ones(H.shape+(2,),int); pq=[(0,src)]; Dd[src]=0
    nb=[(a,b) for a in (-1,0,1) for b in (-1,0,1) if (a,b)!=(0,0)]
    while pq:
        d,(j,i)=heapq.heappop(pq)
        if d>Dd[j,i]: continue
        for a,b in nb:
            jj,ii=j+a,i+b
            if not(0<=jj<ny and 0<=ii<nx) or not mask[jj,ii]: continue
            L=ST*np.hypot(a,b); dh=abs(H[jj,ii]-H[j,i])
            if dh/L>tmax: continue
            nd=d+np.hypot(L,dh)*(1+1.5*max(0,sl[jj,ii]-0.25))   # prefer even ground (no side-slopes)
            if nd<Dd[jj,ii]: Dd[jj,ii]=nd; P[jj,ii]=(j,i); heapq.heappush(pq,(nd,(jj,ii)))
    return Dd,P
S=ij(-2320.0,76.0)
man=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','stage5_manifest.json')))
pois=man['islands']['saltglass']['pois']
out={}
for tmax in (0.36,0.47):
    Dd,P=dij(S,tmax)
    for p in pois:
        if p['name'] in out: continue
        # nearest reachable cell on the POI pad edge
        r=np.hypot(X-p['pos'][0],Z-p['pos'][2]); c=np.isfinite(Dd)&(r<p['radius']+3)
        if not c.any(): print(tmax,'unreached',p['name'],'nearest reach',round(float(r[np.isfinite(Dd)].min()),1)); continue
        j,i=np.argwhere(c)[np.argmin(Dd[c])]; rt=[]
        while (j,i)!=S and j>=0: rt.append((j,i)); j,i=P[j,i]
        rt=rt[::-1]; pts=[[float(X[a,b]),float(H[a,b])+0.08,float(Z[a,b])] for a,b in rt]
        L=sum(np.linalg.norm(np.subtract(pts[k+1],pts[k])) for k in range(len(pts)-1))
        mx=max(np.degrees(np.arctan(abs(pts[k+1][1]-pts[k][1])/max(1e-6,np.hypot(pts[k+1][0]-pts[k][0],pts[k+1][2]-pts[k][2])))) for k in range(len(pts)-1))
        out[p['name']]={'pts':pts,'len':L,'tmax':tmax,'maxdeg':mx}; print(tmax,p['name'],'len %.0f maxdeg %.1f'%(L,mx))
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data','stage11_routes.json'),'w'))
