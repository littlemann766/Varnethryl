# Per-building hero pass: extra massing/ornament layered on top of the card2 builders (doors untouched).
import numpy as np, kit2
from kit2 import cyl, cone, barrel, pot_plant
from kit3 import tower, pinnacle
from bld4 import glancet, statue, rock, cb
from kit2 import crate
UP=np.array([0,1.0,0])
def temple(c):
    m=c['m']; X1=c['X1']; E=c['E']; Rh=c['Rh']; hs=c['hs']; t=np.array([0,0,-1.0]); n=np.array([1.0,0,0])
    m.remap=dict(c['m'].remap)
    for sz in(-1,1):
        z0,z1=sz*8.0,sz*11.0
        m.box((X1-8,0,min(z0,z1)),(X1,8.0,max(z0,z1)),'stone'); m.box((X1-8.1,7.9,min(z0,z1)-0.1),(X1+0.1,8.3,max(z0,z1)+0.1),'stone')
        glancet(m,(X1,1.6,sz*9.5),t,n,1.4,4.6); banner_strip=(X1+0.08,6.9,sz*9.5)
        for z in(z0,(z0+z1)/2,z1): pinnacle(m,(X1+0.05,8.3,z),2.2)
        for x in(X1-2.7,X1-5.4): pinnacle(m,(x,8.3,z1),1.8)
        m.box((X1,0,sz*11.0-0.5*sz-0.3),(X1+0.6,8.6,sz*11.0-0.5*sz+0.3),'stone')            # outer buttress
        tower(m,(X1-1.0,0,sz*12.3),1.35,11.0,6.5,wins=3)                                    # outer spire turrets
        tower(m,(X1-6.5,0,sz*12.0),1.1,9.0,5.0,wins=2)
        # big guardian statues on tall plinths in front of the aisles
        m.box((X1+1.8,0,sz*9.5-0.8),(X1+3.4,1.5,sz*9.5+0.8),'ashlar'); m.box((X1+1.7,1.5,sz*9.5-0.9),(X1+3.5,1.7,sz*9.5+0.9),'ashlar')
        statue(m,'robed',(X1+2.6,1.7,sz*9.5),2.3,90)
        for f in np.linspace(0.12,0.8,4):                                                    # crockets on the gable rake
            pinnacle(m,(X1+0.3,E+(Rh-E)*f,sz*hs*(1-f)),1.0,0.22)
        cb(m,(X1+0.1,7.5,sz*6.9),1.0,3.4,t=(0,0,-1),n=(1,0,0))
    return c
def mage_academy(c):
    m=c['m']; hs=c['hs']; t=np.array([1.0,0,0]); n=np.array([0,0,1.0])
    for sx in(-1,1):
        x0,x1=sx*8.1,sx*13.6
        m.box((min(x0,x1),0,-4.2),(max(x0,x1),9.0,4.2),'stone'); cone(m,((x0+x1)/2,0,0),4.4,9.0,3.4,'slate',4)
        for a in(sx*9.6,sx*12.1):
            glancet(m,(a,1.4,4.2),t,n,1.2,3.4); glancet(m,(a,5.2,4.2),t,n,1.1,2.8)
        tower(m,(sx*10.85,0,4.6),1.3,13.5,6.5,wins=3); tower(m,(sx*14.0,0,0.5),1.05,11.5,5.4,wins=2); tower(m,(sx*13.2,0,-4.0),1.1,12.5,5.8,wins=2)
        tower(m,(sx*8.6,0,-4.4),0.85,14.5,5.0,wins=2)
        for x in(x0,(x0+x1)/2,x1): pinnacle(m,(x,9.0,4.25),2.0,0.35)
        cb(m,(sx*10.85,10.5,4.6+1.35),0.9,3.2)
        # tall glowing blue lancets on the great towers so the blue reads in daylight
        for y in(9.0,12.5): glancet(m,(sx*5.2,y,hs+0.2+1.82),t,n,0.8,2.2)
    for y in(19.0,): glancet(m,(0,y,hs+0.4+2.62),t,n,0.9,2.2)
    return c
def keep(c):
    m=c['m']; R=13; t=np.array([1.0,0,0]); n=np.array([0,0,1.0])
    rng=np.random.default_rng(7); k=0
    m.remap={'rock':'stone'}                               # grey rocky base hugging the curtain wall (card: keep on a crag)
    for ring,(rr,sc,n_) in enumerate(((R+1.2,(3.6,5.0),28),(R+3.8,(2.4,3.6),34))):
        for i in range(n_):
            a=2*np.pi*(i+0.5*ring)/n_; d=np.array([np.cos(a),0,np.sin(a)]); p=d*(rr+rng.random()*1.0)/max(abs(np.cos(a)),abs(np.sin(a)))**0.35
            if p[2]>R-1 and abs(p[0])<6.0: continue          # keep the gate/steps clear
            rock(m,p-[0,0.9,0],rng.uniform(*sc),rng.uniform(0,360),seed=i%4,sy=rng.uniform(0.55,0.9))
    m.remap={}
    for sx in(-1,1):                                       # card massing: stepped secondary towers around the donjon
        tower(m,(sx*3.2,0,-4.0),1.5,21.0,5.5,wins=3,cone_r=1.9); tower(m,(sx*6.5,0,1.0),1.2,17.5,4.6,wins=2)
        tower(m,(sx*9.5,0,-9.0),1.6,13.5,5.0,wins=2)
    return c
