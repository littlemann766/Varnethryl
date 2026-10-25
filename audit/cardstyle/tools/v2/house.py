import numpy as np
from geo import Mesh, norm
T=np.tan
def house(sp):
    m=Mesh(); m.remap=dict(sp.get('remap',{})); W=sp['W'];D=sp['D'];g=sp.get('g',3.2);fl=sp.get('floors',1);fh=sp.get('fh',2.7);j=sp.get('jetty',0.35)
    pit=np.radians(sp.get('pitch',57)); oh=sp.get('oh',0.55); og=0.45
    E=g+fl*fh; hs=D/2+j; Rh=E+hs*T(pit)
    yroof=lambda z:E+(hs-abs(z))*T(pit)
    X0,X1=-W/2,W/2
    # ---- ground floor stone + plinth ----
    m.box((X0,0,-D/2),(X1,g,D/2),'stone'); m.box((X0-0.12,0,-D/2-0.12),(X1+0.12,0.45,D/2+0.12),'stone',0.3)
    # jetty joist band + upper floors plaster
    m.box((X0-0.05,g-0.28,-hs-0.05),(X1+0.05,g,hs+0.05),'beam')
    UP=sp.get('upper','plaster'); FR=sp.get('framing',True)
    m.box((X0,g,-hs),(X1,E,hs),UP)
    m.LOD=1
    for x in np.arange(X0+0.3,X1,0.65):
        for sz in(1,-1): m.box((x-0.09,g-0.45,sz*(D/2)-0.0 if sz>0 else -hs-0.1),(x+0.09,g-0.27,hs+0.1 if sz>0 else -D/2),'beam')
    m.LOD=99
    # ---- timber framing on upper walls (z faces and x faces) ----
    def frame_face(face,y0,y1,a0,a1):
        if not FR: return
        m.LOD=1
        o=0.07; bw=0.2
        def P(a,y):
            if face=='z+': return (a,y,hs+o)
            if face=='z-': return (a,y,-hs-o)
            if face=='x+': return (X1+o,y,a)
            if face=='x-': return (X0-o,y,a)
        n=max(2,int(round((a1-a0)/1.7)))
        xs=np.linspace(a0+0.1,a1-0.1,n+1)
        for a in xs: m.beam(P(a,y0),P(a,y1),bw)
        for yy in np.arange(y0,y1+0.01,fh/2 if fh>2 else fh): m.beam(P(a0,yy),P(a1,yy),bw)
        m.beam(P(a0,y1),P(a1,y1),bw)
        for k in range(n):
            if k in(0,n-1):
                a,b=xs[k],xs[k+1]
                if k==0: m.beam(P(a,y0+0.1),P(b,y0+fh/2-0.1),0.16)
                else: m.beam(P(b,y0+0.1),P(a,y0+fh/2-0.1),0.16)
        m.LOD=99
    for f in range(fl):
        y0=g+f*fh
        frame_face('z+',y0,y0+fh,X0,X1); frame_face('z-',y0,y0+fh,X0,X1)
        frame_face('x+',y0,y0+fh,-hs,hs); frame_face('x-',y0,y0+fh,-hs,hs)
    # ---- gable end walls (closed) ----
    for sx in(1,-1):
        x=X1 if sx>0 else X0
        pts=[(x,E,hs*sx),(x,E,-hs*sx),(x,Rh,0)] if sx>0 else [(x,E,-hs),(x,E,hs),(x,Rh,0)]
        a=(0,0,-1) if sx>0 else (0,0,1)
        m.poly(pts,pts[0],a,(0,1,0),UP)
        m.LOD=1 if FR else -5; o=0.07*sx
        m.beam((x+o,E,-hs),(x+o,E,hs),0.2); m.beam((x+o,E,0),(x+o,Rh-0.2,0),0.2)
        yc=E+(Rh-E)*0.45; zc=hs*0.55
        m.beam((x+o,yc,-zc),(x+o,yc,zc),0.18)
        for s2 in(1,-1): m.beam((x+o,E,s2*hs*0.55),(x+o,yc,s2*hs*0.55),0.16)
        m.LOD=99
    # ---- main roof: slate top, oak soffit, fascia + barge beams, ridge ----
    ox0,ox1=X0-og,X1+og
    for sz in(1,-1):
        ze=sz*(hs+oh); ye=E-oh*T(pit)
        top=[(ox0,ye,ze),(ox1,ye,ze),(ox1,Rh,0),(ox0,Rh,0)]
        if sz<0: top=[top[1],top[0],top[3],top[2]]
        up=norm(np.array(top[3])-np.array(top[0])) if sz>0 else norm(np.array(top[2])-np.array(top[1]))
        a=(1,0,0) if sz>0 else (-1,0,0)
        th=0.16; nrm=np.array([0,np.cos(pit),sz*np.sin(pit)])
        tp=[np.array(p)+nrm*th for p in top]
        m.poly(tp,tp[0],a,up,'slate')
        bt=[top[1],top[0],top[3],top[2]]
        m.poly(bt,bt[0],(-a[0],0,0),up,'oak')
        # fascia (eave edge) and barge boards
        m.beam(np.array([ox0,ye,ze])+nrm*th/2,np.array([ox1,ye,ze])+nrm*th/2,0.2)
        for x in(ox0,ox1): m.beam(np.array([x,ye,ze])+nrm*th/2,np.array([x,Rh,0])+nrm*th/2,0.22)
    m.beam((ox0,Rh+0.15,0),(ox1,Rh+0.15,0),0.3,'slate')
    for x in(ox0,ox1): m.beam((x,Rh+0.2,0),(x,Rh+1.0,0),0.06,'iron'); m.obox((x,Rh+1.0,0),(1,0,0),(0,1,0),(0,0,1),(0.14,0.14,0.14),'gold')
    # ---- max-detail: jetty corbels with carved ends, gutters + downpipes ----
    m.LOD=1
    if j>0.15:
        for x in np.arange(X0+0.9,X1-0.5,1.6):
            for sz in(1,-1):
                z0=sz*D/2; z1=sz*(hs-0.02)
                m.beam((x,g-1.05,z0+sz*0.05),(x,g-0.32,z1),0.14,'beam')
                m.obox((x,g-0.38,z1-sz*0.02),(1,0,0),(0,1,0),(0,0,1),(0.2,0.12,0.2),'beam')
    for sz in(1,-1):
        ze=sz*(hs+oh-0.05); ye=E-oh*T(pit)-0.12
        m.beam((ox0+0.1,ye,ze),(ox1-0.1,ye-0.05,ze),0.13,'iron')
        for x in(ox0+0.25,ox1-0.25):
            m.beam((x,ye,ze),(x,ye-0.35,sz*(hs+0.12)),0.08,'iron'); m.beam((x,ye-0.35,sz*(hs+0.12)),(x,0.15,sz*(hs+0.12)),0.09,'iron')
            m.obox((x,0.08,sz*(hs+0.25)),(1,0,0),(0,1,0),(0,0,1),(0.14,0.14,0.3),'iron')
    m.LOD=99
    ctx=dict(m=m,W=W,D=D,g=g,E=E,hs=hs,Rh=Rh,pit=pit,yroof=yroof,X0=X0,X1=X1,fh=fh,fl=fl,shutters=sp.get('shutters',FR))
    return ctx
