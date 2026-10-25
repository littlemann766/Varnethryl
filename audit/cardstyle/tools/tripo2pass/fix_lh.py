import trimesh,numpy as np,scipy.sparse as sp,sys
from scipy.sparse.csgraph import connected_components
def comps(V,F):
    _,inv=np.unique(V.round(4),axis=0,return_inverse=True); inv=inv.ravel(); G=inv[F]; n=inv.max()+1
    e=np.concatenate([G[:,[0,1]],G[:,[1,2]]]); A=sp.coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(n,n))
    return connected_components(A,directed=False)[1][G[:,0]]
src=sys.argv[1]; s=trimesh.load(src)
for name,g in s.geometry.items():
    T=s.graph[s.graph.nodes_geometry[0]][0]
    V=trimesh.transform_points(g.vertices,T); F=g.faces; fl=comps(V,F)
    cx,cz=-3.2,-2.55; keep=np.ones(len(F),bool); rem=[]
    for i in np.unique(fl):
        sel=fl==i; P=V[F[sel].ravel()]; r=np.hypot(P[:,0]-cx,P[:,2]-cz)
        if P[:,1].max()<8.5 and r.min()>4.9 and sel.sum()<400: keep[sel]=False; rem.append((sel.sum(),P.min(0).round(1).tolist(),P.max(0).round(1).tolist()))
    print(src,'removed',len(rem),'comps',(~keep).sum(),'tris'); [print(' ',x) for x in rem]
    g.update_faces(keep); g.remove_unreferenced_vertices()
s.export(sys.argv[2])
