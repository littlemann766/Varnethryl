import sys,os,json,math,numpy as np
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
import kit
W=lambda h:hexc(h)
LEAFC={'green':W(0x6cb04c),'deep':W(0x3f8044),'autumn':W(0xe88a34),'lime':W(0xa8cc4a),'blossom':W(0xf0b0c8),'yellow':W(0xe8c838),'red':W(0xd04838)}
def trunk(m,h,r0,col=W(0xffffff),tile='bark',seg=7,bend=(0,0)):cyl(m,tile,r0,r0*.6,h,seg,col=col,bend=bend)
def canopy(m,c,rad,col,n_cards=6,blobs=3,sub=1,seed=0):
  r=np.random.default_rng(seed)
  for i in range(blobs):
    o=np.array(c)+r.uniform(-.45,.45,3)*rad*np.array([1,.5,1])
    blob(m,'leaf',rad*r.uniform(.6,.8),scale=(1,.8,1),sub=0,jit=.22,t=o,col=col*0.95,uvs=2.0,seed=int(r.integers(1e6)))
  for i in range(n_cards):
    a=r.uniform(0,6.28);o=np.array(c)+np.array([math.cos(a),r.uniform(-.3,.4),math.sin(a)])*rad*.55
    cards(m,'leaf',rad*1.25,rad*1.25,1,t=o-np.array([0,rad*.62,0]),col=col,yaw=a+1.57,tilt=r.uniform(-.4,.4))
def oak(seed,lod=0,pal='green'):
  m=M();r=np.random.default_rng(seed);h=r.uniform(2.6,3.2);trunk(m,h,.28,bend=(r.uniform(-.3,.3),r.uniform(-.3,.3)),seg=7 if not lod else 5)
  for k in range(0 if lod else 2):
    a=r.uniform(0,6.28);cyl(m,'bark',.12,.06,1.6,5,R=rot('y',a)@rot('z',.9),t=(0,h*.7,0))
  canopy(m,(0,h+1.3,0),2.0,LEAFC[pal],n_cards=12 if not lod else 5,blobs=4 if not lod else 2,sub=1,seed=seed);return m
def pine(seed,lod=0,snowy=False):
  m=M();r=np.random.default_rng(seed);H=r.uniform(6,7.5);trunk(m,H*.35,.22,seg=6 if not lod else 4)
  tiers=4 if not lod else 2
  for i in range(tiers):
    y=H*(.18+.8*i/tiers);rad=(1.9-1.35*i/tiers)*r.uniform(.9,1.1);th=H*.42
    cone(m,'pinecard',rad*.78,th,8 if not lod else 5,t=(0,y,0),col=W(0xa0c0a8))
    cards(m,'pinecard',rad*2.1,th*1.05,3 if not lod else 2,t=(0,y-.1,0),col=W(0xffffff),yaw=r.uniform(0,3))
    if snowy:cone(m,'snow',rad*.7,th*.55,7 if not lod else 5,t=(0,y+th*.42,0),col=W(0xffffff))
  return m
def birch(seed,lod=0):
  m=M();r=np.random.default_rng(seed);h=r.uniform(3.6,4.4);trunk(m,h,.16,tile='snow',col=W(0xd8d4cc),seg=6,bend=(r.uniform(-.4,.4),0))
  for k in range(6):  # dark birch marks as tiny quads
    y=r.uniform(.4,h*.9);a=r.uniform(0,6.28);n=np.array([math.cos(a),0,math.sin(a)])*0.165;tg=np.array([-math.sin(a),0,math.cos(a)])*.07
    p=np.array([0,y,0])+n;m.quad(p-tg,p+tg,p+tg+[0,.05,0],p-tg+[0,.05,0],'iron',W(0x666666))
  canopy(m,(0,h+1.1,0),1.85,LEAFC['lime'],n_cards=7 if not lod else 3,blobs=3 if not lod else 1,seed=seed);return m
def dead(seed,lod=0):
  m=M();r=np.random.default_rng(seed);h=r.uniform(3.4,4.2);trunk(m,h,.26,col=W(0xb8b0a4),seg=6,bend=(.3,-.2))
  for k in range(5 if not lod else 2):
    a=r.uniform(0,6.28);y=r.uniform(h*.45,h*.9);cyl(m,'bark',.09,.02,r.uniform(1,1.8),4,R=rot('y',a)@rot('z',r.uniform(.6,1.1)),t=(0,y,0),col=W(0xb8b0a4))
  return m
