import sys,os,json,numpy as np
from house import *
from writer import write_glb
from kit2 import *
from kit3 import *
from bld4 import *
OUT='/workspace/beth-world/www/proto3d/models/beth/hi/buildings_card2'
def rot(P,N):
    R=np.array([[0,0,-1],[0,1,0],[1,0,0]],float)  # +x -> +z  (x'=-z, z'=x)
    return P@R.T,N@R.T
def inn():
    c=house(dict(W=12,D=9,g=3.4,floors=2,fh=2.7,jetty=0.4,pitch=58,upper='stone',framing=False))
    cg=cross_gable(c,0.6,6.0,pz=0.5,pitch=60,mat='stone',framed=False)
    E,g,zf=c['E'],c['g'],cg['zf']
    door(c,'z+',0.6,1.6,2.8)
    for a in(-1.4,2.6): window(c,'z+',a,0.9,0.9,1.6)
    base=lambda a,y:(np.array([a,y,zf]),np.array([1.0,0,0]),np.array([0,0,1.0]))
    for a in(-0.2,1.4): window(c,None,0,0,w=1.2,h=1.7,base=base(a,g+0.6),flowers=True)
    window(c,None,0,0,w=1.1,h=1.5,base=base(0.6,g+fh_(c)+0.6))
    for a in(-4.6,4.6): window(c,'z+',a,g+0.6,1.2,1.6)
    dormer(c,-4.0,1); dormer(c,4.6,1); dormer(c,-2.5,-1); dormer(c,2.5,-1)
    for a in(-3.0,3.0): window(c,'z-',a,1.0); window(c,'z-',a,g+0.8)
    for f in('x+','x-'):
        window(c,f,0,1.0); window(c,f,0,g+0.8)
        gable_fill(c,f)
    door(c,'z-',0.0,1.3,2.5)
    banner(c,'z+',-5.55,g+2.5,0.8,2.1); banner(c,'z+',5.55,g+2.5,0.8,2.1)
    sign(c,'z+',-5.5,g-0.2,'sign_inn')
    lantern(c,'z+',-0.6,2.6); lantern(c,'z+',1.8,2.6)
    zf0=cg['zf']; steps(c['m'],(0.6,0,zf0),(1,0,0),(0,0,1),2.2)
    for x,z in((-2.6,zf0+0.5),(-3.2,zf0+0.9),(3.6,zf0+0.6)): barrel(c['m'],(x,0,z))
    for x in(-5.2,-4.2,4.6,5.4): pot_plant(c['m'],(x,0,c['D']/2+0.6))
    chimney(c,4.3,-1.6,1.1,1.6); chimney(c,-5.0,1.0,0.9,1.0)
    return c
def fh_(c): return c['fh']
def bakery():
    c=house(dict(W=10,D=8,g=3.2,floors=1,fh=2.8,jetty=0.35,pitch=57))
    cg=cross_gable(c,-1.8,4.6,pz=0.45,pitch=58); zf=cg['zf']; g,E=c['g'],c['E']
    base=lambda a,y:(np.array([a,y,zf]),np.array([1.0,0,0]),np.array([0,0,1.0]))
    door(c,'z+',-1.8,1.5,2.6)
    window(c,None,0,0,base=base(-2.8,g+0.8),flowers=True); window(c,None,0,0,base=base(-0.8,g+0.8),flowers=True)
    window(c,'z+',2.6,0.9,1.6,1.3); window(c,'z+',2.6,g+0.8,flowers=True)
    dormer(c,2.6,1); dormer(c,0,-1)
    for a in(-3,0,3): window(c,'z-',a,1.0); window(c,'z-',a,g+0.8)
    for f in('x+','x-'): window(c,f,-1.5,1.0); window(c,f,1.5,g+0.8); gable_fill(c,f)
    pass; banner(c,'z+',0.8,g+2.0)
    lantern(c,'z+',-0.6,2.4)
    chimney(c,3.9,-1.4,1.3,1.8)   # tall oven chimney
    steps(c['m'],(-1.8,0,zf),(1,0,0),(0,0,1),2.0)
    for x,z in((0.6,4.7),(1.3,4.9)): barrel(c['m'],(x,0,z))
    for x in(3.6,4.4): pot_plant(c['m'],(x,0,4.6))
    return c
def house1():
    c=house(dict(W=8.5,D=7,g=3.0,floors=1,fh=2.7,jetty=0.35,pitch=58))
    g,E=c['g'],c['E']
    # front is the gable end (+x before rotation)
    door(c,'x+',0.3,1.3,2.5)
    window(c,'x+',-2.0,1.0); window(c,'x+',2.0,1.0)
    window(c,'x+',-1.3,g+0.7,flowers=True); window(c,'x+',1.3,g+0.7,flowers=True); gable_fill(c,'x+')
    for f in('z+','z-'):
        for a in(-2.2,1.8): window(c,f,a,1.0); window(c,f,a,g+0.7)
    dormer(c,0.0,1); dormer(c,0.0,-1)
    window(c,'x-',0,1.0); window(c,'x-',0,g+0.7); gable_fill(c,'x-')
    banner(c,'x+',-3.0,g+2.4,1.0,2.4)
    chimney(c,-3.6,0.0,1.0,1.2)
    steps(c['m'],(c['W']/2,0,0.3),(0,0,-1),(1,0,0),1.8)
    barrel(c['m'],(c['W']/2+0.6,0,-2.6)); pot_plant(c['m'],(c['W']/2+0.5,0,2.2)); pot_plant(c['m'],(c['W']/2+0.6,0,-1.6))
    c['front_gable']=True; return c