def townhall(c):
    m=c['m']; t=np.array([1.0,0,0]); n=np.array([0,0,1.0]); zf=c['hs']+0.8
    hs=c['hs']; E=c['E']
    # flat card front: one symmetric screen wall, gold string courses, lion shield centre, banners on the flanking towers
    for s in(-1,1): m.box((min(s*2.72,s*6.0),0,hs-0.05),(max(s*2.72,s*6.0),E+0.4,hs+0.8),'ashlar',2.0)
    for y in(c['g'],E): m.beam((-6.0,y,hs+0.86),(6.0,y,hs+0.86),0.12,'gold')
    hs=hs+0.55
    for sx in(-1,1):
        cb(m,(sx*6.9,E+1.0,hs+0.4+1.55),1.1,4.4)
        for x in(sx*4.3,): glancet(m,(x,1.2,hs+0.25),t,n,0.9,2.4); glancet(m,(x,c['g']+0.6,hs+0.25),t,n,0.9,2.4); glancet(m,(x,c['g']+3.8,hs+0.25),t,n,0.9,2.2)
        pinnacle(m,(sx*6.0,E+0.4,hs+0.1),2.2)
    return c
def inn(c):
    m=c['m']; zf=c['D']/2+0.4+1.2
    for x in(-2.0,3.2): barrel(m,(x,0,zf+1.6),0.32,0.75); m.LOD=1; m.blob((x,0.85,zf+1.6),0.32,'flowers',6); m.LOD=99
    return c
SIGNSIZE=dict(inn=1.3,bakery=1.4,smithy=1.2,market=1.2,guildhall=1.3,townhall=1.1)
def market(c):
    m=c['m']; from kit3 import stall, awning; from kit2 import crate
    D=c['D']; z=D/2
    # crowded card front: striped awnings over every bay, a row of loaded stalls, sacks/crates/barrels/flowers (door at x=-1.8 kept clear)
    awning(m,-5.6,-4.0,c['g']-0.15,z+0.5,1.4,0.6,6)
    for x in(-5.0,3.4,5.4): stall(m,x,z+3.4,1.6)
    for x in(-4.6,-3.4,0.4,2.0,3.2,4.6):
        m.LOD=1; barrel(m,(x,0,z+1.0+0.3*(x%2)),0.28,0.7) if x<0.5 else crate(m,(x,0,z+1.2),0.55); m.LOD=99
    for x in(-5.6,0.0,1.0,5.8): pot_plant(m,(x,0,z+0.5),0.4)
    for x in(-5.3,4.0): m.box((x-0.5,0,z+4.4),(x+0.5,0.6,z+5.0),'oak'); m.blob((x,0.75,z+4.7),0.4,'flowers',6,0.6)
    return c
def smithy(c):
    m=c['m']; X1=c['X1']
    # weapon racks: swords with gold hilts, axes, round shields either side of the door
    for zz in(-2.4,2.3):
        for k in np.linspace(-0.5,0.5,4):
            b0=np.array([X1+0.45,0.15,zz+k]); m.beam(b0,b0+[0.05,1.25,0],0.05,'iron'); m.beam(b0+[0.05,1.25,-0.15],b0+[0.05,1.25,0.15],0.05,'gold'); m.beam(b0+[0.05,1.25,0],b0+[0.05,1.5,0],0.05,'beam')
        for k in(-0.4,0.4):
            p=np.array([X1+0.12,2.2,zz+k]); cyl(m,p,0.0,0,0,'iron',4) if False else None
            m.obox(p,(0,0,1),(0,1,0),(1,0,0),(0.55,0.55,0.06),'gold'); m.obox(p+[0.04,0,0],(0,0,1),(0,1,0),(1,0,0),(0.42,0.42,0.06),'beam')
        a=np.array([X1+0.7,0,zz+0.75]); m.beam(a,a+[0,1.3,0],0.05,'beam'); m.obox(a+[0,1.2,0.12],(0,0,1),(0,1,0),(1,0,0),(0.3,0.25,0.04),'iron')
    return c
APPLY=dict(market=market,smithy=smithy,temple=temple,mage_academy=mage_academy,keep=keep,townhall=townhall,inn=inn)
def apply(name,c):
    f=APPLY.get(name)
    if f:
        o=c['m'].LOD; f(c); c['m'].LOD=o
    return c