def billboard(kind,h,w):
  # 3 crossed planes with rounded (spherical) normals so the impostor shades like a volume, not a flat card
  m=M();c=np.array([0,h*.55,0])
  for i in range(3):
    a=math.pi*i/3;R=rot('y',a);pts=[R@np.array(v) for v in [(-w/2,0,0),(w/2,0,0),(w/2,h,0),(-w/2,h,0)]]
    uv=[tile_uv('imp_'+kind,*q) for q in [(0,1),(1,1),(1,0),(0,0)]]
    nn=[]
    for p in pts:v=p-c;v[1]*=.6;v=v/np.linalg.norm(v)+np.array([0,.35,0]);nn.append(v/np.linalg.norm(v))
    m.tri([pts[0],pts[1],pts[2]],[uv[0],uv[1],uv[2]],W(0xffffff),n=[nn[0],nn[1],nn[2]]);m.tri([pts[0],pts[2],pts[3]],[uv[0],uv[2],uv[3]],W(0xffffff),n=[nn[0],nn[2],nn[3]])
  return m
def bush(seed,pal='green'):
  m=M();r=np.random.default_rng(seed);blob(m,'leaf',.75,scale=(1.2,.8,1),sub=1,t=(0,.5,0),col=LEAFC[pal]*.8,uvs=2,seed=seed)
  for i in range(4):
    a=i*1.57+r.uniform(0,.6);cards(m,'leaf',1.2,1.2,1,t=(math.cos(a)*.4,-.05,math.sin(a)*.4),col=LEAFC[pal],yaw=a+1.57)
  return m
def grass(seed,col=0xffffff,h=.7):
  m=M();cards(m,'grass',1.0,h,3,col=W(col),yaw=np.random.default_rng(seed).uniform(0,3));return m
def flowers(seed,col):
  m=M();r=np.random.default_rng(seed);cards(m,'grass',1.0,.55,2,col=W(0xffffff),yaw=.4);cards(m,'flower',.9,.6,2,col=.45+.55*W(col),yaw=r.uniform(0,3));return m
def rock(seed,size=1,kind='rock',col=0xffffff,sub=1,sq=(1.2,.75,1),top=None):
  m=M();blob(m,kind,size,scale=sq,sub=sub,jit=.28,t=(0,size*sq[1]*.55,0),col=W(col),flat_bottom=-size*sq[1]*.9,seed=seed,top=top);return m
def cliff(seed,kind='rock',col=0xffffff,top=0x9ab08a):
  m=M();r=np.random.default_rng(seed)
  for i in range(5):
    s=r.uniform(1.6,2.6);blob(m,kind,s,scale=(1.1,r.uniform(1.6,2.4),.9),sub=1,jit=.22,t=(r.uniform(-3,3),s*1.1,r.uniform(-1,1)),col=W(col),flat_bottom=-1.2*s,seed=int(r.integers(1e6)),top=W(top) if top else None)
  for i in range(4):
    s=r.uniform(.5,.9);blob(m,kind,s,scale=(1.2,.7,1),sub=1,t=(r.uniform(-4,4),s*.3,r.uniform(1,2.4)),col=W(col),seed=int(r.integers(1e6)))
  return m
# ---- props ----
def fence(seed=0):
  m=M()
  for x in (-1,1):box(m,'wood',.14,1.2,.14,t=(x*1.0,0,0))
  for y in (.45,.9):box(m,'wood',2.2,.1,.06,t=(0,y,0),R=rot('z',np.random.default_rng(seed+int(y*10)).uniform(-.03,.03)))
  return m
def crate():
  m=M();box(m,'wood',.9,.9,.9)
  for s in (-1,1):box(m,'wood',.95,.08,.08,t=(0,.86*(s>0)+.0,.45*s),col=W(0x9a7a5a));box(m,'wood',.08,.08,.95,t=(.45*s,.86,0),col=W(0x9a7a5a))
  return m
def barrel():
  m=M();cyl(m,'wood',.38,.42,.5,12,col=W(0xd8c0a0),j=.12);cyl(m,'wood',.42,.38,.5,12,t=(0,.5,0),col=W(0xd8c0a0),cap=True,j=.12)
  for y in (.1,.5,.88):cyl(m,'iron',.43,.43,.06,12,t=(0,y,0))
  return m
def cart():
  m=M();box(m,'wood',1.4,.12,2.2,t=(0,.7,0))
  for s in (-1,1):box(m,'wood',.08,.4,2.2,t=(.68*s,.82,0));box(m,'wood',1.4,.4,.08,t=(0,.82,1.06*s))
  for s in (-1,1):
    cyl(m,'wood',.5,.5,.1,12,R=rot('z',1.5708),t=(.8*s+(.1 if s<0 else 0),.5,-.2),cap=True,col=W(0xc0a080))
  for s in (-1,1):box(m,'wood',.08,.08,1.6,t=(.35*s,.62,1.9))
  box(m,'wood',.1,.1,1.6,t=(0,.5,-.2),R=rot('z',1.5708)@rot('y',1.5708)*1)
  return m