def house2():
    c=house(dict(W=7.5,D=6.5,g=3.0,floors=1,fh=2.7,jetty=0.35,pitch=58)); g,E=c['g'],c['E']
    door(c,'x+',-1.0,1.3,2.5); window(c,'x+',1.4,0.9)
    window(c,'x+',-1.2,g+0.6,flowers=True); window(c,'x+',1.2,g+0.6,flowers=True); gable_fill(c,'x+'); gable_fill(c,'x-')
    for f in('z+','z-'): window(c,f,-1.8,0.9); window(c,f,1.6,g+0.6)
    dormer(c,0.5,1)
    banner(c,'x+',-2.75,g+2.4,1.0,2.4); chimney(c,-2.8,-1.2,0.9,1.2)
    steps(c['m'],(c['W']/2,0,-1.0),(0,0,-1),(1,0,0),1.6); barrel(c['m'],(c['W']/2+0.55,0,2.4))
    c['front_gable']=True; return c
def house3():
    # card house: short body, the front gable dominates (door kept at x=2.6 on the z+ wall)
    c=house(dict(W=7.6,D=7,g=3.0,floors=1,fh=2.7,jetty=0.35,pitch=56)); g,E=c['g'],c['E']
    cg=cross_gable(c,1.2,5.6,pz=0.4,pitch=60); zf=cg['zf']
    door(c,'z+',2.6,1.3,2.5)
    window(c,'z+',0.4,0.9); window(c,'z+',-2.6,0.9)
    window(c,None,0,0,w=1.6,h=1.5,flowers=True,base=(np.array([1.2,g+0.6,zf]),np.array([1.0,0,0]),np.array([0,0,1.0])))
    for a in(-2,2): window(c,'z-',a,0.9); window(c,'z-',a,g+0.6)
    for f in('x+','x-'): window(c,f,0,0.9); gable_fill(c,f)
    chimney(c,-2.6,-0.8,0.9,1.3)
    steps(c['m'],(2.6,0,zf),(1,0,0),(0,0,1),1.8)
    for x in(-3.2,-1.0): pot_plant(c['m'],(x,0,c['D']/2+0.5))
    return c
def house4():
    c=house(dict(W=7,D=6.5,g=3.0,floors=2,fh=2.6,jetty=0.4,pitch=60)); g,E,fh=c['g'],c['E'],c['fh']
    door(c,'x+',0.0,1.3,2.5); window(c,'x+',-1.9,0.9); window(c,'x+',1.9,0.9)
    for f_ in range(2):
        for a in(-1.3,1.3): window(c,'x+',a,g+f_*fh+0.5,flowers=(f_==0))
    gable_fill(c,'x+'); gable_fill(c,'x-')
    for f in('z+','z-'):
        for a in(-1.6,1.6): window(c,f,a,g+0.5); window(c,f,a,g+fh+0.5)
    banner(c,'x+',-2.75,g+fh+1.8,1.0,2.4); sign(c,'x+',2.9,g-0.2,'sign_inn',0.7,0.7)
    chimney(c,2.5,1.0,0.9,1.0)
    steps(c['m'],(c['W']/2,0,0.0),(0,0,-1),(1,0,0),1.6); pot_plant(c['m'],(c['W']/2+0.5,0,-1.9)); pot_plant(c['m'],(c['W']/2+0.5,0,1.9))
    c['front_gable']=True; return c
def smithy():
    c=house(dict(W=8,D=7.5,g=3.6,floors=1,fh=2.0,jetty=0.0,pitch=55,upper='stone',framing=False)); g,E=c['g'],c['E']; m=c['m']
    door(c,'x+',0.0,2.2,3.2)
    window(c,'x+',0,E+0.5,1.1,1.3)
    for f in('z+','z-'): window(c,f,-1.6,1.2); window(c,f,1.8,g+0.2)
    gable_fill(c,'x-')
    # lion shield on gable
    p,t,n=facepos(c,'x+',0,E+2.4); m.obox(p+n*0.08,t,(0,1,0),n,(1.1,1.3,0.1),'gold')
    m.cell([p+n*0.14-t*0.45-[0,0.55,0],p+n*0.14+t*0.45-[0,0.55,0],p+n*0.14+t*0.45+[0,0.55,0],p+n*0.14-t*0.45+[0,0.55,0]],'banner',0.08,0.92,0.15,0.85)
    banner(c,'x+',-3.2,g+0.6,0.8,1.7); sign(c,'x+',3.2,g-0.4,'sign_anvil',0.8,0.8)
    chimney(c,c['X1']-1.0,0.0,1.4,2.2)
    # forge lean-to on +z side (pre-rotation): becomes the right-hand side
    lean_to(m,-3.2,2.6,c['D']/2,2.8,3.4,2.4)
    anvil(m,(-0.6,0,c['D']/2+1.4)); m.box((1.0,0,c['D']/2),(2.2,1.1,c['D']/2+1.2),'stone')  # forge hearth
    m.box((1.2,1.1,c['D']/2+0.2),(2.0,1.15,c['D']/2+1.0),'iron')
    for x in(-2.6,-2.0): barrel(m,(x,0,c['D']/2+2.2))
    crate(m,(c['W']/2+0.6,0,2.6)); crate(m,(c['W']/2+0.6,0.0,-2.7),0.6)
    steps(m,(c['W']/2,0,0),(0,0,-1),(1,0,0),2.6,k=2)
    for zz in(-2.4,2.3): rack(m,(c['W']/2,0,zz),(0,0,-1),(1,0,0),1.4,2.0)
    c['front_gable']=True; return c
