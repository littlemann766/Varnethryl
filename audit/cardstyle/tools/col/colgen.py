# collision GLB per building: 0.5 m column grid from surface samples, enclosed cells filled, greedy-merged boxes,
# door notches (>=1.4 x 2.3 m) carved; nodes named *-colonly so Godot imports StaticBody3D.
import json,sys,os,numpy as np,trimesh
from scipy import ndimage
C=0.5
def build(src,doors,out,through=False):
    m=trimesh.load(src,force='mesh')
    pts,_=trimesh.sample.sample_surface_even(m,max(20000,int(m.area*40)))
    pts=np.vstack([pts,m.vertices])
    lo=np.floor(m.bounds[0][[0,2]]/C)*C-C; hi=np.ceil(m.bounds[1][[0,2]]/C)*C+C
    nx,nz=((hi-lo)/C).astype(int)+1
    ix=((pts[:,0]-lo[0])/C).astype(int); iz=((pts[:,2]-lo[1])/C).astype(int)
    ylo=np.full((nx,nz),np.inf); yhi=np.full((nx,nz),-np.inf)
    np.minimum.at(ylo,(ix,iz),pts[:,1]); np.maximum.at(yhi,(ix,iz),pts[:,1])
    occ=np.isfinite(ylo)
    base=occ&(ylo<1.6)
    inside=ndimage.binary_fill_holes(base)&~base&occ   # covered (roofed) enclosed cells -> solid; open courtyards stay open
    ylo[inside]=min(0.0,m.bounds[0][1])
    ylo=np.where(ylo<0.6,min(0.0,m.bounds[0][1]),ylo)
    Q=lambda v:np.round(v/0.25)*0.25
    QH=lambda v: np.ceil(v/0.25)*0.25 if v<3.0 else (np.ceil(v/1.0)*1.0 if v<12 else np.ceil(v/2.0)*2.0)  # coarse tops above head height
    cells={}
    for i in range(nx):
        for k in range(nz):
            if occ[i,k] and yhi[i,k]>0.35 and yhi[i,k]-ylo[i,k]>0.1: cells[(i,k)]=[(Q(ylo[i,k]) if ylo[i,k]>0.01 else Q(min(0,ylo[i,k])),max(QH(yhi[i,k]),Q(ylo[i,k])+0.25))]
    cx=lambda i:lo[0]+i*C; cz=lambda k:lo[1]+k*C   # cell centre (bins start at lo, so centre=lo+i*C+C/2)
    for d in doors:
        p=np.array(d['pos']); n=np.array(d['normal']); n=n/np.linalg.norm(n); t=np.array([n[2],0,-n[0]])
        W=max(d['width'],1.4)/2+0.3; H=max(d['height'],2.3)+0.05; y0=p[1]
        depth=d.get('depth',1.5)
        for (i,k),iv in list(cells.items()):
            q=np.array([cx(i)+C/2,0,cz(k)+C/2])-p; a=np.dot(q,t); b=np.dot(q,n)
            if abs(a)<=W and -depth<=b<=3.0:
                if b>0.0:   # outside, in front of the door: drop low steps/props, keep nothing below head height
                    new=[(l,h) for l,h in iv if l>=y0+H]
                else:
                    new=[]
                    for l,h in iv:
                        if l<y0-0.05: new.append((l,min(h,Q(y0))))
                        if h>y0+H: new.append((max(l,np.ceil((y0+H)/0.25)*0.25),h))
                    new=[(l,h) for l,h in new if h-l>=0.2]
                if new: cells[(i,k)]=new
                else: del cells[(i,k)]
    # greedy merge per identical interval
    boxes=[]; key={}
    for (i,k),iv in cells.items():
        for v in iv: key.setdefault(v,set()).add((i,k))
    for (l,h),S in key.items():
        while S:
            i,k=min(S); k1=k
            while (i,k1+1) in S: k1+=1
            i1=i
            while all((i1+1,kk) in S for kk in range(k,k1+1)): i1+=1
            for a in range(i,i1+1):
                for b in range(k,k1+1): S.discard((a,b))
            boxes.append(((cx(i),l,cz(k)),(cx(i1+1),h,cz(k1+1))))
    parts=[]
    for (a,b) in boxes:
        a,b=np.array(a),np.array(b); bx=trimesh.creation.box(extents=b-a); bx.apply_translation((a+b)/2); parts.append(bx)
    mm=trimesh.util.concatenate(parts); mm.merge_vertices()
    sc=trimesh.Scene(); sc.add_geometry(mm,node_name=os.path.basename(out)[:-8]+'-colonly',geom_name=os.path.basename(out)[:-8]+'-colonly')
    sc.export(out); return len(boxes)
if __name__=='__main__':
    print(build(sys.argv[1],json.loads(sys.argv[2]),sys.argv[3]))
