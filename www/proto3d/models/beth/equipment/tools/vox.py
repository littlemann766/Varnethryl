import numpy as np, math
# grid g[x,y,z] = palette index (0 empty). palette: list of (rgb, emissive)
class V:
    def __init__(s,n=20,m=None,k=None): s.g=np.zeros((n,m or n,k or n),np.int16); s.pal=[None]
    def c(s,rgb,glow=0):
        for i,p in enumerate(s.pal):
            if p==(rgb,glow): return i
        s.pal.append((rgb,glow)); return len(s.pal)-1
    def box(s,x0,x1,y0,y1,z0,z1,col):
        g=s.g; g[max(0,x0):x1+1,max(0,y0):y1+1,max(0,z0):z1+1]=col
    def put(s,x,y,z,col):
        x,y,z=int(round(x)),int(round(y)),int(round(z))
        if 0<=x<s.g.shape[0] and 0<=y<s.g.shape[1] and 0<=z<s.g.shape[2]: s.g[x,y,z]=col
    def ball(s,cx,cy,cz,r,col,sq=(1,1,1)):
        X,Y,Z=np.indices(s.g.shape); m=((X-cx)/sq[0])**2+((Y-cy)/sq[1])**2+((Z-cz)/sq[2])**2<=r*r; s.g[m]=col
    def line(s,a,b,col,t=0):
        n=int(max(abs(b[i]-a[i]) for i in range(3))*2)+1
        for i in range(n+1):
            p=[a[j]+(b[j]-a[j])*i/n for j in range(3)]
            for dx in range(-t,t+1):
                for dz in range(-t,t+1): s.put(p[0]+dx,p[1],p[2]+dz,col)
    def down(s):
        g=s.g; sh=[(d+1)//2 for d in g.shape]; o=V(*sh); o.pal=s.pal
        for x in range(sh[0]):
            for y in range(sh[1]):
                for z in range(sh[2]):
                    b=g[2*x:2*x+2,2*y:2*y+2,2*z:2*z+2].ravel(); b=b[b>0]
                    if len(b)>=3 or (len(b)>0 and b.size>0 and len(b)>=2): o.g[x,y,z]=np.bincount(b).argmax()
        return o
def faces(v):
    g=v.g; P=np.pad(g,1); quads=[]
    D=[((1,0,0),0),((-1,0,0),0),((0,1,0),1),((0,-1,0),1),((0,0,1),2),((0,0,-1),2)]
    idx=np.argwhere(g>0)
    for (d,ax) in D:
        nb=P[idx[:,0]+1+d[0],idx[:,1]+1+d[1],idx[:,2]+1+d[2]]
        for p in idx[nb==0]: quads.append((tuple(p),d,int(g[tuple(p)])))
    return quads
