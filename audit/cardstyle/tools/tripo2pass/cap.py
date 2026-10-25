import trimesh,numpy as np,sys
def earclip(P):
    # P: (n,2) simple polygon; returns triangles (indices)
    idx=list(range(len(P))); 
    if np.sum(P[:,0]*np.roll(P[:,1],-1)-np.roll(P[:,0],-1)*P[:,1])<0: idx=idx[::-1]
    T=[]; guard=0
    while len(idx)>3 and guard<len(P)**2:
        guard+=1; n=len(idx); found=False
        for k in range(n):
            a,b,c=idx[k-1],idx[k],idx[(k+1)%n]; A,B,C=P[a],P[b],P[c]
            cr=(B[0]-A[0])*(C[1]-A[1])-(B[1]-A[1])*(C[0]-A[0])
            if cr<=1e-12: continue
            ok=True
            for j in idx:
                if j in(a,b,c): continue
                Q=P[j]
                d1=(B[0]-A[0])*(Q[1]-A[1])-(B[1]-A[1])*(Q[0]-A[0]); d2=(C[0]-B[0])*(Q[1]-B[1])-(C[1]-B[1])*(Q[0]-B[0]); d3=(A[0]-C[0])*(Q[1]-C[1])-(A[1]-C[1])*(Q[0]-C[0])
                if d1>=0 and d2>=0 and d3>=0: ok=False; break
            if ok: T.append((a,b,c)); idx.pop(k); found=True; break
        if not found: break
    if len(idx)==3: T.append(tuple(idx))
    return T
src,dst,xp,tol=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4])
s=trimesh.load(src); total=0
for name,g in s.geometry.items():
    node=[n for n in s.graph.nodes_geometry if s.graph[n][1]==name][0]; T=s.graph[node][0]
    Vw=trimesh.transform_points(g.vertices,T); F=g.faces
    _,first,inv=np.unique(Vw.round(4),axis=0,return_index=True,return_inverse=True); inv=inv.ravel(); G=inv[F]
    DE=np.concatenate([G[:,[0,1]],G[:,[1,2]],G[:,[2,0]]]); key=np.sort(DE,1); u,ii,c=np.unique(key,axis=0,return_index=True,return_counts=True)
    bd=DE[ii[c==1]]; Pm=Vw[first]
    on=(np.abs(Pm[bd[:,0],0]-xp)<tol)&(np.abs(Pm[bd[:,1],0]-xp)<tol); bd=bd[on]
    nxt={}
    for a,b in bd: nxt.setdefault(a,b)
    seen=set(); newF=[]
    for s0 in list(nxt):
        if s0 in seen: continue
        loop=[s0]; seen.add(s0); cur=nxt[s0]
        while cur in nxt and cur not in seen: loop.append(cur); seen.add(cur); cur=nxt[cur]
        if cur!=s0 or len(loop)<3: continue
        P2=Pm[loop][:,[2,1]]
        for a,b,cc in earclip(P2):
            newF.append([first[loop[a]],first[loop[b]],first[loop[cc]]])
    if newF:
        newF=np.array(newF)
        # orient caps to face +x/-x outward (the cut side)
        Vl=g.vertices; nrm=np.cross(Vw[newF[:,1]]-Vw[newF[:,0]],Vw[newF[:,2]]-Vw[newF[:,0]])
        out=np.sign(xp) if xp!=0 else 1
        flip=nrm[:,0]*out<0; newF[flip]=newF[flip][:,::-1]
        g.faces=np.vstack([F,newF]); total+=len(newF)
s.export(dst); print(src,'cap tris',total)
