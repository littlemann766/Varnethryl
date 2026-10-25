# Round-4 High detail injectors (local building units, pre-K). Used by hi_bld.py.
import numpy as np, math
import kit
from kit import M, rot, tile_uv
WH=np.ones(3)
def quad(m,p0,p1,p2,p3,tile,col,uvs):
  n=np.cross(p1-p0,p3-p0);n/=np.linalg.norm(n)+1e-12
  uv=[tile_uv(tile,*np.clip(u,0,1)) for u in uvs]
  m.tri([p0,p1,p2],[uv[0],uv[1],uv[2]],col,n=[n]*3);m.tri([p0,p2,p3],[uv[0],uv[2],uv[3]],col,n=[n]*3)
def roof_rows(m,cx,cz,w,d,y,rise,over,ridge,tile,col,tw=.26,th=.2,budget=6500):
  """individual overlapping tiles/shingles on both slopes (4 tris each: top + butt edge)."""
  if ridge=='x':
    sub=M();roof_rows(sub,0,0,d,w,y,rise,over,'z',tile,col,tw,th,budget);m.merge(sub,rot('y',math.pi/2),(cx,0,cz));return
  hw=w/2+over;L=d+2*over;z0=cz-d/2-over;ext=over*rise/(w/2)
  for s in (-1,1):
    E=np.array([cx+s*hw,y-ext,z0]);Rg=np.array([cx,y+rise,z0]);V=Rg-E;sl=np.linalg.norm(V);V/=sl;U=np.array([0,0,1.])
    n=np.cross(U,V);n=n if n[1]>0 else -n
    sc=max(1.0,math.sqrt((L/tw)*(sl/th)*4/budget));tw2,th2=tw*sc,th*sc
    rows=int(sl/th2);cols=int(L/tw2)+1;r=kit.rng
    for j in range(rows):
      v0=j*th2;off=(tw2/2 if j%2 else 0)
      for i in range(cols):
        u0=i*tw2-off;u1=min(L,u0+tw2*.94);u0=max(0,u0)
        if u1-u0<.05:continue
        lift=.03+.03*(j%1)
        a=E+U*u0+V*v0+n*(lift+.05);b=E+U*u1+V*v0+n*(lift+.05);c=E+U*u1+V*(v0+th2*1.35)+n*lift;dd=E+U*u0+V*(v0+th2*1.35)+n*lift
        cc=col*(1+r.uniform(-.06,.06));uu=lambda q:((q[0]%1.6)/1.6,(q[1]%1.4)/1.4)
        quad(m,a,b,c,dd,tile,cc,[uu((u0,v0)),uu((u1,v0)),uu((u1,v0+th2)),uu((u0,v0+th2))])
        quad(m,a-n*.05,b-n*.05,b,a,tile,cc*.6,[(0,0),(1,0),(1,.1),(0,.1)])
def stone_relief(m,A,B,y0,y1,openings,tile,col,bw=.62,bh=.34,depth=.035,budget=2600):
  """proud ashlar blocks on the outer face of a wall run (front + top + sides faces)."""
  A=np.array([A[0],0,A[1]],float);B=np.array([B[0],0,B[1]],float);L=np.linalg.norm(B-A);U=(B-A)/L;N=np.array([-U[2],0,U[0]]);Y=np.array([0,1.,0])
  sc=max(1.0,math.sqrt(L*(y1-y0)/(bw*bh)*6/budget));bw,bh=bw*sc,bh*sc;r=kit.rng
  rows=int((y1-y0)/bh)
  for j in range(rows):
    yb=y0+j*bh;off=(bw/2 if j%2 else 0);u=-off
    while u<L:
      w=bw*r.uniform(.8,1.2);ua,ub=max(0,u)+.03,min(L,u+w)-.03;u+=w
      if ub-ua<.12:continue
      cu=(ua+ub)/2
      if any(abs(cu-o[0])<o[1]/2+.25 and yb+bh>o[2]-.1 and yb<o[3]+.1 for o in openings):continue
      dp=depth*r.uniform(.6,1.4);c=col*(1+r.uniform(-.08,.08))
      p=lambda uu,yy,dd:A+U*uu+Y*yy+N*dd
      t0,t1=yb+.025,yb+bh-.025;uvs=lambda a,b2,c2,d2:[((a%1.6)/1.6,1-(c2%1.6)/1.6),((b2%1.6)/1.6,1-(c2%1.6)/1.6),((b2%1.6)/1.6,1-(d2%1.6)/1.6),((a%1.6)/1.6,1-(d2%1.6)/1.6)]
      quad(m,p(ua,t0,dp),p(ub,t0,dp),p(ub,t1,dp),p(ua,t1,dp),tile,c,uvs(ua,ub,t0,t1))
      quad(m,p(ua,t1,dp),p(ub,t1,dp),p(ub,t1,0),p(ua,t1,0),tile,c*.9,[(0,0),(1,0),(1,.05),(0,.05)])
      quad(m,p(ua,t0,0),p(ub,t0,0),p(ub,t0,dp),p(ua,t0,dp),tile,c*.7,[(0,0),(1,0),(1,.05),(0,.05)])
      quad(m,p(ua,t0,0),p(ua,t0,dp),p(ua,t1,dp),p(ua,t1,0),tile,c*.8,[(0,0),(.05,0),(.05,1),(0,1)])
      quad(m,p(ub,t0,dp),p(ub,t0,0),p(ub,t1,0),p(ub,t1,dp),tile,c*.8,[(0,0),(.05,0),(.05,1),(0,1)])
def ring_relief(m,R,y0,y1,door,tile,col,bw=.62,bh=.34,depth=.035,budget=3000,taper=0.0):
  """proud ashlar blocks around a round wall (outer face). door=(width,height) centred on +z."""
  C=2*math.pi*R;sc=max(1.0,math.sqrt(C*(y1-y0)/(bw*bh)*10/budget));bw,bh=bw*sc,bh*sc;r=kit.rng
  rows=int((y1-y0)/bh)
  for j in range(rows):
    yb=y0+j*bh;rr=R-taper*(yb-y0)/max(y1-y0,1e-6);n=max(8,int(2*math.pi*rr/bw));off=(.5 if j%2 else 0)
    for i in range(n):
      a0=(i+off)/n*2*math.pi+.01;a1=(i+off+1)/n*2*math.pi-.01;am=(a0+a1)/2
      if door and abs(math.atan2(math.sin(am),math.cos(am)))<math.asin(min(1,(door[0]/2+.25)/rr)) and yb<door[1]+.1:continue
      dp=depth*r.uniform(.6,1.4);c=col*(1+r.uniform(-.08,.08));t0,t1=yb+.025,yb+bh-.025
      p=lambda a,y,d:np.array([math.sin(a)*(rr+d),y,math.cos(a)*(rr+d)])
      u0,u1=(a0*rr%1.6)/1.6,(a0*rr%1.6)/1.6+(a1-a0)*rr/1.6
      quad(m,p(a0,t0,dp),p(a1,t0,dp),p(a1,t1,dp),p(a0,t1,dp),tile,c,[(u0,.3),(min(1,u1),.3),(min(1,u1),.5),(u0,.5)])
      quad(m,p(a0,t1,dp),p(a1,t1,dp),p(a1,t1,0),p(a0,t1,0),tile,c*.9,[(0,0),(1,0),(1,.05),(0,.05)])
      quad(m,p(a0,t0,0),p(a1,t0,0),p(a1,t0,dp),p(a0,t0,dp),tile,c*.7,[(0,0),(1,0),(1,.05),(0,.05)])