def apothecary():
    c=house(dict(W=8,D=6.5,g=3.0,floors=1,fh=2.6,jetty=0.35,pitch=57)); g,E=c['g'],c['E']; m=c['m']
    cg=cross_gable(c,0,4.0,pz=0.35,pitch=60); zf=cg['zf']
    door(c,'z+',0.6,1.2,2.4); window(c,'z+',-0.9,0.8,1.4,1.6)
    for a in(-3.0,3.0): window(c,'z+',a,0.8,1.3,1.6); window(c,'z+',a,g+0.5,flowers=True)
    for a in(-0.9,0.9): window(c,'z+',a,g+0.5,1.0,1.5)
    # shop board (potion sign mounted flat) across cross gable
    p=np.array([0,g+0.15,zf+0.08]); m.obox(p,(1,0,0),(0,1,0),(0,0,1),(3.2,0.55,0.08),'beam')
    m.cell([p+[-0.26,-0.26,0.05],p+[0.26,-0.26,0.05],p+[0.26,0.26,0.05],p+[-0.26,0.26,0.05]],'sign_potion',0.05,0.95,0.3,0.78)
    sign(c,'z+',-3.9,g-0.2,'sign_potion',0.7,0.8); lantern(c,'z+',-1.9,2.5)
    for a in(-2.5,2.5): window(c,'z-',a,0.9); window(c,'z-',a,g+0.5)
    door(c,'z-',0,1.1,2.3); dormer(c,0,-1)
    for f in('x+','x-'): window(c,f,0,0.9); gable_fill(c,f)
    chimney(c,-3.4,-0.6,0.8,1.2); chimney(c,3.4,-0.6,0.8,1.2)
    ivy(m,[(x,y,c['D']/2+0.15) for x in(-3.9,-3.7,3.8) for y in np.arange(0.3,g+2,0.45)],0.28)
    ivy(m,[(x,g-0.05,zf+0.2) for x in np.linspace(-1.8,1.8,8)],0.22)
    for x in(-2.6,-1.6,1.8,2.8): pot_plant(m,(x,0,c['D']/2+0.5))
    steps(m,(0.6,0,zf),(1,0,0),(0,0,1),1.6,k=2)
    return c
def guildhall():
    c=house(dict(W=14,D=11,g=3.8,floors=2,fh=2.9,jetty=0.45,pitch=58)); g,E,fh=c['g'],c['E'],c['fh']; m=c['m']
    cg=cross_gable(c,0,7.0,pz=0.6,pitch=58); zf=cg['zf']
    door(c,'z+',0,2.0,3.2)
    base=lambda a,y:(np.array([a,y,zf]),np.array([1.0,0,0]),np.array([0,0,1.0]))
    for a in(-2.3,2.3): window(c,None,0,0,1.2,1.8,base=base(a,1.0))
    for f_ in range(2):
        for a in(-2.4,0,2.4): window(c,None,0,0,1.2,1.75,flowers=(f_==0 and a!=0),base=base(a,g+f_*fh+0.55))
    for a in(-5.6,5.6):
        window(c,'z+',a,1.0,1.2,1.8)
        for f_ in range(2): window(c,'z+',a,g+f_*fh+0.55,1.2,1.75)
    # big guild banners on the cross gable + corner banners
    for a in(-3.0,3.0): banner(c,'z+',a,g+fh*2-0.2,1.1,3.2)
    for a in(-6.8,6.8): banner(c,'z+',a,g+fh+1.6,0.9,2.0)
    dormer(c,-5.2,1); dormer(c,5.2,1)
    for a in(-4,0,4): dormer(c,a,-1)
    for a in(-5,-1.7,1.7,5):
        window(c,'z-',a,1.0)
        for f_ in range(2): window(c,'z-',a,g+f_*fh+0.55)
    for f in('x+','x-'):
        for a in(-3,0,3):
            window(c,f,a,1.0)
            for f_ in range(2): window(c,f,a,g+f_*fh+0.55)
        gable_fill(c,f)
    # stone corner piers up the front like the card
    for a in(-3.6,3.6): m.box((a-0.35,0,zf-0.2),(a+0.35,E+0.2,zf+0.35),'stone',a)
    chimney(c,5.6,-2.0,1.2,1.8); chimney(c,-5.8,1.5,1.0,1.2)
    steps(m,(0,0,zf),(1,0,0),(0,0,1),3.2,k=4)
    for x in(-4.4,4.4): pot_plant(m,(x,0,zf+0.6),0.4)
    lantern(c,'z+',-1.4,2.8); lantern(c,'z+',1.4,2.8)
    # card: tall stone turret with spire at front-right corner + pinnacle spires on gables + gold trims
    m.box((c['X1']-0.5,0,c['hs']-0.3),(c['X1']+0.25,E+0.3,c['hs']+0.25),'stone',1.3); pinnacle(m,(c['X1']-0.12,E+0.3,c['hs']-0.02),2.0)
    # card: huge gold-framed lion shields fill the front gables
    for a in(-5.6,5.6):
        p=np.array([a,g+fh+1.0,c['hs']+0.12]); m.obox(p,(1,0,0),(0,1,0),(0,0,1),(2.5,3.0,0.14),'gold')
        m.cell([p+[-1.1,-1.35,0.09],p+[1.1,-1.35,0.09],p+[1.1,1.35,0.09],p+[-1.1,1.35,0.09]],'banner',0.08,0.92,0.12,0.86)
    for x in(-3.6,3.6): pinnacle(m,(x,E+0.2,zf+0.1),2.0)
    pinnacle(m,(0,cg['R2']+0.2,zf+0.4),2.4); pinnacle(m,(c['X0']-0.45,c['Rh']+0.2,0),2.2)
    m.beam((-3.5,E+0.05,zf+0.36),(3.5,E+0.05,zf+0.36),0.12,'gold'); m.beam((-3.5,g+0.05,zf+0.36),(3.5,g+0.05,zf+0.36),0.12,'gold')
    p=np.array([0,E+0.7,zf+0.3]); m.obox(p,(1,0,0),(0,1,0),(0,0,1),(3.5,4.7,0.16),'gold')
    m.cell([p+[-1.6,-2.2,0.1],p+[1.6,-2.2,0.1],p+[1.6,2.2,0.1],p+[-1.6,2.2,0.1]],'banner',0.08,0.92,0.12,0.86)
    for s in(-1,1): m.beam(p+[s*1.2,2.35,0],p+[s*1.2,3.0,-0.3],0.05,'iron')
    return c

