# Max-detail dressing + street-prop kit (all on the shared card2 atlas). Everything here is LOD-tagged:
# small clutter -> LOD 1 (gone in Medium), mid props -> LOD 2 (gone in Low); export() then decimates to the ratio caps.
import numpy as np, kit2
from geo import Mesh, norm
from kit2 import cyl, cone, barrel, crate, pot_plant
UP=np.array([0,1.0,0])
def _R(rot):
    r=np.radians(rot); return np.array([[np.cos(r),0,np.sin(r)],[0,1,0],[-np.sin(r),0,np.cos(r)]])
def local(m,fn,pos,rot=0,*a,**k):
    t=Mesh(); t.remap=m.remap; fn(t,*a,**k); t.lod=[min(l,m.LOD) for l in t.lod] if m.LOD<99 else t.lod; m.merge(t,pos,rot)
# ---------- props (built at origin, +z front) ----------
def bench(m,L=1.8):
    m.box((-L/2,0.42,-0.22),(L/2,0.48,0.22),'oak'); m.box((-L/2,0.7,-0.24),(L/2,1.0,-0.19),'oak')
    for s in(-1,1): m.box((s*(L/2-0.15)-0.05,0,-0.2),(s*(L/2-0.15)+0.05,0.42,0.2),'beam'); m.box((s*(L/2-0.15)-0.04,0.42,-0.24),(s*(L/2-0.15)+0.04,1.0,-0.19),'beam')
def cart(m,L=2.4,load=True):
    m.box((-L/2,0.65,-0.6),(L/2,0.75,0.6),'oak')
    for s in(-1,1): m.box((-L/2,0.75,s*0.6-0.04),(L/2,1.15,s*0.6+0.04),'oak'); m.box((s*L/2-0.04,0.75,-0.6),(s*L/2+0.04,1.15,0.6),'oak')
    for s in(-1,1):
        cyl(m,(0.2,0,0),0.0,0,0,'iron',6) if False else None
        c=np.array([0.2,0.5,s*0.72]); seg=12 if kit2.Q==0 else 8
        for i in range(seg):
            a0,a1=2*np.pi*i/seg,2*np.pi*(i+1)/seg
            m.beam(c+[0.5*np.cos(a0),0.5*np.sin(a0),0],c+[0.5*np.cos(a1),0.5*np.sin(a1),0],0.07,'beam')
        for i in range(4): a=np.pi*i/4; m.beam(c-[0.45*np.cos(a),0.45*np.sin(a),0],c+[0.45*np.cos(a),0.45*np.sin(a),0],0.05,'beam')
    m.beam((0.2,0.5,-0.8),(0.2,0.5,0.8),0.07,'iron')
    for s in(-1,1): m.beam((L/2,0.7,s*0.45),(L/2+1.4,0.45,s*0.35),0.07,'beam')
    if load:
        for x in(-0.6,0.3): sack(m,(x,0.75,-0.2)); 
        barrel(m,(-0.1,0.75,0.25),0.3,0.7)
def sack(m,c,r=0.28):
    c=np.asarray(c,float); m.blob(c+[0,r*0.75,0],r,'flowers',6,0.75) if False else cyl(m,c,r,0,r*1.6,'plaster',7,cap='plaster',r1=r*0.7)
def planter(m,L=1.2):
    m.box((-L/2,0,-0.3),(L/2,0.5,0.3),'oak'); m.box((-L/2-0.04,0.45,-0.34),(L/2+0.04,0.52,0.34),'beam')
    for k in np.linspace(-L/2+0.2,L/2-0.2,4): m.blob((k,0.62,0),0.24,'flowers',6)
def crate_stack(m):
    crate(m,(0,0,0),0.75); crate(m,(0.8,0,0.05),0.7); crate(m,(0.35,0.75,0.0),0.6)
def barrel_group(m):
    barrel(m,(0,0,0)); barrel(m,(0.8,0,0.2)); barrel(m,(0.35,0,-0.6),0.34,0.85)
def hay_bale(m):
    m.box((-0.6,0,-0.4),(0.6,0.75,0.4),'plaster',0.7)
    for x in(-0.3,0.3): m.box((x-0.03,-0.01,-0.42),(x+0.03,0.77,0.42),'beam')
def lantern_head(m,c):
    c=np.asarray(c,float); m.obox(c+[0,0.22,0],(1,0,0),UP,(0,0,1),(0.3,0.05,0.3),'iron'); m.obox(c-[0,0.2,0],(1,0,0),UP,(0,0,1),(0.26,0.05,0.26),'iron')
    cone(m,c+[0,0.24,0],0.2,0,0.25,'iron',4) if kit2.Q<2 else None
    for (t,n) in(((1,0,0),(0,0,1)),((0,0,1),(1,0,0))):
        t=np.array(t,float); n=np.array(n,float)
        for s in(1,-1):
            f=c+n*s*0.12; m.cell([f-t*s*0.11-UP*0.18,f+t*s*0.11-UP*0.18,f+t*s*0.11+UP*0.18,f-t*s*0.11+UP*0.18],'window',0.1,0.4,0.55,0.95)
