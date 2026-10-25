# Per-building hero pass: extra massing/ornament layered on top of the card2 builders (doors untouched).
import numpy as np, kit2
from bld4 import CREAM
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
    D=c['D']; z=D/2; g=c['g']; E=c['E']; zf=D/2+0.45+0.5
    # shop front: two-level striped awnings across the whole front
    awning(m,-5.6,-4.1,g-0.15,z+0.05,1.5,0.6,6)
    awning(m,-4.1,0.5,E-0.25,zf+0.05,1.1,0.45,8); awning(m,1.2,5.4,E-0.25,z+0.5,1.1,0.45,8); awning(m,-5.6,-4.1,E-0.25,z+0.5,1.1,0.45,6)
    # full-width tiered display shelves loaded with goods (door bay x=-2.55..-1.05 left clear)
    rng=np.random.default_rng(3)
    for x0,x1,zz in((-5.6,-2.9,z+0.1),(-0.7,0.4,zf+0.05),(1.1,5.5,z+0.1)):
        for k,(y,dz) in enumerate(((0.55,1.15),(0.95,0.8),(1.35,0.45))):
            m.box((x0,y-0.06,zz+dz-0.2),(x1,y,zz+dz+0.2),'oak')
            for xx in np.arange(x0+0.2,x1-0.1,0.38):
                r=rng.random(); p=(xx,y,zz+dz)
                if r<0.3: m.blob((xx,y+0.2,zz+dz),0.26,'flowers',6,0.8)                                   # fruit / flowers heap
                elif r<0.5:                                                                               # cloth bolts (gold / blue / red-oak)
                    for j,st in enumerate(('gold','bluestone','oak')): m.beam((xx-0.17,y+0.1+0.15*j,zz+dz),(xx+0.17,y+0.1+0.15*j,zz+dz),0.14,st)
                elif r<0.75: cyl(m,p,0.17,0,0.42,'oak',8,cap='beam',r1=0.1); m.blob((xx,y+0.48,zz+dz),0.12,'flowers',5)   # pottery with posies
                else: crate(m,(xx,y,zz+dz),0.34); m.blob((xx,y+0.4,zz+dz),0.2,'flowers',5,0.6)
        for xe in(x0,x1): m.box((xe-0.05,0,zz+0.3),(xe+0.05,1.4,zz+1.4),'beam')
    # hanging goods, baskets and flower garlands along both awning edges
    for (x0,x1,yy,zz) in((-5.6,-4.1,g-0.75,z+1.55),(-4.1,0.5,E-0.7,zf+1.15),(1.2,5.4,E-0.7,z+1.6),(1.2,5.3,g-0.75,z+1.65)):
        for xx in np.arange(x0+0.25,x1,0.5): m.LOD=1; m.blob((xx,yy,zz),0.14,'flowers',5,1.0); m.LOD=99
        for xx in np.arange(x0+0.5,x1-0.2,1.1):
            m.beam((xx,yy+0.1,zz),(xx,yy-0.4,zz),0.02,'iron'); cyl(m,(xx,yy-0.75,zz),0.2,0,0.35,'oak',8,cap='oak',r1=0.24); m.blob((xx,yy-0.38,zz),0.17,'flowers',5,0.7)
    # crowded street front
    for x in(-5.0,3.0,5.2): stall(m,x,z+3.5,1.7)
    for x in(-4.6,0.9,2.4,4.2): m.LOD=1; barrel(m,(x,0,z+2.2),0.3,0.75); m.LOD=99
    for x in(-3.6,1.7,3.4): crate(m,(x,0,z+2.4),0.55); crate(m,(x+0.1,0.55,z+2.4),0.45)
    for x in(-5.8,0.2,5.8): pot_plant(m,(x,0,z+1.8),0.4)
    for x in(-3.8,4.4): m.box((x-0.5,0,z+4.6),(x+0.5,0.6,z+5.2),'oak'); m.blob((x,0.75,z+4.9),0.4,'flowers',6,0.6)
    return c