def market():
    c=house(dict(W=11,D=8,g=3.4,floors=1,fh=2.8,jetty=0.45,pitch=57)); g,E=c['g'],c['E']; m=c['m']
    cg=cross_gable(c,-1.8,4.6,pz=0.5,pitch=60); zf=cg['zf']
    door(c,'z+',-1.8,1.5,2.6)
    for a in(-3.4,-0.2): window(c,'z+',a,0.9,1.0,1.6)
    for a in(-3.0,-0.6): window(c,'z+',a,g+0.55,flowers=True)
    for a in(2.2,4.2): window(c,'z+',a,0.9,1.4,1.7); window(c,'z+',a,g+0.55,flowers=True)
    awning(m,-4.1,0.5,g-0.15,zf+0.05,1.5,0.6,8); awning(m,1.2,5.3,g-0.15,c['D']/2+0.05,1.6,0.6,8)
    for x in(-3.0,-0.6,2.4,4.4): stall(m,x,zf+2.2 if x<1 else c['D']/2+2.0,1.8)
    for x,z in((-4.6,zf+0.6),(0.9,zf+0.8),(5.8,c['D']/2+0.8)): barrel(m,(x,0,z))
    crate(m,(1.3,0,c['D']/2+0.7),0.6); crate(m,(-5.0,0,zf+1.3),0.6)
    dormer(c,2.9,1); dormer(c,-2,-1); dormer(c,2,-1)
    for a in(-3,0,3): window(c,'z-',a,0.9); window(c,'z-',a,g+0.55)
    for f in('x+','x-'): window(c,f,0,0.9); gable_fill(c,f)
    sign(c,'z+',-4.9,g-0.2,'sign_potion',0.8,0.9); cb(m,(-1.8,E+2.3,zf+0.05),1.0,2.3)
    # tall stone chimney stack on right side with ivy (card)
    m.box((c['X1'],0,-1.0),(c['X1']+1.2,c['Rh']+1.6,0.4),'stone',0.4); m.box((c['X1']-0.1,c['Rh']+1.6,-1.1),(c['X1']+1.3,c['Rh']+1.8,0.5),'stone')
    ivy(m,[(c['X1']+1.25,y,-0.3+0.4*np.sin(y)) for y in np.arange(0.4,c['Rh'],0.5)],0.32)
    steps(m,(-1.8,0,zf),(1,0,0),(0,0,1),2.0,k=2)
    return c
def townhall():
    c=house(dict(W=13,D=10,g=4.0,floors=2,fh=3.2,jetty=0.0,pitch=55,upper='stone',framing=False,remap=CREAM)); g,E,fh=c['g'],c['E'],c['fh']; m=c['m']
    cg=cross_gable(c,0,5.4,pz=0.8,pitch=55,mat='stone',framed=False,attic=False); zf=cg['zf']
    door(c,'z+',0,2.0,3.4)
    t=np.array([1.0,0,0]); n=np.array([0,0,1.0])
    for a in(-1.7,1.7): lancet(m,(a,4.6,zf),t,n,0.9,2.6)
    p=np.array([0,E+1.3,zf+0.1]); m.obox(p,t,(0,1,0),n,(2.0,2.4,0.14),'gold')
    m.cell([p+[-0.85,-1.05,0.09],p+[0.85,-1.05,0.09],p+[0.85,1.05,0.09],p+[-0.85,1.05,0.09]],'banner',0.08,0.92,0.12,0.85)
    for a in(-4.4,4.4): lancet(m,(a,1.2,c['hs']),t,n,0.9,2.2); lancet(m,(a,g+0.6,c['hs']),t,n,0.9,2.4); lancet(m,(a,g+fh+0.6,c['hs']),t,n,0.9,2.2)
    for a in(-2.8,2.8): banner(c,'z+',a,E-0.4,1.0,5.0)
    for sx in(-1,1):
        tower(m,(sx*(c['W']/2+0.4),0,c['D']/2+0.4),1.5,E+2.2,4.8,wins=4)   # card: two-tower front only
    for x in(-2.7,2.7): pinnacle(m,(x,E+0.2,zf+0.2),2.0)
    pinnacle(m,(0,cg['R2']+0.1,zf+0.3),2.6)
    for a in(-4,0,4):
        lancet(m,(a,1.2,-c['hs']),-t,-n,0.9,2.2); lancet(m,(a,g+0.6,-c['hs']),-t,-n,0.9,2.4)
    for f in('x+','x-'):
        for a in(-2.5,2.5): window(c,f,a,1.2,1.0,2.0); window(c,f,a,g+0.6,1.0,2.0); window(c,f,a,g+fh+0.6,1.0,2.0)
        gable_fill(c,f)
    steps(m,(0,0,zf),(1,0,0),(0,0,1),4.5,k=6)
    return c
