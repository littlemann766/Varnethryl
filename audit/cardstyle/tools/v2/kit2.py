import numpy as np
from geo import norm
from atlas import STRIPS
Q=0  # build quality: 0 High, 1 Medium, 2 Low (set by export)
def SG(seg): return seg if seg<=6 else max(6,int(round(seg*(1,0.55,0.34)[Q])))
def cyl(m,c,r,y0,y1,strip,seg=16,cap=None,r1=None):
    seg=SG(seg)
    c=np.asarray(c,float); r1=r if r1 is None else r1; wm=STRIPS[strip][2]
    for i in range(seg):
        a0=2*np.pi*i/seg; a1=2*np.pi*(i+1)/seg
        p0=c+[r*np.cos(a0),y0,r*np.sin(a0)]; p1=c+[r*np.cos(a1),y0,r*np.sin(a1)]
        q1=c+[r1*np.cos(a1),y1,r1*np.sin(a1)]; q0=c+[r1*np.cos(a0),y1,r1*np.sin(a0)]
        ua=p0-p1; va=np.array([0,1.0,0])
        m.poly([p1,p0,q0,q1],p1,ua,(q1-p1),strip,uoff=(r*a1)/wm*-1)
    if cap:
        for i in range(seg):
            a0=2*np.pi*i/seg; a1=2*np.pi*(i+1)/seg
            m.poly([c+[0,y1,0],c+[r1*np.cos(a1),y1,r1*np.sin(a1)],c+[r1*np.cos(a0),y1,r1*np.sin(a0)]],c+[0,y1,0],(1,0,0),(0,0,-1),cap)
def cone(m,c,r,y0,h,strip='slate',seg=16):
    seg=SG(seg)
    c=np.asarray(c,float); ap=c+[0,y0+h,0]; wm=STRIPS[strip][2]
    for i in range(seg):
        a0=2*np.pi*i/seg; a1=2*np.pi*(i+1)/seg
        p0=c+[r*np.cos(a0),y0,r*np.sin(a0)]; p1=c+[r*np.cos(a1),y0,r*np.sin(a1)]
        m.poly([p1,p0,ap],p1,p0-p1,ap-(p0+p1)/2,strip,uoff=-(r*a1)/wm)
    if Q>=2: return
    m.beam(ap-[0,0.1,0],ap+[0,1.0,0],0.08,'iron'); m.obox(ap+[0,1.0,0],(1,0,0),(0,1,0),(0,0,1),(0.18,0.18,0.18),'gold')
