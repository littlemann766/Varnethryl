import sys,os,json,numpy as np
from house import *
from writer import write_glb
from kit2 import *
OUT='/workspace/beth-world/www/proto3d/models/beth/hi/buildings_card2'
def rot(P,N):
    R=np.array([[0,0,-1],[0,1,0],[1,0,0]],float)  # +x -> +z  (x'=-z, z'=x)
    return P@R.T,N@R.T
def inn():
    c=house(dict(W=12,D=9,g=3.4,floors=2,fh=2.7,jetty=0.4,pitch=58))
    cg=cross_gable(c,0.6,6.0,pz=0.5,pitch=60)
    E,g,zf=c['E'],c['g'],cg['zf']
    door(c,'z+',0.6,1.6,2.8)
    for a in(-1.4,2.6): window(c,'z+',a,0.9,0.9,1.6)
    base=lambda a,y:(np.array([a,y,zf]),np.array([1.0,0,0]),np.array([0,0,1.0]))
    for a in(-1.1,0.6,2.3): window(c,None,0,0,w=1.3,h=1.75,base=base(a,g+0.6),flowers=(a!=0.6)); window(c,None,0,0,w=1.3,h=1.75,base=base(a,g+fh_(c)+0.5))
    for a in(-4.6,4.6): window(c,'z+',a,0.9,1.4,1.9); window(c,'z+',a,g+0.6,1.3,1.75,flowers=True); window(c,'z+',a,g+fh_(c)+0.5,1.3,1.75)
    dormer(c,-4.0,1); dormer(c,4.6,1); dormer(c,-2.5,-1); dormer(c,2.5,-1)
    for a in(-4.2,-1.4,1.4,4.2): window(c,'z-',a,1.0); window(c,'z-',a,g+0.8); window(c,'z-',a,g+fh_(c)+0.7)
    for f in('x+','x-'):
        for a in(-2.0,2.0): window(c,f,a,1.0); window(c,f,a,g+0.8); window(c,f,a,g+fh_(c)+0.7)
        gable_fill(c,f)
    door(c,'z-',0.0,1.3,2.5)
    banner(c,'z+',-3.3,g+2.3); banner(c,'z+',5.5,g+2.3)
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
    sign(c,'z+',-4.3,g-0.1,'sign_bread'); banner(c,'z+',0.8,g+2.0)
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
    banner(c,'x+',-3.3,g+2.0)
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
    banner(c,'x+',-3.0,g+2.0); chimney(c,-2.8,-1.2,0.9,1.2)
    steps(c['m'],(c['W']/2,0,-1.0),(0,0,-1),(1,0,0),1.6); barrel(c['m'],(c['W']/2+0.55,0,2.4))
    c['front_gable']=True; return c
def house3():
    c=house(dict(W=10.5,D=7,g=3.0,floors=1,fh=2.7,jetty=0.35,pitch=56)); g,E=c['g'],c['E']
    cg=cross_gable(c,2.6,4.2,pz=0.4,pitch=58); zf=cg['zf']
    door(c,'z+',2.6,1.3,2.5)
    for a in(-3.8,-1.4): window(c,'z+',a,0.9); window(c,'z+',a,g+0.6,flowers=True)
    window(c,'z+',1.5,g+0.6,flowers=True); window(c,'z+',3.7,g+0.6,flowers=True)
    dormer(c,-2.6,1)
    for a in(-3,0,3): window(c,'z-',a,0.9); window(c,'z-',a,g+0.6)
    for f in('x+','x-'): window(c,f,0,0.9); gable_fill(c,f)
    banner(c,'z+',0.0,g+2.0); chimney(c,-4.4,-0.8,0.9,1.3)
    steps(c['m'],(2.6,0,zf),(1,0,0),(0,0,1),1.8)
    for x in(-4.6,-0.4): pot_plant(c['m'],(x,0,c['D']/2+0.5))
    return c