# ---------- details ----------
def facepos(c,face,a,y,out=0.0):
    hs=c['hs'] if y>=c['g'] else c['D']/2
    cr=c.get('cross')
    if face=='z+' and cr and cr['x0']-0.05<=a<=cr['x1']+0.05: return np.array([a,y,cr['zf']+out]),np.array([1.0,0,0]),np.array([0,0,1.0])
    if face=='z+': return np.array([a,y,hs+out]),np.array([1.0,0,0]),np.array([0,0,1.0])
    if face=='z-': return np.array([a,y,-hs-out]),np.array([-1.0,0,0]),np.array([0,0,-1.0])
    if face=='x+': return np.array([c['X1']+out,y,a]),np.array([0,0,-1.0]),np.array([1.0,0,0])
    if face=='x-': return np.array([c['X0']-out,y,a]),np.array([0,0,1.0]),np.array([-1.0,0,0])
def window(c,face,a,y,w=1.2,h=1.65,flowers=False,base=None):
    m=c['m']
    if base is None: p,t,n=facepos(c,face,a,y)
    else: p,t,n=base
    up=np.array([0,1.0,0]); b=p+n*0.02
    m.cell([b-t*w/2,b+t*w/2,b+t*w/2+up*h,b-t*w/2+up*h],'window')
    m.LOD=2; d=0.26; fw=0.14
    for s in(-1,1): m.obox(p+t*s*(w/2+fw/2)+up*h/2+n*d/2,t,up,n,(fw,h+2*fw,d),'beam')
    m.obox(p+up*(h+fw/2)+n*d/2,t,up,n,(w+2*fw,fw,d),'beam')
    m.obox(p-up*fw/2+n*0.12,t,up,n,(w+0.35,fw,0.24),'stone' if y<c['g'] else 'beam')
    m.LOD=1
    m.obox(p+up*h/2+n*0.06,t,up,n,(0.06,h,0.06),'beam'); m.obox(p+up*h*0.5+n*0.06,t,up,n,(w,0.06,0.06),'beam')
    if c.get('shutters') and base is None and w<=1.5:
        m.LOD=1
        for s in(-1,1):
            sc_=p+t*s*(w/2+0.14+w*0.25)+up*h/2+n*0.06
            m.obox(sc_,t,up,n,(w*0.48,h*0.96,0.06),'oak')
            for yy in(0.2,0.8): m.obox(sc_+up*(yy-0.5)*h+n*0.04-t*s*w*0.12,t,up,n,(w*0.26,0.05,0.03),'iron')
            m.obox(sc_+n*0.035,t,up,n,(w*0.04,h*0.8,0.02),'beam')
        m.LOD=99
    if flowers:
        bc=p-up*0.38+n*0.26; m.obox(bc,t,up,n,(w+0.2,0.32,0.34),'oak')
        for k in np.linspace(-w/2,w/2,6): m.blob(bc+t*k+up*0.24,0.26,'flowers')
        for k in np.linspace(-w/2+0.15,w/2-0.15,4): m.blob(bc+t*k+up*0.2+n*0.16,0.2,'flowers',squash=0.7)
    m.LOD=99