def crenels_line(m,a,b,y,h=0.9,w=0.7,t=0.6,gap=0.6):
    a=np.asarray(a,float);b=np.asarray(b,float); d=b-a; L=np.linalg.norm(d); ax=d/L; az=np.cross(ax,[0,1,0])
    m.obox((a+b)/2+[0,y+0.25,0],ax,(0,1,0),az,(L,0.5,t),'stone')
    n=int(L//(w+gap))
    if Q>=2: return
    if Q==1: w,gap=w*2+gap,gap*2
    n=int(L//(w+gap))
    for k in range(n+1):
        p=a+ax*(k*(w+gap)+w/2) if n>0 else (a+b)/2
        if np.linalg.norm(p-a)>L: break
        m.obox(p+[0,y+0.5+h/2,0],ax,(0,1,0),az,(w,h,t),'stone',k*0.1)
def crenels_ring(m,c,r,y,n=12,h=0.9,t=0.6):
    c=np.asarray(c,float); cyl(m,c,r+0.25,y,y+0.5,'stone',n*2,cap=None)
    if Q>=2: cyl(m,c,r+0.2,y+0.5,y+1.0,'stone',n,cap=None); return
    if Q==1: n=max(6,n//2)
    for k in range(n):
        a=2*np.pi*(k+0.25)/n; p=c+[ (r+0.1)*np.cos(a),y+0.5+h/2,(r+0.1)*np.sin(a)]
        ax=np.array([-np.sin(a),0,np.cos(a)]); m.obox(p,ax,(0,1,0),np.cross(ax,[0,1,0]),(2*np.pi*r/n*0.5,h,t),'stone',k*0.2)
def barrel(m,c,r=0.38,h=0.95):
    c=np.asarray(c,float)
    cyl(m,c,r*0.85,0,h*0.18,'oak',10); cyl(m,c+[0,h*0.18,0],r*0.85,0,h*0.32,'oak',10,r1=r)
    cyl(m,c+[0,h*0.5,0],r,0,h*0.32,'oak',10,r1=r*0.85); cyl(m,c+[0,h*0.82,0],r*0.85,0,h*0.18,'oak',10,cap='oak')
    for y in(0.2,0.8): cyl(m,c+[0,h*y-0.03,0],r*(0.9 if y<0.5 else 0.9)+0.02,0,0.06,'iron',10)
def pot_plant(m,c,r=0.3):
    c=np.asarray(c,float); cyl(m,c,r*0.75,0,0.45,'stone',8,r1=r); m.blob(c+[0,0.62,0],r*1.15,'flowers',squash=0.8)
def steps(m,c,t,n_,w,k=3,rise=0.17,run=0.32):
    c=np.asarray(c,float); t=np.asarray(t,float); n_=np.asarray(n_,float)
    for i in range(k):
        m.obox(c+n_*(run*(k-i)/2)+[0,rise*(i+0.5),0],t,(0,1,0),n_,(w,rise,run*(k-i)),'stone',i*0.3)
    for s in(-1,1):
        p=c+t*s*(w/2+0.35)+n_*(run*k/2)
        m.obox(p+[0,0.35,0],t,(0,1,0),n_,(0.6,0.7,run*k),'stone',0.5); m.blob(p+[0,0.85,0],0.32,'flowers',squash=0.7)
def crate(m,c,s=0.7):
    c=np.asarray(c,float); m.box(c+[-s/2,0,-s/2],c+[s/2,s,s/2],'oak',0.3)
    for y in(0.05,s-0.05): m.box(c+[-s/2-0.02,y-0.04,-s/2-0.02],c+[s/2+0.02,y+0.04,s/2+0.02],'beam')
def anvil(m,c):
    c=np.asarray(c,float); m.box(c+[-0.3,0,-0.3],c+[0.3,0.5,0.3],'beam')
    m.box(c+[-0.12,0.5,-0.12],c+[0.12,0.75,0.12],'iron'); m.box(c+[-0.45,0.75,-0.18],c+[0.35,0.95,0.18],'iron')
    m.poly([c+[0.35,0.95,0.18],c+[0.35,0.75,0.18],c+[0.7,0.9,0]],c+[0.35,0.75,0.18],(0,-1,0),(1,0,0),'iron')
def lean_to(m,x0,x1,z0,depth,h0,h1,posts=3):
    # mono-pitch slate shed against wall at z=z0 extending to z0+depth (along +z)
    z1=z0+depth
    for x in np.linspace(x0+0.15,x1-0.15,posts): m.box((x-0.12,0,z1-0.24),(x+0.12,h1,z1),'beam')
    m.beam((x0,h1,z1-0.12),(x1,h1,z1-0.12),0.24)
    pts=[(x0,h1,z1+0.4),(x1,h1,z1+0.4),(x1,h0,z0),(x0,h0,z0)]
    a=(1,0,0); up=np.array(pts[3])-np.array(pts[0])
    th=np.array([0,0.15,0])
    m.poly([np.array(p)+th for p in pts],np.array(pts[0])+th,a,up,'slate')
    m.poly([pts[1],pts[0],pts[3],pts[2]],pts[1],(-1,0,0),up,'oak')
def ivy(m,pts,r=0.3):
    for p in pts: m.blob(p,r,'flowers',seg=5,squash=1.3)