def bakery(c):
    m=c['m']; g=c['g']; hs=c['D']/2+0.35; zf=hs; n=np.array([0,0,1.0]); t=np.array([1.0,0,0])
    # card-size bread sign hanging face-on to the street from a scrolled iron bracket
    p=np.array([-3.9,g+1.9,hs]); a=p+n*1.4
    m.beam(p,a,0.07,'iron'); m.beam(p-UP*0.8,a-UP*0.05,0.05,'iron'); m.obox(a,t,UP,n,(0.12,0.12,0.12),'gold')
    for s in(-1,1): m.beam(a+t*s*0.75-UP*0.0,a+t*s*0.75-UP*0.35,0.025,'iron')
    m.beam(a-t*0.95,a+t*0.95,0.05,'iron')
    bc=a-UP*1.45
    m.obox(bc,t,UP,n,(2.05,2.15,0.1),'gold')
    for s in(1,-1):
        f=bc+n*s*0.06; tt=t*s
        m.cell([f-tt*0.9-UP*0.95,f+tt*0.9-UP*0.95,f+tt*0.9+UP*0.95,f-tt*0.9+UP*0.95],'sign_bread')
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
def library(c):
    m=c['m']; zf=c['hs']+1.2
    for s in(-1,1):   # card: robed statues flanking the gold portal
        m.box((s*2.1-0.6,0,zf+1.0),(s*2.1+0.6,1.3,zf+2.2),'ashlar'); statue(m,'robed',(s*2.1,1.3,zf+1.6),1.9,0)
    return c
def observatory(c):
    m=c['m']; m.remap={'rock':'stone'}; rng=np.random.default_rng(5)
    for i in range(14):  # taller crag the tower stands on
        a=2*np.pi*i/14; r=5.5+rng.random()*2.5; rock(m,(r*np.cos(a),-0.5,r*np.sin(a)),rng.uniform(3.5,5.0),rng.uniform(0,360),seed=i%4,sy=rng.uniform(0.8,1.2))
    m.remap=dict(CREAM)
    return c
def crypt(c):
    m=c['m']; X1=c['X1']; from detail import lantern_post, local
    from kit3 import steps as _st
    for k in range(4): m.box((X1+0.4+k*0.45,0,-1.9-k*0.3),(X1+0.85+k*0.45,0.75-k*0.18,1.9+k*0.3),'stone',k*0.3)   # wide worn stairs
    for s in(-1,1): local(m,lantern_post,(X1+2.4,0,s*2.9),180)
    for s in(-1,1):
        for k in range(3): rock(m,(X1+0.9+k*1.2,-0.3,s*(3.6+0.5*k)),1.3,k*70,seed=k)
    return c
def thieves_den(c):
    m=c['m']; X1=c['X1']; from detail import lantern_post, local
    for s in(-1,1): local(m,lantern_post,(X1+1.6,0,0.5+s*2.0),180)
    p=np.array([X1+0.12,c['g']-0.1,0.0]); m.obox(p,(0,0,-1),(0,1,0),(1,0,0),(4.6,0.9,0.12),'beam'); m.cell([p+[0.08,-0.35,2.1],p+[0.08,-0.35,-2.1],p+[0.08,0.35,-2.1],p+[0.08,0.35,2.1]],'sign_potion',0.05,0.95,0.42,0.58)
    return c
def apothecary(c):
    m=c['m']; z=c['D']/2+0.35+0.3; g=c['g']; from kit2 import leaf
    for x in np.arange(-3.7,3.8,0.55):   # card: drying-herb bunches hanging along the whole front
        if abs(x-0.6)<0.75: continue
        m.beam((x,g-0.2,z),(x,g-0.6,z),0.015,'beam')
        for k in range(5 if kit2.Q==0 else 2): leaf(m,(x+0.08*np.sin(k*2.1),g-0.65-0.12*k,z+0.05),(0.3*np.cos(k*2.1),-0.2,1),0.16,k*0.9)
    p=np.array([0,g+0.15,c['hs']+0.35+0.12]); m.obox(p,(1,0,0),(0,1,0),(0,0,1),(4.0,0.95,0.1),'beam')
    m.cell([p+[-1.85,-0.4,0.06],p+[1.85,-0.4,0.06],p+[1.85,0.4,0.06],p+[-1.85,0.4,0.06]],'sign_potion',0.05,0.95,0.42,0.58)
    return c
def house_banner(c):
    m=c['m']; X1=c['X1']; g=c['g']
    p=np.array([X1+0.12,g+1.4,-c['D']/2+0.9]); m.obox(p,(0,0,-1),(0,1,0),(1,0,0),(1.25,2.7,0.06),'gold')   # big lion banner like the card
    m.cell([p+[0.05,-1.25,0.55],p+[0.05,-1.25,-0.55],p+[0.05,1.25,-0.55],p+[0.05,1.25,0.55]],'banner',0.08,0.92,0.12,0.86)
    return c
APPLY=dict(library=library,observatory=observatory,crypt=crypt,thieves_den=thieves_den,apothecary=apothecary,house1=house_banner,house2=house_banner,house4=house_banner,bakery=bakery,market=market,smithy=smithy,temple=temple,mage_academy=mage_academy,keep=keep,townhall=townhall,inn=inn)
def apply(name,c):
    f=APPLY.get(name)
    if f:
        o=c['m'].LOD; f(c); c['m'].LOD=o
    return c