def house4():
    c=house(dict(W=7,D=6.5,g=3.0,floors=2,fh=2.6,jetty=0.4,pitch=60)); g,E,fh=c['g'],c['E'],c['fh']
    door(c,'x+',0.0,1.3,2.5); window(c,'x+',-1.9,0.9); window(c,'x+',1.9,0.9)
    for f_ in range(2):
        for a in(-1.3,1.3): window(c,'x+',a,g+f_*fh+0.5,flowers=(f_==0))
    gable_fill(c,'x+'); gable_fill(c,'x-')
    for f in('z+','z-'):
        for a in(-1.6,1.6): window(c,f,a,g+0.5); window(c,f,a,g+fh+0.5)
    banner(c,'x+',-2.9,g+fh+1.6); sign(c,'x+',2.9,g-0.2,'sign_inn',0.7,0.7)
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
    chimney(c,-2.4,1.6,1.4,2.0)
    # forge lean-to on +z side (pre-rotation): becomes the right-hand side
    lean_to(m,-3.2,2.6,c['D']/2,2.8,3.4,2.4)
    anvil(m,(-0.6,0,c['D']/2+1.4)); m.box((1.0,0,c['D']/2),(2.2,1.1,c['D']/2+1.2),'stone')  # forge hearth
    m.box((1.2,1.1,c['D']/2+0.2),(2.0,1.15,c['D']/2+1.0),'iron')
    for x in(-2.6,-2.0): barrel(m,(x,0,c['D']/2+2.2))
    crate(m,(c['W']/2+0.6,0,2.6)); crate(m,(c['W']/2+0.6,0.0,-2.7),0.6)
    steps(m,(c['W']/2,0,0),(0,0,-1),(1,0,0),2.6,k=2)
    c['front_gable']=True; return c
def apothecary():
    c=house(dict(W=8,D=6.5,g=3.0,floors=1,fh=2.6,jetty=0.35,pitch=57)); g,E=c['g'],c['E']; m=c['m']
    cg=cross_gable(c,0,4.0,pz=0.35,pitch=60); zf=cg['zf']
    door(c,'z+',0.6,1.2,2.4); window(c,'z+',-0.9,0.8,1.4,1.6)
    for a in(-3.0,3.0): window(c,'z+',a,0.8,1.3,1.6); window(c,'z+',a,g+0.5,flowers=True)
    for a in(-0.9,0.9): window(c,'z+',a,g+0.5,1.0,1.5)
    # shop board (potion sign mounted flat) across cross gable
    p=np.array([0,g+0.15,zf+0.08]); m.obox(p,(1,0,0),(0,1,0),(0,0,1),(3.2,0.55,0.08),'beam')
    m.cell([p+[-1.4,-0.22,0.05],p+[1.4,-0.22,0.05],p+[1.4,0.22,0.05],p+[-1.4,0.22,0.05]],'sign_potion',0.05,0.95,0.42,0.58)
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
    for a in(-1.2,1.2): banner(c,'z+',a,g+fh*2-0.2,1.1,2.6)
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
    return c

SPECS={k:v for k,v in globals().items() if k in('inn','bakery','house1','house2','house3','house4','smithy','apothecary','guildhall')}
def export(name):
    c=SPECS[name](); m=c['m']; os.makedirs(OUT,exist_ok=True); info={}
    for lod,suf in((99,''),(1,'_lod1'),(2,'_lod2')):
        # lod: keep tris with lod-tag > threshold ; hi keeps all (threshold -1)
        P,F,UV,N=m.arrays(-1 if lod==99 else lod)
        if c.get('front_gable'): P,N=rot(P,N)
        f=f'{OUT}/bld_{name}_card2{suf}.glb'; write_glb(f,P,F,UV,N,f'bld_{name}_card2','atlas')
        info[suf or '_hi']=dict(tris=len(F),kb=os.path.getsize(f)//1024)
    print(name,info); return info
if __name__=='__main__':
    for n in sys.argv[1:]: export(n)
