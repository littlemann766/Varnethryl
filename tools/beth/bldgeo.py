# Planar-grid geometry helpers: every face is tiled in atlas-sized cells so a clamped atlas tile repeats correctly.
import numpy as np, math
import kit
from kit import M, tile_uv, rot
def _clip(poly,cell):
  # poly: list of 2D pts (convex, CCW); cell: (x0,y0,x1,y1)
  def clip(P,inside,inter):
    out=[]
    for i in range(len(P)):
      a,b=P[i-1],P[i];ia,ib=inside(a),inside(b)
      if ib:
        if not ia:out.append(inter(a,b))
        out.append(b)
      elif ia:out.append(inter(a,b))
    return out
  x0,y0,x1,y1=cell;P=poly
  for ax,v,s in ((0,x0,1),(0,x1,-1),(1,y0,1),(1,y1,-1)):
    if not P:break
    P=clip(P,lambda p:(p[ax]-v)*s>=-1e-9,lambda a,b:(lambda t:(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))((v-a[ax])/((b[ax]-a[ax]) or 1e-12)))
  return P
def face(m,O,U,V,poly,tile,col,cell=(1.6,1.6),off=(0,0),jit=.05,rng=None,normal=None):
  """poly: convex polygon in (u,v) plane coords. O origin, U/V unit axes (3D). Normal = U x V."""
  O,U,V=np.asarray(O,float),np.asarray(U,float),np.asarray(V,float);n=np.cross(U,V) if normal is None else np.asarray(normal,float)
  n=n/np.linalg.norm(n);us=[p[0] for p in poly];vs=[p[1] for p in poly];cu,cv=cell
  i0,i1=math.floor((min(us)+off[0])/cu),math.ceil((max(us)+off[0])/cu);j0,j1=math.floor((min(vs)+off[1])/cv),math.ceil((max(vs)+off[1])/cv)
  r=rng or kit.rng
  for i in range(i0,i1):
    for j in range(j0,j1):
      c=(i*cu-off[0],j*cv-off[1],(i+1)*cu-off[0],(j+1)*cv-off[1]);P=_clip(poly,c)
      if len(P)<3:continue
      cc=np.asarray(col)*(1+r.uniform(-jit,jit))
      pts=[O+U*p[0]+V*p[1] for p in P];uv=[tile_uv(tile,min(1,max(0,(p[0]-c[0])/cu)),min(1,max(0,1-(p[1]-c[1])/cv))) for p in P]
      for k in range(1,len(P)-1):m.tri([pts[0],pts[k],pts[k+1]],[uv[0],uv[k],uv[k+1]],cc,n=[n]*3)
def rect(m,O,U,V,w,h,tile,col,cell=(1.6,1.6),**k):face(m,O,U,V,[(0,0),(w,0),(w,h),(0,h)],tile,col,cell,**k)
def obox(m,c,size,tile,col,yaw=0,cell=(1.6,1.6),faces='all',tiles=None):
  """oriented box: c=center-bottom (x,y,z), size=(sx,sy,sz), yaw about y. tiles: dict face->tile"""
  sx,sy,sz=size;R=rot('y',yaw);c=np.asarray(c,float);ex,ey,ez=R@np.array([1.,0,0]),np.array([0,1.,0]),R@np.array([0,0,1.])
  b=c-ex*sx/2-ez*sz/2;t=tiles or {}
  F={'front':(b+ez*sz,ex,ey,sx,sy),'back':(b+ex*sx,-ex,ey,sx,sy),'right':(b+ex*sx+ez*sz,-ez,ey,sz,sy),'left':(b,ez,ey,sz,sy),
     'top':(b+ey*sy+ez*sz,ex,-ez,sx,sz),'bottom':(b,ex,ez,sx,sz)}
  for k,(O,U,V,w,h) in F.items():
    if faces!='all' and k not in faces:continue
    rect(m,O,U,V,w,h,t.get(k,tile),col,cell)
