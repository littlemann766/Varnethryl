# Batch 4 card2 buildings + shared helpers (cream ashlar, sculpted statues, gold tracery, rocks)
import numpy as np
import kit2, sculpt
from geo import Mesh, norm
from house import house, door, window, dormer, gable_fill, banner, sign, lantern, chimney, cross_gable, cloth, facepos
from kit2 import cyl, cone, crenels_line, crenels_ring, barrel, crate, pot_plant, steps, ivy, lean_to
from kit3 import tower, pinnacle, lancet, rose, rack
CREAM={'stone':'ashlar'}
UP=np.array([0,1.0,0])
STAT_TRIS=dict(lion=(3200,1400,500),robed=(600,260,90),rock=(420,180,70))
def statue(m,name,pos,scale=1.0,rot=0,strip='statue'):
    key='rock' if name.startswith('rock') else name
    V,F=sculpt.get(name,STAT_TRIS[key][kit2.Q]); m.sculpt(V,F,strip,pos,scale,rot)
def rock(m,pos,scale=1.0,rot=0,seed=0,sy=None):
    V,F=sculpt.get(f'rock{seed%4}',STAT_TRIS['rock'][kit2.Q]); V=V*np.array([1,(sy or 1.0),1]); m.sculpt(V,F,'rock',pos,scale,rot)
def _lod(m,v):
    o=m.LOD; m.LOD=v; return o
def glancet(m,p,t,n,w=0.9,h=2.6):
    """lancet window with gold tracery (mullion, transom, pointed head)"""
    lancet(m,p,t,n,w,h); p=np.asarray(p,float); t=np.asarray(t,float); n=np.asarray(n,float); o=_lod(m,1)
    m.obox(p+UP*(h/2+w*0.3)+n*0.07,t,UP,n,(0.07,h+w*0.6,0.05),'gold')
    for y in(h*0.45,h*0.9): m.obox(p+UP*y+n*0.07,t,UP,n,(w,0.06,0.05),'gold')
    ap=p+UP*(h+w*0.62)+n*0.07
    for s in(-1,1): m.beam(p+UP*h+t*s*w/2+n*0.07,ap,0.06,'gold')
    m.LOD=o
def gold_portal(m,p,t,n,w,h):
    p=np.asarray(p,float); t=np.asarray(t,float); n=np.asarray(n,float); o=_lod(m,1)
    for s in(-1,1): m.obox(p+t*s*(w/2+0.55)+UP*h/2+n*0.36,t,UP,n,(0.12,h+0.6,0.08),'gold')
    ap=p+UP*(h+1.4)+n*0.36
    for s in(-1,1): m.beam(p+t*s*(w/2+0.55)+UP*(h+0.3)+n*0.36,ap,0.12,'gold')
    m.LOD=o; pinnacle(m,ap-n*0.1-UP*0.1,1.3,0.28)
def gold_ring(m,c,t,n,r,seg=16):
    c=np.asarray(c,float); t=np.asarray(t,float); o=_lod(m,1)
    for i in range(seg):
        a0,a1=2*np.pi*i/seg,2*np.pi*(i+1)/seg
        m.beam(c+(t*np.cos(a0)+UP*np.sin(a0))*r,c+(t*np.cos(a1)+UP*np.sin(a1))*r,0.09,'gold')
    m.LOD=o
def cb(m,top,w,h,t=(1,0,0),n=(0,0,1)):
    t=np.asarray(t,float); n=np.asarray(n,float); top=np.asarray(top,float)
    m.beam(top-n*0.3,top+n*0.25,0.07,'iron'); m.beam(top+n*0.25-t*(w/2+0.1),top+n*0.25+t*(w/2+0.1),0.06,'iron')
    cloth(m,top+n*0.25-UP*0.04,t,n,w,h,'banner',0.05)
def sq_tower(m,c,w,h,roof_h=0,crenel=True,wins=2,face=(0,0,1)):
    c=np.asarray(c,float); m.box(c+[-w/2,0,-w/2],c+[w/2,h,w/2],'stone')
    m.box(c+[-w/2-0.12,0,-w/2-0.12],c+[w/2+0.12,0.6,w/2+0.12],'stone',0.3)
    if crenel:
        y=h; m.box(c+[-w/2-0.25,h-0.4,-w/2-0.25],c+[w/2+0.25,h,w/2+0.25],'stone',0.5)
        pts=[c+[-w/2-0.1,0,w/2+0.1],c+[w/2+0.1,0,w/2+0.1],c+[w/2+0.1,0,-w/2-0.1],c+[-w/2-0.1,0,-w/2-0.1]]
        for i in range(4): crenels_line(m,pts[i],pts[(i+1)%4],h-0.5,t=0.4)
    if roof_h: cone(m,c,w*0.62,h+(0.9 if crenel else 0),roof_h,'slate',8)
    f=np.asarray(face,float); t=np.cross(UP,f)
    for k in range(wins):
        y=2.8+k*(h-4)/max(1,wins); p=c+f*(w/2+0.03)+UP*y
        m.cell([p-t*0.35,p+t*0.35,p+t*0.35+UP*1.1,p-t*0.35+UP*1.1],'window',0.1,0.9,0.05,0.95)
def lean(m,k,axis=0,y0=0.0):
    P=np.array(m.P).reshape(-1,3); P[:,axis]+=np.maximum(P[:,1]-y0,0)*k; m.P=list(P)
def hay(m,c,s=1.0,rot=0):
    c=np.asarray(c,float); m.box(c+[-0.6*s,0,-0.4*s],c+[0.6*s,0.75*s,0.4*s],'plaster',0.7)
    for x in(-0.3,0.3): m.box(c+[x*s-0.03,-0.01,-0.42*s],c+[x*s+0.03,0.77*s,0.42*s],'beam')
def fence(m,a,b,h=1.1,post=2.0):
    a=np.asarray(a,float); b=np.asarray(b,float); L=np.linalg.norm(b-a); k=max(1,int(L/post))
    for i in range(k+1): q=a+(b-a)*i/k; m.box(q+[-0.08,0,-0.08],q+[0.08,h,0.08],'beam')
    for y in(h*0.45,h*0.9): m.beam(a+[0,y,0],b+[0,y,0],0.09,'oak')
def dummy(m,c):
    c=np.asarray(c,float); m.beam(c,c+[0,1.9,0],0.14,'beam'); m.beam(c+[-0.55,1.4,0],c+[0.55,1.4,0],0.1,'beam')
    cyl(m,c+[0,0.9,0],0.26,0,0.7,'plaster',8,cap='plaster'); m.blob(c+[0,1.85,0],0.2,'flowers',5) if False else cyl(m,c+[0,1.7,0],0.17,0,0.32,'plaster',6,cap='plaster')
