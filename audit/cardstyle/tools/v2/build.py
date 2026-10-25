import sys,os,json,numpy as np
from house import *
from writer import write_glb
OUT='/workspace/beth-world/www/proto3d/models/beth/hi/buildings_card2'
def rot(P,N):
    R=np.array([[0,0,-1],[0,1,0],[1,0,0]],float)  # +x -> +z  (x'=-z, z'=x)
    return P@R.T,N@R.T
def inn():
    c=house(dict(W=12,D=9,g=3.4,floors=2,fh=2.7,jetty=0.4,pitch=58))
    cg=cross_gable(c,0.6,6.0,pz=0.5,pitch=60)
    E,g,zf=c['E'],c['g'],cg['zf']
    door(c,'z+',0.6,1.6,2.8)
    base=lambda a,y:(np.array([a,y,zf]),np.array([1.0,0,0]),np.array([0,0,1.0]))
    for a in(-1.0,2.2): window(c,None,0,0,base=base(a,g+0.8),flowers=True); window(c,None,0,0,base=base(a,g+fh_(c)+0.7))
    window(c,None,0,0,w=0.8,h=1.0,base=base(0.6,E+0.6))
    for a in(-4.6,4.6): window(c,'z+',a,1.0); window(c,'z+',a,g+0.8,flowers=True)
    dormer(c,-4.0,1); dormer(c,4.6,1); dormer(c,-2.5,-1); dormer(c,2.5,-1)
    for a in(-4.2,-1.4,1.4,4.2): window(c,'z-',a,1.0); window(c,'z-',a,g+0.8); window(c,'z-',a,g+fh_(c)+0.7)
    for f in('x+','x-'):
        for a in(-2.0,2.0): window(c,f,a,1.0); window(c,f,a,g+0.8); window(c,f,a,g+fh_(c)+0.7)
        window(c,f,0,c['E']+0.7,0.7,1.0)
    door(c,'z-',0.0,1.3,2.5)
    banner(c,'z+',-3.3,g+2.3); banner(c,'z+',5.5,g+2.3)
    sign(c,'z+',-5.5,g-0.2,'sign_inn')
    lantern(c,'z+',-0.6,2.6); lantern(c,'z+',1.8,2.6)
    chimney(c,4.3,-1.6,1.1,1.6); chimney(c,-5.0,1.0,0.9,1.0)
    return c
def fh_(c): return c['fh']
def bakery():
    c=house(dict(W=10,D=8,g=3.2,floors=1,fh=2.8,jetty=0.35,pitch=57))
    cg=cross_gable(c,-1.8,4.6,pz=0.45,pitch=58); zf=cg['zf']; g,E=c['g'],c['E']
    base=lambda a,y:(np.array([a,y,zf]),np.array([1.0,0,0]),np.array([0,0,1.0]))
    door(c,'z+',-1.8,1.5,2.6)
    window(c,None,0,0,base=base(-2.8,g+0.8),flowers=True); window(c,None,0,0,base=base(-0.8,g+0.8),flowers=True)
    window(c,None,0,0,w=0.75,h=0.95,base=base(-1.8,E+0.5))
    window(c,'z+',2.6,0.9,1.6,1.3); window(c,'z+',2.6,g+0.8,flowers=True)
    dormer(c,2.6,1); dormer(c,0,-1)
    for a in(-3,0,3): window(c,'z-',a,1.0); window(c,'z-',a,g+0.8)
    for f in('x+','x-'): window(c,f,-1.5,1.0); window(c,f,1.5,g+0.8); window(c,f,0,E+0.6,0.7,1.0)
    sign(c,'z+',4.4,g-0.1,'sign_bread'); banner(c,'z+',0.6,g+2.0)
    lantern(c,'z+',-0.6,2.4)
    chimney(c,3.9,-1.4,1.3,1.8)   # tall oven chimney
    return c
def house1():
    c=house(dict(W=8.5,D=7,g=3.0,floors=1,fh=2.7,jetty=0.35,pitch=58))
    g,E=c['g'],c['E']
    # front is the gable end (+x before rotation)
    door(c,'x+',0.3,1.3,2.5)
    window(c,'x+',-2.0,1.0); window(c,'x+',2.0,1.0)
    window(c,'x+',-1.3,g+0.7,flowers=True); window(c,'x+',1.3,g+0.7,flowers=True); window(c,'x+',0,E+0.6,0.8,1.1)
    for f in('z+','z-'):
        for a in(-2.2,1.8): window(c,f,a,1.0); window(c,f,a,g+0.7)
    dormer(c,0.0,1); dormer(c,0.0,-1)
    window(c,'x-',0,1.0); window(c,'x-',0,g+0.7)
    banner(c,'x+',-3.3,g+2.0)
    chimney(c,-3.6,0.0,1.0,1.2)
    c['front_gable']=True; return c
SPECS={'inn':inn,'bakery':bakery,'house1':house1}
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