def temple():
    c=house(dict(W=18,D=11,g=5.0,floors=1,fh=3.5,jetty=0.0,pitch=60,upper='stone',framing=False,remap=dict(CREAM,window='bluewin'))); g,E=c['g'],c['E']; m=c['m']
    X1=c['X1']; t=np.array([0,0,-1.0]); n=np.array([1.0,0,0]); up=np.array([0,1.0,0])
    # front facade on +x (rotated to +z): gold-framed portal, tall traceried lancet, rose in the gable, spired towers
    door(c,'x+',0,2.6,4.6); gold_portal(m,(X1,0,0),t,n,2.6,4.6)
    glancet(m,(X1,5.6,0),t,n,2.8,4.6); rose(m,(X1,E+4.4,0),t,n,1.25); gold_ring(m,(X1+0.2,E+4.4,0),t,n,1.45)
    for a in(-3.0,3.0): glancet(m,(X1,2.0,a),t,n,1.0,3.6); glancet(m,(X1,7.4,a),t,n,0.9,2.6)
    for a in(-4.6,4.6): banner(c,'x+',a,E-0.6,1.1,4.0)
    for sz in(-1,1): tower(m,(X1+0.3,0,sz*(c['D']/2+0.6)),1.9,E+3.0,6.0,wins=4)
    for z in(-2.2,2.2): pinnacle(m,(X1+0.2,E+0.2,z),2.4)
    for z in(-1.4,1.4): pinnacle(m,(X1+0.25,E+2.6,z*0.7),1.8)
    pinnacle(m,(X1+0.45,c['Rh']+0.2,0),3.0)
    # statues on plinths flanking the steps + on the tower buttresses
    for sz in(-1,1):
        m.box((X1+2.2,0,sz*2.6-0.55),(X1+3.3,1.1,sz*2.6+0.55),'stone'); m.box((X1+2.1,1.1,sz*2.6-0.62),(X1+3.4,1.25,sz*2.6+0.62),'stone')
        statue(m,'robed',(X1+2.75,1.25,sz*2.6),1.55,90)
        m.obox((X1+0.35,4.9,sz*1.75),(0,0,1),(0,1,0),(1,0,0),(1.1,0.2,0.9),'stone'); statue(m,'robed',(X1+0.5,5.0,sz*1.75),1.15,90)
    # sides: traceried lancets + buttresses topped by side spires
    for x in np.arange(-7,7.1,3.5):
        for sz,ts,ns in((1,(1,0,0),(0,0,1)),(-1,(-1,0,0),(0,0,-1))):
            glancet(m,(x,1.6,sz*c['hs']),np.array(ts,float),np.array(ns,float),1.0,3.6)
            if x<7:
                zc=sz*(c['hs']+0.05); m.box((x+1.55,0,zc-0.55),(x+2.05,g+0.8,zc+0.55),'stone')
                pinnacle(m,(x+1.8,g+0.8,zc),2.8)
    # rear corner spire turrets
    for sz in(-1,1): tower(m,(c['X0']+0.2,0,sz*(c['D']/2+0.2)),1.2,E+0.5,4.2,wins=2)
    # crossing spire with gold ridge trims
    m.box((-3.2,c['Rh']-2.5,-1.6),(-0.2,c['Rh']+1.5,1.6),'stone'); cone(m,(-1.7,0,0),2.3,c['Rh']+1.5,7.5,'slate',8)
    for x in(-0.2,-3.2): m.beam((x,c['Rh']+1.5,-1.6),(x,c['Rh']+1.5,1.6),0.12,'gold')
    m.beam((c['X0']-0.4,c['Rh']+0.32,0),(X1+0.4,c['Rh']+0.32,0),0.1,'gold')
    steps(m,(X1+0.4,0,0),(0,0,-1),(1,0,0),5.0,k=6)
    c['front_gable']=True; return c
def gatehouse():
    from geo import Mesh
    m=Mesh(); c=dict(m=m)
    m.box((-4,0,-3),(4,9,3),'stone'); crenels_line(m,(-4,0,3.0),(4,0,3.0),9.0); crenels_line(m,(4,0,-3.0),(-4,0,-3.0),9.0)
    t=np.array([1.0,0,0]); n=np.array([0,0,1.0]); up=np.array([0,1.0,0])
    for zz,nn,tt in((3.0,n,t),(-3.0,-n,-t)):
        p=np.array([0,0,zz]); b=p+nn*0.03
        m.cell([b-tt*1.9,b+tt*1.9,b+tt*1.9+up*5.4,b-tt*1.9+up*5.4],'door')
        o=m.LOD; m.LOD=2
        for k in range(11):
            th=np.pi*k/10; q=p+tt*np.cos(th)*2.15+up*(3.4+np.sin(th)*2.15)+nn*0.2
            m.obox(q,tt*np.cos(th+np.pi/2)+up*np.sin(th+np.pi/2),-(tt*np.cos(th)+up*np.sin(th)),nn,(0.5,0.6,0.45),'stone',k*0.1)
        m.LOD=o
        for s_ in(-1,1): m.obox(p+tt*s_*2.2+up*1.7+nn*0.2,tt,up,nn,(0.5,3.4,0.45),'stone')
    m.LOD=1
    for x in np.linspace(-1.6,1.6,7): m.box((x-0.05,0.4,3.1),(x+0.05,4.9,3.2),'iron')   # portcullis
    for y in(1.5,3.0,4.4): m.box((-1.7,y-0.05,3.1),(1.7,y+0.05,3.22),'iron')
    m.LOD=99
    for sx in(-1,1):
        tower(m,(sx*5.4,0,0.3),2.8,15.5,6.5,wins=4,cone_r=3.2)
        p=np.array([sx*5.4,7.5,0.3+2.85]); banner(dict(m=m,hs=0,g=0,D=0,X0=0,X1=0),'__',0,0) if False else None
        cloth_b(m,np.array([sx*5.4,12.0,3.3]),1.5,4.6)
        m.box((sx*8.2-1.4*sx-1.4,0,-2.2),(sx*8.2-1.4*sx+1.4,7.0,2.2),'stone') if False else None
        a0=sx*7.8; a1=sx*12.0; lo=min(a0,a1); hi=max(a0,a1)
        m.box((lo,0,-1.8),(hi,7.0,1.8),'stone'); crenels_line(m,(lo,0,1.8),(hi,0,1.8),7.0); crenels_line(m,(hi,0,-1.8),(lo,0,-1.8),7.0)
    for x in(-3.0,3.0): m.box((x-0.2,9.0,-0.2),(x+0.2,9.5,0.2),'stone')
    p=np.array([0,7.4,3.05]); m.obox(p,t,up,n,(1.4,1.6,0.12),'gold')
    m.cell([p+[-0.6,-0.7,0.08],p+[0.6,-0.7,0.08],p+[0.6,0.7,0.08],p+[-0.6,0.7,0.08]],'banner',0.08,0.92,0.12,0.85)
    return c