def trough(m,c,L=2.0):
    c=np.asarray(c,float); m.box(c+[-L/2,0,-0.35],c+[L/2,0.6,0.35],'oak')
def dome(m,c,r,y0,rings=5,seg=16,strip='slate',ribs=True):
    c=np.asarray(c,float); rings=max(2,int(round(rings*(1,0.6,0.4)[kit2.Q])))
    for i in range(rings):
        a0,a1=np.pi/2*i/rings,np.pi/2*(i+1)/rings
        cyl(m,c,r*np.cos(a0),y0+r*np.sin(a0),y0+r*np.sin(a1),strip,seg,r1=max(0.02,r*np.cos(a1)))
    if ribs and kit2.Q<2:
        o=_lod(m,1)
        for k in range(8):
            ph=2*np.pi*k/8; d=np.array([np.cos(ph),0,np.sin(ph)])
            pts=[c+d*r*np.cos(a)*1.02+UP*(y0+r*np.sin(a)*1.02) for a in np.linspace(0,np.pi/2,5)]
            for p,q in zip(pts[:-1],pts[1:]): m.beam(p,q,0.12,'gold')
        m.LOD=o
    m.box(c+[-0.3,y0+r-0.1,-0.3],c+[0.3,y0+r+0.9,0.3],'stone'); cone(m,c,0.45,y0+r+0.9,1.2,'slate',8)

# ------------------------------------------------------------------ buildings
def library():
    c=house(dict(W=17,D=11,g=5.0,floors=1,fh=3.6,jetty=0.0,pitch=58,upper='stone',framing=False,remap=CREAM)); g,E=c['g'],c['E']; m=c['m']
    cg=cross_gable(c,0,7.4,pz=1.2,pitch=62,mat='stone',framed=False,attic=False); zf=cg['zf']
    t=np.array([1.0,0,0]); n=np.array([0,0,1.0])
    door(c,'z+',0,2.4,4.0); gold_portal(m,(0,0,zf),t,n,2.4,4.0)
    glancet(m,(0,5.4,zf),t,n,2.6,3.6); rose(m,(0,E+3.4,zf),t,n,1.3); gold_ring(m,(0,E+3.4,zf+0.2),t,n,1.5)
    for a in(-2.6,2.6): glancet(m,(a,1.4,zf),t,n,0.9,3.0); glancet(m,(a,5.8,zf),t,n,0.85,2.6)
    for a in(-1.9,1.9): banner(c,'z+',a,E+0.2,0.9,3.2)
    for a in(-5.6,5.6):
        glancet(m,(a,1.4,c['hs']),t,n,1.1,3.0); glancet(m,(a,5.6,c['hs']),t,n,1.0,2.6); banner(c,'z+',a+np.sign(a)*1.6,E-0.4,0.9,3.0)
    for a in(-3.75,3.75):   # turrets framing the entrance gable
        tower(m,(a,0,zf-0.3),0.85,cg['R2']-0.6,3.4,wins=3)
    pinnacle(m,(0,cg['R2']+0.1,zf+0.2),2.6)
    for x in(-7.5,7.5):
        for sz in(1,-1): tower(m,(x+np.sign(x)*0.6,0,sz*(c['D']/2+0.3)),0.75,E+1.2,3.0,wins=2)
    for a in(-3,0,3): dormer(c,a*1.6,-1,ww=1.1,wh=1.5)
    for a in(-5.5,5.5): dormer(c,a,1,ww=1.1,wh=1.5)
    for a in(-6,-2,2,6): glancet(m,(a,1.4,-c['hs']),-t,-n,1.0,3.0); glancet(m,(a,5.6,-c['hs']),-t,-n,1.0,2.6)
    for f in('x+','x-'):
        p,tt,nn=facepos(c,f,0,1.4)
        for a in(-2.6,2.6): glancet(m,p+tt*a,tt,nn,1.0,3.0); glancet(m,p+tt*a+UP*4.2,tt,nn,1.0,2.6)
        gable_fill(c,f)
    for sx in(-1,1):
        m.box((sx*3.4-0.5,0,zf+2.4),(sx*3.4+0.5,1.1,zf+3.4),'stone'); statue(m,'robed',(sx*3.4,1.1,zf+2.9),0.95,0)
    steps(m,(0,0,zf),(1,0,0),(0,0,1),5.4,k=5)
    for x in(-6.2,6.2): pot_plant(m,(x,0,c['hs']+0.6),0.45)
    lantern(c,'z+',-1.9,3.0); lantern(c,'z+',1.9,3.0)
    chimney(c,-6.4,-1.5,0.9,1.2)
    return c
