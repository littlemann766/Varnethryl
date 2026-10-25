# LOD decimation for unindexed card2 meshes: quadric on positions, then per-face UV re-projection from the closest
# source triangle (barycentric extrapolation on that triangle's plane), so each new face samples one strip/cell.
import numpy as np, pymeshlab, trimesh
def decimate(P,F,UV,target):
    if len(F)<=target: return P,F,UV
    _,first,inv=np.unique(P.round(4),axis=0,return_index=True,return_inverse=True); inv=inv.ravel()
    V=np.ascontiguousarray(P[first],dtype=np.float64); Fm=inv[F]; ok=(Fm[:,0]!=Fm[:,1])&(Fm[:,1]!=Fm[:,2])&(Fm[:,0]!=Fm[:,2]); Fm=np.ascontiguousarray(Fm[ok],dtype=np.int32)
    ms=pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(vertex_matrix=V,face_matrix=Fm))
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(target),qualitythr=0.3,preservenormal=True,planarquadric=True,preservetopology=False)
    m=ms.current_mesh(); V2=m.vertex_matrix(); F2=m.face_matrix()
    from scipy.spatial import cKDTree
    T=V2[F2]; cen=T.mean(1); n2=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n2/=np.linalg.norm(n2,axis=1,keepdims=True)+1e-12
    S=P[F]; sc=S.mean(1); sn=np.cross(S[:,1]-S[:,0],S[:,2]-S[:,0]); sa=np.linalg.norm(sn,axis=1); sn/=sa[:,None]+1e-12
    d,ii=cKDTree(sc).query(cen,k=12)
    pl=np.abs(np.einsum('nkj,nkj->nk',cen[:,None]-sc[ii],sn[ii]))+0.5*d/(d.max(1,keepdims=True)+1e-9)+1.5*(1-np.einsum('nj,nkj->nk',n2,sn[ii]))
    tid=ii[np.arange(len(ii)),pl.argmin(1)]
    A=P[F[tid,0]];B=P[F[tid,1]];C=P[F[tid,2]]; ua=UV[F[tid,0]];ub=UV[F[tid,1]];uc=UV[F[tid,2]]
    out=np.zeros((len(F2),3,2))
    for k in range(3):
        bc=trimesh.triangles.points_to_barycentric(np.stack([A,B,C],1),T[:,k])
        bc=np.where(np.isfinite(bc).all(1,keepdims=True),bc,1/3.0); out[:,k]=bc[:,[0]]*ua+bc[:,[1]]*ub+bc[:,[2]]*uc
    # keep strip V inside the source triangle's V range (avoid bleeding into neighbour strips/cells)
    vlo=np.minimum(np.minimum(ua[:,1],ub[:,1]),uc[:,1])[:,None]; vhi=np.maximum(np.maximum(ua[:,1],ub[:,1]),uc[:,1])[:,None]
    out[:,:,1]=np.clip(out[:,:,1],vlo,vhi)
    P2=T.reshape(-1,3); return P2,np.arange(len(P2)).reshape(-1,3),out.reshape(-1,2)
def normals(P,F):
    n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12; return np.repeat(n,3,0)