def cloth_b(m,top,w,h):
    from house import cloth
    t=np.array([1.0,0,0]); n=np.array([0,0,1.0])
    m.beam(top-n*0.4,top+n*0.25,0.07,'iron'); m.beam(top+n*0.25-t*(w/2+0.1),top+n*0.25+t*(w/2+0.1),0.06,'iron')
    cloth(m,top+n*0.25-[0,0.04,0],t,n,w,h,'banner',0.05)
def wall_segment():
    from geo import Mesh
    m=Mesh(); L=12
    m.box((-L/2,0,-1.5),(L/2,7.0,1.5),'stone'); m.box((-L/2-0.1,0,-1.7),(L/2+0.1,0.8,1.7),'stone',0.3)
    crenels_line(m,(-L/2,0,1.5),(L/2,0,1.5),7.0); crenels_line(m,(L/2,0,-1.5),(-L/2,0,-1.5),7.0)
    for x in(-3,3): cloth_b(m,np.array([x,6.4,1.6]),1.0,2.6)
    for x in(-5,0,5): m.box((x-0.6,0,1.5),(x+0.6,5.0,2.1),'stone',x)  # buttresses
    return dict(m=m)
def watchtower():
    from geo import Mesh
    m=Mesh(); tower(m,(0,0,0),3.0,13.0,6.0,wins=4,cone_r=3.6); cloth_b(m,np.array([0,9.5,3.05]),1.2,3.0)
    door_m=np.array([0,0,3.02]); m.cell([door_m+[-0.7,0,0],door_m+[0.7,0,0],door_m+[0.7,2.5,0],door_m+[-0.7,2.5,0]],'door')
    return dict(m=m)
def keep():
    from geo import Mesh
    m=Mesh(); m.remap={}; t=np.array([1.0,0,0]); n=np.array([0,0,1.0]); up=np.array([0,1.0,0])
    m.box((-6,0,-6),(6,16,6),'stone')
    for a,b in(((-6,0,6),(6,0,6)),((6,0,-6),(-6,0,-6)),((6,0,6),(6,0,-6)),((-6,0,-6),(-6,0,6))): crenels_line(m,a,b,16.0)
    for sx in(-1,1):
        for sz in(-1,1): tower(m,(sx*6,0,sz*6),2.2,19.0,6.5,wins=4,cone_r=2.7)
    tower(m,(0,0,0),2.8,24.0,7.5,wins=3,cone_r=3.3)
    for x in(-3,3):
        for y in(5,9,13): lancet(m,(x,y,6.0),t,n,0.9,2.0)
    p=np.array([0,0,6.0]); b=p+n*0.03; m.cell([b-t*1.5,b+t*1.5,b+t*1.5+up*4.2,b-t*1.5+up*4.2],'door')
    for x in(-1.6,1.6): cloth_b(m,np.array([x*2.3,14.5,6.1]),1.4,4.5)
    # curtain wall + corner towers in grey fieldstone (core keep stays cream)
    m.remap={}
    R=13
    for (a,b) in(((-R,R),(R,R)),((R,R),(R,-R)),((R,-R),(-R,-R)),((-R,-R),(-R,R))):
        a3=np.array([a[0],0,a[1]]); b3=np.array([b[0],0,b[1]]); d=b3-a3; L=np.linalg.norm(d); ax=d/L; az=np.cross(ax,[0,1,0])
        m.obox((a3+b3)/2+[0,3.75,0],ax,up,az,(L,7.5,2.4),'stone'); crenels_line(m,a3-az*1.0,b3-az*1.0,7.5); crenels_line(m,b3+az*1.0,a3+az*1.0,7.5)
    for sx in(-1,1):
        for sz in(-1,1): tower(m,(sx*R,0,sz*R),2.6,11.0,5.0,wins=2,cone_r=3.1)
    # gate in front curtain + flags
    p=np.array([0,0,R+1.25]); m.cell([p-t*1.8,p+t*1.8,p+t*1.8+up*4.6,p-t*1.8+up*4.6],'door')
    for sx in(-1,1): tower(m,(sx*3.2,0,R+0.6),1.9,10.0,4.6,wins=2,crenel=False)
    steps(m,(0,0,R+1.3),t,n,4.0,k=3)
    return dict(m=m)