def mage_academy():
    c=house(dict(W=15,D=11,g=5.0,floors=2,fh=3.2,jetty=0.0,pitch=63,upper='stone',framing=False,remap={'window':'bluewin'})); g,E,fh=c['g'],c['E'],c['fh']; m=c['m']
    t=np.array([1.0,0,0]); n=np.array([0,0,1.0]); hs=c['hs']
    # central great tower on the front with a tall blue spire, flanked by lesser spired towers
    tower(m,(0,0,hs+0.4),2.6,E+8.0,10.5,wins=5,cone_r=3.1)
    door(dict(m=m,hs=hs+0.4+2.6,D=0,g=0,X0=0,X1=0),'z+',0,2.2,3.6)
    for y in(6.0,10.5,15.0): glancet(m,(0,y,hs+0.4+2.62),t,n,1.0,2.4)
    cb(m,(0,E+5.4,hs+3.1),1.6,5.0)
    for sx in(-1,1):
        tower(m,(sx*5.2,0,hs+0.2),1.8,E+4.0,7.5,wins=4); cb(m,(sx*5.2,E+1.2,hs+2.05),1.1,3.6)
        tower(m,(sx*(c['W']/2+0.6),0,0.0),1.5,E+1.5,6.2,wins=3)
        tower(m,(sx*(c['W']/2-0.6),0,-hs-0.6),1.4,E+3.0,6.5,wins=3)
        for a in(sx*2.9,sx*7.3): glancet(m,(a,1.4,hs),t,n,1.0,3.0); glancet(m,(a,g+0.7,hs),t,n,0.9,2.3); glancet(m,(a,g+fh+0.6,hs),t,n,0.9,2.2)
        for z in(-2.5,2.5): pinnacle(m,(sx*(c['W']/2+0.1),c['Rh']-2.2,z*0.3),2.2)
    for a in(-4.5,0,4.5): dormer(c,a,1,ww=1.0,wh=1.6); dormer(c,a,-1,ww=1.0,wh=1.6)
    for x in np.linspace(-6,6,5): pinnacle(m,(x,c['Rh']+0.15,0),1.8)
    for a in(-5,-1.7,1.7,5): glancet(m,(a,1.4,-hs),-t,-n,1.0,3.0); glancet(m,(a,g+0.7,-hs),-t,-n,0.9,2.3)
    for f in('x+','x-'): gable_fill(c,f)
    for x in(-3.5,3.5): cb(m,(x,g+fh*2-0.3,hs+0.05),1.0,3.4)
    for sx in(-1,1):
        tower(m,(sx*2.7,0,hs+1.2),0.95,E+2.2,5.0,wins=3)                      # entrance turrets
        tower(m,(sx*3.6,c['Rh']-3.5,-0.5),0.85,4.6,4.2,wins=1)               # roofline spires
        tower(m,(sx*6.6,c['Rh']-5.0,-2.6),0.8,4.0,3.8,wins=1)
        cb(m,(sx*2.7,E-0.2,hs+2.2),0.9,3.0)
    tower(m,(0,c['Rh']-3.0,-2.8),1.1,5.5,5.5,wins=2)
    # crowd of spires: flank turrets, buttress spirelets, rear cluster
    for sx in(-1,1):
        for x,z,r,h,rh in((sx*4.4,hs+0.6,0.7,E+0.5,4.0),(sx*7.9,hs-1.5,0.75,E-1.0,4.2),(sx*7.9,-hs+1.0,0.75,E-0.5,4.4),(sx*1.6,-hs-0.8,0.9,E+4.5,5.6),(sx*4.5,-hs-1.6,1.0,E+2.0,5.2)):
            tower(m,(x,0,z),r,h,rh,wins=1)
        for z in(-3.0,0.0,3.0): pinnacle(m,(sx*(c['W']/2+0.15),E+0.2,z),2.4,0.4)
        for x in(1.3,3.9,6.5): pinnacle(m,(sx*x,E+0.2,hs+0.1),2.0,0.35)
    tower(m,(0,0,-hs-2.4),1.6,E+6.0,8.0,wins=3)
    steps(m,(0,0,hs+3.0),t,n,4.4,k=5)
    for x in(-2.8,2.8): pot_plant(m,(x,0,hs+3.6),0.45); lantern(dict(m=m,hs=hs+3.0,D=0,g=0,X0=0,X1=0),'z+',x*0.55,3.2)
    return c
def observatory():
    m=Mesh(); m.remap=dict(CREAM); t=np.array([1.0,0,0]); n=np.array([0,0,1.0])
    # rocky outcrop
    for i,(x,z,s,ry) in enumerate(((0,0,6.5,0),(4.5,3,3.6,40),(-4.8,2.5,3.4,110),(3,-4.8,3.8,200),(-3.5,-4,3.6,290),(0,5.2,3.0,70))):
        rock(m,(x,-0.5,z),s,ry,i,0.7)
    B=3.4; R=3.0
    m.box((-4.2,3.4,-4.2),(4.2,4.0,4.2),'stone'); cyl(m,(0,0,0),R+0.35,4.0,5.0,'stone',20)
    cyl(m,(0,0,0),R,5.0,20.0,'stone',20)
    for y in(9.6,14.6,19.6): cyl(m,(0,0,0),R+0.18,y,y+0.35,'stone',20)
    for k in range(8):        # pilasters with pinnacles
        a=2*np.pi*(k+0.5)/8; d=np.array([np.cos(a),0,np.sin(a)]); tt=np.cross(UP,d)
        m.obox(d*(R+0.15)+UP*12.5,tt,UP,d,(0.55,15,0.4),'stone'); pinnacle(m,d*(R+0.2)+UP*20.2,2.0,0.4)
        for y in(6.0,10.6,15.6):
            lancet(m,d*(R+0.0)+UP*y if False else (np.cos(a+np.pi/8)*R*1.0,y,np.sin(a+np.pi/8)*R*1.0),np.cross(UP,[np.cos(a+np.pi/8),0,np.sin(a+np.pi/8)]),(np.cos(a+np.pi/8),0,np.sin(a+np.pi/8)),0.7,2.3) if (k%2==0 or y>8) else None
    door(dict(m=m,hs=R+0.02,D=0,g=0,X0=0,X1=0),'z+',0,1.5,2.8); m.P=m.P  # entrance at base front
    p=np.array([0,5.0,R+0.05]); glancet(m,(0,5.0,R+0.05),t,n,1.2,2.4)
    steps(m,(0,3.95,4.2),t,n,2.6,k=4)
    # gallery + drum + dome + telescope
    cyl(m,(0,0,0),R+0.9,20.0,20.5,'stone',20,cap='stone'); crenels_ring(m,(0,0,0),R+0.6,20.3,n=14,h=0.7,t=0.3) if False else None
    for k in range(20):
        a=2*np.pi*k/20; m.beam((np.cos(a)*(R+0.8),20.5,np.sin(a)*(R+0.8)),(np.cos(a)*(R+0.8),21.4,np.sin(a)*(R+0.8)),0.07,'iron')
    cyl(m,(0,0,0),R+0.8,21.35,21.45,'iron',20)
    cyl(m,(0,0,0),R-0.4,20.5,23.0,'stone',20)
    for k in range(8):
        a=2*np.pi*k/8; d=np.array([np.cos(a),0,np.sin(a)]); p=d*(R-0.37)+UP*21.0; tt=np.cross(UP,d)
        m.cell([p-tt*0.35,p+tt*0.35,p+tt*0.35+UP*1.4,p-tt*0.35+UP*1.4],'window',0.1,0.9,0.05,0.95)
    cyl(m,(0,0,0),R-0.1,23.0,23.4,'stone',20)
    dome(m,(0,0,0),R-0.3,23.4,6,20)
    m.beam((0.6,24.2,-0.4),(-3.6,27.4,-2.2),0.55,'iron'); m.beam((-3.6,27.4,-2.2),(-4.1,27.8,-2.45),0.7,'gold')
    for x in(-2.6,2.6): lantern(dict(m=m,hs=R+0.35,D=0,g=0,X0=0,X1=0),'z+',x*0.5,6.5)
    return dict(m=m)
