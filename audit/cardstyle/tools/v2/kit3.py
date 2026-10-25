import numpy as np
from geo import norm
import kit2
from kit2 import cyl,cone,crenels_ring,crenels_line,barrel,crate,pot_plant,steps,ivy
def tower(m,c,r,h,roof_h=None,crenel=False,wins=3,cone_r=None,banner_dir=None):
    c=np.asarray(c,float); cyl(m,c,r,0,h,'stone',18)
    cyl(m,c,r+0.12,0,0.6,'stone',18)  # plinth
    if crenel: crenels_ring(m,c,r,h-0.2,n=10); top=h+1.4
    else:
        if kit2.Q<2: cyl(m,c+[0,h-0.5,0],r,0,0.5,'stone',18,r1=r+0.3)  # corbel ring
        top=h
    if roof_h: cone(m,c+[0,0,0],(cone_r or r+0.45),top,roof_h)
    if kit2.Q>=1: wins=min(wins,2) if kit2.Q==1 else min(wins,1)
    for k in range(wins):
        y=2.5+k*(h-3)/max(1,wins)
        a=np.pi/2+(k%2)*0.6; n=np.array([np.cos(a),0,np.sin(a)]); t=np.array([-np.sin(a),0,np.cos(a)])
        p=c+n*(r+0.03)+[0,y,0]; up=np.array([0,1.0,0])
        m.cell([p+t*0.3,p-t*0.3,p-t*0.3+up*1.0,p+t*0.3+up*1.0],'window',0.1,0.9,0.05,0.95)
        m.obox(p+up*1.05+n*0.08,t,up,n,(0.8,0.15,0.2),'stone')
    return top+(roof_h or 0)
def pinnacle(m,p,h=1.6,w=0.35):
    p=np.asarray(p,float); m.box(p+[-w/2,0,-w/2],p+[w/2,h*0.45,w/2],'stone'); cone(m,p,w*0.75,h*0.45,h*0.55,'slate',6 if kit2.Q<2 else 4)
def lancet(m,p,t,n,w=0.9,h=2.6):
    t=np.asarray(t,float); n=np.asarray(n,float); p=np.asarray(p,float); up=np.array([0,1.0,0]); b=p+n*0.03
    m.cell([b-t*w/2,b+t*w/2,b+t*w/2+up*h,b-t*w/2+up*h],'window')
    for s in(-1,1): m.obox(p+t*s*(w/2+0.12)+up*h/2+n*0.15,t,up,n,(0.24,h,0.3),'stone')
    for k in range(5):
        th=np.pi*k/4; q=p+up*h+t*np.cos(th)*(w/2+0.12)+up*np.sin(th)*(w*0.7)+n*0.15
        m.obox(q,t,up,n,(0.3,0.3,0.3),'stone',k*0.2)
def rose(m,p,t,n,r=1.4,seg=16):
    t=np.asarray(t,float); n=np.asarray(n,float); p=np.asarray(p,float); up=np.array([0,1.0,0])
    for i in range(seg):
        a0=2*np.pi*i/seg; a1=2*np.pi*(i+1)/seg
        q0=p+(t*np.cos(a0)+up*np.sin(a0))*r+n*0.03; q1=p+(t*np.cos(a1)+up*np.sin(a1))*r+n*0.03
        m.cell([p+n*0.03,p+n*0.03,q1,q0],'window',0.2,0.8,0.1,0.9)
        mid=p+(t*np.cos((a0+a1)/2)+up*np.sin((a0+a1)/2))*(r+0.15)+n*0.15
        m.obox(mid,t*np.cos((a0+a1)/2+np.pi/2)+up*np.sin((a0+a1)/2+np.pi/2),t*np.cos((a0+a1)/2)+up*np.sin((a0+a1)/2),n,(2*np.pi*r/seg+0.05,0.3,0.3),'stone',i*0.1)
        m.beam(p+n*0.08,q0+n*0.08-(q0-p)*0.05,0.06,'iron')
def awning(m,x0,x1,y,z,depth=1.4,drop=0.6,stripes=8):
    # striped blue/cream awning sloping out from wall at z (normal +z)
    xs=np.linspace(x0,x1,stripes+1)
    for i in range(stripes):
        a,b=xs[i],xs[i+1]; pts=[(a,y-drop,z+depth),(b,y-drop,z+depth),(b,y,z),(a,y,z)]
        if i%2==0: m.cell([np.array(p) for p in pts],'banner',0.82,0.88,0.85,0.9)
        else: m.poly(pts,pts[0],(1,0,0),np.array(pts[3])-np.array(pts[0]),'plaster')
        q=[(a,y-drop,z+depth),(b,y-drop,z+depth),(b,y-drop-0.3,z+depth),(a,y-drop-0.3,z+depth)]
        q=[q[2],q[3],q[0],q[1]][::-1]
        if i%2==0: m.cell([np.array(p) for p in [(a,y-drop-0.3,z+depth),(b,y-drop-0.3,z+depth),(b,y-drop,z+depth),(a,y-drop,z+depth)]],'banner',0.82,0.88,0.85,0.9)
        else: m.poly([(a,y-drop-0.3,z+depth),(b,y-drop-0.3,z+depth),(b,y-drop,z+depth),(a,y-drop,z+depth)],(a,y-drop-0.3,z+depth),(1,0,0),(0,1,0),'plaster')
    for x in(x0,x1): m.beam((x,y-drop,z+depth),(x,y,z),0.05,'iron')