def fountain():
    from geo import Mesh
    m=Mesh(); m.remap=dict(CREAM)
    m.box((-7,0,-7),(7,0.12,7),'stone')                               # plaza flagstones
    cyl(m,(0,0,0),4.6,0,0.9,'stone',28,cap=None); cyl(m,(0,0,0),4.15,0.0,0.9,'stone',28)
    cyl(m,(0,0.88,0),4.65,0,0.12,'stone',28,r1=4.65)
    # water disc
    for i in range(28):
        a0=2*np.pi*i/28; a1=2*np.pi*(i+1)/28
        m.cell([np.array([0,0.7,0]),np.array([0,0.7,0]),np.array([4.15*np.cos(a1),0.7,4.15*np.sin(a1)]),np.array([4.15*np.cos(a0),0.7,4.15*np.sin(a0)])],'water',i/28,(i+1)/28,0.0,1.0)
    cyl(m,(0,0,0),1.7,0,1.6,'stone',16,cap='stone'); cyl(m,(0,1.6,0),1.3,0,0.4,'stone',16,r1=2.5)
    cyl(m,(0,2.0,0),2.5,0,0.25,'stone',16,cap='stone'); cyl(m,(0,2.25,0),1.0,0,1.2,'stone',12,cap='stone')
    for k in range(8):  # lion-head spouts + water arcs (blue)
        a=2*np.pi*k/8; d=np.array([np.cos(a),0,np.sin(a)])
        m.obox(d*1.75+[0,1.25,0],np.cross(d,[0,1,0]),(0,1,0),d,(0.35,0.35,0.3),'gold')
        pts=[d*1.9+[0,1.25,0],d*2.6+[0,1.2,0],d*3.1+[0,0.9,0],d*3.3+[0,0.7,0]]
        for p,q in zip(pts[:-1],pts[1:]): m.beam(p,q,0.09,'slate')
    statue(m,'lion',(0,3.42,0),1.05,0,'bluestone')
    for k in range(6):
        a=2*np.pi*(k+0.5)/6; pot_plant(m,(6.0*np.cos(a),0.12,6.0*np.sin(a)),0.45)
    return dict(m=m)