def door(c,face,a,w=1.5,h=2.7):
    m=c['m']; p,t,n=facepos(c,face,a,0.0); up=np.array([0,1.0,0]); b=p+n*0.02
    m.cell([b-t*w/2,b+t*w/2,b+t*w/2+up*h,b-t*w/2+up*h],'door')
    # stone arch voussoirs + jambs + steps
    r=w/2*0.84; cy=h-w/2*0.84*1.0
    m.LOD=1
    for k in range(9):
        th=np.pi*k/8; q=p+t*np.cos(th)*(r+0.17)+up*(cy+np.sin(th)*(r+0.17))+n*0.12
        m.obox(q,t*np.cos(th+np.pi/2)+up*np.sin(th+np.pi/2),-(t*np.cos(th)+up*np.sin(th)),n,(0.3,0.38,0.32),'stone',k*0.13)
    for s in(-1,1): m.obox(p+t*s*(r+0.05)+up*cy/2+n*0.16,t,up,n,(0.34,cy,0.32),'stone')
    m.obox(p+up*(cy+r+0.12)+n*0.2,t,up,n,(0.32,0.45,0.36),'stone',0.9)
    m.LOD=99
    for k in range(2): m.obox(p+n*(0.45+0.35*(1-k))+up*(0.1+0.2*k),t,up,n,(w+0.8-0.3*k,0.2+0.2*k if False else 0.2,0.7),'stone')
def cloth(m,top_c,t,n,w,h,name,wave=0.08,swallow=True):
    # banner cloth grid hanging down from top centre, gentle wave along n
    nx,ny=4,8; up=np.array([0,1.0,0]); V={}
    for i in range(nx+1):
        for k in range(ny+1):
            u=i/nx; v=k/ny; yy=-h*v
            if swallow and k==ny: yy+= (h*0.18)*(1-abs(u-0.5)*2)
            V[i,k]=top_c+t*(u-0.5)*w+up*yy+n*wave*np.sin(u*np.pi*2+v*3)*v
    from atlas import CELLS,S
    ci=CELLS.index(name); x0=ci*256/S; cw=256/S; y0=1536/S; ch=512/S
    UV=lambda i,k:(x0+cw*(0.01+0.98*i/nx),1-(y0+ch*(0.005+0.99*k/ny)))
    for i in range(nx):
        for k in range(ny):
            a,b,cc,d=(i,k+1),(i+1,k+1),(i+1,k),(i,k)
            for ids in(((a,b,cc),(a,cc,d)),((a,cc,b),(a,d,cc))):
                for tr in ids: m.tri(*(V[x] for x in tr),*(UV(*x) for x in tr))