def treasury():
    m=Mesh(); t=np.array([1.0,0,0]); n=np.array([0,0,1.0])
    m.box((-6,0,-4),(6,10,4),'stone'); m.box((-6.15,0,-4.15),(6.15,0.7,4.15),'stone',0.3)
    for a,b in(((-6,0,4),(6,0,4)),((6,0,-4),(-6,0,-4)),((6,0,4),(6,0,-4)),((-6,0,-4),(-6,0,4))): crenels_line(m,a,b,10.0)
    m.box((-4,0,-9),(4,11,-3),'stone'); 
    for a,b in(((-4,0,-3),(4,0,-3)),((4,0,-9),(-4,0,-9)),((4,0,-3),(4,0,-9)),((-4,0,-9),(-4,0,-3))): crenels_line(m,a,b,11.0)
    for sx in(-1,1):
        sq_tower(m,(sx*6.2,0,4.0),4.0,15.0,6.0,True,3,(0,0,1)); cb(m,(sx*4.0,8.8,4.05),1.4,4.6)
        sq_tower(m,(sx*6.2,0,-4.5),3.4,12.5,0,True,2,(sx,0,0))
        for z in(-1.5,1.5): window(dict(m=m,hs=0,g=0,D=0,X0=-6,X1=6),'x+' if sx>0 else 'x-',z,6.0,0.7,1.2)
    # gate: arch voussoirs, oak doors, iron portcullis
    p=np.array([0,0,4.0]); b=p+n*0.03
    m.cell([b-t*1.8,b+t*1.8,b+t*1.8+UP*5.0,b-t*1.8+UP*5.0],'door')
    for k in range(11):
        th=np.pi*k/10; q=p+t*np.cos(th)*2.1+UP*(3.1+np.sin(th)*2.1)+n*0.2
        m.obox(q,t*np.cos(th+np.pi/2)+UP*np.sin(th+np.pi/2),-(t*np.cos(th)+UP*np.sin(th)),n,(0.5,0.6,0.45),'stone',k*0.1)
    for s_ in(-1,1): m.obox(p+t*s_*2.15+UP*1.55+n*0.2,t,UP,n,(0.5,3.1,0.45),'stone')
    o=_lod(m,1)
    for x in np.linspace(-1.6,1.6,8): m.box((x-0.05,0.3,4.12),(x+0.05,4.8,4.22),'iron')
    for y in(1.2,2.4,3.6): m.box((-1.7,y-0.05,4.12),(1.7,y+0.05,4.24),'iron')
    m.LOD=o
    pp=np.array([0,7.6,4.05]); m.obox(pp,t,UP,n,(1.6,1.9,0.14),'gold')
    m.cell([pp+[-0.7,-0.85,0.09],pp+[0.7,-0.85,0.09],pp+[0.7,0.85,0.09],pp+[-0.7,0.85,0.09]],'banner',0.08,0.92,0.12,0.85)
    for x in(-2.4,2.4): lantern(dict(m=m,hs=4.0,g=0,D=8,X0=0,X1=0),'z+',x,3.4)
    for x in(-3.2,3.2): m.box((x-0.12,0,4.3),(x+0.12,0.9,4.6),'stone')
    steps(m,(0,0,4.0),t,n,5.0,k=2)
    return dict(m=m)
def crypt():
    c=house(dict(W=8.5,D=6.4,g=5.2,floors=0,fh=1,jetty=0.0,pitch=62,upper='stone',framing=False,oh=0.35)); E=c['E']; m=c['m']; X1=c['X1']
    t=np.array([0,0,-1.0]); n=np.array([1.0,0,0])
    # gothic front (+x): pointed door in a deep traceried portal, buttress piers with pinnacles
    door(c,'x+',0,1.9,3.4)
    o=_lod(m,1)
    for s in(-1,1): m.beam((X1+0.45,3.4,s*1.3),(X1+0.45,5.4,0),0.36,'stone')
    m.LOD=o
    glancet(m,(X1+0.02,E+0.5,0),t,n,1.1,1.6)
    for sz in(-1,1):
        m.box((X1-0.3,0,sz*2.6-0.45),(X1+0.6,E+0.9,sz*2.6+0.45),'stone',sz*0.2); pinnacle(m,(X1+0.15,E+0.9,sz*2.6),2.6,0.55)
        m.box((X1-0.3,0,sz*3.25-0.35),(X1+0.3,E-1,sz*3.25+0.35),'stone')
        for x in(-2.5,0.5): glancet(m,(x,1.6,sz*3.2),np.array([sz*1.0,0,0]),np.array([0,0,sz*1.0]),0.8,2.4)
        for x in(-1,2.2): m.box((x-0.3,0,sz*3.2-0.2 if sz>0 else -3.6),(x+0.3,3.4,sz*3.6 if sz>0 else -3.0),'stone')
    for z in(-1.2,1.2): lantern(dict(m=m,hs=0,g=0,D=0,X0=0,X1=X1),'x+',z*1.2,2.6)
    rose(m,(X1+0.02,E+2.6,0),t,n,0.75,12); gold_ring(m,(X1+0.2,E+2.6,0),t,n,0.85,12)
    for sz in(-1,1):
        z=sz*1.75; m.box((X1-0.1,0.4,z-0.42),(X1+0.35,0.6,z+0.42),'stone'); statue(m,'robed',(X1+0.15,0.6,z),0.85,90)
        o=_lod(m,1)
        for s in(-1,1): m.beam((X1+0.3,2.5,z-0.4),(X1+0.3,3.1,z),0.12,'stone') if s<0 else m.beam((X1+0.3,2.5,z+0.4),(X1+0.3,3.1,z),0.12,'stone')
        m.LOD=o
        q=np.array([X1+0.62,E-0.6,sz*2.6]); m.cell([q+[0,0,-0.3],q+[0,0,0.3],q+[0,1.6,0.3],q+[0,1.6,-0.3]],'banner',0.2,0.8,0.2,0.8)
    pinnacle(m,(X1+0.3,c['Rh']+0.1,0),2.6,0.4)
    pinnacle(m,(c['X0']-0.2,c['Rh']+0.1,0),2.0,0.35)
    # mound of mossy rock around the back, stair up the front
    for i,(x,z,s,ry) in enumerate(((-4.5,-3.5,2.4,0),(-5.2,1.8,2.6,80),(-1.5,-4.6,2.2,160),(1.8,4.4,1.9,240),(-2.5,4.2,2.3,300),(5.8,3.8,1.6,30),(5.6,-3.6,1.7,120))):
        rock(m,(x,-0.2,z),s,ry,i,0.9)
    steps(m,(X1+1.3,0,0),t,n,3.2,k=4)
    ivy(m,[(c['X0']-0.1,y,z) for z in(-2.5,0.6,2.2) for y in np.arange(0.3,4.4,0.5)],0.3)
    c['front_gable']=True; return c