def wall(m,A,B,y0,y1,T,tile,col,openings=(),inner_tile=None,cell=(1.6,1.6),edge_tile=None):
  """Wall from A to B (xz) whose OUTER face is on the A->B line, thickness T toward the inside (left of A->B looking down is outside...).
  outward normal = (dz,-dx) normalized. openings: (u_center,width,y_bottom,y_top)."""
  A=np.array([A[0],0,A[1]],float);B=np.array([B[0],0,B[1]],float);L=np.linalg.norm(B-A);U=(B-A)/L;N=np.array([-U[2],0,U[0]]);Y=np.array([0,1.,0])
  cuts=sorted({0,L}|{max(0,min(L,o[0]-o[1]/2)) for o in openings}|{max(0,min(L,o[0]+o[1]/2)) for o in openings})
  pieces=[]
  for a,b in zip(cuts,cuts[1:]):
    mid=(a+b)/2;holes=sorted([(o[2],o[3]) for o in openings if abs(mid-o[0])<o[1]/2])
    y=y0
    for hb,ht in holes:
      if hb>y:pieces.append((a,b,y,hb))
      y=max(y,ht)
    if y<y1:pieces.append((a,b,y,y1))
  et=edge_tile or tile
  for a,b,ya,yb in pieces:
    w,h=b-a,yb-ya;O=A+U*a+Y*ya
    rect(m,O,U,Y,w,h,tile,col,cell,off=(a,ya))                         # outer
    rect(m,O+U*w-N*T,-U,Y,w,h,inner_tile or tile,col*0.92,cell,off=(-b,ya))  # inner
    for (yy,sgn) in ((yb,1),(ya,-1)):
      if (sgn>0 and yb<y1-1e-6) or (sgn<0 and ya>y0+1e-6) or (sgn>0 and abs(yb-y1)<1e-6):
        O2=A+U*a+Y*yy;rect(m,O2,U,-N*sgn if sgn>0 else -N,w,T,et,col,cell) if sgn>0 else rect(m,O2-N*T,U,N,w,T,et,col,cell)
    for (uu,sgn) in ((a,-1),(b,1)):
      if a<1e-6 and sgn<0 or b>L-1e-6 and sgn>0:continue
      O3=A+U*uu+Y*ya
      if sgn>0:rect(m,O3,-N,Y,T,h,et,col,cell)
      else:rect(m,O3-N*T,N,Y,T,h,et,col,cell)
  return U,N
def gable(m,cx,cz,w,d,y,rise,over,ridge,tile,col,thick=.18,gtile=None,gcol=None,cap_tile=None):
  """ridge 'z' (ridge along z) or 'x'. Slopes + fascia + gable triangles (gable on the ends)."""
  if ridge=='x':
    # build as ridge z then rotate: swap w/d and rotate points 90deg
    sub=M();gable(sub,0,0,d,w,y,rise,over,'z',tile,col,thick,gtile,gcol,cap_tile);m.merge(sub,rot('y',math.pi/2),(cx,0,cz));return
  hw=w/2+over;L=d+2*over;z0=cz-d/2-over;slope=math.hypot(hw,rise+over*rise/(w/2))
  ext=over*rise/(w/2)
  for s in (-1,1):
    E=np.array([cx+s*hw,y-ext,z0]);Rg=np.array([cx,y+rise,z0]);V=(Rg-E);sl=np.linalg.norm(V);V/=sl;U=np.array([0,0,1.])
    if s<0:rect(m,E+U*L,-U,V,L,sl,tile,col,(1.6,1.4))
    else:rect(m,E,U,V,L,sl,tile,col,(1.6,1.4))
    # underside/thickness edge
    rect(m,E,U if s>0 else U,np.array([0,-1.,0]) if False else -np.cross(U,V)*s*0+np.array([0,1e-9,0])*0+np.array([0,-thick,0])/thick,L,thick,cap_tile or 'b_timber',np.array(col)*.7,(1.6,1.6)) if False else None
    for zz,sg in ((z0,-1),(z0+L,1)):
      P=[E+np.array([0,0,zz-z0]),Rg+np.array([0,0,zz-z0])];
      obox(m,((P[0]+P[1])/2)+np.array([0,-thick/2,0]),(0.12,thick,sl),cap_tile or 'b_timber',np.array([1,1,1.])*.9,yaw=0,faces=('front','back','left','right','top','bottom')) if False else None
  # fascia boards along eaves
  for s in (-1,1):obox(m,(cx+s*hw,y-ext-.22,cz),(.16,.26,L),'b_timber',np.array([1,1,1.]),cell=(1.6,1.6))
  # ridge cap
  obox(m,(cx,y+rise-.05,cz),(.36,.3,L+.1),cap_tile or 'b_darkstone',np.array([1,1,1.]))
  # gable triangles (on wall plane, z = cz +- d/2)
  for zz,sg in ((cz+d/2,1),(cz-d/2,-1)):
    O=np.array([cx-w/2,y,zz]);U=np.array([1.,0,0]) if sg>0 else np.array([-1.,0,0]);O=O if sg>0 else np.array([cx+w/2,y,zz])
    face(m,O,U,np.array([0,1.,0]),[(0,0),(w,0),(w/2,rise)],gtile or tile,gcol if gcol is not None else col,(1.6,1.6))
    face(m,O+U*w,-U,np.array([0,1.,0]),[(0,0),(w,0),(w/2,rise)],gtile or tile,(gcol if gcol is not None else col)*np.array(.9),(1.6,1.6),off=(0,0))