def stall(m,x,z,w=2.0):
    m.box((x-w/2,0.85,z-0.4),(x+w/2,0.95,z+0.4),'oak')
    for sx in(-1,1):
        for sz in(-1,1): m.box((x+sx*(w/2-0.08)-0.05,0,z+sz*0.32-0.05),(x+sx*(w/2-0.08)+0.05,0.85,z+sz*0.32+0.05),'beam')
    for k in np.linspace(-w/2+0.3,w/2-0.3,3): m.blob((x+k,1.08,z),0.17,'flowers',squash=0.7)
def rack(m,p,t,n,w=1.4,h=2.0):
    t=np.asarray(t,float); n=np.asarray(n,float); p=np.asarray(p,float); up=np.array([0,1.0,0])
    for s in(-1,1): m.obox(p+t*s*w/2+up*h/2+n*0.2,t,up,n,(0.1,h,0.1),'beam')
    for y in(0.6,1.2,1.8): m.obox(p+up*y+n*0.2,t,up,n,(w,0.06,0.35),'oak')
    for k in np.linspace(-w/2+0.2,w/2-0.2,5):  # swords/tools leaning
        m.beam(p+t*k+up*0.66+n*0.3,p+t*(k+0.05)+up*1.15+n*0.12,0.04,'iron')
        m.beam(p+t*k+up*1.26+n*0.3,p+t*(k+0.05)+up*1.75+n*0.12,0.04,'iron')
def lion_statue(m,c,s=1.0,strip='slate'):
    c=np.asarray(c,float); B=lambda lo,hi,st=strip:m.box(c+np.array(lo)*s,c+np.array(hi)*s,st)
    cyl(m,c+[0,0,-0.2*s],0.75*s,0,1.3*s,strip,10,r1=0.55*s)           # haunch/body
    cyl(m,c+[0,1.1*s,0.25*s],0.55*s,0,1.0*s,strip,10,r1=0.45*s)      # chest
    cyl(m,c+[0,1.85*s,0.45*s],0.7*s,0,0.9*s,strip,12,r1=0.35*s,cap=strip)  # mane
    B((-0.32,2.0,0.6),(0.32,2.55,1.25))                                  # head/muzzle
    B((-0.15,2.0,1.2),(0.15,2.25,1.4))
    for sx in(-1,1):
        B((sx*0.35-0.13,0,0.45),(sx*0.35+0.13,1.3,0.7)); B((sx*0.35-0.16,0,0.6),(sx*0.35+0.16,0.15,0.95))  # forelegs + paws
        B((sx*0.6-0.2,0,-0.7),(sx*0.6+0.2,0.5,0.2))   # hind paws
        B((sx*0.25-0.08,2.55,0.75),(sx*0.25+0.08,2.75,0.9))  # ears
    m.beam(c+np.array([0.5,0.3,-0.8])*s,c+np.array([0.9,0.9,-0.4])*s,0.1*s,strip)
def boat(m,c,L=7,W=2.2,rot=0):
    from geo import Mesh
    b=Mesh()
    for s in(-1,1):
        pts=[(-L/2,0.3,0),(L/2,0.3,0),(L/2-0.8,1.2,s*W/2),(-L/2+0.6,1.2,s*W/2)]
        if s<0: pts=[pts[1],pts[0],pts[3],pts[2]]
        b.poly(pts,pts[0],np.array(pts[1])-np.array(pts[0]),np.array(pts[3])-np.array(pts[0]),'oak')
    b.box((-L/2+0.8,1.0,-W/2+0.2),(L/2-1.0,1.1,W/2-0.2),'oak')
    b.beam((0,1.1,0),(0,7.4,0),0.18)
    # real sails: billowed cream canvas mainsail between yard and boom, jib to the bow, rigging lines
    b.beam((0,6.6,-1.9),(0,6.6,1.9),0.1,'beam'); b.beam((0.15,2.0,-0.1),(0.15,2.0,1.9) if False else (-0.2,2.1,0),0.01,'beam')
    b.beam((0,2.1,-1.7),(0,2.1,1.7),0.09,'beam')
    ys=np.linspace(2.2,6.5,6); bil=lambda y:0.55*np.sin(np.pi*(y-2.2)/4.3)
    for y0,y1 in zip(ys[:-1],ys[1:]):
        w0=1.65-0.08*(y0-2.2); w1=1.65-0.08*(y1-2.2)
        q=[(0.08+bil(y0),y0,-w0),(0.08+bil(y0),y0,w0),(0.08+bil(y1),y1,w1),(0.08+bil(y1),y1,-w1)]
        b.poly(q,q[0],(0,0,1),(0,1,0),'plaster'); b.poly([q[1],q[0],q[3],q[2]],q[1],(0,0,-1),(0,1,0),'plaster')
    for s in(-1,1): b.beam((0,7.3,0),(s*L/2*0.9,1.2,0),0.02,'iron'); b.beam((0,6.6,s*1.9),(0,1.2,s*W/2),0.015,'iron')
    jib=[(0.1,1.3,0.0),(L/2-0.5,1.3,0.0),(0.1,6.8,0.0)]
    jb=[(L/2*0.15,1.6,0.04),(L/2-0.4,1.4,0.04),(0.25,6.6,0.04)]
    b.poly(jb,jb[0],(1,0,0),(0,1,0),'plaster'); b.poly([jb[1],jb[0],jb[2]],jb[1],(-1,0,0),(0,1,0),'plaster')
    b.beam((0,7.4,0),(0,7.9,0),0.03,'iron'); b.obox(np.array([0.3,7.75,0]),(1,0,0),(0,1,0),(0,0,1),(0.6,0.35,0.02),'gold')
    m.merge(b,c,rot)