def lighthouse():
    m=Mesh(); t=np.array([1.0,0,0]); n=np.array([0,0,1.0])
    for i,(x,z,s,ry,sy) in enumerate(((0,0,7.5,0,0.8),(6,3.5,4.4,40,1),(-5.8,3,4.6,110,0.9),(3.5,-6,5.0,200,1),(-5,-5,4.8,290,0.9),(1,7,3.6,70,0.8),(-8.5,0,3.4,20,1),(8,-2,3.6,150,0.8))):
        rock(m,(x,-0.8,z),s,ry,i,sy)
    B=4.2
    cyl(m,(0,0,0),3.3,B-0.6,B+0.6,'stone',16,cap='stone')
    cyl(m,(0,0,0),3.3,B+0.6,B+13.0,'stone',18,r1=2.6)
    cyl(m,(0,0,0),2.6,B+13.0,B+13.7,'stone',18,r1=3.1)     # corbel
    Y=B+13.7; cyl(m,(0,0,0),3.2,Y,Y+0.25,'stone',18,cap='stone')
    for k in range(18):
        a=2*np.pi*k/18; m.beam((3.1*np.cos(a),Y+0.25,3.1*np.sin(a)),(3.1*np.cos(a),Y+1.2,3.1*np.sin(a)),0.06,'iron')
    cyl(m,(0,0,0),3.1,Y+1.15,Y+1.25,'iron',18)
    for k in range(8):   # lantern room: glowing glazing between iron mullions
        a0,a1=2*np.pi*k/8,2*np.pi*(k+1)/8; r=1.9
        p0=np.array([r*np.cos(a0),Y+0.4,r*np.sin(a0)]); p1=np.array([r*np.cos(a1),Y+0.4,r*np.sin(a1)])
        m.cell([p1,p0,p0+UP*2.0,p1+UP*2.0],'window',0.12,0.88,0.05,0.95); m.beam(p0,p0+UP*2.1,0.1,'iron')
    cyl(m,(0,0,0),1.95,Y+0.25,Y+0.4,'iron',8); cyl(m,(0,0,0),2.2,Y+2.4,Y+2.6,'iron',8)
    cone(m,(0,0,0),2.45,Y+2.6,3.4,'slate',12)
    door(dict(m=m,hs=2.68,D=0,g=0,X0=0,X1=0),'z+',0,1.3,2.4) if False else None
    p=np.array([0,B+0.6,3.28]); m.cell([p-t*0.65,p+t*0.65,p+t*0.65+UP*2.4,p-t*0.65+UP*2.4],'door')
    for k in range(7):
        th=np.pi*k/6; q=p+t*np.cos(th)*0.8+UP*(1.75+np.sin(th)*0.8)+n*0.12
        m.obox(q,t*np.cos(th+np.pi/2)+UP*np.sin(th+np.pi/2),-(t*np.cos(th)+UP*np.sin(th)),n,(0.3,0.32,0.3),'stone')
    for y,a in((B+4.8,0.3),(B+8.2,-0.5),(B+11.0,0.9)):
        r=3.3-(y-B-0.6)/12.4*0.7; d=np.array([np.sin(a),0,np.cos(a)]); tt=np.cross(UP,d); q=d*(r+0.02)+UP*y
        m.cell([q-tt*0.35,q+tt*0.35,q+tt*0.35+UP*1.0,q-tt*0.35+UP*1.0],'window',0.1,0.9,0.05,0.95)
    # timber stair zig-zag up the rocks on the right + keeper's lean-to
    pts=[(8.5,0.3,4.5),(6.0,2.2,4.5),(5.6,2.2,5.6),(3.0,B-0.6,4.6)]
    for a,b in zip(pts[:-1],pts[1:]):
        a=np.array(a);b=np.array(b); d=b-a; L=np.linalg.norm(d[[0,2]]); k=max(2,int(L/0.35))
        for i in range(k):
            q=a+d*(i+0.5)/k; m.box(q+[-0.5,-0.06,-0.5],q+[0.5,0.06,0.5],'oak') if d[1]!=0 else m.box(q+[-0.55,-0.06,-0.55],q+[0.55,0.06,0.55],'oak')
        for s in(-0.55,0.55):
            off=np.array([0,0,s]) if abs(d[0])>abs(d[2]) else np.array([s,0,0]); m.beam(a+off+UP*1.0,b+off+UP*1.0,0.07,'beam')
            m.beam(a+off,a+off+UP*1.05,0.1,'beam')
    m.box((-3.4,B-0.6,-0.8),(-1.8,B+2.2,1.6),'stone'); m.box((-3.6,B+2.2,-1.0),(-1.6,B+2.45,1.8),'slate')
    return dict(m=m)
def windmill():
    m=Mesh(); t=np.array([1.0,0,0]); n=np.array([0,0,1.0])
    cyl(m,(0,0,0),3.5,0,0.5,'stone',8,cap=None); cyl(m,(0,0,0),3.3,0.5,3.4,'stone',8,r1=3.1)
    cyl(m,(0,0,0),3.15,3.4,3.7,'beam',8,r1=3.15)
    cyl(m,(0,0,0),3.0,3.7,10.0,'plaster',8,r1=2.25)
    # timber framing on each octagon face
    o=_lod(m,1)
    for k in range(8):
        a=2*np.pi*k/8; a1=2*np.pi*(k+1)/8
        P=lambda r,y,aa:np.array([r*np.cos(aa),y,r*np.sin(aa)])
        m.beam(P(3.02,3.7,a),P(2.27,10.0,a),0.2)
        m.beam(P(3.02,3.7,a),P(2.66,6.85,a1)*1.0,0.14)
        m.beam(P(2.66,6.85,a),P(2.66,6.85,a1),0.16)
    m.LOD=o
    cyl(m,(0,0,0),2.5,10.0,10.4,'beam',8); cyl(m,(0,0,0),3.25,3.55,3.75,'slate',8)
    cone(m,(0,0,0),2.85,10.4,3.6,'slate',12)
    # door, windows
    p=np.array([0,0.0,3.25]); m.cell([p-t*0.65,p+t*0.65,p+t*0.65+UP*2.4,p-t*0.65+UP*2.4],'door')
    for y,a in((5.0,0.0),(7.6,0.0),(5.4,2.3),(5.4,-2.3),(8.0,np.pi)):
        r=3.0-(y-3.7)/6.3*0.75; d=np.array([np.sin(a),0,np.cos(a)]); tt=np.cross(UP,d); q=d*(r*0.93+0.05)+UP*y
        m.cell([q-tt*0.45,q+tt*0.45,q+tt*0.45+UP*1.1,q-tt*0.45+UP*1.1],'window',0.05,0.95,0.03,0.97)
    # sails: hub on the front, 4 lattice arms
    hub=np.array([0,10.4,2.85]); m.beam(hub-n*1.2,hub+n*0.5,0.45,'beam'); m.obox(hub+n*0.55,t,UP,n,(0.7,0.7,0.3),'iron')
    for k in range(4):
        a=np.pi/4+k*np.pi/2; d=np.array([np.cos(a),np.sin(a),0]); s=np.array([-np.sin(a),np.cos(a),0])
        tip=hub+n*0.6+d*8.0; m.beam(hub+n*0.6,tip,0.22,'beam')
        o=_lod(m,1)
        m.beam(hub+n*0.6+d*1.4+s*1.25,tip+s*1.25,0.09,'beam')
        for r in np.linspace(1.4,8.0,12 if kit2.Q==0 else 6): m.beam(hub+n*0.62+d*r,hub+n*0.62+d*r+s*1.3,0.07,'beam')
        m.LOD=o
        q=hub+n*0.55
        for r in np.linspace(1.6,7.6,4 if kit2.Q==0 else 2): m.beam(hub+n*0.58+d*r,hub+n*0.58+d*(r+0.9)+s*1.25,0.04,'beam')
    for x,z in((2.8,2.6),(3.3,1.6)): barrel(m,(x,0,z))
    for x,z in((-2.9,2.8),(-3.6,2.0)): crate(m,(x,0,z),0.6)
    fence(m,(-7,0,6),(7,0,6)); steps(m,(0,0,3.3),t,n,1.8,k=2)
    return dict(m=m)