def wall_lantern(m,p,n):
    p=np.asarray(p,float); n=norm(n); q=p+n*0.45
    m.beam(p,q+UP*0.15,0.05,'iron'); m.beam(p-UP*0.3,q,0.04,'iron'); lantern_head(m,q-UP*0.25)
def lantern_post(m,h=3.2):
    m.box((-0.25,0,-0.25),(0.25,0.3,0.25),'stone'); cyl(m,(0,0,0),0.08,0.3,h,'iron',8)
    m.beam((0,h-0.1,0),(0.6,h,0),0.06,'iron'); m.beam((0,h-0.6,0),(0.55,h-0.05,0),0.04,'iron'); lantern_head(m,(0.6,h-0.35,0))
    for k in range(3): cyl(m,(0,0,0),0.12,0.3+k*0.02+0.6*k,0.3+0.6*k+0.1,'iron',8)
def hanging_sign(m,p,n,cellname,w=0.9,h=0.9):
    """bracket sign hanging off a wall point p with outward normal n"""
    from geo import Mesh as _M
    p=np.asarray(p,float); n=norm(n); t=np.cross(UP,n); L=1.3
    m.beam(p,p+n*L,0.07,'iron'); m.beam(p-UP*0.6,p+n*L*0.7,0.05,'iron'); m.obox(p+n*L,t,UP,n,(0.1,0.1,0.1),'gold')
    for k in range(4 if kit2.Q==0 else 0): a=k*np.pi/2; m.beam(p+n*0.3+UP*0.05,p+n*(0.3+0.2*np.cos(a))+UP*(0.05+0.2*np.sin(a)),0.025,'iron')  # scroll
    bc=p+n*(L*0.6)-UP*(0.25+h/2)
    for s in(-1,1): m.beam(p+n*(L*0.6+s*w*0.35),bc+n*s*w*0.35+UP*h/2,0.02,'iron')
    for s in(1,-1):
        f=bc+t*s*0.04; tt=n*s; m.cell([f-tt*w/2-UP*h/2,f+tt*w/2-UP*h/2,f+tt*w/2+UP*h/2,f-tt*w/2+UP*h/2],cellname)
    m.obox(bc,n,UP,t,(w+0.08,h+0.08,0.06),'beam')
def well(m):
    cyl(m,(0,0,0),1.0,0,0.9,'stone',14,cap=None); cyl(m,(0,0,0),0.8,0.0,0.92,'stone',14); cyl(m,(0,0.9,0),1.05,0,0.12,'stone',14,r1=1.05)
    m.cell([np.array([0,0.5,0]),np.array([0,0.5,0]),np.array([0.78,0.5,0]),np.array([0,0.5,0.78])],'water',0.1,0.2,0.2,0.8)
    for s in(-1,1): m.box((s*0.95-0.08,0.9,-0.08),(s*0.95+0.08,2.6,0.08),'beam')
    m.beam((-1.1,2.5,0),(1.1,2.5,0),0.14,'beam'); cyl(m,(0,1.95,0),0.0,0,0,'iron',6) if False else None
    for s in(-1,1): m.poly([(-1.4,2.4,s*1.0),(1.4,2.4,s*1.0),(1.4,3.2,0),(-1.4,3.2,0)][::(1 if s>0 else -1)],(-1.4,2.4,s*1.0),(s,0,0),(0,0.8,-s*1.0),'slate')
    m.beam((0.2,2.5,0),(0.2,1.5,0),0.02,'iron'); cyl(m,(0.2,1.2,0),0.18,0,0.3,'oak',8,cap='oak')
    m.beam((1.1,2.5,0),(1.35,2.2,0),0.04,'iron')
def fence(m,L=4.0,h=1.1):
    k=max(1,int(L/2))
    for i in range(k+1): x=-L/2+L*i/k; m.box((x-0.07,0,-0.07),(x+0.07,h,0.07),'beam'); m.obox((x,h+0.03,0),(1,0,0),UP,(0,0,1),(0.18,0.06,0.18),'beam')
    for y in(h*0.4,h*0.82): m.box((-L/2,y-0.05,-0.03),(L/2,y+0.05,0.03),'oak')
def signpost(m):
    m.box((-0.3,0,-0.3),(0.3,0.25,0.3),'stone'); m.box((-0.07,0.25,-0.07),(0.07,2.8,0.07),'beam')
    for y,rot,dx in((2.4,0,1),(2.0,35,-1),(1.6,-25,1)):
        r=np.radians(rot); d=np.array([np.cos(r),0,np.sin(r)])*dx; t2=np.cross(UP,d)
        c=d*0.55+UP*y; m.obox(c,d,UP,t2,(1.1,0.26,0.05),'oak'); m.poly([c+d*0.55+UP*0.13+t2*0.03,c+d*0.75+t2*0.03,c+d*0.55-UP*0.13+t2*0.03],c,d,UP,'oak')
    cone(m,(0,0,0),0.12,2.8,0.2,'slate',4)
