# Procedural card-style building kit: strip-tiled walls/roofs on the shared card2 atlas + modelled details.
import numpy as np
from atlas import STRIPS, CELLS, S, RECTS
def norm(v): v=np.asarray(v,float); return v/np.linalg.norm(v)
class Mesh:
    def __init__(s): s.P=[]; s.UV=[]; s.lod=[]; s.remap={}  # lod: min lod level that drops this tri (99 = never)
    LOD=99
    def tri(s,a,b,c,ua,ub,uc):
        s.P+= [a,b,c]; s.UV+=[ua,ub,uc]; s.lod.append(s.LOD)
    # ---- strip-mapped planar convex polygon ----
    def poly(s,pts,o,ua,va,strip,uoff=0.0,flip=False):
        strip=s.remap.get(strip,strip)
        pts=[np.asarray(p,float) for p in pts]; ua=norm(ua); va=np.asarray(va,float); va=norm(va-ua*np.dot(va,ua)); o=np.asarray(o,float)
        nn=np.cross(ua,va); r=np.dot(pts[0]-o,nn); o=o+nn*r
        y0,h,wm,bh=STRIPS[strip]
        st=[(np.dot(p-o,ua),np.dot(p-o,va)) for p in pts]
        tmin=min(t for _,t in st); tmax=max(t for _,t in st)
        k0=int(np.floor(tmin/bh)); k1=int(np.ceil(tmax/bh))
        for k in range(k0,k1):
            lo,hi=k*bh,(k+1)*bh
            P=clip(clip(st,lo,1),hi,-1)
            if len(P)<3: continue
            u=[(x/wm+uoff) for x,_ in P]; v=[(y0+(hi-t)/bh*h)/S for _,t in P]
            # nudge V inside strip
            v=[min(max(vv,(y0+1.5)/S),(y0+h-1.5)/S) for vv in v]
            W=[o+ua*x+va*t for x,t in P]
            for i in range(1,len(P)-1):
                ids=(0,i,i+1) if not flip else (0,i+1,i)
                s.tri(*(W[j] for j in ids),*((u[j],1-v[j]) for j in ids))
    def cell(s,corners,name,u0=0,u1=1,v0=0,v1=1):
        # corners: bl, br, tr, tl ; maps a sub-rect of a detail cell
        if name=='door':
            c_=np.mean(np.asarray(corners,float),0); s.__dict__.setdefault('doors',[]).append(c_)
        if name=='banner' and u0==0.08 and u1==0.92 and v1==0.85 and not getattr(s,'no_relief',False): s._relief(corners)
        name=s.remap.get(name,name)
        if name in RECTS: rx,ry,rw,rh=RECTS[name]; x0,y0,cw,ch=rx/S,ry/S,rw/S,rh/S
        else: i=CELLS.index(name); x0=i*256/S; y0=1536/S; cw=256/S; ch=512/S
        uv=[(x0+cw*(u0*0.98+0.01),1-(y0+ch*(1-v0)*0.99+0.002)),(x0+cw*(u1*0.98+0.01),1-(y0+ch*(1-v0)*0.99+0.002)),
            (x0+cw*(u1*0.98+0.01),1-(y0+ch*(1-v1)*0.99+0.002)),(x0+cw*(u0*0.98+0.01),1-(y0+ch*(1-v1)*0.99+0.002))]
        c=[np.asarray(p,float) for p in corners]
        s.tri(c[0],c[1],c[2],uv[0],uv[1],uv[2]); s.tri(c[0],c[2],c[3],uv[0],uv[2],uv[3])
    def obox(s,c,ax,ay,az,size,strip,uoff=0.0):
        # oriented box; ax,ay,az unit axes; size (sx,sy,sz); side faces use ay as V (up)
        c=np.asarray(c,float); ax,ay,az=norm(ax),norm(ay),norm(az); hx,hy,hz=np.asarray(size)/2
        def q(o,a,b,ha,hb,up):
            pts=[o-a*ha-b*hb,o+a*ha-b*hb,o+a*ha+b*hb,o-a*ha+b*hb]
            s.poly(pts,o-a*ha-b*hb,a,b,strip,uoff)
        q(c+az*hz,ax,ay,hx,hy,1); q(c-az*hz,-ax,ay,hx,hy,1)
        q(c+ax*hx,-az,ay,hz,hy,1); q(c-ax*hx,az,ay,hz,hy,1)
        q(c+ay*hy,ax,-az,hx,hz,1); q(c-ay*hy,ax,az,hx,hz,1)
    def box(s,lo,hi,strip,uoff=0.0):
        lo=np.asarray(lo,float);hi=np.asarray(hi,float); s.obox((lo+hi)/2,(1,0,0),(0,1,0),(0,0,1),hi-lo,strip,uoff)
    def beam(s,a,b,w,strip='beam',up=(0,1,0)):
        a=np.asarray(a,float);b=np.asarray(b,float); d=b-a; L=np.linalg.norm(d); ax=d/L
        upv=np.asarray(up,float);
        if abs(np.dot(upv,ax))>0.9: upv=np.array([1.0,0,0]) if abs(ax[0])<0.9 else np.array([0,0,1.0])
        az=norm(np.cross(ax,upv)); ay=np.cross(az,ax)
        s.obox((a+b)/2,ax,ay,az,(L,w,w),strip)
    def blob(s,c,r,name,seg=6,squash=1.0):
        # low-poly ellipsoid mapped to a detail cell (plants/flowers)
        c=np.asarray(c,float); rings=3
        def p(i,j):
            th=np.pi*i/rings; ph=2*np.pi*j/seg
            return c+np.array([r*np.sin(th)*np.cos(ph),r*np.cos(th)*squash,r*np.sin(th)*np.sin(ph)])
        for i in range(rings):
            for j in range(seg):
                a,b,cc,d=p(i,j),p(i+1,j),p(i+1,j+1),p(i,j+1)
                uv=lambda ii,jj:(0,0)
                ci=CELLS.index(name); x0=ci*256/S+0.01*256/S
                U=lambda jj:x0+(jj/seg)*0.9*256/S; V=lambda ii:1-(1536+ (ii/rings)*500+5)/S
                s.tri(a,cc,b,(U(j),V(i)),(U(j+1),V(i+1)),(U(j),V(i+1)))
                s.tri(a,d,cc,(U(j),V(i)),(U(j+1),V(i)),(U(j+1),V(i+1)))
    def _sculpt(s,V,F,strip='statue',off=(0,0,0),scale=1.0,rot=0):
        # organic mesh (marching cubes) mapped into a strip by world position
        strip=s.remap.get(strip,strip); y0,h,wm,bh=STRIPS[strip]
        r=np.radians(rot); R=np.array([[np.cos(r),0,np.sin(r)],[0,1,0],[-np.sin(r),0,np.cos(r)]])
        V=np.asarray(V,float)*scale@R.T+np.asarray(off,float)
        for f in F:
            P=V[f]; n=np.cross(P[1]-P[0],P[2]-P[0]); ax=np.argmax(np.abs(n))
            uv=[]
            for p in P:
                a,b=[(p[1],p[2]),(p[0],p[2]),(p[0],p[1])][ax]
                uv.append((a/wm,1-(y0+1.5+((b/bh)%1.0)*(h-3))/S))
            s.tri(P[0],P[1],P[2],*uv)
    def _relief(s,corners):
        import sculpt, kit2
        c=[np.asarray(p,float) for p in corners]; t=norm(c[1]-c[0]); up=norm(c[3]-c[0]); n=norm(np.cross(t,up)); h=np.linalg.norm(c[3]-c[0])
        tris=(1100,380,0)[kit2.Q]
        if not tris: return
        V,F=sculpt.get('lionrelief',tris); sc=h*0.72; base=(c[0]+c[1])/2+up*h*0.12+n*0.02
        W=base+V[:,[0]]*sc*t+V[:,[1]]*sc*up+V[:,[2]]*sc*n
        o=s.LOD; s.LOD=1; s.sculpt(W,F,'gold'); s.LOD=o
    def sculpt(s,V,F,strip='statue',off=(0,0,0),scale=1.0,rot=0,_k=None):
        return s._sculpt(V,F,strip,off,scale,rot)
    def merge(s,o,off=(0,0,0),rot=0):
        P=np.array(o.P).reshape(-1,3); r=np.radians(rot); R=np.array([[np.cos(r),0,np.sin(r)],[0,1,0],[-np.sin(r),0,np.cos(r)]])
        P=P@R.T+np.asarray(off,float); s.P+=list(P); s.UV+=list(o.UV); s.lod+=list(o.lod)
        for d_ in getattr(o,'doors',[]): s.__dict__.setdefault('doors',[]).append(R@d_+np.asarray(off,float))
    def arrays(s,maxlod=99):
        keep=np.array(s.lod)>maxlod
        P=np.array(s.P).reshape(-1,3,3)[keep].reshape(-1,3); UV=np.array(s.UV).reshape(-1,3,2)[keep].reshape(-1,2)
        F=np.arange(len(P)).reshape(-1,3)
        n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
        N=np.repeat(n,3,0)
        return P,F,UV,N
def clip(poly,val,sign):
    # keep points with sign*(t-val)>=0
    out=[]; n=len(poly)
    for i in range(n):
        a=poly[i]; b=poly[(i+1)%n]; da=sign*(a[1]-val); db=sign*(b[1]-val)
        if da>=0: out.append(a)
        if (da>=0)!=(db>=0):
            t=da/(da-db); out.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
    return out