def stables():
    c=house(dict(W=13,D=8,g=3.6,floors=1,fh=1.6,jetty=0.2,pitch=50,oh=0.8)); g,E=c['g'],c['E']; m=c['m']; X1=c['X1']
    t=np.array([0,0,-1.0]); n=np.array([1.0,0,0]); hs=c['hs']
    # big open doorway in the gable end (+x), loft door above, banners
    p=np.array([X1+0.02,0,0]); m.box((X1-0.05,0,-1.6),(X1+0.05,3.3,1.6),'beam')
    m.cell([p+[0,0,1.5],p+[0,0,-1.5],p+[0,3.2,-1.5],p+[0,3.2,1.5]],'door',0.2,0.8,0.0,0.5)
    for s in(-1,1):
        m.box((X1-0.1,0,s*1.75-0.15),(X1+0.25,3.5,s*1.75+0.15),'beam')
        m.obox((X1+0.9,1.55,s*2.4),(0,0,1),UP,(1,0,0),(1.4,3.1,0.1),'oak')   # swung doors
        banner(c,'x+',s*-2.9,g+1.4,0.9,2.2)
    m.box((X1-0.1,3.4,-1.9),(X1+0.3,3.6,1.9),'beam')
    window(c,'x+',0,E+0.4,1.3,1.4); gable_fill(c,'x-')
    # stalls along the long side (+z): half doors between posts, horse heads peeking
    for x in np.arange(-5.2,5.3,2.1):
        m.box((x-0.12,0,hs+0.05),(x+0.12,g,hs+0.3),'beam')
        if x<5.2: m.obox((x+1.05,0.65,hs+0.18),(1,0,0),UP,(0,0,1),(1.7,1.3,0.12),'oak')
    for x in(-4.15,-0.0,4.15):
        V,F=sculpt.get('rock0',60) if False else (None,None)
    for x in(-4.15,0.0,4.15):
        q=np.array([x,1.55,hs+0.4]); m.obox(q+[0,0.05,0.35],(1,0,0),UP,(0,0,1),(0.32,0.45,0.75),'beam'); m.obox(q+[0,0.35,-0.05],(1,0,0),UP,(0,0,1),(0.34,0.6,0.5),'beam')
    for a in(-2.1,2.1): window(c,'z-',a*2,1.0,1.1,1.2)
    for f in('z+','z-'):
        for a in(-4.2,0,4.2): window(c,f,a,g+0.15,0.9,0.9)
    # cupola on ridge
    m.box((-0.8,c['Rh']-0.4,-0.8),(0.8,c['Rh']+1.2,0.8),'plaster'); cone(m,(0,0,0),1.25,c['Rh']+1.2,1.6,'slate',4)
    for x,z in((X1+1.4,-3.6),(X1+2.2,-3.0),(X1+1.0,3.4)): hay(m,(x,0,z))
    for x,z in((X1+1.6,3.9),(X1+2.4,4.4)): barrel(m,(x,0,z))
    trough(m,(1.0,0,hs+1.4),2.4); fence(m,(X1+4,0,-4.5),(X1+4,0,4.5))
    lantern(c,'x+',-1.95,2.8)
    c['front_gable']=True; return c
def farmhouse():
    c=house(dict(W=13,D=8,g=3.2,floors=1,fh=2.6,jetty=0.3,pitch=55)); g,E=c['g'],c['E']; m=c['m']
    cgs=[cross_gable(c,x,3.8,pz=0.5,pitch=58) for x in(-3.6,3.6)]; zf=cgs[0]['zf']
    door(c,'z+',0,1.3,2.5)
    # small porch gable over the door
    m.box((-1.1,2.6,c['D']/2),(1.1,2.75,c['D']/2+1.1),'beam')
    for s in(-1,1):
        m.box((s*1.0-0.08,0,c['D']/2+0.95),(s*1.0+0.08,2.6,c['D']/2+1.1),'beam')
        m.poly([(0,3.5,c['D']/2-0.1),(0,3.5,c['D']/2+1.3),(s*1.35,2.65,c['D']/2+1.3),(s*1.35,2.65,c['D']/2-0.1)][::(1 if s<0 else -1)],(0,3.5,c['D']/2),(0,0,1) if s<0 else (0,0,-1),(s*-1,0.6,0),'slate')
    for x in(-3.6,3.6):
        window(c,'z+',x,0.9,1.4,1.6); 
    window(c,'z+',-1.9,g+0.5,1.0,1.4,flowers=True); window(c,'z+',1.9,g+0.5,1.0,1.4,flowers=True)
    for a in(-4.2,-1.4,1.4,4.2): window(c,'z-',a,0.9); window(c,'z-',a,g+0.5)
    for f in('x+','x-'): window(c,f,-1.6,0.9); window(c,f,1.6,0.9); gable_fill(c,f)
    chimney(c,-6.0,0.0,1.1,1.4); chimney(c,1.8,-1.4,1.0,1.2)
    steps(m,(0,0,c['D']/2+1.1),(1,0,0),(0,0,1),2.0,k=2)
    for x in(-5.6,5.6): pot_plant(m,(x,0,c['D']/2+0.6),0.4)
    fence(m,(-8,0,7),(-1.5,0,7)); fence(m,(1.5,0,7),(8,0,7))
    lantern(c,'z+',-0.95,2.3)
    return c
