import trimesh,numpy as np,sys
from scipy import ndimage
from skimage.measure import find_contours, approximate_polygon
from scipy.spatial import cKDTree
sys.path.insert(0,'/tmp'); from cap import earclip
src,dst,xp,tol=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]); res=0.08
s=trimesh.load(src); tot=0
for name,g in s.geometry.items():
    node=[n for n in s.graph.nodes_geometry if s.graph[n][1]==name][0]; T=s.graph[node][0]; Ti=np.linalg.inv(T)
    Vw=trimesh.transform_points(g.vertices,T); F=g.faces
    _,first,inv=np.unique(Vw.round(4),axis=0,return_index=True,return_inverse=True); inv=inv.ravel(); G=inv[F]
    DE=np.concatenate([G[:,[0,1]],G[:,[1,2]],G[:,[2,0]]]); key=np.sort(DE,1); u,ii,c=np.unique(key,axis=0,return_index=True,return_counts=True)
    bd=DE[ii[c==1]]; Pm=Vw[first]; on=(np.abs(Pm[bd[:,0],0]-xp)<tol)&(np.abs(Pm[bd[:,1],0]-xp)<tol); bd=bd[on]
    if not len(bd): continue
    A=Pm[bd[:,0]][:,[2,1]]; B=Pm[bd[:,1]][:,[2,1]]; lo=np.minimum(A,B).min(0)-0.5; hi=np.maximum(A,B).max(0)+0.5
    W,H=((hi-lo)/res).astype(int)+1; img=np.zeros((W,H),bool)
    for a,b in zip(A,B):
        n=int(np.linalg.norm(b-a)/res*2)+2
        for t in np.linspace(0,1,n): p=((a+(b-a)*t-lo)/res).astype(int); img[p[0],p[1]]=True
    img=ndimage.binary_closing(ndimage.binary_dilation(img,iterations=2),iterations=4); img=ndimage.binary_fill_holes(img); img=ndimage.binary_erosion(img,iterations=2)
    lab,nl=ndimage.label(img)
    bvi=np.unique(bd.ravel()); tree=cKDTree(Pm[bvi][:,[2,1]])
    newV=[];newUV=[];newF=[]; base=len(g.vertices); uv=g.visual.uv
    for L in range(1,nl+1):
        if (lab==L).sum()<20: continue
        cs=find_contours(np.pad(lab==L,1).astype(float),0.5)
        if not cs: continue
        cpt=max(cs,key=len); cpt=approximate_polygon(cpt,0.8)[:-1]
        if len(cpt)<3: continue
        P2=(cpt-1)*res+lo
        tris=earclip(P2)
        k0=len(newV)
        for q in P2:
            newV.append([xp,q[1],q[0]]); d,j=tree.query(q); newUV.append(uv[first[bvi[j]]])
        for a,b,cc in tris: newF.append([base+k0+a,base+k0+b,base+k0+cc])
    if not newF: continue
    newV=np.array(newV); newF=np.array(newF); Vall=np.vstack([Vw,newV])
    nrm=np.cross(Vall[newF[:,1]]-Vall[newF[:,0]],Vall[newF[:,2]]-Vall[newF[:,0]]); out=np.sign(xp)
    fl=nrm[:,0]*out<0; newF[fl]=newF[fl][:,::-1]
    Vl=trimesh.transform_points(newV,Ti)
    vis=g.visual; g2=trimesh.Trimesh(np.vstack([g.vertices,Vl]),np.vstack([F,newF]),process=False)
    g2.visual=trimesh.visual.TextureVisuals(uv=np.vstack([uv,np.array(newUV)]),material=vis.material)
    s.geometry[name]=g2; tot+=len(newF)
s.export(dst); print(src,'cap tris',tot)
