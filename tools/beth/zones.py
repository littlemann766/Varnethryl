# Round-2 zone kits (landscape atlas). Imported by build.py.
import math,numpy as np
from kit import *
from assets import *
W=lambda h:hexc(h)
def frozen_pond(r=4.0):
  m=M();n=20
  for i in range(n):
    a0,a1=2*math.pi*i/n,2*math.pi*(i+1)/n;rr=r*(1+.08*math.sin(i*1.7))
    p=[np.array([0,.06,0]),np.array([math.cos(a0)*rr,.06,math.sin(a0)*rr]),np.array([math.cos(a1)*rr,.06,math.sin(a1)*rr])]
    m.tri(p,[tile_uv('ice',.5+q[0]/r/2*.9,.5+q[2]/r/2*.9) for q in p],W(0xd8ecff),n=[np.array([0,1.,0])]*3)
  rr=np.random.default_rng(3)
  for i in range(14):a=i/14*6.283;blob(m,'snow',rr.uniform(.5,.9),scale=(1.4,.35,1),sub=1,t=(math.cos(a)*r*1.02,.05,math.sin(a)*r*1.02),col=W(0xffffff))
  for i in range(3):blob(m,'ice',.35,scale=(1,.5,1),sub=0,t=(rr.uniform(-2,2),.1,rr.uniform(-2,2)),col=W(0xffffff))
  return m
def snow_drift(seed):
  m=M();r=np.random.default_rng(seed)
  for i in range(3):blob(m,'snow',r.uniform(1.2,2.0),scale=(1.6,.35,1),sub=1,jit=.12,t=(i*1.4-1.4,0,r.uniform(-.4,.4)),col=W(0xffffff),seed=int(r.integers(1e6)),colvar=.03)
  return m
def ice_spire(seed):
  m=M();r=np.random.default_rng(seed)
  for i in range(4):blob(m,'ice',r.uniform(.3,.6),scale=(.6,r.uniform(3,5),.6),sub=0,jit=.1,t=(r.uniform(-.8,.8),0,r.uniform(-.8,.8)),col=W(0xffffff),seed=int(r.integers(1e6)))
  blob(m,'snow',1.0,scale=(1.3,.3,1.2),sub=1,t=(0,0,0),col=W(0xffffff));return m
def ash_tree(seed):
  m=dead(seed);m2=M();m2.merge(m,np.eye(3),(0,0,0),1,tint=W(0x8a8580))
  r=np.random.default_rng(seed)
  for i in range(4):a=r.uniform(0,6.28);cards(m2,'leaf',1.0,.9,1,t=(math.cos(a)*.8,3.0+r.uniform(0,.8),math.sin(a)*.8),col=W(0x6a6058),yaw=a)
  return m2
def steam_vent(seed):
  m=M();r=np.random.default_rng(seed)
  for i in range(7):a=i/7*6.283;blob(m,'basalt',r.uniform(.35,.6),sub=0,t=(math.cos(a)*.9,.1,math.sin(a)*.9),col=W(0xffffff))
  blob(m,'lavacrust',.7,scale=(1,.15,1),sub=0,t=(0,.02,0),col=W(0xffffff))
  for k in range(4):blob(m,'snow',.45+k*.28,scale=(1,.8,1),sub=1,jit=.25,t=(k*.12,1.0+k*1.0,k*.05),col=W(0xd6d2cc)*(1-k*.03),colvar=.02)
  return m
def basalt_boulder(seed):return rock(seed,1.2,kind='basalt',sq=(1.2,.7,1),top=W(0x8a7e80))
def pier_post():
  m=M();cyl(m,'bark',.18,.16,3.2,8,t=(0,-1.6,0),cap=True,col=W(0x9a8070));cyl(m,'cloth',.2,.2,.18,8,t=(0,1.1,0),col=W(0xb09a70));cyl(m,'cloth',.2,.2,.12,8,t=(0,.8,0),col=W(0xb09a70));return m
def crate_stack():
  m=M();c=crate()
  for (x,y,z,ry) in ((0,0,0,0),(.95,0,.1,.3),(.4,.9,.05,.8)):m.merge(c,rot('y',ry),(x,y,z))
  return m