def banner(c,face,a,y,w=0.9,h=1.9):
    m=c['m']; p,t,n=facepos(c,face,a,y); up=np.array([0,1.0,0])
    m.beam(p,p+n*0.75,0.07,'iron'); m.beam(p-up*0.5,p+n*0.6,0.05,'iron')
    m.beam(p+n*0.75-t*(w/2+0.08),p+n*0.75+t*(w/2+0.08),0.06,'iron')
    for s in(-1,1): m.obox(p+n*0.75+t*s*(w/2+0.12),t,up,n,(0.09,0.09,0.09),'gold')
    cloth(m,p+n*0.75-up*0.04,t,n,w,h,'banner')
def sign(c,face,a,y,name,w=0.9,h=0.9):
    m=c['m']; p,t,n=facepos(c,face,a,y); up=np.array([0,1.0,0]); L=1.25
    m.beam(p,p+n*L,0.07,'iron'); m.beam(p-up*0.55,p+n*L*0.7,0.05,'iron')
    m.obox(p+n*L,t,up,n,(0.1,0.1,0.1),'gold')
    bc=p+n*(L*0.55)-up*(0.2+h/2)
    for s in(-1,1): m.beam(p+n*(L*0.55+s*w*0.35),bc+n*s*w*0.35+up*h/2,0.025,'iron')
    # board: plane spanned by n (width) and up; thickness along t
    th=0.07
    for s in(1,-1):
        f=bc+t*s*th/2; tt=n*s
        m.cell([f-tt*w/2-up*h/2,f+tt*w/2-up*h/2,f+tt*w/2+up*h/2,f-tt*w/2+up*h/2],name)
    m.obox(bc+up*h/2,n,up,t,(w+0.06,0.06,th+0.02),'beam'); m.obox(bc-up*h/2,n,up,t,(w+0.06,0.06,th+0.02),'beam')
    for s in(-1,1): m.obox(bc+n*s*w/2,n,up,t,(0.06,h,th+0.02),'beam')
def lantern(c,face,a,y):
    m=c['m']; p,t,n=facepos(c,face,a,y); up=np.array([0,1.0,0]); q=p+n*0.3
    m.beam(p,q,0.04,'iron'); m.obox(q-up*0.2,t,up,n,(0.2,0.04,0.2),'iron'); m.obox(q-up*0.45,t,up,n,(0.22,0.05,0.22),'iron')
    for s in(1,-1):
        for (tt,nn) in((t,n),(n,t)):
            f=q-up*0.32+nn*s*0.1; m.cell([f-tt*s*0.09-up*0.11,f+tt*s*0.09-up*0.11,f+tt*s*0.09+up*0.11,f-tt*s*0.09+up*0.11],'window',0.1,0.4,0.55,0.95)
def chimney(c,x,z,w=1.0,extra=1.3):
    m=c['m']; top=c['Rh']+extra; y0=c['yroof'](z)-1.0
    m.box((x-w/2,y0,z-w/2),(x+w/2,top,z+w/2),'stone',0.2)
    m.box((x-w/2-0.1,top,z-w/2-0.1),(x+w/2+0.1,top+0.18,z+w/2+0.1),'stone',0.5)
    for s in(-1,1): m.box((x+s*w*0.22-0.12,top+0.18,z-0.12),(x+s*w*0.22+0.12,top+0.55,z+0.12),'stone',0.7)