def barn():
    c=house(dict(W=13,D=10,g=2.2,floors=1,fh=3.8,jetty=0.0,pitch=52,upper='oak',oh=0.7)); g,E=c['g'],c['E']; m=c['m']; X1=c['X1']; hs=c['hs']
    t=np.array([0,0,-1.0]); n=np.array([1.0,0,0])
    # big double barn doors on the gable end (+x), one swung open showing hay
    m.cell([np.array([X1+0.02,0,1.8]),np.array([X1+0.02,0,-1.8]),np.array([X1+0.02,4.2,-1.8]),np.array([X1+0.02,4.2,1.8])],'door',0.2,0.8,0.0,0.45)
    m.box((X1-0.1,4.2,-2.1),(X1+0.25,4.45,2.1),'beam')
    for s in(-1,1): m.box((X1-0.1,0,s*1.95-0.15),(X1+0.25,4.3,s*1.95+0.15),'beam')
    m.obox((X1+0.12,2.1,0.9),(0,0,1),UP,(1,0,0),(1.8,4.1,0.12),'oak'); m.beam((X1+0.2,0.3,1.8),(X1+0.2,4.0,0.0),0.14)
    m.obox((X1+0.9,2.1,-2.6),(1,0,0),UP,(0,0,1),(1.7,4.1,0.12),'oak')
    for k in range(3): hay(m,(X1-0.9,k*0.76,-0.8+0.0*k),1.0)
    window(c,'x+',0,E+0.2,1.4,1.6); m.box((X1,E+2.3,-0.1),(X1+1.0,E+2.45,0.1),'beam')
    gable_fill(c,'x-')
    for f in('z+','z-'):
        for a in(-4.2,0,4.2): window(c,f,a,2.2,1.1,1.3)
    lean_to(m,-5.0,3.0,hs,3.0,3.2,2.0)
    for x,z in((X1+1.5,3.6),(X1+2.3,3.0),(X1+1.6,-4.2)): hay(m,(x,0,z))
    for z in(-4.5,4.6): barrel(m,(X1+1.0,0,z))
    cyl(m,(0,0,0),0.01,0,0.01,'stone',6)
    m.box((-1.0,c['Rh']-0.3,-1.0),(1.0,c['Rh']+1.0,1.0),'oak'); cone(m,(0,0,0),1.5,c['Rh']+1.0,1.4,'slate',4)
    fence(m,(X1+4,0,-6),(X1+4,0,6)); fence(m,(-7.5,0,7.5),(X1+4,0,7.5))
    c['front_gable']=True; return c
def training_hall():
    c=house(dict(W=15,D=10,g=3.4,floors=1,fh=3.2,jetty=0.4,pitch=46,upper='stone',framing=False)); g,E=c['g'],c['E']; m=c['m']; X1=c['X1']
    t=np.array([0,0,-1.0]); n=np.array([1.0,0,0])
    door(c,'x+',0,2.6,3.4)
    for a in(-3.0,3.0): window(c,'x+',a,1.0,1.1,1.6); banner(c,'x+',a,g+2.2,1.0,2.4)
    window(c,'x+',-1.6,g+0.5,1.0,1.5); window(c,'x+',1.6,g+0.5,1.0,1.5)
    # guild lion crest in the gable
    p,tt,nn=facepos(c,'x+',0,E+1.0); m.obox(p+nn*0.1+UP*0.4,tt,UP,nn,(1.6,1.9,0.14),'gold')
    m.cell([p+nn*0.18-tt*0.7-UP*0.45,p+nn*0.18+tt*0.7-UP*0.45,p+nn*0.18+tt*0.7+UP*1.25,p+nn*0.18-tt*0.7+UP*1.25],'banner',0.08,0.92,0.12,0.85)
    window(c,'x+',0,E+2.45,0.6,0.75)
    o=_lod(m,1); hs=c['hs']
    for s_ in(-1,1): m.beam(p+tt*s_*hs*0.9+nn*0.07,p+tt*s_*hs*0.3+nn*0.07+UP*hs*0.6*np.tan(c['pit']),0.14)
    m.LOD=o
    for f in('z+','z-'):
        for a in(-5,-1.7,1.7,5): window(c,f,a,1.0); window(c,f,a,g+0.6)
    gable_fill(c,'x-'); dormer(c,-3,1); dormer(c,3,1); dormer(c,0,-1)
    chimney(c,-5.5,-1.8,1.0,1.2)
    for z in(-3.5,3.5): pinnacle(m,(X1+0.2,E+0.1,z*1.25),1.6)
    # yard: fence, training dummies, weapon racks, barrels, side stair
    fence(m,(X1+0.5,0,6.5),(X1+8,0,6.5)); fence(m,(X1+8,0,6.5),(X1+8,0,-6.5)); fence(m,(X1+0.5,0,-6.5),(X1+8,0,-6.5))
    for z in(-4.2,4.2): dummy(m,(X1+5.5,0,z)); dummy(m,(X1+3.6,0,z*1.25))
    for z in(-3.4,3.4): rack(m,(X1+0.05,0,z*1.5),(0,0,-1),(1,0,0),1.3,1.9)
    for x,z in((X1+1.2,-5.5),(X1+1.9,-5.9)): barrel(m,(x,0,z))
    for k in range(9): m.box((-3.0+k*0.4,k*0.38,c['D']/2+0.3),(-2.6+k*0.4,k*0.38+0.38,c['D']/2+1.5),'stone')
    steps(m,(X1+0.4,0,0),t,n,3.6,k=2)
    c['front_gable']=True; return c
def thieves_den():
    c=house(dict(W=7,D=5.4,g=3.0,floors=3,fh=2.6,jetty=0.5,pitch=63)); g,E,fh=c['g'],c['E'],c['fh']; m=c['m']; X1=c['X1']
    door(c,'x+',0.5,1.3,2.5); window(c,'x+',-1.9,1.0,0.9,1.2)
    for f_ in range(3):
        for a in(-1.4,1.4): window(c,'x+',a,g+f_*fh+0.5,0.9,1.4)
    gable_fill(c,'x+'); gable_fill(c,'x-')
    p,tt,nn=facepos(c,'x+',0,g-0.35)
    m.obox(p+nn*0.14,tt,UP,nn,(3.4,0.6,0.1),'beam'); m.cell([p+nn*0.2-tt*1.55-UP*0.24,p+nn*0.2+tt*1.55-UP*0.24,p+nn*0.2+tt*1.55+UP*0.24,p+nn*0.2-tt*1.55+UP*0.24],'banner',0.08,0.92,0.42,0.52)
    for a in(-2.1,2.1): banner(c,'x+',a,g+fh+1.2,0.7,2.0)
    sign(c,'x+',2.6,g+0.2,'sign_potion',0.7,0.7); lantern(c,'x+',-0.6,2.6); lantern(c,'x+',1.6,2.6)
    for f in('z+','z-'):
        for f_ in range(3): window(c,f,0,g+f_*fh+0.5,0.9,1.3)
    dormer(c,0,1,ww=0.9,wh=1.2); chimney(c,-2.4,1.4,0.8,1.6)
    lean(m,0.025,2,3.0)
    # crooked neighbours forming the alley
    for sz,dz,sp in((1,7.2,dict(W=6.5,D=6.2,g=3.0,floors=2,fh=2.6,jetty=0.5,pitch=60)),(-1,-7.0,dict(W=6.8,D=6.0,g=3.0,floors=2,fh=2.5,jetty=0.5,pitch=62))):
        h=house(sp); door(h,'x+',0.0,1.2,2.4)
        for f_ in range(2):
            for a in(-1.3,1.3): window(h,'x+',a,h['g']+f_*h['fh']+0.5,0.9,1.3)
        gable_fill(h,'x+'); chimney(h,1.6,-1.0,0.8,1.3); lean(h['m'],-0.03*sz,2,3.0)
        m.merge(h['m'],(-0.8,0,dz))
    for s in(-1,1): m.box((-2.0,0,s*3.0-0.25),(X1-1.2,c['E']+0.6,s*3.0+0.25),'stone',s)   # recessed party walls: den front stands proud like the card alley
    for z in(-2.9,3.2): barrel(m,(X1+0.6,0,z)); crate(m,(X1+1.2,0,z*0.9),0.6)
    c['front_gable']=True; return c