def net_rack():
  m=M()
  for s in (-1,1):cyl(m,'bark',.08,.07,2.4,6,t=(s*1.6,0,0))
  cyl(m,'bark',.06,.06,3.4,6,R=rot('z',math.pi/2),t=(1.7,2.3,0))
  for i in range(9):
    x=-1.5+i*.375;pts=[np.array([x,2.3,0])]
    for k in range(1,7):pts.append(np.array([x+.05*math.sin(k),2.3-k*.32,.08*math.sin(k*.8+i)]))
    for a,b in zip(pts,pts[1:]):
      d=b-a;L=np.linalg.norm(d);sub=M();box(sub,'cloth',.03,L,.03,col=W(0x7a6a50),j=0);
      ax=np.cross([0,1,0],d/L);ang=math.acos(np.clip(np.dot([0,1,0],d/L),-1,1));
      Rm=np.eye(3) if np.linalg.norm(ax)<1e-6 else __import__('scipy.spatial.transform',fromlist=['Rotation']).Rotation.from_rotvec(ax/np.linalg.norm(ax)*ang).as_matrix() if False else _rotvec(ax,ang);m.merge(sub,Rm,a)
  for k in range(7):box(m,'cloth',3.0,.03,.03,t=(0,2.3-k*.32,.05),col=W(0x7a6a50),j=0)
  for i in range(3):blob(m,'cloth',.25,scale=(1.4,.6,1),sub=0,t=(-1+i,.15,.5),col=W(0x8a9aa0))
  return m
def _rotvec(ax,ang):
  n=np.linalg.norm(ax)
  if n<1e-9:return np.eye(3)
  k=ax/n;K_=np.array([[0,-k[2],k[1]],[k[2],0,-k[0]],[-k[1],k[0],0]]);return np.eye(3)+math.sin(ang)*K_+(1-math.cos(ang))*K_@K_
def line(m,a,b,r=.03,tile='cloth',col=W(0x6a5a40),seg=3):
  a,b=np.asarray(a,float),np.asarray(b,float);d=b-a;L=np.linalg.norm(d);sub=M();cyl(sub,tile,r,r,L,seg,col=col,j=0)
  m.merge(sub,_rotvec(np.cross([0,1,0],d/L),math.acos(np.clip(np.dot([0,1,0],d/L),-1,1))),a)