def cross_gable(c,cx,cw,pz=0.25,pitch=None,attic=True,face_windows=(),mat='plaster',framed=True):
    # front (+z) cross gable from ground: ridge along z
    m=c['m']; g=c['g'];E=c['E'];hs=c['hs'];D=c['D']; pit=c['pit'] if pitch is None else np.radians(pitch)
    x0,x1=cx-cw/2,cx+cw/2; zf=hs+pz; ch=cw/2; R2=E+ch*np.tan(pit)
    m.box((x0,0,D/2-0.1),(x1,g,D/2+pz),'stone',0.4)
    m.box((x0,g,hs-0.2),(x1,E,zf),mat,0.4)
    m.poly([(x0,E,zf),(x1,E,zf),(cx,R2,zf)],(x0,E,zf),(1,0,0),(0,1,0),mat,0.4)
    m.LOD=1 if framed else -5
    for x in np.linspace(x0+0.1,x1-0.1,4): m.beam((x,g,zf+0.07),(x,E,zf+0.07),0.2)
    for yy in(g,g+(E-g)/2,E): m.beam((x0,yy,zf+0.07),(x1,yy,zf+0.07),0.2)
    m.beam((cx,E,zf+0.07),(cx,R2-0.15,zf+0.07),0.2)
    m.LOD=99
    oh=0.5; zb=zf+0.5; zback=max(0.0,hs-(R2-E)/np.tan(c['pit'])-0.5)
    for sx in(1,-1):
        xe=cx+sx*(ch+oh); ye=E-oh*np.tan(pit); th=0.16
        nrm=np.array([sx*np.sin(pit),np.cos(pit),0])
        pts=[(xe,ye,zback),(xe,ye,zb),(cx,R2,zb),(cx,R2,zback)]
        if sx<0: pts=[pts[1],pts[0],pts[3],pts[2]]
        pts=[np.array(p)+nrm*th for p in pts]
        a=(0,0,1) if sx>0 else (0,0,-1)
        upv=norm(np.array([-sx*np.cos(pit),np.sin(pit),0]))
        m.poly(pts,pts[0],a,upv,'slate')
        bt=[np.array(p)-nrm*th for p in (pts[1],pts[0],pts[3],pts[2])]
        m.poly(bt,bt[0],(0,0,-a[2]),upv,'oak')
        m.beam(np.array([xe,ye,zb]),np.array([cx,R2,zb])+nrm*0.05,0.22)
        m.beam(np.array([xe,ye,zback]),np.array([xe,ye,zb]),0.2)
    m.beam((cx,R2+0.15,zback),(cx,R2+0.15,zb),0.3,'slate')
    c['cross']=dict(zf=zf,R2=R2,x0=x0,x1=x1)
    if attic:
        base=lambda a,y:(np.array([a,y,zf]),np.array([1.0,0,0]),np.array([0,0,1.0]))
        window(c,None,0,0,w=1.2,h=1.5,base=base(cx,E+0.4))
        if R2-E>3.2: window(c,None,0,0,w=0.6,h=0.75,base=base(cx,E+2.35))
    return c['cross']
def dormer(c,x,side=1,w=1.6,ww=1.1,wh=1.4):
    m=c['m']; hs=c['hs']; zf=side*(hs-0.9); yb=c['yroof'](zf); x0,x1=x-w/2,x+w/2
    h=0.15+wh+0.22; zb=side*0.6; pit=np.radians(38)
    m.box((x0,yb-0.4,min(zb,zf)),(x1,yb+h,max(zb,zf)),'plaster',0.6)
    base=(np.array([x,yb+0.15,zf]),np.array([side*1.0,0,0]),np.array([0,0,side*1.0]))
    window(c,None,0,0,w=ww,h=wh,base=base)
    R2=yb+h+(w/2)*np.tan(pit)
    pf=[(x0,yb+h,zf),(x1,yb+h,zf),(x,R2,zf)]
    if side<0: pf=[pf[1],pf[0],pf[2]]
    m.poly(pf,pf[0],(side,0,0),(0,1,0),'plaster',0.6)
    for sx in(1,-1):
        xe=x+sx*(w/2+0.3); ye=yb+h-0.3*np.tan(pit); zz=zf+side*0.3
        p=[(xe,ye,zb),(xe,ye,zz),(x,R2+0.12,zz),(x,R2+0.12,zb)]
        a=norm(np.array(p[1])-np.array(p[0])); up=norm(np.array(p[3])-np.array(p[0]))
        m.poly(p,p[0],a,up,'slate',0.3)
        m.poly([p[1],p[0],p[3],p[2]],p[1],-a,up,'oak')
        m.beam(np.array([xe,ye,zz]),np.array([x,R2+0.1,zz]),0.16)
    m.beam((x,R2+0.2,zb),(x,R2+0.2,zz),0.22,'slate')
def gable_fill(c,face):
    """second small window high in a gable + herringbone beams so the triangle isn't empty"""
    E,Rh=c['E'],c['Rh']; m=c['m']
    window(c,face,0,E+0.45,1.2,1.5)
    window(c,face,0,E+0.45+1.5+0.5,0.6,0.75)
    p,t,n=facepos(c,face,0,E); m.LOD=1; hs=c['hs']; tp=np.tan(c['pit'])
    for s_ in(-1,1):
        m.beam(p+t*s_*hs*0.85+n*0.07,p+t*s_*hs*0.25+n*0.07+np.array([0,hs*0.6*tp,0]),0.14)
    m.LOD=99