def port():
    from geo import Mesh
    m=Mesh()
    m.box((-16,-2.5,-12),(16,1.2,-4),'stone')                               # quay
    m.box((-16,1.0,-4),(16,1.25,6),'oak')                                   # deck
    for x in np.arange(-15.5,16,2.5):
        for z in(-3.6,0.9,5.6): m.box((x-0.18,-2.5,z-0.18),(x+0.18,1.0,z+0.18),'beam')
    for x in np.arange(-15,16,3): m.box((x-0.2,1.25,5.6),(x+0.2,2.0,6.0),'beam')   # bollards
    w1=house(dict(W=10,D=7,g=3.4,floors=1,fh=3.0,jetty=0.0,pitch=55,upper='stone',framing=False))
    door(w1,'z+',0,2.4,3.0); window(w1,'z+',-3.2,1.2); window(w1,'z+',3.2,1.2); window(w1,'z+',-2.6,4.0); window(w1,'z+',2.6,4.0)
    gable_fill(w1,'x+'); gable_fill(w1,'x-'); dormer(w1,0,1)
    m.merge(w1['m'],(-8,1.2,-8.5))
    w2=house(dict(W=8,D=6.5,g=3.2,floors=1,fh=2.7,jetty=0.35,pitch=57,upper='stone',framing=False))
    door(w2,'z+',-1.5,1.4,2.6); window(w2,'z+',1.8,1.0); window(w2,'z+',-1.8,3.8,flowers=True); window(w2,'z+',1.8,3.8,flowers=True)
    gable_fill(w2,'x+'); gable_fill(w2,'x-'); sign(w2,'z+',3.7,3.0,'sign_inn',0.7,0.7); chimney(w2,2.5,-1.2,0.9,1.2)
    m.merge(w2['m'],(5,1.2,-8.0))
    awning(m,0.5,4.5,3.6,-4.4+0.1,1.6,0.6,8)
    # crane
    m.beam((12,1.25,2),(12,9,2),0.35); m.beam((12,8.5,2),(16.5,9.5,4.5),0.25); m.beam((12,5,2),(15,9.2,3.7),0.18)
    m.beam((16.4,9.4,4.5),(16.4,4.0,4.5),0.04,'iron'); crate(m,(16.4,3.2,4.5),0.9)
    for x,z in((-3,-2.5),(-2.2,-2.2),(-2.6,-1.4),(8,-3),(9,0),(3.5,2.5)): barrel(m,(x,1.25,z))
    for x,z,sz in((-5,0.5,0.9),(-4.1,0.4,0.7),(7.5,1.5,0.8),(8.4,1.6,0.8),(7.9,1.6+0.0,0.6)): crate(m,(x,1.25,z),sz)
    boat(m,(-6,-0.7,9.0),8,2.6,0); boat(m,(7,-0.7,9.5),7,2.2,10)
    for x in(-10,0,10): m.beam((x,1.25,5.4),(x,4.2,5.4),0.12,'iron'); lantern(dict(m=m,hs=5.3,g=0,D=10.6,X0=0,X1=0),'z+',x,4.0)
    # more harbour: row of warehouses/houses, market stalls, drying nets, extra boats
    for k,(x,z,W_,D_,rot) in enumerate(((-14,-8.0,7,6,0),(13,-8.5,7.5,6.5,0),(-1.5,-9.5,6,6,0))):
        h=house(dict(W=W_,D=D_,g=3.2,floors=1+(k%2),fh=2.6,jetty=0.35,pitch=57,upper='stone' if k%2==0 else 'plaster',framing=(k%2==1)))
        door(h,'z+',-1.0,1.3,2.5); window(h,'z+',1.5,1.0); window(h,'z+',-1.4,3.8,flowers=(k==1)); window(h,'z+',1.4,3.8)
        gable_fill(h,'x+'); gable_fill(h,'x-'); chimney(h,1.8,-1.0,0.8,1.1)
        if k==2: banner(h,'z+',2.6,3.6)
        m.merge(h['m'],(x,1.2,z))
    for x in(-12.5,-9.5,9.5): stall(m,x,-2.0,2.0) if False else None
    for x0 in(-13.5,-10.0,8.0):
        m.box((x0,1.25,-3.2),(x0+2.4,2.15,-2.4),'oak')
        for sx in(0,2.3): m.beam((x0+sx,1.25,-3.2),(x0+sx,3.4,-3.2),0.08,'beam'); m.beam((x0+sx,1.25,-2.4),(x0+sx,3.1,-2.4),0.08,'beam')
        m.cell([np.array([x0-0.1,3.1,-2.1]),np.array([x0+2.5,3.1,-2.1]),np.array([x0+2.5,3.5,-3.4]),np.array([x0-0.1,3.5,-3.4])],'banner',0.82,0.88,0.85,0.9)
        for q in(0.5,1.2,1.9): m.blob((x0+q,2.3,-2.8),0.18,'flowers',5,0.7)
    for x0 in(-8.0,3.0):    # fishing nets drying on poles
        for sx in(0,3.0): m.beam((x0+sx,1.25,3.6),(x0+sx,4.0,3.6),0.1,'beam')
        for t_ in np.linspace(0,1,7 if kit2.Q==0 else 3):
            m.beam((x0+t_*3.0,3.9,3.62),(x0+t_*3.0+0.15,1.7,3.62),0.025,'iron'); 
        for y_ in(2.0,2.7,3.4): m.beam((x0,y_,3.62),(x0+3.0,y_+0.05,3.62),0.025,'iron')
    boat(m,(-16,-0.7,10.5),6,2.0,-15); boat(m,(15,-0.7,11),6.5,2.2,20); boat(m,(1,-0.7,13),5,1.8,80)
    for x,z in((-11,2.0),(-10.3,2.4),(11.5,-1.0)): barrel(m,(x,1.25,z))
    # busy card harbour: back row of tall varied stone/timber houses + warehouses, stacked cargo on the quay
    m.box((-17,-2.5,-20),(17,1.2,-12),'stone')
    for k,(x,W_,D_,fl,pit,up) in enumerate(((-13.5,7,6,2,60,'stone'),(-6.5,8.5,6.5,3,56,'plaster'),(1.0,6.5,6,2,62,'stone'),(8.0,9.5,7,2,52,'stone'),(14.5,5.5,5.5,3,60,'plaster'))):
        h=house(dict(W=W_,D=D_,g=3.4,floors=fl,fh=2.7,jetty=0.4 if up=='plaster' else 0.0,pitch=pit,upper=up,framing=(up=='plaster')))
        for f_ in range(fl):
            for a in np.linspace(-W_/2+1.4,W_/2-1.4,max(2,int(W_/2.5))): window(h,'z+',a,3.4+f_*2.7+0.5,1.0,1.4,flowers=(f_==0 and k%2==0))
        door(h,'z+',0,1.4,2.6); gable_fill(h,'x+'); gable_fill(h,'x-'); chimney(h,W_/2-1.0,-1.0,0.9,1.3)
        if k in(1,3): dormer(h,-1.2,1); banner(h,'z+',W_/2-0.7,4.2)
        m.merge(h['m'],(x,1.2,-16.0))
    for (x,z) in((-11.5,-2.6),(-6.0,-1.0),(4.5,-0.8),(10.5,-2.2),(-1.0,2.6)):
        for i in range(3):
            for j in range(3-i): crate(m,(x+j*0.95+i*0.47,1.25+i*0.9,z),0.9)
    for (x,z) in((-14.5,1.5),(13.5,1.0),(2.5,-2.5)):
        for i in range(4): barrel(m,(x+(i%2)*0.8,1.25,z+(i//2)*0.8))
        barrel(m,(x+0.4,1.25+1.0,z+0.4))
    for x in(-8.5,6.0): m.box((x-1.0,1.25,-1.5),(x+1.0,1.45,-0.3),'oak'); [cyl(m,(x-0.6+0.6*i,1.45,-0.9),0.3,0,0.5,'plaster',7,cap='plaster',r1=0.2) for i in range(3)]
    boat(m,(-10,-0.7,15),7.5,2.4,-5)
    return dict(m=m)

def walls_demo():
    from geo import Mesh
    m=Mesh(); ws=wall_segment()['m']; wt=watchtower()['m']
    for x in(-6.5,6.5): m.merge(ws,(x,0,0))
    for x in(-15,15): m.merge(wt,(x,0,0))
    m.merge(wt,(0,0,-0.5)) if False else None
    return dict(m=m)

SPECS={k:v for k,v in globals().items() if callable(v) and k not in('house','export','rot','fh_','cloth_b','write_glb') and not k[0].isupper()}
def export(name,dress_on=True):
    import kit2, detail, deci
    os.makedirs(OUT,exist_ok=True); info={}; hi_n=None
    for q,(lod,suf) in enumerate(((99,''),(1,'_lod1'),(2,'_lod2'))):
        # rebuild at quality q, add the detail dressing, drop tris tagged <= lod, then decimate to the ratio caps
        kit2.Q=q; c=SPECS[name](); import hero; hero.apply(name,c); m=c['m']
        if dress_on: detail.dress(name,m,bool(c.get('front_gable')))
        P,F,UV,N=m.arrays(-1 if lod==99 else lod)
        if q==0: hi_n=len(F)
        else:
            cap=int(hi_n*(0.5 if q==1 else 0.2)*0.97)
            if len(F)>cap: P,F,UV=deci.decimate(P,F,UV,cap); N=deci.normals(P,F)
        if c.get('front_gable'): P,N=rot(P,N)
        f=f'{OUT}/bld_{name}_card2{suf}.glb'; write_glb(f,P,F,UV,N,f'bld_{name}_card2','atlas')
        info[suf or '_hi']=dict(tris=len(F),kb=os.path.getsize(f)//1024)
    kit2.Q=0; print(name,info,flush=True); return info
if __name__=='__main__':
    for n in sys.argv[1:]: export(n)
