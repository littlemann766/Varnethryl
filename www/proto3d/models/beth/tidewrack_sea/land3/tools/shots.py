import json,numpy as np,trimesh
from files import *
L=json.load(open(G+'landings.json')); MAN=json.load(open(G+'stage5_manifest.json'))
def terr(r):
    ms=[]
    for f in files(r):
        b=f.split('/')[-1][:-4]
        if is_terrain(b):
            s=trimesh.load(G+f,force='mesh'); ms.append(s)
    return trimesh.util.concatenate(ms)
shots=[]
for r in REG:
    T=terr(r); ray=trimesh.ray.ray_triangle.RayMeshIntersector(T)
    def h(x,z):
        loc,_,_=ray.intersects_location([[x,500,z]],[[0,-1,0]])
        return float(loc[:,1].max()) if len(loc) else 0.0
    for k,v in L.items():
        if v['region']!=r: continue
        inl=np.array(v['inland']); sh=np.array(v['shore']); p=np.array([sh[0],sh[2]])+inl*45
        I=MAN['islands'].get(k)
        rt=[po['route'] for po in (I['pois'] if I else []) if po.get('route') and len(po['route'])>12]
        if rt:
            R_=np.array(max(rt,key=len)); j=len(R_)//3; p=R_[j][[0,2]]; dd=R_[min(j+6,len(R_)-1)][[0,2]]-p; inl=dd/(np.linalg.norm(dd)+1e-9)
        hy=h(*p); c=p-inl*6
        shots.append(dict(region=r,name=f'{r}_{k}_hero',cam=[c[0],hy+2.8,c[1]],at=[p[0]+inl[0]*20,hy+1.0,p[1]+inl[1]*20],hero=[p[0],hy,p[1]]))
    # ship approach from the first landing of region
    k=[k for k,v in L.items() if v['region']==r][0]; v=L[k]; inl=np.array(v['inland']); mo=np.array([v['moor'][0],v['moor'][2]])
    c=mo-inl*34; shots.append(dict(region=r,name=f'{r}_ship_approach',cam=[c[0],14,c[1]],at=[mo[0]+inl[0]*90,8,mo[1]+inl[1]*90]))
    V=T.vertices; i=int(V[:,1].argmax()); pk=V[i]
    # mountain: look from the side facing the region centre
    cen=V.mean(0); d=np.array([cen[0]-pk[0],cen[2]-pk[2]]); d/=np.linalg.norm(d)+1e-9
    c=np.array([pk[0],pk[2]])+d*260
    shots.append(dict(region=r,name=f'{r}_mountain',cam=[c[0],max(h(*c),0)+pk[1]*0.55+12,c[1]],at=[pk[0],pk[1]*0.6,pk[2]]))
    # border: strongest vertex-colour change on land (y>3), gentle ground
    col=T.visual.vertex_colors[:,:3].astype(float); E=T.edges_unique; dc=np.abs(col[E[:,0]]-col[E[:,1]]).sum(1)
    ok=(V[E[:,0],1]>3)&(V[E[:,1],1]>3)&(V[E[:,0],1]<40)
    dc[~ok]=0
    # pick dense cluster: grid sum
    mid=(V[E[:,0]]+V[E[:,1]])/2; g=np.floor(mid[:,[0,2]]/40).astype(int); keys,inv=np.unique(g,axis=0,return_inverse=True); sc=np.bincount(inv.ravel(),dc)
    kb=keys[sc.argmax()]; bx,bz=(kb+0.5)*40; by=h(bx,bz)
    shots.append(dict(region=r,name=f'{r}_border',cam=[bx-28,by+16,bz-28],at=[bx,by,bz],hero=[bx,by,bz]))
    for S in shots:
        if S['region']==r: S['cam'][1]=max(S['cam'][1],h(S['cam'][0],S['cam'][2])+2.5) if 'hero' not in S['name'] else S['cam'][1]
    print(r,len(T.faces),pk.round(1),(bx,by,bz))


json.dump(shots,open('shots.json','w'),indent=0)