def colosseum():
    m=Mesh(); m.remap=dict(CREAM,window='iron'); A,B=26.0,21.0; N=28 if kit2.Q==0 else (20 if kit2.Q==1 else 14); tiers=[(0,6.5),(6.5,12.5),(12.5,18.0)]
    P=lambda th,s=1.0,y=0:np.array([A*s*np.cos(th),y,B*s*np.sin(th)])
    for i in range(N):
        a0,a1=2*np.pi*i/N,2*np.pi*(i+1)/N; am=(a0+a1)/2
        p0,p1=P(a0),P(a1); d=p1-p0; L=np.linalg.norm(d); tt=d/L; nn=np.cross(tt,UP); nn=-nn if np.dot(nn,P(am))<0 else nn
        for ti,(y0,y1) in enumerate(tiers):
            # piers at segment ends, arch over the opening, solid spandrel + cornice band
            w=0.9; m.obox(p0+UP*(y0+y1)/2,tt,UP,nn,(w,y1-y0,1.4),'stone',i*0.1)
            ah=(y1-y0)*0.66; r=(L-w)/2
            m.obox((p0+p1)/2+UP*(y0+ah+(y1-y0-ah)/2+0.15),tt,UP,nn,(L,y1-y0-ah-0.3,1.0),'stone',i*0.13)
            if kit2.Q==0:
                for k in range(1,4):
                    th=np.pi*k/4; q=(p0+p1)/2+tt*np.cos(th)*r*0.98+UP*(y0+ah-r*0.55+np.sin(th)*r*0.6)
                    m.obox(q,tt,UP,nn,(L*0.3,0.4,1.0),'stone',k*0.2)
            m.obox((p0+p1)/2+UP*(y1-0.15)+nn*0.12,tt,UP,nn,(L+0.1,0.3,1.4),'stone',0.5)
            if ti==0 and i%9==0:
                m.cell([p0+tt*0.5+nn*0.05,p1-tt*0.5+nn*0.05,p1-tt*0.5+nn*0.05+UP*4.0,p0+tt*0.5+nn*0.05+UP*4.0],'door',0.05,0.95,0.0,0.8)
        m.obox((p0+p1)/2+UP*19.0,tt,UP,nn,(L,2.0,1.2),'stone',i*0.1)   # attic
        if i%3==0 and kit2.Q<2:
            m.beam(p0+UP*20.0,p0+UP*23.0,0.1,'iron'); cloth(m,p0+UP*22.6+nn*0.3,tt,nn,1.3,2.6,'banner',0.05)
        if i%3==1: cb(m,(p0+p1)/2+UP*12.0+nn*0.75,2.6,7.0,tt,nn)
        # inner back wall (dark recess behind the arcades) + seating tiers
        q0,q1=P(a0,0.92),P(a1,0.92); m.obox((q0+q1)/2+UP*9.5,q1-q0,UP,np.cross(q1-q0,UP),(np.linalg.norm(q1-q0),19,0.5),'rock')
        for k in range(7 if kit2.Q==0 else 4):
            s=0.9-k*0.065 if kit2.Q==0 else 0.9-k*0.11; h=16.0-k*(14.0/(7 if kit2.Q==0 else 4))
            r0,r1=P(a0,s),P(a1,s); dd=r1-r0
            m.obox((r0+r1)/2+UP*(h-0.45),dd,UP,np.cross(dd,UP),(np.linalg.norm(dd)+0.05,0.9,A*0.07),'stone',k*0.3)
    rings=6 if kit2.Q==0 else (4 if kit2.Q==1 else 3); Hd=8.5; y0=20.0; sA,sB=0.93,0.93
    for j in range(rings):
        e0,e1=np.pi/2*j/rings,np.pi/2*(j+1)/rings
        for i in range(N):
            a0,a1=2*np.pi*i/N,2*np.pi*(i+1)/N
            Q=lambda a,e:np.array([A*sA*np.cos(e)*np.cos(a),y0+Hd*np.sin(e),B*sB*np.cos(e)*np.sin(a)])
            pts=[Q(a0,e0),Q(a1,e0),Q(a1,e1),Q(a0,e1)]
            if j==rings-1: pts=pts[:3]
            m.poly(pts[::-1],pts[0],pts[1]-pts[0],(pts[-1]-pts[0]),'slate')
    if kit2.Q<2:
        o=_lod(m,1)
        for i in range(0,N,3):
            a=2*np.pi*i/N; pts=[np.array([A*sA*np.cos(e)*np.cos(a)*1.005,y0+Hd*np.sin(e)*1.01,B*sB*np.cos(e)*np.sin(a)*1.005]) for e in np.linspace(0,np.pi/2,6)]
            for p_,q_ in zip(pts[:-1],pts[1:]): m.beam(p_,q_,0.22,'gold')
        m.LOD=o
    cyl(m,(0,0,0),2.2,y0+Hd-0.2,y0+Hd+2.2,'stone',8); cone(m,(0,0,0),2.8,y0+Hd+2.2,3.0,'slate',8)
    # arena sand floor
    for i in range(N):
        a0,a1=2*np.pi*i/N,2*np.pi*(i+1)/N; r=0.48
        m.poly([P(a0,r,0.6),P(a1,r,0.6),np.array([0,0.6,0])][::-1],np.array([0,0.6,0]),(1,0,0),(0,0,-1),'plaster')
    steps(m,(0,0,B+0.7),(1,0,0),(0,0,1),8,k=3)
    return dict(m=m)
