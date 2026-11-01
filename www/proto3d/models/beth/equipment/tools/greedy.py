import numpy as np
DIRS=[((1,0,0),0),((-1,0,0),0),((0,1,0),1),((0,-1,0),1),((0,0,1),2),((0,0,-1),2)]
def quads(g):
    """greedy-merged exposed faces. returns list of (corners[4] in voxel units, dir, colour index)"""
    P=np.pad(g,1); out=[]; sh=g.shape
    for d,ax in DIRS:
        nb=P[1+d[0]:1+d[0]+sh[0],1+d[1]:1+d[1]+sh[1],1+d[2]:1+d[2]+sh[2]]
        vis=np.where((g>0)&(nb==0),g,0)
        o=[i for i in range(3) if i!=ax]; s=d[ax]
        for k in range(sh[ax]):
            sl=np.take(vis,k,axis=ax).copy()   # 2D over o[0],o[1]
            H,W=sl.shape
            for a in range(H):
                b=0
                while b<W:
                    c=sl[a,b]
                    if c==0: b+=1; continue
                    w=1
                    while b+w<W and sl[a,b+w]==c: w+=1
                    h=1
                    while a+h<H and np.all(sl[a+h,b:b+w]==c): h+=1
                    sl[a:a+h,b:b+w]=0
                    base=[0,0,0]; base[ax]=k+(1 if s>0 else 0)
                    cs=[]
                    for da,db in [(0,0),(h,0),(h,w),(0,w)]:
                        q=list(base); q[o[0]]=a+da; q[o[1]]=b+db; cs.append(q)
                    out.append((cs,d,int(c))); b+=w
    return out