def cobble_edge(m,L=4.0):
    k=int(L/0.5)
    for i in range(k): x=-L/2+i*0.5+0.25; m.obox((x,0.08,0),(1,0,0),UP,(0,0,1),(0.46,0.18+0.03*((i*7)%3),0.32),'stone',i*0.37)
def ivy_strand(m,top,n,L=2.5):
    top=np.asarray(top,float); n=norm(n); k=max(3,int(L/0.35))
    for i in range(k): m.blob(top-UP*(i*L/k)+n*0.12+np.cross(UP,n)*0.12*np.sin(i*1.7),0.2*(1-0.4*i/k),'flowers',5,0.8)
def moss(m,c,r=0.35):
    m.blob(np.asarray(c,float),r,'flowers',6,0.25)
PROPS=dict(lantern_post=lantern_post,market_cart=cart,well=well,bench=bench,hay_bale=hay_bale,fence=fence,signpost=signpost,flower_planter=planter,cobble_edge=cobble_edge,crate_stack=crate_stack,barrel_group=barrel_group)
# ---------- dressing pass ----------
SIGN=dict(inn='sign_inn',bakery='sign_bread',smithy='sign_anvil',apothecary='sign_potion',market='sign_potion',library='sign_book',mage_academy='sign_book',
          observatory='sign_book',training_hall='sign_sword',treasury='sign_sword',guildhall='sign_sword',thieves_den='sign_potion',townhall='sign_book',
          house1='sign_bread',house4='sign_inn')
CLUT=dict(inn='bbcpPb',bakery='sbpPc',smithy='bxcxb',apothecary='pPbp',market='cbxsPx',guildhall='bPpbx',townhall='PbPbP',temple='PbPbP',mage_academy='PpPbx',
          keep='xcbxh',library='PbPbp',house1='pbx',house2='pbP',house3='pbxs',house4='pPb',training_hall='xbh',treasury='xbx',thieves_den='bxsx',
          windmill='shhc',observatory='Pb',crypt='p',gatehouse='cx',port='',fountain='bPbP',colosseum='cbxPc',wall_segment='',watchtower='x',walls_demo='')
def dress(name,m,front_gable):
    rng=np.random.default_rng(sum(map(ord,name)))
    P=np.array(m.P).reshape(-1,3); lo=P.min(0); hi=P.max(0)
    ax,lat=(0,2) if front_gable else (2,0)          # front axis (+), lateral axis
    sgn=-1 if front_gable else 1                      # lateral direction that is 'right' after export rotation
    nF=np.zeros(3); nF[ax]=1
    doors=[d for d in getattr(m,'doors',[]) if d[ax]>hi[ax]-3.5]
    def free(a,r=1.4): return all(abs(a-d[lat])>r+1.0 for d in doors)
    def at(a,off,rot_extra=0): p=np.zeros(3); p[ax]=hi[ax]+off; p[lat]=a; return p
    rot_front=0 if not front_gable else 90
    o=m.LOD
    # front clutter
    seq=CLUT.get(name,'pb'); span=np.linspace(lo[lat]+1.0,hi[lat]-1.0,max(2,len(seq)+2))[1:-1]
    fn=dict(b=barrel_group,x=crate_stack,c=cart,p=planter,P=lambda mm: pot_plant(mm,(0,0,0),0.45),s=bench,h=hay_bale)
    for ch,a in zip(seq,span):
        if not free(a): continue
        m.LOD=2 if ch in'cs' else 1
        local(m,fn[ch],at(a,0.9+0.5*rng.random()),rot_front+rng.uniform(-12,12))
    # wall lanterns + specific hanging sign beside the main door
    if doors and name not in('port','fountain','colosseum','walls_demo','wall_segment'):
        d=max(doors,key=lambda d:d[ax])
        m.LOD=1
        for s in(-1,1):
            p=d.copy(); p[ax]+=0.05; p[lat]+=s*1.6; p[1]=2.7; wall_lantern(m,p,nF)
        if name in SIGN:
            p=d.copy(); p[ax]+=0.05; p[lat]+=2.8 if free(d[lat]+2.8,0.3) else -2.8; p[1]=3.3; m.LOD=2; hanging_sign(m,p,nF,SIGN[name])
    # hanging ivy on the side walls + moss tufts at the base (weathering)
    m.LOD=1
    if name not in('port','fountain','colosseum','crypt','observatory','windmill'):
        for s_ in(-1,1):
            for k in range(3):
                p=np.zeros(3); p[lat]=hi[lat] if s_>0 else lo[lat]; p[lat]-=s_*0.15; p[ax]=lo[ax]+(hi[ax]-lo[ax])*rng.uniform(0.2,0.8); p[1]=min(hi[1]-1,3.4+rng.random()*2)
                nn=np.zeros(3); nn[lat]=s_; ivy_strand(m,p,nn,rng.uniform(1.5,3.0))
        for k in range(6):
            p=np.zeros(3); p[ax]=lo[ax]+(hi[ax]-lo[ax])*rng.random(); s_=rng.choice([-1,1]); p[lat]=(hi[lat] if s_>0 else lo[lat])+s_*0.1; p[1]=0.05; moss(m,p,rng.uniform(0.25,0.45))
    m.LOD=o
