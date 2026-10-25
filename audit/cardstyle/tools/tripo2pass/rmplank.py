import trimesh,numpy as np,scipy.sparse as sp,sys
from scipy.sparse.csgraph import connected_components
s=trimesh.load(sys.argv[1])
for name,g in s.geometry.items():
    node=[n for n in s.graph.nodes_geometry if s.graph[n][1]==name][0]; T=s.graph[node][0]
    V=trimesh.transform_points(g.vertices,T); F=g.faces
    _,inv=np.unique(V.round(4),axis=0,return_inverse=True); inv=inv.ravel(); G=inv[F]; n=inv.max()+1
    e=np.concatenate([G[:,[0,1]],G[:,[1,2]]]); lab=connected_components(sp.coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(n,n)),directed=False)[1][G[:,0]]
    keep=np.ones(len(F),bool)
    for i in np.unique(lab):
        sel=lab==i; P=V[F[sel].ravel()]
        if P[:,2].min()<-6.5 and P[:,0].min()>4.5: keep[sel]=False; print('rm',sel.sum(),P.min(0).round(1),P.max(0).round(1))
    g.update_faces(keep); g.remove_unreferenced_vertices()
s.export(sys.argv[2])