def ring_wall(m,R,y0,y1,T,N,tile,col,door=None,taper=0.0,cell=(1.6,1.6)):
  """round wall, N segments. door=(width,height) centred on +z. taper: radius reduction at top."""
  for i in range(N):
    a0,a1=2*math.pi*i/N,2*math.pi*(i+1)/N
    p=lambda a,r,y:np.array([math.sin(a)*r,y,math.cos(a)*r])
    mid=(a0+a1)/2;R1=R-taper
    chord=2*R*math.sin(math.pi/N)
    ys=[(y0,y1)]
    if door and abs(math.atan2(math.sin(mid),math.cos(mid)))<math.asin(min(1,door[0]/2/R))+math.pi/N*0.5:ys=[(door[1],y1)]
    for ya,yb in ys:
      ra=R-taper*(ya-y0)/(y1-y0);rb=R-taper*(yb-y0)/(y1-y0)
      A0,A1,B1,B0=p(a0,ra,ya),p(a1,ra,ya),p(a1,rb,yb),p(a0,rb,yb)
      U=(A1-A0)/np.linalg.norm(A1-A0);V=(B0-A0);hv=np.linalg.norm(V);V/=hv
      rect(m,A0,U,V,np.linalg.norm(A1-A0),hv,tile,col,cell,off=(i*np.linalg.norm(A1-A0),ya))
      ia,ib=ra-T,rb-T;I0,I1,J1,J0=p(a0,ia,ya),p(a1,ia,ya),p(a1,ib,yb),p(a0,ib,yb)
      U2=(I0-I1)/np.linalg.norm(I0-I1);V2=(J1-I1)/np.linalg.norm(J1-I1)
      rect(m,I1,U2,V2,np.linalg.norm(I0-I1),np.linalg.norm(J1-I1),tile,col*.9,cell)
      if ya>y0:  # door lintel underside
        rect(m,I0,(A0-I0)/np.linalg.norm(A0-I0),U, np.linalg.norm(A0-I0),np.linalg.norm(A1-A0),tile,col,cell) if False else face(m,A0,U,(I0-A0)/np.linalg.norm(I0-A0),[(0,0),(np.linalg.norm(A1-A0),0),(np.linalg.norm(A1-A0),T),(0,T)],tile,col,cell)
  # top rim
  for i in range(N):
    a0,a1=2*math.pi*i/N,2*math.pi*(i+1)/N;r=R-taper
    P=[np.array([math.sin(a)*rr,y1,math.cos(a)*rr]) for a,rr in ((a0,r),(a1,r),(a1,r-T),(a0,r-T))]
    U=(P[1]-P[0]);w=np.linalg.norm(U);U/=w;V=np.cross(np.array([0,1.,0]),U);V=-V if np.dot(V,P[3]-P[0])<0 else V
    face(m,P[0],U,V,[(0,0),(w,0),(w-0.0,T),(0,T)],tile,col,cell)