def lamppost():
  m=M();box(m,'cobble',.5,.25,.5);cyl(m,'iron',.07,.06,3.0,8,t=(0,.25,0));box(m,'iron',.6,.06,.06,t=(.25,3.05,0))
  box(m,'cloth',.3,.38,.3,t=(.5,2.62,0),col=W(0xfff0b0));cone(m,'iron',.24,.18,4,R=rot('y',.785),t=(.5,3.0,0));return m
def tent(col=0xa08868):
  m=M();cone(m,'cloth',1.8,2.6,8,col=W(col));cyl(m,'wood',.05,.04,3.0,4,col=W(0xffffff));return m
def palisade(n=5):
  m=M()
  for i in range(n):cyl(m,'bark',.16,.16,2.2,6,t=(i*.34-n*.17,0,0));cone(m,'wood',.16,.4,6,t=(i*.34-n*.17,2.2,0))
  box(m,'wood',n*.34,.1,.1,t=(0,1.4,.14));return m
def firepit():
  m=M()
  for i in range(8):a=i*.785;blob(m,'rock',.22,sub=0,t=(math.cos(a)*.6,.1,math.sin(a)*.6),col=W(0x908880))
  for i in range(3):cyl(m,'bark',.07,.07,1.0,5,R=rot('y',i*2.1)@rot('z',1.2),t=(0,.05,0),col=W(0x403020))
  blob(m,'lavacrust',.32,scale=(1,.2,1),sub=0,t=(0,.03,0));return m
def dock(length=10,width=4):
  m=M()
  for i in range(int(length/0.5)):box(m,'wood',width,.08,.46,t=(0,1.0,-length/2+i*.5+.25),col=W(0xd0b8a0)*(0.9+0.1*(i%3)))
  for z in np.linspace(-length/2+.2,length/2-.2,4):
    for s in (-1,1):cyl(m,'bark',.15,.15,2.6,6,t=(s*(width/2-.1),-1.5,z))
  return m
def ship():
  m=M();L=14;Wd=2.4;Hh=2.2;n=10
  def prof(t):return math.sin(math.pi*min(max(t,0),1))**.6
  secs=[]
  for i in range(n+1):
    t=i/n;z=-L/2+t*L;w=Wd*max(prof(t),.06);secs.append([np.array([-w,Hh,z]),np.array([-w*.8,Hh*.45,z]),np.array([0,0,z]),np.array([w*.8,Hh*.45,z]),np.array([w,Hh,z])])
  for i in range(n):
    for k in range(4):m.quad(secs[i][k],secs[i+1][k],secs[i+1][k+1],secs[i][k+1],'wood',W(0xb08060),(0,0,1,1))
  for i in range(n):m.quad(secs[i][0],secs[i][4],secs[i+1][4],secs[i+1][0],'wood',W(0xe0c8a8))
  cyl(m,'bark',.18,.12,11,8,t=(0,Hh,0.5));box(m,'wood',.12,.12,5,R=rot('y',1.57),t=(0,Hh+7.5,.5))
  m.quad(np.array([-2.4,Hh+7.4,.6]),np.array([2.4,Hh+7.4,.6]),np.array([2.6,Hh+2.6,.9]),np.array([-2.6,Hh+2.6,.9]),'cloth',W(0xffffff))
  box(m,'wood',3.4,1.0,3,t=(0,Hh-.1,-L/2+2.2),col=W(0x9a7050));return m
def ruin_wall(seed):
  m=M();r=np.random.default_rng(seed)
  for i in range(6):
    hh=r.uniform(.8,3.2);box(m,'cobble',1.0,hh,.8,t=(i*1.0-2.5,0,0),col=W(0xd8d0c0)*r.uniform(.85,1.05))
  for i in range(6):blob(m,'cobble',r.uniform(.25,.5),sub=0,t=(r.uniform(-3,3),.15,r.uniform(.6,1.8)),col=W(0xc8c0b0))
  return m
def ruin_arch():
  m=M()
  for s in (-1,1):box(m,'cobble',.9,3.4,.9,t=(s*1.25,0,0),col=W(0xd8d0c0))
  box(m,'cobble',3.4,.6,.9,t=(.2,3.4,0),R=rot('z',-.05),col=W(0xc8c0b0));return m  # 1.6 m x 3.4 m opening
def path_stones(seed,n=9):
  m=M();r=np.random.default_rng(seed)
  for i in range(n):
    z=i*.9-n*.45;x=math.sin(i*.6)*.6+r.uniform(-.2,.2)
    blob(m,'cobble',r.uniform(.32,.45),scale=(1.2,.12,1),sub=0,jit=.15,t=(x,.0,z),col=W(0xe0d8c8))
  return m