def ship(large=True):
  """Galleon (large) or sloop. Same frame as port-ships.js buildSailingShip(scale): deck at y~1.64, keel ~1.62-depth, length L along z (bow +z)."""
  m=M();n=30;c=14;L=13 if large else 9;Wd=2.5 if large else 1.65;depth=2.3 if large else 1.25;top=1.64
  beam=lambda t:(max(.001,math.sin(math.pi*min(max(t,0),1))))**.55*Wd+.09
  sh=lambda t:.35*(2*t-1)**2   # sheer: ends rise
  secs=[]
  for i in range(n+1):
    t=i/n;z=(t-.5)*L;b=beam(t);ring=[]
    for j in range(c+1):
      a=-math.pi/2+j*math.pi/c;ring.append(np.array([b*math.sin(a),top+sh(t)-depth*math.cos(a)*(0.55+0.45*math.sin(math.pi*t)),z]))
    secs.append(ring)
  for i in range(n):
    for j in range(c):
      col=W(0x8a6040) if j not in (0,c-1) else W(0x5a3a28)
      if j in (c//2-1,c//2):col=W(0x4a3020)
      m.quad(secs[i][j],secs[i+1][j],secs[i+1][j+1],secs[i][j+1],'wood',col,(0,0,1,.25))
  for i in range(n):  # deck
    a,b,cc,d=secs[i][0],secs[i+1][0],secs[i+1][c],secs[i][c];m.quad(a,d,cc,b,'wood',W(0xd8c0a0),(0,0,1,.5))
  for i in range(1,n,2):  # bulwark posts + rail
    for s in (0,c):p=secs[i][s];box(m,'wood',.08,.55,.08,t=(p[0],p[1],p[2]),col=W(0x6a4a30),j=0)
  for s in (0,c):
    for i in range(n):line(m,secs[i][s]+[0,.55,0],secs[i+1][s]+[0,.55,0],.05,'wood',W(0x9a794b),4)
  for i in range(4,n-3,3):   # gunports
    for s in (0,c):p=secs[i][s];box(m,'iron',.05,.3,.35,t=(p[0]*1.01,p[1]-.75,p[2]),col=W(0x2a2420),j=0)
  # stern castle + windows, forecastle
  zc=-L/2+1.8 if large else -L/2+1.2;box(m,'wood',Wd*1.7,1.5 if large else .9,2.6 if large else 1.6,t=(0,top+sh(.1),zc),col=W(0x7a5a40))
  for x in (-.6,0,.6):box(m,'iron',.35,.4,.05,t=(x,top+sh(.1)+.6,zc-1.32 if large else zc-.82),col=W(0xffe0a0),j=0)
  box(m,'wood',Wd*1.8,.1,2.8 if large else 1.8,t=(0,top+sh(.1)+(1.5 if large else .9),zc),col=W(0xb08a60))
  if large:box(m,'wood',Wd*1.3,.9,2.0,t=(0,top+sh(.9),L/2-1.9),col=W(0x7a5a40))
  # masts, yards, sails, rigging
  masts=[(L*.18,9.5,3),(-L*.08,10.5,3),(-L*.3,7.5,2)] if large else [(0.3,8.0,2)]
  for (z,h,ns) in masts:
    cyl(m,'bark',.17,.1,h,8,t=(0,top,z),col=W(0xa08060));
    for k in range(ns):
      y=top+2.2+k*(h-2.6)/ns;wy=(3.4-k*.7)*(1 if large else .8);hh=(h-2.6)/ns*.86
      cyl(m,'bark',.07,.07,wy*2,6,R=rot('z',math.pi/2),t=(wy,y+hh,z),col=W(0x7a5a40))
      gw,gh=6,5
      for gi in range(gw):
        for gj in range(gh):
          def P(u,v):return np.array([-wy+2*wy*u,y+hh*(1-v)+.0,z+.55*math.sin(math.pi*u)*math.sin(math.pi*v*.9+.3)])
          u0,u1,v0,v1=gi/gw,(gi+1)/gw,gj/gh,(gj+1)/gh
          m.quad(P(u0,v1),P(u1,v1),P(u1,v0),P(u0,v0),'cloth',W(0xf0e6cc),(u0,v0,u1,v1))
    for s in (-1,1):
      for k in range(4):line(m,(0,top+h*.85,z),(s*(beam(.5+z/L)+.0),top+.5,z-.6+k*.4),.025)
    line(m,(0,top+h*.95,z),(0,top+.6,z+L*.22),.025)
    for s in (-1,1):
      for q in range(1,6):yq=top+.5+q*(h*.85-.5)/6;f=q/6;line(m,(s*(beam(.5+z/L))*(1-f),yq,z-.6*(1-f)),(s*(beam(.5+z/L))*(1-f),yq,z+.6*(1-f)),.015)
  line(m,(0,top+.6,L/2),(0,top+2.0,L/2+3.0 if large else L/2+2.0),.09,'bark',W(0x7a5a40),6)   # bowsprit
  m.quad(np.array([0,top+masts[0][1],masts[0][0]]),np.array([0,top+masts[0][1]-.6,masts[0][0]]),np.array([0,top+masts[0][1]-.4,masts[0][0]+1.4]),np.array([0,top+masts[0][1]-.1,masts[0][0]+1.4]),'cloth',W(0xb83a30))
  return m
def hob_tent2(col=0x6a4a38):
  m=M();cone(m,'cloth',2.9,4.2,6,col=W(col)*.75)
  for i in range(6):a=i/6*6.283+.52;line(m,(math.cos(a)*2.7,0,math.sin(a)*2.7),(math.cos(a)*-.3,4.9,math.sin(a)*-.3),.07,'bark',W(0x7a5a40),5)
  box(m,'wood',1.4,2.0,.05,R=rot('y',0),t=(0,0,2.45),col=W(0x3a2a20))
  return m
def hob_totem(seed=1):
  m=M();r=np.random.default_rng(seed);y=0
  for k in range(3):
    h=r.uniform(.9,1.2);cyl(m,'bark',.42,.38,h,8,t=(0,y,0),col=W([0x8a5a3a,0x6a4a30,0x9a3a2a][k]),cap=True);box(m,'wood',.5,.12,.1,t=(0,y+h*.55,.38),col=W(0x2a1a10),j=0);y+=h
  blob(m,'snow',.42,scale=(1,.9,1.1),sub=1,t=(0,y+.3,0),col=W(0xe0d8c0))
  for s in (-1,1):cone(m,'snow',.12,.8,5,R=rot('z',-s*1.0),t=(s*.3,y+.4,0),col=W(0xd8d0b8))
  for s in (-1,1):box(m,'cloth',.06,.9,.04,t=(s*.5,y-1.0,.0),col=W(0x9a2a20),j=0)
  return m
def hob_banner():
  m=M();cyl(m,'bark',.11,.14,4.6,6,col=W(0x7a5a40));m.quad(np.array([.1,4.3,0]),np.array([1.6,4.2,.1]),np.array([1.5,2.4,.15]),np.array([.1,2.3,0]),'cloth',W(0x9a2e2a));return m
def hob_rack():
  m=M()
  for s in (-1,1):cyl(m,'bark',.07,.07,1.6,5,t=(s*.9,0,0))
  cyl(m,'bark',.06,.06,2.0,5,R=rot('z',math.pi/2),t=(1.0,1.4,0))
  for i in range(4):line(m,(-.6+i*.4,0.05,.25),(-.6+i*.4,1.5,0),.04,'iron',W(0xa0a0a8),4)
  return m
